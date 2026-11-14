"""Capture the integrated native Q-0485 / Q-0487 screens in an offscreen Qt session.

Screenshots are headless Qt render evidence, not Windows desktop captures. The NASA
archive uses the repository's real historical source; synthetic data are shown
only after the explicit SIMULATED briefing action and remain in demo SQLite.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
# Keep offline server state explicit and disable implicit port 8765 autostart in preview renders.
os.environ.setdefault("AETHERION_API_URL", "http://127.0.0.1:1")
os.environ.setdefault("AETHERION_AUTOSTART_LOCAL_SERVER", "0")

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
from PySide6.QtWidgets import QApplication, QTreeWidgetItemIterator

from aetherion_desktop.main import AetherionWindow


def capture(
    window: AetherionWindow,
    folder: Path,
    name: str,
    width: int,
    height: int,
) -> Path:
    window.resize(width, height)
    window.show()
    QTest.qWait(120)
    QApplication.processEvents()
    path = folder / f"{name}-{width}x{height}.png"
    if not window.grab().save(str(path), "PNG"):
        raise RuntimeError(f"Could not save preview image: {path}")
    print(f"RENDERED {path}")
    return path


def wait_until(predicate, description: str, timeout_seconds: float = 30.0) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        QApplication.processEvents()
        if predicate():
            return
        QTest.qWait(50)
    raise RuntimeError(f"Timed out waiting for {description}")




def open_visible_browse_route(window: AetherionWindow, route: str) -> None:
    """Select a visible Browse row and use its visible Open control."""
    navigator = window.operations_home_page.navigator
    iterator = QTreeWidgetItemIterator(navigator)
    target = None
    while iterator.value() is not None:
        candidate = iterator.value()
        if candidate.data(0, Qt.ItemDataRole.UserRole) == route:
            target = candidate
            break
        iterator += 1
    if target is None:
        raise RuntimeError(f"Browse route is missing: {route}")
    navigator.scrollToItem(target)
    item_rect = navigator.visualItemRect(target)
    QTest.mouseClick(
        navigator.viewport(), Qt.MouseButton.LeftButton, pos=item_rect.center()
    )
    QTest.mouseClick(
        window.operations_home_page.open_action, Qt.MouseButton.LeftButton
    )
    QTest.qWait(100)


def capture_both_sizes(window, output: Path, name: str) -> None:
    capture(window, output, name, 1360, 850)
    capture(window, output, f"{name}-minimum", 1040, 650)

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render native AETHERION Qt screens offscreen.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "artifacts" / "q0485-ui-preview",
        help="Directory where rendered PNG screenshots are written.",
    )
    args = parser.parse_args(argv)
    output: Path = args.output_dir
    output.mkdir(parents=True, exist_ok=True)

    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(
        QSettings.Format.IniFormat,
        QSettings.Scope.UserScope,
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
    app.setApplicationName("AETHERION offscreen UI preview")
    app.setFont(QFont("Arial", 10))
    window = AetherionWindow()

    # Public Home is the real first screen; the SIMULATED action is visible immediately.
    if window.pages.currentWidget() is not window.operations_home_page:
        raise RuntimeError("Cold start did not display public Mission Operations")
    if window.operations_home_page.navigator.currentItem().data(0, Qt.ItemDataRole.UserRole) != "home":
        raise RuntimeError("Cold start did not select the Mission Workspace overview")
    if "SIMULATED" not in window.operations_home_page.demo.text().upper() and "GIẢ LẬP" not in window.operations_home_page.demo.text().upper():
        raise RuntimeError("First-screen Demo CTA is not labelled as simulated")

    def render_locale(locale: str, suffix: str, include_patient: bool = False) -> None:
        if locale != window.ui_language:
            window.preferences.set_language(locale)
            window.ui_language = locale
            window._retranslate_shell()

        window.show_portal()
        capture_both_sizes(window, output, f"mission-home-{suffix}")

        QTest.mouseClick(window.operations_home_page.nasa_full, Qt.MouseButton.LeftButton)
        QTest.qWait(150)
        if (
            window.pages.currentWidget() is not window.operations_home_page
            or window.operations_home_page.workspace_stack.currentWidget() is not window.hackathon_demo_page
            or window.hackathon_demo_page.pages.currentWidget() is not window.hackathon_demo_page.briefing
        ):
            raise RuntimeError("Home NASA archive action did not open the historical MA-7 briefing")
        capture_both_sizes(window, output, f"nasa-ma7-archive-{suffix}")

        QTest.keyClick(window, Qt.Key.Key_Home, Qt.KeyboardModifier.AltModifier)
        QTest.qWait(80)
        QTest.mouseClick(window.operations_home_page.demo, Qt.MouseButton.LeftButton)
        QTest.qWait(120)
        if window.operations_home_page.workspace_stack.currentWidget() is not window.simulated_briefing_page:
            raise RuntimeError("First-screen SIMULATED Demo did not open its briefing")
        if window.operations_home_page.navigator.currentItem().data(0, Qt.ItemDataRole.UserRole) != "demo":
            raise RuntimeError("Browse selection did not follow the SIMULATED briefing")
        capture_both_sizes(window, output, f"simulated-briefing-{suffix}")

        if include_patient:
            QTest.mouseClick(window.simulated_briefing_page.start, Qt.MouseButton.LeftButton)
            wait_until(
                lambda: window.synthetic_patient_page.ready,
                "the isolated SIMULATED database to load",
            )
            capture(window, output, f"simulated-patient-experience-{suffix}", 1360, 850)

        QTest.keyClick(window, Qt.Key.Key_Home, Qt.KeyboardModifier.AltModifier)
        QTest.qWait(80)
        open_visible_browse_route(window, "monitor")
        if window.pages.currentWidget() is not window.login_page:
            raise RuntimeError("Selecting protected Monitoring did not open Login")
        if window._pending_protected_route != "monitor":
            raise RuntimeError("Protected Monitoring destination was not retained")
        if locale == "vi" and window.login_page.demo_button.text() != "Kho lưu trữ NASA MA-7":
            raise RuntimeError("Login archive action is not clearly named in Vietnamese")
        if locale == "en" and window.login_page.demo_button.text() != "NASA MA-7 archive":
            raise RuntimeError("Login archive action is not clearly named in English")
        capture_both_sizes(window, output, f"protected-route-login-{suffix}")

        QTest.mouseClick(window.login_page.demo_button, Qt.MouseButton.LeftButton)
        QTest.qWait(120)
        if window.operations_home_page.workspace_stack.currentWidget() is not window.hackathon_demo_page:
            raise RuntimeError("Explicit NASA MA-7 archive action did not open NASA source")
        if window._pending_protected_route is not None:
            raise RuntimeError("Choosing the public archive left a stale protected route")

    render_locale("vi", "vi", include_patient=True)
    render_locale("en", "en")

    # Authenticated route resume is exercised by the focused startup test with a successful
    # bearer-authenticated /subjects response; this offscreen preview never injects a token.
    window.close()
    app.processEvents()
    print(f"PREVIEW_COUNT {len(tuple(output.glob('*.png')))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
