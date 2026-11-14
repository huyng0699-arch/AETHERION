"""Deterministic, provenance-bound condition identifier utilities (Q-0138)."""

from __future__ import annotations

import hashlib
import re
from typing import Any

CONDITION_ID_RE = re.compile(r"^COND-[0-9a-f]{12}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def make_condition_id(
    *,
    source_publisher: str,
    source_url: str,
    canonical_title: str,
    source_sha256: str,
) -> str:
    """Return a deterministic stable condition ID bound to verified source provenance."""
    if not source_publisher.strip():
        raise ValueError("source_publisher is required")
    if not source_url.startswith("https://"):
        raise ValueError("source_url must use https://")
    if not canonical_title.strip():
        raise ValueError("canonical_title is required")
    if not SHA256_RE.fullmatch(source_sha256.lower()):
        raise ValueError("source_sha256 must be a 64-character lowercase hex digest")

    payload = "|".join([
        source_publisher.strip().upper(),
        source_url.strip(),
        " ".join(canonical_title.split()).lower(),
        source_sha256.lower(),
    ])
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]
    return f"COND-{digest}"


def validate_condition_record(record: dict[str, Any]) -> None:
    """Validate that a condition record carries stable ID and verified provenance."""
    cid = record.get("condition_id", "")
    if not CONDITION_ID_RE.fullmatch(cid):
        raise ValueError(f"Invalid condition_id: {cid!r}")

    state = record.get("verification_state")
    if state not in {"READY", "NO_DATA", "UNVERIFIED", "STALE", "OFFLINE", "DENIED", "ERROR"}:
        raise ValueError(f"Invalid verification_state: {state!r}")

    if state == "READY":
        expected = make_condition_id(
            source_publisher=str(record.get("source_publisher", "")),
            source_url=str(record.get("source_url", "")),
            canonical_title=str(record.get("canonical_title", "")),
            source_sha256=str(record.get("source_sha256", "")),
        )
        if cid != expected:
            raise ValueError(f"condition_id {cid} does not match provenance digest {expected}")
