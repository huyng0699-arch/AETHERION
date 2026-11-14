import importlib.util
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PERSONAL_DIR = ROOT / "apps" / "desktop" / "src" / "aetherion_desktop" / "features" / "personal"


def _load_anatomy_handoff():
    pkg = types.ModuleType("personal_pkg")
    pkg.__path__ = [str(PERSONAL_DIR)]
    sys.modules["personal_pkg"] = pkg

    id_spec = importlib.util.spec_from_file_location("personal_pkg.identity", PERSONAL_DIR / "identity.py")
    id_mod = importlib.util.module_from_spec(id_spec)
    assert id_spec and id_spec.loader
    sys.modules["personal_pkg.identity"] = id_mod
    id_spec.loader.exec_module(id_mod)

    ah_spec = importlib.util.spec_from_file_location("personal_pkg.anatomy_handoff", PERSONAL_DIR / "anatomy_handoff.py")
    ah_mod = importlib.util.module_from_spec(ah_spec)
    assert ah_spec and ah_spec.loader
    sys.modules["personal_pkg.anatomy_handoff"] = ah_mod
    ah_spec.loader.exec_module(ah_mod)
    return ah_mod


class TestPersonalAnatomyHandoff(unittest.TestCase):
    def test_region_handoff_preserves_subject_and_resolves_approved_stl(self):
        ah = _load_anatomy_handoff()
        res = ah.build_anatomy_handoff("CREW-ALPHA-01", "tok-123", "lower_extremity_femur")
        self.assertEqual(res.status, "READY")
        self.assertEqual(res.subject_id, "CREW-ALPHA-01")
        self.assertEqual(res.anatomical_id, "femur_right_visible_human_male")
        self.assertIsNotNone(res.model_entry)
        self.assertEqual(res.model_entry["license"], "CC BY 4.0")
        self.assertFalse(res.diagnostic_claim)
        self.assertTrue(res.educational_reference_only)
        self.assertIn("CREW-ALPHA-01", res.return_route)

    def test_unknown_region_returns_no_data_with_same_subject(self):
        ah = _load_anatomy_handoff()
        res = ah.build_anatomy_handoff("CREW-ALPHA-01", "tok-123", "unmapped_region_xyz")
        self.assertEqual(res.status, "NO_DATA")
        self.assertEqual(res.subject_id, "CREW-ALPHA-01")
        self.assertIsNone(res.model_entry)

    def test_missing_token_fails_closed_as_denied(self):
        ah = _load_anatomy_handoff()
        res = ah.build_anatomy_handoff("CREW-ALPHA-01", "", "mandible")
        self.assertEqual(res.status, "DENIED")
        self.assertIsNone(res.subject_id)
        self.assertIsNone(res.model_entry)


if __name__ == "__main__":
    unittest.main()
