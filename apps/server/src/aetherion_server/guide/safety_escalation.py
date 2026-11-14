"""Deterministic safety escalation entry operable with AI disabled (Q-0157)."""

from __future__ import annotations

from typing import Any

RED_FLAG_KEYWORDS = (
    "chest pain",
    "shortness of breath",
    "difficulty breathing",
    "unconscious",
    "severe bleeding",
    "stroke",
    "anaphylaxis",
    "radiation sickness",
)


def evaluate_safety_escalation(
    user_text: str = "",
    *,
    ai_enabled: bool = False,
    ai_reachable: bool = False,
) -> dict[str, Any]:
    """Always expose deterministic human assistance entry regardless of AI availability."""
    normalized = user_text.strip().lower()
    matched_flags = [kw for kw in RED_FLAG_KEYWORDS if kw in normalized]
    urgent = len(matched_flags) > 0

    return {
        "assistance_entry_available": True,
        "assistance_route": "safety/assistance",
        "ai_enabled": ai_enabled,
        "ai_reachable": ai_reachable,
        "ai_required": False,
        "escalation_recommended": urgent,
        "matched_red_flags": matched_flags,
        "claimed_dispatch": False,
        "claimed_diagnosis": False,
        "message": (
            "Urgent red-flag keywords detected; deterministic Assistance route is active for human report/acknowledgement."
            if urgent
            else "Deterministic Assistance route remains available for human report/acknowledgement even when AI is disabled."
        ),
    }
