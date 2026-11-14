"""Read-only complete *available* source catalog for the NASA hackathon demo.

This loader never creates artificial observations or silently upgrades an
extracted CliFF JSON record to a verified, offline original NASA PDF.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re

EXPECTED_CLIFF = 119
EXPECTED_HAZARDS = (
    ("space_radiation", "space_radiation.json"),
    ("isolation_and_confinement", "isolation_confinement.json"),
    ("distance_from_earth", "distance_from_earth.json"),
    ("gravity_fields", "altered_gravity.json"),
    ("hostile_closed_environments", "hostile_closed_environment.json"),
)
MAX_ARTICLE_BYTES = 700_000
MAX_HAZARD_BYTES = 200_000
MAX_SYMPTOM_BYTES = 2_000_000
CLIFF_RE = re.compile(r"^CLIFF-(0[0-9][0-9]|1[01][0-9])$")


def source_root() -> Path | None:
    """Resolve installed snapshot first, then exact AETHERION checkout; no web."""
    override = os.environ.get("AETHERION_DEMO_DATA_ROOT")
    if override:
        root = Path(override).expanduser().resolve()
        return root if root.is_dir() else None
    package = Path(__file__).resolve().parent / "data"
    if (package / "cliff").is_dir() or (package / "hazards").is_dir():
        return package
    for base in Path(__file__).resolve().parents:
        original = base / "knowledge" / "nasa" / "cliff_119_2023" / "records"
        if original.is_dir():
            return base / "knowledge"
    return None


def _read_json(path: Path, cap: int) -> tuple[dict, str]:
    if not path.is_file():
        raise FileNotFoundError(path.name)
    if path.stat().st_size > cap:
        raise ValueError("Overlarge scientific record " + path.name)
    raw = path.read_bytes()
    value = json.loads(raw.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Scientific record must be a JSON object")
    return value, hashlib.sha256(raw).hexdigest()


def _directories(root: Path) -> tuple[Path, Path, Path]:
    if (root / "cliff").is_dir() or (root / "hazards").is_dir():
        return root / "cliff", root / "hazards", root / "symptoms.json"
    return (root / "nasa" / "cliff_119_2023" / "records",
            root / "nasa" / "hazards",
            root / "symptoms" / "ASTRA_819_REFERENCE.json")


def load_demo_catalog(progress=None) -> dict:
    """Import all locally available valid source JSON; never invent missing files.

    progress receives (processed, expected, source_kind), called from worker.
    The MA-7 numerical archive is one separate source and cannot be mixed into
    human profiles, hazard facts, translated glossary or CliFF evidence.
    """
    from .nasa_ma7 import load_real_nasa_data
    ma7 = load_real_nasa_data()  # fail closed: core numerical source required
    root = source_root()
    expected = EXPECTED_CLIFF + len(EXPECTED_HAZARDS) + 1
    done = 0
    def tick(kind: str):
        nonlocal done
        done += 1
        if progress:
            progress(done, expected, kind)
    # A distributable wheel contains an integrity manifest for the copied
    # JSON files. This checks local package integrity only, not NASA PDF SHA.
    installed_hashes: dict[str, str] | None = None
    if root is not None and (root / "snapshot.json").is_file():
        snapshot, _ = _read_json(root / "snapshot.json", 100_000)
        if snapshot.get("schema") != "aetherion-nasa-demo-package-v1":
            raise ValueError("Unsupported packaged NASA reference manifest")
        rows = snapshot.get("files")
        if not isinstance(rows, list):
            raise ValueError("Missing packaged NASA source inventory")
        installed_hashes = {}
        for item in rows:
            if (not isinstance(item, dict) or
                    not isinstance(item.get("path"), str) or
                    not isinstance(item.get("sha256"), str)):
                raise ValueError("Malformed packaged NASA source manifest")
            if item["path"] in installed_hashes:
                raise ValueError("Duplicate NASA package source path")
            installed_hashes[item["path"]] = item["sha256"]

    def check_hash(path: Path, digest: str):
        if installed_hashes is None:
            return
        if root is None:
            raise ValueError("Missing NASA source data root")
        relative = path.relative_to(root).as_posix()
        if installed_hashes.get(relative) != digest:
            raise ValueError("NASA JSON package checksum does not match manifest")

    articles = []
    hazards = []
    glossary = []
    warnings = []
    missing = []
    errors = []
    provenance = {"ma7": {"source_url": ma7["source_url"],
                          "state": "NASA_REPORT_TABLE_TRANSCRIPTION"}}
    if root is None:
        warnings.append("Reference catalog directory is not installed")
        missing = [f"CLIFF-{i:03}" for i in range(1, EXPECTED_CLIFF + 1)]
        for _ in range(expected):
            tick("not_installed")
    else:
        cliff_root, hazard_root, glossary_file = _directories(root)
        for number in range(1, EXPECTED_CLIFF + 1):
            ident = f"CLIFF-{number:03}"
            try:
                record_path = cliff_root / (ident + ".json")
                record, digest = _read_json(record_path, MAX_ARTICLE_BYTES)
                check_hash(record_path, digest)
                if (record.get("article_id") != ident or
                        not isinstance(record.get("sections"), list) or
                        not isinstance(record.get("tables"), list) or
                        not isinstance(record.get("references"), list) or
                        not isinstance(record.get("source"), dict)):
                    raise ValueError("CliFF schema or identity does not match source slot")
                # NASA source claim is preserved as data, never proof of original PDF.
                title = record.get("display_title")
                if not isinstance(title, str) or not title.strip():
                    raise ValueError("CliFF title missing")
                articles.append(record)
                provenance[ident] = {"local_json_sha256": digest,
                                     "original_pdf_sha_verified": False,
                                     "source_claim": record["source"].get("verification_state")}
            except FileNotFoundError:
                missing.append(ident)
            except (OSError, ValueError, UnicodeError, TypeError) as ex:
                errors.append(f"{ident}: {type(ex).__name__}")
                missing.append(ident)
            tick("cliff")
        for ident, filename in EXPECTED_HAZARDS:
            try:
                hazard_path = hazard_root / filename
                hazard, digest = _read_json(hazard_path, MAX_HAZARD_BYTES)
                check_hash(hazard_path, digest)
                if (hazard.get("hazard_id") != ident or
                        hazard.get("is_live_telemetry") is not False or
                        not isinstance(hazard.get("primary_sources"), list) or
                        not hazard["primary_sources"]):
                    raise ValueError("NASA hazard identity or evidence metadata missing")
                hazards.append(hazard)
                provenance[ident] = {"local_json_sha256": digest,
                                     "state": "NASA_SOURCE_LINKED_REFERENCE_ONLY"}
            except (OSError, ValueError, UnicodeError, TypeError) as ex:
                errors.append(f"{ident}: {type(ex).__name__}")
            tick("hazards")
        try:
            dictionary, digest = _read_json(glossary_file, MAX_SYMPTOM_BYTES)
            check_hash(glossary_file, digest)
            if (dictionary.get("total_labels") != 819 or
                    dictionary.get("clinical_validation_completed") is not False or
                    not isinstance(dictionary.get("entries"), list) or
                    len(dictionary["entries"]) != 819):
                raise ValueError("Wrong size/review status for original symptom reference")
            glossary = dictionary["entries"]
            provenance["symptoms"] = {"local_json_sha256": digest,
                                      "state": "ORIGINAL_VI_NOT_CLINICALLY_REVIEWED"}
        except (OSError, ValueError, UnicodeError, TypeError) as ex:
            errors.append(f"symptoms: {type(ex).__name__}")
        tick("symptoms")
    return {
        "dataset_id": ma7["dataset_id"],
        "ma7": ma7,
        "articles": tuple(articles),
        "hazards": tuple(hazards),
        "glossary": tuple(glossary),
        "missing_cliff": tuple(missing),
        "errors": tuple(errors),
        "warnings": tuple(warnings),
        "provenance": provenance,
        "total_loaded": 19 + len(articles) + len(hazards) + len(glossary),
        "counts": {
            "ma7_timepoints": 19, "ma7_non_null_values": sum(
                1 for group in ma7["groups"] for row in group["records"]
                for value in row["measures"].values() if value["value"] is not None),
            "cliff": len(articles), "cliff_expected": EXPECTED_CLIFF,
            "hazards": len(hazards), "hazards_expected": len(EXPECTED_HAZARDS),
            "symptoms": len(glossary), "symptoms_expected": 819,
        },
        "source_root": str(root) if root is not None else "",
    }


def local_article_text(record: dict) -> str:
    """Unmodified original extracted paragraphs for full reading."""
    return "\n\n".join(
        str(section.get("heading", "")) + "\n" + str(section.get("text_content", ""))
        for section in record.get("sections", []) if isinstance(section, dict)
    )
