"""Route Guide questions to verified NASA five-hazard reference modules (Q-0152)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

HAZARD_KEYWORDS: dict[str, tuple[str, ...]] = {
    "space_radiation": ("radiation", "dosimeter", "msv", "cosmic", "solar", "dna", "shielding"),
    "isolation_and_confinement": ("isolation", "confinement", "sleep", "circadian", "mood", "crew", "behavioral"),
    "distance_from_earth": ("distance", "delay", "latency", "autonomous", "mars", "resupply", "communication"),
    "gravity_fields": ("gravity", "microgravity", "bone", "muscle", "fluid", "vestibular", "orthostatic"),
    "hostile_closed_environments": ("co2", "habitat", "closed", "cabin", "air", "water", "microbiome", "hostile"),
}


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def load_nasa_hazards(repo_root: Path | None = None) -> dict[str, dict[str, Any]]:
    root = repo_root or _default_repo_root()
    hazards_dir = root / "knowledge" / "nasa" / "hazards"
    loaded: dict[str, dict[str, Any]] = {}
    if not hazards_dir.is_dir():
        return loaded
    for path in sorted(hazards_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        hid = data.get("hazard_id")
        if hid:
            loaded[str(hid)] = data
    return loaded


def route_question_to_hazard(question: str, repo_root: Path | None = None) -> dict[str, Any]:
    hazards = load_nasa_hazards(repo_root=repo_root)
    q_lower = question.strip().lower()
    if not q_lower:
        return {
            "question": question,
            "status": "NO_QUERY",
            "target_route": None,
            "hazard_id": None,
            "primary_sources": [],
            "is_live_telemetry": False,
        }

    best_id: str | None = None
    best_score = 0
    for hid, keywords in HAZARD_KEYWORDS.items():
        if hid not in hazards:
            continue
        score = sum(1 for kw in keywords if kw in q_lower)
        if score > best_score:
            best_score = score
            best_id = hid

    if best_id is None or best_score == 0:
        return {
            "question": question,
            "status": "UNMATCHED",
            "target_route": None,
            "hazard_id": None,
            "primary_sources": [],
            "is_live_telemetry": False,
        }

    hazard = hazards[best_id]
    return {
        "question": question,
        "status": "ROUTED",
        "target_route": f"explore/hazards/{best_id}",
        "hazard_id": best_id,
        "title": hazard.get("title", best_id),
        "primary_sources": hazard.get("primary_sources", []),
        "affected_organ_systems": hazard.get("affected_organ_systems", []),
        "limitations": hazard.get("limitations", []),
        "is_live_telemetry": bool(hazard.get("is_live_telemetry", False)),
    }
