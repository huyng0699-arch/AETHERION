"""Focused unit tests for Q-0096: source-linked non-diagnostic educational guidance."""

from __future__ import annotations

import unittest

from aetherion_server.care.guidance_citations import filter_approved_educational_actions


class CareGuidanceCitationsTests(unittest.TestCase):
    def test_only_approved_verified_cliff_educational_actions_appear(self) -> None:
        candidates = [
            {
                "action_id": "act-ok",
                "approved": True,
                "article_id": "CLIFF-040",
                "label_en": "Review CO2-induced headache reference",
                "label_vi": "Xem tài liệu tham khảo đau đầu do CO2",
            },
            {
                "action_id": "act-missing-slot",
                "approved": True,
                "article_id": "CLIFF-019",
                "label_en": "Unverified missing slot",
            },
            {
                "action_id": "act-diag",
                "approved": True,
                "diagnostic_claim": True,
                "article_id": "CLIFF-040",
                "label_en": "Diagnose CO2 toxicity",
            },
            {
                "action_id": "act-unapproved",
                "approved": False,
                "article_id": "CLIFF-040",
                "label_en": "Unapproved action",
            },
        ]

        res = filter_approved_educational_actions(candidates)
        self.assertEqual(res["status"], "READY")
        self.assertEqual([a["action_id"] for a in res["approved_actions"]], ["act-ok"])
        self.assertTrue(res["approved_actions"][0]["educational_only"])
        self.assertFalse(res["approved_actions"][0]["diagnostic_claim"])
        self.assertIn("CO2", res["approved_actions"][0]["citation_title"])
        self.assertEqual(
            {r["action_id"]: r["reason"] for r in res["rejected"]},
            {
                "act-missing-slot": "missing_or_unverified_citation",
                "act-diag": "diagnostic_or_prescriptive_disallowed",
                "act-unapproved": "not_approved",
            },
        )


if __name__ == "__main__":
    unittest.main()
