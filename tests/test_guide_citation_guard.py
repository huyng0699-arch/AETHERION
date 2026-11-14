import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER_SRC = ROOT / "apps" / "server" / "src"
if str(SERVER_SRC) not in sys.path:
    sys.path.insert(0, str(SERVER_SRC))

from aetherion_server.guide.citation_guard import filter_approved_citations


class GuideCitationGuardTests(unittest.TestCase):
    def test_approved_and_invented_citations_are_separated(self) -> None:
        res = filter_approved_citations(
            ["OSD-575", "nasa-cliff-119-status-json", "FAKE-MEDICAL-PAPER-2026"],
            repo_root=ROOT,
        )
        self.assertEqual([a["citation_id"] for a in res["approved"]], ["OSD-575"])
        self.assertEqual(
            [r["citation_id"] for r in res["rejected"]],
            ["nasa-cliff-119-status-json", "FAKE-MEDICAL-PAPER-2026"],
        )
        self.assertTrue(res["uncertainty_marked"])

    def test_all_approved_citations_clear_uncertainty_flag(self) -> None:
        res = filter_approved_citations(["OSD-575", "space_radiation"], repo_root=ROOT)
        self.assertEqual(len(res["approved"]), 2)
        self.assertEqual(res["rejected"], [])
        self.assertFalse(res["uncertainty_marked"])


if __name__ == "__main__":
    unittest.main()
