"""Q-0425: real read-only SQLite catalog tests; fixture is synthetic engineering data."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sqlite3
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / 'apps/desktop/src/aetherion_desktop/medical_library.py'

# Load without importing PySide6: actual Windows Qt execution is a separate gate.
spec = importlib.util.spec_from_file_location('aetherion_medical_catalog', MODULE)
module = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'library.sqlite'
        self.catalog = module.OfflineMedicalCatalog(self.path)

    def _make_database(self):
        with sqlite3.connect(self.path) as db:
            db.executescript('''
            CREATE TABLE library_info (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE sources (source_id TEXT PRIMARY KEY, verification_state TEXT, source_url TEXT);
            CREATE TABLE articles (article_id TEXT PRIMARY KEY, slot INTEGER, display_title TEXT,
                                   category TEXT, completeness_state TEXT, source_id TEXT);
            INSERT INTO library_info VALUES ('library_kind', 'NASA_CLIFF_119_MEDICAL_REFERENCE');
            INSERT INTO sources VALUES ('fixture','UNVERIFIED','https://example.org/fixture');
            INSERT INTO articles VALUES ('a',1,'SYNTHETIC abdominal example','TEST','UNVERIFIED','fixture');
            INSERT INTO articles VALUES ('b',2,'SYNTHETIC dental example','TEST','PARTIAL','fixture');
            ''')

    def test_missing_db_never_created(self):
        snap = self.catalog.list_articles()
        self.assertEqual(snap.state, 'MISSING')
        self.assertEqual(snap.total, 0)
        self.assertFalse(self.path.exists())

    def test_empty_db_honestly_reports_zero(self):
        self._make_database()
        with sqlite3.connect(self.path) as db:
            db.execute('DELETE FROM articles')
        snap = self.catalog.list_articles()
        self.assertEqual((snap.state, snap.total, len(snap.articles)), ('EMPTY', 0, 0))

    def test_readonly_list_filter_and_unverified_flags(self):
        self._make_database()
        snap = self.catalog.list_articles()
        self.assertEqual((snap.state, snap.total, len(snap.articles)), ('READY', 2, 2))
        self.assertTrue(all(a.source_state == 'UNVERIFIED' for a in snap.articles))
        self.assertEqual([a.slot for a in snap.articles], [1, 2])
        selected = self.catalog.list_articles('DENTAL')
        self.assertEqual((selected.total, len(selected.articles)), (2, 1))
        self.assertEqual(selected.articles[0].title, 'SYNTHETIC dental example')
        # Search strings are never interpolated into SQL.
        self.assertEqual(len(self.catalog.list_articles("%' OR 1=1 --").articles), 0)

    def test_reject_unrelated_sqlite_database(self):
        with sqlite3.connect(self.path) as db:
            db.execute('CREATE TABLE unrelated (id INTEGER)')
        snap = self.catalog.list_articles()
        self.assertEqual((snap.state, snap.total), ('ERROR', 0))

    def test_reject_wrong_library_identity(self):
        self._make_database()
        with sqlite3.connect(self.path) as db:
            db.execute("UPDATE library_info SET value='OTHER' WHERE key='library_kind'")
        self.assertEqual(self.catalog.list_articles().state, 'ERROR')

    def test_reject_non_sqlite_file(self):
        self.path.write_bytes(b'this is NOT a valid SQLite file')
        self.assertEqual(self.catalog.list_articles().state, 'ERROR')

    def test_does_not_write_to_library(self):
        self._make_database()
        before = self.path.read_bytes()
        self.catalog.list_articles('abc')
        self.catalog.list_articles('')
        self.assertEqual(self.path.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
