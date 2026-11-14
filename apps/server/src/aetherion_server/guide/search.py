"""Offline, search-first Guide catalog and deterministic keyword search (Q-0151)."""

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


def load_guide_entries(repo_root: Path | None = None) -> list[dict[str, Any]]:
    root = repo_root or _default_repo_root()
    entries: list[dict[str, Any]] = []

    registry = _read_json(root / "knowledge" / "nasa" / "source_registry.json")
    if registry:
        for item in registry.get("items", []):
            entries.append(
                {
                    "entry_id": item["item_id"],
                    "title": f"{item.get('publisher', 'NASA')} ({item.get('quest_id', 'ref')})",
                    "summary": f"Verified registry item at {item.get('local_path', '')} [{item.get('validation_state', 'UNVERIFIED')}].",
                    "source_url": item["source_uri"],
                    "publisher": item.get("publisher", "NASA"),
                    "verification_status": item.get("validation_state", "UNVERIFIED"),
                    "is_live_telemetry": bool(item.get("is_live_telemetry", False)),
                    "tags": ["nasa", "registry", str(item.get("quest_id", "")).lower()],
                    "local_path": item.get("local_path", ""),
                }
            )

    osdr = _read_json(root / "knowledge" / "nasa" / "osdr_datasets.json")
    if osdr:
        for ds in osdr.get("datasets", []):
            hazards = [str(h) for h in ds.get("hazard_domains", [])]
            entries.append(
                {
                    "entry_id": ds["osd_id"],
                    "title": f"{ds['osd_id']}: {ds['title']}",
                    "summary": f"Mission: {ds.get('mission_or_platform', 'N/A')}. Limitations: {ds.get('limitations', '')}",
                    "source_url": ds["url"],
                    "publisher": ds.get("publisher", "NASA OSDR"),
                    "verification_status": ds.get("verification_status", "UNVERIFIED"),
                    "is_live_telemetry": bool(ds.get("is_live_telemetry", False)),
                    "tags": ["osdr", "nasa", ds["osd_id"].lower(), *hazards],
                    "local_path": "knowledge/nasa/osdr_datasets.json",
                }
            )

    cliff = _read_json(root / "knowledge" / "medical" / "cliff_119_audit.json")
    if cliff:
        verified_count = int(cliff.get("verified_local_originals", 0))
        expected_count = int(cliff.get("expected_count", 119))
        entries.append(
            {
                "entry_id": "nasa-imm-cliff-119-audit",
                "title": f"NASA IMM CliFF 119 Audit ({verified_count}/{expected_count} local originals)",
                "summary": cliff.get(
                    "note",
                    f"CliFF 119 local archive status: {verified_count}/{expected_count} verified.",
                ),
                "source_url": cliff.get("source_url", "https://www.nasa.gov/integrated-medical-model-documentation/"),
                "publisher": "NASA Integrated Medical Model (IMM)",
                "verification_status": cliff.get("status", "VERIFIED_NOT_IMPORTED"),
                "is_live_telemetry": False,
                "tags": ["cliff", "119", "medical", "audit"],
                "local_path": "knowledge/medical/cliff_119_audit.json",
            }
        )

    return entries


def search_guide(
    query: str = "",
    repo_root: Path | None = None,
    *,
    ai_enabled: bool = False,
) -> dict[str, Any]:
    """Search sourced Guide entries offline without requiring AI or a symptom."""
    entries = load_guide_entries(repo_root=repo_root)
    cleaned = query.strip().lower()
    if not cleaned:
        matched = entries
    else:
        terms = [t for t in cleaned.split() if t]
        matched = []
        for entry in entries:
            haystack = " ".join(
                [
                    entry["entry_id"],
                    entry["title"],
                    entry["summary"],
                    entry["publisher"],
                    " ".join(entry["tags"]),
                ]
            ).lower()
            if all(term in haystack for term in terms):
                matched.append(entry)

    return {
        "query": query,
        "requires_ai": False,
        "requires_symptom": False,
        "ai_used": False if not ai_enabled else False,
        "total_available": len(entries),
        "count": len(matched),
        "results": matched,
    }
