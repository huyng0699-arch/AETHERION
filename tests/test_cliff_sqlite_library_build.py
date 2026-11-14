from __future__ import annotations

from pathlib import Path
import sqlite3
import unittest

from knowledge.nasa.cliff_119_2023 import library_schema

REPO_ROOT = Path(__file__).resolve().parents[1]
SQLITE_PATH = REPO_ROOT / "knowledge" / "nasa" / "cliff_119_2023" / "AETHERION_NASA_CLIFF_119.sqlite"


class CliffSqliteLibraryBuildTests(unittest.TestCase):
    def test_offline_sqlite_library_contains_full_articles_and_media_blobs(self) -> None:
        self.assertTrue(SQLITE_PATH.is_file(), f"Missing offline SQLite library at {SQLITE_PATH}")
        conn = sqlite3.connect(f"file:{SQLITE_PATH}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        try:
            audit = library_schema.audit(conn, verify_media=True)
            self.assertEqual(audit["integrity"], "ok")
            self.assertEqual(audit["foreign_key_errors"], 0)
            self.assertGreaterEqual(audit["articles"], 116)
            self.assertGreaterEqual(audit["complete_articles"], 116)
            self.assertGreaterEqual(audit["media_assets"], 360)
            self.assertEqual(audit["media_hash_mismatches"], [])

            sections_count = conn.execute("SELECT COUNT(*) FROM article_sections").fetchone()[0]
            tables_count = conn.execute("SELECT COUNT(*) FROM article_tables").fetchone()[0]
            refs_count = conn.execute("SELECT COUNT(*) FROM source_references").fetchone()[0]
            self.assertGreater(sections_count, 1000)
            self.assertGreater(tables_count, 500)
            self.assertGreater(refs_count, 500)

            row = conn.execute(
                "SELECT display_title, category FROM articles WHERE article_id = ?",
                ("CLIFF-061",),
            ).fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row["display_title"], "Seizures")

            media_row = conn.execute(
                "SELECT length(data) AS nbytes, mime_type, license_identifier FROM media WHERE article_id = ? LIMIT 1",
                ("CLIFF-077",),
            ).fetchone()
            self.assertIsNotNone(media_row)
            self.assertGreater(media_row["nbytes"], 0)
            self.assertTrue(media_row["license_identifier"])
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
