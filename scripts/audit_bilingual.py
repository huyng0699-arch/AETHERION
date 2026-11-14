#!/usr/bin/env python3
"""Small, read-only bilingual and source-language audit. No clinical translation.

Usage: python scripts/audit_bilingual.py
This checks only string-catalog consistency and the language provenance boundary.
It never modifies, guesses translations for, or certifies NASA/medical records.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import string
import sys

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "apps" / "desktop" / "src" / "aetherion_desktop"
CATALOGS = PACKAGE / "i18n"
DATA = ROOT / "knowledge"
SOURCES = DATA / "nasa" / "cliff_119_2023"


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def fields(message: str) -> set[str]:
    found: set[str] = set()
    for _text, name, _format_spec, _conversion in string.Formatter().parse(message):
        if name:
            found.add(name)
    return found


def check_catalogs() -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    vi = read_json(CATALOGS / "vi.json")
    en = read_json(CATALOGS / "en.json")
    if not isinstance(vi, dict) or not isinstance(en, dict):
        return ["Both locale catalogs must be JSON objects."], {}
    keys_vi, keys_en = set(vi), set(en)
    for key in sorted(keys_vi - keys_en):
        errors.append(f"English translation missing: {key}")
    for key in sorted(keys_en - keys_vi):
        errors.append(f"Vietnamese translation missing: {key}")
    for key in sorted(keys_vi & keys_en):
        a, b = vi[key], en[key]
        if not isinstance(a, str) or not a.strip() or not isinstance(b, str) or not b.strip():
            errors.append(f"Invalid empty/non-string translation: {key}")
            continue
        try:
            if fields(a) != fields(b):
                errors.append(f"Variable placeholders differ: {key}")
        except ValueError as error:
            errors.append(f"Invalid brace placeholder {key}: {error}")

    # Only literal semantic keys used by tr(locale, "key") are audited;
    # dynamically constructed tile keys are checked separately.
    literal_refs: set[str] = set()
    python_sources = list(PACKAGE.rglob("*.py"))
    for path in python_sources:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, UnicodeError) as error:
            errors.append(f"Python parse error in {path.relative_to(ROOT)}: {error}")
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
                continue
            if node.func.id == "tr" and len(node.args) >= 2:
                arg = node.args[1]
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    literal_refs.add(arg.value)
    for key in sorted(literal_refs - keys_en):
        errors.append(f"Referenced UI translation not defined in both catalogs: {key}")
    for stem in ("heart", "activity", "sleep", "mass", "energy", "mood"):
        key = f"personal.tile.{stem}"
        if key not in keys_en or key not in keys_vi:
            errors.append(f"Required dynamic tile translation missing: {key}")
    return errors, {
        "vi_catalog_entries": len(keys_vi),
        "en_catalog_entries": len(keys_en),
        "literal_ui_key_references": len(literal_refs),
        "python_files_parsed": len(python_sources),
    }


def audit_symptom_english_aliases() -> tuple[list[str], dict[str, int | str]]:
    """Validate the additive English terminology without touching source JSON."""
    errors: list[str] = []
    source_path = DATA / "symptoms" / "ASTRA_819_REFERENCE.json"
    overlay_path = DATA / "symptoms" / "label_aliases_en.json"
    if not source_path.is_file() or not overlay_path.is_file():
        return ["Original symptom source or English alias overlay missing"], {}
    try:
        source_bytes = source_path.read_bytes()
        original = json.loads(source_bytes.decode("utf-8"))
        overlay = read_json(overlay_path)
        if not isinstance(original, dict) or not isinstance(overlay, dict):
            return ["Symptom source/overlay must both be JSON objects"], {}
        source_hash = hashlib.sha1(
            b"blob " + str(len(source_bytes)).encode("ascii") + bytes((0,)) + source_bytes
        ).hexdigest()
        if overlay.get("source_blob_sha") != source_hash:
            errors.append("English overlay targets a different source Git blob; labels are stale")
        if (overlay.get("source_language"), overlay.get("target_language"),
                overlay.get("translation_status")) != (
                    "vi", "en", "UNREVIEWED_TERMINOLOGY"):
            errors.append("English symptom overlay has incorrect language/review metadata")
        original_by_name = {
            row.get("name"): row for row in original.get("entries", [])
            if isinstance(row, dict) and isinstance(row.get("name"), str)
        }
        entries = overlay.get("labels", [])
        if not isinstance(entries, list):
            return ["English alias labels must be an array"], {}
        seen_ids: set[str] = set()
        seen_terms: dict[str, str] = {}
        for index, item in enumerate(entries):
            if not isinstance(item, dict):
                errors.append(f"Alias #{index} is not an object")
                continue
            vi = item.get("source_label_vi")
            ident = item.get("symptom_id")
            english = item.get("label_en")
            other = item.get("aliases_en", [])
            original_entry = original_by_name.get(vi) if isinstance(vi, str) else None
            if (not original_entry or not isinstance(ident, str)
                    or ident not in original_entry.get("ids", [])):
                errors.append(f"Alias #{index} has no matching original Vietnamese label/ID")
            if not isinstance(english, str) or not english.strip():
                errors.append(f"Alias #{index} has no English label")
                continue
            if not isinstance(other, list) or not all(
                isinstance(x, str) and x.strip() for x in other
            ):
                errors.append(f"Alias #{index} has invalid English synonyms")
                continue
            if ident in seen_ids:
                errors.append(f"Repeated symptom ID in English overlay: {ident}")
            seen_ids.add(str(ident))
            for term in (english, *other):
                normalized_term = " ".join(term.casefold().split())
                previous = seen_terms.get(normalized_term)
                if previous is not None and previous != ident:
                    errors.append(f"Ambiguous English alias: {term}")
                seen_terms[normalized_term] = str(ident)
        return errors, {
            "source_symptom_labels": len(original_by_name),
            "english_draft_labels": len(entries),
            "distinct_english_search_terms": len(seen_terms),
            "translation_review_status": "UNREVIEWED_TERMINOLOGY",
        }
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        return [f"Unable to audit English alias source integrity: {type(exc).__name__}"], {}


def audit_data_paths() -> dict[str, int | bool]:
    # Counting records is not a verdict that the original PDFs are installed.
    records = list((SOURCES / "records").glob("CLIFF-*.json"))
    qa = list((SOURCES / "qa").glob("CLIFF-*.json"))
    media = list((SOURCES / "media").glob("CLIFF-*/*.json"))
    symptom = DATA / "symptoms" / "ASTRA_819_REFERENCE.json"
    symptom_reference_has_vietnamese_names = False
    if symptom.is_file():
        obj = read_json(symptom)
        if isinstance(obj, dict):
            entries = obj.get("entries", [])
            if isinstance(entries, list):
                symptom_reference_has_vietnamese_names = any(
                    isinstance(item, dict) and
                    any(char in str(item.get("name", "")) for char in "ăâđêôơưáàảãạĂÂĐÊÔƠƯ")
                    for item in entries
                )
    own_json = list(DATA.rglob("*.json")) + list((ROOT / "packages" / "contracts").rglob("*.json"))
    return {
        "medical_cliff_record_json_count": len(records),
        "medical_cliff_qa_json_count": len(qa),
        "medical_image_provenance_json_count": len(media),
        "source_reference_uses_vietnamese_symptom_labels": symptom_reference_has_vietnamese_names,
        "knowledge_and_contract_json_count": len(own_json),
        "scientific_originals_translation_verified": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print machine-readable audit")
    args = parser.parse_args()
    errors, catalog = check_catalogs()
    alias_errors, alias_stats = audit_symptom_english_aliases()
    errors.extend(alias_errors)
    report = {
        "result": "PASS" if not errors else "FAIL",
        "catalogs": catalog,
        "english_symptom_overlay": alias_stats,
        "source_data_observations": audit_data_paths(),
        "notes": (
            "Counts do not prove that NASA PDF originals were downloaded or reviewed.",
            "The symptom source is Vietnamese; English clinical aliases require separate review.",
            "NASA original source text must remain unchanged when switching UI languages.",
        ),
        "errors": errors,
    }
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"BILINGUAL {report['result']}: {catalog.get('vi_catalog_entries', 0)} VI / "
              f"{catalog.get('en_catalog_entries', 0)} EN UI keys")
        print(f"CliFF records: {report['source_data_observations']['medical_cliff_record_json_count']}; "
              f"QA: {report['source_data_observations']['medical_cliff_qa_json_count']}; "
              f"media: {report['source_data_observations']['medical_image_provenance_json_count']}")
        for error in errors:
            print("ERROR:", error, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
