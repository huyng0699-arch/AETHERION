"""Exact-subject authorization handoff for Personal Health (Q-0089).

Never select a default crew ID or reuse a previous person's profile. The
protected API, not this client helper, remains the authorization authority.
Only machine statuses are produced; UI must localize them via VI/EN catalogs.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping
import unicodedata

from .identity import checked_personal_handoff


@dataclass(frozen=True)
class SubjectSelection:
    status: str
    subject_id: str | None
    record_count: int

    @property
    def can_open(self) -> bool:
        return self.status in {"AUTHORIZED", "NO_DATA"} and self.subject_id is not None


def confirm_subject_from_authorized_response(
    requested_subject: str,
    access_token: str,
    http_status: int | None,
    payload: object,
) -> SubjectSelection:
    """Permit the *exact* requested identity only after matched HTTP 200.

    A successful no-data read is valid authorization, not a healthy reading.
    Malformed responses fail closed. Do not keep tokens or patient data here.
    """
    rejected = SubjectSelection("DENIED", None, 0)
    try:
        subject, _ = checked_personal_handoff(requested_subject, access_token)
    except ValueError:
        return rejected
    if any(unicodedata.category(ch) in {"Cc", "Cf", "Cs"} for ch in subject):
        return rejected
    if http_status in (401, 403) or http_status is None:
        return rejected
    if http_status != 200 or not isinstance(payload, Mapping):
        return SubjectSelection("ERROR", None, 0)
    if payload.get("subject_id") != subject:
        return rejected
    observations = payload.get("observations")
    if not isinstance(observations, list):
        return SubjectSelection("ERROR", None, 0)
    for observation in observations:
        if not isinstance(observation, Mapping) or observation.get("subject_id") != subject:
            return SubjectSelection("ERROR", None, 0)
    return SubjectSelection("NO_DATA" if not observations else "AUTHORIZED",
                            subject, len(observations))
