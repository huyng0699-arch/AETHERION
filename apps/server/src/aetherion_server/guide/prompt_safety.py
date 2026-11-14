"""Sanitize untrusted external page content so it cannot override safety rules (Q-0164)."""

from __future__ import annotations

import re
from typing import Any

INJECTION_PATTERNS = (
    re.compile(r"ignore\s+(all\s+)?(previous|prior|safety)\s+instructions", re.IGNORECASE),
    re.compile(r"override\s+(medical|safety|alert)\s+(policy|rules|instructions)", re.IGNORECASE),
    re.compile(r"system\s*:\s*", re.IGNORECASE),
    re.compile(r"<\s*/?\s*system\s*>", re.IGNORECASE),
    re.compile(r"disable\s+assistance", re.IGNORECASE),
)


def sanitize_untrusted_source_text(raw_text: str) -> dict[str, Any]:
    """Strip/quarantine prompt-injection directives from untrusted external text."""
    detected: list[str] = []
    sanitized = raw_text
    for pattern in INJECTION_PATTERNS:
        if pattern.search(sanitized):
            detected.append(pattern.pattern)
            sanitized = pattern.sub("[QUARANTINED_DIRECTIVE]", sanitized)

    return {
        "injection_detected": len(detected) > 0,
        "matched_patterns": detected,
        "safety_policy_overridden": False,
        "trust_level": "UNTRUSTED_EXTERNAL_DATA",
        "sanitized_text": sanitized,
    }
