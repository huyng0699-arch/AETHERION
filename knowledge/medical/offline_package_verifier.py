"""Offline licensed document packager and disconnected integrity verifier (Q-0147)."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def package_licensed_document(
    src_file: Path,
    bundle_dir: Path,
    metadata: dict[str, Any],
) -> Path:
    """Package a licensed document for offline use while preserving exact provenance and SHA-256."""
    if not src_file.is_file():
        raise FileNotFoundError(f"Source document not found: {src_file}")
    if metadata.get("relicensed_under_apache_2_0") is not False:
        raise ValueError("Packaged third-party/NASA document must have relicensed_under_apache_2_0=False")
    for req in ("doc_id", "title", "publisher", "source_url", "license_or_terms"):
        val = metadata.get(req)
        if not isinstance(val, str) or not val.strip():
            raise ValueError(f"Missing required metadata field: {req}")

    bundle_dir.mkdir(parents=True, exist_ok=True)
    doc_id = metadata["doc_id"]
    dest_file = bundle_dir / f"{doc_id}{src_file.suffix}"
    shutil.copy2(src_file, dest_file)
    digest = sha256_file(dest_file)

    manifest = {
        "doc_id": doc_id,
        "filename": dest_file.name,
        "sha256": digest,
        "title": metadata["title"],
        "publisher": metadata["publisher"],
        "author": metadata.get("author", metadata["publisher"]),
        "doi": metadata.get("doi"),
        "date": metadata.get("date", ""),
        "source_url": metadata["source_url"],
        "license_or_terms": metadata["license_or_terms"],
        "relicensed_under_apache_2_0": False,
        "is_live_telemetry": False,
    }
    manifest_path = bundle_dir / f"{doc_id}.manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path


def open_offline_document(bundle_dir: Path, doc_id: str) -> dict[str, Any]:
    """Open a packaged document completely disconnected and verify SHA-256 and metadata."""
    manifest_path = bundle_dir / f"{doc_id}.manifest.json"
    if not manifest_path.is_file():
        return {"status": "NO_DATA", "doc_id": doc_id, "metadata": None, "content_bytes": None}

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    doc_path = bundle_dir / manifest["filename"]
    if not doc_path.is_file():
        return {"status": "NO_DATA", "doc_id": doc_id, "metadata": manifest, "content_bytes": None}

    actual_sha = sha256_file(doc_path)
    if actual_sha != manifest.get("sha256"):
        return {
            "status": "ERROR",
            "reason": "SHA-256 mismatch on offline document",
            "doc_id": doc_id,
            "metadata": manifest,
            "content_bytes": None,
        }

    return {
        "status": "READY",
        "offline_verified": True,
        "doc_id": doc_id,
        "metadata": manifest,
        "content_bytes": doc_path.read_bytes(),
    }
