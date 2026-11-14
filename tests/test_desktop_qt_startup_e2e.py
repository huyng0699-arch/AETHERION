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
            env["AETHERION_BOOTSTRAP_USER"] = "admin_qt_e2e"
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
                _wait_health(base_url)
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
                    drain_deadline = time.monotonic() + 2.0
                    while win._server_state == "checking" and time.monotonic() < drain_deadline:
                        app.processEvents()
                        time.sleep(0.02)
                    win.api_url = base_url

                    # 1. Unauthenticated cold start begins on LoginPage
                    self.assertIs(win.pages.currentWidget(), win.login_page)

                    # 2. Authenticate via native LoginPage against the live test server
                    win.login_page.server_input.setText(base_url)
                    win.login_page.username_input.setText("admin_qt_e2e")
                    win.login_page.password_input.setText("TestPass1234!")
                    win.login_page.sign_in_button.click()
                    auth_deadline = time.monotonic() + 6.0
                    while (win.pages.currentWidget() is win.login_page) and time.monotonic() < auth_deadline:
                        app.processEvents()
                        time.sleep(0.03)
                    self.assertTrue(win.access_token)
                    self.assertIs(win.pages.currentWidget(), win.operations_home_page)
                    self.assertEqual(win.operations_home_page.workspace_stack.currentIndex(), 0)

                    # 3. Top navigation handlers switch workspace views and return to overview
                    win.nav_ai.click()
                    app.processEvents()
                    self.assertIs(
                        win.operations_home_page.workspace_stack.currentWidget(),
                        win.assistant_page,
                    )
                    win.nav_home.click()
                    app.processEvents()
                    self.assertEqual(win.operations_home_page.workspace_stack.currentIndex(), 0)

                    # 4. Live server health check completes against running uvicorn
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
