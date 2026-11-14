"""2D point-selection and exact source drill-down for authorized Mission records.

A caller provides a source-checked SeriesState from Q-0064. This component
never requests data, manufactures trend points, or infers a clinical status.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import hypot, isfinite

from .time_series import SeriesState


@dataclass(frozen=True)
class PickablePoint:
    index: int
    x: float
    y: float


@dataclass(frozen=True)
class PointProvenance:
    subject_id: str
    metric: str
    value: float
    unit: str
    observed_at: str
    source_id: str
    quality: str
    verification_state: str


def point_provenance(series: SeriesState, index: int) -> PointProvenance:
    """Return the *selected* original point; never interpolate or promote trust."""
    if series.status in {"DENIED", "OFFLINE", "ERROR", "NO_DATA"}:
        raise ValueError("restricted or unavailable series cannot reveal point details")
    if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < len(series.points):
        raise IndexError("requested point does not exist")
    point = series.points[index]
    if (not isinstance(point.source_id, str) or not point.source_id.strip() or
            not isinstance(point.unit, str) or not point.unit.strip() or
            not isfinite(point.value) or not isinstance(point.timestamp, datetime) or
            point.timestamp.tzinfo is None or point.timestamp.utcoffset() is None):
        raise ValueError("a point without exact measurement provenance cannot be selected")
    return PointProvenance(series.subject_id, series.metric, point.value, point.unit,
                           point.timestamp.isoformat(), point.source_id,
                           point.quality, point.verification_state)


def positions(series: SeriesState, width: float, height: float) -> tuple[PickablePoint, ...]:
    """Calculate 2D coordinates strictly for existing observations.

    A single observation is a standalone dot, **not** a trend or line.
    """
    if (series.status in {"DENIED", "OFFLINE", "ERROR", "NO_DATA"} or not series.points or
            not isfinite(width) or not isfinite(height) or width <= 0 or height <= 0):
        return ()
    valid = [point_provenance(series, i) for i in range(len(series.points))]
    values = [v.value for v in valid]
    times = [series.points[i].timestamp.timestamp() for i in range(len(valid))]
    low_v, high_v = min(values), max(values)
    low_t, high_t = min(times), max(times)
    w, h = max(1.0, width - 64.0), max(1.0, height - 64.0)
    result = []
    for i, (timestamp, value) in enumerate(zip(times, values)):
        x = 32.0 + ((timestamp - low_t) / (high_t - low_t) * w if high_t > low_t else w / 2)
        y = 32.0 + ((high_v - value) / (high_v - low_v) * h if high_v > low_v else h / 2)
        result.append(PickablePoint(i, x, y))
    return tuple(result)


def pick_point(series: SeriesState, x: float, y: float, width: float, height: float,
               radius: float = 12) -> int | None:
    """Only real dots inside the hit radius are selectable; not between them."""
    if not all(isfinite(v) for v in (x, y, radius)) or radius <= 0:
        return None
    near = ((hypot(p.x - x, p.y - y), p.index) for p in positions(series, width, height))
    candidates = [(distance, index) for distance, index in near if distance <= radius]
    return min(candidates)[1] if candidates else None


def build_provenance_plot(series: SeriesState, parent=None):
    """Native Qt 2D canvas; click/keyboard picks a precise audited record."""
    from PySide6.QtCore import QPointF, Qt
    from PySide6.QtGui import QBrush, QPainter, QPen, QPolygonF
    from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

    root = QWidget(parent)
    layout = QVBoxLayout(root)
    detail = QLabel("Select a recorded point to inspect exact value, time and source")
    detail.setWordWrap(True)
    detail.setAccessibleName("Selected observation provenance")

    class ProvenanceCanvas(QWidget):
        def __init__(self):
            super().__init__(root)
            self.setMinimumHeight(200)
            self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            self.setAccessibleName(f"{series.metric} recorded observations for {series.subject_id}")
            self._selected = None

        def select(self, index: int):
            original = point_provenance(series, index)
            self._selected = index
            detail.setText(
                f"Subject: {original.subject_id} · Metric: {original.metric}\n"
                f"Recorded: {original.value:g} {original.unit} · {original.observed_at}\n"
                f"Source: {original.source_id} · Quality: {original.quality} · "
                f"Verification: {original.verification_state}\n"
                "Recorded source only; not a medical diagnosis"
            )
            self.update()

        def paintEvent(self, event):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            points = positions(series, float(self.width()), float(self.height()))
            if not points:
                painter.setPen(QPen(Qt.GlobalColor.white))
                painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                                 f"{series.status} — no source-backed plot points")
            else:
                if series.can_plot and len({series.points[p.index].timestamp for p in points}) >= 2:
                    painter.setPen(QPen(Qt.GlobalColor.cyan, 2))
                    painter.drawPolyline(QPolygonF([QPointF(p.x, p.y) for p in points]))
                for p in points:
                    painter.setPen(QPen(Qt.GlobalColor.white))
                    painter.setBrush(QBrush(Qt.GlobalColor.yellow if p.index == self._selected
                                           else Qt.GlobalColor.cyan))
                    painter.drawEllipse(QPointF(p.x, p.y), 5, 5)
                painter.setPen(QPen(Qt.GlobalColor.white))
                painter.drawText(8, 18, "2D · recorded observations (select a dot for provenance)")
            painter.end()

        def mousePressEvent(self, event):
            if event.button() != Qt.MouseButton.LeftButton:
                return super().mousePressEvent(event)
            found = pick_point(series, event.position().x(), event.position().y(),
                               float(self.width()), float(self.height()))
            if found is not None:
                self.select(found)

        def keyPressEvent(self, event):
            if not series.points or event.key() not in (Qt.Key.Key_Left, Qt.Key.Key_Right):
                return super().keyPressEvent(event)
            direction = -1 if event.key() == Qt.Key.Key_Left else 1
            index = 0 if self._selected is None else min(len(series.points) - 1,
                                                          max(0, self._selected + direction))
            self.select(index)

    layout.addWidget(ProvenanceCanvas())
    layout.addWidget(detail)
    return root
