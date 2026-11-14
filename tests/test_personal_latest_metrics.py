"""Focused source-identity tests for the latest-metric Personal Today summary."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

FILE = (
    Path(__file__).resolve().parents[1]
    / "apps/desktop/src/aetherion_desktop/features/personal/latest_metrics.py"
)
spec = importlib.util.spec_from_file_location("aetherion_latest_metrics", FILE)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def card(*, metric="heart_rate", unit="bpm", scope="CREW",
         observed_at="2026-11-14T06:00:00+00:00", source_id="manual",
         quality="UNVERIFIED"):
    return SimpleNamespace(
        metric=metric, unit=unit, scope=scope,
        observed_at=observed_at, source_id=source_id, quality=quality
    )


class LatestMetricCardTests(unittest.TestCase):
    def test_chooses_newest_real_observation(self):
        earlier = card(observed_at="2026-11-14T05:00:00+00:00")
        later = card(observed_at="2026-11-14T07:00:00+00:00", source_id="sensor")
        result = module.latest_metric_cards((earlier, later))
        self.assertEqual(result, (later,))
        self.assertEqual(result[0].source_id, "sensor")

    def test_scope_and_units_never_collapsed(self):
        a = card(scope="CREW", unit="bpm")
        b = card(scope="CABIN", unit="bpm")
        c = card(scope="CREW", unit="other")
        self.assertEqual(len(module.latest_metric_cards((a, b, c))), 3)

    def test_unverified_and_invalid_provenance(self):
        measured = card(quality="UNVERIFIED")
        self.assertEqual(module.latest_metric_cards((measured,))[0].quality, "UNVERIFIED")
        for bad in (card(source_id=""), card(observed_at="2026-11-14T06:00:00")):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    module.latest_metric_cards((bad,))


if __name__ == "__main__":
    unittest.main()
