"""2D native Qt series based on genuine, source-identified API observations.

No interpolation, thresholds, diagnosis or single-point trends are invented.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite


@dataclass(frozen=True)
class SeriesPoint:
    timestamp: datetime
    value: float
    unit: str
    source_id: str
    verification_state: str
    quality: str


@dataclass(frozen=True)
class SeriesState:
    status: str
    subject_id: str
    metric: str
    points: tuple[SeriesPoint, ...]
    note: str
    can_plot: bool


def _empty(status: str, subject: str, metric: str, note: str) -> SeriesState:
    return SeriesState(status, subject, metric, (), note, False)


def _time(raw: object) -> datetime:
    if not isinstance(raw, str):
        raise ValueError("timestamp missing")
    value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("naive timestamp")
    return value.astimezone(timezone.utc)


def from_series_api(subject: str, metric: str, status_code: int | None,
                    payload: object, *, now: datetime | None = None) -> SeriesState:
    """Fail closed on mixed identities or source gaps; do not create synthetic data."""
    if not subject or not metric:
        raise ValueError("explicit subject and metric are required")
    if status_code in (401, 403):
        return _empty("DENIED", subject, metric, "No authorized source data")
    if status_code is None or status_code == 503:
        return _empty("OFFLINE", subject, metric, "Server unavailable; no health inference")
    if status_code != 200:
        return _empty("ERROR", subject, metric, "Series API request failed")
    if (not isinstance(payload, dict) or payload.get("subject_id") != subject or
            payload.get("metric") != metric or not isinstance(payload.get("points"), list)):
        return _empty("ERROR", subject, metric, "Series API identity or shape mismatch")
    records = payload["points"]
    if payload.get("count", len(records)) != len(records):
        return _empty("ERROR", subject, metric, "Series count disagrees with server data")
    clock = now or datetime.now(timezone.utc)
    if clock.tzinfo is None or clock.utcoffset() is None:
        raise ValueError("reference time must be timezone-aware")
    clock = clock.astimezone(timezone.utc)
    points = []
    try:
        for row in records:
            if not isinstance(row, dict) or row.get("subject_id") != subject or row.get("metric") != metric:
                raise ValueError("series subject or metric mismatch")
            unit = row.get("unit")
            source = row.get("source_id")
            quality = row.get("quality")
            verification = row.get("verification_state")
            if any(not isinstance(v, str) or not v.strip() for v in (unit, source, quality, verification)):
                raise ValueError("missing provenance fields")
            if verification == "TEST_FIXTURE" or row.get("scope") == "engineering_test" or source.lower().startswith(("research:", "nasa_osdr:")):
                continue
            val = row.get("value")
            if isinstance(val, bool) or not isinstance(val, (int, float)) or not isfinite(val):
                raise ValueError("invalid value")
            observed = _time(row.get("observed_at"))
            _time(row.get("received_at"))
            if observed > clock:
                raise ValueError("future timestamp")
            points.append(SeriesPoint(observed, float(val), unit.strip(), source.strip(), verification, quality))
    except (TypeError, ValueError, OverflowError):
        return _empty("ERROR", subject, metric, "Invalid measurement or provenance; no trend drawn")
    if not points:
        return _empty("NO_DATA", subject, metric, "No source-backed live time points")
    if len({p.unit for p in points}) != 1:
        return _empty("ERROR", subject, metric, "Incompatible units: no unsafe mixed-unit graph")
    points.sort(key=lambda p: p.timestamp)
    distinct_times = len({p.timestamp for p in points})
    if distinct_times < 2:
        return SeriesState("UNVERIFIED", subject, metric, tuple(points),
                           "One observed time only; trend unavailable", False)
    verified = all(p.verification_state == "VERIFIED" and p.quality == "READY" for p in points)
    return SeriesState("READY" if verified else "UNVERIFIED", subject, metric, tuple(points),
                       "Source-backed 2D recorded time series; not a diagnosis", True)


def build_series_widget(state: SeriesState, parent=None):
    """Qt 2D polyline over actual recorded points; no 3D or invented data."""
    from PySide6.QtCore import QPointF, Qt
    from PySide6.QtGui import QPainter, QPen, QPolygonF
    from PySide6.QtWidgets import QWidget

    class TimeSeriesWidget(QWidget):
        def __init__(self):
            super().__init__(parent)
            self.setAccessibleName(f"Recorded {state.metric} time series for {state.subject_id}")
            self.setMinimumHeight(180)

        def paintEvent(self, event):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setPen(QPen(Qt.GlobalColor.white))
            if not state.can_plot:
                painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, state.note)
                painter.end()
                return
            width, height = max(1, self.width() - 64), max(1, self.height() - 64)
            values = [p.value for p in state.points]
            t0, t1 = state.points[0].timestamp.timestamp(), state.points[-1].timestamp.timestamp()
            low, high = min(values), max(values)
            span = high - low or 1.0
            coords = [QPointF(32 + (p.timestamp.timestamp()-t0)/(t1-t0)*width,
                              32 + height - (p.value-low)/span*height) for p in state.points]
            painter.setPen(QPen(Qt.GlobalColor.cyan, 2))
            painter.drawPolyline(QPolygonF(coords))
            painter.setPen(QPen(Qt.GlobalColor.white))
            painter.drawText(12, 18, f"{state.metric} ({state.points[0].unit}) — {state.status}")
            painter.drawText(12, self.height()-10, "Recorded source: " + state.points[-1].source_id)
            painter.end()

    return TimeSeriesWidget()
