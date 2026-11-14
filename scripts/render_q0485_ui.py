"""Capture the integrated native Q-0485 screens in an offscreen Qt session.

Screenshots are CI render evidence, not Windows desktop captures. The NASA
archive uses the repository's real historical source; synthetic data are shown
only after the explicit SIMULATED briefing action and remain in demo SQLite.
"""
from __future__ import annotations

import os
from pathlib import Path
import sys
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
# Keep the expected offline server state explicit in this isolated preview.
os.environ.setdefault("AETHERION_API_URL", "http://127.0.0.1:1")

ROOT = Path(__file__).resolve().parents[1]
PREVIEW_HOME = ROOT / "artifacts" / "q0485-ui-preview" / "ephemeral-home"
PREVIEW_HOME.mkdir(parents=True, exist_ok=True)
os.environ["HOME"] = str(PREVIEW_HOME)
os.environ["XDG_CONFIG_HOME"] = str(PREVIEW_HOME / "config")
if os.name == "nt":
    os.environ["USERPROFILE"] = str(PREVIEW_HOME)
    os.environ["APPDATA"] = str(PREVIEW_HOME / "AppData" / "Roaming")
    os.environ["LOCALAPPDATA"] = str(PREVIEW_HOME / "AppData" / "Local")
sys.path.insert(0, str(ROOT / "apps" / "desktop" / "src"))

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QFont
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from aetherion_desktop.main import AetherionWindow


def capture(window: AetherionWindow, folder: Path, name: str,
            width: int, height: int) -> None:
    window.resize(width, height)
    window.show()
    QTest.qWait(120)
    QApplication.processEvents()
    path = folder / f"{name}-{width}x{height}.png"
    if not window.grab().save(str(path), "PNG"):
        raise RuntimeError(f"Could not save preview image: {path}")
    print(f"RENDERED {path.relative_to(ROOT)}")


def wait_until(predicate, description: str, timeout_seconds: float = 30.0) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        QApplication.processEvents()
        if predicate():
            return
        QTest.qWait(50)
    raise RuntimeError(f"Timed out waiting for {description}")


def main() -> int:
    output = ROOT / "artifacts" / "q0485-ui-preview"
    output.mkdir(parents=True, exist_ok=True)

    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(
        QSettings.Format.IniFormat, QSettings.Scope.UserScope,
        str(PREVIEW_HOME / "qt-settings"),
    )
    settings = QSettings("TRUY TINH", "AETHERION")
    settings.setValue("ui/language", "vi")
    settings.setValue("visual/theme", "daybreak")
    settings.setValue("visual/mode", "light")
    settings.setValue("visual/font_family", "Arial")
    settings.setValue("visual/font_size", 10)
    settings.setValue("visual/reduce_motion", True)

    app = QApplication.instance() or QApplication([])
    app.setApplicationName("AETHERION Q-0485 offscreen UI preview")
    app.setFont(QFont("Arial", 10))
    window = AetherionWindow()

    # Cold-start Mission Operations at the design reference and minimum sizes.
    capture(window, output, "mission-home-vi", 1600, 900)
    capture(window, output, "mission-home-vi-minimum", 1040, 650)

    # Confirm the existing Monitor page uses one visible conductor in its shell.
    window.show_monitor()
    QTest.qWait(250)
    if window.operations_home_page.time_conductor.isVisible():
        raise RuntimeError("Duplicate Home Time Conductor is visible on Monitoring")
    capture(window, output, "monitoring-openmct-shell", 1040, 650)

    # Exercise the actual prominent Demo control and explicit Start action.
    QTest.mouseClick(window.operations_home_page.demo, Qt.MouseButton.LeftButton)
    QTest.qWait(100)
    if (window.operations_home_page.workspace_stack.currentWidget()
            is not window.simulated_briefing_page):
        raise RuntimeError("Demo CTA did not open the SIMULATED briefing")
    if window.operations_home_page.navigator.currentItem().data(
            0, Qt.ItemDataRole.UserRole) != "demo":
        raise RuntimeError("Browse selection did not follow the Demo briefing")
    capture(window, output, "simulated-briefing-vi", 1360, 850)

    QTest.mouseClick(window.simulated_briefing_page.start, Qt.MouseButton.LeftButton)
    wait_until(
        lambda: window.synthetic_patient_page.ready,
        "the isolated SIMULATED database to load",
    )
    if not window.synthetic_patient_page.ready:
        raise RuntimeError(
            "SIMULATED experience did not load: "
            + window.synthetic_patient_page.state.text()
        )
    capture(window, output, "simulated-patient-experience-vi", 1360, 850)

    # The source table uses the authentic repository-bundled NASA observations.
    window.operations_home_page._choose("archive")
    capture(window, output, "nasa-ma7-source-table-vi", 1360, 850)

    # Also retain the richer NASA module's source briefing as a separate entry.
    window.show_hackathon_demo()
    QTest.qWait(150)
    if window.operations_home_page.navigator.currentItem().data(
            0, Qt.ItemDataRole.UserRole) != "archive":
        raise RuntimeError("Browse selection did not follow NASA MA-7")
    capture(window, output, "nasa-ma7-archive-entry-vi", 1360, 850)

    # Capture the same first screen in English to inspect localization geometry.
    window.preferences.set_language("en")
    window.ui_language = "en"
    window._retranslate_shell()
    window.show_portal()
    QTest.qWait(100)
    capture(window, output, "mission-home-en", 1360, 850)

    window.close()
    app.processEvents()
    print(f"PREVIEW_COUNT {len(tuple(output.glob('*.png')))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
