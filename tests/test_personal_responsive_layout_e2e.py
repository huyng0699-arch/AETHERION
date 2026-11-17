"""Focused E2E test for Q-0087: Personal desktop responsive layout at 1040x650, 1280x720, 1600x900."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from PySide6.QtWidgets import QApplication, QPushButton

from aetherion_desktop.main import AetherionWindow


class PersonalResponsiveLayoutE2ETests(unittest.TestCase):
    def test_no_clipping_at_target_resolutions(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        with patch.dict(os.environ, {"AETHERION_AUTOSTART_LOCAL_SERVER": "0"}):
            app = QApplication.instance() or QApplication([])
            win = AetherionWindow()
            win.access_token = "layout-audit-token"
            win.show()
            win.show_personal()
            app.processEvents()

            page = win.personal_today_page
            self.assertIs(win.operations_home_page.workspace_stack.currentWidget(), page)
            viewport = page.workspace_scroll.viewport()

            for locale in ("vi", "en"):
                win.ui_language = locale
                win._retranslate_shell()
                for width, height in ((1040, 650), (1280, 720), (1600, 900)):
                    win.resize(width, height)
                    app.processEvents()
                    self.assertEqual(win.width(), width)
                    self.assertEqual(win.height(), height)
                    self.assertLessEqual(page.width(), width)
                    self.assertLessEqual(page.height(), height)

                    # Essential header, controls, filter, and table fit within viewport & window via native scrolling
                    for w in (page.hero_title, page.subject_label, page.refresh_button, page.origin_filter, page.table):
                        page.workspace_scroll.ensureWidgetVisible(w)
                        app.processEvents()
                        self.assertTrue(w.isVisible())
                        tl = w.mapTo(viewport, w.rect().topLeft())
                        br = w.mapTo(viewport, w.rect().bottomRight())
                        self.assertGreaterEqual(tl.x(), 0)
                        self.assertGreaterEqual(tl.y(), 0)
                        self.assertLessEqual(br.x(), viewport.width())
                        self.assertLessEqual(br.y(), viewport.height())

                    # Every action must be reachable by scrolling and fit on both axes.
                    # A button outside the scroll viewport is not clipped if scrolling
                    # brings its complete rectangle into view.
                    for btn in page.findChildren(QPushButton):
                        if not btn.isVisible():
                            continue
                        self.assertGreater(btn.width(), 0)
                        self.assertGreater(btn.height(), 0)
                        page.workspace_scroll.ensureWidgetVisible(btn)
                        app.processEvents()
                        top_left = btn.mapTo(viewport, btn.rect().topLeft())
                        bottom_right = btn.mapTo(viewport, btn.rect().bottomRight())
                        with self.subTest(locale=locale, resolution=(width, height), button=btn.objectName()):
                            self.assertGreaterEqual(top_left.x(), 0)
                            self.assertGreaterEqual(top_left.y(), 0)
                            self.assertLessEqual(bottom_right.x(), viewport.width())
                            self.assertLessEqual(bottom_right.y(), viewport.height())
                            win_top_left = btn.mapTo(win, btn.rect().topLeft())
                            win_bottom_right = btn.mapTo(win, btn.rect().bottomRight())
                            self.assertGreaterEqual(win_top_left.x(), 0)
                            self.assertGreaterEqual(win_top_left.y(), 0)
                            self.assertLessEqual(win_bottom_right.x(), width)
                            self.assertLessEqual(win_bottom_right.y(), height)

                    self.assertGreater(page.table.width(), 200)
                    self.assertGreater(page.table.height(), 80)

            win.close()


if __name__ == "__main__":
    unittest.main()
