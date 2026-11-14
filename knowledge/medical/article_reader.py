"""Source-aware encyclopedia article reader (Q-0142)."""

from __future__ import annotations

from typing import Any

from knowledge.medical.scientific_rights_inventory import can_display_in_encyclopedia

VALID_VERIFICATION_STATES = {"READY", "NO_DATA", "UNVERIFIED", "STALE", "OFFLINE", "DENIED", "ERROR"}


def render_article_view(article: dict[str, Any], rights_record: dict[str, Any]) -> dict[str, Any]:
    """Build a source-aware article reader payload showing author, DOI, URL, date, and verification status."""
    author = article.get("author")
    if not isinstance(author, str) or not author.strip():
        raise ValueError("Article must declare a non-empty 'author'")

    source_url = article.get("source_url")
    if not isinstance(source_url, str) or not source_url.startswith("https://"):
        raise ValueError("Article must declare an https:// 'source_url'")

    date_str = article.get("date")
    if not isinstance(date_str, str) or not date_str.strip():
        raise ValueError("Article must declare a non-empty 'date'")

    verification_status = article.get("verification_status")
    if verification_status not in VALID_VERIFICATION_STATES:
        raise ValueError(f"Invalid verification_status: {verification_status!r}")

    doi = article.get("doi")
    abstract_allowed = can_display_in_encyclopedia(rights_record, surface="abstract")
    full_text_allowed = can_display_in_encyclopedia(rights_record, surface="full_text") and verification_status == "READY"
    figure_allowed = can_display_in_encyclopedia(rights_record, surface="figure") and verification_status == "READY"

    return {
        "article_id": article.get("article_id", ""),
        "title": article.get("title", ""),
        "author": author.strip(),
        "doi": doi if isinstance(doi, str) and doi.strip() else None,
        "source_url": source_url.strip(),
        "date": date_str.strip(),
        "verification_status": verification_status,
        "is_live_telemetry": False,
        "license_or_terms": rights_record["license_or_terms"],
        "abstract": article.get("abstract") if abstract_allowed else None,
        "full_text": article.get("full_text") if full_text_allowed else None,
        "figures_allowed": figure_allowed,
        "restriction_notice": (
            None
            if full_text_allowed
            else "Full text/figures withheld pending verified import and rights clearance; see source_url."
        ),
    }
