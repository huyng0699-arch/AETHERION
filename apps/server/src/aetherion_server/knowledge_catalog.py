"""Read-only reference indexing for the actual NASA CliFF JSON and owner-authorized symptom vocabulary.

Reference indexing is NOT validation of clinical evidence or NASA original PDF completeness.
This is an on-demand metadata and text search; no fabricated record or diagnosis.
"""
from __future__ import annotations

from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import unicodedata

REPOSITORY = Path(__file__).resolve().parents[4]
RECORDS = REPOSITORY / "knowledge" / "nasa" / "cliff_119_2023" / "records"
CONDITIONS = REPOSITORY / "knowledge" / "nasa" / "impact_conditions_2023.json"
SYMPTOMS = REPOSITORY / "knowledge" / "symptoms" / "ASTRA_819_REFERENCE.json"
SYMPTOM_EN_ALIASES = REPOSITORY / "knowledge" / "symptoms" / "label_aliases_en.json"
ARTICLE_RE = re.compile(r"^CLIFF-\d{3}$")
MAX_RESULTS = 200


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


@lru_cache(maxsize=1)
def symptom_english_aliases() -> dict[str, dict]:
    """Additive, UNREVIEWED English display/search terms keyed by Vietnamese name.

    Never rewrite the source 819-entry catalog, infer risk levels, diagnose,
    or pretend that translation drafts were reviewed by a clinician.
    A stale/malformed overlay is ignored rather than silently mis-mapped.
    """
    if not SYMPTOM_EN_ALIASES.is_file() or not SYMPTOMS.is_file():
        return {}
    try:
        source_bytes = SYMPTOMS.read_bytes()
        # Windows Git may check text files out as CRLF. Compare the raw blob
        # and its Git-normalized LF variant; never modify either local file.
        def git_blob_sha(content: bytes) -> str:
            blob = b"blob " + str(len(content)).encode("ascii") + bytes((0,)) + content
            return hashlib.sha1(blob).hexdigest()

        valid_source_hashes = {
            git_blob_sha(source_bytes),
            git_blob_sha(source_bytes.replace(bytes((13, 10)), bytes((10,)))),
        }
        raw = json.loads(SYMPTOM_EN_ALIASES.read_text(encoding="utf-8"))
        if (not isinstance(raw, dict) or raw.get("schema_version") != "1.0.0"
                or raw.get("source_blob_sha") not in valid_source_hashes
                or raw.get("source_language") != "vi"
                or raw.get("target_language") != "en"
                or raw.get("translation_status") != "UNREVIEWED_TERMINOLOGY"
                or not isinstance(raw.get("labels"), list)):
            return {}
        source_names = {
            item["name"]: item for item in symptom_source()["entries"]
            if isinstance(item, dict) and isinstance(item.get("name"), str)
        }
        labels: dict[str, dict] = {}
        for item in raw["labels"]:
            if not isinstance(item, dict):
                continue
            vi = item.get("source_label_vi")
            ident = item.get("symptom_id")
            en = item.get("label_en")
            aliases = item.get("aliases_en")
            if (not isinstance(vi, str) or not isinstance(ident, str)
                    or not isinstance(en, str) or not en.strip()
                    or len(en) > 140 or not isinstance(aliases, list)
                    or len(aliases) > 12 or not all(
                        isinstance(v, str) and v.strip() and len(v) <= 140 for v in aliases
                    ) or vi not in source_names
                    or ident not in source_names[vi].get("ids", [])
                    or vi in labels):
                continue
            labels[vi] = {"label_en": en.strip(), "aliases_en": tuple(aliases),
                          "review_status": "UNREVIEWED_TERMINOLOGY"}
        return labels
    except (OSError, UnicodeError, ValueError, TypeError):
        return {}


def symptoms(query: str = "", limit: int = 30, route: str = "") -> dict:
    source = symptom_source()
    english = symptom_english_aliases()
    term = normalized(query[:200])
    route = route.strip().lower()
    hits = []
    for item in source["entries"]:
        if not isinstance(item, dict):
            continue
        if route and route not in item.get("routes", []):
            continue
        localized = english.get(item.get("name", ""), {})
        key = normalized(" ".join([
            item.get("name", ""), *item.get("aliases", []),
            localized.get("label_en", ""), *localized.get("aliases_en", ()),
        ]))
        if term and term not in key:
            continue
        hits.append({
            "name": item.get("name"), "ids": item.get("ids", []),
            "aliases": item.get("aliases", []), "routes": item.get("routes", []),
            "legacy_tier_unreviewed": item.get("tier"),
            "review_state": item.get("review_status", "unknown"),
            "name_en": localized.get("label_en"),
            "english_aliases": list(localized.get("aliases_en", ())),
            "translation_review_state": localized.get(
                "review_status", "NO_TRANSLATION"),
        })
    return {
        "total_source_labels": len(source["entries"]),
        "matched": len(hits), "items": hits[:max(1, min(limit, MAX_RESULTS))],
        "clinical_validation": False,
        "english_translation_coverage": len(english),
        "english_translation_review_state": "UNREVIEWED_TERMINOLOGY",
        "notice": "ASTRA author-owned vocabulary; original tiers and English translation drafts are NOT clinically reviewed.",
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
        "content_state": record.get(
            "completeness_state", "STRUCTURED_JSON_LOCAL_NOT_PDF_INTEGRITY_PROOF"
        ),
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
        "source": "Read-only local catalogue of NASA IMM CliFF records and NASA index metadata",
        "note": (
            "A source verification flag in JSON is a claim, not independent verification of original PDF bytes. "
            "Metadata-only entries contain no extracted NASA document text."
        ),
    }


@lru_cache(maxsize=1)
def condition_index() -> dict:
    """NASA IMPACT condition names and their Appendix C PDF page references."""
    if not CONDITIONS.is_file():
        return {"source_title": "", "source_url": "", "records": []}
    try:
        data = json.loads(CONDITIONS.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return {"source_title": "", "source_url": "", "records": []}
    return data if isinstance(data, dict) and isinstance(data.get("records"), list) else {
        "source_title": "", "source_url": "", "records": []
    }


def conditions(query: str = "") -> dict:
    data = condition_index()
    source_url = str(data.get("source_url") or "")
    term = normalized(query[:200])
    all_rows = data["records"]
    items = []
    for row in all_rows:
        if not isinstance(row, dict):
            continue
        condition_id = str(row.get("condition_id") or "")
        title = str(row.get("title") or "")
        if term and term not in normalized(condition_id + " " + title):
            continue
        page = row.get("source_page")
        article_id = row.get("article_id")
        if article_id and record_by_id(str(article_id)) is None:
            article_id = None
        items.append({
            "condition_id": condition_id,
            "title": title,
            "source_page": page,
            "source_url": f"{source_url}#page={page}" if source_url and isinstance(page, int) else source_url,
            "article_id": article_id,
        })
    return {
        "total": len(all_rows), "matched": len(items), "items": items,
        "source_title": str(data.get("source_title") or ""), "source_url": source_url,
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
        "completeness_state": data.get("completeness_state", "STRUCTURED_JSON_LOCAL_NOT_PDF_INTEGRITY_PROOF"),
        "source_notes": data.get("source_notes", ""),
        "source": data.get("source") or {},
        "read_only": True, "clinical_decision_support": False,
    }


def status() -> dict:
    source = symptom_source()
    docs = records()
    expected = {f"CLIFF-{n:03}" for n in range(1, 120)}
    actual = {x["article_id"] for x in docs}
    metadata_only = sum(
        1 for item in docs
        if str(item.get("completeness_state", "")).startswith("METADATA_ONLY")
    )
    return {
        "json_articles": len(docs), "expected_slots": 119,
        "missing_slots": sorted(expected - actual),
        "full_text_records": len(docs) - metadata_only,
        "metadata_only_records": metadata_only,
        "symptom_labels": len(source["entries"]),
        "article_full_text_search": True,
        "original_pdf_archive_verified": False,
        "clinical_rules_validated": False,
        "read_only": True,
    }

