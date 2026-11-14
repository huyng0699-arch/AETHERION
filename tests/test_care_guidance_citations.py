"""Focused fail-closed checks for Q-0096 clinical citation filtering."""

from __future__ import annotations

from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from aetherion_server.care.guidance_citations import filter_approved_educational_actions


class CareGuidanceCitationsTests(unittest.TestCase):
    def test_only_verified_approved_educational_actions(self) -> None:
        with TemporaryDirectory() as directory:
            db = Path(directory) / "cliff.sqlite"
            conn = sqlite3.connect(db)
            try:
                conn.execute("CREATE TABLE articles (article_id TEXT, display_title TEXT, source_id TEXT)")
                conn.execute(
                    "INSERT INTO articles VALUES (?, ?, ?)",
                    ("CLIFF-040", "CO2-induced headache", "NASA-CLIFF-040"),
                )
                conn.commit()
            finally:
                conn.close()

            candidates = [
                {"action_id": "ok", "approved": True, "article_id": "CLIFF-040",
                 "label_en": "Read educational reference", "label_vi": "Đọc tài liệu tham khảo"},
                {"action_id": "missing", "approved": True, "article_id": "CLIFF-119"},
                {"action_id": "diagnosis", "approved": True, "diagnostic_claim": True,
                 "article_id": "CLIFF-040"},
                {"action_id": "unapproved", "approved": False, "article_id": "CLIFF-040"},
            ]
            result = filter_approved_educational_actions(candidates, sqlite_path=db)
            self.assertEqual(result["status"], "READY")
            self.assertEqual([a["action_id"] for a in result["approved_actions"]], ["ok"])
            self.assertEqual(result["approved_actions"][0]["source_id"], "NASA-CLIFF-040")
            self.assertEqual(
                {item["action_id"]: item["reason"] for item in result["rejected"]},
                {"missing": "missing_or_unverified_citation",
                 "diagnosis": "diagnostic_or_prescriptive_disallowed",
                 "unapproved": "not_approved"},
            )

    def test_absent_catalog_fails_closed_even_with_caller_citation(self) -> None:
        with TemporaryDirectory() as directory:
            missing = Path(directory) / "missing.sqlite"
            result = filter_approved_educational_actions(
                [{"action_id": "unverified", "approved": True, "article_id": "CLIFF-040",
                  "citation_title": "Caller-provided title", "source_id": "caller"}],
                sqlite_path=missing,
            )
            self.assertEqual(result["status"], "NO_DATA")
            self.assertEqual(result["approved_actions"], [])
            self.assertEqual(result["rejected"][0]["reason"], "missing_or_unverified_citation")
            self.assertFalse(missing.exists())

    def test_incompatible_catalog_fails_closed(self) -> None:
        with TemporaryDirectory() as directory:
            db = Path(directory) / "empty.sqlite"
            conn = sqlite3.connect(db)
            conn.close()
            result = filter_approved_educational_actions(
                [{"action_id": "unverified", "approved": True, "article_id": "CLIFF-040"}],
                sqlite_path=db,
            )
            self.assertEqual(result["status"], "NO_DATA")
            self.assertEqual(result["approved_actions"], [])


if __name__ == "__main__":
    unittest.main()
