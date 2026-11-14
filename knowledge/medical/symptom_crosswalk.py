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


def build_reviewed_differential_link(
    *,
    condition_id: str,
    canonical_title: str,
    symptoms: list[str],
    evidence_citations: list[dict[str, str]],
    author: str,
    reviewed_at_utc: str,
    uncertainties: list[str],
    differential: list[str] | None = None,
    is_nasa_cliff_equivalent: bool = False,
) -> dict[str, Any]:
    """Construct a typed, clinically reviewed symptom-to-topic entry without assuming ASTRA=CliFF equivalence."""
    if not condition_id.strip() or not canonical_title.strip():
        raise ValueError("condition_id and canonical_title are required")
    if not symptoms:
        raise ValueError("At least one symptom is required")
    if not evidence_citations:
        raise ValueError("Cited evidence is required for reviewed differential topics")
    if not author.strip() or not reviewed_at_utc.strip():
        raise ValueError("author and reviewed_at_utc are required")
    if not uncertainties:
        raise ValueError("Explicit uncertainty notes are required")
    return {
        "condition_id": condition_id.strip(),
        "canonical_title": canonical_title.strip(),
        "symptoms": [s.strip() for s in symptoms if s.strip()],
        "evidence_citations": list(evidence_citations),
        "author": author.strip(),
        "reviewed_at_utc": reviewed_at_utc.strip(),
        "uncertainties": list(uncertainties),
        "differential": list(differential or []),
        "is_nasa_cliff_equivalent": bool(is_nasa_cliff_equivalent),
        "verification_state": "READY",
        "review_state": "APPROVED",
    }


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
            "astra_cliff_equivalence_assumed": False,
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
            citations = list(entry.get("evidence_citations", []))
            uncertainties = list(entry.get("uncertainties", []))
            topics.append(
                {
                    "condition_id": entry["condition_id"],
                    "canonical_title": entry["canonical_title"],
                    "matched_terms": matched,
                    "differential": entry.get("differential", []),
                    "uncertainties": uncertainties,
                    "uncertainty_recorded": bool(uncertainties),
                    "evidence_citations": citations,
                    "evidence_status": "CITED" if citations else "UNVERIFIED_CITATIONS",
                    "author": entry.get("author", ""),
                    "reviewed_at_utc": entry.get("reviewed_at_utc", ""),
                    "is_nasa_cliff_equivalent": bool(entry.get("is_nasa_cliff_equivalent", False)),
                    "is_diagnosis": False,
                }
            )

    topics.sort(key=lambda t: (-len(t["matched_terms"]), t["canonical_title"].lower()))
    return {
        "status": "READY" if topics else "NO_DATA",
        "is_diagnosis": False,
        "auto_diagnosed": False,
        "astra_cliff_equivalence_assumed": False,
        "clinical_disclaimer": "Reference topic crosswalk only — not an automatic medical diagnosis.",
        "normalized_terms": normalized_terms,
        "possible_topics": topics,
    }
