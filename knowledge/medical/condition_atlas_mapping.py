"""Condition-to-Atlas organ mapping preserving selected condition context (Q-0145)."""

from __future__ import annotations

from pathlib import Path
import json
import sqlite3
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_APPROVED_MODELS_PATH = REPO_ROOT / "knowledge" / "anatomy" / "approved_models.json"
DEFAULT_CLIFF_SQLITE_PATH = REPO_ROOT / "knowledge" / "nasa" / "cliff_119_2023" / "AETHERION_NASA_CLIFF_119.sqlite"

BODY_SYSTEM_TO_ORGAN = {
    "neuro-ocular": {"organ_id": "eye_optic_nerve", "atlas_region": "head_neuro_ocular"},
    "nervous": {"organ_id": "brain_cns", "atlas_region": "head_neuro_ocular"},
    "cardiovascular": {"organ_id": "heart_vasculature", "atlas_region": "thorax_cardiovascular"},
    "musculoskeletal": {"organ_id": "skeleton_muscle", "atlas_region": "systemic_musculoskeletal"},
    "vestibular": {"organ_id": "inner_ear_vestibular", "atlas_region": "head_vestibular"},
    "immune_hematopoietic": {"organ_id": "bone_marrow_lymphatic", "atlas_region": "systemic_immune"},
}

ANATOMICAL_STRUCTURE_LINKS: dict[str, dict[str, Any]] = {
    "mandible_visible_human_male": {
        "anatomical_id": "mandible_visible_human_male",
        "atlas_region": "head_craniofacial_mandible",
        "body_system": "musculoskeletal",
        "label_en": "Mandible (Lower Jaw)",
        "label_vi": "Xương hàm dưới",
        "cliff_article_ids": ["CLIFF-020", "CLIFF-022", "CLIFF-023", "CLIFF-038"],
        "topic_tags": ["dental", "craniofacial", "mandible", "oral_trauma"],
    },
    "eye_optic_nerve": {
        "anatomical_id": "eye_optic_nerve",
        "atlas_region": "head_neuro_ocular",
        "body_system": "neuro-ocular",
        "label_en": "Eye & Optic Nerve",
        "label_vi": "Mắt và dây thần kinh thị giác",
        "cliff_article_ids": ["CLIFF-096", "CLIFF-113", "CLIFF-114"],
        "topic_tags": ["sans", "neuro_ocular", "vision"],
    },
    "brain_cns": {
        "anatomical_id": "brain_cns",
        "atlas_region": "head_neuro_ocular",
        "body_system": "nervous",
        "label_en": "Brain & Central Nervous System",
        "label_vi": "Não và hệ thần kinh trung ương",
        "cliff_article_ids": ["CLIFF-038", "CLIFF-039", "CLIFF-040", "CLIFF-041", "CLIFF-042"],
        "topic_tags": ["head_injury", "headache", "co2", "space_adaptation"],
    },
    "heart_vasculature": {
        "anatomical_id": "heart_vasculature",
        "atlas_region": "thorax_cardiovascular",
        "body_system": "cardiovascular",
        "label_en": "Heart & Vasculature",
        "label_vi": "Tim và hệ mạch máu",
        "cliff_article_ids": ["CLIFF-009", "CLIFF-014", "CLIFF-015"],
        "topic_tags": ["cardiovascular", "arrhythmia", "orthostatic"],
    },
    "skeleton_muscle": {
        "anatomical_id": "skeleton_muscle",
        "atlas_region": "systemic_musculoskeletal",
        "body_system": "musculoskeletal",
        "label_en": "Musculoskeletal System",
        "label_vi": "Hệ cơ xương khớp",
        "cliff_article_ids": ["CLIFF-045", "CLIFF-046", "CLIFF-053", "CLIFF-055", "CLIFF-099"],
        "topic_tags": ["fracture", "bone_loss", "musculoskeletal"],
    },
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


def map_anatomical_structure_to_knowledge(
    anatomical_id: str,
    *,
    models_path: Path | None = None,
    db_path: Path | None = None,
) -> dict[str, Any]:
    """Map a picked anatomical structure ID to verified NASA CliFF topics and model origin.

    Never claims clinical diagnosis from 3D geometry or picked structure.
    """
    clean_id = (anatomical_id or "").strip()
    if not clean_id or clean_id not in ANATOMICAL_STRUCTURE_LINKS:
        return {
            "status": "NO_DATA",
            "anatomical_id": clean_id,
            "origin": None,
            "linked_documents": [],
            "topic_tags": [],
            "diagnostic_claim": False,
            "educational_reference_only": True,
            "disclaimer": "Educational anatomical reference only; 3D geometry or picked structure never constitutes a clinical diagnosis.",
        }

    spec = ANATOMICAL_STRUCTURE_LINKS[clean_id]
    m_path = models_path or DEFAULT_APPROVED_MODELS_PATH
    origin: dict[str, Any] | None = None
    if m_path.exists():
        catalog = json.loads(m_path.read_text(encoding="utf-8"))
        for model in catalog.get("models", []):
            if model.get("anatomical_id") == clean_id:
                origin = {
                    "filename": model.get("filename"),
                    "source_url": model.get("source_url"),
                    "author": model.get("author"),
                    "license": model.get("license"),
                    "rights_status": model.get("rights_status"),
                    "sha256": model.get("sha256"),
                    "purpose": model.get("purpose"),
                }
                break

    sqlite_path = db_path or DEFAULT_CLIFF_SQLITE_PATH
    linked_docs: list[dict[str, str]] = []
    candidate_ids = list(spec.get("cliff_article_ids", []))
    if sqlite_path.exists() and candidate_ids:
        placeholders = ",".join("?" for _ in candidate_ids)
        conn = sqlite3.connect(f"file:{sqlite_path}?mode=ro", uri=True)
        try:
            rows = conn.execute(
                f"SELECT article_id, display_title, category FROM articles WHERE article_id IN ({placeholders}) ORDER BY slot",
                candidate_ids,
            ).fetchall()
            for art_id, title, category in rows:
                linked_docs.append(
                    {
                        "article_id": str(art_id),
                        "display_title": str(title),
                        "category": str(category),
                        "route": f"/knowledge/articles/{art_id}",
                    }
                )
        finally:
            conn.close()
    else:
        for art_id in candidate_ids:
            linked_docs.append({"article_id": art_id, "route": f"/knowledge/articles/{art_id}"})

    return {
        "status": "READY" if linked_docs else "NO_DATA",
        "anatomical_id": clean_id,
        "atlas_region": spec["atlas_region"],
        "body_system": spec["body_system"],
        "label_en": spec["label_en"],
        "label_vi": spec["label_vi"],
        "origin": origin,
        "linked_documents": linked_docs,
        "topic_tags": list(spec["topic_tags"]),
        "diagnostic_claim": False,
        "educational_reference_only": True,
        "disclaimer": "Educational anatomical reference only; 3D geometry or picked structure never constitutes a clinical diagnosis.",
    }
