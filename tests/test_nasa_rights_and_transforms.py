from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RIGHTS_JSON = ROOT / "knowledge" / "nasa" / "dataset_rights_and_transforms.json"
RIGHTS_MD = ROOT / "knowledge" / "nasa" / "dataset_rights_and_transforms.md"
OSDR_JSON = ROOT / "knowledge" / "nasa" / "osdr_datasets.json"


class TestNasaRightsAndTransforms(unittest.TestCase):
    def test_all_selected_osdr_datasets_have_rights_and_versions(self) -> None:
        rights = json.loads(RIGHTS_JSON.read_text(encoding="utf-8"))
        osdr = json.loads(OSDR_JSON.read_text(encoding="utf-8"))

        rights_by_id = {d["dataset_id"]: d for d in rights["datasets"]}
        self.assertFalse(rights["policy_summary"]["third_party_nasa_relicensed"])

        for ds in osdr["datasets"]:
            osd_id = ds["osd_id"]
            self.assertIn(osd_id, rights_by_id, f"{osd_id} missing from rights registry")
            entry = rights_by_id[osd_id]
            self.assertEqual(entry["version"], ds["version"])
            self.assertFalse(entry["relicensed_under_apache_2_0"])
            self.assertTrue(entry["allowed_reuse"])
            self.assertTrue(entry["prohibited_reuse"])
            self.assertTrue(entry["exact_transformation"]["transform_id"])

    def test_markdown_sha256_and_cliff_entry(self) -> None:
        rights = json.loads(RIGHTS_JSON.read_text(encoding="utf-8"))
        rights_by_id = {d["dataset_id"]: d for d in rights["datasets"]}
        self.assertIn("NASA-IMM-CLIFF-119", rights_by_id)
        self.assertFalse(rights_by_id["NASA-IMM-CLIFF-119"]["relicensed_under_apache_2_0"])

        md_text = RIGHTS_MD.read_text(encoding="utf-8")
        digest = hashlib.sha256(RIGHTS_JSON.read_bytes()).hexdigest()
        self.assertIn(digest, md_text)


if __name__ == "__main__":
    unittest.main()
