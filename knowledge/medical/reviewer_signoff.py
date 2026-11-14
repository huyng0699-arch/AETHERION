"""Healthcare expert reviewer sign-off and evidence grading tracker (Q-0149)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

VALID_EVIDENCE_GRADES = {
    "LEVEL_1_SYSTEMATIC_REVIEW",
    "LEVEL_2_NASA_HRP_EVIDENCE",
    "LEVEL_3_COHORT_OR_OSDR",
    "LEVEL_4_CASE_OR_EXPERT_CONSENSUS",
    "UNGRADED",
}

VALID_DECISIONS = {"APPROVED", "NEEDS_REVISION", "REJECTED"}


def create_reviewer_signoff(
    *,
    condition_id: str,
    reviewer_name: str,
    reviewer_credentials: str,
    reviewed_at_utc: str,
    content_version: str,
    evidence_grade: str,
    decision: str,
    notes: str = "",
) -> dict[str, Any]:
    """Create and validate a healthcare expert reviewer sign-off record."""
    if not condition_id.strip():
        raise ValueError("condition_id is required")
    if not reviewer_name.strip():
        raise ValueError("reviewer_name is required")
    if not reviewer_credentials.strip():
        raise ValueError("reviewer_credentials is required")
    if not content_version.strip():
        raise ValueError("content_version is required")
    if evidence_grade not in VALID_EVIDENCE_GRADES:
        raise ValueError(f"Invalid evidence_grade: {evidence_grade!r}")
    if decision not in VALID_DECISIONS:
        raise ValueError(f"Invalid decision: {decision!r}")

    # Validate ISO-8601 UTC timestamp
    if not reviewed_at_utc.endswith("Z"):
        raise ValueError("reviewed_at_utc must be an ISO-8601 UTC timestamp ending in 'Z'")
    datetime.fromisoformat(reviewed_at_utc.replace("Z", "+00:00"))

    if decision == "APPROVED" and evidence_grade == "UNGRADED":
        raise ValueError("Cannot APPROVE condition content with evidence_grade='UNGRADED'")

    return {
        "condition_id": condition_id.strip(),
        "reviewer_name": reviewer_name.strip(),
        "reviewer_credentials": reviewer_credentials.strip(),
        "reviewed_at_utc": reviewed_at_utc,
        "content_version": content_version.strip(),
        "evidence_grade": evidence_grade,
        "decision": decision,
        "notes": notes.strip(),
    }


def evaluate_signoff_status(signoff: dict[str, Any] | None, *, current_version: str) -> str:
    """Return READY, STALE, UNVERIFIED, or NO_DATA for a condition's reviewer sign-off."""
    if signoff is None:
        return "NO_DATA"
    if signoff.get("decision") != "APPROVED":
        return "UNVERIFIED"
    if signoff.get("content_version") != current_version:
        return "STALE"
    return "READY"
