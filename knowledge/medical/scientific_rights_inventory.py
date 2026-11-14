"""Scientific rights inventory validator for encyclopedia articles (Q-0139)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ALLOWED_DIMENSIONS = {
    "abstract_rights": {
        "ALLOWED_WITH_ATTRIBUTION",
        "PROHIBITED",
        "UNVERIFIED_PENDING_LICENSE_CHECK",
    },
    "full_text_rights": {
        "ALLOWED_WITH_ATTRIBUTION",
        "LINK_OUT_ONLY",
        "PROHIBITED",
        "UNVERIFIED_PENDING_LICENSE_CHECK",
    },
    "figure_rights": {
        "ALLOWED_WITH_ATTRIBUTION",
        "RESTRICTED_BY_THIRD_PARTY_COPYRIGHT",
        "PROHIBITED",
        "UNVERIFIED_PENDING_LICENSE_CHECK",
    },
    "modification_rights": {
        "ALLOWED_WITH_ATTRIBUTION",
        "NO_DERIVATIVES",
        "PROHIBITED",
        "UNVERIFIED_PENDING_LICENSE_CHECK",
    },
}

VALID_IMPORT_STATES = {
    "READY",
    "NO_DATA",
    "NOT_IMPORTED",
    "LINKED_REFERENCE_ONLY",
    "VERIFIED_METADATA_ONLY",
    "POLICY_TEMPLATE",
    "UNVERIFIED",
}


def validate_article_rights_record(record: dict[str, Any]) -> None:
    """Validate provenance and 4-dimension reuse rights for an encyclopedia source."""
    required_str_fields = (
        "source_id",
        "title",
        "publisher",
        "source_url",
        "license_or_terms",
        "import_status",
    )
    for field in required_str_fields:
        val = record.get(field)
        if not isinstance(val, str) or not val.strip():
            raise ValueError(f"Missing or empty required string field: {field}")

    if not record["source_url"].startswith("https://"):
        raise ValueError(f"source_url must use https://: {record['source_url']!r}")

    if record["import_status"] not in VALID_IMPORT_STATES:
        raise ValueError(f"Invalid import_status: {record['import_status']!r}")

    if record.get("relicensed_under_apache_2_0") is not False:
        raise ValueError("Third-party/NASA scientific works must never be relicensed under Apache-2.0")

    for dim, valid_values in ALLOWED_DIMENSIONS.items():
        val = record.get(dim)
        if val not in valid_values:
            raise ValueError(f"Invalid {dim}: {val!r}")

    # Honest gating: unimported/no-data sources cannot claim full-text or figure display rights.
    if record["import_status"] in {"NO_DATA", "NOT_IMPORTED", "UNVERIFIED"}:
        if record.get("full_text_display_allowed") is not False:
            raise ValueError("Unimported source cannot allow local full-text display")
        if record.get("figure_display_allowed") is not False:
            raise ValueError("Unimported source cannot allow local figure display")


def can_display_in_encyclopedia(record: dict[str, Any], *, surface: str) -> bool:
    """Return True only if the requested surface ('abstract', 'full_text', 'figure') is permitted."""
    validate_article_rights_record(record)
    if surface == "abstract":
        return record["abstract_rights"] == "ALLOWED_WITH_ATTRIBUTION"
    if surface == "full_text":
        return (
            bool(record.get("full_text_display_allowed"))
            and record["full_text_rights"] == "ALLOWED_WITH_ATTRIBUTION"
            and record["import_status"] == "READY"
        )
    if surface == "figure":
        return (
            bool(record.get("figure_display_allowed"))
            and record["figure_rights"] == "ALLOWED_WITH_ATTRIBUTION"
            and record["import_status"] == "READY"
        )
    raise ValueError(f"Unknown encyclopedia surface: {surface!r}")


def load_rights_inventory(path: Path | None = None) -> dict[str, Any]:
    """Load and validate the scientific rights inventory JSON."""
    target = path or Path(__file__).with_name("scientific_rights_inventory.json")
    data = json.loads(target.read_text(encoding="utf-8"))
    sources = data.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("Inventory must contain a non-empty 'sources' list")
    for item in sources:
        validate_article_rights_record(item)
    return data
