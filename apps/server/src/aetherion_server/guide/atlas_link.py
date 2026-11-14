"""Guide-to-Body-Atlas link preserving user and science topic context (Q-0162)."""

from __future__ import annotations

from typing import Any


def build_guide_to_atlas_link(
    *,
    user_id: str,
    scope: str,
    science_topic_id: str,
    science_topic_title: str,
    organ_id: str,
    return_route: str = "/guide",
) -> dict[str, Any]:
    """Build a Body Atlas navigation payload preserving current user and science topic."""
    if not user_id.strip():
        raise ValueError("user_id is required")
    if not scope.strip():
        raise ValueError("scope is required")
    if not science_topic_id.strip():
        raise ValueError("science_topic_id is required")
    if not organ_id.strip():
        raise ValueError("organ_id is required")

    clean_organ = organ_id.strip()
    return {
        "link_type": "GUIDE_TO_BODY_ATLAS",
        "target_route": f"/atlas/organ/{clean_organ}",
        "organ_id": clean_organ,
        "preserved_context": {
            "user_id": user_id.strip(),
            "scope": scope.strip(),
            "science_topic_id": science_topic_id.strip(),
            "science_topic_title": science_topic_title.strip(),
            "return_route": return_route.strip() or "/guide",
        },
        "is_live_telemetry": False,
    }
