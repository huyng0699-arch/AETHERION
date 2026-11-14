"""Resolve Guide citations to accessible Encyclopedia / NASA entries (Q-0154)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def build_citation_index(repo_root: Path | None = None) -> dict[str, dict[str, Any]]:
    root = repo_root or _default_repo_root()
    index: dict[str, dict[str, Any]] = {}

    registry = _read_json(root / "knowledge" / "nasa" / "source_registry.json")
    if registry:
        for item in registry.get("items", []):
            cid = item["item_id"]
            index[cid] = {
                "citation_id": cid,
                "title": f"{item.get('publisher', 'NASA')} ({item.get('quest_id', 'ref')})",
                "local_path": item.get("local_path", ""),
                "source_url": item["source_uri"],
                "publisher": item.get("publisher", "NASA"),
                "verification_status": item.get("validation_state", "UNVERIFIED"),
                "is_live_telemetry": False,
            }

    osdr = _read_json(root / "knowledge" / "nasa" / "osdr_datasets.json")
    if osdr:
        for ds in osdr.get("datasets", []):
            cid = ds["osd_id"]
            index[cid] = {
                "citation_id": cid,
                "title": ds["title"],
                "local_path": "knowledge/nasa/osdr_datasets.json",
                "source_url": ds["url"],
                "publisher": ds.get("publisher", "NASA OSDR"),
                "verification_status": ds.get("verification_status", "UNVERIFIED"),
                "is_live_telemetry": False,
            }

    hazards_dir = root / "knowledge" / "nasa" / "hazards"
    if hazards_dir.is_dir():
        for hpath in sorted(hazards_dir.glob("*.json")):
            hdata = _read_json(hpath)
            if not hdata or "hazard_id" not in hdata:
                continue
            cid = hdata["hazard_id"]
            sources = hdata.get("primary_sources", [])
            primary_url = sources[0]["url"] if sources else "https://www.nasa.gov/hrp/"
            index[cid] = {
                "citation_id": cid,
                "title": hdata.get("title", cid),
                "local_path": f"knowledge/nasa/hazards/{hpath.name}",
                "source_url": primary_url,
                "publisher": "NASA Human Research Program (HRP)",
                "verification_status": "VERIFIED_OFFICIAL_SOURCE",
                "is_live_telemetry": False,
            }

    return index


def resolve_citation(citation_id: str, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _default_repo_root()
    cleaned = citation_id.strip()
    if not cleaned:
        return {"citation_id": citation_id, "status": "NOT_FOUND", "route": None, "entry": None}

    if cleaned.lower().startswith("cliff-") or cleaned.lower().startswith("cliff_119_"):
        cliff = _read_json(root / "knowledge" / "medical" / "cliff_119_audit.json")
        verified = int(cliff.get("verified_local_originals", 0)) if cliff else 0
        if verified == 0:
            return {
                "citation_id": cleaned,
                "status": "UNAVAILABLE_UNIMPORTED",
                "route": None,
                "entry": None,
                "reason": "Original NASA IMM CliFF 119 document is not imported locally (0/119); no full text fabricated.",
            }

    index = build_citation_index(repo_root=root)
    entry = index.get(cleaned)
    if not entry:
        return {"citation_id": cleaned, "status": "NOT_FOUND", "route": None, "entry": None}

    local_file = root / entry["local_path"]
    if not entry["local_path"] or not local_file.is_file():
        return {
            "citation_id": cleaned,
            "status": "UNAVAILABLE_MISSING_FILE",
            "route": None,
            "entry": entry,
        }

    return {
        "citation_id": cleaned,
        "status": "ACCESSIBLE",
        "route": f"encyclopedia/entry/{cleaned}",
        "entry": entry,
    }
