"""Focused E2E test for Q-0090: Personal Today real API record appears in native UI and persists after restart."""

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

from PySide6.QtNetwork import QNetworkAccessManager, QNetworkProxy, QNetworkProxyFactory
from PySide6.QtWidgets import QApplication

from aetherion_desktop.features.personal.authorized_today import AuthorizedPersonalTodayPage

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


class PersonalRestartPersistenceE2ETests(unittest.TestCase):
    def test_real_api_observation_appears_and_persists_across_restart(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        port = _free_port()
        base_url = f"http://127.0.0.1:{port}"
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env["AETHERION_DB_PATH"] = str(Path(tmp) / "personal_restart_e2e.sqlite3")
            env["AETHERION_BOOTSTRAP_USER"] = "admin_pers"
            env["AETHERION_BOOTSTRAP_PASSWORD"] = "TestPass1234!"
            env["AETHERION_BOOTSTRAP_ROLE"] = "admin"

            def _start_api() -> subprocess.Popen:
                return subprocess.Popen(
                    [sys.executable, "-m", "uvicorn", "aetherion_server.main:app", "--host", "127.0.0.1", "--port", str(port)],
                    cwd=str(REPO_ROOT),
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )

            def _wait_ready(proc: subprocess.Popen) -> str:
                deadline = time.monotonic() + 10.0
                while time.monotonic() < deadline:
                    try:
                        st, _ = _http_json(opener, "GET", f"{base_url}/health")
                        if st == 200:
                            break
                    except Exception:
                        time.sleep(0.15)
                else:
                    raise RuntimeError("Server did not start")
                _, body = _http_json(
                    opener,
                    "POST",
                    f"{base_url}/api/v1/auth/login",
                    {"username": "admin_pers", "password": "TestPass1234!"},
                )
                return body["access_token"]

            def _stop_api(proc: subprocess.Popen) -> None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=5)
                if proc.stdout:
                    proc.stdout.close()
                if proc.stderr:
                    proc.stderr.close()

            with patch.dict(
                os.environ,
                {"HTTP_PROXY": "", "HTTPS_PROXY": "", "http_proxy": "", "https_proxy": "", "ALL_PROXY": ""},
            ):
                app = QApplication.instance() or QApplication([])
                QNetworkProxyFactory.setUseSystemConfiguration(False)
                QNetworkProxy.setApplicationProxy(QNetworkProxy(QNetworkProxy.ProxyType.NoProxy))

                proc1 = _start_api()
                proc2 = None
                try:
                    token1 = _wait_ready(proc1)
                    _http_json(
                        opener,
                        "POST",
                        f"{base_url}/api/v1/subjects",
                        {"subject_id": "CREW-01", "display_name": "Crew One", "scope": "personal", "role_label": "crew"},
                        token=token1,
                    )
                    _http_json(
                        opener,
                        "POST",
                        f"{base_url}/api/v1/observations",
                        {
                            "subject_id": "CREW-01",
                            "scope": "personal",
                            "metric": "heart_rate",
                            "value": 71.0,
                            "unit": "bpm",
                            "source_id": "wearable_1",
                            "observed_at": "2026-11-14T10:30:00+00:00",
                            "quality": "READY",
                            "verification_state": "DEVICE_UNVERIFIED",
                            "idempotency_key": "q0090-e2e-001",
                        },
                        token=token1,
                    )

                    net1 = QNetworkAccessManager()
                    net1.setProxy(QNetworkProxy(QNetworkProxy.ProxyType.NoProxy))
                    page1 = AuthorizedPersonalTodayPage(base_url, net1)
                    page1.select_subject("CREW-01", token1)

                    dl1 = time.monotonic() + 5.0
                    while not page1._displayed_cards and time.monotonic() < dl1:
                        app.processEvents()
                        time.sleep(0.05)

                    self.assertEqual(len(page1._displayed_cards), 1)
                    self.assertEqual(page1.table.rowCount(), 1)
                    page1.close()
                    _stop_api(proc1)

                    # Restart API + fresh Personal UI instance
                    proc2 = _start_api()
                    token2 = _wait_ready(proc2)

                    net2 = QNetworkAccessManager()
                    net2.setProxy(QNetworkProxy(QNetworkProxy.ProxyType.NoProxy))
                    page2 = AuthorizedPersonalTodayPage(base_url, net2)
                    page2.select_subject("CREW-01", token2)

                    dl2 = time.monotonic() + 5.0
                    while not page2._displayed_cards and time.monotonic() < dl2:
                        app.processEvents()
                        time.sleep(0.05)

                    self.assertEqual(len(page2._displayed_cards), 1)
                    self.assertEqual(page2.table.rowCount(), 1)
                    page2.close()
                finally:
                    if proc1.poll() is None:
                        _stop_api(proc1)
                    if proc2 is not None and proc2.poll() is None:
                        _stop_api(proc2)


if __name__ == "__main__":
    unittest.main()
