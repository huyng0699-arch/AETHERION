"""Focused offscreen interaction and render check for Q-0486.

The only records below are explicitly fictional engineering fixtures. They are
not patient data, NASA data, sensor output, or real measurements.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "desktop" / "src"))

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget

from aetherion_desktop.telemetry_plot import TelemetryPlot, connectable_pairs


@dataclass(frozen=True)
class EngineeringPreviewPoint:
    metric: str
    value: float
    unit: str
    observed_at: datetime
    source_id: str
    scope: str
    quality: str
    verification: str


def make_preview() -> tuple[list[EngineeringPreviewPoint], datetime]:
    start = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0) - timedelta(hours=14)
    rows: list[EngineeringPreviewPoint] = []

    def add(source: str, hours: float, value: float, quality: str = "UNVERIFIED") -> None:
        rows.append(EngineeringPreviewPoint(
            metric="engineering_demo_signal",
            value=value,
            unit="arb",
            observed_at=start + timedelta(hours=hours),
            source_id=source,
            scope="engineering_test",
            quality=quality,
            verification="TEST_FIXTURE",
        ))

    alpha = [0, 1, 2, 3, 4, 12, 13, 14]
    alpha_values = [1.4, 2.2, 1.8, 3.1, 2.7, 4.0, 3.6, 4.7]
    for hour, value in zip(alpha, alpha_values):
        add("ENGINEERING_FIXTURE_ALPHA", hour, value)

    beta = [0.5, 1.5, 2.5, 3.5, 12.5, 13.5]
    beta_values = [3.1, 2.8, 3.7, 3.3, 2.2, 3.0]
    for hour, value in zip(beta, beta_values):
        add("ENGINEERING_FIXTURE_BETA", hour, value)

    # A value with an ERROR state must remain in the table-compatible filter
    # result but must not be drawn as a chart point or line.
    add("ENGINEERING_FIXTURE_ALPHA", 8, 99.0, quality="ERROR")
    return rows, start


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("artifacts/q0486-telemetry-plot.png"))
    args = parser.parse_args()

    app = QApplication.instance() or QApplication([])
    app.setApplicationName("AETHERION Q-0486 offscreen preview")
    records, start = make_preview()

    # Gap behavior is explicit and visual-only. The eight-hour hiatus remains
    # disconnected even though both endpoints are visible engineering fixtures.
    assert connectable_pairs(records, None) == []
    pairs = connectable_pairs(records, timedelta(hours=2))
    assert pairs
    assert all(
        (right.observed_at - left.observed_at) <= timedelta(hours=2)
        for left, right in pairs
    )
    assert not any(
        left.source_id == "ENGINEERING_FIXTURE_ALPHA"
        and left.observed_at == start + timedelta(hours=4)
        and right.observed_at == start + timedelta(hours=12)
        for left, right in pairs
    )

    window = QWidget()
    window.setWindowTitle("AETHERION · telemetry component preview")
    window.resize(1280, 760)
    layout = QVBoxLayout(window)
    banner = QLabel(
        "ENGINEERING PREVIEW · FICTIONAL DATA · NOT A HEALTH OR NASA RECORD"
    )
    banner.setStyleSheet(
        "QLabel { background: #7B2F2F; color: white; padding: 10px 14px; "
        "font-size: 15px; font-weight: 700; border-radius: 6px; }"
    )
    layout.addWidget(banner)
    chart = TelemetryPlot(
        records, locale="en", max_visual_gap=timedelta(hours=2)
    )
    layout.addWidget(chart, 1)

    snapshots: list[list[object]] = []
    chart.filtered_records_changed.connect(lambda rows: snapshots.append(list(rows)))
    window.show()
    app.processEvents()

    # Range changes expose the same filtered list a companion table should use.
    chart.set_time_bounds(start + timedelta(hours=1), start + timedelta(hours=4))
    filtered = chart.filtered_records()
    assert filtered == snapshots[-1]
    assert filtered
    assert all(
        start + timedelta(hours=1) <= row.observed_at <= start + timedelta(hours=4)
        for row in filtered
    )

    # Source filter is shared with the table contract; locale labels are bilingual.
    alpha_index = chart.source_selector.findData("ENGINEERING_FIXTURE_ALPHA")
    assert alpha_index > 0
    chart.source_selector.setCurrentIndex(alpha_index)
    assert all(row.source_id == "ENGINEERING_FIXTURE_ALPHA" for row in chart.filtered_records())
    chart.set_locale("vi")
    assert chart.range_label.text() == "Khoảng thời gian · UTC"
    chart.set_locale("en")
    chart.reset_view()
    chart.source_selector.setCurrentIndex(0)
    app.processEvents()

    # The invalid-status record remains available to the table contract but is
    # excluded from drawable points.
    assert any(row.quality == "ERROR" for row in chart.filtered_records())
    assert all(point.quality in {"READY", "UNVERIFIED", "STALE"} for point in chart.canvas.points)
    assert len(chart.canvas.points) == len(records) - 1

    # Exercise the actual Qt hover and click path at a plotted point.
    point_record = records[2]
    position = chart.canvas.point_position_for(point_record)
    assert position is not None
    QTest.mouseMove(chart.canvas, position)
    app.processEvents()
    assert "ENGINEERING_FIXTURE_ALPHA" in chart.detail.text()
    QTest.mouseClick(chart.canvas, Qt.MouseButton.LeftButton, pos=position)
    app.processEvents()
    assert chart.selected_record is point_record
    assert "TEST_FIXTURE" in chart.detail.text()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    image = window.grab().toImage()
    assert not image.isNull()
    assert image.width() >= 1100 and image.height() >= 650
    assert image.save(str(args.output), "PNG")
    assert QImage(str(args.output)).isNull() is False
    print(f"Q-0486_SMOKE_OK records={len(records)} plotted={len(chart.canvas.points)} "
          f"gap_pairs={len(pairs)} image={args.output.resolve()}")
    window.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
