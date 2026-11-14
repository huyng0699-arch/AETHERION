"""Focused verification for Q-0487: LoginPage loopback gate, StartupRuntime isolation, and closeEvent cleanup."""

from __future__ import annotations

import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from PySide6.QtWidgets import QApplication

from aetherion_desktop.login_page import _normalize_loopback_base_url
from aetherion_desktop.main import AetherionWindow
from aetherion_desktop.startup_runtime import StartupRuntime, _may_autostart_server


class StartupRuntimeQ0487Tests(unittest.TestCase):
    def test_autostart_guard_only_allows_default_loopback_http(self) -> None:
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("AETHERION_AUTOSTART_LOCAL_SERVER", None)
            os.environ.pop("AETHERION_API_URL", None)
            self.assertTrue(_may_autostart_server("http://127.0.0.1:8765"))
            self.assertTrue(_may_autostart_server("http://127.0.0.1:8765/"))
            self.assertFalse(_may_autostart_server("http://192.168.1.50:8765"))
            self.assertFalse(_may_autostart_server("https://127.0.0.1:8765"))
            self.assertFalse(_may_autostart_server("http://127.0.0.1:8765/api"))
            self.assertFalse(_may_autostart_server("http://user@127.0.0.1:8765"))

        with patch.dict(os.environ, {"AETHERION_AUTOSTART_LOCAL_SERVER": "0"}):
            self.assertFalse(_may_autostart_server("http://127.0.0.1:8765"))

        with patch.dict(os.environ, {"AETHERION_API_URL": "http://127.0.0.1:18000"}):
            self.assertFalse(_may_autostart_server("http://127.0.0.1:8765"))

    def test_login_url_normalization_rejects_non_loopback(self) -> None:
        self.assertEqual(_normalize_loopback_base_url("http://127.0.0.1:8765/"), "http://127.0.0.1:8765")
        self.assertEqual(_normalize_loopback_base_url("https://localhost:8443"), "https://localhost:8443")
        self.assertEqual(_normalize_loopback_base_url("http://[::1]:8765"), "http://[::1]:8765")
        for bad in (
            "",
            "https://example.com",
            "http://192.168.0.10:8765",
            "ftp://127.0.0.1:8765",
            "http://127.0.0.1:8765/api",
            "http://127.0.0.1:8765?x=1",
        ):
            with self.assertRaises(ValueError):
                _normalize_loopback_base_url(bad)

    def test_demo_sqlite_seed_and_late_callback_guard(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as tmp:
            tmp_home = Path(tmp)
            with patch.dict(
                os.environ,
                {
                    "HOME": str(tmp_home),
                    "XDG_CONFIG_HOME": str(tmp_home / "config"),
                    "AETHERION_AUTOSTART_LOCAL_SERVER": "0",
                    "AETHERION_API_URL": "http://127.0.0.1:1",
                },
            ):
                # 1. StartupRuntime asynchronously seeds only synthetic_patients_v1.sqlite3
                runtime = StartupRuntime("http://127.0.0.1:1")
                results: list[bool] = []
                runtime.request_demo_ready(results.append)
                deadline = time.monotonic() + 25.0
                while not results and time.monotonic() < deadline:
                    app.processEvents()
                    time.sleep(0.05)
                runtime.stop()
                self.assertEqual(results, [True])
                demo_db = tmp_home / ".aetherion" / "demo" / "synthetic_patients_v1.sqlite3"
                self.assertTrue(demo_db.is_file())

                # 2. AetherionWindow starts on LoginPage, blocks unauthenticated health routes,
                # allows Demo walkthrough, and ignores late Demo callback after navigating away.
                win = AetherionWindow()
                self.assertIs(win.pages.currentWidget(), win.login_page)
                win.show_monitor()
                app.processEvents()
                self.assertIs(win.pages.currentWidget(), win.login_page)

                win.login_page.demo_button.click()
                app.processEvents()
                self.assertIs(win.pages.currentWidget(), win.operations_home_page)
                self.assertIs(
                    win.operations_home_page.workspace_stack.currentWidget(),
                    win.simulated_briefing_page,
                )

                # Navigate away before late callback arrives -> must NOT yank user back to Demo
                win.show_care_guide()
                app.processEvents()
                self.assertIs(
                    win.operations_home_page.workspace_stack.currentWidget(),
                    win.care_page,
                )
                win._finish_simulated_demo_start(True)
                app.processEvents()
                self.assertIs(
                    win.operations_home_page.workspace_stack.currentWidget(),
                    win.care_page,
                )
                win.close()


if __name__ == "__main__":
    unittest.main()
