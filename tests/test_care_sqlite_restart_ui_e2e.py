"""Focused E2E test for Q-0105: Care SQLite restart + native Qt CareJourneyPage persistence."""

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
import urllib.request

from unittest.mock import patch
from PySide6.QtNetwork import QNetworkProxy, QNetworkProxyFactory
from PySide6.QtWidgets import QApplication, QMessageBox

from aetherion_desktop.features.care.journey_page import CareJourneyPage

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


class CareSqliteRestartUIE2ETests(unittest.TestCase):
    def test_care_episode_persists_across_sqlite_server_and_ui_restart(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        port = _free_port()
        base_url = f"http://127.0.0.1:{port}"
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "care_restart_e2e.sqlite3"
            env = os.environ.copy()
            env["AETHERION_DB_PATH"] = str(db_path)
            env["AETHERION_BOOTSTRAP_USER"] = "admin_care"
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
                    raise RuntimeError("Server failed to start")
                _, body = _http_json(
                    opener,
                    "POST",
                    f"{base_url}/api/v1/auth/login",
                    {"username": "admin_care", "password": "TestPass1234!"},
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

                    page1 = CareJourneyPage(api_url=base_url, locale="vi")
                    page1.net.setProxy(QNetworkProxy(QNetworkProxy.ProxyType.NoProxy))
                    page1.set_identity("CREW-01", token1)
                    for _ in range(10):
                        app.processEvents()
                        time.sleep(0.03)
                    page1.new_concern.setText("Mild post-EVA fatigue")
                    page1.new_consent.setChecked(True)
                    with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
                        page1.create_episode()

                    dl = time.monotonic() + 5.0
                    while not page1.episode_id and time.monotonic() < dl:
                        app.processEvents()
                        time.sleep(0.05)

                    created_episode_id = page1.episode_id
                    self.assertTrue(created_episode_id, msg=f"status={page1.status.text()}")
                    page1.close()
                    _stop_api(proc1)

                    # Restart server + new UI instance against the same SQLite database
                    proc2 = _start_api()
                    token2 = _wait_ready(proc2)

                    page2 = CareJourneyPage(api_url=base_url, locale="en")
                    page2.net.setProxy(QNetworkProxy(QNetworkProxy.ProxyType.NoProxy))
                    page2.set_identity("CREW-01", token2)

                    dl2 = time.monotonic() + 5.0
                    while page2.episodes.count() == 0 and time.monotonic() < dl2:
                        app.processEvents()
                        time.sleep(0.05)

                    self.assertGreaterEqual(page2.episodes.count(), 1)
                    page2.episodes.setCurrentRow(0)
                    dl3 = time.monotonic() + 3.0
                    while not page2.episode_id and time.monotonic() < dl3:
                        app.processEvents()
                        time.sleep(0.05)
                    self.assertEqual(page2.episode_id, created_episode_id)
                    page2.close()
                finally:
                    if proc1.poll() is None:
                        _stop_api(proc1)
                    if proc2 is not None and proc2.poll() is None:
                        _stop_api(proc2)


if __name__ == "__main__":
    unittest.main()
