"""Non-diagnostic provenance and uncertainty evaluation for Care (Q-0095).

Only checks data identity, age, timestamps, sources and verification labels.
No symptoms, numerical clinical thresholds, treatments, automatic triage, or
illness probabilities are computed. Human clinical review remains separate.
"""
from __future__ import annotations

from dataclasses import dataclass, is_dataclass, asdict
from datetime import datetime, timezone
import math
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class QualityFinding:
    observation_uid: str
    state: str
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class QualitySummary:
    state: str
    findings: tuple[QualityFinding, ...]
    reviewed_observations: int
    clinical_status: str = "NOT_ASSESSED"
    requires_human_review: bool = True
    note: str = "Source/data quality is not a diagnosis or a recommendation to treat."


def _timestamp(value: Any) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError("missing time")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid time") from exc
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("timezone missing")
    return result.astimezone(timezone.utc)


def evaluate_provenance(
    subject_id: str,
    observations: Sequence[Mapping[str, Any] | Any],
    *,
    now: datetime | None = None,
    stale_after_seconds: int = 3600,
) -> QualitySummary:
    """Audit records already filtered by server subject authorization.

    Never use this function to authorize access. A mismatched subject fails
    closed and suppresses every finding. NO_DATA and unverified information
    cannot imply a person is well, ill, unconscious or in need of treatment.
    """
    if not isinstance(subject_id, str) or not subject_id.strip():
        raise ValueError("subject_id is required")
    if not isinstance(observations, (list, tuple)) or len(observations) > 500:
        raise ValueError("Expected a list of at most 500 authorized observations")
    if not isinstance(stale_after_seconds, int) or stale_after_seconds <= 0:
        raise ValueError("stale_after_seconds must be positive")
    clock = now or datetime.now(timezone.utc)
    if not isinstance(clock, datetime) or clock.tzinfo is None or clock.utcoffset() is None:
        raise ValueError("Time reference must include UTC offset")
    clock = clock.astimezone(timezone.utc)

    normalized: list[Mapping[str, Any]] = []
    for item in observations:
        if is_dataclass(item) and not isinstance(item, type):
            item = asdict(item)
        if not isinstance(item, Mapping):
            return QualitySummary("ERROR", (), 0, note="Malformed observation container; no clinical assessment")
        if item.get("subject_id") != subject_id.strip():
            return QualitySummary("DENIED", (), 0, note="Unauthorized/mismatched subject; no observations disclosed")
        normalized.append(item)

    if not normalized:
        return QualitySummary("NO_DATA", (), 0, note="No source-backed measurements; missing data has no health meaning")

    findings: list[QualityFinding] = []
    seen_uids: set[str] = set()
    for item in normalized:
        uid = str(item.get("observation_uid") or "").strip()
        if not uid or uid in seen_uids:
            return QualitySummary("ERROR", (), 0, note="Missing or repeated observation identity")
        seen_uids.add(uid)
        try:
            for key in ("source_id", "unit", "metric", "scope", "quality", "verification_state"):
                value = item.get(key)
                if not isinstance(value, str) or not value.strip():
                    raise ValueError(f"missing {key}")
            reading = float(item.get("value"))
            if not math.isfinite(reading):
                raise ValueError("nonfinite value")
            observed = _timestamp(item.get("observed_at"))
            received = _timestamp(item.get("received_at"))
        except (ValueError, TypeError, OverflowError):
            findings.append(QualityFinding(uid, "ERROR", ("Invalid source, unit, value or time provenance",)))
            continue

        quality = str(item["quality"]).upper()
        verification = str(item["verification_state"]).upper()
        reasons: list[str] = []
        if quality in ("ERROR", "DENIED", "OFFLINE"):
            state = quality
            reasons.append("Technical or permission state from canonical observation source")
        elif quality == "NO_DATA":
            state = "NO_DATA"
            reasons.append("No recorded measurement is available")
        elif quality == "STALE" or (clock - observed).total_seconds() > stale_after_seconds:
            state = "STALE"
            reasons.append("Observation is older than the selected freshness window")
        elif observed > clock or received < observed:
            state = "UNVERIFIED"
            reasons.append("Future event time or inconsistent observation/receipt clock")
        elif quality != "READY" or verification != "VERIFIED":
            state = "UNVERIFIED"
            reasons.append("Recorded source quality has not been independently verified")
        else:
            # Even independently verified provenance is not a medical verdict.
            state = "PROVENANCE_PRESENT"
            reasons.append("Required source/identity/time metadata present; no clinical assessment")
        findings.append(QualityFinding(uid, state, tuple(reasons)))

    observed_states = {x.state for x in findings}
    for state in ("DENIED", "ERROR", "OFFLINE", "STALE", "UNVERIFIED", "NO_DATA"):
        if state in observed_states:
            return QualitySummary(state, tuple(findings), len(findings))
    return QualitySummary("PROVENANCE_PRESENT", tuple(findings), len(findings))
