"""Focused E2E test for Q-0087: Personal desktop responsive layout at 1040x650, 1280x720, 1600x900."""

from __future__ import annotations

import os
import unittest

from PySide6.QtWidgets import QApplication, QPushButton

from aetherion_desktop.main import AetherionWindow


class PersonalResponsiveLayoutE2ETests(unittest.TestCase):
    def test_no_clipping_at_target_resolutions(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        app = QApplication.instance() or QApplication([])
        win = AetherionWindow()
        win.show()
        win.show_personal()
        app.processEvents()

        page = win.personal_today_page
        self.assertIs(win.pages.currentWidget(), page)

        for width, height in ((1040, 650), (1280, 720), (1600, 900)):
            win.resize(width, height)
            app.processEvents()
            self.assertEqual(win.width(), width)
            self.assertEqual(win.height(), height)
            self.assertLessEqual(page.width(), width)
            self.assertLessEqual(page.height(), height)
            self.assertGreater(page.table.width(), 200)
            self.assertGreater(page.table.height(), 80)

            for btn in page.findChildren(QPushButton):
                if btn.isVisible():
                    self.assertGreater(btn.width(), 0)
                    self.assertGreater(btn.height(), 0)
                    top_left = btn.mapTo(win, btn.rect().topLeft())
                    bottom_right = btn.mapTo(win, btn.rect().bottomRight())
                    self.assertGreaterEqual(top_left.x(), 0)
                    self.assertLessEqual(bottom_right.x(), width)

        win.close()


if __name__ == "__main__":
    unittest.main()
