"""Native Mission Control keyboard navigation and visible-focus affordances.

The parent must pass actual Qt controls. Keyboard shortcuts are parent-scoped,
never global hooks and never authorization bypasses. No mock buttons or data.
"""
from __future__ import annotations

from collections.abc import Mapping

# (control ID, accessible name, focus/action shortcut)
ESSENTIAL_CONTROLS = (
    ("username", "Local account username", "Ctrl+1"),
    ("password", "Local account password", "Ctrl+2"),
    ("sign_in", "Sign in to authorized Mission data", "Alt+S"),
    ("subject_input", "Authorized crew subject identifier", "Ctrl+3"),
    ("open_subject", "Open exact authorized subject", "Alt+O"),
    ("refresh", "Refresh recorded observations", "Alt+R"),
    ("subjects", "Select an authorized subject", "Ctrl+4"),
    ("observations", "Source backed observations and provenance", "Ctrl+5"),
)
OPTIONAL_PORTAL = ("back_to_portal", "Return to Portal", "Alt+P")
_ACTIONS = frozenset({"sign_in", "open_subject", "refresh", "back_to_portal"})
_FOCUS_STYLE = "\nQPushButton:focus,QLineEdit:focus,QListWidget:focus,QTableWidget:focus { border: 2px solid #4dd7ec; }\n"


def shortcut_plan(*, portal_button: bool = False) -> tuple[tuple[str, str, str], ...]:
    """Auditable input-to-action map; no Qt import needed to inspect it."""
    plan = ESSENTIAL_CONTROLS + ((OPTIONAL_PORTAL,) if portal_button else ())
    shortcuts = [item[2] for item in plan]
    if len(shortcuts) != len(set(shortcuts)):
        raise ValueError("duplicate keyboard shortcut")
    return plan


def install_mission_keyboard_navigation(parent, controls: Mapping[str, object]):
    """Bind shortcuts and tab focus to EXISTING visible Mission Qt widgets.

    Caller must supply username/password fields, sign-in/open/refresh buttons,
    subject input/list and provenance table. Optional `back_to_portal` is a
    real navigation button. Shortcut dispatch only clicks an enabled, visible
    native button (or focuses the existing enabled control).

    Return QShortcut objects for diagnostics; each is owned by `parent`.
    The page's existing authentication logic remains the sole authority.
    """
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QKeySequence, QShortcut
    from PySide6.QtWidgets import QWidget

    if not isinstance(parent, QWidget):
        raise TypeError("parent must be a native Qt widget")
    if not isinstance(controls, Mapping):
        raise TypeError("controls must be a mapping of real Qt widgets")
    plan = shortcut_plan(portal_button="back_to_portal" in controls)
    missing = [name for name, _, _ in plan if name not in controls]
    if missing:
        raise ValueError("missing essential Mission controls: " + ", ".join(missing))
    widgets = []
    for name, label, key in plan:
        widget = controls[name]
        if not isinstance(widget, QWidget) or widget is parent or not parent.isAncestorOf(widget):
            raise ValueError(f"{name} must be a child widget of the Mission page")
        widget.setAccessibleName(label)
        widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        widget.setToolTip(f"{label} ({key})")
        current = widget.styleSheet()
        if _FOCUS_STYLE.strip() not in current:
            widget.setStyleSheet(current + _FOCUS_STYLE)
        widgets.append(widget)

    for previous, following in zip(widgets, widgets[1:]):
        QWidget.setTabOrder(previous, following)

    shortcuts = []
    for (name, _, key), widget in zip(plan, widgets):
        shortcut = QShortcut(QKeySequence(key), parent)
        shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        shortcut.setAutoRepeat(False)

        def activate(w=widget, action=name):
            # Never trigger hidden or disabled actions through a shortcut.
            if not w.isEnabled() or not w.isVisibleTo(parent):
                return
            if action in _ACTIONS:
                w.click()
            else:
                w.setFocus(Qt.FocusReason.ShortcutFocusReason)

        shortcut.activated.connect(activate)
        shortcuts.append(shortcut)
    return tuple(shortcuts)
