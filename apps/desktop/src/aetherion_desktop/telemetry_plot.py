"""Reusable native Qt telemetry plot with explicit time, quality, and source context.

The component consumes caller-supplied response-validated records. It does not
fetch, invent, classify, or persist health or NASA data. By default it renders
points without connecting them; a host may opt into a documented visual-only
maximum gap when its source cadence is known.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import math
from typing import Iterable, Sequence

from PySide6.QtCore import QPoint, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPalette, QPen, QPolygonF
from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)


UTC = timezone.utc
DISPLAY_QUALITIES = frozenset({"READY", "UNVERIFIED", "STALE"})
KNOWN_QUALITIES = frozenset({"READY", "UNVERIFIED", "STALE", "NO_DATA", "OFFLINE", "DENIED", "ERROR"})
SOURCE_COLORS = (
    "#2678B2", "#CE5B48", "#25866E", "#865FC2",
    "#B48121", "#278E9E", "#C04C86", "#667A2C",
)

_TEXT = {
    "en": {
        "metric": "Metric",
        "source": "Source",
        "range": "Time range · UTC",
        "all_sources": "All sources",
        "all_loaded": "All loaded",
        "custom": "Custom range",
        "reset": "Reset view",
        "empty": "No displayable records in this time range.",
        "hint": "Hover a point for provenance; click a point to select it.",
        "no_cadence": "Points only · source cadence not declared",
        "gap_rule": "Visual line gap limit: {gap}. This is not a freshness or medical threshold.",
        "utc": "UTC",
        "unit": "Unit",
        "quality": "Quality",
        "verification": "Verification",
        "scope": "Scope",
        "all_preview": "ENGINEERING PREVIEW · FICTIONAL DATA · NOT A HEALTH OR NASA RECORD",
        "hours1": "1 hour",
        "hours24": "24 hours",
        "days7": "7 days",
        "days30": "30 days",
        "quality_ready": "READY",
        "quality_unverified": "UNVERIFIED",
        "quality_stale": "STALE",
        "nearest": "No point selected",
        "range_from": "From",
        "range_to": "To",
    },
    "vi": {
        "metric": "Chỉ số",
        "source": "Nguồn",
        "range": "Khoảng thời gian · UTC",
        "all_sources": "Tất cả nguồn",
        "all_loaded": "Toàn bộ dữ liệu đã tải",
        "custom": "Khoảng tùy chỉnh",
        "reset": "Đặt lại biểu đồ",
        "empty": "Không có bản ghi hiển thị trong khoảng thời gian này.",
        "hint": "Di chuột để xem nguồn; bấm vào điểm để chọn.",
        "no_cadence": "Chỉ hiện điểm · nguồn chưa khai báo nhịp lấy mẫu",
        "gap_rule": "Giới hạn nối điểm để hiển thị: {gap}. Đây không phải ngưỡng độ mới hay y khoa.",
        "utc": "UTC",
        "unit": "Đơn vị",
        "quality": "Chất lượng",
        "verification": "Xác minh",
        "scope": "Phạm vi",
        "all_preview": "BẢN XEM KỸ THUẬT · DỮ LIỆU HƯ CẤU · KHÔNG PHẢI DỮ LIỆU SỨC KHỎE HAY NASA",
        "hours1": "1 giờ",
        "hours24": "24 giờ",
        "days7": "7 ngày",
        "days30": "30 ngày",
        "quality_ready": "READY",
        "quality_unverified": "UNVERIFIED",
        "quality_stale": "STALE",
        "nearest": "Chưa chọn điểm",
        "range_from": "Từ",
        "range_to": "Đến",
    },
}


@dataclass(frozen=True)
class TimeBounds:
    """Inclusive UTC display bounds shared by plot and any companion table."""

    start_utc: datetime
    end_utc: datetime

    def __post_init__(self) -> None:
        start = _as_utc(self.start_utc)
        end = _as_utc(self.end_utc)
        if end <= start:
            raise ValueError("time bounds must have end_utc later than start_utc")
        object.__setattr__(self, "start_utc", start)
        object.__setattr__(self, "end_utc", end)


@dataclass(frozen=True)
class _PlotPoint:
    record: object
    metric: str
    value: float
    unit: str
    observed_at: datetime
    source_id: str
    scope: str
    quality: str
    verification: str


def _field(record: object, name: str, default: object = None) -> object:
    if isinstance(record, dict):
        return record.get(name, default)
    return getattr(record, name, default)


def _as_utc(value: object) -> datetime:
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("plot records require timezone-aware observed_at timestamps")
    return value.astimezone(UTC)


def _normalize(record: object) -> _PlotPoint:
    metric = str(_field(record, "metric", "")).strip()
    unit = str(_field(record, "unit", "")).strip()
    source = str(_field(record, "source_id", "")).strip()
    scope = str(_field(record, "scope", "")).strip()
    verification = str(_field(record, "verification", _field(record, "verification_state", ""))).strip()
    if not metric or not unit or not source or not scope or not verification:
        raise ValueError("plot records require metric, unit, source, scope, and verification provenance")
    try:
        value = float(_field(record, "value"))
    except (TypeError, ValueError) as exc:
        raise ValueError("plot record value must be numeric") from exc
    if not math.isfinite(value):
        raise ValueError("plot record value must be finite")
    quality = str(_field(record, "quality", "UNVERIFIED")).strip().upper()
    if quality not in KNOWN_QUALITIES:
        quality = "UNVERIFIED"
    return _PlotPoint(
        record=record,
        metric=metric,
        value=value,
        unit=unit,
        observed_at=_as_utc(_field(record, "observed_at")),
        source_id=source,
        scope=scope,
        quality=quality,
        verification=verification,
    )


def filter_records(
    records: Iterable[object],
    *,
    metric_key: tuple[str, str] | None = None,
    source_id: str | None = None,
    time_bounds: TimeBounds | None = None,
) -> list[object]:
    """Return the exact stable record slice a plot and table can share."""
    result: list[_PlotPoint] = []
    for record in records:
        point = _normalize(record)
        if metric_key is not None and (point.metric, point.unit) != metric_key:
            continue
        if source_id is not None and point.source_id != source_id:
            continue
        if time_bounds is not None and not (
            time_bounds.start_utc <= point.observed_at <= time_bounds.end_utc
        ):
            continue
        result.append(point)
    result.sort(key=lambda item: item.observed_at)
    return [item.record for item in result]


def connectable_pairs(
    records: Iterable[object],
    max_visual_gap: timedelta | None,
) -> list[tuple[object, object]]:
    """Pairs eligible for a line, only under an explicit visual-only gap rule."""
    if max_visual_gap is None or max_visual_gap <= timedelta(0):
        return []
    points = sorted(
        (_normalize(record) for record in records),
        key=lambda item: (item.source_id, item.observed_at),
    )
    pairs: list[tuple[object, object]] = []
    previous: _PlotPoint | None = None
    for point in points:
        if point.quality not in DISPLAY_QUALITIES:
            previous = None
            continue
        if previous is not None:
            gap = point.observed_at - previous.observed_at
            if (
                point.source_id == previous.source_id
                and point.metric == previous.metric
                and point.unit == previous.unit
                and point.quality == previous.quality
                and gap <= max_visual_gap
            ):
                pairs.append((previous.record, point.record))
        previous = point
    return pairs


def _nice_ticks(low: float, high: float, target: int = 5) -> list[float]:
    span = high - low
    if not math.isfinite(span) or span <= 0:
        return [low]
    raw = span / max(target, 1)
    power = 10 ** math.floor(math.log10(raw))
    normalized = raw / power
    step = (1 if normalized <= 1 else 2 if normalized <= 2 else
            5 if normalized <= 5 else 10) * power
    first = math.ceil(low / step) * step
    count = min(12, int(math.floor((high - first) / step)) + 1)
    return [first + i * step for i in range(max(0, count))]


def _expanded_bounds(points: Sequence[_PlotPoint]) -> TimeBounds | None:
    if not points:
        return None
    start = min(point.observed_at for point in points)
    end = max(point.observed_at for point in points)
    if start == end:
        start -= timedelta(seconds=30)
        end += timedelta(seconds=30)
    return TimeBounds(start, end)


class _PlotCanvas(QWidget):
    point_hovered = Signal(object)
    point_selected = Signal(object)
    bounds_changed = Signal(object, object)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setMinimumHeight(320)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.points: list[_PlotPoint] = []
        self.bounds: TimeBounds | None = None
        self.metric_label = ""
        self.unit_label = ""
        self.empty_label = _TEXT["en"]["empty"]
        self.max_visual_gap: timedelta | None = None
        self.hovered: _PlotPoint | None = None
        self.selected: _PlotPoint | None = None
        self._press_pos: QPoint | None = None
        self._drag_start_bounds: TimeBounds | None = None
        self._dragged = False

    def set_data(
        self,
        points: list[_PlotPoint],
        bounds: TimeBounds | None,
        metric_label: str,
        unit_label: str,
        max_visual_gap: timedelta | None,
        empty_label: str,
    ) -> None:
        self.points = points
        self.bounds = bounds
        self.metric_label = metric_label
        self.unit_label = unit_label
        self.max_visual_gap = max_visual_gap
        self.empty_label = empty_label
        if self.hovered and not any(p.record is self.hovered.record for p in points):
            self.hovered = None
        if self.selected and not any(p.record is self.selected.record for p in points):
            self.selected = None
        self.update()

    def _plot_rect(self) -> QRectF:
        return QRectF(self.rect()).adjusted(100, 44, -22, -58)

    def _display_bounds(self) -> TimeBounds | None:
        return self.bounds or _expanded_bounds(self.points)

    def _value_bounds(self) -> tuple[float, float] | None:
        if not self.points:
            return None
        low = min(point.value for point in self.points)
        high = max(point.value for point in self.points)
        if low == high:
            pad = max(abs(low) * 0.08, 1.0)
            return low - pad, high + pad
        pad = (high - low) * 0.08
        return low - pad, high + pad

    def _project(self, point: _PlotPoint) -> QPointF | None:
        rect = self._plot_rect()
        bounds = self._display_bounds()
        value_bounds = self._value_bounds()
        if bounds is None or value_bounds is None or rect.width() <= 1 or rect.height() <= 1:
            return None
        time_span = (bounds.end_utc - bounds.start_utc).total_seconds()
        value_span = value_bounds[1] - value_bounds[0]
        if time_span <= 0 or value_span <= 0:
            return None
        x = rect.left() + rect.width() * (
            (point.observed_at - bounds.start_utc).total_seconds() / time_span
        )
        y = rect.bottom() - rect.height() * (
            (point.value - value_bounds[0]) / value_span
        )
        return QPointF(x, y)

    def point_position_for(self, record: object) -> QPoint | None:
        """Pixel position helper used by keyboard/smoke interaction checks."""
        point = next((item for item in self.points if item.record is record), None)
        projected = self._project(point) if point else None
        return QPoint(round(projected.x()), round(projected.y())) if projected else None

    def hit_test(self, position: QPointF, limit_px: float = 18.0) -> _PlotPoint | None:
        limit_sq = limit_px * limit_px
        nearest: _PlotPoint | None = None
        nearest_sq = limit_sq
        for point in self.points:
            projected = self._project(point)
            if projected is None:
                continue
            distance_sq = (projected.x() - position.x()) ** 2 + (projected.y() - position.y()) ** 2
            if distance_sq <= nearest_sq:
                nearest, nearest_sq = point, distance_sq
        return nearest

    def _source_color(self, source_id: str) -> QColor:
        index = hashlib.sha256(source_id.encode("utf-8")).digest()[0] % len(SOURCE_COLORS)
        return QColor(SOURCE_COLORS[index])

    def _draw_marker(self, painter: QPainter, x: float, y: float, quality: str, color: QColor, selected: bool) -> None:
        radius = 5.0 if selected else 4.0
        painter.setPen(QPen(color.darker(135), 1.2))
        painter.setBrush(color)
        rect = QRectF(x - radius, y - radius, radius * 2, radius * 2)
        if quality == "UNVERIFIED":
            diamond = QPolygonF([
                QPointF(x, y - radius - 1), QPointF(x + radius + 1, y),
                QPointF(x, y + radius + 1), QPointF(x - radius - 1, y),
            ])
            painter.drawPolygon(diamond)
        elif quality == "STALE":
            painter.drawRect(rect)
        else:
            painter.drawEllipse(rect)
        if selected:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(self.palette().color(QPalette.ColorRole.Text), 2))
            painter.drawEllipse(QRectF(x - radius - 3, y - radius - 3, radius * 2 + 6, radius * 2 + 6))

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        palette = self.palette()
        painter.fillRect(self.rect(), palette.color(palette.ColorRole.Base))
        rect = self._plot_rect()
        if rect.width() < 80 or rect.height() < 80:
            return
        text_color = palette.color(palette.ColorRole.Text)
        grid_color = palette.color(palette.ColorRole.Mid)
        grid_color.setAlpha(105)
        painter.setFont(self.font())

        if not self.points:
            painter.setPen(text_color)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.empty_label)
            return

        value_bounds = self._value_bounds()
        time_bounds = self._display_bounds()
        if value_bounds is None or time_bounds is None:
            return

        painter.setPen(text_color)
        painter.drawText(QRectF(6, 4, max(80, rect.left() - 14), 22),
                         Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                         self.metric_label)
        painter.drawText(QRectF(rect.right() - 56, 4, 54, 22),
                         Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                         "UTC")

        painter.setPen(QPen(grid_color, 1))
        for value in _nice_ticks(*value_bounds, target=5):
            y = rect.bottom() - rect.height() * (
                (value - value_bounds[0]) / (value_bounds[1] - value_bounds[0])
            )
            painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
            painter.setPen(text_color)
            painter.drawText(QRectF(3, y - 10, rect.left() - 12, 20),
                             Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                             f"{value:g}")
            painter.setPen(QPen(grid_color, 1))

        span_seconds = (time_bounds.end_utc - time_bounds.start_utc).total_seconds()
        tick_count = 4 if self.width() >= 760 else 3
        for index in range(tick_count + 1):
            fraction = index / tick_count
            x = rect.left() + rect.width() * fraction
            painter.setPen(QPen(grid_color, 1))
            painter.drawLine(QPointF(x, rect.top()), QPointF(x, rect.bottom()))
            tick_time = time_bounds.start_utc + timedelta(seconds=span_seconds * fraction)
            if span_seconds <= 24 * 3600:
                label = tick_time.strftime("%H:%M")
            elif span_seconds <= 14 * 24 * 3600:
                label = tick_time.strftime("%d %b\n%H:%M")
            else:
                label = tick_time.strftime("%Y-%m-%d")
            painter.setPen(text_color)
            width = 112 if "\n" in label else 88
            painter.drawText(QRectF(x - width / 2, rect.bottom() + 5, width, 34),
                             Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                             label)

        # Only explicitly allowed same-source/same-quality adjacent pairs get a line.
        point_by_identity = {id(point.record): point for point in self.points}
        pairs = connectable_pairs(
            [point.record for point in self.points], self.max_visual_gap
        )
        for first_record, second_record in pairs:
            first, second = point_by_identity[id(first_record)], point_by_identity[id(second_record)]
            first_xy, second_xy = self._project(first), self._project(second)
            if first_xy is None or second_xy is None:
                continue
            color = self._source_color(first.source_id)
            painter.setPen(QPen(color, 1.8))
            painter.drawLine(first_xy, second_xy)

        for point in self.points:
            projected = self._project(point)
            if projected is None:
                continue
            selected = bool(self.selected and self.selected.record is point.record)
            self._draw_marker(
                painter, projected.x(), projected.y(), point.quality,
                self._source_color(point.source_id), selected,
            )

        crosshair = self.hovered
        if crosshair is not None:
            projected = self._project(crosshair)
            if projected is not None:
                cross_pen = QPen(text_color, 1, Qt.PenStyle.DashLine)
                painter.setPen(cross_pen)
                painter.drawLine(QPointF(projected.x(), rect.top()),
                                 QPointF(projected.x(), rect.bottom()))
                painter.drawLine(QPointF(rect.left(), projected.y()),
                                 QPointF(rect.right(), projected.y()))
                self._draw_marker(
                    painter, projected.x(), projected.y(), crosshair.quality,
                    self._source_color(crosshair.source_id), True,
                )

        painter.setPen(text_color)
        painter.drawText(QRectF(rect.left(), rect.bottom() + 39, rect.width(), 16),
                         Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter,
                         f"{self.unit_label}   ·   {time_bounds.start_utc:%Y-%m-%d %H:%M} — "
                         f"{time_bounds.end_utc:%Y-%m-%d %H:%M} UTC")

    def wheelEvent(self, event) -> None:
        bounds = self._display_bounds()
        if bounds is None:
            return
        rect = self._plot_rect()
        if not rect.contains(event.position()):
            event.ignore()
            return
        old_span = (bounds.end_utc - bounds.start_utc).total_seconds()
        factor = 0.8 if event.angleDelta().y() > 0 else 1.25
        new_span = max(1.0, min(old_span * factor, 3650 * 24 * 3600))
        ratio = min(1.0, max(0.0, (event.position().x() - rect.left()) / rect.width()))
        center = bounds.start_utc + timedelta(seconds=old_span * ratio)
        start = center - timedelta(seconds=new_span * ratio)
        self.bounds_changed.emit(start, start + timedelta(seconds=new_span))
        event.accept()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._plot_rect().contains(event.position()):
            bounds = self._display_bounds()
            if bounds:
                self._press_pos = event.position().toPoint()
                self._drag_start_bounds = bounds
                self._dragged = False
                self.setFocus(Qt.FocusReason.MouseFocusReason)
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._press_pos is not None and self._drag_start_bounds is not None:
            delta = event.position().toPoint() - self._press_pos
            if abs(delta.x()) > 3:
                self._dragged = True
            if self._dragged:
                span = (self._drag_start_bounds.end_utc - self._drag_start_bounds.start_utc).total_seconds()
                shift = -delta.x() / max(1.0, self._plot_rect().width()) * span
                start = self._drag_start_bounds.start_utc + timedelta(seconds=shift)
                self.bounds_changed.emit(start, start + timedelta(seconds=span))
                event.accept()
                return
        hovered = self.hit_test(event.position())
        if hovered is not self.hovered:
            self.hovered = hovered
            self.point_hovered.emit(hovered.record if hovered else None)
            self.update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._press_pos is not None:
            if not self._dragged:
                point = self.hit_test(event.position())
                if point is not None:
                    self.selected = point
                    self.point_selected.emit(point.record)
                    self.update()
            self._press_pos = None
            self._drag_start_bounds = None
            self._dragged = False
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def leaveEvent(self, event) -> None:
        if self.hovered is not None:
            self.hovered = None
            self.point_hovered.emit(None)
            self.update()
        super().leaveEvent(event)


class TelemetryPlot(QWidget):
    """Self-contained plot controls plus a table-compatible filtered-record API."""

    time_bounds_changed = Signal(object, object)
    filtered_records_changed = Signal(object)
    point_inspected = Signal(object)
    point_selected = Signal(object)

    def __init__(
        self,
        records: Iterable[object] = (),
        *,
        locale: str = "en",
        max_visual_gap: timedelta | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.locale = "vi" if locale == "vi" else "en"
        self.max_visual_gap = max_visual_gap
        self._records: list[_PlotPoint] = []
        self._visible: list[object] = []
        self._plot_points: list[_PlotPoint] = []
        self._bounds: TimeBounds | None = None
        self.selected_record: object | None = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 10, 12, 10)
        outer.setSpacing(8)

        controls = QHBoxLayout()
        self.metric_label = QLabel()
        self.metric_selector = QComboBox()
        self.metric_selector.setAccessibleName("Metric and unit")
        controls.addWidget(self.metric_label)
        controls.addWidget(self.metric_selector, 2)
        self.source_label = QLabel()
        self.source_selector = QComboBox()
        self.source_selector.setAccessibleName("Telemetry source")
        controls.addWidget(self.source_label)
        controls.addWidget(self.source_selector, 2)
        self.range_label = QLabel()
        self.range_selector = QComboBox()
        self.range_selector.setAccessibleName("UTC time range")
        controls.addWidget(self.range_label)
        controls.addWidget(self.range_selector, 1)
        self.reset_button = QPushButton()
        self.reset_button.clicked.connect(self.reset_view)
        controls.addWidget(self.reset_button)
        outer.addLayout(controls)

        self.legend = QLabel()
        self.legend.setTextFormat(Qt.TextFormat.RichText)
        self.legend.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.legend.setWordWrap(True)
        outer.addWidget(self.legend)

        self.canvas = _PlotCanvas()
        self.canvas.point_hovered.connect(self._on_point_inspected)
        self.canvas.point_selected.connect(self._on_point_selected)
        self.canvas.bounds_changed.connect(self._on_canvas_bounds_changed)
        outer.addWidget(self.canvas, 1)

        self.detail = QLabel()
        self.detail.setWordWrap(True)
        self.detail.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        outer.addWidget(self.detail)
        self.caption = QLabel()
        self.caption.setWordWrap(True)
        outer.addWidget(self.caption)

        self.metric_selector.currentIndexChanged.connect(self._recompute)
        self.source_selector.currentIndexChanged.connect(self._recompute)
        self.range_selector.currentIndexChanged.connect(self._on_range_changed)
        self.set_locale(self.locale)
        self.set_records(records)

    def set_locale(self, locale: str) -> None:
        self.locale = "vi" if locale == "vi" else "en"
        strings = _TEXT[self.locale]
        self.metric_label.setText(strings["metric"])
        self.source_label.setText(strings["source"])
        self.range_label.setText(strings["range"])
        self.reset_button.setText(strings["reset"])
        self.detail.setText(strings["hint"])
        self.setAccessibleName("Biểu đồ telemetry AETHERION" if self.locale == "vi" else
                               "AETHERION telemetry chart")
        self.metric_selector.setAccessibleName(strings["metric"])
        self.source_selector.setAccessibleName(strings["source"])
        self.range_selector.setAccessibleName(strings["range"])
        self._rebuild_range_options()
        self._update_source_options()
        self._update_legend()
        self._recompute()

    def _rebuild_range_options(self) -> None:
        selected = self.range_selector.currentData() if hasattr(self, "range_selector") else None
        self.range_selector.blockSignals(True)
        self.range_selector.clear()
        strings = _TEXT[self.locale]
        options = [
            ("1h", strings["hours1"]),
            ("24h", strings["hours24"]),
            ("7d", strings["days7"]),
            ("30d", strings["days30"]),
            ("all", strings["all_loaded"]),
        ]
        for key, label in options:
            self.range_selector.addItem(label, key)
        if selected == "custom":
            self.range_selector.addItem(strings["custom"], "custom")
        index = self.range_selector.findData(selected)
        self.range_selector.setCurrentIndex(index if index >= 0 else self.range_selector.findData("all"))
        self.range_selector.blockSignals(False)

    def _update_source_options(self) -> None:
        if not hasattr(self, "source_selector"):
            return
        selected = self.source_selector.currentData()
        self.source_selector.blockSignals(True)
        self.source_selector.clear()
        self.source_selector.addItem(_TEXT[self.locale]["all_sources"], None)
        for source in sorted({point.source_id for point in self._records}):
            self.source_selector.addItem(source, source)
        index = self.source_selector.findData(selected)
        self.source_selector.setCurrentIndex(index if index >= 0 else 0)
        self.source_selector.blockSignals(False)

    def set_records(self, records: Iterable[object]) -> None:
        previous_metric = self.metric_selector.currentData()
        previous_source = self.source_selector.currentData()
        self._records = sorted((_normalize(record) for record in records),
                               key=lambda point: point.observed_at)
        self._update_metric_options(previous_metric)
        self._update_source_options()
        if self.range_selector.currentData() != "custom":
            self._bounds = None
            self._rebuild_range_options()
        self._recompute()

    def _update_metric_options(self, selected: object = None) -> None:
        self.metric_selector.blockSignals(True)
        self.metric_selector.clear()
        for metric, unit in sorted({(point.metric, point.unit) for point in self._records}):
            self.metric_selector.addItem(f"{metric} ({unit})", (metric, unit))
        index = self.metric_selector.findData(selected)
        if index >= 0:
            self.metric_selector.setCurrentIndex(index)
        elif self.metric_selector.count():
            self.metric_selector.setCurrentIndex(0)
        self.metric_selector.blockSignals(False)

    def set_time_bounds(self, start_utc: datetime, end_utc: datetime) -> None:
        """Set external/shared UTC bounds, for a host's time conductor and table."""
        bounds = TimeBounds(start_utc, end_utc)
        self._bounds = bounds
        if self.range_selector.findData("custom") < 0:
            self.range_selector.addItem(_TEXT[self.locale]["custom"], "custom")
        self.range_selector.blockSignals(True)
        self.range_selector.setCurrentIndex(self.range_selector.findData("custom"))
        self.range_selector.blockSignals(False)
        self._recompute()
        self.time_bounds_changed.emit(bounds.start_utc, bounds.end_utc)

    def reset_view(self) -> None:
        self._bounds = None
        self._rebuild_range_options()
        self._recompute()
        loaded = _expanded_bounds(self._records)
        if loaded is not None:
            self.time_bounds_changed.emit(loaded.start_utc, loaded.end_utc)

    def _on_range_changed(self, *_: object) -> None:
        choice = self.range_selector.currentData()
        if choice == "custom":
            return
        if choice == "all":
            self._bounds = None
        elif choice in {"1h", "24h", "7d", "30d"} and self._records:
            duration = {
                "1h": timedelta(hours=1),
                "24h": timedelta(hours=24),
                "7d": timedelta(days=7),
                "30d": timedelta(days=30),
            }[choice]
            end = max(point.observed_at for point in self._records)
            self._bounds = TimeBounds(end - duration, end)
        else:
            self._bounds = None
        self._recompute()
        if self._bounds:
            self.time_bounds_changed.emit(self._bounds.start_utc, self._bounds.end_utc)
        elif (loaded := _expanded_bounds(self._records)) is not None:
            self.time_bounds_changed.emit(loaded.start_utc, loaded.end_utc)

    def _on_canvas_bounds_changed(self, start_utc: datetime, end_utc: datetime) -> None:
        self._bounds = TimeBounds(start_utc, end_utc)
        if self.range_selector.findData("custom") < 0:
            self.range_selector.addItem(_TEXT[self.locale]["custom"], "custom")
        self.range_selector.blockSignals(True)
        self.range_selector.setCurrentIndex(self.range_selector.findData("custom"))
        self.range_selector.blockSignals(False)
        self._recompute()
        self.time_bounds_changed.emit(self._bounds.start_utc, self._bounds.end_utc)

    def _recompute(self, *_: object) -> None:
        metric_key = self.metric_selector.currentData()
        source_id = self.source_selector.currentData()
        selected = filter_records(
            (point.record for point in self._records),
            metric_key=metric_key,
            source_id=source_id,
            time_bounds=self._bounds,
        )
        self._visible = selected
        allowed = {id(record) for record in selected}
        self._plot_points = [
            point for point in self._records
            if id(point.record) in allowed and point.quality in DISPLAY_QUALITIES
        ]
        visible_bounds = self._bounds or _expanded_bounds(self._plot_points)
        metric_label = ""
        unit_label = ""
        if metric_key:
            metric_label, unit_label = metric_key
        self.canvas.set_data(
            self._plot_points, visible_bounds, metric_label, unit_label, self.max_visual_gap,
            _TEXT[self.locale]["empty"],
        )
        self.filtered_records_changed.emit(list(self._visible))
        self._update_legend()
        if self._plot_points:
            self.caption.setText(self._gap_caption())
        else:
            self.caption.setText(_TEXT[self.locale]["empty"])

    def filtered_records(self) -> list[object]:
        """Exact filtered rows for a companion table; includes non-displayable states."""
        return list(self._visible)

    def _gap_caption(self) -> str:
        if self.max_visual_gap is None:
            return _TEXT[self.locale]["no_cadence"]
        total_seconds = self.max_visual_gap.total_seconds()
        if total_seconds >= 3600 and total_seconds % 3600 == 0:
            gap = f"{total_seconds / 3600:g} h"
        elif total_seconds >= 60 and total_seconds % 60 == 0:
            gap = f"{total_seconds / 60:g} min"
        else:
            gap = f"{total_seconds:g} s"
        return _TEXT[self.locale]["gap_rule"].format(gap=gap)

    def _update_legend(self) -> None:
        if not hasattr(self, "legend"):
            return
        source_ids = sorted({point.source_id for point in self._plot_points})
        source_html: list[str] = []
        for source in source_ids:
            color = self.canvas._source_color(source).name()
            source_html.append(
                f'<span style="color:{color}">●</span> {html_escape(source)}'
            )
        strings = _TEXT[self.locale]
        quality = (
            f'● {strings["quality_ready"]}  ·  ◇ {strings["quality_unverified"]}  ·  '
            f'□ {strings["quality_stale"]}'
        )
        sections = []
        if source_html:
            sections.append("  ".join(source_html))
        sections.append(f'{strings["quality"]}: {quality}')
        self.legend.setText(" &nbsp; | &nbsp; ".join(sections))

    def _format_point(self, record: object) -> str:
        point = _normalize(record)
        stamp = point.observed_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        strings = _TEXT[self.locale]
        return (
            f"{point.metric}: {point.value:g} {point.unit} · {stamp} · "
            f'{strings["source"]}: {point.source_id} · {strings["scope"]}: {point.scope} · '
            f'{strings["quality"]}: {point.quality} · '
            f'{strings["verification"]}: {point.verification}'
        )

    def _on_point_inspected(self, record: object) -> None:
        if record is None:
            self.detail.setText(_TEXT[self.locale]["hint"])
            return
        text = self._format_point(record)
        self.detail.setText(text)
        self.point_inspected.emit(record)

    def _on_point_selected(self, record: object) -> None:
        self.selected_record = record
        self._on_point_inspected(record)
        self.point_selected.emit(record)


def html_escape(value: str) -> str:
    """Escape record supplied source identifiers before adding them to QLabel rich text."""
    return (
        value.replace("&", "&amp;").replace("<", "&lt;")
        .replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;")
    )
