"""Focused verification for Q-0487: LoginPage loopback gate, StartupRuntime isolation, and closeEvent cleanup."""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from PySide6.QtCore import QDateTime
from PySide6.QtWidgets import QApplication

from aetherion_desktop.login_page import _normalize_loopback_base_url
from aetherion_desktop.mission_ops_home import MissionOperationsHome
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
                # StartupRuntime asynchronously seeds only the isolated demo SQLite.
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

                # The native public Operations shell is the first screen. Protected
                # real-data routes still stop at Login until a session is verified.
                win = AetherionWindow()
                self.assertIs(win.pages.currentWidget(), win.operations_home_page)
                win.open_operations_route("monitor")
                app.processEvents()
                self.assertIs(win.pages.currentWidget(), win.login_page)

                # The Login-page archive action is explicitly NASA MA-7, not Demo.
                win.login_page.demo_button.click()
                app.processEvents()
                self.assertIs(win.pages.currentWidget(), win.operations_home_page)
                self.assertIs(
                    win.operations_home_page.workspace_stack.currentWidget(),
                    win.hackathon_demo_page,
                )

                # The first-screen SIMULATED Demo opens its separate briefing.
                win.show_portal()
                win.operations_home_page.demo.click()
                app.processEvents()
                self.assertIs(
                    win.operations_home_page.workspace_stack.currentWidget(),
                    win.simulated_briefing_page,
                )

                # Navigating to the NASA archive before a late seed callback arrives
                # must not replace the user's chosen public screen.
                win.show_hackathon_demo()
                app.processEvents()
                self.assertIs(
                    win.operations_home_page.workspace_stack.currentWidget(),
                    win.hackathon_demo_page,
                )
                win._finish_simulated_demo_start(True)
                app.processEvents()
                self.assertIs(
                    win.operations_home_page.workspace_stack.currentWidget(),
                    win.hackathon_demo_page,
                )
                win.close()

    def test_home_utc_range_matches_monitoring_min_and_max(self) -> None:
        """Home accepts the same inclusive 1-minute..366-day bounds as Q-0477."""
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        app = QApplication.instance() or QApplication([])
        messages = {
            "en": (
                "UTC range must be at least 1 minute.",
                "UTC range cannot exceed 366 days.",
            ),
            "vi": (
                "Khoảng UTC phải dài ít nhất 1 phút.",
                "Khoảng UTC không được vượt quá 366 ngày.",
            ),
        }

        for locale, (too_short_message, too_long_message) in messages.items():
            with self.subTest(locale=locale):
                home = MissionOperationsHome(locale=locale)
                # Preserve millisecond precision in the widget used for the min-boundary test.
                home.begin_utc.setDisplayFormat("yyyy-MM-dd HH:mm:ss.zzz 'UTC'")
                home.end_utc.setDisplayFormat("yyyy-MM-dd HH:mm:ss.zzz 'UTC'")
                emitted: list[tuple[str, str]] = []
                home.time_range_changed.connect(
                    lambda start, end: emitted.append((start, end))
                )
                previously_applied = (home._start_epoch, home._end_epoch)
                start = QDateTime.currentDateTimeUtc()

                home.begin_utc.setDateTime(start)
                home.end_utc.setDateTime(start.addMSecs(59_999))
                home.apply_utc_window()
                self.assertEqual(home.window_status.text(), too_short_message)
                self.assertEqual(
                    (home._start_epoch, home._end_epoch), previously_applied
                )
                self.assertEqual(emitted, [])

                exactly_minimum = start.addSecs(60)
                home.end_utc.setDateTime(exactly_minimum)
                home.apply_utc_window()
                self.assertEqual(
                    (home._start_epoch, home._end_epoch),
                    (start.toSecsSinceEpoch(), exactly_minimum.toSecsSinceEpoch()),
                )
                self.assertEqual(len(emitted), 1)

                accepted_minimum = (home._start_epoch, home._end_epoch)
                home.end_utc.setDateTime(start.addDays(366).addMSecs(1))
                home.apply_utc_window()
                self.assertEqual(home.window_status.text(), too_long_message)
                self.assertEqual(
                    (home._start_epoch, home._end_epoch), accepted_minimum
                )
                self.assertEqual(len(emitted), 1)

                exactly_maximum = start.addDays(366)
                home.end_utc.setDateTime(exactly_maximum)
                home.apply_utc_window()
                self.assertEqual(
                    (home._start_epoch, home._end_epoch),
                    (start.toSecsSinceEpoch(), exactly_maximum.toSecsSinceEpoch()),
                )
                self.assertEqual(len(emitted), 2)
                home.close()

    def test_auth_me_resumes_route_and_rejected_session_is_cleared(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        app = QApplication.instance() or QApplication([])

        class AuthHandler(BaseHTTPRequestHandler):
            def _reply(self, status: int, payload: dict | None = None) -> None:
                body = json.dumps(payload or {}).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self) -> None:
                if self.path == "/api/v1/auth/me":
                    self.server.auth_me_requests.append(self.headers.get("Authorization", ""))
                    if self.headers.get("Authorization") != "Bearer verified-bearer":
                        self._reply(401, {"detail": "unauthorized"})
                    elif self.server.auth_status == 200:
                        self._reply(200, {
                            "username": "operator",
                            "role": "crew",
                            "allowed_subjects": ["CREW-01"],
                            "expires_at": "2030-01-01T00:00:00Z",
                        })
                    else:
                        self._reply(self.server.auth_status, {"detail": "unauthorized"})
                elif self.path == "/health":
                    self._reply(200, {"status": "ok"})
                elif self.path.startswith("/api/v1/observations?"):
                    subject = "CREW-01"
                    self._reply(200, {"subject_id": subject, "observations": []})
                elif self.path == "/api/v1/subjects/CREW-01":
                    self._reply(200, {"subject": {
                        "subject_id": "CREW-01", "display_name": "Crew One"
                    }})
                else:
                    self._reply(404, {"detail": "not found"})

            def do_POST(self) -> None:
                if self.path == "/api/v1/auth/logout":
                    self.server.logout_requests += 1
                    self.send_response(204)
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                else:
                    self._reply(404, {"detail": "not found"})

            def log_message(self, *_args) -> None:
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), AuthHandler)
        server.auth_status = 200
        server.auth_me_requests = []
        server.logout_requests = 0
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        base_url = f"http://127.0.0.1:{server.server_port}"
        temporary_home = tempfile.TemporaryDirectory()
        windows = []
        try:
            with patch.dict(
                os.environ,
                {
                    "AETHERION_AUTOSTART_LOCAL_SERVER": "0",
                    "AETHERION_API_URL": base_url,
                    "HOME": temporary_home.name,
                    "XDG_CONFIG_HOME": str(Path(temporary_home.name) / "config"),
                },
            ):
                win = AetherionWindow()
                windows.append(win)
                win.monitor_page.refresh = lambda: None
                win.open_operations_route("monitor")
                self.assertIs(win.pages.currentWidget(), win.login_page)
                win.login_page.authenticated.emit(
                    {"access_token": "verified-bearer", "user": {"username": "operator"}},
                    base_url,
                )
                deadline = time.monotonic() + 5.0
                while not getattr(win, "_session_verified", False) and time.monotonic() < deadline:
                    app.processEvents()
                    time.sleep(0.01)
                app.processEvents()
                self.assertTrue(getattr(win, "_session_verified", False))
                self.assertEqual(server.auth_me_requests, ["Bearer verified-bearer"])
                self.assertEqual(win.access_token, "verified-bearer")
                self.assertEqual(getattr(win, "allowed_subject_ids", ()), ("CREW-01",))
                self.assertIs(win.pages.currentWidget(), win.operations_home_page)
                self.assertIs(
                    win.operations_home_page.workspace_stack.currentWidget(),
                    win.monitor_page,
                )
                self.assertEqual(win.mission_control_page._token, "verified-bearer")
                self.assertEqual(win.mission_control_page.api_url, base_url)

                win.assistant_page.set_identity("CREW-01", "verified-bearer")
                win.show_assistant()
                self.assertEqual(win.assistant_page._identity, "account:operator")
                win.sign_out()
                self.assertEqual(win.access_token, "")
                self.assertFalse(getattr(win, "_session_verified", False))
                self.assertEqual(win.mission_control_page._token, "")
                self.assertEqual(win.mission_control_page._subjects, [])
                deadline = time.monotonic() + 2.0
                while server.logout_requests < 1 and time.monotonic() < deadline:
                    app.processEvents()
                    time.sleep(0.01)
                self.assertEqual(server.logout_requests, 1)

                # A rejected /auth/me response must revoke/clear the login token and
                # leave later selections gated at Login.
                server.auth_status = 403
                win.open_operations_route("monitor")
                win.login_page.authenticated.emit(
                    {"access_token": "verified-bearer", "user": {"username": "operator"}},
                    base_url,
                )
                deadline = time.monotonic() + 5.0
                while win.access_token and time.monotonic() < deadline:
                    app.processEvents()
                    time.sleep(0.01)
                app.processEvents()
                self.assertEqual(win.access_token, "")
                self.assertFalse(getattr(win, "_session_verified", False))
                self.assertEqual(win.mission_control_page._token, "")
                win.open_operations_route("monitor")
                self.assertIs(win.pages.currentWidget(), win.login_page)
                deadline = time.monotonic() + 2.0
                while server.logout_requests < 2 and time.monotonic() < deadline:
                    app.processEvents()
                    time.sleep(0.01)
                self.assertGreaterEqual(server.logout_requests, 2)
        finally:
            for win in windows:
                win.close()
            server.shutdown()
            server.server_close()
            server_thread.join(timeout=2.0)
            temporary_home.cleanup()

    def test_mission_control_reuses_verified_session_and_clears_it(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        app = QApplication.instance() or QApplication([])
        with patch.dict(
            os.environ,
            {
                "AETHERION_AUTOSTART_LOCAL_SERVER": "0",
                "AETHERION_API_URL": "http://127.0.0.1:1",
            },
        ):
            win = AetherionWindow()
            page = win.mission_control_page
            page.set_locale("en")
            auth_container = page.username.parentWidget()
            login_actions = [
                button for button in auth_container.findChildren(type(page.open_personal_button))
                if button.objectName() == "primaryAction"
            ]
            self.assertEqual(len(login_actions), 1)
            login_action = login_actions[0]
            with patch.object(page, "refresh_subject") as refresh_subject:
                page.set_verified_session(
                    "verified-bearer",
                    {"username": "operator", "role": "crew", "allowed_subjects": ["CREW-01"]},
                    "http://127.0.0.1:18000",
                )
                self.assertEqual(page._token, "verified-bearer")
                self.assertEqual(page.api_url, "http://127.0.0.1:18000")
                self.assertFalse(login_action.isEnabled())
                self.assertEqual(page._subjects, ["CREW-01"])
                self.assertEqual(page._selected_subject(), "CREW-01")
                refresh_subject.assert_called_once()

                for allowed in ([], ["CREW-01", "CREW-02"]):
                    page.set_verified_session(
                        "verified-bearer",
                        {"username": "operator", "role": "crew", "allowed_subjects": allowed},
                        "http://127.0.0.1:18000",
                    )
                    self.assertEqual(page._selected_subject(), "")
                    self.assertFalse(page.open_personal_button.isEnabled())
                self.assertEqual(page._subjects, ["CREW-01", "CREW-02"])

                page.clear_session()
                self.assertEqual(page._token, "")
                self.assertEqual(page._subjects, [])
                self.assertEqual(page._selected_subject(), "")
                self.assertFalse(page.open_personal_button.isEnabled())
                self.assertTrue(page.username.isEnabled())
                self.assertTrue(login_action.isEnabled())
            win.close()


if __name__ == "__main__":
    unittest.main()
