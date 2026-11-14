"""Focused interaction audit for Q-0244: every visible main menu control opens a real view."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from PySide6.QtWidgets import QApplication, QWidget

from aetherion_desktop.main import AetherionWindow


class MainMenuControlsAuditTests(unittest.TestCase):
    def test_every_top_menu_button_and_action_opens_real_page(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        with patch.dict(os.environ, {"AETHERION_AUTOSTART_LOCAL_SERVER": "0"}):
            app = QApplication.instance() or QApplication([])
            win = AetherionWindow()

            # Unauthenticated public Browse routes open inside operations_home_page,
            # while protected health routes stay gated on login_page.
            self.assertIs(win.pages.currentWidget(), win.login_page)
            win.show_personal()
            app.processEvents()
            self.assertIs(win.pages.currentWidget(), win.login_page)

            for public_route in ("care_guide", "medical_library", "demo", "archive"):
                item = win.operations_home_page._objects[public_route]
                win.operations_home_page.navigator.setCurrentItem(item)
                win.operations_home_page.open_action.click()
                app.processEvents()
                self.assertIs(win.pages.currentWidget(), win.operations_home_page)

            # Authenticate in-memory session and audit every navigation handler + Browse entry
            win.access_token = "audit-session-token"
            visited_pages: set[str] = set()

            # Direct top-bar buttons
            for attr in ("nav_ai", "nav_crew", "nav_home"):
                btn = getattr(win, attr)
                self.assertTrue(btn.isEnabled(), f"{attr} should be enabled")
                btn.click()
                app.processEvents()
                self.assertIs(win.pages.currentWidget(), win.operations_home_page)
                cur = win.operations_home_page.workspace_stack.currentWidget()
                self.assertIsInstance(cur, QWidget)
                self.assertGreater(len(cur.findChildren(QWidget)), 0, f"{attr} opened empty widget")
                visited_pages.add(type(cur).__name__)

            # Menu-backed navigation actions
            for attr in ("nav_health", "nav_monitor", "nav_science", "nav_more"):
                btn = getattr(win, attr)
                menu = btn.menu()
                self.assertIsNotNone(menu, f"{attr} missing menu")
                actions = [a for a in menu.actions() if not a.isSeparator()]
                self.assertGreater(len(actions), 0, f"{attr} menu has no actions")
                for act in actions:
                    self.assertTrue(act.isEnabled(), f"{attr} action {act.text()} disabled")
                    act.trigger()
                    app.processEvents()
                    self.assertIs(win.pages.currentWidget(), win.operations_home_page)
                    cur = win.operations_home_page.workspace_stack.currentWidget()
                    self.assertIsInstance(cur, QWidget)
                    self.assertGreater(
                        len(cur.findChildren(QWidget)),
                        0,
                        f"{attr} action {act.text()} opened empty widget",
                    )
                    visited_pages.add(type(cur).__name__)

            # Primary Browse tree opens every hosted module directly
            for route in ("care_guide", "medical_library", "atlas", "settings", "demo", "archive"):
                item = win.operations_home_page._objects[route]
                win.operations_home_page.navigator.setCurrentItem(item)
                win.operations_home_page.open_action.click()
                app.processEvents()
                self.assertIs(win.pages.currentWidget(), win.operations_home_page)
                cur = win.operations_home_page.workspace_stack.currentWidget()
                self.assertIsInstance(cur, QWidget)
                visited_pages.add(type(cur).__name__)

            # Must cover multiple distinct real pages across workspaces and overview
            self.assertGreaterEqual(len(visited_pages), 7)
            win.close()


if __name__ == "__main__":
    unittest.main()
