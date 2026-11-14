"""Focused interaction audit for Q-0244: every visible main menu control opens a real view."""

from __future__ import annotations

import os
from pathlib import Path
import unittest

from PySide6.QtWidgets import QApplication, QWidget

from aetherion_desktop.main import AetherionWindow


class MainMenuControlsAuditTests(unittest.TestCase):
    def test_every_top_menu_button_and_action_opens_real_page(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        app = QApplication.instance() or QApplication([])
        win = AetherionWindow()

        visited_pages: set[str] = set()

        # Direct top-bar buttons
        for attr in ("nav_ai", "nav_crew", "nav_home"):
            btn = getattr(win, attr)
            self.assertTrue(btn.isEnabled(), f"{attr} should be enabled")
            btn.click()
            app.processEvents()
            cur = win.pages.currentWidget()
            self.assertIsInstance(cur, QWidget)
            self.assertGreater(len(cur.findChildren(QWidget)), 0, f"{attr} opened empty widget")
            visited_pages.add(type(cur).__name__)

        # Menu-backed top-bar buttons
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
                cur = win.pages.currentWidget()
                self.assertIsInstance(cur, QWidget)
                self.assertGreater(
                    len(cur.findChildren(QWidget)),
                    0,
                    f"{attr} action {act.text()} opened empty widget",
                )
                visited_pages.add(type(cur).__name__)

        # Must cover multiple distinct real pages (PortalPage, InterviewWorkspace, MissionControlPage, etc.)
        self.assertGreaterEqual(len(visited_pages), 7)
        win.close()


if __name__ == "__main__":
    unittest.main()
