"""Focused real loopback HTTP smoke test for Q-0444: local Ollama inference selection."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import sys
import threading
import unittest
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER_SRC = REPO_ROOT / "apps" / "server" / "src"
if str(SERVER_SRC) not in sys.path:
    sys.path.insert(0, str(SERVER_SRC))

from aetherion_server import symptom_interview


class OllamaLocalInferenceTests(unittest.TestCase):
    def test_loopback_ollama_receives_limited_context_and_selects_allowed_id(self):
        captured: dict = {}

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length).decode("utf-8"))
                captured["request"] = body
                user_ctx = json.loads(body["messages"][1]["content"])
                chosen_id = user_ctx["allowed_question_ids"][-1]
                reply = {"message": {"content": json.dumps({"next_question_id": chosen_id})}}
                raw = json.dumps(reply).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def log_message(self, *_args):
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with patch.dict(
                os.environ,
                {
                    "AETHERION_INTERVIEW_AI_PROVIDER": "ollama",
                    "AETHERION_INTERVIEW_AI_MODEL": "llama3.2",
                    "AETHERION_OLLAMA_BASE_URL": f"http://127.0.0.1:{port}",
                },
                clear=False,
            ):
                res = symptom_interview.next_question(["Khó thở"], {}, use_ai=True)
                self.assertEqual(res["model_status"], "MODEL_SELECTED")
                self.assertEqual(res["model_provider"], "ollama")
                self.assertFalse(res["cloud_used"])
                self.assertIsNotNone(res["next_question"])
                user_ctx = json.loads(captured["request"]["messages"][1]["content"])
                self.assertEqual(res["next_question"]["id"], user_ctx["allowed_question_ids"][-1])
        finally:
            server.shutdown()
            server.server_close()

        # Non-loopback URL must be rejected
        with patch.dict(
            os.environ,
            {
                "AETHERION_INTERVIEW_AI_PROVIDER": "ollama",
                "AETHERION_INTERVIEW_AI_MODEL": "llama3.2",
                "AETHERION_OLLAMA_BASE_URL": "https://evil.example.com",
            },
            clear=False,
        ):
            res_bad = symptom_interview.next_question(["Khó thở"], {}, use_ai=True)
            self.assertEqual(res_bad["model_status"], "MODEL_UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()
