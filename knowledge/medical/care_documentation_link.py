"""Reviewed-only condition documentation link for Care action workflows (Q-0146)."""

from __future__ import annotations

from typing import Any

from knowledge.medical.condition_schema import validate_normalized_condition


def get_care_workflow_documentation(
    condition_id: str,
    condition_records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Return reviewed educational material for a condition in Care workflows, or NO_DATA."""
    for record in condition_records:
        if record.get("condition_id") != condition_id:
            continue
        if record.get("review_state") != "APPROVED" or record.get("verification_state") != "READY":
            return {
                "status": "NO_DATA",
                "condition_id": condition_id,
                "reason": "Only APPROVED and READY educational material may appear in Care workflows.",
                "documentation": None,
            }
        validate_normalized_condition(record)
        return {
            "status": "READY",
            "condition_id": condition_id,
            "workflow_role": "EDUCATIONAL_REFERENCE_ONLY",
            "replaces_clinician_judgment": False,
            "documentation": {
                "canonical_title": record["canonical_title"],
                "overview": record["overview"],
                "uncertainties": record["uncertainties"],
                "evidence": record["evidence"],
                "review_state": record["review_state"],
            },
        }

    return {
        "status": "NO_DATA",
        "condition_id": condition_id,
        "reason": "Condition not found in verified library.",
        "documentation": None,
    }
