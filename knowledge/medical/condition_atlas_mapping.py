"""Condition-to-Atlas organ mapping preserving selected condition context (Q-0145)."""

from __future__ import annotations

from typing import Any

BODY_SYSTEM_TO_ORGAN = {
    "neuro-ocular": {"organ_id": "eye_optic_nerve", "atlas_region": "head_neuro_ocular"},
    "nervous": {"organ_id": "brain_cns", "atlas_region": "head_neuro_ocular"},
    "cardiovascular": {"organ_id": "heart_vasculature", "atlas_region": "thorax_cardiovascular"},
    "musculoskeletal": {"organ_id": "skeleton_muscle", "atlas_region": "systemic_musculoskeletal"},
    "vestibular": {"organ_id": "inner_ear_vestibular", "atlas_region": "head_vestibular"},
    "immune_hematopoietic": {"organ_id": "bone_marrow_lymphatic", "atlas_region": "systemic_immune"},
}


def map_condition_to_atlas(condition: dict[str, Any]) -> dict[str, Any]:
    """Resolve Atlas organ target(s) for a condition while preserving condition context."""
    context = {
        "condition_id": condition.get("condition_id", ""),
        "canonical_title": condition.get("canonical_title", ""),
        "verification_state": condition.get("verification_state", "UNVERIFIED"),
        "return_route": f"/encyclopedia/condition/{condition.get('condition_id', '')}",
    }

    targets: list[dict[str, str]] = []
    seen_organs: set[str] = set()
    for system in condition.get("body_systems", []):
        key = str(system).strip().lower()
        mapping = BODY_SYSTEM_TO_ORGAN.get(key)
        if mapping and mapping["organ_id"] not in seen_organs:
            seen_organs.add(mapping["organ_id"])
            targets.append(dict(mapping))

    return {
        "status": "READY" if targets else "NO_DATA",
        "primary_organ": targets[0] if targets else None,
        "organ_targets": targets,
        "preserved_condition_context": context,
    }
