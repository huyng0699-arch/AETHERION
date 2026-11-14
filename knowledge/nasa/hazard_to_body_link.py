"""Deterministic routing from NASA five spaceflight hazards to anatomy systems, metrics, or NO_DATA."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from knowledge.nasa.offline_literature import load_offline_nasa_library

HAZARD_BODY_MAP: dict[str, dict[str, Any]] = {
    "space_radiation": {
        "anatomy_systems": ["immune_hematopoietic", "cardiovascular_endothelium", "musculoskeletal_bone_marrow"],
        "relevant_metrics": ["radiation_dose_msv"],
    },
    "isolation_and_confinement": {
        "anatomy_systems": ["behavioral_neurocognitive"],
        "relevant_metrics": ["daily_sleep_hours", "mood_self_report"],
    },
    "distance_from_earth": {
        "anatomy_systems": [],
        "relevant_metrics": [],
    },
    "gravity_fields": {
        "anatomy_systems": ["musculoskeletal", "cardiovascular"],
        "relevant_metrics": ["blood_pressure_mmhg", "heart_rate_bpm"],
    },
    "hostile_closed_environments": {
        "anatomy_systems": ["respiratory_habitat_exposure"],
        "relevant_metrics": ["cabin_co2_ppm", "cabin_o2_kpa", "cabin_temperature_c", "cabin_relative_humidity_pct"],
    },
}


@dataclass(frozen=True)
class HazardRouteResult:
    hazard_id: str
    anatomy_systems: list[str]
    relevant_metrics: list[str]
    matched_observations: list[dict[str, Any]]
    status: str
    primary_sources: list[dict[str, Any]]


def resolve_hazard_route(
    hazard_id: str,
    observations: list[dict[str, Any]] | None = None,
) -> HazardRouteResult:
    if hazard_id not in HAZARD_BODY_MAP:
        raise ValueError(f"Unknown NASA hazard_id: {hazard_id!r}")

    lib = load_offline_nasa_library()
    hazard_doc = lib["hazards"][hazard_id]
    mapping = HAZARD_BODY_MAP[hazard_id]
    relevant = list(mapping["relevant_metrics"])

    matched: list[dict[str, Any]] = []
    if observations:
        relevant_set = set(relevant)
        for obs in observations:
            if obs.get("metric") in relevant_set:
                matched.append(obs)

    status = "READY" if matched else "NO_DATA"
    return HazardRouteResult(
        hazard_id=hazard_id,
        anatomy_systems=list(mapping["anatomy_systems"]),
        relevant_metrics=relevant,
        matched_observations=matched,
        status=status,
        primary_sources=list(hazard_doc.get("primary_sources", [])),
    )
