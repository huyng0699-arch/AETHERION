"""Conservative origin labels for source-backed Personal Today observations.

Never infer a physical sensor from metric name or unverified source strings.
"""
from __future__ import annotations


def record_origin(card: object) -> tuple[str, str]:
    """Return filter key and honest origin label."""
    verification = str(getattr(card, "verification_state", "")).upper()
    source = str(getattr(card, "source_id", "")).casefold()
    if verification == "SELF_REPORTED":
        return "self", "Self-reported"
    if verification == "VERIFIED" and source != "personal_self_checkin":
        return "verified", "Verified provenance (source shown)"
    return "unverified", "Origin unverified"
