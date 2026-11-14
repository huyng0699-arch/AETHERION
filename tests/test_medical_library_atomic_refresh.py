import hashlib
from pathlib import Path
from contextlib import closing
import sqlite3
import tempfile
import unittest
from packages.medical_library.atomic_refresh import install_verified_library


class AtomicRefreshTests(unittest.TestCase):
    def test_backup_and_rejection(self):
        with tempfile.TemporaryDirectory() as folder:
            source, target = Path(folder)/"new.sqlite", Path(folder)/"active.sqlite"
            for path, value in ((source, "new"), (target, "old")):
                with closing(sqlite3.connect(path)) as db:
                    db.execute("PRAGMA user_version=1")
                    db.execute("CREATE TABLE records(value TEXT)")
                    db.execute("INSERT INTO records VALUES (?)", (value,))
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                install_verified_library(source, target, expected_sha256="0"*64, expected_schema_version=1)
            with self.assertRaisesRegex(ValueError, "schema version"):
                install_verified_library(source, target, expected_sha256=digest, expected_schema_version=2)
            with closing(sqlite3.connect(target)) as db:
                self.assertEqual(db.execute("SELECT value FROM records").fetchone()[0], "old")
            self.assertEqual(install_verified_library(source, target, expected_sha256=digest, expected_schema_version=1), digest)
            with closing(sqlite3.connect(target)) as db:
                self.assertEqual(db.execute("SELECT value FROM records").fetchone()[0], "new")
            with closing(sqlite3.connect(target.with_suffix(".sqlite.bak"))) as db:
                self.assertEqual(db.execute("SELECT value FROM records").fetchone()[0], "old")
