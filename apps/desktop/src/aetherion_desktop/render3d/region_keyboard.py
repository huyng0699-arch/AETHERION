"""Native Atlas region navigation without a mouse (Q-0133).

Works with the *existing* model selector and canonical QtInteractor; activating
a region triggers its genuine checked mesh-loading handler. The shortcuts do
not invent body structures, bypass rights checks or move patient data.
"""
from __future__ import annotations


def next_region_index(current: int, count: int, direction: int) -> int | None:
    """Choose a real existing row; wrap, but never invent an entry."""
    if isinstance(current, bool) or isinstance(count, bool):
        raise ValueError("Atlas row count/index must be integers")
    if not isinstance(current, int) or not isinstance(count, int) or count < 0:
        raise ValueError("Invalid Atlas selector state")
    if direction not in (-1, 1):
        raise ValueError("Direction must be backward or forward")
    if count == 0:
        return None
    return 0 if current < 0 else (current + direction) % count


def install_region_keyboard(viewer, selector):
    """Scope focus and next/previous mesh to an actual native VTK viewport.

    Ctrl+arrows/orbit/zoom remain owned by Q-0124. Alt+N/Alt+P select the
    actual next/previous model via QComboBox.currentIndexChanged; Alt+M
    focuses the native region selector so arrows work without the mouse.
    """
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QKeySequence, QShortcut
    from PySide6.QtWidgets import QComboBox, QWidget

    if not isinstance(viewer, QWidget) or not isinstance(selector, QComboBox):
        raise TypeError("Expected real QtInteractor and region selector")
    previous = getattr(viewer, "_aetherion_region_shortcuts", None)
    if previous is not None:
        return previous

    def select(direction: int):
        if not viewer.isVisible() or not selector.isEnabled():
            return
        index = next_region_index(selector.currentIndex(), selector.count(), direction)
        if index is not None and index != selector.currentIndex():
            selector.setCurrentIndex(index)  # calls Atlas._select with real source ID

    def focus_selector():
        if viewer.isVisible() and selector.isEnabled():
            selector.setFocus(Qt.FocusReason.ShortcutFocusReason)

    actions = (
        ("Alt+N", lambda: select(1)),
        ("Alt+P", lambda: select(-1)),
        ("Alt+M", focus_selector),
    )
    bindings = []
    for key, callback in actions:
        shortcut = QShortcut(QKeySequence(key), viewer)
        shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        shortcut.setAutoRepeat(False)
        shortcut.activated.connect(callback)
        bindings.append(shortcut)
    viewer._aetherion_region_shortcuts = tuple(bindings)
    return viewer._aetherion_region_shortcuts
