"""Offline end-to-end Guide pipeline with cloud AI disabled (Q-0165)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from aetherion_server.guide.atlas_link import build_guide_to_atlas_link
from aetherion_server.guide.care_handoff import build_guide_to_care_handoff
from aetherion_server.guide.hazard_router import route_question_to_hazard
from aetherion_server.guide.low_bandwidth_reader import build_low_bandwidth_article_payload
from aetherion_server.guide.search import load_guide_entries


def run_offline_guide_flow(
    *,
    query: str,
    user_id: str,
    scope: str,
    repo_root: Path | None = None,
    cloud_ai_enabled: bool = False,
) -> dict[str, Any]:
    """Execute verified local Guide search, hazard routing, and citations without cloud AI."""
    if cloud_ai_enabled:
        raise ValueError("Offline acceptance requires cloud_ai_enabled=False")

    entries = load_guide_entries(repo_root=repo_root)
    q_lower = query.strip().lower()
    matched_entries = [
        e for e in entries
        if q_lower in str(e.get("title", "")).lower()
        or q_lower in str(e.get("summary", "")).lower()
        or any(q_lower in str(t).lower() for t in e.get("tags", []))
    ]
    hazard_route = route_question_to_hazard(query, repo_root=repo_root)

    reader_payload = (
        build_low_bandwidth_article_payload(matched_entries[0])
        if matched_entries
        else None
    )
    care_handoff = (
        build_guide_to_care_handoff(
            subject_id=user_id,
            scope=scope,
            episode_id="EP-OFFLINE-001",
            selected_source=matched_entries[0],
        )
        if matched_entries
        else None
    )
    atlas_link = (
        build_guide_to_atlas_link(
            user_id=user_id,
            scope=scope,
            science_topic_id=str(hazard_route["hazard_id"]),
            science_topic_title=str(hazard_route.get("title", "")),
            organ_id="heart_vasculature",
        )
        if hazard_route.get("status") == "ROUTED"
        else None
    )

    citations = [
        {
            "entry_id": e["entry_id"],
            "source_url": e["source_url"],
            "verification_status": e["verification_status"],
            "is_live_telemetry": False,
        }
        for e in matched_entries
    ]

    return {
        "status": "READY" if (matched_entries or hazard_route.get("status") == "ROUTED") else "NO_DATA",
        "cloud_ai_used": False,
        "offline_verified": True,
        "matched_count": len(matched_entries),
        "citations": citations,
        "hazard_route": hazard_route,
        "reader_payload": reader_payload,
        "care_handoff": care_handoff,
        "atlas_link": atlas_link,
    }
