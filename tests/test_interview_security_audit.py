"""Targeted security & privacy negative-path audit for Q-0471."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER_SRC = REPO_ROOT / "apps" / "server" / "src"
if str(SERVER_SRC) not in sys.path:
    sys.path.insert(0, str(SERVER_SRC))

from aetherion_server.main import create_app
from aetherion_server import symptom_interview


class _FakeHTTPResponse:
    def __init__(self, payload: dict):
        self._raw = json.dumps(payload).encode("utf-8")

    def read(self, _limit: int = 32768) -> bytes:
        return self._raw

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class InterviewSecurityAuditTests(unittest.TestCase):
    def test_cloud_off_by_default_and_no_secret_leak(self) -> None:
        secret = "sk-test-never-leak-12345"
        with patch.dict(
            os.environ,
            {
                "AETHERION_INTERVIEW_AI_PROVIDER": "openai",
                "AETHERION_INTERVIEW_AI_MODEL": "gpt-4o-mini",
                "AETHERION_OPENAI_API_KEY": secret,
            },
            clear=False,
        ):
            with tempfile.TemporaryDirectory() as tmp:
                app = create_app(db_path=Path(tmp) / "sec.sqlite3")
                with TestClient(app) as client:
                    st = client.get("/api/v1/knowledge/interview/ai-status")
                    self.assertEqual(st.status_code, 200)
                    self.assertNotIn(secret, st.text)

                    sym_resp = client.get("/api/v1/knowledge/symptoms", params={"query": "kho tho", "limit": 5})
                    self.assertEqual(sym_resp.status_code, 200)
                    chosen_symptom = sym_resp.json()["items"][0]["name"]

                    # Default request: cloud off, stored_by_server false
                    r1 = client.post(
                        "/api/v1/knowledge/interview/next",
                        json={"symptoms": [chosen_symptom]},
                    )
                    self.assertEqual(r1.status_code, 200)
                    b1 = r1.json()
                    self.assertFalse(b1["cloud_used"])
                    self.assertFalse(b1["stored_by_server"])
                    self.assertFalse(b1["clinical_validation"])
                    self.assertEqual(b1["model_status"], "NOT_REQUESTED")

                    # use_ai=True without allow_cloud=True must block cloud call
                    with patch("urllib.request.urlopen") as mock_urlopen:
                        r2 = client.post(
                            "/api/v1/knowledge/interview/next",
                            json={"symptoms": [chosen_symptom], "use_ai": True, "allow_cloud": False},
                        )
                        self.assertEqual(r2.status_code, 200)
                        b2 = r2.json()
                        self.assertIn(b2["model_status"], ("CLOUD_CONSENT_REQUIRED", "ADMIN_DISABLED"))
                        self.assertFalse(b2["cloud_used"])
                        direct_b2 = symptom_interview.next_question([chosen_symptom], {}, use_ai=True, allow_cloud=False)
                        self.assertEqual(direct_b2["model_status"], "CLOUD_CONSENT_REQUIRED")
                        self.assertFalse(direct_b2["cloud_used"])
                        mock_urlopen.assert_not_called()

    def test_prompt_injection_and_oversized_payload_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            app = create_app(db_path=Path(tmp) / "sec2.sqlite3")
            with TestClient(app) as client:
                chosen_symptom = client.get("/api/v1/knowledge/symptoms", params={"query": "kho tho", "limit": 5}).json()["items"][0]["name"]

                # Even if AI tries to return an arbitrary clinical rule or huge payload, deterministic rules win
                with patch.dict(
                    os.environ,
                    {
                        "AETHERION_INTERVIEW_AI_PROVIDER": "ollama",
                        "AETHERION_INTERVIEW_AI_MODEL": "llama3",
                    },
                    clear=False,
                ):
                    with patch(
                        "urllib.request.urlopen",
                        return_value=_FakeHTTPResponse({"message": {"content": json.dumps({"next_question_id": "diagnose_safe"})}}),
                    ):
                        res = symptom_interview.next_question(
                            [chosen_symptom],
                            {},
                            use_ai=True,
                        )
                        self.assertEqual(res["model_status"], "INVALID_MODEL_SELECTION")
                        self.assertFalse(res["clinical_validation"])

                        res_flag = symptom_interview.next_question(
                            [chosen_symptom],
                            {"breathing_at_rest": "YES"},
                            use_ai=True,
                        )
                        self.assertEqual(res_flag["model_status"], "SAFETY_STOP")
                        self.assertEqual(res_flag["state"], "WITNESSED_RED_FLAG_REPORTED")
                        self.assertFalse(res_flag["clinical_validation"])

                    with patch(
                        "urllib.request.urlopen",
                        return_value=_FakeHTTPResponse({"message": {"content": "x" * 2048}}),
                    ):
                        res2 = symptom_interview.next_question([chosen_symptom], {}, use_ai=True)
                        self.assertEqual(res2["model_status"], "MODEL_RESPONSE_TOO_LARGE")

                bad_sym = client.post(
                    "/api/v1/knowledge/interview/next",
                    json={"symptoms": ["a" * 200]},
                )
                self.assertEqual(bad_sym.status_code, 422)

                bad_ans = client.post(
                    "/api/v1/knowledge/interview/next",
                    json={"symptoms": [chosen_symptom], "answers": {"onset": "x" * 100}},
                )
                self.assertEqual(bad_ans.status_code, 422)

                bad_art = client.get("/api/v1/knowledge/articles/bad$id")
                self.assertEqual(bad_art.status_code, 404)


if __name__ == "__main__":
    unittest.main()
