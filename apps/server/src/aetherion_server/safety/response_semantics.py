"""Missing response versus unconsciousness semantics (Q-0168).

An unanswered check-in NEVER automatically proves loss of consciousness.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class CheckinResponseAssessment:
    subject_id: str
    checkin_id: str
    response_status: str
    unconsciousness_assumed: bool
    medical_emergency_auto_declared: bool
    requires_human_or_witness_verification: bool
    source: str
    assessed_at_utc: str
    reason: str


def assess_checkin_response(
    *,
    subject_id: str,
    checkin_id: str,
    response_received: bool,
    witness_observed_unconscious: bool = False,
    witness_id: str | None = None,
    source: str = "checkin_monitor",
    now: datetime | None = None,
) -> CheckinResponseAssessment:
    """Assess a check-in without equating missing response with unconsciousness."""
    if not subject_id.strip():
        raise ValueError("subject_id must be non-empty")
    if not checkin_id.strip():
        raise ValueError("checkin_id must be non-empty")
    if not source.strip():
        raise ValueError("source must be non-empty")

    ts = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat()

    if witness_observed_unconscious:
        if not witness_id or not witness_id.strip():
            raise ValueError("witness_id is required when witness_observed_unconscious is True")
        return CheckinResponseAssessment(
            subject_id=subject_id,
            checkin_id=checkin_id,
            response_status="WITNESS_REPORTED_UNCONSCIOUS",
            unconsciousness_assumed=False,
            medical_emergency_auto_declared=False,
            requires_human_or_witness_verification=False,
            source=f"witness:{witness_id.strip()}",
            assessed_at_utc=ts,
            reason="Direct witness logged unresponsiveness; explicit human report, not automated inference.",
        )

    if response_received:
        return CheckinResponseAssessment(
            subject_id=subject_id,
            checkin_id=checkin_id,
            response_status="RESPONDED",
            unconsciousness_assumed=False,
            medical_emergency_auto_declared=False,
            requires_human_or_witness_verification=False,
            source=source.strip(),
            assessed_at_utc=ts,
            reason="Crewmember actively responded to check-in.",
        )

    return CheckinResponseAssessment(
        subject_id=subject_id,
        checkin_id=checkin_id,
        response_status="UNANSWERED_CHECKIN",
        unconsciousness_assumed=False,
        medical_emergency_auto_declared=False,
        requires_human_or_witness_verification=True,
        source=source.strip(),
        assessed_at_utc=ts,
        reason="No response received; unanswered check-in does NOT prove unconsciousness. Human or witness follow-up required.",
    )
