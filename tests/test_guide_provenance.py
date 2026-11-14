import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER_SRC = ROOT / "apps" / "server" / "src"
if str(SERVER_SRC) not in sys.path:
    sys.path.insert(0, str(SERVER_SRC))

from aetherion_server.guide.provenance import explain_observation_provenance


class GuideProvenanceTests(unittest.TestCase):
    def test_missing_observation_reports_no_data(self) -> None:
        res = explain_observation_provenance(None, repo_root=ROOT)
        self.assertEqual(res["verification_state"], "NO_DATA")
        self.assertIn("Missing data does not indicate healthy status", res["explanation"])

    def test_verified_nasa_source_is_marked_non_live_research(self) -> None:
        obs = {
            "metric": "cytokine_il6",
            "value": 1.24,
            "unit": "pg/mL",
            "observed_at": "2021-09-19T12:00:00Z",
            "source_id": "nasa-osdr-datasets-json",
            "verification_state": "READY",
            "is_live_telemetry": True,  # must be overridden by registry truth
        }
        res = explain_observation_provenance(obs, repo_root=ROOT)
        self.assertEqual(res["verification_state"], "READY")
        self.assertFalse(res["is_live_telemetry"])
        self.assertIn("cytokine_il6=1.24 pg/mL", res["explanation"])
        self.assertIn("2021-09-19T12:00:00Z", res["explanation"])
        self.assertIn("NASA Open Science Data Repository", res["explanation"])

    def test_stale_and_unverified_states_are_distinguished(self) -> None:
        stale = explain_observation_provenance(
            {
                "metric": "heart_rate",
                "value": 72,
                "unit": "bpm",
                "observed_at": "2026-11-10T00:00:00Z",
                "source_id": "manual-checkin",
                "verification_state": "STALE",
            },
            repo_root=ROOT,
        )
        self.assertEqual(stale["verification_state"], "STALE")
        self.assertIn("STALE:", stale["explanation"])

        unverified = explain_observation_provenance(
            {"metric": "spo2", "value": 98, "unit": "%", "verification_state": "READY"},
            repo_root=ROOT,
        )
        self.assertEqual(unverified["verification_state"], "UNVERIFIED")


if __name__ == "__main__":
    unittest.main()
