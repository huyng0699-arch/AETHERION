"""Optional symptom disclosure that never blocks healthy-person navigation (Q-0156)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .hazard_router import route_question_to_hazard
from .search import search_guide


def build_guide_session(
    *,
    disclosed_symptoms: list[str] | None = None,
    query: str = "",
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Build a Guide session where symptom disclosure is strictly optional."""
    cleaned_symptoms = [s.strip() for s in (disclosed_symptoms or []) if s and s.strip()]
    search_result = search_guide(query=query, repo_root=repo_root, ai_enabled=False)

    routed_hazards: list[dict[str, Any]] = []
    if cleaned_symptoms:
        routed = route_question_to_hazard(" ".join(cleaned_symptoms), repo_root=repo_root)
        if routed.get("status") == "ROUTED":
            routed_hazards.append(routed)

    return {
        "symptom_required": False,
        "navigation_blocked": False,
        "healthy_navigation_available": True,
        "disclosed_symptoms": cleaned_symptoms,
        "mode": "SYMPTOM_CONTEXT" if cleaned_symptoms else "HEALTHY_EXPLORATION",
        "search_results": search_result,
        "suggested_hazards": routed_hazards,
        "diagnosis_produced": False,
    }
