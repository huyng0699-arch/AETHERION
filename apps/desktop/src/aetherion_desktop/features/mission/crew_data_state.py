"""Fail-closed Mission Control data state for authenticated server observations.

The Qt shell supplies *actual* HTTP results. This module performs no network
requests, stores no credentials, and never invents crew measurements. A backend
response is interpreted for precisely one requested subject at a time.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite


QUALITY_STATES = frozenset({"READY", "NO_DATA", "STALE", "OFFLINE", "DENIED", "ERROR", "UNVERIFIED"})
NONLIVE_VERIFICATIONS = frozenset({"TEST_FIXTURE"})


@dataclass(frozen=True)
class CrewMeasurement:
    metric: str
    value: float
    unit: str
    source_id: str
    subject_id: str
    scope: str
    observed_at: str
    received_at: str
    quality: str
    verification_state: str


@dataclass(frozen=True)
class CrewDataState:
    status: str
    subject_id: str
    measurements: tuple[CrewMeasurement, ...]
    message: str
    last_observed_at: str | None = None
    has_more: bool = False
    next_cursor: str | None = None


def _state(status: str, subject_id: str, message: str) -> CrewDataState:
    return CrewDataState(status, subject_id, (), message)


def _parse_time(raw: object) -> datetime:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("timestamp required")
    value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timezone required")
    return value.astimezone(timezone.utc)


def _nonempty(item: dict, key: str) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing {key}")
    return value.strip()


def state_from_server_response(
    subject_id: str,
    http_status: int | None,
    payload: object = None,
    *,
    now: datetime | None = None,
    network_error: bool = False,
    stale_after_seconds: int = 3600,
) -> CrewDataState:
    """Create a screen-safe state from one authenticated API request.

    HTTP errors and invalid provenance fail closed: no partial records survive.
    Research and test fixtures are not considered live astronaut telemetry.
    The caller must discard superseded responses when changing subject IDs.
    """
    if not isinstance(subject_id, str) or not subject_id.strip() or len(subject_id) > 80:
        raise ValueError("requested subject_id must contain 1-80 characters")
    if stale_after_seconds <= 0:
        raise ValueError("stale_after_seconds must be positive")
    if network_error or http_status is None:
        return _state("OFFLINE", subject_id, "No server response; no crew health status inferred")
    if http_status in (401, 403):
        return _state("DENIED", subject_id, "Authentication or subject authorization denied")
    if http_status == 503:
        return _state("OFFLINE", subject_id, "The API or its observation store is unavailable")
    if http_status != 200:
        return _state("ERROR", subject_id, "The server rejected the observation request")

    if not isinstance(payload, dict) or payload.get("subject_id") != subject_id:
        return _state("ERROR", subject_id, "Subject identity mismatch in server response")
    items = payload.get("observations")
    if not isinstance(items, list):
        return _state("ERROR", subject_id, "Missing observations array")
    has_more = payload.get("has_more", False)
    next_cursor = payload.get("next_cursor")
    if not isinstance(has_more, bool) or (has_more and not isinstance(next_cursor, str)):
        return _state("ERROR", subject_id, "Invalid server pagination state")
    if has_more and not next_cursor:
        return _state("ERROR", subject_id, "More records reported without a cursor")
    if next_cursor is not None and (not isinstance(next_cursor, str) or not next_cursor):
        return _state("ERROR", subject_id, "Invalid continuation cursor")
    if not items and has_more:
        return _state("ERROR", subject_id, "Inconsistent empty page with has_more")

    clock = now or datetime.now(timezone.utc)
    if clock.tzinfo is None or clock.utcoffset() is None:
        raise ValueError("now must include a timezone")
    clock = clock.astimezone(timezone.utc)
    rows: list[CrewMeasurement] = []
    excluded_nonlive = 0
    try:
        for item in items:
            if not isinstance(item, dict) or item.get("subject_id") != subject_id:
                raise ValueError("record subject identity mismatch")
            metric = _nonempty(item, "metric")
            unit = _nonempty(item, "unit")
            source = _nonempty(item, "source_id")
            scope = _nonempty(item, "scope")
            verification = _nonempty(item, "verification_state").upper()
            quality = _nonempty(item, "quality").upper()
            if quality not in QUALITY_STATES:
                raise ValueError("unrecognized observation quality")
            value = item.get("value")
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
                raise ValueError("observation value must be finite numeric")
            observed = _parse_time(item.get("observed_at"))
            received = _parse_time(item.get("received_at"))
            if received < observed:
                raise ValueError("received_at precedes observed_at")
            if (scope.lower() == "engineering_test" or
                verification in NONLIVE_VERIFICATIONS or
                source.lower().startswith(("nasa_osdr:", "research:"))):
                excluded_nonlive += 1
                continue
            if quality == "READY" and verification != "VERIFIED":
                quality = "UNVERIFIED"
            if observed > clock:
                quality = "UNVERIFIED"
            elif quality == "READY" and (clock - observed).total_seconds() > stale_after_seconds:
                quality = "STALE"
            rows.append(CrewMeasurement(metric, float(value), unit, source, subject_id, scope,
                                        observed.isoformat(), received.isoformat(), quality, verification))
    except (TypeError, ValueError, OverflowError):
        return _state("ERROR", subject_id, "Untrusted or incomplete observation provenance")
    if not rows:
        message = ("No live observations; research/test fixtures were excluded" if excluded_nonlive
                   else "No recorded observations for this authorized subject")
        return _state("NO_DATA", subject_id, message)

    rows.sort(key=lambda row: row.observed_at, reverse=True)
    if any(row.quality == "READY" for row in rows):
        status = "READY"
    elif all(row.quality == "STALE" for row in rows):
        status = "STALE"
    elif all(row.quality == "OFFLINE" for row in rows):
        status = "OFFLINE"
    else:
        status = "UNVERIFIED"
    message = "Recorded observations with provenance, not a clinical assessment"
    if excluded_nonlive:
        message += "; research/test fixtures excluded"
    return CrewDataState(status, subject_id, tuple(rows), message, rows[0].observed_at,
                         has_more, next_cursor if has_more else None)
