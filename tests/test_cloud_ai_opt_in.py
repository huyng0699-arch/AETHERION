"""Focused tests for Q-0445: secure optional cloud AI with explicit opt-in and fail-closed errors."""

import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import urllib.error

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER_SRC = REPO_ROOT / "apps" / "server" / "src"
if str(SERVER_SRC) not in sys.path:
    sys.path.insert(0, str(SERVER_SRC))

from aetherion_server import runtime_config, symptom_interview


class CloudAiOptInTests(unittest.TestCase):
    def test_runtime_config_defaults_cloud_off_and_validates_flag(self):
        cfg = runtime_config.read_runtime_config({})
        self.assertFalse(cfg.cloud_ai_opt_in)

        cfg_on = runtime_config.read_runtime_config({"AETHERION_ALLOW_CLOUD_AI": "true"})
        self.assertTrue(cfg_on.cloud_ai_opt_in)

        with self.assertRaises(ValueError):
            runtime_config.read_runtime_config({"AETHERION_ALLOW_CLOUD_AI": "maybe"})

    def test_cloud_provider_fails_closed_and_respects_server_disable(self):
        sym = "Khó thở"
        with patch.dict(
            os.environ,
            {
                "AETHERION_INTERVIEW_AI_PROVIDER": "openai",
                "AETHERION_INTERVIEW_AI_MODEL": "gpt-4o-mini",
                "AETHERION_OPENAI_API_KEY": "sk-secret-value",
                "AETHERION_ALLOW_CLOUD_AI": "false",
            },
            clear=False,
        ):
            res = symptom_interview.next_question([sym], {}, use_ai=True, allow_cloud=True)
            self.assertEqual(res["model_status"], "CLOUD_DISABLED_BY_SERVER_CONFIG")
            self.assertFalse(res["cloud_used"])
            self.assertIsNotNone(res["next_question"])

        with patch.dict(
            os.environ,
            {
                "AETHERION_INTERVIEW_AI_PROVIDER": "openai",
                "AETHERION_INTERVIEW_AI_MODEL": "gpt-4o-mini",
                "AETHERION_OPENAI_API_KEY": "sk-secret-value",
                "AETHERION_ALLOW_CLOUD_AI": "true",
            },
            clear=False,
        ):
            with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
                res2 = symptom_interview.next_question([sym], {}, use_ai=True, allow_cloud=True)
                self.assertEqual(res2["model_status"], "MODEL_UNAVAILABLE")
                self.assertFalse(res2["cloud_used"])
                self.assertIsNotNone(res2["next_question"])


if __name__ == "__main__":
    unittest.main()
