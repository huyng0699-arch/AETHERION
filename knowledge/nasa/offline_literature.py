"""Offline loader for packaged, source-attributed NASA literature and five-hazard modules."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

NASA_DIR = Path(__file__).resolve().parent
HAZARDS_DIR = NASA_DIR / "hazards"

REQUIRED_HAZARD_FILES = (
    "space_radiation.json",
    "isolation_confinement.json",
    "distance_from_earth.json",
    "gravity_fields_placeholder_check",
)


def load_offline_nasa_library(base_dir: Path = NASA_DIR) -> dict[str, Any]:
    """Load packaged NASA references from local disk without any network access."""
    challenge = json.loads((base_dir / "challenge_2026.json").read_text(encoding="utf-8"))
    resources = json.loads((base_dir / "official_resources.json").read_text(encoding="utf-8"))
    osdr = json.loads((base_dir / "osdr_datasets.json").read_text(encoding="utf-8"))
    rights = json.loads((base_dir / "dataset_rights_and_transforms.json").read_text(encoding="utf-8"))
    registry = json.loads((base_dir / "source_registry.json").read_text(encoding="utf-8"))
    cliff_status = json.loads((base_dir / "cliff_119_status.json").read_text(encoding="utf-8"))

    hazards_dir = base_dir / "hazards"
    hazard_files = (
        "space_radiation.json",
        "isolation_confinement.json",
        "distance_from_earth.json",
        "altered_gravity.json",
        "hostile_closed_environment.json",
    )
    hazards = {}
    for fname in hazard_files:
        payload = json.loads((hazards_dir / fname).read_text(encoding="utf-8"))
        hazards[payload["hazard_id"]] = payload

    return {
        "offline_mode": True,
        "is_live_telemetry": False,
        "challenge_2026": challenge,
        "official_resources": resources,
        "osdr_datasets": osdr,
        "dataset_rights_and_transforms": rights,
        "source_registry": registry,
        "cliff_119_status": cliff_status,
        "hazards": hazards,
    }
