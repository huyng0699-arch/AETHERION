#!/usr/bin/env python3
"""Acquire medical raster images with explicit file-level rights and byte provenance.

A declared license is NOT independently verified by this tool. Human review of
source, rights statement, clinical accuracy and attribution remains mandatory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

MAX_IMAGE_BYTES = 25 * 1024 * 1024
EXTENSIONS = {"image/png": ".png", "image/jpeg": ".jpg", "image/gif": ".gif", "image/webp": ".webp"}
REQUIRED = ("source_url", "rights_url", "license", "author", "title", "caption",
            "alt_text", "clinical_relevance", "article_id")


class ImageRightsError(ValueError):
    """Invalid image, provenance, or rights declaration."""


def _https(url: str) -> str:
    parsed = urlparse(url) if isinstance(url, str) else None
    if not parsed or parsed.scheme != "https" or not parsed.hostname or parsed.username:
        raise ImageRightsError("source_url and rights_url must be absolute HTTPS URLs without credentials")
    return url


def _dimensions(data: bytes) -> tuple[str, int, int]:
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        w, h = struct.unpack(">II", data[16:24])
        mime = "image/png"
    elif data[:6] in (b"GIF87a", b"GIF89a") and len(data) >= 10:
        w, h = struct.unpack("<HH", data[6:10])
        mime = "image/gif"
    elif data.startswith(b"RIFF") and data[8:12] == b"WEBP" and len(data) >= 30:
        if data[12:16] == b"VP8X":
            w = 1 + int.from_bytes(data[24:27], "little")
            h = 1 + int.from_bytes(data[27:30], "little")
        elif data[12:16] == b"VP8L" and data[20] == 0x2f:
            bits = int.from_bytes(data[21:25], "little")
            w, h = (bits & 0x3fff) + 1, ((bits >> 14) & 0x3fff) + 1
        else:
            raise ImageRightsError("unsupported WebP variant")
        mime = "image/webp"
    elif data.startswith(b"\xff\xd8"):
        mime = "image/jpeg"
        w = h = 0
        i = 2
        while i + 4 < len(data):
            if data[i] != 0xff:
                i += 1
                continue
            while i < len(data) and data[i] == 0xff:
                i += 1
            if i >= len(data):
                break
            marker = data[i]
            i += 1
            if marker in (0xd8, 0xd9, 0x01) or 0xd0 <= marker <= 0xd7:
                continue
            if i + 2 > len(data):
                break
            length = int.from_bytes(data[i:i + 2], "big")
            if length < 2 or i + length > len(data):
                break
            if marker in (0xc0, 0xc1, 0xc2, 0xc3, 0xc5, 0xc6, 0xc7,
                          0xc9, 0xca, 0xcb, 0xcd, 0xce, 0xcf) and length >= 7:
                h = int.from_bytes(data[i + 3:i + 5], "big")
                w = int.from_bytes(data[i + 5:i + 7], "big")
                break
            i += length
        if not w or not h:
            raise ImageRightsError("JPEG lacks valid SOF dimensions")
    else:
        raise ImageRightsError("not a supported PNG, JPEG, GIF or WebP image")
    if not (1 <= w <= 30000 and 1 <= h <= 30000 and w * h <= 100_000_000):
        raise ImageRightsError("invalid or excessive image dimensions")
    return mime, w, h


def verify_image(data: bytes, declared_mime: str | None = None) -> dict:
    if not isinstance(data, bytes) or not data or len(data) > MAX_IMAGE_BYTES:
        raise ImageRightsError("image empty, not bytes, or exceeds 25 MiB")
    mime, w, h = _dimensions(data)
    if declared_mime and declared_mime.split(";", 1)[0].strip().lower() != mime:
        raise ImageRightsError("declared Content-Type disagrees with image signature")
    return {"mime_type": mime, "width": w, "height": h,
            "size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def verify_metadata(meta: dict) -> dict:
    if not isinstance(meta, dict):
        raise ImageRightsError("metadata must be an object")
    for key in REQUIRED:
        if not isinstance(meta.get(key), str) or not meta[key].strip():
            raise ImageRightsError(f"missing required file-level provenance: {key}")
    _https(meta["source_url"])
    _https(meta["rights_url"])
    if not re.fullmatch(r"CLIFF-\d{3}", meta["article_id"]):
        raise ImageRightsError("article_id must be CLIFF-NNN")
    if meta["license"].strip().lower() in (
        "unknown", "unverified", "all rights reserved", "none", "n/a", "public domain?", "copyright"
    ):
        raise ImageRightsError("license is unverified or non-redistributable")
    if meta.get("rights_verified") is not True:
        raise ImageRightsError("rights_verified must be true after file-level manual review")
    return dict(meta)


def acquire(meta: dict, output_dir: Path, opener=None) -> dict:
    """Fetch approved image, reject non-HTTPS redirects, save content-addressed asset.

    opener is injectable for tests. This does not certify rights or clinical accuracy.
    """
    meta = verify_metadata(meta)
    req = urllib.request.Request(
        meta["source_url"], headers={"User-Agent": "AETHERION-medical-image-provenance/1.0"}
    )
    fetch = opener or urllib.request.urlopen
    with fetch(req, timeout=20) as response:
        final_url = response.geturl()
        _https(final_url)
        data = response.read(MAX_IMAGE_BYTES + 1)
        content_type = response.headers.get("Content-Type")
    verified = verify_image(data, content_type)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = verified["sha256"] + EXTENSIONS[verified["mime_type"]]
    path = output_dir / filename
    if path.exists() and path.read_bytes() != data:
        raise ImageRightsError("content-addressed asset differs from existing file")
    path.write_bytes(data)
    record = {
        **meta, **verified, "final_url": final_url,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "asset_path": filename, "rights_review_status": "metadata_declared_manual_review_required"
    }
    (output_dir / (verified["sha256"] + ".json")).write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("metadata_json", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    try:
        result = acquire(json.loads(args.metadata_json.read_text(encoding="utf-8")), args.output_dir)
    except (ImageRightsError, OSError, ValueError) as exc:
        parser.exit(2, f"image acquisition rejected: {exc}\n")
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
