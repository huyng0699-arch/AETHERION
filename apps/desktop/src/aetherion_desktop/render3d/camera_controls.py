"""Real VTK camera transforms and viewer-scoped native Qt keyboard controls.

Q-0124: changing the vtkCamera is a real 3D pose update, not a 2D UI animation.
No global shortcut, automatic patient inference or second rendering backend.
"""
from __future__ import annotations

from math import isfinite, sqrt
from typing import Any


def _unit(v: tuple[float, float, float]) -> tuple[float, float, float]:
    length = sqrt(sum(x * x for x in v))
    if not isfinite(length) or length <= 1e-9:
        raise ValueError("Degenerate camera direction")
    return tuple(x / length for x in v)


def _cross(a, b) -> tuple[float, float, float]:
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def move_camera(camera: Any, action: str) -> None:
    """Apply an explicit, bounded motion to a real vtkCamera in world space.

    Camera target and position move together on pan; no mesh coordinates,
    data sources, clinical records or material properties are changed.
    """
    if action in {"orbit_left", "orbit_right", "orbit_up", "orbit_down"}:
        azimuth = {"orbit_left": -30.0, "orbit_right": 30.0}.get(action, 0.0)
        elevation = {"orbit_up": 20.0, "orbit_down": -20.0}.get(action, 0.0)
        if azimuth:
            camera.Azimuth(azimuth)
        if elevation:
            camera.Elevation(elevation)
        camera.OrthogonalizeViewUp()
    elif action in {"pan_left", "pan_right", "pan_up", "pan_down"}:
        pos = tuple(float(v) for v in camera.GetPosition())
        target = tuple(float(v) for v in camera.GetFocalPoint())
        direction = _unit(tuple(target[i] - pos[i] for i in range(3)))
        up = _unit(tuple(float(v) for v in camera.GetViewUp()))
        right = _unit(_cross(direction, up))
        distance = float(camera.GetDistance())
        if not isfinite(distance) or distance <= 1e-9:
            raise ValueError("Cannot pan degenerate camera")
        scale = distance * 0.06
        dx = {"pan_left": -1.0, "pan_right": 1.0}.get(action, 0.0)
        dy = {"pan_down": -1.0, "pan_up": 1.0}.get(action, 0.0)
        offset = tuple(scale * (dx * right[i] + dy * up[i]) for i in range(3))
        camera.SetPosition(*(pos[i] + offset[i] for i in range(3)))
        camera.SetFocalPoint(*(target[i] + offset[i] for i in range(3)))
    elif action == "zoom_in":
        camera.Zoom(1.2)
    elif action == "zoom_out":
        camera.Zoom(1.0 / 1.2)
    else:
        raise ValueError("Unknown native camera action")
    camera.Modified()


# Focused on the actual VTK viewport, not entire app.
CAMERA_KEYS = (
    ("Ctrl+Left", "orbit_left"),
    ("Ctrl+Right", "orbit_right"),
    ("Ctrl+Up", "orbit_up"),
    ("Ctrl+Down", "orbit_down"),
    ("Alt+Left", "pan_left"),
    ("Alt+Right", "pan_right"),
    ("Alt+Up", "pan_up"),
    ("Alt+Down", "pan_down"),
    ("Ctrl+=", "zoom_in"),
    ("Ctrl+-", "zoom_out"),
    ("Ctrl+0", "reset"),
)


def install_camera_shortcuts(viewer: Any):
    """Attach shortcuts once to a real PyVistaQt QtInteractor QWidget.

    Use this only after the native QtInteractor has been constructed. The
    existing mouse orbit/pan/scroll and clickable Reset Camera button remain.
    """
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QKeySequence, QShortcut
    from PySide6.QtWidgets import QWidget

    if not isinstance(viewer, QWidget):
        raise TypeError("Expected a native QtInteractor QWidget")
    previous = getattr(viewer, "_aetherion_camera_shortcuts", None)
    if previous is not None:
        return previous

    shortcuts = []
    for keys, action in CAMERA_KEYS:
        shortcut = QShortcut(QKeySequence(keys), viewer)
        shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        shortcut.setAutoRepeat(False)

        def on_key(name=action):
            if not viewer.isEnabled() or not viewer.isVisible():
                return
            if name == "reset":
                viewer.reset_camera()
            else:
                move_camera(viewer.camera, name)
            viewer.render()

        shortcut.activated.connect(on_key)
        shortcuts.append(shortcut)
    viewer._aetherion_camera_shortcuts = tuple(shortcuts)
    viewer.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    return viewer._aetherion_camera_shortcuts
