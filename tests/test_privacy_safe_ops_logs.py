"""Focused unit tests for Q-0013: privacy-safe machine-readable operational logs."""

from __future__ import annotations

import io
import json
import logging
import unittest

from aetherion_server.ops_logging import build_privacy_safe_logger, emit_ops_log


class PrivacySafeOpsLogsTests(unittest.TestCase):
    def test_redacts_tokens_and_patient_fields_with_machine_readable_json(self) -> None:
        buf = io.StringIO()
        logger = build_privacy_safe_logger("aetherion.ops.test", stream=buf)

        emit_ops_log(
            logger,
            logging.WARNING,
            "auth_check Bearer super_secret_token_12345 sk-testkey1234567890",
            subject_id="CREW-01",
            access_token="tok_abc123",
            password="MyPassword!",
            symptoms=["headache"],
            http_status=401,
            route="/api/v1/observations",
        )

        raw_line = buf.getvalue().strip()
        parsed = json.loads(raw_line)
        self.assertEqual(parsed["severity"], "WARNING")
        self.assertIn("T", parsed["ts_utc"])
        self.assertTrue(parsed["ts_utc"].endswith("+00:00"))
        self.assertNotIn("super_secret_token_12345", raw_line)
        self.assertNotIn("sk-testkey1234567890", raw_line)
        self.assertNotIn("CREW-01", raw_line)
        self.assertNotIn("tok_abc123", raw_line)
        self.assertNotIn("MyPassword!", raw_line)
        self.assertNotIn("headache", raw_line)
        self.assertEqual(parsed["fields"]["http_status"], 401)
        self.assertEqual(parsed["fields"]["route"], "/api/v1/observations")


if __name__ == "__main__":
    unittest.main()
