"""Q-0074: fail-closed projection for a crew-wide Mission dashboard.

A crew-wide screen is NOT an authenticated per-person clinical screen.
Only authorized technical/environmental aggregates pass this boundary.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite
from typing import Mapping, Iterable

# Deliberately exclude all clinical, vital-sign, self-report and personal fields.
PUBLIC_TECHNICAL_METRICS = frozenset({
    "cabin_temperature_c", "cabin_pressure_kpa", "cabin_co2_ppm",
    "habitat_humidity_pct", "network_latency_ms", "system_uptime_s",
})
SAFE_FIELDS = frozenset({"metric", "value", "unit", "source_id", "observed_at", "scope", "verification_state"})
EXPECTED_UNITS = {
    "cabin_temperature_c": "C",
    "cabin_pressure_kpa": "kPa",
    "cabin_co2_ppm": "ppm",
    "habitat_humidity_pct": "%",
    "network_latency_ms": "ms",
    "system_uptime_s": "s",
}
FORBIDDEN_FIELDS = frozenset({
    "subject_id", "crew_id", "patient_id", "user_id", "name", "email",
    "birth_date", "diagnosis", "symptoms", "medical_history", "notes",
    "heart_rate", "ecg", "blood_pressure", "medication", "location",
})


@dataclass(frozen=True)
class CrewWideTechnicalReading:
    metric: str
    value: float
    unit: str
    source_id: str
    observed_at: str
    verification_state: str


@dataclass(frozen=True)
class CrewWideProjection:
    state: str
    readings: tuple[CrewWideTechnicalReading, ...]
    note: str


def project_crew_wide(
    records: Iterable[Mapping[str, object]],
    *,
    authorized_for_crew_dashboard: bool,
    now: datetime,
    max_age_seconds: int = 3600,
) -> CrewWideProjection:
    """Only display source-backed, non-personal, current technical measurements.

    Reject an entire response when a row contains identity/clinical fields.
    Unknown technical metrics are dropped rather than rendered or inferred.
    Authorization MUST be established by the backend, not by this boolean alone.
    """
    if not authorized_for_crew_dashboard:
        return CrewWideProjection("DENIED", (), "Crew-wide dashboard authorization required")
    if now.tzinfo is None or now.utcoffset() is None or max_age_seconds <= 0:
        raise ValueError("valid timezone-aware clock and age threshold required")
    if isinstance(records, (str, bytes, Mapping)):
        raise ValueError("expected a sequence of source-backed records")
    clock = now.astimezone(timezone.utc)
    accepted = []
    for record in records:
        if not isinstance(record, Mapping):
            raise ValueError("malformed observation")
        # Reject any extra field: a future server schema must be audited before
        # it can cross this boundary, including nested/unexpected payloads.
        if set(record) & FORBIDDEN_FIELDS or set(record) - SAFE_FIELDS:
            return CrewWideProjection("REDACTED", (), "Personal or unaudited fields withheld")
        if record.get("scope") not in {"CABIN", "HABITAT", "SYSTEM", "NETWORK"}:
            continue
        metric = record.get("metric")
        if metric not in PUBLIC_TECHNICAL_METRICS:
            continue
        value = record.get("value")
        unit = record.get("unit")
        source = record.get("source_id")
        verification = record.get("verification_state")
        stamp = record.get("observed_at")
        if (isinstance(value, bool) or not isinstance(value, (int, float))
                or not isfinite(value) or unit != EXPECTED_UNITS[metric]
                or not isinstance(source, str) or not source.strip()
                or not isinstance(verification, str) or verification not in {"VERIFIED", "UNVERIFIED"}
                or not isinstance(stamp, str)):
            return CrewWideProjection("ERROR", (), "Invalid technical source/provenance")
        try:
            measured = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        except ValueError:
            return CrewWideProjection("ERROR", (), "Invalid measurement timestamp")
        if measured.tzinfo is None or measured.utcoffset() is None:
            return CrewWideProjection("ERROR", (), "Timestamp without timezone")
        age = (clock - measured.astimezone(timezone.utc)).total_seconds()
        if age < 0 or age > max_age_seconds:
            continue
        accepted.append(CrewWideTechnicalReading(metric, float(value), unit, source,
                                                  measured.astimezone(timezone.utc).isoformat(),
                                                  verification))
    accepted.sort(key=lambda item: (item.metric, item.observed_at))
    return CrewWideProjection("READY" if accepted else "NO_DATA", tuple(accepted),
                              "Technical/environmental observations only; no personal health data "
                              "or diagnosis. Verification is source-specific.")
