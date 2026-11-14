"""Latest source-backed observation per metric/scope/unit for Personal Today.

A dashboard summary is NOT a diagnosis. Keep originals in the server history;
never merge measurements with different units or different observation scopes.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, TypeVar

T = TypeVar("T")


def latest_metric_cards(cards: Iterable[T]) -> tuple[T, ...]:
    """Return newest card for each independent metric, scope and unit."""
    newest: dict[tuple[str, str, str], tuple[datetime, T]] = {}
    for card in cards:
        metric = getattr(card, "metric", "")
        scope = getattr(card, "scope", "")
        unit = getattr(card, "unit", "")
        observed = getattr(card, "observed_at", "")
        source = getattr(card, "source_id", "")
        if not all(isinstance(x, str) and x.strip() for x in (metric, scope, unit, observed, source)):
            raise ValueError("A displayed metric must contain scope, unit, time and source")
        try:
            stamp = datetime.fromisoformat(observed.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("Invalid observation timestamp") from exc
        if stamp.tzinfo is None or stamp.utcoffset() is None:
            raise ValueError("Observation time must include a timezone")
        stamp = stamp.astimezone(timezone.utc)
        key = (scope.casefold(), metric.casefold(), unit.casefold())
        previous = newest.get(key)
        # Ties keep the first record, preserving the server's stable ordering.
        if previous is None or stamp > previous[0]:
            newest[key] = (stamp, card)
    return tuple(
        card for _, card in sorted(
            newest.values(), key=lambda pair: pair[0], reverse=True
        )
    )
