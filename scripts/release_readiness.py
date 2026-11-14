#!/usr/bin/env python3
"""Evidence-conservative Quest release gate report; never authorizes release.

This audit inspects declared Quest metadata only. It does NOT execute an EXE,
verify health claims, contact NASA, or approve a human clinical workflow.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re

GATES = (
    ("Q-0002", "native_windows_boot", ("demo", "release")),
    ("Q-0003", "clean_windows_install", ("release",)),
    ("Q-0004", "independent_api_and_desktop", ("demo", "release")),
    ("Q-0005", "safe_runtime_configuration", ("release",)),
    ("Q-0010", "native_windows_executable", ("release",)),
    ("Q-0047", "authenticated_observation_api", ("demo", "release")),
    ("Q-0061", "real_mission_control", ("demo", "release")),
    ("Q-0091", "persisted_care_journey", ("demo", "release")),
    ("Q-0106", "nasa_source_provenance", ("demo", "release")),
    ("Q-0241", "actual_green_ci", ("demo", "release")),
    ("Q-0256", "official_team_challenge_proof", ("demo",)),
    ("Q-0435", "119_article_offline_library_acceptance", ("library",)),
)


def quest_metadata(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    data = path.read_text(encoding="utf-8")
    block = re.match(r"\A---\s*\n(.*?)\n---\s*\n", data, re.S)
    if block is None:
        return {}
    meta = {}
    for line in block.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip().strip('"')
    return meta


def classify(meta: dict[str, str]) -> str:
    if not meta:
        return "MISSING_QUEST"
    if meta.get("status") != "DONE":
        return "NOT_COMPLETE"
    if meta.get("review") != "APPROVED":
        return "REVIEW_PENDING"
    owner = meta.get("owner", "").strip().lower()
    reviewer = meta.get("reviewer", "").strip().lower()
    if not reviewer or reviewer == "null" or reviewer.startswith(owner + " ") or reviewer == owner or "self-" in reviewer or "self check" in reviewer or "self-check" in reviewer:
        return "SELF_OR_UNVERIFIED_REVIEW"
    if not re.fullmatch(r"[0-9a-f]{40}", meta.get("tested_commit", "")):
        return "MISSING_TESTED_COMMIT"
    evidence = meta.get("evidence", "").strip()
    if evidence in {"", "[]", "null", "_none_"}:
        return "MISSING_EVIDENCE"
    return "RECORDED_ACCEPTANCE_NOT_RETESTED"


def evaluate(repo: Path, scope: str) -> dict:
    selected = []
    for quest_id, name, scopes in GATES:
        if scope not in scopes:
            continue
        meta = quest_metadata(repo / "quests" / "v1" / f"{quest_id}.md")
        result = classify(meta)
        selected.append({
            "quest": quest_id,
            "gate": name,
            "quest_status": meta.get("status", "MISSING"),
            "review": meta.get("review", "MISSING"),
            "documentary_status": result,
            "source": f"quests/v1/{quest_id}.md",
        })
    ready = all(item["documentary_status"] == "RECORDED_ACCEPTANCE_NOT_RETESTED" for item in selected)
    return {
        "as_of_utc": datetime.now(timezone.utc).isoformat(),
        "scope": scope,
        "documentary_gates_complete": ready,
        "release_authorized": False,
        "note": "Metadata is not independent proof of a running Windows binary, NASA submission, patient safety, or deployment authorization.",
        "gates": selected,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Conservative AETHERION release evidence matrix")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--scope", choices=["demo", "release", "library"], default="demo")
    parser.add_argument("--output", type=Path, help="Optional machine-readable JSON report")
    args = parser.parse_args(argv)
    result = evaluate(args.repo, args.scope)
    content = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding="utf-8")
    print(content, end="")
    return 0 if result["documentary_gates_complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
