"""Symptom-to-condition reference crosswalk without automatic diagnosis (Q-0144)."""

from __future__ import annotations

from typing import Any

SYMPTOM_ALIASES = {
    "blurry vision": "visual acuity shift",
    "blurred vision": "visual acuity shift",
    "lightheaded": "dizziness",
    "lightheadedness": "dizziness",
    "fast heart rate": "tachycardia",
}


def normalize_symptom_term(term: str) -> str:
    """Normalize a user-entered symptom term to canonical search vocabulary."""
    cleaned = " ".join(term.strip().lower().split())
    return SYMPTOM_ALIASES.get(cleaned, cleaned)


def crosswalk_symptoms_to_topics(
    symptom_terms: list[str],
    entries: list[dict[str, Any]],
) -> dict[str, Any]:
    """Return possible reference topics matching symptom terms without automatic diagnosis."""
    normalized_terms = [normalize_symptom_term(t) for t in symptom_terms if t and t.strip()]
    if not normalized_terms or not entries:
        return {
            "status": "NO_DATA",
            "is_diagnosis": False,
            "auto_diagnosed": False,
            "clinical_disclaimer": "Reference topic crosswalk only — not an automatic medical diagnosis.",
            "normalized_terms": normalized_terms,
            "possible_topics": [],
        }

    topics: list[dict[str, Any]] = []
    for entry in entries:
        if entry.get("verification_state") != "READY" or entry.get("review_state") != "APPROVED":
            continue
        entry_symptoms = [str(s).strip().lower() for s in entry.get("symptoms", [])]
        matched = [
            term for term in normalized_terms
            if any(term in sym or sym in term for sym in entry_symptoms)
        ]
        if matched:
            topics.append(
                {
                    "condition_id": entry["condition_id"],
                    "canonical_title": entry["canonical_title"],
                    "matched_terms": matched,
                    "differential": entry.get("differential", []),
                    "uncertainties": entry.get("uncertainties", []),
                    "is_diagnosis": False,
                }
            )

    topics.sort(key=lambda t: (-len(t["matched_terms"]), t["canonical_title"].lower()))
    return {
        "status": "READY" if topics else "NO_DATA",
        "is_diagnosis": False,
        "auto_diagnosed": False,
        "clinical_disclaimer": "Reference topic crosswalk only — not an automatic medical diagnosis.",
        "normalized_terms": normalized_terms,
        "possible_topics": topics,
    }
