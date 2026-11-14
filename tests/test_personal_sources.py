"""Focused provenance checks for Personal Health origin separation."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

MODULE = (
    Path(__file__).resolve().parents[1]
    / "apps/desktop/src/aetherion_desktop/features/personal/source_classification.py"
)
spec = importlib.util.spec_from_file_location("aetherion_record_origin", MODULE)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class SourceSeparationTests(unittest.TestCase):
    def test_self_report_does_not_become_sensor(self):
        card = SimpleNamespace(verification_state="SELF_REPORTED", source_id="personal_self_checkin")
        self.assertEqual(module.record_origin(card), ("self", "Self-reported"))

    def test_verified_provenance_not_asserted_to_be_sensor(self):
        card = SimpleNamespace(verification_state="VERIFIED", source_id="manual_verified")
        key, label = module.record_origin(card)
        self.assertEqual(key, "verified")
        self.assertNotIn("sensor", label.lower())

    def test_unknown_origin_stays_unknown(self):
        card = SimpleNamespace(verification_state="UNVERIFIED", source_id="wearable-looking-name")
        self.assertEqual(module.record_origin(card)[0], "unverified")


if __name__ == "__main__":
    unittest.main()
