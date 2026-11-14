"""UTC conductor and evidence-preserving segmentation for AETHERION telemetry.

An independent pure-Python model: no Qt, simulated measurements or clinical
interpolation. Inspired by the documented Open MCT time-bounds concepts, but
this is an AETHERION-native implementation, not NASA source or branding.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from statistics import median
from typing import Iterable, Any
import math

MIN_SPAN = timedelta(minutes=1)
MAX_SPAN = timedelta(days=366)


def utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("UTC-aware datetime required")
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class TimeBounds:
    start: datetime
    end: datetime

    def __post_init__(self):
        start, end = utc(self.start), utc(self.end)
        if not MIN_SPAN <= end - start <= MAX_SPAN:
            raise ValueError("invalid time window (1 minute – 366 days)")
        object.__setattr__(self, "start", start)
        object.__setattr__(self, "end", end)

    @property
    def span(self) -> timedelta:
        return self.end - self.start

    def contains(self, value: datetime) -> bool:
        return self.start <= utc(value) <= self.end

    def as_query(self):
        return {"since": self.start.isoformat().replace("+00:00", "Z"),
                "until": self.end.isoformat().replace("+00:00", "Z")}


class TimeConductor:
    """Shared UTC bounds; 'latest' polls historical API, not a live subscription."""

    def __init__(self, span: timedelta = timedelta(days=7), now: datetime | None = None):
        if not MIN_SPAN <= span <= MAX_SPAN:
            raise ValueError("invalid span")
        end = utc(now or datetime.now(timezone.utc))
        self.mode = "latest"
        self.bounds = TimeBounds(end - span, end)

    def latest(self, span: timedelta | None = None, now: datetime | None = None):
        length = span or self.bounds.span
        end = utc(now or datetime.now(timezone.utc))
        self.bounds = TimeBounds(end - length, end)
        self.mode = "latest"
        return self.bounds

    def fixed(self, start: datetime, end: datetime):
        self.bounds = TimeBounds(start, end)
        self.mode = "fixed"
        return self.bounds

    def pan(self, fraction: float):
        if not math.isfinite(fraction) or abs(fraction) > 10:
            raise ValueError("invalid pan")
        delta = self.bounds.span * fraction
        return self.fixed(self.bounds.start + delta, self.bounds.end + delta)

    def zoom(self, factor: float, anchor_fraction: float = .5):
        if not math.isfinite(factor) or factor <= 0 or not 0 <= anchor_fraction <= 1:
            raise ValueError("invalid zoom")
        span = self.bounds.span * factor
        if span < MIN_SPAN: span = MIN_SPAN
        if span > MAX_SPAN: span = MAX_SPAN
        anchor = self.bounds.start + self.bounds.span * anchor_fraction
        return self.fixed(anchor - span * anchor_fraction,
                          anchor + span * (1 - anchor_fraction))


def series_channel(point: Any) -> tuple[str, str, str]:
    """A channel never merges measurements with different units or scopes."""
    return str(point.metric), str(point.unit), str(point.scope)


def visible_points(points: Iterable[Any], bounds: TimeBounds, channel=None, source=None):
    rows = [p for p in points if bounds.contains(p.observed_at)
            and (channel is None or series_channel(p) == channel)
            and (source is None or p.source_id == source)]
    return sorted(rows, key=lambda p: (utc(p.observed_at), p.source_id))


def eligible_for_line(point: Any) -> bool:
    """Unknown / unreviewed data are scatter-only; quality is not inferred."""
    return str(point.quality).upper() == "READY" and str(point.verification).upper() == "VERIFIED"


def segment_telemetry(points: Iterable[Any], bounds: TimeBounds, channel=None, source=None):
    """Return (source-group points, strict consecutive point pairs, gap count).

    No cross-source or cross-scope joins. No bridge across invalid samples, time
    gaps or unverified quality. Cadence derived only with at least three
    same-source valid samples. No interpolation of missing measurements.
    """
    data = visible_points(points, bounds, channel, source)
    groups: dict[tuple[str, str, str, str], list] = {}
    for p in data:
        key = (p.source_id, p.scope, p.metric, p.unit)
        groups.setdefault(key, []).append(p)
    edges = []
    gaps = 0
    for key, group in groups.items():
        confirmed = [p for p in group if eligible_for_line(p)]
        deltas = [(utc(b.observed_at) - utc(a.observed_at)).total_seconds()
                  for a, b in zip(confirmed, confirmed[1:])]
        positive = [v for v in deltas if v > 0]
        if len(confirmed) < 3 or len(positive) < 2:
            continue  # Unknown cadence: points only, never imply continuity.
        baseline = min(median(positive), min(positive) * 3)
        max_gap = max(1.0, baseline * 1.6)
        for left, right in zip(group, group[1:]):
            delta = (utc(right.observed_at) - utc(left.observed_at)).total_seconds()
            if eligible_for_line(left) and eligible_for_line(right) and 0 < delta <= max_gap:
                edges.append((left, right))
            elif delta > max_gap or not (eligible_for_line(left) and eligible_for_line(right)):
                gaps += 1
    return groups, edges, gaps


def utc_ticks(bounds: TimeBounds, count: int = 5):
    if count < 2 or count > 20: raise ValueError("invalid tick count")
    return [bounds.start + bounds.span * (i / (count - 1)) for i in range(count)]
