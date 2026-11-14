"""Focused test for Q-0460: per-session structured history without default persistence."""

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


class InterviewSessionHistoryTests(unittest.TestCase):
    def test_ephemeral_session_history_tracks_unknowns_without_storing(self):
        with tempfile.TemporaryDirectory() as tmp:
            app = create_app(db_path=Path(tmp) / "hist.sqlite3")
            with TestClient(app) as client:
                sym = client.get("/api/v1/knowledge/symptoms", params={"query": "kho tho", "limit": 1}).json()["items"][0]["name"]
                resp = client.post(
                    "/api/v1/knowledge/interview/next",
                    json={
                        "symptoms": [sym],
                        "answers": {
                            "breathing_at_rest": "UNKNOWN",
                            "present_now": "YES",
                        },
                    },
                )
                self.assertEqual(resp.status_code, 200)
                body = resp.json()
                self.assertFalse(body["stored_by_server"])
                self.assertTrue(body["persistence_requires_consent"])
                self.assertEqual(body["unknown_answers_count"], 1)
                self.assertEqual(len(body["session_history"]), 2)
                by_qid = {item["question_id"]: item for item in body["session_history"]}
                self.assertTrue(by_qid["breathing_at_rest"]["is_unknown"])
                self.assertTrue(by_qid["breathing_at_rest"]["is_critical"])
                self.assertFalse(by_qid["present_now"]["is_unknown"])


if __name__ == "__main__":
    unittest.main()
