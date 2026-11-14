"""Focused tests for Q-0469: anatomy-to-NASA/medical knowledge mapping."""

from __future__ import annotations

import unittest

from knowledge.medical.condition_atlas_mapping import (
    map_anatomical_structure_to_knowledge,
    map_condition_to_atlas,
)


class AnatomyToKnowledgeMappingTests(unittest.TestCase):
    def test_mandible_maps_to_verified_cliff_docs_and_origin_without_diagnosis_claim(self) -> None:
        res = map_anatomical_structure_to_knowledge("mandible_visible_human_male")
        self.assertEqual(res["status"], "READY")
        self.assertEqual(res["anatomical_id"], "mandible_visible_human_male")
        self.assertFalse(res["diagnostic_claim"])
        self.assertTrue(res["educational_reference_only"])
        self.assertIsNotNone(res["origin"])
        self.assertEqual(res["origin"]["license"], "CC BY 4.0")
        self.assertEqual(res["origin"]["rights_status"], "APPROVED")

        doc_ids = {d["article_id"] for d in res["linked_documents"]}
        self.assertEqual(doc_ids, {"CLIFF-020", "CLIFF-022", "CLIFF-023", "CLIFF-038"})
        self.assertTrue(doc_ids.isdisjoint({"CLIFF-019", "CLIFF-021", "CLIFF-119"}))

    def test_unknown_anatomical_id_returns_no_data_without_fabrication(self) -> None:
        res = map_anatomical_structure_to_knowledge("unknown_structure_xyz")
        self.assertEqual(res["status"], "NO_DATA")
        self.assertEqual(res["linked_documents"], [])
        self.assertFalse(res["diagnostic_claim"])

    def test_existing_condition_to_atlas_preserved(self) -> None:
        res = map_condition_to_atlas({"condition_id": "sans", "body_systems": ["neuro-ocular"]})
        self.assertEqual(res["status"], "READY")
        self.assertEqual(res["primary_organ"]["organ_id"], "eye_optic_nerve")


if __name__ == "__main__":
    unittest.main()
