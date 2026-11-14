import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER_SRC = ROOT / "apps" / "server" / "src"
if str(SERVER_SRC) not in sys.path:
    sys.path.insert(0, str(SERVER_SRC))

from aetherion_server.guide import load_guide_entries, search_guide


class GuideSearchTests(unittest.TestCase):
    def test_open_guide_without_symptom_or_ai_returns_sourced_entries(self) -> None:
        resp = search_guide("", repo_root=ROOT, ai_enabled=False)
        self.assertFalse(resp["requires_ai"])
        self.assertFalse(resp["requires_symptom"])
        self.assertFalse(resp["ai_used"])
        self.assertGreater(resp["count"], 0)
        self.assertEqual(resp["count"], resp["total_available"])
        for item in resp["results"]:
            self.assertTrue(item["source_url"].startswith("https://"))
            self.assertFalse(item["is_live_telemetry"])

    def test_keyword_search_matches_osdr_and_cliff_audit(self) -> None:
        osdr = search_guide("OSD-575", repo_root=ROOT, ai_enabled=False)
        self.assertGreaterEqual(osdr["count"], 1)
        self.assertTrue(any(r["entry_id"] == "OSD-575" for r in osdr["results"]))

        cliff = search_guide("CliFF 119", repo_root=ROOT, ai_enabled=False)
        self.assertGreaterEqual(cliff["count"], 1)

    def test_unknown_query_returns_empty_without_hallucination(self) -> None:
        empty = search_guide("xyznonexistentterm999", repo_root=ROOT, ai_enabled=False)
        self.assertEqual(empty["count"], 0)
        self.assertEqual(empty["results"], [])
        self.assertGreater(len(load_guide_entries(repo_root=ROOT)), 0)


if __name__ == "__main__":
    unittest.main()
