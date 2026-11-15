"""Focused offline search & 119-article FTS5 benchmark tests (Q-0428).

Uses synthetic engineering fixtures inside temporary directories only; never
claims NASA approval or clinical validity.
"""
from __future__ import annotations

from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import time
import unittest

from knowledge.nasa.cliff_119_2023 import library_schema
from packages.medical_library.offline_search import (
    categories,
    search,
    search_detailed,
    search_status,
)


def _populate_synthetic_db(db_path: Path, count: int = 119) -> None:
    library_schema.create_file(db_path)
    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute("PRAGMA foreign_keys=ON")
        with conn:
            for idx in range(1, count + 1):
                article_id = f"CLIFF-{idx:03d}"
                source_id = f"src-{idx:03d}"
                category = "Cardiovascular" if idx % 2 == 0 else "Neurology"
                title = (
                    f"Hypovolemic Shock Syndrome {idx}"
                    if idx == 16
                    else f"Synthetic Condition {idx}"
                )
                body = (
                    "Acute intravascular volume depletion with tachycardia and hypotension."
                    if idx == 16
                    else f"Structured engineering placeholder text for slot {idx} ischemia monitoring."
                )
                conn.execute(
                    """
                    INSERT INTO sources (
                        source_id, publisher, title, source_url, content_sha256,
                        original_bytes, license_identifier, attribution,
                        verification_state, retrieved_at_utc
                    ) VALUES (?, 'NASA', ?, ?, ?, 1024, 'US_GOV_PUBLIC_DOMAIN', 'NASA TEST', 'VERIFIED', '2026-11-14T00:00:00+00:00')
                    """,
                    (source_id, title, f"https://www.nasa.gov/test/{idx}.pdf", f"{idx:064x}"),
                )
                state = "PARTIAL" if idx == 119 and count == 119 else "COMPLETE"
                conn.execute(
                    """
                    INSERT INTO articles (
                        article_id, slot, display_title, category, source_id,
                        completeness_state, created_utc, updated_utc
                    ) VALUES (?, ?, ?, ?, ?, ?, '2026-11-14T00:00:00Z', '2026-11-14T00:00:00Z')
                    """,
                    (article_id, idx, title, category, source_id, state),
                )
                conn.execute(
                    """
                    INSERT INTO article_sections (
                        section_id, article_id, ordinal, heading, text_content, page_start
                    ) VALUES (?, ?, 0, 'Summary', ?, 1)
                    """,
                    (f"sec-{idx}", article_id, body),
                )
                conn.execute(
                    """
                    INSERT INTO article_search (article_id, display_title, content)
                    VALUES (?, ?, ?)
                    """,
                    (article_id, title, body),
                )


class OfflineSearchTests(unittest.TestCase):
    def test_fts5_search_category_filter_safety_and_119_benchmark(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "cliff_fts5.sqlite"
            _populate_synthetic_db(db, count=119)

            status = search_status(db)
            self.assertEqual(status["articles"], 119)
            self.assertEqual(status["complete_articles"], 118)
            self.assertTrue(status["fts5_available"])
            self.assertFalse(status["library_complete"])

            self.assertEqual(categories(db), ["Cardiovascular", "Neurology"])

            t0 = time.perf_counter()
            hits, backend = search_detailed(db, "tachycardia hypotension")
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            self.assertEqual(backend, "fts5")
            self.assertEqual([h.article_id for h in hits], ["CLIFF-016"])
            self.assertLess(elapsed_ms, 100.0, f"119-article FTS5 search too slow: {elapsed_ms:.2f}ms")

            # Special FTS5 syntax characters are safely neutralized instead of throwing OperationalError.
            self.assertEqual(search(db, 'tachycardia OR "unclosed'), [])
            self.assertEqual(search(db, "%_\\"), [])

            # Complete filter excludes incomplete CLIFF-119 unless complete_only=False.
            self.assertEqual(search(db, "Condition 119"), [])
            self.assertEqual(
                [h.article_id for h in search(db, "Condition 119", complete_only=False)],
                ["CLIFF-119"],
            )

            # Mid-word substring gracefully uses deterministic LIKE fallback.
            sub_hits, sub_backend = search_detailed(db, "chemia", limit=5)
            self.assertEqual(sub_backend, "like")
            self.assertEqual(len(sub_hits), 5)

    def test_deterministic_like_fallback_when_fts5_table_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "cliff_no_fts.sqlite"
            _populate_synthetic_db(db, count=10)
            with closing(sqlite3.connect(db)) as conn:
                with conn:
                    conn.execute("DROP TABLE article_search")

            status = search_status(db)
            self.assertFalse(status["fts5_available"])
            hits, backend = search_detailed(db, "Synthetic", category="Neurology")
            self.assertEqual(backend, "like")
            self.assertEqual(len(hits), 5)
            self.assertTrue(all(h.category == "Neurology" for h in hits))

            with self.assertRaises(ValueError):
                search(db, "x" * 257)
            with self.assertRaises(ValueError):
                search(db, "ok", limit=0)


if __name__ == "__main__":
    unittest.main()
