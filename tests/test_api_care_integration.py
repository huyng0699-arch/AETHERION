"""Focused auth/consent/negative-path checks for the canonical Care API.

Not a clinical validation study and not a substitute for native Windows review.
"""
from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient

from aetherion_server.bootstrap import ensure_bootstrap_user
from aetherion_server.main import create_app
from aetherion_server.symptom_interview import next_question


class CareJournalIntegration(unittest.TestCase):
    def test_authorized_consent_and_gather_evaluate_act_recheck(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "care.sqlite3"
            ensure_bootstrap_user(
                database, username="operator", password="operator-test-password",
                role="operator", allowed_subjects=["*"])
            ensure_bootstrap_user(
                database, username="crew_one", password="crew-one-test-password",
                role="crew", allowed_subjects=["SUB-1"])
            ensure_bootstrap_user(
                database, username="crew_two", password="crew-two-test-password",
                role="crew", allowed_subjects=["SUB-2"])
            with TestClient(create_app(db_path=database)) as client:
                def auth(user, password):
                    result = client.post(
                        "/api/v1/auth/login",
                        json={"username": user, "password": password})
                    self.assertEqual(result.status_code, 200)
                    return {"Authorization": "Bearer " + result.json()["access_token"]}

                ops = auth("operator", "operator-test-password")
                crew1 = auth("crew_one", "crew-one-test-password")
                crew2 = auth("crew_two", "crew-two-test-password")
                for subject in ("SUB-1", "SUB-2"):
                    created = client.post(
                        "/api/v1/subjects", headers=ops,
                        json={"subject_id": subject, "display_name": subject})
                    self.assertEqual(created.status_code, 201)

                body = {
                    "subject_id": "SUB-1",
                    "chief_concern": "Đau đầu tự khai",
                    "symptom_terms": ["đau đầu"],
                    "interview_answers": {"present_now": "YES"},
                }
                url = "/api/v1/care/episodes"
                self.assertEqual(client.post(url, json={**body, "explicit_consent": True}).status_code, 401)
                self.assertEqual(client.post(url, headers=crew1, json=body).status_code, 422)
                created = client.post(
                    url, headers=crew1, json={**body, "explicit_consent": True})
                self.assertEqual(created.status_code, 201, created.text)
                episode = created.json()["episode"]
                ident = episode["episode_id"]
                self.assertEqual(episode["subject_id"], "SUB-1")
                self.assertEqual(episode["current_phase"], "GATHER")
                self.assertEqual(episode["events"][0]["data_state"], "UNVERIFIED")
                self.assertEqual(created.json()["clinical_assessment"], "NOT_ASSESSED")

                path = url + "/" + ident
                self.assertEqual(client.get(path, headers=crew2).status_code, 404)
                self.assertEqual(
                    client.get(url, params={"subject_id": "SUB-1"}, headers=crew2).status_code, 403)

                def step(next_phase, **kwargs):
                    return client.post(path + "/advance", headers=crew1,
                        json={"next_phase": next_phase, "summary": "Human recorded step",
                              "human_confirmed": True, **kwargs})

                self.assertEqual(step("RECHECK", outcome="UNKNOWN").status_code, 409)
                self.assertEqual(
                    client.post(path + "/advance", headers=crew1,
                        json={"next_phase": "EVALUATE", "summary": "Observed",
                              "human_confirmed": False}).status_code, 422)
                self.assertEqual(step("EVALUATE").status_code, 200)
                self.assertEqual(step("ACT").status_code, 422)
                self.assertEqual(step("ACT", action_status="NOT_DONE").status_code, 200)
                self.assertEqual(step("RECHECK", outcome="UNKNOWN").status_code, 200)
                current = client.get(path, headers=crew1)
                self.assertEqual(current.status_code, 200)
                self.assertEqual(current.json()["episode"]["current_phase"], "RECHECK")
                self.assertEqual(len(current.json()["episode"]["events"]), 4)
                listed = client.get(url, params={"subject_id": "SUB-1"}, headers=crew1)
                self.assertEqual(len(listed.json()["episodes"]), 1)

    def test_ambiguous_terms_and_red_flags_stay_independent_of_ai(self):
        ambiguous = next_question(["dau co"], {}, use_ai=False)
        self.assertEqual(ambiguous["state"], "AMBIGUOUS_SYMPTOM")
        self.assertIsNone(ambiguous["next_question"])
        self.assertGreaterEqual(len(ambiguous["ambiguous"][0]["candidates"]), 2)

        exact = next_question(["đau cổ"], {}, use_ai=False)
        self.assertEqual(exact["recognized"], ["đau cổ"])
        self.assertEqual(exact["state"], "MORE_INFORMATION_REQUIRED")

        urgent = next_question(
            ["bất tỉnh"], {"witnessed_unresponsive": "YES"}, use_ai=True)
        self.assertEqual(urgent["state"], "WITNESSED_RED_FLAG_REPORTED")
        self.assertIsNone(urgent["next_question"])
        self.assertEqual(urgent["model_status"], "SAFETY_STOP")
        self.assertTrue(urgent["needs_human_help"])


if __name__ == "__main__":
    unittest.main()
