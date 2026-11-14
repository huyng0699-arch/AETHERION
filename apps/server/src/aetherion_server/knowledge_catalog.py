"""Read-only reference indexing for the actual NASA CliFF JSON and owner-authorized symptom vocabulary.

Reference indexing is NOT validation of clinical evidence or NASA original PDF completeness.
This is an on-demand metadata and text search; no fabricated record or diagnosis.
"""
from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
import re
import unicodedata

REPOSITORY = Path(__file__).resolve().parents[4]
RECORDS = REPOSITORY / "knowledge" / "nasa" / "cliff_119_2023" / "records"
SYMPTOMS = REPOSITORY / "knowledge" / "symptoms" / "ASTRA_819_REFERENCE.json"
ARTICLE_RE = re.compile(r"^CLIFF-\d{3}$")
MAX_RESULTS = 100


def normalized(text: str) -> str:
    plain = unicodedata.normalize("NFD", str(text).casefold())
    plain = "".join(c for c in plain if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", plain.replace("đ", "d")).strip()


@lru_cache(maxsize=1)
def symptom_source() -> dict:
    if not SYMPTOMS.is_file():
        return {"entries": [], "total_labels": 0, "clinical_validation_completed": False}
    data = json.loads(SYMPTOMS.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("entries"), list):
        raise ValueError("Unsupported ASTRA symptom data")
    if len(data["entries"]) != 819 or data.get("total_labels") != 819:
        raise ValueError("Original symptom catalog count is not 819; import integrity review required")
    return data


def symptoms(query: str = "", limit: int = 30, route: str = "") -> dict:
    source = symptom_source()
    term = normalized(query[:200])
    route = route.strip().lower()
    hits = []
    for item in source["entries"]:
        if not isinstance(item, dict):
            continue
        if route and route not in item.get("routes", []):
            continue
        key = normalized(" ".join([item.get("name", ""), *item.get("aliases", [])]))
        if term and term not in key:
            continue
        hits.append({
            "name": item.get("name"), "ids": item.get("ids", []),
            "aliases": item.get("aliases", []), "routes": item.get("routes", []),
            "legacy_tier_unreviewed": item.get("tier"),
            "review_state": item.get("review_status", "unknown"),
        })
    return {
        "total_source_labels": len(source["entries"]),
        "matched": len(hits), "items": hits[:max(1, min(limit, MAX_RESULTS))],
        "clinical_validation": False,
        "notice": "ASTRA author-owned vocabulary; original tiers are NOT clinically reviewed risk classifications.",
    }


def _load_record(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return None
    return data if isinstance(data, dict) and data.get("article_id") == path.stem else None


@lru_cache(maxsize=1)
def records() -> tuple[dict, ...]:
    if not RECORDS.is_dir():
        return ()
    documents = []
    for path in sorted(RECORDS.glob("CLIFF-???.json")):
        data = _load_record(path)
        if data is not None:
            documents.append(data)
    return tuple(documents)


def record_by_id(article_id: str) -> dict | None:
    if ARTICLE_RE.fullmatch(article_id) is None:
        return None
    return next((x for x in records() if x["article_id"] == article_id), None)


def _summary(record: dict) -> dict:
    sections = record.get("sections", [])
    texts = [str(s.get("text_content", "")) for s in sections if isinstance(s, dict)]
    source = record.get("source") or {}
    return {
        "article_id": record["article_id"],
        "title": record.get("display_title", ""),
        "category": record.get("category", ""),
        "slot": record.get("slot"),
        "sections": len(sections),
        "text_words": sum(len(t.split()) for t in texts),
        "tables": len(record.get("tables") or []),
        "references": len(record.get("references") or []),
        "media": len(record.get("media") or []),
        "original_url": source.get("final_url") or source.get("source_url"),
        "source_claim": source.get("verification_state", "UNKNOWN"),
        "original_sha256_claim": source.get("content_sha256"),
        "content_state": "STRUCTURED_JSON_LOCAL_NOT_PDF_INTEGRITY_PROOF",
    }


@lru_cache(maxsize=1)
def searchable_index() -> tuple[tuple[str, dict], ...]:
    indexed = []
    for item in records():
        sections = item.get("sections") or []
        whole = " ".join([
            str(item.get("display_title", "")), str(item.get("category", "")),
            *(str(s.get("heading", "")) + " " + str(s.get("text_content", ""))
              for s in sections if isinstance(s, dict)),
        ])
        indexed.append((normalized(whole), item))
    return tuple(indexed)


def articles(query: str = "", limit: int = 30, category: str = "") -> dict:
    query = normalized(query[:200])
    category = normalized(category[:100])
    hits = []
    for fulltext, item in searchable_index():
        if category and category not in normalized(item.get("category", "")):
            continue
        if query and query not in fulltext:
            continue
        hits.append(_summary(item))
    return {
        "indexed": len(records()), "matched": len(hits),
        "items": hits[:max(1, min(limit, MAX_RESULTS))],
        "source": "Local JSON records produced from NASA IMM CliFF source PDFs",
        "note": "A source verification flag in JSON is a claim, not independent verification of original PDF bytes.",
    }


def article(article_id: str) -> dict | None:
    data = record_by_id(article_id)
    if data is None:
        return None
    return {
        "summary": _summary(data),
        "sections": data.get("sections") or [],
        "tables": data.get("tables") or [],
        "references": data.get("references") or [],
        "media": data.get("media") or [],
        "limitations": data.get("limitations") or [],
        "source": data.get("source") or {},
        "read_only": True, "clinical_decision_support": False,
    }


def status() -> dict:
    source = symptom_source()
    docs = records()
    expected = {f"CLIFF-{n:03}" for n in range(1, 120)}
    actual = {x["article_id"] for x in docs}
    return {
        "json_articles": len(docs), "expected_slots": 119,
        "missing_slots": sorted(expected - actual),
        "symptom_labels": len(source["entries"]),
        "article_full_text_search": True,
        "original_pdf_archive_verified": False,
        "clinical_rules_validated": False,
        "read_only": True,
    }
