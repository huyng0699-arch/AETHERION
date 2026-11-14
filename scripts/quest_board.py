#!/usr/bin/env python3
"""Validate and inspect the AETHERION Quest backlog; no third-party dependencies."""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUESTS = ROOT / "quests" / "v1"
VALID_STATES = {"READY", "QUEUED", "PLANNED", "RUNNING", "DONE", "BLOCKED", "STALE"}
VALID_PRIORITIES = {"P0", "P1", "P2", "P3"}


def parse_quest(file: Path) -> dict[str, object]:
    """Read the small YAML frontmatter subset used in Quest specs.

    Supports inline arrays and indented '- item' lists. Ignore indented
    description/block-scalar content: text containing colons is not a new
    frontmatter key. Never execute arbitrary YAML tags or import PyYAML.
    """
    data = file.read_text(encoding="utf-8-sig")
    match = re.match(r"\\A---[ \\t]*\\r?\\n(.*?)\\r?\\n---[ \\t]*\\r?\\n", data, flags=re.DOTALL)
    if not match:
        raise ValueError(f"{file}: missing or malformed YAML frontmatter")

    meta: dict[str, object] = {}
    active_list: str | None = None
    for raw in match.group(1).splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if raw[0].isspace():
            if active_list and re.match(r"^\\s*-\\s+", raw):
                existing = meta.get(active_list)
                if isinstance(existing, list):
                    item = re.sub(r"^\\s*-\\s+", "", raw).strip().strip("'\\\"")
                    if item:
                        existing.append(item)
            # Continuation text, YAML literal block or nested object; not a
            # new top-level attribute and never a silent status override.
            continue
        active_list = None
        found = re.fullmatch(r"([A-Za-z_][A-Za-z_0-9-]*):[ \\t]*(.*)", raw)
        if not found:
            raise ValueError(f"{file}: malformed top-level metadata: {raw!r}")
        key, value = found.groups()
        if key in meta:
            raise ValueError(f"{file}: duplicate frontmatter key: {key}")
        value = value.strip()
        if not value:
            meta[key] = []
            active_list = key
        elif value in {"|", "|-", "|+", ">", ">-", ">+"}:
            meta[key] = ""  # multiline prose is not a machine state
        elif value.startswith("[") and value.endswith("]"):
            meta[key] = [
                part.strip().strip("'\\\"")
                for part in value[1:-1].split(",")
                if part.strip()
            ]
        else:
            meta[key] = value.strip("'\\\"")
    return meta


def scan_all() -> tuple[dict[str, dict[str, object]], list[str]]:
    """Collect every readable Quest even if one file has broken frontmatter."""
    tasks: dict[str, dict[str, object]] = {}
    problems: list[str] = []
    if not QUESTS.is_dir():
        return tasks, [f"Quest directory is missing: {QUESTS}"]
    for path in sorted(QUESTS.glob("Q-????.md")):
        try:
            meta = parse_quest(path)
        except (OSError, UnicodeError, ValueError) as exc:
            problems.append(str(exc))
            continue
        quest_id = str(meta.get("id", ""))
        if quest_id != path.stem:
            problems.append(f"{path}: frontmatter ID mismatch: {quest_id!r}")
            continue
        if quest_id in tasks:
            problems.append(f"Duplicate Quest ID: {quest_id}")
            continue
        tasks[quest_id] = meta
    return tasks, problems


def load_all() -> dict[str, dict[str, object]]:
    """Strict API used by validators/tests; do not silently drop corrupt files."""
    tasks, errors = scan_all()
    if errors:
        raise ValueError("; ".join(errors[:10]))
    return tasks


def verify(tasks: dict[str, dict[str, object]]) -> list[str]:
    errors: list[str] = []
    if not tasks:
        errors.append("No Quest files found")
        return errors
    expected = {f"Q-{i:04d}" for i in range(1, len(tasks) + 1)}
    if set(tasks) != expected:
        errors.append(f"Expected contiguous Q-0001..Q-{len(tasks):04d}; missing={sorted(expected - set(tasks))}, extra={sorted(set(tasks) - expected)}")

    for ident, info in tasks.items():
        state = info.get("status")
        priority = info.get("priority")
        deps = info.get("depends_on")
        if state not in VALID_STATES:
            errors.append(f"{ident}: invalid status {state}")
        if priority not in VALID_PRIORITIES:
            errors.append(f"{ident}: invalid priority {priority}")
        if not isinstance(deps, list):
            errors.append(f"{ident}: depends_on not a list")
            continue
        if ident in deps:
            errors.append(f"{ident}: self-dependency")
        if len(deps) != len(set(deps)):
            errors.append(f"{ident}: duplicate dependencies")
        for dep in deps:
            if dep not in tasks:
                errors.append(f"{ident}: unknown dependency {dep}")
        # Owner policy permits READY/QUEUED components to start implementation
        # before their prerequisites are DONE. Retain dependency edges; prevent
        # final acceptance through the separate DONE/reviewer gates.
        if state == "DONE" and info.get("review") != "APPROVED":
            errors.append(f"{ident}: DONE without review: APPROVED")
        if state == "RUNNING" and (info.get("owner") in (None, "null", "") or info.get("run_id") in (None, "null", "")):
            errors.append(f"{ident}: RUNNING without owner and run_id")
    visited: set[str] = set()
    in_stack: set[str] = set()

    def visit(node: str) -> None:
        if node in in_stack:
            errors.append(f"Dependency cycle detected: {node}")
            return
        if node in visited:
            return
        in_stack.add(node)
        for dep in tasks[node].get("depends_on", []):
            if dep in tasks:
                visit(str(dep))
        in_stack.remove(node)
        visited.add(node)

    for task in tasks:
        visit(task)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command", choices=["check", "stats", "ready", "running", "json"],
        nargs="?", default="stats",
    )
    args = parser.parse_args()
    tasks, read_errors = scan_all()
    issues = read_errors + verify(tasks)

    # Validation is strict. Read-only listings must remain available if one
    # Quest is malformed: the user must still be able to identify the work
    # queue and repair the offending record.
    if args.command == "check":
        if issues:
            for issue in issues:
                print("ERROR:", issue)
            print(f"FAILED: {len(tasks)} readable Quest specs; {len(issues)} integrity issues")
            return 1
        print(f"OK: {len(tasks)} unique Quest specs; IDs contiguous; dependencies valid and acyclic")
        return 0

    if not tasks:
        print("ERROR: No readable Quest files", file=sys.stderr)
        return 1
    if args.command == "stats":
        print("TOTAL", len(tasks))
        print("STATUS", dict(sorted(collections.Counter(
            str(x.get("status", "UNKNOWN")) for x in tasks.values()
        ).items())))
        print("PRIORITY", dict(sorted(collections.Counter(
            str(x.get("priority", "UNKNOWN")) for x in tasks.values()
        ).items())))
        print("STREAMS", dict(sorted(collections.Counter(
            str(x.get("stream", "UNKNOWN")) for x in tasks.values()
        ).items())))
    elif args.command == "ready":
        for ident, item in sorted(tasks.items()):
            if item.get("status") == "READY":
                print(ident, item.get("stream", "UNKNOWN"), item.get("priority", "UNKNOWN"))
    elif args.command == "running":
        for ident, item in sorted(tasks.items()):
            if item.get("status") == "RUNNING":
                print(ident, item.get("owner", "UNCLAIMED"), item.get("lease_until_utc", ""))
    else:
        print(json.dumps(tasks, indent=2, ensure_ascii=False))

    if issues:
        print(
            f"WARNING: Quest integrity has {len(issues)} issue(s); "
            "listing includes only readable Quest files. "
            "Run 'python scripts/quest_board.py check' for every error. "
            "This is NOT an acceptance PASS.",
            file=sys.stderr,
        )
        for issue in issues[:6]:
            print("WARNING:", issue, file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
