"""Focused E2E test for Q-0004: independent API & desktop processes + offline/reconnect detection."""

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


def _wait_health(opener, base_url: str, proc: subprocess.Popen, timeout: float = 10.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with opener.open(f"{base_url}/health", timeout=2.0) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                if resp.status == 200 and body.get("status") == "ok":
                    return
        except Exception:
            time.sleep(0.15)
    err = proc.stderr.read().decode(errors="replace") if proc.stderr else ""
    raise RuntimeError(f"Server did not become healthy: poll={proc.poll()} stderr={err[:500]}")


def _wait_state(app: QApplication, win: AetherionWindow, target: str, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while win._server_state != target and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.05)


class ProcessSeparationReconnectE2ETests(unittest.TestCase):
    def test_separate_launch_scripts_and_offline_reconnect_detection(self) -> None:
        server_ps1 = (REPO_ROOT / "scripts" / "start_server.ps1").read_text(encoding="utf-8")
        desktop_ps1 = (REPO_ROOT / "scripts" / "start_desktop.ps1").read_text(encoding="utf-8")
        self.assertIn("aetherion_server.main:app", server_ps1)
        self.assertIn("aetherion_desktop", desktop_ps1)
        self.assertNotIn("aetherion_desktop", server_ps1)
        self.assertNotIn("uvicorn", desktop_ps1)

        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        port = _free_port()
        base_url = f"http://127.0.0.1:{port}"
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env["AETHERION_DB_PATH"] = str(Path(tmp) / "process_sep_e2e.sqlite3")
            env["AETHERION_BOOTSTRAP_USER"] = "admin_e2e"
            env["AETHERION_BOOTSTRAP_PASSWORD"] = "TestPass1234!"
            env["AETHERION_BOOTSTRAP_ROLE"] = "admin"

            def _start_api() -> subprocess.Popen:
                return subprocess.Popen(
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

            proc1 = _start_api()
            proc2 = None
            try:
                _wait_health(opener, base_url, proc1)

                app = QApplication.instance() or QApplication([])
                QNetworkProxy.setApplicationProxy(QNetworkProxy(QNetworkProxy.ProxyType.NoProxy))
                win = AetherionWindow()
                win.network.setProxy(QNetworkProxy(QNetworkProxy.ProxyType.NoProxy))

                # Drain initial startup check_server() before switching api_url
                dl = time.monotonic() + 3.0
                while win._server_state == "checking" and time.monotonic() < dl:
                    app.processEvents()
                    time.sleep(0.05)

                win.api_url = base_url

                # 1. Connected -> online
                win.check_server()
                _wait_state(app, win, "online")
                self.assertEqual(win._server_state, "online")

                # 2. Disconnected API -> offline
                _stop_api(proc1)
                win.check_server()
                _wait_state(app, win, "offline")
                self.assertEqual(win._server_state, "offline")

                # 3. Restart API on same port -> reconnect detected (online)
                proc2 = _start_api()
                _wait_health(opener, base_url, proc2)
                win.check_server()
                _wait_state(app, win, "online")
                self.assertEqual(win._server_state, "online")
                win.close()
            finally:
                if proc1.poll() is None:
                    _stop_api(proc1)
                if proc2 is not None and proc2.poll() is None:
                    _stop_api(proc2)


if __name__ == "__main__":
    unittest.main()
