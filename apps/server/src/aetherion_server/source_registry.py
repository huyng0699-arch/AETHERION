"""Source registry API resolving recorded scientific/media/anatomy sources (Q-0052)."""

from __future__ import annotations

from functools import lru_cache
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query

REPO_ROOT = Path(__file__).resolve().parents[4]
CLIFF_RECORDS_DIR = REPO_ROOT / "knowledge" / "nasa" / "cliff_119_2023" / "records"
ANATOMY_MODELS_PATH = REPO_ROOT / "knowledge" / "anatomy" / "approved_models.json"
SYMPTOMS_REF_PATH = REPO_ROOT / "knowledge" / "symptoms" / "ASTRA_819_REFERENCE.json"

router = APIRouter(prefix="/api/v1/sources", tags=["Source Registry"])


@lru_cache(maxsize=1)
def _load_registry() -> dict[str, dict[str, Any]]:
    registry: dict[str, dict[str, Any]] = {}

    if CLIFF_RECORDS_DIR.is_dir():
        for rec_path in sorted(CLIFF_RECORDS_DIR.glob("CLIFF-*.json")):
            try:
                data = json.loads(rec_path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            src = data.get("source")
            if isinstance(src, dict) and src.get("source_id"):
                sid = str(src["source_id"])
                registry[sid] = {
                    "source_id": sid,
                    "kind": "nasa_cliff_record",
                    "article_id": data.get("article_id"),
                    "title": src.get("title") or data.get("display_title"),
                    "publisher": src.get("publisher"),
                    "source_uri": src.get("final_url") or src.get("source_url"),
                    "license": src.get("license_identifier"),
                    "attribution": src.get("attribution"),
                    "verification_status": src.get("verification_state", "UNKNOWN"),
                    "content_sha256": src.get("content_sha256"),
                }

    if ANATOMY_MODELS_PATH.is_file():
        try:
            manifest = json.loads(ANATOMY_MODELS_PATH.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            manifest = None
        # The canonical AETHERION manifest is {"schema_version": ..., "models": [...]};
        # accept an older list only for compatibility, never assume it is a list.
        models = manifest.get("models") if isinstance(manifest, dict) else manifest
        if isinstance(models, list):
            for item in models:
                if not isinstance(item, dict):
                    continue
                mid = item.get("anatomical_id") or item.get("id")
                if not isinstance(mid, str) or not mid.strip():
                    continue
                mid = mid.strip()
                if len(mid) > 160 or any(ord(ch) < 32 for ch in mid):
                    continue
                declared_sha = item.get("sha256")
                valid_sha = (declared_sha.lower() if isinstance(declared_sha, str)
                             and re.fullmatch(r"[0-9a-fA-F]{64}", declared_sha)
                             else None)
                rights = str(item.get("rights_status") or "").upper()
                sid = f"anatomy:{mid}"
                registry[sid] = {
                    "source_id": sid,
                    "kind": "anatomy_3d_model",
                    "anatomical_id": mid,
                    "title": item.get("title_en") or item.get("title_vi")
                             or item.get("label") or item.get("title") or mid,
                    "publisher": item.get("author") or item.get("creator") or item.get("source"),
                    "source_uri": item.get("source_url") or item.get("url"),
                    "license": item.get("license"),
                    "attribution": item.get("citation") or item.get("attribution"),
                    # Rights metadata is self-declared in the audited manifest.
                    # Listing alone is not proof that a mesh file is present or hashed.
                    "verification_status": (
                        "RIGHTS_MANIFEST_APPROVED_BINARY_UNVERIFIED"
                        if rights == "APPROVED" else "UNVERIFIED"
                    ),
                    "content_sha256": valid_sha,
                    "content_integrity_state": "EXPECTED_MANIFEST_SHA256_NOT_REHASHED",
                }

    if SYMPTOMS_REF_PATH.is_file():
        try:
            # Hash the actual UTF-8 file bytes. A 40-character Git blob SHA-1
            # is never a SHA-256 and must not be labelled as one.
            symptom_sha256 = hashlib.sha256(SYMPTOMS_REF_PATH.read_bytes()).hexdigest()
        except OSError:
            pass
        else:
            registry["astra-symptom-vocabulary-819"] = {
                "source_id": "astra-symptom-vocabulary-819",
                "kind": "symptom_vocabulary",
                "title": "ASTRA 819 Symptom Label Reference",
                "publisher": "AETHERION Owner-Authorized Legacy Vocabulary Import",
                "source_uri": "knowledge/symptoms/ASTRA_819_REFERENCE.json",
                "license": "Project-Internal Reference",
                "attribution": "Exact 819-label symptom vocabulary; clinical_validation_completed=false",
                "verification_status": "UNREVIEWED_VOCABULARY_ONLY",
                "content_sha256": symptom_sha256,
                "content_integrity_state": "SHA256_COMPUTED_FROM_LOCAL_BYTES",
            }

    return registry


def list_sources(*, kind: str = "", limit: int = 50) -> dict[str, Any]:
    reg = _load_registry()
    items = list(reg.values())
    if kind.strip():
        k = kind.strip().lower()
        items = [x for x in items if str(x.get("kind", "")).lower() == k]
    return {
        "total": len(items),
        "items": items[: max(1, min(limit, 200))],
    }


def resolve_source(source_id: str) -> dict[str, Any] | None:
    return _load_registry().get(source_id.strip())


@router.get("")
def get_sources(
    kind: str = Query("", max_length=60),
    limit: int = Query(50, ge=1, le=200),
):
    return list_sources(kind=kind, limit=limit)


@router.get("/{source_id:path}")
def get_source(source_id: str):
    item = resolve_source(source_id)
    if item is None:
        raise HTTPException(status_code=404, detail=f"Unknown source_id: {source_id}")
    return item
