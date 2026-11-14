#!/usr/bin/env python3
"""Mechanical independent-review queue, not a substitute for a separate review agent.

Run from repository checkout every 15 minutes. Emits report for an independent
agent to examine acceptance evidence. Never changes Quest PASS/DONE status.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
QUESTS = ROOT / "quests" / "v1"


def frontmatter(data: str) -> dict[str, str]:
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n", data, flags=re.DOTALL)
    if not match:
        return {}
    info = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            info[key.strip()] = value.strip()
    return info


def changed_quest_paths() -> set[str]:
    try:
        raw = subprocess.check_output(
            ["git", "-C", str(ROOT), "log", "--since=30 minutes ago",
             "--name-only", "--pretty=format:", "--", "quests/v1/"],
            stderr=subprocess.DEVNULL, text=True, timeout=15,
        )
        return {line.strip() for line in raw.splitlines()
                if re.fullmatch(r"quests/v1/Q-\d{4}\.md", line.strip())}
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return set()


def git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL, text=True, timeout=10,
        ).strip()
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return "UNKNOWN"


def scan() -> tuple[list[dict[str, str]], collections.Counter]:
    changed = changed_quest_paths()
    tasks = []
    counts: collections.Counter = collections.Counter()
    for path in sorted(QUESTS.glob("Q-????.md")):
        content = path.read_text(encoding="utf-8")
        m = frontmatter(content)
        status = m.get("status", "UNKNOWN")
        review = m.get("review", "PENDING")
        counts[status] += 1
        relpath = path.relative_to(ROOT).as_posix()
        reason = ""
        if status == "DONE":
            reviewer = (m.get("reviewer_id") or m.get("reviewed_by")
                        or m.get("independent_reviewer") or "")
            owner = m.get("owner", "")
            if review != "APPROVED":
                reason = "DONE without review: APPROVED"
            elif reviewer and reviewer == owner:
                reason = "Self-approved by implementer; independent review required"
            elif not reviewer:
                reason = "DONE lacks identifiable independent reviewer"
            elif not (
                m.get("tested_commit")
                or m.get("implementation_commit")
                or m.get("commit_sha")
                or re.search(r"\b[0-9a-f]{40}\b", content)
            ):
                reason = "DONE without identifiable commit SHA; inspect claimed evidence"
            elif relpath in changed:
                reason = "Recently changed DONE; review evidence at current HEAD"
        elif review in {"PENDING", "COMPONENT_APPROVED", "REWORK_REQUIRED"} and (
            m.get("implementation_state") in {"COMPONENT_READY", "READY_FOR_REVIEW"}
            or review in {"COMPONENT_APPROVED", "REWORK_REQUIRED"}
        ):
            reason = "Component/rework awaits independent review"
        elif status == "RUNNING" and m.get("implementation_state") in {
            "COMPONENT_READY", "READY_FOR_REVIEW"
        }:
            reason = "Running Quest claims complete component"
        elif relpath in changed and status in {"RUNNING", "BLOCKED", "READY", "QUEUED"}:
            reason = "Quest changed recently; check for new evidence"

        if reason:
            tasks.append({
                "id": m.get("id", path.stem),
                "path": relpath,
                "status": status,
                "review": review,
                "owner": m.get("owner", ""),
                "reason": reason,
            })
    tasks.sort(key=lambda x: (x["status"] != "DONE", x["id"]))
    return tasks, counts


def render(items: list[dict[str, str]], counts: collections.Counter) -> str:
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    out = [
        "# AETHERION independent acceptance queue",
        "",
        f"- Generated UTC: {timestamp}",
        f"- Git HEAD: \`{git_sha()}\`",
        f"- Quest files enumerated: **{sum(counts.values())}**",
        f"- Status distribution: \`{dict(sorted(counts.items()))}\`",
        f"- Potential review items: **{len(items)}**",
        "",
        "> This is a mechanical triage, **not** an AI or human review and never",
        "> grants APPROVED/DONE. A separate agent must inspect each task's original",
        "> acceptance criteria, actual diff, evidence and integration requirements.",
        "",
        "| Quest | Current state | Review | Claim owner | Why inspect |",
        "|---|---|---|---|---|",
    ]
    for t in items[:100]:
        link = f"[{t['id']}](https://github.com/huyng0699-arch/AETHERION/blob/main/{t['path']})"
        cells = [link, t["status"], t["review"], t["owner"], t["reason"]]
        out.append("| " + " | ".join(c.replace("|", "\\|").replace("\n", " ")
                                   for c in cells) + " |")
    if len(items) > 100:
        out += ["", f"**Only first 100 of {len(items)} candidates displayed.**"]
    if not items:
        out += ["| — | — | — | — | No entries match current mechanical review rules |"]
    out += [
        "", "## Required independent action",
        "",
        "1. Read \`quests/review/REVIEW-0001.md\` and \`AGENTS.md\`.",
        "2. For each candidate, fetch the **current** Quest and actual implemented commit.",
        "3. Compare original acceptance and actual behavior; don't infer PASS from this queue.",
        "4. Record reviewer identity, reviewed Git SHA, evidence and approval/rework",
        "   in that Quest using compare-and-swap. Never self-approve.",
        "5. Repeat on the next cycle; avoid duplicate reviews of an unchanged artifact.",
        ""
    ]
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="quest-review-report.md")
    args = parser.parse_args()
    if not QUESTS.is_dir():
        parser.error("Quest directory is missing")
    items, counts = scan()
    report = render(items, counts)
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(report, encoding="utf-8")
    print(f"Reviewed mechanically: {sum(counts.values())} Quest files; "
          f"queued {len(items)} for independent review; wrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
