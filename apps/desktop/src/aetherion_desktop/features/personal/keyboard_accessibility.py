"""Bilingual native keyboard and screen-reader bindings for Personal Today.

Q-0088 prepares an adapter for the existing, authenticated Personal page.
It does not create fake buttons, bypass server authorization or alter records.
The parent page must call apply_locale() whenever its UI language changes.
"""
from __future__ import annotations

from ...localization import normalize_locale, tr

TILE_ORDER = ("heart", "activity", "sleep", "mass", "energy", "mood")


def keyboard_focus_order() -> tuple[str, ...]:
    """Semantic order, independent of VI/EN rendered labels."""
    return ("refresh",) + tuple("tile." + tile for tile in TILE_ORDER) + ("origin_filter", "observations")


class PersonalKeyboardAccessibility:
    """Install native Qt focus navigation on existing authorized page controls."""

    def __init__(self, page):
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QKeySequence, QShortcut
        from PySide6.QtWidgets import QComboBox, QPushButton, QTableWidget, QWidget

        if not isinstance(page, QWidget):
            raise TypeError("Personal page must be a native QWidget")
        if not isinstance(getattr(page, "refresh_button", None), QPushButton):
            raise ValueError("Personal refresh control missing")
        if not isinstance(getattr(page, "origin_filter", None), QComboBox):
            raise ValueError("Personal source filter missing")
        if not isinstance(getattr(page, "table", None), QTableWidget):
            raise ValueError("Personal observation table missing")
        tiles = getattr(page, "metric_tiles", None)
        if not isinstance(tiles, dict) or any(tile not in tiles for tile in TILE_ORDER):
            raise ValueError("Missing one or more Personal metric tile controls")

        self.page = page
        self.tile_buttons = {}
        for tile in TILE_ORDER:
            parts = tiles[tile]
            if not isinstance(parts, tuple) or len(parts) != 3 or not isinstance(parts[2], QPushButton):
                raise ValueError("Invalid Personal tile action")
            if not page.isAncestorOf(parts[2]):
                raise ValueError("Personal tile action belongs to another page")
            self.tile_buttons[tile] = parts[2]
        controls = [page.refresh_button] + list(self.tile_buttons.values()) + [
            page.origin_filter, page.table
        ]
        for item in controls:
            item.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        for previous, following in zip(controls, controls[1:]):
            QWidget.setTabOrder(previous, following)
        # Actual buttons already support Enter/Space: preserve their genuine
        # click handlers instead of installing a simulated action.
        page.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._shortcuts = []
        self._bind_shortcut(QShortcut, QKeySequence, Qt, "Ctrl+R", page,
                            self._refresh_current_subject)
        self._bind_shortcut(QShortcut, QKeySequence, Qt, "Ctrl+L", page,
                            self._focus_filter)
        self._bind_shortcut(QShortcut, QKeySequence, Qt, "Return", page.table,
                            self._select_current_row)
        self._bind_shortcut(QShortcut, QKeySequence, Qt, "Escape", page.table,
                            self._leave_table)
        self.apply_locale(getattr(page, "ui_language", "vi"))

    def _bind_shortcut(self, shortcut_type, sequence_type, qt, keys, parent, action):
        shortcut = shortcut_type(sequence_type(keys), parent)
        shortcut.setContext(qt.ShortcutContext.WidgetWithChildrenShortcut)
        shortcut.setAutoRepeat(False)
        shortcut.activated.connect(action)
        self._shortcuts.append(shortcut)

    def _refresh_current_subject(self):
        button = self.page.refresh_button
        if button.isEnabled() and button.isVisibleTo(self.page):
            button.click()  # invokes the existing authenticated refresh logic

    def _focus_filter(self):
        widget = self.page.origin_filter
        if widget.isEnabled():
            widget.setFocus()

    def _select_current_row(self):
        table = self.page.table
        row = table.currentRow()
        if not table.isEnabled() or row < 0 or row >= table.rowCount():
            return
        table.selectRow(row)
        item = table.item(row, 0)
        if item is not None:
            table.scrollToItem(item)

    def _leave_table(self):
        """Escape dismisses the selection, never logs out or changes subject."""
        self.page.table.clearSelection()
        self._focus_filter()

    def apply_locale(self, locale: str) -> None:
        """Re-label accessibility chrome without refetching/mutating health data."""
        locale = normalize_locale(locale)
        page = self.page
        page.refresh_button.setAccessibleName(tr(locale, "personal.refreshAccessible"))
        page.origin_filter.setAccessibleName(tr(locale, "personal.filterAccessible"))
        page.table.setAccessibleName(tr(locale, "mission.dataTitle"))
        page.table.setAccessibleDescription(tr(locale, "mission.note.recorded"))
        page.subject_label.setAccessibleName(tr(locale, "personal.subjectAccessible"))
        for tile, button in self.tile_buttons.items():
            title = tr(locale, "personal.tile." + tile)
            button.setAccessibleName(tr(locale, "personal.recordType") + " · " + title)
            button.setToolTip(title)


def install_personal_keyboard_accessibility(page):
    """Idempotently prepare existing Personal Qt controls; return the controller.

    Call `controller.apply_locale(language)` from the host page's set_locale().
    This component does NOT claim complete integrated Windows accessibility.
    """
    previous = getattr(page, "_aetherion_personal_keyboard", None)
    if previous is not None:
        previous.apply_locale(getattr(page, "ui_language", "vi"))
        return previous
    controller = PersonalKeyboardAccessibility(page)
    page._aetherion_personal_keyboard = controller
    return controller
