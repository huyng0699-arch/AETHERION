"""Guide-to-Care canonical episode handoff preserving source and subject context (Q-0161)."""

from __future__ import annotations

from typing import Any

CARE_STAGES = ("GATHER", "EVALUATE", "ACT", "RECHECK")


def build_guide_to_care_handoff(
    *,
    subject_id: str,
    scope: str,
    episode_id: str,
    selected_source: dict[str, Any],
    current_stage: str = "GATHER",
) -> dict[str, Any]:
    """Build a canonical Care episode handoff payload from a Guide source and subject."""
    if not subject_id.strip():
        raise ValueError("subject_id is required")
    if not scope.strip():
        raise ValueError("scope is required")
    if not episode_id.strip():
        raise ValueError("episode_id is required")
    if current_stage not in CARE_STAGES:
        raise ValueError(f"Invalid care stage: {current_stage!r}")

    source_url = str(selected_source.get("source_url", ""))
    if not source_url.startswith("https://"):
        raise ValueError("selected_source.source_url must use https://")
    if selected_source.get("is_live_telemetry") is True:
        raise ValueError("Guide reference source must never claim is_live_telemetry=True")

    return {
        "handoff_type": "GUIDE_TO_CARE_EPISODE",
        "canonical_episode_id": episode_id.strip(),
        "subject_id": subject_id.strip(),
        "scope": scope.strip(),
        "care_flow": list(CARE_STAGES),
        "current_stage": current_stage,
        "human_agency_required": True,
        "auto_diagnosed": False,
        "is_educational_context_only": True,
        "attached_source": {
            "entry_id": selected_source.get("entry_id", ""),
            "title": selected_source.get("title", ""),
            "publisher": selected_source.get("publisher", "NASA"),
            "source_url": source_url,
            "verification_status": selected_source.get("verification_status", "UNVERIFIED"),
            "is_live_telemetry": False,
        },
        "target_route": f"/care/episodes/{episode_id.strip()}",
    }
