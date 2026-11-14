from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = ROOT / "submission" / "SCIENTIFIC_LIMITATIONS.md"


class TestSubmissionScientificLimitations(unittest.TestCase):
    def test_scientific_limitations_explicitly_label_gaps(self) -> None:
        self.assertTrue(DOC_PATH.is_file(), f"Missing {DOC_PATH}")
        text = DOC_PATH.read_text(encoding="utf-8")

        for required in (
            "Not Clinically Validated",
            "No Live Flight / Biomedical Hardware Connected",
            "NO_DATA",
            "UNVERIFIED",
            "0/119",
            "NOT_IMPORTED",
            "2050",
        ):
            self.assertIn(required, text)


if __name__ == "__main__":
    unittest.main()
