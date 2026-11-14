#!/usr/bin/env python3
"""Q-0253: Windows-only interactive DPI/keyboard acceptance probe.

Run in a *real* Windows desktop session, not QT_QPA_PLATFORM=offscreen.
This is a probe, not a substitute for a human screen/keyboard review.
"""
from __future__ import annotations

import json
import os
import platform
import sys
from datetime import datetime, timezone


def main() -> int:
    if sys.platform != "win32" or os.environ.get("QT_QPA_PLATFORM", "").lower() in {
        "offscreen", "minimal", "vnc", "headless"
    }:
        print("BLOCKED: native Windows interactive Qt session required", file=sys.stderr)
        return 2

    try:
        from PySide6.QtCore import Qt
        from PySide6.QtTest import QTest
        from PySide6.QtWidgets import QApplication, QPushButton
        from aetherion_desktop.main import AetherionWindow
    except (ImportError, RuntimeError) as exc:
        print(f"BLOCKED: Qt application unavailable: {exc}", file=sys.stderr)
        return 2

    app = QApplication.instance() or QApplication(sys.argv)
    if app.platformName().lower() != "windows":
        print(f"BLOCKED: Qt platform {app.platformName()} is not native Windows", file=sys.stderr)
        return 2

    screen = app.primaryScreen()
    ratio = float(screen.devicePixelRatio())
    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "os": platform.platform(),
        "qt_platform": app.platformName(),
        "screen_dpr": ratio,
        "locale_results": [],
    }
    failures = []
    if not 1.45 <= ratio <= 1.55:
        failures.append("Display scaling is not 150%; set Windows scale to 150% and rerun")

    for locale in ("vi", "en"):
        window = None
        try:
            window = AetherionWindow()
            # Set locale through existing user-facing setting rather than editing data.
            if hasattr(window, "set_ui_language"):
                window.set_ui_language(locale)
            elif hasattr(window, "set_language"):
                window.set_language(locale)
            else:
                # QSettings is not mutated by the probe; report lack of a switch.
                failures.append(f"{locale}: language-switch API not found")
            for width, height in ((1040, 650), (1280, 720), (1600, 900)):
                window.resize(width, height)
                window.show()
                app.processEvents()
                actual = window.size()
                if actual.width() < width or actual.height() < height:
                    failures.append(f"{locale}: window did not reach {width}x{height}")
                # Focused visible top-bar controls; scrollable page descendants
                # are intentionally not treated as clipped merely for scrolling.
                controls = [
                    b for b in window.top_bar.findChildren(QPushButton)
                    if b.isVisible() and b.isEnabled()
                ]
                if not controls:
                    failures.append(f"{locale}: no visible enabled top-bar controls")
                for button in controls:
                    top = button.mapTo(window, button.rect().topLeft())
                    bottom = button.mapTo(window, button.rect().bottomRight())
                    if min(top.x(), top.y()) < 0 or bottom.x() >= window.width() or bottom.y() >= window.height():
                        failures.append(f"{locale}: clipped top-bar control {button.objectName()}")
                if controls:
                    controls[0].setFocus(Qt.FocusReason.TabFocusReason)
                    QTest.keyClick(controls[0], Qt.Key.Key_Tab)
                    app.processEvents()
                    focused = app.focusWidget()
                    if focused is None or focused is controls[0]:
                        failures.append(f"{locale}: Tab did not advance keyboard focus")
                report["locale_results"].append({
                    "locale": locale, "requested_size": [width, height],
                    "actual_size": [actual.width(), actual.height()],
                    "visible_topbar_buttons": len(controls),
                })
                window.hide()
        except Exception as exc:
            failures.append(f"{locale}: runtime exception: {type(exc).__name__}: {exc}")
        finally:
            if window is not None:
                window.close()
                window.deleteLater()
                app.processEvents()

    report["failures"] = failures
    report["result"] = "FAIL" if failures else "PROBE_PASS_REQUIRES_HUMAN_REVIEW"
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
