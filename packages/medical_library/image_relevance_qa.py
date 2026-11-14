"""Fail-closed medical image relevance and deduplication QA (Q-0432).

This module cannot infer clinical correctness. A distinct qualified human reviewer
must explicitly approve the condition, anatomy, modality and caption for each image.
Perceptual matching is advisory; exact SHA-256 duplicates are blocked.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
from typing import Any, Iterable


@dataclass(frozen=True)
class ImageQAResult:
    asset_id: str
    sha256: str
    accepted: bool
    findings: tuple[str, ...]
    perceptual_hash: str | None = None


def _dhash(data: bytes) -> str | None:
    """Return a 64-bit difference hash, or None when Pillow cannot decode it."""
    try:
        from PIL import Image, UnidentifiedImageError
    except ImportError:
        return None
    try:
        with Image.open(BytesIO(data)) as image:
            image.verify()
        with Image.open(BytesIO(data)) as image:
            image = image.convert("L").resize((9, 8))
            pixels = list(image.getdata())
        bits = 0
        for row in range(8):
            for col in range(8):
                bits = (bits << 1) | int(pixels[row * 9 + col] > pixels[row * 9 + col + 1])
        return f"{bits:016x}"
    except (OSError, ValueError, UnidentifiedImageError):
        return None


def audit_images(
    assets: Iterable[dict[str, Any]],
    *,
    near_duplicate_hamming_distance: int = 5,
) -> list[ImageQAResult]:
    """Audit real image bytes and documented independent clinical review.

    Required fields: asset_id, image_bytes, condition_id, caption, alt_text,
    reviewer_id, reviewed_condition_id, reviewed_sha256, review_decision.
    A reviewer attestation is *metadata*, not proof of reviewer independence;
    the acceptance reviewer must independently verify it.
    """
    if not 0 <= near_duplicate_hamming_distance <= 64:
        raise ValueError("near_duplicate_hamming_distance must be between 0 and 64")
    results: list[ImageQAResult] = []
    seen_exact: dict[str, str] = {}
    seen_perceptual: list[tuple[str, int]] = []
    for record in assets:
        asset_id = str(record.get("asset_id") or "").strip()
        data = record.get("image_bytes")
        findings: list[str] = []
        if not isinstance(data, bytes) or not data:
            findings.append("MISSING_IMAGE_BYTES")
            data = b""
        digest = sha256(data).hexdigest() if data else ""
        declared_hash = str(record.get("sha256") or "").strip().lower()
        if declared_hash != digest or not digest:
            findings.append("SHA256_MISMATCH")
        if not asset_id:
            findings.append("MISSING_ASSET_ID")
        condition = str(record.get("condition_id") or "").strip()
        if not condition:
            findings.append("MISSING_CONDITION_ID")
        if not str(record.get("caption") or "").strip():
            findings.append("MISSING_CLINICAL_CAPTION")
        if not str(record.get("alt_text") or "").strip():
            findings.append("MISSING_ALT_TEXT")
        reviewer = str(record.get("reviewer_id") or "").strip()
        if (
            not reviewer
            or record.get("review_decision") != "APPROVED"
            or str(record.get("reviewed_condition_id") or "") != condition
            or str(record.get("reviewed_sha256") or "").lower() != digest
        ):
            findings.append("CLINICAL_RELEVANCE_REVIEW_REQUIRED")
        if digest and digest in seen_exact:
            findings.append(f"EXACT_DUPLICATE_OF:{seen_exact[digest]}")
        elif digest:
            seen_exact[digest] = asset_id or "<unnamed>"
        phash = _dhash(data) if data else None
        if phash is None:
            findings.append("IMAGE_DECODE_UNVERIFIED")
        else:
            value = int(phash, 16)
            for previous_id, previous_value in seen_perceptual:
                if (value ^ previous_value).bit_count() <= near_duplicate_hamming_distance:
                    findings.append(f"POSSIBLE_VISUAL_DUPLICATE_OF:{previous_id}")
                    break
            seen_perceptual.append((asset_id or "<unnamed>", value))
        results.append(ImageQAResult(asset_id, digest, not findings, tuple(findings), phash))
    return results
