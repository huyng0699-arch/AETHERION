#!/usr/bin/env python3
"""Record reproducible evidence for an *existing* native Windows screenshot.

This tool does not capture, generate, alter, or certify screenshots. The operator
must capture the real application on Windows and inspect it independently.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import platform
import struct
import subprocess
import sys
from datetime import datetime, timezone

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def inspect_png(path: Path) -> dict[str, object]:
    with path.open("rb") as stream:
        header = stream.read(24)
    if len(header) != 24 or header[:8] != PNG_SIGNATURE or header[12:16] != b"IHDR":
        raise ValueError("Not a PNG with a valid IHDR header")
    width, height = struct.unpack(">II", header[16:24])
    if not 0 < width <= 32768 or not 0 < height <= 32768:
        raise ValueError("Implausible PNG dimensions")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return {"sha256": digest.hexdigest(), "bytes": path.stat().st_size,
            "width_px": width, "height_px": height}


def git_head() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD"], capture_output=True,
        text=True, check=True, timeout=10,
    )
    sha = result.stdout.strip()
    if len(sha) != 40 or any(c not in "0123456789abcdef" for c in sha):
        raise ValueError("Unexpected Git commit identifier")
    return sha


def windows_dpi() -> int:
    try:
        return int(ctypes.windll.user32.GetDpiForSystem())
    except (AttributeError, OSError) as exc:
        raise RuntimeError("Cannot read Windows system DPI") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True, type=Path, help="Existing real Windows PNG")
    parser.add_argument("--output", required=True, type=Path, help="New JSON evidence file")
    parser.add_argument("--screen", required=True, help="Actual screen/route shown")
    parser.add_argument("--notes", required=True, help="Human observation, not a PASS claim")
    args = parser.parse_args(argv)

    if os.name != "nt":
        parser.error("Real Windows required; no Linux/macOS evidence substitution")
    if not args.image.is_file():
        parser.error("Screenshot file does not exist")
    if args.output.exists():
        parser.error("Output already exists; refusing to overwrite evidence")
    try:
        details = inspect_png(args.image)
        commit = git_head()
        dpi = windows_dpi()
    except (ValueError, OSError, RuntimeError, subprocess.SubprocessError) as exc:
        parser.error(str(exc))
    evidence = {
        "schema": "aetherion.windows_screenshot_evidence.v1",
        "captured_by_tool": False,
        "verified_application_render": False,
        "independent_review": "PENDING",
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(),
        "system_dpi": dpi,
        "system_scale_percent": round(dpi / 96 * 100, 2),
        "git_head": commit,
        "screen": args.screen,
        "operator_notes": args.notes,
        "screenshot_filename": args.image.name,
        "screenshot": details,
        "limitations": [
            "PNG header and hash do not prove the app is visible or genuine.",
            "Operator must verify screenshot content, app state and provenance.",
            "No Windows build, navigation, accessibility or medical acceptance inferred.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(evidence, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(f"Recorded evidence: {args.output} (review PENDING)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
