"""Focused E2E test for Q-0245: Mission-to-Personal identity handoff and unknown-crew rejection."""

from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import urllib.request

from PySide6.QtNetwork import QNetworkProxy
from PySide6.QtWidgets import QApplication

from aetherion_desktop.main import AetherionWindow

REPO_ROOT = Path(__file__).resolve().parents[1]


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _http_json(opener, method: str, url: str, payload: dict | None = None, token: str | None = None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with opener.open(req, timeout=5.0) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


class MissionToPersonalIdentityE2ETests(unittest.TestCase):
    def test_selected_crew_handoff_and_unknown_crew_rejection_without_fallback(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        port = _free_port()
        base_url = f"http://127.0.0.1:{port}"
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env["AETHERION_DB_PATH"] = str(Path(tmp) / "mission_personal_e2e.sqlite3")
            env["AETHERION_BOOTSTRAP_USER"] = "admin_e2e"
            env["AETHERION_BOOTSTRAP_PASSWORD"] = "TestPass1234!"
            env["AETHERION_BOOTSTRAP_ROLE"] = "admin"
            proc = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "aetherion_server.main:app",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(port),
                ],
                cwd=str(REPO_ROOT),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            try:
                deadline = time.monotonic() + 10.0
                while time.monotonic() < deadline:
                    try:
                        st, _ = _http_json(opener, "GET", f"{base_url}/health")
                        if st == 200:
                            break
                    except Exception:
                        time.sleep(0.15)
                else:
                    err = proc.stderr.read().decode(errors="replace") if proc.stderr else ""
                    raise RuntimeError(f"Server did not start: poll={proc.poll()} stderr={err[:500]}")

                _, login_body = _http_json(
                    opener,
                    "POST",
                    f"{base_url}/api/v1/auth/login",
                    {"username": "admin_e2e", "password": "TestPass1234!"},
                )
                token = login_body["access_token"]

                # Create real subject CREW-01 and post one LIVE observation
                _http_json(
                    opener,
                    "POST",
                    f"{base_url}/api/v1/subjects",
                    {
                        "subject_id": "CREW-01",
                        "display_name": "Crew One",
                        "scope": "personal",
                        "role_label": "crew",
                    },
                    token=token,
                )
                _http_json(
                    opener,
                    "POST",
                    f"{base_url}/api/v1/observations",
                    {
                        "subject_id": "CREW-01",
                        "scope": "personal",
                        "metric": "heart_rate",
                        "value": 68.0,
                        "unit": "bpm",
                        "source_id": "wearable_1",
                        "observed_at": "2026-11-14T10:00:00+00:00",
                        "quality": "READY",
                        "verification_state": "DEVICE_UNVERIFIED",
                        "idempotency_key": "q0245-e2e-001",
                    },
                    token=token,
                )

                with patch.dict(
                    os.environ,
                    {
                        "AETHERION_API_URL": base_url,
                        "AETHERION_AUTOSTART_LOCAL_SERVER": "0",
                    },
                ):
                    app = QApplication.instance() or QApplication([])
                    QNetworkProxy.setApplicationProxy(QNetworkProxy(QNetworkProxy.ProxyType.NoProxy))
                    win = AetherionWindow()
                    win.network.setProxy(QNetworkProxy(QNetworkProxy.ProxyType.NoProxy))
                    # Exercise the actual Desktop login completion with the
                    # bearer token and user returned by the running Server.
                    self.assertIn("user", login_body)
                    win._login_complete(login_body, base_url)
                    self.assertEqual(win.access_token, token)
                    self.assertEqual(win.session_identity, login_body["user"])

                    # Login completion asynchronously loads the first authorized
                    # subject. Drain that request before testing explicit handoff,
                    # otherwise it could race the UNKNOWN-999 rejection below.
                    login_deadline = time.monotonic() + 5.0
                    while not win.personal_today_page._displayed_cards and time.monotonic() < login_deadline:
                        app.processEvents()
                        time.sleep(0.05)
                    self.assertEqual(len(win.personal_today_page._displayed_cards), 1)

                    # 1. Mission -> Personal handoff for CREW-01
                    win.mission_control_page.subject_activated.emit("CREW-01", token)
                    wait_dl = time.monotonic() + 5.0
                    while not win.personal_today_page._displayed_cards and time.monotonic() < wait_dl:
                        app.processEvents()
                        time.sleep(0.05)

                    self.assertIs(win.pages.currentWidget(), win.operations_home_page)
                    self.assertIs(
                        win.operations_home_page.workspace_stack.currentWidget(),
                        win.personal_today_page,
                    )
                    self.assertEqual(win.personal_today_page._subject_id, "CREW-01")
                    self.assertEqual(len(win.personal_today_page._displayed_cards), 1)

                    # 2. Unknown crew must clear prior CREW-01 records and never fall back
                    win.mission_control_page.subject_activated.emit("UNKNOWN-999", token)
                    for _ in range(15):
                        app.processEvents()
                        time.sleep(0.03)
                    self.assertEqual(win.personal_today_page._subject_id, "UNKNOWN-999")
                    self.assertEqual(win.personal_today_page._displayed_cards, ())
                    self.assertEqual(win.personal_today_page.table.rowCount(), 0)
                    self.assertIs(win.pages.currentWidget(), win.operations_home_page)

                    # 3. Invalid/empty handoff rejected without fallback
                    win.mission_control_page.subject_activated.emit("", "")
                    app.processEvents()
                    self.assertEqual(win.personal_today_page._subject_id, "")
                    self.assertEqual(win.personal_today_page._displayed_cards, ())
                    win.close()
            finally:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                if proc.stdout:
                    proc.stdout.close()
                if proc.stderr:
                    proc.stderr.close()


if __name__ == "__main__":
    unittest.main()
