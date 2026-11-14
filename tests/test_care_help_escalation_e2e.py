"""Focused E2E test for Q-0103: Need Help escalation records assistance request without false delivery claims."""

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


class CareHelpEscalationE2ETests(unittest.TestCase):
    def test_need_help_records_request_without_false_delivery_claim(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        port = _free_port()
        base_url = f"http://127.0.0.1:{port}"
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env["AETHERION_DB_PATH"] = str(Path(tmp) / "care_help_e2e.sqlite3")
            env["AETHERION_BOOTSTRAP_USER"] = "admin_help"
            env["AETHERION_BOOTSTRAP_PASSWORD"] = "TestPass1234!"
            env["AETHERION_BOOTSTRAP_ROLE"] = "admin"

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
                    {"username": "admin_help", "password": "TestPass1234!"},
                )
                token = login_body["access_token"]

                # 1. Record NEED_HELP_NOW assistance request via canonical safety API
                st_post, post_body = _http_json(
                    opener,
                    "POST",
                    f"{base_url}/api/v1/safety/incidents",
                    {
                        "subject_id": "CREW-01",
                        "incident_type": "NEED_HELP_NOW",
                        "note": "Need assistance from Care workflow",
                        "source": "care_ui_help_button",
                    },
                    token=token,
                )
                self.assertEqual(st_post, 201)
                inc = post_body.get("incident", post_body)
                self.assertEqual(inc["incident_type"], "NEED_HELP_NOW")
                self.assertEqual(inc["subject_id"], "CREW-01")
                # Must not falsely claim external delivery without transport evidence
                self.assertNotEqual(inc.get("delivery_state"), "DELIVERED")
                self.assertNotEqual(inc.get("notification_state"), "DELIVERED")

                # 2. Readback from SQLite-backed API
                inc_id = inc["incident_id"]
                st_get, get_body = _http_json(
                    opener,
                    "GET",
                    f"{base_url}/api/v1/safety/incidents/{inc_id}",
                    token=token,
                )
                self.assertEqual(st_get, 200)
                read_inc = get_body.get("incident", get_body)
                self.assertEqual(read_inc["incident_id"], inc_id)
                self.assertEqual(read_inc["incident_type"], "NEED_HELP_NOW")

                # 3. Verify CareJourneyPage.show_safety() triggers safety guidance dialog
                app = QApplication.instance() or QApplication([])
                QNetworkProxyFactory.setUseSystemConfiguration(False)
                QNetworkProxy.setApplicationProxy(QNetworkProxy(QNetworkProxy.ProxyType.NoProxy))
                page = CareJourneyPage(api_url=base_url, locale="en")
                with patch.object(QMessageBox, "warning") as mock_warn:
                    page.show_safety()
                    self.assertTrue(mock_warn.called)
                page.close()
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
