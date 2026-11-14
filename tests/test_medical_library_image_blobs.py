import hashlib
import sqlite3
import unittest
from packages.medical_library.image_blobs import install, read_offline, set_thumbnail


class OfflineImageTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.execute("""CREATE TABLE media(media_id TEXT PRIMARY KEY,data BLOB,mime_type TEXT,
            sha256 TEXT,caption TEXT,alt_text TEXT,attribution TEXT,license_identifier TEXT,
            source_url TEXT,usage_review TEXT)""")
        self.raw = b"engineering-fixture-not-medical-image"
        self.sha = hashlib.sha256(self.raw).hexdigest()
        self.db.execute("INSERT INTO media VALUES (?,?,?,?,?,?,?,?,?,?)", (
            "test", self.raw, "image/png", self.sha, "Engineering fixture",
            "Fixture", "Fixture author", "CC0-1.0", "https://example.org/fixture", "APPROVED"))
        install(self.db)
        install(self.db)

    def tearDown(self):
        self.db.close()

    def test_roundtrip(self):
        set_thumbnail(self.db, "test", data=b"thumbnail", mime_type="image/png",
                      width=10, height=10, original_sha256=self.sha)
        image = read_offline(self.db, "test")
        self.assertEqual(image.thumbnail, b"thumbnail")
        self.assertEqual(image.original, self.raw)

    def test_reject_bad_source_hash(self):
        with self.assertRaises(ValueError):
            set_thumbnail(self.db, "test", data=b"t", mime_type="image/png",
                          width=1, height=1, original_sha256="0" * 64)

    def test_reject_corrupt_thumbnail(self):
        set_thumbnail(self.db, "test", data=b"t", mime_type="image/png",
                      width=1, height=1, original_sha256=self.sha)
        self.db.execute("UPDATE media SET thumbnail_data=? WHERE media_id=?", (b"altered", "test"))
        with self.assertRaises(ValueError):
            read_offline(self.db, "test")

    def test_reject_unapproved(self):
        self.db.execute("UPDATE media SET usage_review='RESTRICTED'")
        with self.assertRaises(ValueError):
            read_offline(self.db, "test")


if __name__ == "__main__":
    unittest.main()
