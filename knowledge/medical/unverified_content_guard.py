"""Unverified and author-generated content flag guard for encyclopedia entries (Q-0143)."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _is_nasa_https_url(url: str) -> bool:
    if not isinstance(url, str) or not url.startswith("https://"):
        return False
    host = (urlparse(url).hostname or "").lower()
    return host == "nasa.gov" or host.endswith(".nasa.gov")


def classify_content_provenance(entry: dict[str, Any]) -> dict[str, Any]:
    """Classify provenance and expose mandatory unverified / author-generated flags."""
    origin_type = str(entry.get("origin_type", "UNKNOWN")).upper()
    verification_state = str(entry.get("verification_state", "UNVERIFIED")).upper()
    source_url = str(entry.get("source_url", ""))
    source_sha256 = str(entry.get("source_sha256", "")).lower()

    is_author_generated = origin_type in {"AUTHOR_GENERATED", "AI_ASSISTED", "COMMUNITY_NOTE"}
    if is_author_generated and entry.get("label_as_nasa") is True:
        raise ValueError("Author-generated or AI-assisted text must never be labeled as an official NASA article")

    is_official_nasa = (
        origin_type == "NASA_ORIGINAL"
        and verification_state == "READY"
        and _is_nasa_https_url(source_url)
        and bool(SHA256_RE.fullmatch(source_sha256))
    )

    if entry.get("label_as_nasa") is True and not is_official_nasa:
        raise ValueError("Cannot label unverified or non-NASA-verified entry as an official NASA article")

    is_unverified = verification_state != "READY" or not is_official_nasa

    if is_author_generated:
        badge = "AUTHOR_GENERATED_NOT_OFFICIAL_NASA"
        warning = "Author-generated content — NOT an official NASA article."
    elif not is_official_nasa and verification_state != "READY":
        badge = f"UNVERIFIED_{verification_state}"
        warning = f"Unverified content ({verification_state}) — not verified against an official NASA source."
    elif is_official_nasa:
        badge = "VERIFIED_NASA_SOURCE"
        warning = None
    else:
        badge = "NON_NASA_VERIFIED_REFERENCE"
        warning = "External verified reference — not an official NASA publication."

    return {
        "entry_id": entry.get("entry_id", ""),
        "origin_type": origin_type,
        "verification_state": verification_state,
        "is_official_nasa_article": is_official_nasa,
        "is_author_generated": is_author_generated,
        "is_unverified": is_unverified,
        "badge": badge,
        "warning_banner": warning,
    }
