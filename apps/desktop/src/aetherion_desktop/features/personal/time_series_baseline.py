"""Authenticated Personal Health 2D trend and observed-sample reference mean.

No prefilled measurement, clinical normal range or fabricated baseline. NASA
research/test fixtures and cabin measurements are excluded from personal views.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite


@dataclass(frozen=True)
class PersonalPoint:
    measured_at: datetime
    value: float
    unit: str
    source_id: str
    quality: str
    verification_state: str


@dataclass(frozen=True)
class PersonalSeries:
    status: str
    subject_id: str
    metric: str
    points: tuple[PersonalPoint, ...]
    unit: str | None
    sample_reference_mean: float | None
    note: str
    can_plot: bool


def _empty(status: str, subject: str, metric: str, note: str) -> PersonalSeries:
    return PersonalSeries(status, subject, metric, (), None, None, note, False)


def _time(raw: object) -> datetime:
    if not isinstance(raw, str):
        raise ValueError("missing timestamp")
    t = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if t.tzinfo is None or t.utcoffset() is None:
        raise ValueError("missing timestamp timezone")
    return t.astimezone(timezone.utc)


def personal_series_from_api(subject_id: str, metric: str, http_status: int | None,
                             payload: object, *, now: datetime | None = None,
                             stale_seconds: int = 3600) -> PersonalSeries:
    """Read only original, authorized observations from /observations/series."""
    if not subject_id or not metric or stale_seconds < 1:
        raise ValueError("explicit subject/metric and positive stale threshold required")
    if http_status in (401, 403):
        return _empty("DENIED", subject_id, metric, "Subject authorization denied")
    if http_status is None or http_status == 503:
        return _empty("OFFLINE", subject_id, metric, "No server connection; no inferred health state")
    if http_status != 200:
        return _empty("ERROR", subject_id, metric, "Server request failed")
    if (not isinstance(payload, dict) or payload.get("subject_id") != subject_id or
            payload.get("metric") != metric or not isinstance(payload.get("points"), list)):
        return _empty("ERROR", subject_id, metric, "Response identity or schema mismatch")
    rows = payload["points"]
    if payload.get("count", len(rows)) != len(rows):
        return _empty("ERROR", subject_id, metric, "Server count mismatch")
    clock = now or datetime.now(timezone.utc)
    if clock.tzinfo is None or clock.utcoffset() is None:
        raise ValueError("reference clock must include timezone")
    clock = clock.astimezone(timezone.utc)
    points = []
    try:
        for row in rows:
            if not isinstance(row, dict) or row.get("subject_id") != subject_id or row.get("metric") != metric:
                raise ValueError("cross-subject/metric record")
            if row.get("scope") not in {"CREW", "crew", "personal"}:
                raise ValueError("not an individual measurement")
            source, unit = row.get("source_id"), row.get("unit")
            quality, verification = row.get("quality"), row.get("verification_state")
            if any(not isinstance(v, str) or not v.strip() for v in (source, unit, quality, verification)):
                raise ValueError("missing provenance")
            if quality not in {"READY", "NO_DATA", "STALE", "OFFLINE", "DENIED", "ERROR", "UNVERIFIED"}:
                raise ValueError("invalid record quality")
            if verification == "TEST_FIXTURE" or source.lower().startswith(("nasa_osdr:", "research:")):
                continue
            number = row.get("value")
            if isinstance(number, bool) or not isinstance(number, (int, float)) or not isfinite(number):
                raise ValueError("invalid numeric value")
            measured = _time(row.get("observed_at"))
            received = _time(row.get("received_at"))
            if received < measured:
                raise ValueError("received before observed")
            if measured > clock:
                raise ValueError("future time is not a historic observation")
            if quality == "READY" and verification != "VERIFIED":
                quality = "UNVERIFIED"
            elif quality == "READY" and (clock - measured).total_seconds() > stale_seconds:
                quality = "STALE"
            points.append(PersonalPoint(measured, float(number), unit, source, quality, verification))
    except (ValueError, TypeError, OverflowError):
        return _empty("ERROR", subject_id, metric, "Invalid personal measurement provenance")
    if not points:
        return _empty("NO_DATA", subject_id, metric, "No real, source-backed personal observations")
    if len({p.unit for p in points}) != 1:
        return _empty("ERROR", subject_id, metric, "Mixed measurement units cannot be charted")
    points.sort(key=lambda p: p.measured_at)
    times = {p.measured_at for p in points}
    if len(times) < 2:
        return PersonalSeries("UNVERIFIED", subject_id, metric, tuple(points), points[0].unit,
                              None, "Only one distinct observed time; no trend/baseline inferred", False)
    # A sample arithmetic mean is NOT a medically validated or personal normal range.
    reference_mean = sum(p.value for p in points) / len(points)
    quality = "STALE" if all(p.quality == "STALE" for p in points) else (
        "READY" if all(p.quality == "READY" for p in points) else "UNVERIFIED")
    return PersonalSeries(quality, subject_id, metric, tuple(points), points[0].unit,
                          reference_mean, f"Reference: arithmetic mean of {len(points)} recorded samples, "
                          "not a normal range or diagnosis", True)


def build_personal_series_widget(series: PersonalSeries, parent=None):
    """Native 2D chart for source-backed measurements only; no fake markers."""
    from PySide6.QtCore import QPointF, Qt
    from PySide6.QtGui import QPainter, QPen, QPolygonF
    from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

    root = QWidget(parent)
    lay = QVBoxLayout(root)
    lay.addWidget(QLabel(series.note))

    class SeriesCanvas(QWidget):
        def __init__(self):
            super().__init__(root)
            self.setMinimumHeight(180)
            self.setAccessibleName(f"Personal recorded {series.metric} 2D time series")

        def paintEvent(self, event):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(Qt.GlobalColor.white))
            if not series.can_plot:
                painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, series.note)
                painter.end()
                return
            ts = [point.measured_at.timestamp() for point in series.points]
            vals = [point.value for point in series.points]
            w, h = max(1.0, self.width()-64.0), max(1.0, self.height()-64.0)
            lo, hi = min(vals), max(vals)
            pts = [QPointF(32+(t-ts[0])/(ts[-1]-ts[0])*w,
                           32+(hi-v)/(hi-lo or 1.0)*h) for t,v in zip(ts,vals)]
            painter.setPen(QPen(Qt.GlobalColor.cyan, 2))
            painter.drawPolyline(QPolygonF(pts))
            painter.setPen(QPen(Qt.GlobalColor.white))
            painter.drawText(8, 18, f"{series.metric} ({series.unit}) · {series.status}")
            painter.drawText(8, self.height()-10,
                             f"Observed mean: {series.sample_reference_mean:g} {series.unit}; not clinical baseline")
            painter.end()

    lay.addWidget(SeriesCanvas())
    return root
