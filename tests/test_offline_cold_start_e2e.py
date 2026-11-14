"""Focused E2E test for Q-0006: offline cold start of local API and native Qt desktop without downloads."""

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

from PySide6.QtNetwork import QNetworkProxy
from PySide6.QtWidgets import QApplication

from aetherion_desktop.main import AetherionWindow

REPO_ROOT = Path(__file__).resolve().parents[1]


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


class OfflineColdStartE2ETests(unittest.TestCase):
    def test_offline_cold_start_api_and_qt_without_downloads(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        port = _free_port()
        base_url = f"http://127.0.0.1:{port}"
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            for proxy_var in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"):
                env[proxy_var] = ""
            env["NO_PROXY"] = "127.0.0.1,localhost"
            env["AETHERION_DB_PATH"] = str(Path(tmp) / "offline_cold_start.sqlite3")
            env["AETHERION_ALLOW_CLOUD_AI"] = "false"
            env["AETHERION_BOOTSTRAP_USER"] = "admin_offline"
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
                health_body = {}
                while time.monotonic() < deadline:
                    try:
                        with opener.open(f"{base_url}/health", timeout=2.0) as resp:
                            health_body = json.loads(resp.read().decode("utf-8"))
                            if resp.status == 200 and health_body.get("status") == "ok":
                                break
                    except Exception:
                        time.sleep(0.15)
                else:
                    err = proc.stderr.read().decode(errors="replace") if proc.stderr else ""
                    raise RuntimeError(f"Offline API failed to start: poll={proc.poll()} stderr={err[:500]}")

                # Verify local offline medical library endpoint serves locally without internet
                with opener.open(f"{base_url}/api/v1/knowledge/status", timeout=3.0) as resp:
                    self.assertEqual(resp.status, 200)
                    status_body = json.loads(resp.read().decode("utf-8"))
                    self.assertEqual(status_body["json_articles"], 116)
                    self.assertEqual(status_body["symptom_labels"], 819)

                # Block non-loopback DNS resolution in-process during Qt cold start
                orig_getaddrinfo = socket.getaddrinfo

                def _loopback_only_getaddrinfo(host, *args, **kwargs):
                    if host not in ("127.0.0.1", "localhost", "::1", None):
                        raise OSError(f"External network disabled in offline cold start test: {host}")
                    return orig_getaddrinfo(host, *args, **kwargs)

                socket.getaddrinfo = _loopback_only_getaddrinfo
                try:
                    app = QApplication.instance() or QApplication([])
                    QNetworkProxy.setApplicationProxy(QNetworkProxy(QNetworkProxy.ProxyType.NoProxy))
                    win = AetherionWindow()
                    win.network.setProxy(QNetworkProxy(QNetworkProxy.ProxyType.NoProxy))

                    dl = time.monotonic() + 3.0
                    while win._server_state == "checking" and time.monotonic() < dl:
                        app.processEvents()
                        time.sleep(0.05)

                    win.api_url = base_url
                    win.check_server()
                    dl2 = time.monotonic() + 5.0
                    while win._server_state != "online" and time.monotonic() < dl2:
                        app.processEvents()
                        time.sleep(0.05)

                    self.assertEqual(win._server_state, "online")
                    self.assertIs(win.pages.currentWidget(), win.portal_page)
                    win.close()
                finally:
                    socket.getaddrinfo = orig_getaddrinfo
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
