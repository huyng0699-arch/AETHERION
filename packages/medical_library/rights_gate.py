"""NASA and third-party copyright attribution and distribution gate (Q-0431)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re
from typing import Any
from urllib.parse import urlparse


class DistributionRightsError(ValueError):
    """Raised when an asset or article cannot be legally redistributed or lacks required attribution."""


NASA_ALLOWED_HOSTS = (
    "nasa.gov",
    "www.nasa.gov",
    "ntrs.nasa.gov",
    "osdr.nasa.gov",
    "humanresearchroadmap.nasa.gov",
    "images.nasa.gov",
)

PERMISSIVE_THIRD_PARTY_LICENSES = frozenset(
    {
        "CC0-1.0",
        "PUBLIC_DOMAIN",
        "US_GOV_PUBLIC_DOMAIN",
        "CC-BY-4.0",
        "CC-BY-3.0",
        "CC-BY-SA-4.0",
        "CC-BY-SA-3.0",
        "MIT",
        "BSD-3-Clause",
    }
)

BLOCKED_LICENSES = frozenset(
    {
        "ALL_RIGHTS_RESERVED",
        "UNKNOWN",
        "UNVERIFIED",
        "FAIR_USE_ONLY",
        "NO_REDISTRIBUTION",
        "COPYRIGHTED_PERMISSION_REQUIRED",
    }
)


@dataclass(frozen=True)
class RightsAuditResult:
    entity_id: str
    entity_type: str
    origin_kind: str
    license_name: str
    source_url: str
    credit_line: str
    redistribution_allowed: bool
    conditions: tuple[str, ...]


def _is_valid_sha256(value: str | None) -> bool:
    return bool(value and re.match(r"^[a-f0-9]{64}$", value))


def _is_nasa_host(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    return any(host == allowed or host.endswith(f".{allowed}") for allowed in NASA_ALLOWED_HOSTS)


def validate_nasa_original_rights(record: dict[str, Any]) -> RightsAuditResult:
    """Validate an authentic NASA original document/media item."""
    entity_id = str(record.get("entity_id", "")).strip()
    entity_type = str(record.get("entity_type", "article")).strip()
    source_url = str(record.get("source_url", "")).strip()
    publisher = str(record.get("publisher", "")).strip()
    sha256 = record.get("sha256")
    retrieved_at = str(record.get("retrieved_at_utc", "")).strip()

    if not entity_id:
        raise DistributionRightsError("entity_id is required")
    if not source_url.startswith("https://") or not _is_nasa_host(source_url):
        raise DistributionRightsError(
            f"Non-NASA URL cannot be classified as NASA original: {source_url!r}"
        )
    if "nasa" not in publisher.lower():
        raise DistributionRightsError(f"NASA original must attribute NASA publisher, got {publisher!r}")
    if not _is_valid_sha256(sha256):
        raise DistributionRightsError("NASA original requires verified 64-char lowercase sha256")
    dt = datetime.fromisoformat(retrieved_at)
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise DistributionRightsError("retrieved_at_utc must be timezone-aware")

    license_name = str(record.get("license_name", "US_GOV_PUBLIC_DOMAIN")).strip() or "US_GOV_PUBLIC_DOMAIN"
    if license_name in BLOCKED_LICENSES:
        raise DistributionRightsError(f"Blocked license on NASA item {entity_id}: {license_name}")

    credit_line = str(record.get("credit_line", "")).strip() or f"NASA ({source_url})"
    return RightsAuditResult(
        entity_id=entity_id,
        entity_type=entity_type,
        origin_kind="NASA_ORIGINAL",
        license_name=license_name,
        source_url=source_url,
        credit_line=credit_line,
        redistribution_allowed=True,
        conditions=("no_nasa_endorsement_claim", "risk_planning_evidence_only"),
    )


def validate_third_party_rights(record: dict[str, Any]) -> RightsAuditResult:
    """Validate a non-NASA scientific image or article separately and enforce license conditions."""
    entity_id = str(record.get("entity_id", "")).strip()
    entity_type = str(record.get("entity_type", "media")).strip()
    source_url = str(record.get("source_url", "")).strip()
    creator = str(record.get("creator", "")).strip()
    publisher = str(record.get("publisher", "")).strip()
    license_name = str(record.get("license_name", "")).strip()
    credit_line = str(record.get("credit_line", "")).strip()
    sha256 = record.get("sha256")

    if not entity_id:
        raise DistributionRightsError("entity_id is required")
    if not (source_url.startswith("https://") or source_url.startswith("http://")):
        raise DistributionRightsError(f"Third-party item {entity_id} requires valid source_url")
    if not creator or not publisher:
        raise DistributionRightsError(f"Third-party item {entity_id} requires creator and publisher")
    if entity_type == "media" and not _is_valid_sha256(sha256):
        raise DistributionRightsError(f"Third-party media {entity_id} requires verified sha256")

    if license_name in BLOCKED_LICENSES or license_name not in PERMISSIVE_THIRD_PARTY_LICENSES:
        raise DistributionRightsError(
            f"Redistribution blocked for {entity_id}: unverified or non-redistributable license {license_name!r}"
        )

    conditions: list[str] = []
    if license_name.startswith("CC-BY"):
        if not credit_line:
            raise DistributionRightsError(
                f"CC-BY license for {entity_id} requires non-empty credit_line attribution"
            )
        conditions.append("attribution_required")
    if "SA" in license_name:
        if not str(record.get("share_alike_notice", "")).strip():
            raise DistributionRightsError(
                f"ShareAlike license {license_name} for {entity_id} requires share_alike_notice"
            )
        conditions.append("share_alike_required")

    return RightsAuditResult(
        entity_id=entity_id,
        entity_type=entity_type,
        origin_kind="THIRD_PARTY_VERIFIED",
        license_name=license_name,
        source_url=source_url,
        credit_line=credit_line or f"{creator} / {publisher}",
        redistribution_allowed=True,
        conditions=tuple(conditions),
    )


def build_embedded_notice_bundle(results: list[RightsAuditResult]) -> dict[str, Any]:
    """Build an auditable attribution bundle for offline SQLite embedding and UI display."""
    if not results:
        raise DistributionRightsError("Cannot build notice bundle from empty results")
    blocked = [r.entity_id for r in results if not r.redistribution_allowed]
    if blocked:
        raise DistributionRightsError(f"Blocked items present in bundle: {blocked}")

    return {
        "disclaimer": (
            "NASA CliFF materials are risk-planning evidence, not validated bedside treatment protocols. "
            "NASA does not endorse AETHERION."
        ),
        "total_items": len(results),
        "nasa_originals": sum(1 for r in results if r.origin_kind == "NASA_ORIGINAL"),
        "third_party_items": sum(1 for r in results if r.origin_kind == "THIRD_PARTY_VERIFIED"),
        "notices": [
            {
                "entity_id": r.entity_id,
                "entity_type": r.entity_type,
                "origin_kind": r.origin_kind,
                "license_name": r.license_name,
                "source_url": r.source_url,
                "credit_line": r.credit_line,
                "conditions": list(r.conditions),
            }
            for r in results
        ],
    }
