import hashlib
import json
import struct
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANATOMY_DIR = ROOT / "knowledge" / "anatomy"
APPROVED_PATH = ANATOMY_DIR / "approved_models.json"


class TestQ0466AnatomyMeshes(unittest.TestCase):
    def test_approved_models_rights_hashes_and_binary_stl(self):
        data = json.loads(APPROVED_PATH.read_text(encoding="utf-8"))
        models = data["models"]
        self.assertGreaterEqual(len(models), 7)
        required = data["required_fields"]

        seen_ids = set()
        for entry in models:
            for field in required:
                self.assertTrue(entry.get(field), f"Missing {field} in {entry}")
            aid = entry["anatomical_id"]
            self.assertNotIn(aid, seen_ids)
            seen_ids.add(aid)

            self.assertEqual(entry["rights_status"], "APPROVED")
            self.assertNotIn("nc", entry["license"].lower())
            self.assertNotIn("nc", entry["derivative_license"].lower())
            self.assertEqual(entry["purpose"], "EDUCATIONAL_VISUALIZATION_ONLY_NOT_FOR_DIAGNOSIS")

            stl_path = ANATOMY_DIR / entry["filename"]
            self.assertTrue(stl_path.is_file(), f"Missing STL {stl_path}")
            raw = stl_path.read_bytes()
            self.assertEqual(len(raw), entry["size_bytes"])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), entry["sha256"])

            tri_count = struct.unpack("<I", raw[80:84])[0]
            self.assertGreater(tri_count, 0)
            self.assertEqual(84 + tri_count * 50, len(raw))


if __name__ == "__main__":
    unittest.main()
