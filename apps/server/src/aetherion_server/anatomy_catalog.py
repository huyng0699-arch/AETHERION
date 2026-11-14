"""Server-controlled anatomical mesh catalog and verified file delivery (Q-0467)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_ANATOMY_DIR = REPO_ROOT / "knowledge" / "anatomy"
DEFAULT_CATALOG_PATH = DEFAULT_ANATOMY_DIR / "approved_models.json"

ALLOWED_MESH_CONTENT_TYPES = {
    ".stl": "model/stl",
    ".obj": "model/obj",
    ".ply": "application/x-ply",
    ".glb": "model/gltf-binary",
    ".gltf": "model/gltf+json",
}
REQUIRED_FIELDS = (
    "anatomical_id",
    "filename",
    "sha256",
    "source_url",
    "author",
    "license",
    "rights_status",
    "derivative_license",
)
_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def _safe_mesh_path(models_dir: Path, filename: str) -> Path | None:
    if not filename or Path(filename).is_absolute():
        return None
    root = models_dir.resolve()
    candidate = (root / filename).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    if candidate.suffix.lower() not in ALLOWED_MESH_CONTENT_TYPES:
        return None
    if not candidate.is_file():
        return None
    return candidate


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while chunk := fh.read(65536):
            h.update(chunk)
    return h.hexdigest()


def list_approved_models(
    *,
    catalog_path: Path | None = None,
    models_dir: Path | None = None,
) -> dict[str, Any]:
    """Return only rights-approved, path-audited, SHA-256-verified anatomical meshes."""
    target_catalog = catalog_path or DEFAULT_CATALOG_PATH
    base_dir = models_dir or target_catalog.parent
    if not target_catalog.is_file():
        return {
            "status": "NO_DATA",
            "models": [],
            "notice": "Approved anatomy catalog not found.",
        }
    data = json.loads(target_catalog.read_text(encoding="utf-8"))
    approved: list[dict[str, Any]] = []
    for entry in data.get("models", []):
        if not isinstance(entry, dict):
            continue
        if any(not str(entry.get(field, "")).strip() for field in REQUIRED_FIELDS):
            continue
        if str(entry.get("rights_status", "")).upper() != "APPROVED":
            continue
        ident = str(entry["anatomical_id"]).strip()
        if not _ID_RE.fullmatch(ident):
            continue
        mesh_path = _safe_mesh_path(base_dir, str(entry["filename"]).strip())
        if mesh_path is None:
            continue
        actual_sha = _sha256_file(mesh_path)
        if actual_sha != str(entry["sha256"]).strip().lower():
            continue
        content_type = ALLOWED_MESH_CONTENT_TYPES[mesh_path.suffix.lower()]
        item: dict[str, Any] = {
            "anatomical_id": ident,
            "filename": mesh_path.relative_to(Path(base_dir).resolve()).as_posix(),
            "size_bytes": mesh_path.stat().st_size,
            "sha256": actual_sha,
            "content_type": content_type,
            "source_url": entry["source_url"],
            "author": entry["author"],
            "license": entry["license"],
            "rights_status": "APPROVED",
            "derivative_license": entry["derivative_license"],
        }
        if "lod" in entry:
            item["lod"] = entry["lod"]
        approved.append(item)

    return {
        "status": "READY" if approved else "NO_DATA",
        "models": approved,
        "notice": data.get("notice", ""),
    }


def resolve_approved_model_file(
    anatomical_id: str,
    *,
    catalog_path: Path | None = None,
    models_dir: Path | None = None,
) -> tuple[Path, dict[str, Any]] | None:
    """Resolve one verified approved mesh file for delivery; returns None if unauthorized/missing."""
    if not _ID_RE.fullmatch(anatomical_id):
        return None
    target_catalog = catalog_path or DEFAULT_CATALOG_PATH
    base_dir = models_dir or target_catalog.parent
    catalog = list_approved_models(catalog_path=target_catalog, models_dir=base_dir)
    for item in catalog["models"]:
        if item["anatomical_id"] == anatomical_id:
            mesh_path = _safe_mesh_path(base_dir, item["filename"])
            if mesh_path is not None:
                return mesh_path, item
    return None
