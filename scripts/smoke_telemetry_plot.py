"""Q-0486 offscreen interaction and render smoke using fictional fixtures only.

This builds an AETHERION-style native operations layout: Browse, a shared UTC
Time Conductor, a plot and telemetry table, and a right-hand Inspect panel.
Nothing in the fixture represents a patient, NASA record, sensor, or measurement.
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

from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QColor, QImage, QWheelEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QFrame, QHeaderView, QLabel, QListWidget,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout, QWidget,
)

from aetherion_desktop.telemetry_plot import (
    TelemetryPlot, TimeBounds, UtcTimeConductor, connectable_pairs,
)


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

    for hour, value in zip(
        [0, 1, 2, 3, 4, 12, 13, 14],
        [1.4, 2.2, 1.8, 3.1, 2.7, 4.0, 3.6, 4.7],
    ):
        add("ENGINEERING_FIXTURE_ALPHA", hour, value)
    for hour, value in zip(
        [0.5, 1.5, 2.5, 3.5, 12.5, 13.5],
        [3.1, 2.8, 3.7, 3.3, 2.2, 3.0],
    ):
        add("ENGINEERING_FIXTURE_BETA", hour, value)

    # A numeric row with ERROR stays available to a companion table but must
    # never be painted as a chart point.
    add("ENGINEERING_FIXTURE_ALPHA", 8, 99.0, quality="ERROR")
    return rows, start


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("artifacts/q0486-telemetry-plot.png"))
    args = parser.parse_args()

    app = QApplication.instance() or QApplication([])
    app.setApplicationName("AETHERION Q-0486 offscreen preview")
    records, start = make_preview()

    # A caller-supplied visual gap rule joins nearby points only; no segment
    # crosses the eight-hour hiatus. No cadence rule is inferred by the widget.
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
    window.setWindowTitle("AETHERION · native telemetry workspace preview")
    window.resize(1600, 900)
    root = QVBoxLayout(window)
    root.setContentsMargins(18, 14, 18, 18)
    root.setSpacing(10)

    banner = QLabel(
        "ENGINEERING PREVIEW · FICTIONAL DATA · NOT A HEALTH OR NASA RECORD"
    )
    banner.setTextFormat(Qt.TextFormat.PlainText)
    banner.setStyleSheet(
        "QLabel { background: #73313B; color: white; padding: 10px 14px; "
        "font-size: 15px; font-weight: 700; border-radius: 6px; }"
    )
    root.addWidget(banner)

    time_conductor = UtcTimeConductor(records, locale="en")
    time_conductor.setStyleSheet(
        "QWidget { background: #EDF3F7; border: 1px solid #BCCBD6; border-radius: 5px; }"
    )
    root.addWidget(time_conductor)

    workspace = QHBoxLayout()
    workspace.setSpacing(12)
    root.addLayout(workspace, 1)

    browse_frame = QFrame()
    browse_frame.setFrameShape(QFrame.Shape.StyledPanel)
    browse_frame.setMinimumWidth(170)
    browse_layout = QVBoxLayout(browse_frame)
    browse_title = QLabel("BROWSE")
    browse_title.setStyleSheet("font-weight: 700;")
    browse_layout.addWidget(browse_title)
    browse = QListWidget()
    browse.addItems([
        "Engineering preview",
        "engineering_demo_signal (arb)",
        "ENGINEERING_FIXTURE_ALPHA",
        "ENGINEERING_FIXTURE_BETA",
    ])
    browse.setCurrentRow(1)
    browse_layout.addWidget(browse, 1)
    workspace.addWidget(browse_frame)

    center = QWidget()
    center_layout = QVBoxLayout(center)
    center_layout.setContentsMargins(0, 0, 0, 0)
    center_title = QLabel("AETHERION · Mission Operations adaptation · Telemetry")
    center_title.setStyleSheet("font-size: 19px; font-weight: 700;")
    center_layout.addWidget(center_title)

    chart = TelemetryPlot(
        records, locale="en", max_visual_gap=timedelta(hours=2)
    )
    center_layout.addWidget(chart, 3)

    table_title = QLabel("Telemetry table · same metric, source, and UTC bounds")
    table_title.setStyleSheet("font-weight: 700;")
    center_layout.addWidget(table_title)
    table = QTableWidget(0, 6)
    table.setHorizontalHeaderLabels(
        ["Time (UTC)", "Value", "Unit", "Source", "Quality", "Verification"]
    )
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    table.setAlternatingRowColors(True)
    table.verticalHeader().hide()
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    table.setMinimumHeight(210)
    center_layout.addWidget(table, 1)
    workspace.addWidget(center, 1)

    inspect_frame = QFrame()
    inspect_frame.setFrameShape(QFrame.Shape.StyledPanel)
    inspect_frame.setMinimumWidth(230)
    inspect_layout = QVBoxLayout(inspect_frame)
    inspect_title = QLabel("INSPECT")
    inspect_title.setStyleSheet("font-weight: 700;")
    inspect_layout.addWidget(inspect_title)
    inspect_note = QLabel(
        "Select a point to inspect its timestamp, source, scope, quality, and verification."
    )
    inspect_note.setWordWrap(True)
    inspect_note.setStyleSheet("color: #536C7D;")
    inspect_layout.addWidget(inspect_note)
    inspect_value = QLabel("No point selected")
    inspect_value.setTextFormat(Qt.TextFormat.PlainText)
    inspect_value.setWordWrap(True)
    inspect_value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    inspect_layout.addWidget(inspect_value)
    inspect_layout.addStretch(1)
    workspace.addWidget(inspect_frame)

    def render_table(rows: list[object]) -> None:
        table.setRowCount(len(rows))
        for index, row in enumerate(rows):
            stamp = row.observed_at.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            columns = (
                stamp, f"{row.value:g}", row.unit, row.source_id,
                row.quality, row.verification,
            )
            for column, value in enumerate(columns):
                table.setItem(index, column, QTableWidgetItem(str(value)))

    def inspect(record: object) -> None:
        if record is None:
            record = chart.selected_record
        inspect_value.setText(
            chart._format_point(record) if record is not None else "No point selected"
        )

    chart.filtered_records_changed.connect(render_table)
    chart.point_inspected.connect(inspect)
    chart.point_selected.connect(inspect)
    time_conductor.time_bounds_changed.connect(
        lambda start_utc, end_utc: chart.set_time_bounds(
            start_utc, end_utc, emit=False
        )
    )
    chart.time_bounds_changed.connect(
        lambda start_utc, end_utc: time_conductor.set_time_bounds(
            start_utc, end_utc, emit=False
        )
    )

    window.show()
    app.processEvents()
    assert time_conductor.bounds is not None
    chart.set_time_bounds(
        time_conductor.bounds.start_utc,
        time_conductor.bounds.end_utc,
        emit=False,
    )
    render_table(chart.filtered_records())
    app.processEvents()

    # The shared conductor drives both the chart and table through one filter API.
    custom = TimeBounds(start + timedelta(hours=1), start + timedelta(hours=4))
    time_conductor.set_time_bounds(custom.start_utc, custom.end_utc)
    app.processEvents()
    filtered = chart.filtered_records()
    assert len(filtered) == table.rowCount() == 7
    assert chart._bounds == time_conductor.bounds
    assert all(custom.start_utc <= row.observed_at <= custom.end_utc for row in filtered)

    alpha_index = chart.source_selector.findData("ENGINEERING_FIXTURE_ALPHA")
    assert alpha_index > 0
    chart.source_selector.setCurrentIndex(alpha_index)
    app.processEvents()
    assert chart.filtered_records()
    assert len(chart.filtered_records()) == table.rowCount()
    assert all(table.item(i, 3).text() == "ENGINEERING_FIXTURE_ALPHA" for i in range(table.rowCount()))

    chart.set_locale("vi")
    time_conductor.set_locale("vi")
    assert chart.metric_label.text() == "Chỉ số"
    assert time_conductor.range_label.text() == "Khoảng thời gian · UTC"
    chart.set_locale("en")
    time_conductor.set_locale("en")

    # Reset is owned by the shared time conductor and resets its visible state
    # and the table/plot bounds together.
    time_conductor.reset_view()
    app.processEvents()
    assert time_conductor.range_selector.currentData() == "all"
    assert time_conductor.bounds is not None
    assert chart._bounds == time_conductor.bounds
    chart.source_selector.setCurrentIndex(0)
    app.processEvents()
    assert len(chart.filtered_records()) == len(records)
    assert table.rowCount() == len(records)

    # Wheel zoom and drag pan are real Qt pointer events and update the same
    # Time Conductor used by the table.
    target = records[2]
    position = chart.canvas.point_position_for(target)
    assert position is not None
    original_bounds = time_conductor.bounds
    assert original_bounds is not None
    original_span = (original_bounds.end_utc - original_bounds.start_utc).total_seconds()
    local = QPointF(position)
    global_pos = QPointF(chart.canvas.mapToGlobal(position))
    wheel = QWheelEvent(
        local, global_pos, QPoint(0, 0), QPoint(0, 120),
        Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase, False,
    )
    QApplication.sendEvent(chart.canvas, wheel)
    app.processEvents()
    zoomed = time_conductor.bounds
    assert zoomed is not None
    assert (zoomed.end_utc - zoomed.start_utc).total_seconds() < original_span

    before_drag = time_conductor.bounds
    assert before_drag is not None
    position = chart.canvas.point_position_for(target)
    assert position is not None
    QTest.mousePress(chart.canvas, Qt.MouseButton.LeftButton, pos=position)
    QTest.mouseMove(chart.canvas, position + QPoint(50, 0), 20)
    QTest.mouseRelease(chart.canvas, Qt.MouseButton.LeftButton, pos=position + QPoint(50, 0))
    app.processEvents()
    after_drag = time_conductor.bounds
    assert after_drag is not None and after_drag.start_utc != before_drag.start_utc

    # Restore all loaded data for a readable preview, select a point, then move
    # the cursor away to confirm selected provenance stays in Inspect.
    time_conductor.reset_view()
    chart.source_selector.setCurrentIndex(0)
    app.processEvents()
    position = chart.canvas.point_position_for(target)
    assert position is not None
    QTest.mouseMove(chart.canvas, position)
    app.processEvents()
    assert "ENGINEERING_FIXTURE_ALPHA" in chart.detail.text()
    QTest.mouseClick(chart.canvas, Qt.MouseButton.LeftButton, pos=position)
    app.processEvents()
    assert chart.selected_record is target
    QTest.mouseMove(chart.canvas, QPoint(chart.canvas.width() - 4, chart.canvas.height() - 4))
    app.processEvents()
    assert "TEST_FIXTURE" in chart.detail.text()
    assert "ENGINEERING_FIXTURE_ALPHA" in inspect_value.text()

    # Plot-only rows exclude ERROR, while table parity retains the actual record.
    assert any(row.quality == "ERROR" for row in chart.filtered_records())
    assert all(point.quality in {"READY", "UNVERIFIED", "STALE"} for point in chart.canvas.points)
    assert len(chart.canvas.points) == len(records) - 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    image = window.grab().toImage().convertToFormat(QImage.Format.Format_ARGB32)
    assert not image.isNull()
    assert image.width() >= 1500 and image.height() >= 850
    assert image.save(str(args.output), "PNG")
    saved = QImage(str(args.output))
    assert not saved.isNull()
    sampled = {
        saved.pixelColor(x, y).rgba()
        for x in range(0, saved.width(), max(1, saved.width() // 60))
        for y in range(0, saved.height(), max(1, saved.height() // 35))
    }
    assert len(sampled) > 40
    print(
        f"Q-0486_SMOKE_OK records={len(records)} plotted={len(chart.canvas.points)} "
        f"table={table.rowCount()} gap_pairs={len(pairs)} colors={len(sampled)} "
        f"image={args.output.resolve()}"
    )
    window.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
