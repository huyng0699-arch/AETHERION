"""Q-0085: real loopback HTTP checks; fixtures are synthetic engineering data."""
from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
from pathlib import Path
import sys
from threading import Thread
import unittest
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "apps/desktop/src/aetherion_desktop/features/personal/authoritative_reload.py"
spec = importlib.util.spec_from_file_location("aetherion_authoritative_reload_tests", SOURCE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def observation(subject="CREW-1", value=68):
    return {
        "subject_id": subject, "metric": "heart_rate", "value": value,
        "unit": "beats/min", "source_id": "manual_unverified", "scope": "CREW",
        "observed_at": "2026-11-14T09:00:00Z",
        "quality": "UNVERIFIED", "verification_state": "SELF_REPORTED",
    }


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        host = self.server
        if urlsplit(self.path).path != "/api/v1/observations":
            return self._reply(404, {"error": "not found"})
        if self.headers.get("Authorization") != "Bearer valid-token":
            return self._reply(401, {"error": "invalid session"})
        if self.headers.get("Cache-Control") != "no-store":
            return self._reply(400, {"error": "cache policy missing"})
        query = parse_qs(urlsplit(self.path).query)
        host.last_requested_subject = query.get("subject_id", [""])[0]
        return self._reply(host.http_code, host.payload)

    def _reply(self, code, body):
        raw = json.dumps(body).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *args):
        pass


class AuthoritativeReloadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.server.http_code = 200
        cls.server.payload = {}
        cls.server.last_requested_subject = ""
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)

    def setUp(self):
        self.server.http_code = 200
        self.server.payload = {
            "subject_id": "CREW-1", "observations": [observation()], "has_more": False,
        }

    def load(self, subject="CREW-1", token="valid-token"):
        return mod.reload_personal_from_server(self.base, subject, token, timeout=2)

    def test_reload_after_restart_uses_new_server_values_not_memory(self):
        first = self.load()
        self.assertTrue(first.source_is_server)
        self.assertEqual(first.observations[0]["value"], 68)
        # Simulate a NEW client process making another request, with changed server data.
        self.server.payload["observations"] = [observation(value=81)]
        second = self.load()
        self.assertEqual(second.observations[0]["value"], 81)
        self.assertEqual(first.observations[0]["value"], 68)

    def test_expired_or_wrong_session_never_recovers_private_data(self):
        state = self.load(token="wrong")
        self.assertEqual((state.status, state.observations, state.http_status),
                         ("DENIED", (), 401))

    def test_other_subject_response_fails_closed(self):
        state = self.load("CREW-2")
        self.assertEqual((state.status, state.observations), ("ERROR", ()))
        self.assertEqual(self.server.last_requested_subject, "CREW-2")

    def test_missing_provenance_rejects_entire_response(self):
        self.server.payload["observations"] = [observation(), observation(value=70)]
        self.server.payload["observations"][1]["source_id"] = ""
        self.assertEqual((self.load().status, self.load().observations), ("ERROR", ()))

    def test_research_or_test_fixture_not_live(self):
        for patch in ({"verification_state": "TEST_FIXTURE"},
                      {"source_id": "nasa_osdr:research"},
                      {"scope": "engineering_test"}):
            with self.subTest(patch=patch):
                self.server.payload["observations"] = [{**observation(), **patch}]
                self.assertEqual(self.load().status, "ERROR")

    def test_empty_authoritative_read_returns_no_data(self):
        self.server.payload["observations"] = []
        state = self.load()
        self.assertEqual((state.status, state.observations), ("NO_DATA", ()))
        self.assertTrue(state.source_is_server)

    def test_server_unavailable_does_not_return_cached_readings(self):
        self.server.http_code = 503
        state = self.load()
        self.assertEqual((state.status, state.observations), ("OFFLINE", ()))

    def test_url_subject_is_encoded_and_unsafe_base_is_rejected(self):
        url = mod.build_authoritative_url(self.base, "CREW-1&limit=999")
        self.assertEqual(parse_qs(urlsplit(url).query)["subject_id"], ["CREW-1&limit=999"])
        with self.assertRaises(ValueError):
            mod.build_authoritative_url("https://token:secret@example.org", "CREW-1")
        with self.assertRaises(ValueError):
            mod.build_authoritative_url(self.base, "bad\nheader")

    def test_missing_token_rejected_before_http_request(self):
        for token in ("", "contains space", "bad\nheader"):
            with self.subTest(token=token), self.assertRaises(ValueError):
                self.load(token=token)

    def test_all_records_preserve_original_quality_and_time(self):
        state = self.load()
        row = state.observations[0]
        self.assertEqual(row["source_id"], "manual_unverified")
        self.assertEqual(row["quality"], "UNVERIFIED")
        self.assertEqual(row["observed_at"], "2026-11-14T09:00:00Z")


if __name__ == "__main__":
    unittest.main()
