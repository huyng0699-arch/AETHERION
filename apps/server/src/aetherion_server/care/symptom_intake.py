"""Optional self-reported Care check-in contract (Q-0094).

Pure validation: no database writes, AI, diagnosis, notification, or automatic
care escalation. Skipping never creates a 'healthy' or 'no-symptoms' record.
A future authorized Care API may accept the explicit report after its own checks.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

ANSWERS = frozenset({"YES", "NO", "UNKNOWN", "SKIP"})
IMPACT = frozenset({"NONE", "MILD", "MODERATE", "SEVERE", "UNKNOWN"})
MAX_NOTE_CHARS = 2000


def _identifier(value: str, name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be text")
    cleaned = value.strip()
    if not 1 <= len(cleaned) <= 80 or any(ord(char) < 32 for char in cleaned):
        raise ValueError(f"{name} must be 1-80 printable characters")
    return cleaned


def _note(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("note must be text")
    if len(value) > MAX_NOTE_CHARS:
        raise ValueError("note is too long")
    if any(ord(c) < 32 and c not in "\r\n\t" for c in value):
        raise ValueError("note contains unsupported control characters")
    return value.replace("\r\n", "\n").strip()


def prepare_optional_checkin(
    *,
    subject_id: str | None,
    actor_id: str | None,
    answer: str,
    note: str = "",
    impact: str = "UNKNOWN",
    explicit_consent: bool = False,
    reported_at: datetime | None = None,
) -> dict[str, Any] | None:
    """Prepare an explicit draft, or None on SKIP, without persistence.

    'NO' is only a user answer at a time; it is not a clinician's health verdict.
    NO_DATA (no report) and a recorded explicit NO are separate states.
    """
    if answer not in ANSWERS:
        raise ValueError("answer must be YES, NO, UNKNOWN or SKIP")
    if answer == "SKIP":
        # Intentionally ignore all other fields: do not collect identifiers,
        # sensitive notes or timestamps for someone declining symptom intake.
        return None
    if explicit_consent is not True:
        raise ValueError("Explicit consent is required for a voluntary report")
    person = _identifier(subject_id, "subject_id")
    actor = _identifier(actor_id, "actor_id")
    if impact not in IMPACT:
        raise ValueError("impact must be a declared self-reported value")
    cleaned_note = _note(note)
    moment = reported_at or datetime.now(timezone.utc)
    if not isinstance(moment, datetime) or moment.tzinfo is None or moment.utcoffset() is None:
        raise ValueError("reported_at must have a timezone")
    return {
        "kind": "USER_REPORTED_CONCERN" if answer == "YES" else "VOLUNTARY_USER_CHECKIN",
        "subject_id": person,
        "actor_id": actor,
        "answer": answer,
        "impact": impact,
        "note": cleaned_note,
        "source_id": "manual_user_report",
        "scope": "personal",
        "quality": "UNVERIFIED",
        "verification_state": "SELF_REPORTED",
        "reported_at": moment.astimezone(timezone.utc).isoformat(),
        "clinical_assessment": None,
        "persistence_state": "NOT_SAVED",
    }
