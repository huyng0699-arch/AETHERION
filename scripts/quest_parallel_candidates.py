#!/usr/bin/env python3
"""List READY and QUEUED Quests that can start independent implementation now.

Read-only: does not claim, approve, reorder, or modify dependencies.
"""
from pathlib import Path
import argparse
import sys

from quest_board import parse_quest

ROOT = Path(__file__).resolve().parents[1]
QUESTS = ROOT / "quests" / "v1"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--priority", choices=["P0", "P1", "P2", "P3"])
    args = ap.parse_args()
    tasks = {}
    malformed = []
    for path in sorted(QUESTS.glob("Q-????.md")):
        try:
            tasks[path.stem] = parse_quest(path)
        except (OSError, UnicodeError, ValueError) as exc:
            malformed.append(f"{path.stem}: {exc}")
    rows = []
    for ident, info in tasks.items():
        status, priority = info.get("status"), info.get("priority", "P3")
        if status not in {"READY", "QUEUED"}:
            continue
        if args.priority and args.priority != priority:
            continue
        if not args.priority and priority in {"P2", "P3"}:
            continue
        deps = info.get("depends_on", [])
        if not isinstance(deps, list):
            malformed.append(f"{ident}: depends_on is not a list")
            continue
        pending = [str(d) for d in deps if tasks.get(str(d), {}).get("status") != "DONE"]
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
    if malformed:
        print(f"WARNING: {len(malformed)} malformed/incomplete Quest records were not selected. "
              "Use scripts/quest_board.py check for strict diagnostics.", file=sys.stderr)
        for item in malformed[:8]:
            print("WARNING:", item, file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
