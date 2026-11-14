"""Explain what was measured, when, and by which verified source (Q-0153)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

VALID_STATES = {"READY", "NO_DATA", "STALE", "OFFLINE", "DENIED", "ERROR", "UNVERIFIED"}


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _load_source_index(repo_root: Path | None = None) -> dict[str, dict[str, Any]]:
    root = repo_root or _default_repo_root()
    reg_path = root / "knowledge" / "nasa" / "source_registry.json"
    if not reg_path.is_file():
        return {}
    data = json.loads(reg_path.read_text(encoding="utf-8"))
    return {item["item_id"]: item for item in data.get("items", []) if "item_id" in item}


def explain_observation_provenance(
    observation: dict[str, Any] | None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    if not observation:
        return {
            "verification_state": "NO_DATA",
            "what": None,
            "when": None,
            "source_id": None,
            "verified_source": None,
            "is_live_telemetry": False,
            "explanation": "NO_DATA: No measurement has been recorded. Missing data does not indicate healthy status.",
        }

    metric = observation.get("metric") or "unknown_metric"
    value = observation.get("value")
    unit = observation.get("unit") or "unspecified_unit"
    observed_at = observation.get("observed_at")
    source_id = observation.get("source_id")
    raw_state = str(observation.get("verification_state") or "UNVERIFIED").upper()
    state = raw_state if raw_state in VALID_STATES else "UNVERIFIED"

    source_index = _load_source_index(repo_root=repo_root)
    reg_entry = source_index.get(str(source_id)) if source_id else None

    if not source_id or not observed_at or value is None:
        state = "UNVERIFIED" if state == "READY" else state

    is_live = False if reg_entry is not None else bool(observation.get("is_live_telemetry", False))
    what_str = f"{metric}={value} {unit}" if value is not None else f"{metric} (no value)"
    when_str = str(observed_at) if observed_at else "unknown_time"
    source_label = (
        f"{reg_entry['publisher']} ({reg_entry['source_uri']})"
        if reg_entry
        else (str(source_id) if source_id else "unattributed_source")
    )

    if state == "STALE":
        prefix = "STALE: Measurement is outdated"
    elif state == "OFFLINE":
        prefix = "OFFLINE: Source is currently unreachable"
    elif state == "UNVERIFIED":
        prefix = "UNVERIFIED: Provenance or source verification is incomplete"
    elif state == "NO_DATA":
        prefix = "NO_DATA: No valid measurement available"
    elif state in ("DENIED", "ERROR"):
        prefix = f"{state}: Measurement unavailable due to access or source error"
    else:
        prefix = "READY: Verified measurement"

    research_note = " (historical research reference, not live crew telemetry)" if reg_entry else ""
    explanation = f"{prefix} — {what_str}, observed at {when_str}, from {source_label}{research_note}."

    return {
        "verification_state": state,
        "what": what_str,
        "when": when_str,
        "source_id": source_id,
        "verified_source": reg_entry,
        "is_live_telemetry": is_live,
        "explanation": explanation,
    }
