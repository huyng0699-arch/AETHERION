"""Focused E2E test for Q-0243: Desktop Qt startup and top navigation with a running server."""

from __future__ import annotations

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


def _wait_health(base_url: str, timeout: float = 10.0) -> None:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    deadline = time.monotonic() + timeout
    last_err: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with opener.open(f"{base_url}/health", timeout=1.0) as resp:
                if resp.status == 200:
                    return
        except Exception as exc:
            last_err = exc
            time.sleep(0.15)
    raise RuntimeError(f"Server did not become healthy at {base_url}: {last_err}")


class DesktopQtStartupE2ETests(unittest.TestCase):
    def test_qt_startup_portal_top_nav_and_live_server_check(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        port = _free_port()
        base_url = f"http://127.0.0.1:{port}"
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env["AETHERION_DB_PATH"] = str(Path(tmp) / "desktop_e2e.sqlite3")
            env["AETHERION_API_URL"] = base_url
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
                _wait_health(base_url)
                app = QApplication.instance() or QApplication([])
                QNetworkProxy.setApplicationProxy(QNetworkProxy(QNetworkProxy.ProxyType.NoProxy))
                win = AetherionWindow()
                win.network.setProxy(QNetworkProxy(QNetworkProxy.ProxyType.NoProxy))
                drain_deadline = time.monotonic() + 2.0
                while win._server_state == "checking" and time.monotonic() < drain_deadline:
                    app.processEvents()
                    time.sleep(0.02)
                win.api_url = base_url

                # 1. Starts on 5-card Portal
                self.assertIs(win.pages.currentWidget(), win.portal_page)

                # 2. Top navigation buttons switch real pages and return home
                win.nav_ai.click()
                self.assertIsNot(win.pages.currentWidget(), win.portal_page)
                win.nav_home.click()
                self.assertIs(win.pages.currentWidget(), win.portal_page)

                # 3. Live server health check completes against running uvicorn
                win.check_server()
                deadline = time.monotonic() + 5.0
                while win._server_state == "checking" and time.monotonic() < deadline:
                    app.processEvents()
                    time.sleep(0.05)
                self.assertNotEqual(win._server_state, "checking")
                self.assertIn(win._server_state, {"ready", "connected", "online", "ok"})
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
