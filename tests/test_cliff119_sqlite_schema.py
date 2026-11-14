"""Q-0420: real SQLite schema tests; synthetic fixture is explicitly not NASA data."""
from contextlib import closing
import hashlib
import importlib.util
import sqlite3
import tempfile
import unittest
from pathlib import Path

SCHEMA = Path(__file__).resolve().parents[1] / "knowledge/nasa/cliff_119_2023/library_schema.py"
spec = importlib.util.spec_from_file_location("cliff119_library_schema", SCHEMA)
lib = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lib)

class TestCliFFSQLiteSchema(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / lib.DEFAULT_LIBRARY_NAME
        self.db = lib.connect(self.path)
        self.addCleanup(self.db.close)
        lib.initialize(self.db)

    def _fixture(self):
        # Synthetic engineering fixture, NOT copied NASA medical content.
        self.db.execute("""INSERT INTO sources(source_id,publisher,title,source_url,license_identifier,attribution)
                           VALUES ('test-source','SYNTHETIC','TEST ONLY','https://example.org/test','TEST_ONLY','TEST ONLY')""")
        self.db.execute("""INSERT INTO articles(article_id,slot,display_title,category,source_id,created_utc,updated_utc)
                           VALUES ('test-article',1,'SYNTHETIC','TEST','test-source','2026-11-14T00:00:00Z','2026-11-14T00:00:00Z')""")
        self.db.commit()

    def test_empty_database_is_not_complete(self):
        result = lib.audit(self.db)
        self.assertEqual(result["schema_version"], 1)
        self.assertEqual(result["articles"], 0)
        self.assertFalse(result["library_complete"])
        self.assertEqual(result["integrity"], "ok")

    def test_migration_is_idempotent(self):
        lib.initialize(self.db)
        self.assertEqual(lib.audit(self.db)["schema_version"], 1)

    def test_foreign_keys_reject_nonexistent_source(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("""INSERT INTO articles(article_id,slot,display_title,category,source_id,created_utc,updated_utc)
                               VALUES ('bad',1,'BAD','TEST','missing','a','b')""")

    def test_media_blob_roundtrip_hash_and_readonly(self):
        self._fixture()
        blob = b"\x89PNG\r\n\x1a\nSYNTHETIC-TEST-NOT-MEDICAL"
        digest = hashlib.sha256(blob).hexdigest()
        self.db.execute("""INSERT INTO media(media_id,article_id,ordinal,media_kind,data,mime_type,width,height,
                           sha256,creator,license_identifier,source_url,attribution,caption,alt_text,usage_review)
                           VALUES ('test-image','test-article',0,'OTHER',?,'image/png',16,16,?,
                           'SYNTHETIC','TEST_ONLY','https://example.org/test','TEST ONLY','TEST','TEST','PENDING')""",(blob,digest))
        self.db.commit()
        audit = lib.audit(self.db)
        self.assertEqual(audit["media_assets"],1)
        self.assertFalse(audit["library_complete"])
        self.assertEqual(audit["media_hash_mismatches"],[])
        with closing(lib.connect(self.path, read_only=True)) as readonly:
            self.assertEqual(readonly.execute("SELECT data FROM media").fetchone()[0],blob)
            with self.assertRaises(sqlite3.OperationalError):
                readonly.execute("DELETE FROM articles")

    def test_corrupted_blob_is_detected(self):
        self._fixture()
        blob = b"SYNTHETIC-IMAGE-TEST"
        self.db.execute("""INSERT INTO media(media_id,article_id,ordinal,media_kind,data,mime_type,
                       sha256,creator,license_identifier,source_url,attribution,caption,alt_text)
                       VALUES ('m','test-article',1,'OTHER',?,'image/png',?,
                       'TEST','TEST','https://example.org','TEST','TEST','TEST')""",
                       (blob,"0"*64))
        self.db.commit()
        self.assertEqual(lib.audit(self.db)["media_hash_mismatches"],["m"])

if __name__ == "__main__":
    unittest.main()
