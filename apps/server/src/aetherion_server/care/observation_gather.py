"""Fail-closed selection of actual, source-linked observations for Care GATHER.

Caller must obtain records through the server's authenticated, subject-scoped API.
This pure helper never queries SQLite, invents a measurement, diagnoses illness,
or interprets silence / absent measurements as health or unconsciousness.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import math
from typing import Mapping, Sequence, Any


@dataclass(frozen=True)
class GatheredObservation:
    observation_uid: str
    subject_id: str
    metric: str
    value: float
    unit: str
    scope: str
    source_id: str
    observed_at: str
    received_at: str
    recorded_quality: str
    verification_state: str
    effective_quality: str


@dataclass(frozen=True)
class GatherResult:
    status: str  # READY, NO_DATA, STALE, UNVERIFIED, OFFLINE, ERROR, DENIED
    observations: tuple[GatheredObservation, ...]
    ignored_non_live: int
    note: str


def _date(value: object, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} is missing")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} is not ISO-8601") from exc
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError(f"{field} is not timezone aware")
    return dt.astimezone(timezone.utc)


def _text(row: Mapping[str, Any], key: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"required observation provenance missing: {key}")
    return value.strip()


def select_for_care_gather(
    subject_id: str,
    observations: Sequence[Mapping[str, Any]],
    *,
    selected_observation_uids: set[str] | None = None,
    now: datetime | None = None,
    stale_after_seconds: int = 3600,
) -> GatherResult:
    """Return only eligible *recorded* observations with honest quality flags.

    Supplying a subject_id does not grant access. The caller must first enforce
    authenticated subject access through the canonical server. A mixed-subject
    input is entirely rejected rather than exposing anyone else's data.
    """
    if not isinstance(subject_id, str) or not 1 <= len(subject_id.strip()) <= 80:
        raise ValueError("Valid subject_id is required")
    if not isinstance(observations, (list, tuple)) or len(observations) > 500:
        raise ValueError("Expected at most 500 authorized observations")
    if stale_after_seconds <= 0:
        raise ValueError("stale_after_seconds must be positive")
    now = now or datetime.now(timezone.utc)
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("Reference time must have a timezone")
    now_utc = now.astimezone(timezone.utc)
    if selected_observation_uids is not None and not isinstance(selected_observation_uids, set):
        raise ValueError("selected_observation_uids must be a set")

    # Fail before extracting any values if the source includes another subject.
    for item in observations:
        if not isinstance(item, Mapping):
            return GatherResult("ERROR", (), 0, "Malformed authorized observation list")
        if item.get("subject_id") != subject_id.strip():
            return GatherResult("DENIED", (), 0, "Subject identity mismatch; no data disclosed")

    collected: list[GatheredObservation] = []
    ignored_non_live = 0
    for item in observations:
        if item.get("verification_state") == "TEST_FIXTURE" or item.get("scope") == "engineering_test":
            ignored_non_live += 1
            continue
        if selected_observation_uids is not None and item.get("observation_uid") not in selected_observation_uids:
            continue
        try:
            uid = _text(item, "observation_uid")
            metric = _text(item, "metric")
            unit = _text(item, "unit")
            scope = _text(item, "scope")
            source = _text(item, "source_id")
            quality = _text(item, "quality").upper()
            verification = _text(item, "verification_state").upper()
            observed = _date(item.get("observed_at"), "observed_at")
            received = _date(item.get("received_at"), "received_at")
            measured = float(item["value"])
            if not math.isfinite(measured):
                raise ValueError("value is not finite")
            if quality not in {"READY", "NO_DATA", "STALE", "OFFLINE", "DENIED", "ERROR", "UNVERIFIED"}:
                raise ValueError("quality is unknown")
        except (KeyError, ValueError, TypeError, OverflowError):
            return GatherResult("ERROR", (), ignored_non_live,
                                "Observation has invalid numeric, time or provenance fields")
        if quality == "NO_DATA":
            continue  # an empty state is never a recorded measurement
        effective = quality
        if quality == "READY":
            if observed > now_utc:
                effective = "UNVERIFIED"
            elif (now_utc - observed).total_seconds() > stale_after_seconds:
                effective = "STALE"
            elif verification != "VERIFIED":
                effective = "UNVERIFIED"
        collected.append(GatheredObservation(
            uid, subject_id.strip(), metric, measured, unit, scope, source,
            observed.isoformat(), received.isoformat(), quality, verification, effective,
        ))

    if not collected:
        return GatherResult("NO_DATA", (), ignored_non_live,
                            "No eligible recorded measurements; missing data is not a health assessment")
    statuses = {x.effective_quality for x in collected}
    if "ERROR" in statuses:
        status = "ERROR"
    elif "DENIED" in statuses:
        status = "DENIED"
    elif "OFFLINE" in statuses:
        status = "OFFLINE"
    elif "STALE" in statuses:
        status = "STALE"
    elif "UNVERIFIED" in statuses:
        status = "UNVERIFIED"
    else:
        status = "READY"
    return GatherResult(status, tuple(collected), ignored_non_live,
                        "Recorded provenance only; Care evaluation and diagnosis are separate, unimplemented steps")
