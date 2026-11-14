"""Reject invented or unapproved medical citations in Guide responses (Q-0158)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .citations import build_citation_index


def filter_approved_citations(
    proposed_ids: list[str],
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Filter candidate citation IDs against the verified local registry."""
    index = build_citation_index(repo_root=repo_root)
    approved: list[dict[str, Any]] = []
    rejected: list[dict[str, str]] = []

    for cid in proposed_ids:
        cleaned = cid.strip()
        entry = index.get(cleaned)
        if entry is None:
            rejected.append(
                {
                    "citation_id": cid,
                    "reason": "UNVERIFIED_OR_INVENTED: Not present in approved local registry.",
                }
            )
            continue
        if entry.get("verification_status") == "VERIFIED_NOT_IMPORTED":
            rejected.append(
                {
                    "citation_id": cid,
                    "reason": "VERIFIED_NOT_IMPORTED: Referenced source has not been imported locally.",
                }
            )
            continue
        approved.append(entry)

    return {
        "approved": approved,
        "rejected": rejected,
        "uncertainty_marked": len(rejected) > 0 or len(approved) == 0,
    }
