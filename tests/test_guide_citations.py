import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER_SRC = ROOT / "apps" / "server" / "src"
if str(SERVER_SRC) not in sys.path:
    sys.path.insert(0, str(SERVER_SRC))

from aetherion_server.guide.citations import resolve_citation


class GuideCitationsTests(unittest.TestCase):
    def test_accessible_osdr_and_hazard_citations_resolve(self) -> None:
        osdr = resolve_citation("OSD-575", repo_root=ROOT)
        self.assertEqual(osdr["status"], "ACCESSIBLE")
        self.assertEqual(osdr["route"], "encyclopedia/entry/OSD-575")
        self.assertFalse(osdr["entry"]["is_live_telemetry"])

        hazard = resolve_citation("space_radiation", repo_root=ROOT)
        self.assertEqual(hazard["status"], "ACCESSIBLE")
        self.assertEqual(hazard["route"], "encyclopedia/entry/space_radiation")

    def test_unimported_cliff_citation_is_honestly_unavailable(self) -> None:
        cliff = resolve_citation("cliff-001", repo_root=ROOT)
        self.assertEqual(cliff["status"], "UNAVAILABLE_UNIMPORTED")
        self.assertIsNone(cliff["route"])
        self.assertIn("0/119", cliff["reason"])

    def test_unknown_citation_returns_not_found(self) -> None:
        missing = resolve_citation("nonexistent-citation-id", repo_root=ROOT)
        self.assertEqual(missing["status"], "NOT_FOUND")
        self.assertIsNone(missing["route"])


if __name__ == "__main__":
    unittest.main()
