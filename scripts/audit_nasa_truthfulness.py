#!/usr/bin/env python3
"""Independent truthfulness and NASA-branding audit across knowledge/nasa/ and submission/."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_BRANDING_PATTERNS = (
    re.compile(r"\bendorsed by nasa\b", re.IGNORECASE),
    re.compile(r"\bcertified by nasa\b", re.IGNORECASE),
    re.compile(r"\bofficial nasa product\b", re.IGNORECASE),
    re.compile(r"\bflight[- ]certified\b", re.IGNORECASE),
)


def audit_truthfulness(root_dir: Path = ROOT) -> list[str]:
    findings: list[str] = []
    nasa_dir = root_dir / "knowledge" / "nasa"

    for json_file in sorted(nasa_dir.rglob("*.json")):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            findings.append(f"{json_file.relative_to(root_dir)}: invalid JSON ({exc})")
            continue

        # Check no JSON payload claims NASA research is live telemetry
        if isinstance(data, dict) and data.get("is_live_telemetry") is True:
            findings.append(f"{json_file.relative_to(root_dir)}: is_live_telemetry must not be true")

        # Check CliFF 119 status is never falsely marked complete without 119 PDFs
        if json_file.name == "cliff_119_status.json":
            if data.get("is_119_complete") is True and data.get("verified_pdf_count", 0) != 119:
                findings.append(f"{json_file.relative_to(root_dir)}: fabricated 119 completeness")

    for scan_dir in (nasa_dir, root_dir / "submission"):
        if not scan_dir.is_dir():
            continue
        for md_file in sorted(scan_dir.rglob("*.md")):
            text = md_file.read_text(encoding="utf-8")
            for pattern in FORBIDDEN_BRANDING_PATTERNS:
                for match in pattern.finditer(text):
                    line_start = text.rfind("\n", 0, match.start()) + 1
                    prefix = text[line_start:match.start()].lower()
                    if any(w in prefix for w in ("not", "never", "no ")):
                        continue
                    findings.append(
                        f"{md_file.relative_to(root_dir)}: inaccurate NASA branding/certification claim matching {pattern.pattern!r}"
                    )

    return findings


def main() -> int:
    findings = audit_truthfulness()
    if findings:
        for item in findings:
            print(f"FAIL: {item}")
        return 1
    print("OK: NASA scientific truthfulness and branding audit passed (0 violations).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
