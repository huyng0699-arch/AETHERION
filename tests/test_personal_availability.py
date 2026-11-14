"""Focused regression: missing/unverified/stale personal data are not healthy."""
import importlib.util
from pathlib import Path
import sys
import unittest

FILE = (
    Path(__file__).resolve().parents[1]
    / "apps/desktop/src/aetherion_desktop/features/personal/today_dashboard.py"
)
spec = importlib.util.spec_from_file_location("personal_availability_spec", FILE)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
assert spec.loader is not None
spec.loader.exec_module(module)


def record(quality="READY", verification_state="VERIFIED",
           observed_at="2026-11-14T06:00:00+00:00"):
    return dict(
        subject_id="CREW-02", metric="heart_rate", value=75, unit="bpm",
        scope="CREW", source_id="verified_instrument",
        observed_at=observed_at, quality=quality,
        verification_state=verification_state,
    )


class AvailabilityTests(unittest.TestCase):
    def test_empty_is_unknown(self):
        snapshot = module.build_personal_today_snapshot(
            {"subject_id": "CREW-02", "observations": []}, "CREW-02"
        )
        self.assertEqual(snapshot.state, "NO_DATA")
        self.assertEqual(snapshot.cards, ())

    def test_self_reported_is_not_ready(self):
        snapshot = module.build_personal_today_snapshot(
            {"subject_id": "CREW-02", "observations": [record(
                verification_state="SELF_REPORTED")]}, "CREW-02"
        )
        self.assertEqual(snapshot.state, "UNVERIFIED")
        self.assertEqual(snapshot.cards[0].quality, "UNVERIFIED")
        self.assertNotIn("healthy", snapshot.status_note.lower())

    def test_stale_data_is_not_ready(self):
        from datetime import datetime, timezone
        snapshot = module.build_personal_today_snapshot(
            {"subject_id": "CREW-02", "observations": [
                record(observed_at="2026-11-12T06:00:00+00:00")]},
            "CREW-02", now=datetime(2026, 11, 14, 6, 0, tzinfo=timezone.utc)
        )
        self.assertEqual(snapshot.state, "STALE")

    def test_mixed_verified_and_unverified_never_green(self):
        from datetime import datetime, timezone
        snapshot = module.build_personal_today_snapshot(
            {"subject_id": "CREW-02", "observations": [
                record(), record(verification_state="SELF_REPORTED")]},
            "CREW-02", now=datetime(2026, 11, 14, 6, 30, tzinfo=timezone.utc)
        )
        self.assertEqual(snapshot.state, "UNVERIFIED")


if __name__ == "__main__":
    unittest.main()
