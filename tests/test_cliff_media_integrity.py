from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import unittest

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
RECORDS_DIR = REPO_ROOT / "knowledge" / "nasa" / "cliff_119_2023" / "records"


class CliffMediaIntegrityTests(unittest.TestCase):
    def test_all_media_assets_have_valid_sha_license_and_decodable_binary(self) -> None:
        checked = 0
        for rec_path in sorted(RECORDS_DIR.glob("CLIFF-*.json")):
            data = json.loads(rec_path.read_text(encoding="utf-8"))
            for item in data.get("media", []):
                checked += 1
                file_path = REPO_ROOT / item["file_path"]
                self.assertTrue(file_path.is_file(), f"Missing media file {file_path}")
                raw = file_path.read_bytes()
                self.assertGreater(len(raw), 0, f"Empty media file {file_path}")
                actual_sha = hashlib.sha256(raw).hexdigest()
                self.assertEqual(item.get("sha256"), actual_sha, f"SHA mismatch in {rec_path.name}: {file_path.name}")

                lic = str(item.get("license_identifier", "")).strip()
                self.assertTrue(lic, f"Missing license_identifier in {rec_path.name}")
                self.assertFalse(lic.startswith("http"), f"License must not be a raw URL in {rec_path.name}: {lic}")
                self.assertTrue(str(item.get("creator", "")).strip(), f"Missing creator in {rec_path.name}")
                self.assertTrue(str(item.get("attribution", "")).strip(), f"Missing attribution in {rec_path.name}")
                self.assertTrue(str(item.get("source_url", "")).startswith("http"), f"Invalid source_url in {rec_path.name}")

                mime = item.get("mime_type", "")
                if mime == "image/jpeg":
                    self.assertTrue(raw.startswith(b"\xff\xd8"), f"Missing JPEG SOI in {file_path}")
                    self.assertIn(b"\xff\xd9", raw, f"Missing JPEG EOI in {file_path}")
                if mime != "image/svg+xml":
                    im = Image.open(io.BytesIO(raw))
                    im.load()
        self.assertGreaterEqual(checked, 360)


if __name__ == "__main__":
    unittest.main()
