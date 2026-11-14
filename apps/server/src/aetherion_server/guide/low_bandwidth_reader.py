"""Keyboard-accessible, low-bandwidth Guide article reader (Q-0160)."""

from __future__ import annotations

import json
from typing import Any

DEFAULT_KEYBOARD_SHORTCUTS = {
    "next_section": "j",
    "prev_section": "k",
    "focus_search": "/",
    "open_source_citation": "Enter",
    "back_to_list": "Escape",
}


def build_low_bandwidth_article_payload(
    entry: dict[str, Any],
    *,
    max_bytes: int = 2048,
    include_images: bool = False,
) -> dict[str, Any]:
    """Build a compact, keyboard-navigable Guide payload for constrained connectivity."""
    if max_bytes < 512:
        raise ValueError("max_bytes must be at least 512 bytes to preserve provenance")

    summary = str(entry.get("summary", "")).strip()
    media = entry.get("media", []) if isinstance(entry.get("media"), list) else []
    media_stubs = [
        {"alt_text": str(m.get("alt_text", "Figure")), "omitted_for_bandwidth": True}
        for m in media
    ] if not include_images else media

    payload: dict[str, Any] = {
        "entry_id": entry.get("entry_id", ""),
        "title": str(entry.get("title", "")).strip(),
        "summary": summary,
        "publisher": entry.get("publisher", "NASA"),
        "source_url": entry.get("source_url", ""),
        "verification_status": entry.get("verification_status", "UNVERIFIED"),
        "is_live_telemetry": bool(entry.get("is_live_telemetry", False)),
        "low_bandwidth_mode": True,
        "images_omitted": not include_images and len(media) > 0,
        "media": media_stubs,
        "keyboard_navigation": {
            "tab_order": ["title", "summary", "media_alt_list", "source_citation", "back_to_list"],
            "shortcuts": dict(DEFAULT_KEYBOARD_SHORTCUTS),
        },
        "truncated": False,
    }

    encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    if len(encoded) > max_bytes:
        # Trim summary cleanly while preserving provenance and keyboard metadata
        overhead = len(encoded) - len(summary.encode("utf-8"))
        allowed_summary_bytes = max(32, max_bytes - overhead - 8)
        trimmed = summary.encode("utf-8")[:allowed_summary_bytes].decode("utf-8", errors="ignore").rstrip()
        payload["summary"] = f"{trimmed}..."
        payload["truncated"] = True

    final_bytes = len(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
    payload["payload_bytes"] = final_bytes
    return payload
