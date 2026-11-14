#!/usr/bin/env python3
"""Validate and inspect the AETHERION 435-Quest backlog; no third-party dependencies."""
from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUESTS = ROOT / "quests" / "v1"
EXPECTED_COUNT = 435
VALID_STATES = {"READY", "QUEUED", "PLANNED", "RUNNING", "DONE", "BLOCKED", "STALE"}
VALID_PRIORITIES = {"P0", "P1", "P2", "P3"}


def parse_quest(file: Path) -> dict[str, object]:
    text = file.read_text(encoding="utf-8")
    match = re.match(r"---\s*\n(.*?)\n---\s*\n", text, flags=re.DOTALL)
    if not match:
        raise ValueError(f"{file}: missing YAML-style front matter")
    meta: dict[str, object] = {}
    for raw in match.group(1).splitlines():
        if ":" not in raw:
            raise ValueError(f"{file}: malformed metadata: {raw}")
        key, value = raw.split(":", 1)
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            meta[key.strip()] = [s.strip() for s in value[1:-1].split(",") if s.strip()]
        else:
            meta[key.strip()] = value
    return meta


def load_all() -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    for path in sorted(QUESTS.glob("Q-????.md")):
        meta = parse_quest(path)
        quest_id = str(meta.get("id", ""))
        if quest_id in result:
            raise ValueError(f"Duplicate Quest ID: {quest_id}")
        result[quest_id] = meta
        if quest_id != path.stem:
            raise ValueError(f"{path}: frontmatter ID mismatch: {quest_id}")
    return result


def verify(tasks: dict[str, dict[str, object]]) -> list[str]:
    errors: list[str] = []
    expected = {f"Q-{i:04d}" for i in range(1, EXPECTED_COUNT + 1)}
    if set(tasks) != expected:
        errors.append(f"Expected exactly {EXPECTED_COUNT} IDs; missing={sorted(expected - set(tasks))}, extra={sorted(set(tasks) - expected)}")

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
        if state == "READY" and any(tasks.get(dep, {}).get("status") != "DONE" for dep in deps):
            errors.append(f"{ident}: READY with unfinished dependency")
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
    parser.add_argument("command", choices=["check", "stats", "ready", "running", "json"], nargs="?", default="stats")
    args = parser.parse_args()
    tasks = load_all()
    issues = verify(tasks)
    if args.command == "check":
        if issues:
            for issue in issues:
                print("ERROR:", issue)
            return 1
        print(f"OK: {len(tasks)} unique Quest specs; IDs contiguous; dependencies valid and acyclic")
        return 0
    if issues:
        for issue in issues:
            print("ERROR:", issue)
        return 1
    if args.command == "stats":
        print("TOTAL", len(tasks))
        print("STATUS", dict(sorted(collections.Counter(x["status"] for x in tasks.values()).items())))
        print("PRIORITY", dict(sorted(collections.Counter(x["priority"] for x in tasks.values()).items())))
        print("STREAMS", dict(sorted(collections.Counter(x["stream"] for x in tasks.values()).items())))
    elif args.command == "ready":
        for k, v in tasks.items():
            if v["status"] == "READY":
                print(k, v["stream"], v["priority"])
    elif args.command == "running":
        for k, v in tasks.items():
            if v["status"] == "RUNNING":
                print(k, v["owner"], v.get("lease_until_utc", ""))
    else:
        print(json.dumps(tasks, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
