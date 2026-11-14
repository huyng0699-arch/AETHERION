#!/usr/bin/env python3
"""List READY and QUEUED Quests that can start independent implementation now.

Read-only: does not claim, approve, reorder, or modify dependencies.
"""
from pathlib import Path
import argparse
import re

ROOT = Path(__file__).resolve().parents[1]
QUESTS = ROOT / "quests" / "v1"


def parse(path):
    data = path.read_text(encoding="utf-8")
    block = re.match(r"\A---\s*\n(.*?)\n---\s*\n", data, re.S)
    if not block:
        return {}
    result = {}
    for line in block.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip()
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--priority", choices=["P0", "P1", "P2", "P3"])
    args = ap.parse_args()
    tasks = {p.stem: parse(p) for p in QUESTS.glob("Q-????.md")}
    rows = []
    for ident, info in tasks.items():
        status, priority = info.get("status"), info.get("priority", "P3")
        if status not in {"READY", "QUEUED"}:
            continue
        if args.priority and args.priority != priority:
            continue
        if not args.priority and priority in {"P2", "P3"}:
            continue
        deps = re.findall(r"Q-\d{4}", info.get("depends_on", "[]"))
        pending = [d for d in deps if tasks.get(d, {}).get("status") != "DONE"]
        rows.append(({"P0": 0, "P1": 1, "P2": 2, "P3": 3}.get(priority, 9),
                     ident, status, priority, pending))
    rows.sort()
    print("PARALLEL START QUEUE — dependency PASS is not needed to START")
    for _, ident, state, priority, pending in rows[:max(args.limit, 0)]:
        print(f"{ident}  {priority}  {state:7}  integration_pending="
              f"{','.join(pending) or '-'}")
    print(f"Eligible: {len(rows)}; listed: {min(len(rows), max(0, args.limit))}")
    print("Claim by exact GitHub blob SHA; preserve dependencies, exclusive paths.")
    print("Only an independent reviewer can approve final integrated DONE.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
