"""Unit tests for Q-0076 Personal Today real dashboard."""

from __future__ import annotations

from datetime import datetime, timezone
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "apps/desktop/src/aetherion_desktop/features/personal/today_dashboard.py"
)
spec = importlib.util.spec_from_file_location("personal_today_dashboard", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
assert spec.loader is not None
spec.loader.exec_module(mod)

NOW = datetime(2026, 11, 14, 6, 0, tzinfo=timezone.utc)


def obs(**extra):
    base = {
        "subject_id": "USER-1",
        "metric": "resting_heart_rate",
        "value": 64,
        "unit": "bpm",
        "observed_at": "2026-11-14T05:30:00+00:00",
        "source_id": "wearable_sync",
        "scope": "PERSONAL",
        "quality": "READY",
        "verification_state": "VERIFIED",
    }
    base.update(extra)
    return base


class PersonalTodayDashboardTests(unittest.TestCase):
    def test_healthy_user_opens_without_forced_symptom_intake_on_no_data(self) -> None:
        snap = mod.build_personal_today_snapshot({"subject_id": "USER-1", "observations": []}, "USER-1", now=NOW)
        self.assertEqual(snap.state, "NO_DATA")
        self.assertFalse(snap.intake_required)
        self.assertEqual(snap.cards, ())

    def test_offline_and_denied_states_are_explicit(self) -> None:
        off = mod.build_personal_today_snapshot({}, "USER-1", offline=True)
        self.assertEqual(off.state, "OFFLINE")
        self.assertFalse(off.intake_required)

        den = mod.build_personal_today_snapshot({}, "USER-1", denied=True)
        self.assertEqual(den.state, "DENIED")

    def test_self_reported_never_upgraded_to_ready(self) -> None:
        snap = mod.build_personal_today_snapshot(
            {"subject_id": "USER-1", "observations": [obs(verification_state="SELF_REPORTED")]},
            "USER-1",
            now=NOW,
        )
        self.assertEqual(snap.cards[0].quality, "UNVERIFIED")
        self.assertEqual(snap.cards[0].source_id, "wearable_sync")

    def test_stale_verified_observation_marked_stale(self) -> None:
        snap = mod.build_personal_today_snapshot(
            {"subject_id": "USER-1", "observations": [obs(observed_at="2026-11-12T05:00:00+00:00")]},
            "USER-1",
            now=NOW,
        )
        self.assertEqual(snap.state, "STALE")
        self.assertEqual(snap.cards[0].quality, "STALE")

    def test_missing_provenance_or_identity_mismatch_fails_closed(self) -> None:
        for bad in (
            {"subject_id": "OTHER", "observations": []},
            {"subject_id": "USER-1", "observations": [obs(source_id="")]},
            {"subject_id": "USER-1", "observations": [obs(value=float("nan"))]},
            {"subject_id": "USER-1", "observations": [obs(observed_at="2026-11-14T05:00:00")]},
        ):
            snap = mod.build_personal_today_snapshot(bad, "USER-1", now=NOW)
            self.assertEqual(snap.state, "ERROR")
            self.assertEqual(snap.cards, ())

    def test_submit_personal_checkin_sends_self_reported_provenance(self) -> None:
        captured = {}

        class _Resp(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        def fake_opener(req, timeout=10):
            captured["url"] = req.full_url
            captured["body"] = json.loads(req.data.decode("utf-8"))
            return _Resp(b'{"accepted": true}')

        result = mod.submit_personal_checkin(
            "http://127.0.0.1:8765/",
            "USER-1",
            "energy_level",
            8,
            "score_1_10",
            note="feeling well",
            now=NOW,
            opener=fake_opener,
        )
        self.assertTrue(result["accepted"])
        self.assertEqual(captured["body"]["verification_state"], "SELF_REPORTED")
        self.assertEqual(captured["body"]["quality"], "UNVERIFIED")
        self.assertEqual(captured["body"]["scope"], "PERSONAL")


if __name__ == "__main__":
    unittest.main()
