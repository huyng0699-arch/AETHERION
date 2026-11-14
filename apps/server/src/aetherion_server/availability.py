"""Deterministic data availability computation (NO_DATA, READY, STALE) without clinical claims (Q-0050)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _parse_utc(iso_str: str) -> datetime:
    dt = datetime.fromisoformat(iso_str)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def compute_availability(
    observations: list[dict[str, Any]],
    *,
    stale_after_seconds: int = 3600,
    now: datetime | None = None,
) -> dict[str, Any]:
    if stale_after_seconds <= 0:
        raise ValueError("stale_after_seconds must be positive")
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    else:
        current = current.astimezone(timezone.utc)

    if not observations:
        return {
            "availability_status": "NO_DATA",
            "observation_count": 0,
            "latest_observed_at": None,
            "age_seconds": None,
            "metrics_present": [],
            "stale_after_seconds": stale_after_seconds,
            "clinical_interpretation": "NONE_DETERMINISTIC_AVAILABILITY_ONLY",
            "note": "No live observations recorded. NO_DATA does not indicate normal or healthy status.",
        }

    latest_item = max(observations, key=lambda item: (_parse_utc(item["observed_at"]), int(item["id"])))
    latest_dt = _parse_utc(latest_item["observed_at"])
    age_seconds = max(0.0, (current - latest_dt).total_seconds())
    availability_status = "READY" if age_seconds <= stale_after_seconds else "STALE"
    metrics_present = sorted({str(item["metric"]) for item in observations})

    return {
        "availability_status": availability_status,
        "observation_count": len(observations),
        "latest_observed_at": latest_item["observed_at"],
        "age_seconds": round(age_seconds, 3),
        "metrics_present": metrics_present,
        "stale_after_seconds": stale_after_seconds,
        "clinical_interpretation": "NONE_DETERMINISTIC_AVAILABILITY_ONLY",
        "note": (
            "Data availability is computed solely from observation timestamps; "
            "no clinical diagnosis or health conclusion is inferred."
        ),
    }
