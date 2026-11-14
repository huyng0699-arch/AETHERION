"""Verification tests for Q-0257 English challenge response."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESPONSE_PATH = ROOT / "submission" / "CHALLENGE_RESPONSE.md"

REFERENCED_REPO_FILES = [
    "apps/server/src/aetherion_server/main.py",
    "apps/server/src/aetherion_server/store.py",
    "apps/desktop/src/aetherion_desktop/main.py",
    "knowledge/nasa/challenge_2026.json",
    "knowledge/nasa/osdr_datasets.json",
    "knowledge/nasa/cliff_119_2023/audit_status.json",
]


def test_challenge_response_covers_four_stage_loop_and_real_files() -> None:
    assert RESPONSE_PATH.is_file(), f"Missing {RESPONSE_PATH}"
    text = RESPONSE_PATH.read_text(encoding="utf-8")

    for stage in ("GATHER", "EVALUATE", "ACT", "RECHECK"):
        assert stage in text, f"Missing care stage {stage}"

    for rel_path in REFERENCED_REPO_FILES:
        assert rel_path in text, f"Expected reference to {rel_path}"
        assert (ROOT / rel_path).is_file(), f"Referenced file does not exist: {rel_path}"


def test_challenge_response_enforces_honesty_and_safety_disclaimers() -> None:
    text = RESPONSE_PATH.read_text(encoding="utf-8")
    lower = text.lower()
    assert "not flight-ready" in lower or "not clinically certified" in lower or "not fda" in lower
    assert "never passed off as live astronaut vital signs" in lower or "not live telemetry" in lower
    assert "0 / 119" in text
    assert "NO_DATA" in text
