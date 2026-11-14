"""Focused Qt/offscreen integration evidence for Q-0485.

This runs the native Qt widgets in a virtual platform. The PNGs are render
artifacts only; they do not represent a visible Windows desktop acceptance.
"""
from __future__ import annotations

import os
from pathlib import Path
import tempfile
import time
import sys


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    temp_home = tempfile.TemporaryDirectory(prefix="aetherion-q0485-")
    os.environ["HOME"] = temp_home.name
    os.environ["USERPROFILE"] = temp_home.name
    os.environ["XDG_CONFIG_HOME"] = str(Path(temp_home.name) / ".config")
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    os.environ["AETHERION_API_URL"] = "http://127.0.0.1:9"
    sys.path.insert(0, str(root / "apps" / "desktop" / "src"))

    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication

    from aetherion_desktop.features.demo.nasa_ma7 import load_real_nasa_data
    from aetherion_desktop.features.demo.synthetic_patients import demo_path, demo_stats
    from aetherion_desktop.main import AetherionWindow
    from aetherion_desktop.mission_ops_home import ROUTE_IDS

    app = QApplication.instance() or QApplication([])
    window = AetherionWindow()
    window.show()
    app.processEvents()

    assert window.pages.currentWidget() is window.ops_home_page, "cold start did not open Mission Operations"
    assert set(window.ops_home_page._route_items) == set(ROUTE_IDS), "Home route tree is incomplete"
    assert window.ops_home_page.primary_demo.isVisible(), "first-view Demo CTA is not visible"

    screenshot_dir = Path(os.environ.get("Q0485_SCREENSHOT_DIR", root / "outputs" / "q0485-desktop-smoke"))
    screenshot_dir.mkdir(parents=True, exist_ok=True)

    def capture(name: str, width: int, height: int) -> None:
        window.resize(width, height)
        app.processEvents()
        image = window.grab()
        if image.isNull():
            raise AssertionError(f"Qt returned an empty render for {name}")
        target = screenshot_dir / f"{name}-{width}x{height}.png"
        if not image.save(str(target)):
            raise AssertionError(f"Unable to save render artifact: {target}")

    capture("mission-operations", 1280, 720)
    capture("mission-operations", 1600, 900)

    targets = {
        "mission": window.mission_control_page,
        "health": window.personal_today_page,
        "monitor": window.monitor_page,
        "ecg": window.ecg_page,
        "assistant": window.assistant_page,
        "interview": window.symptom_page,
        "care": window.care_journal_page,
        "science": window.knowledge_browser_page,
        "hazards": window.nasa_explore_page,
        "medical_library": window.medical_library_page,
        "atlas": window.atlas_page,
        "crew": window.mission_control_page,
        "settings": window.settings_page,
    }
    for route in ROUTE_IDS:
        window.open_home_route(route)
        app.processEvents()
        assert window.pages.currentWidget() is targets[route], f"route failed: {route}"

    window.show_portal()
    app.processEvents()
    assert window.pages.currentWidget() is window.ops_home_page, "Home compatibility action reopened the old Portal"

    # The real NASA historical archive remains a distinct, source-identified route.
    window.ops_home_page.nasa_archive_requested.emit()
    app.processEvents()
    assert window.pages.currentWidget() is window.hackathon_demo_page
    nasa = load_real_nasa_data()
    assert nasa["dataset_id"] == "NASA-MA7-MERCURY-1962"
    assert nasa["is_synthetic"] is False and nasa["is_live"] is False
    capture("nasa-ma7-archive", 1280, 720)

    # Demo is a separate user action; the isolated SQLite must not exist yet.
    home_before = window.pages.currentWidget()
    assert home_before is window.hackathon_demo_page
    window.show_portal()
    QTest.mouseClick(window.ops_home_page.primary_demo, Qt.MouseButton.LeftButton)
    app.processEvents()
    assert window.pages.currentWidget() is window.demo_briefing_page
    assert "SIMULATED" in window.demo_briefing_page.badge.text().upper()
    assert not demo_path().exists(), "synthetic database was created before the explicit Start action"
    capture("simulated-briefing", 1280, 720)

    QTest.mouseClick(window.demo_briefing_page.start_button, Qt.MouseButton.LeftButton)
    deadline = time.monotonic() + 30
    while not window.synthetic_demo_page.ready and time.monotonic() < deadline:
        app.processEvents()
        QTest.qWait(25)
    assert window.pages.currentWidget() is window.synthetic_demo_page
    assert window.synthetic_demo_page.ready, "Patient Demo did not load"
    stats = demo_stats()
    assert stats["is_synthetic"] is True
    assert (stats["subjects"], stats["days"], stats["metrics"]) == (5, 540, 12)
    assert stats["observations"] == 31610, f"SQLite readback row count changed: {stats['observations']}"
    assert demo_path().resolve().is_relative_to(Path(temp_home.name).resolve())
    assert window.synthetic_demo_page.subject_combo.count() == 5
    assert window.synthetic_demo_page.tabs.count() == 5
    assert "AETHERION-SYNTHETIC-PATIENTS-V1" in window.synthetic_demo_page.source_info.text()
    capture("simulated-patient-demo", 1280, 720)

    window.synthetic_demo_page.back_requested.emit()
    app.processEvents()
    assert window.pages.currentWidget() is window.demo_briefing_page
    window.demo_briefing_page.back_requested.emit()
    app.processEvents()
    assert window.pages.currentWidget() is window.ops_home_page

    initial_locale = window.ui_language
    window._change_language()
    assert window.ui_language != initial_locale
    assert window.ops_home_page.language == window.ui_language
    assert window.demo_briefing_page.language == window.ui_language
    window._change_language()
    assert window.ui_language == initial_locale

    print("Q-0485 headless integration PASS")
    print(f"Routes checked: {len(targets)}")
    print(f"NASA archive: {nasa['dataset_id']} (historical, non-live)")
    print(f"Isolated SQLite readback: {stats['subjects']} subjects, {stats['days']} days, "
          f"{stats['metrics']} metrics, {stats['observations']} observations")
    print(f"Render artifacts: {screenshot_dir}")
    window.close()
    app.processEvents()
    temp_home.cleanup()


if __name__ == "__main__":
    main()
