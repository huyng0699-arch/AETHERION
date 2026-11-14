from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER_SRC = REPO_ROOT / "apps" / "server" / "src"
if str(SERVER_SRC) not in sys.path:
    sys.path.insert(0, str(SERVER_SRC))

from aetherion_server.main import create_app


class SymptomInterviewDeterministicTests(unittest.TestCase):
    def test_deterministic_stateful_questioning_and_red_flag_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            app = create_app(db_path=Path(tmp) / "interview.sqlite3")
            with TestClient(app) as client:
                # 1. Start with a recognized symptom (breathing/neuro route or general label)
                sym_resp = client.get("/api/v1/knowledge/symptoms", params={"query": "kho tho", "limit": 5})
                self.assertEqual(sym_resp.status_code, 200)
                sym_items = sym_resp.json()["items"]
                self.assertGreaterEqual(len(sym_items), 1)
                chosen_symptom = sym_items[0]["name"]

                # 2. First deterministic step with no answers -> critical question prioritized
                step1 = client.post(
                    "/api/v1/knowledge/interview/next",
                    json={"symptoms": [chosen_symptom], "answers": {}, "use_ai": False},
                )
                self.assertEqual(step1.status_code, 200)
                d1 = step1.json()
                self.assertEqual(d1["state"], "MORE_INFORMATION_REQUIRED")
                self.assertEqual(d1["model_status"], "NOT_REQUESTED")
                self.assertFalse(d1["clinical_validation"])
                self.assertFalse(d1["stored_by_server"])
                self.assertIsNotNone(d1["next_question"])
                self.assertIn("UNKNOWN", d1["next_question"]["answers"])

                # 3. Answer UNKNOWN to first question, verify progression through onset/duration/history
                q1_id = d1["next_question"]["id"]
                step2 = client.post(
                    "/api/v1/knowledge/interview/next",
                    json={"symptoms": [chosen_symptom], "answers": {q1_id: "UNKNOWN"}, "use_ai": False},
                )
                self.assertEqual(step2.status_code, 200)
                d2 = step2.json()
                self.assertEqual(d2["answered"], 1)
                self.assertNotEqual(d2["next_question"]["id"], q1_id)

                # 4. Explicit witnessed red flag -> WITNESSED_RED_FLAG_REPORTED
                step_red = client.post(
                    "/api/v1/knowledge/interview/next",
                    json={
                        "symptoms": [chosen_symptom],
                        "answers": {"breathing_at_rest": "YES", "onset": "SUDDEN", "duration": "MINUTES"},
                        "use_ai": False,
                    },
                )
                self.assertEqual(step_red.status_code, 200)
                d_red = step_red.json()
                self.assertEqual(d_red["state"], "WITNESSED_RED_FLAG_REPORTED")
                self.assertIn("breathing_at_rest", d_red["red_flags_reported"])
                self.assertFalse(d_red["clinical_validation"])


if __name__ == "__main__":
    unittest.main()
