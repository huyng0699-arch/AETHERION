"""Reusable native Qt accessibility controls for crew assistance.

This module does not send an incident, infer medical state, or bypass authorization.
Callers must connect the returned button to their existing authenticated action.
"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QPushButton, QWidget


_LABELS = {
    "vi": {
        "request": "Yêu cầu hỗ trợ",
        "acknowledge": "Xác nhận đã xem",
        "cancel": "Quay lại",
    },
    "en": {
        "request": "Request assistance",
        "acknowledge": "Acknowledge",
        "cancel": "Back",
    },
}


def accessible_action_button(
    action: str,
    locale: str,
    on_activate: Callable[[], None],
    *,
    parent: QWidget | None = None,
) -> QPushButton:
    """Return a keyboard-focusable, large-target native action.

    The callback is supplied by the host; no network or clinical action is
    performed implicitly. Unsupported locales fall back to English.
    """
    if action not in _LABELS["en"]:
        raise ValueError(f"Unsupported assistance action: {action}")
    if not callable(on_activate):
        raise TypeError("on_activate must be callable")
    language = locale if locale in _LABELS else "en"
    label = _LABELS[language][action]
    button = QPushButton(label, parent)
    button.setObjectName(f"assistance_{action}_button")
    button.setAccessibleName(label)
    button.setAccessibleDescription(
        "Kích hoạt bằng Enter hoặc Space" if language == "vi"
        else "Activate with Enter or Space"
    )
    button.setMinimumSize(160, 48)
    button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    button.clicked.connect(lambda _checked=False: on_activate())
    return button


def bind_assistance_shortcut(
    host: QWidget,
    button: QPushButton,
    *,
    key_sequence: str = "Alt+A",
) -> QShortcut:
    """Provide an optional scoped keyboard alternative to pointer activation.

    Retain the returned shortcut (or parent it to host) for its lifetime.
    The shortcut clicks the existing enabled button, so disabled or denied
    actions cannot be activated through this keyboard route.
    """
    shortcut = QShortcut(QKeySequence(key_sequence), host)
    shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
    shortcut.activated.connect(lambda: button.click() if button.isEnabled() else None)
    return shortcut
