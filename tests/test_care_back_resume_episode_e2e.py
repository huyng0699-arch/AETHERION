"""Focused E2E test for Q-0101: return from another tab and resume same person and episode."""

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

from PySide6.QtNetwork import QNetworkProxy, QNetworkProxyFactory
from PySide6.QtWidgets import QApplication, QMessageBox

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


class CareBackResumeEpisodeE2ETests(unittest.TestCase):
    def test_switch_tabs_and_resume_same_subject_and_episode(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        port = _free_port()
        base_url = f"http://127.0.0.1:{port}"
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env["AETHERION_DB_PATH"] = str(Path(tmp) / "care_resume_e2e.sqlite3")
            env["AETHERION_BOOTSTRAP_USER"] = "admin_resume"
            env["AETHERION_BOOTSTRAP_PASSWORD"] = "TestPass1234!"
            env["AETHERION_BOOTSTRAP_ROLE"] = "admin"

            with patch.dict(
                os.environ,
                {"HTTP_PROXY": "", "HTTPS_PROXY": "", "http_proxy": "", "https_proxy": "", "ALL_PROXY": ""},
            ):
                proc = subprocess.Popen(
                    [sys.executable, "-m", "uvicorn", "aetherion_server.main:app", "--host", "127.0.0.1", "--port", str(port)],
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
                        raise RuntimeError("Server did not start")

                    _, login_body = _http_json(
                        opener,
                        "POST",
                        f"{base_url}/api/v1/auth/login",
                        {"username": "admin_resume", "password": "TestPass1234!"},
                    )
                    token = login_body["access_token"]
                    _http_json(
                        opener,
                        "POST",
                        f"{base_url}/api/v1/subjects",
                        {"subject_id": "CREW-01", "display_name": "Crew One", "scope": "personal", "role_label": "crew"},
                        token=token,
                    )

                    app = QApplication.instance() or QApplication([])
                    QNetworkProxyFactory.setUseSystemConfiguration(False)
                    QNetworkProxy.setApplicationProxy(QNetworkProxy(QNetworkProxy.ProxyType.NoProxy))

                    win = AetherionWindow()
                    win.network.setProxy(QNetworkProxy(QNetworkProxy.ProxyType.NoProxy))
                    win.care_journal_page.api_url = base_url
                    win.care_journal_page.net.setProxy(QNetworkProxy(QNetworkProxy.ProxyType.NoProxy))
                    win.care_journal_page.set_identity("CREW-01", token)
                    for _ in range(10):
                        app.processEvents()
                        time.sleep(0.03)

                    win.care_journal_page.new_concern.setText("Post-EVA shoulder soreness")
                    win.care_journal_page.new_consent.setChecked(True)
                    with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
                        win.care_journal_page.create_episode()

                    dl = time.monotonic() + 5.0
                    while not win.care_journal_page.episode_id and time.monotonic() < dl:
                        app.processEvents()
                        time.sleep(0.05)

                    ep_id = win.care_journal_page.episode_id
                    self.assertTrue(ep_id)

                    # Navigate away to medical library tab and portal tab
                    win.show_medical_library()
                    app.processEvents()
                    self.assertIs(win.pages.currentWidget(), win.medical_library_page)

                    win.show_portal()
                    app.processEvents()
                    self.assertIs(win.pages.currentWidget(), win.portal_page)

                    # Return to care tab and verify same subject and episode resumed
                    win.show_care()
                    app.processEvents()
                    self.assertIs(win.pages.currentWidget(), win.care_journal_page)
                    self.assertEqual(win.care_journal_page.subject_id, "CREW-01")
                    self.assertEqual(win.care_journal_page.episode_id, ep_id)
                    win.close()
                finally:
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


if __name__ == "__main__":
    unittest.main()
