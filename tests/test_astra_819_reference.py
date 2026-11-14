"""Focused verification for Q-0441: ASTRA 819 symptom vocabulary provenance."""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "knowledge" / "symptoms" / "ASTRA_819_REFERENCE.json"
README_PATH = REPO_ROOT / "knowledge" / "symptoms" / "README.md"
EXPECTED_GIT_BLOB = "f76580a14166499433cea7f93cbb89f7db62ec17"


class Astra819ReferenceTests(unittest.TestCase):
    def test_exact_git_blob_counts_and_unreviewed_flags(self) -> None:
        raw = REFERENCE_PATH.read_bytes()
        git_blob = hashlib.sha1(f"blob {len(raw)}\0".encode("utf-8") + raw).hexdigest()
        self.assertEqual(git_blob, EXPECTED_GIT_BLOB)

        payload = json.loads(raw.decode("utf-8"))
        self.assertEqual(payload["total_labels"], 819)
        self.assertEqual(payload["total_links"], 826)
        self.assertEqual(len(payload["entries"]), 819)
        self.assertFalse(payload["clinical_validation_completed"])
        self.assertEqual(payload["classification_method"], "provisional_author_heuristic")

        counts = payload["counts"]
        self.assertEqual(counts.get("emergency"), 41)
        self.assertEqual(counts.get("urgent"), 125)
        self.assertEqual(counts.get("routine"), 653)

        readme = README_PATH.read_text(encoding="utf-8")
        self.assertIn(EXPECTED_GIT_BLOB, readme)
        self.assertIn("clinical_validation_completed=false", readme)


if __name__ == "__main__":
    unittest.main()
