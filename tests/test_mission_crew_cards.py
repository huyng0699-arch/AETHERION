"""Q-0063 tests: subject-locked cards with source-aware no-data states."""
from __future__ import annotations

from dataclasses import dataclass
import importlib.util
from pathlib import Path
import sys
import unittest

MODULE = (Path(__file__).resolve().parents[1]
          / "apps/desktop/src/aetherion_desktop/features/mission/crew_cards.py")
spec = importlib.util.spec_from_file_location("aetherion_crew_cards_test", MODULE)
cards = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = cards
spec.loader.exec_module(cards)


@dataclass(frozen=True)
class Row:
    subject_id: str = "CREW-7"
    source_id: str = "human_entry"
    observed_at: str = "2026-11-14T06:00:00Z"


@dataclass(frozen=True)
class State:
    subject_id: str = "CREW-7"
    status: str = "UNVERIFIED"
    measurements: tuple = (Row(),)


class CardTests(unittest.TestCase):
    def test_latest_real_source_and_timestamp(self):
        model = cards.card_from_state("CREW-7", State(measurements=(
            Row(observed_at="2026-11-14T05:00:00Z", source_id="older"),
            Row(observed_at="2026-11-14T06:00:00Z", source_id="newer"))))
        self.assertEqual(model.subject_id, "CREW-7")
        self.assertEqual(model.latest_source_id, "newer")
        self.assertEqual(model.last_observed_at, "2026-11-14T06:00:00Z")
        self.assertEqual(model.measurement_count, 2)
        self.assertTrue(model.allow_open)

    def test_no_data_never_fabricates_source(self):
        model = cards.card_from_state("CREW-7", State(status="NO_DATA", measurements=()))
        self.assertEqual(model.measurement_count, 0)
        self.assertIsNone(model.latest_source_id)
        self.assertIsNone(model.last_observed_at)
        self.assertIn("NO_DATA", model.display_note)

    def test_denied_cannot_open_or_expose_earlier_records(self):
        model = cards.card_from_state("CREW-7", State(status="DENIED", measurements=()))
        self.assertFalse(model.allow_open)
        with self.assertRaises(ValueError):
            cards.card_from_state("CREW-7", State(status="DENIED"))

    def test_offline_no_health_verdict(self):
        model = cards.card_from_state("CREW-7", State(status="OFFLINE", measurements=()))
        self.assertIsNone(model.latest_source_id)
        self.assertIn("no current observation", model.display_note)

    def test_error_cannot_open(self):
        model = cards.card_from_state("CREW-7", State(status="ERROR", measurements=()))
        self.assertFalse(model.allow_open)

    def test_subject_mismatch_fails_closed(self):
        with self.assertRaises(ValueError):
            cards.card_from_state("CREW-8", State())
        with self.assertRaises(ValueError):
            cards.card_from_state("CREW-7", State(measurements=(Row(subject_id="CREW-8"),)))

    def test_missing_source_rejected(self):
        with self.assertRaises(ValueError):
            cards.card_from_state("CREW-7", State(measurements=(Row(source_id=""),)))

    def test_naive_timestamp_rejected(self):
        with self.assertRaises(ValueError):
            cards.card_from_state("CREW-7", State(measurements=(Row(observed_at="2026-11-14T06:00:00"),)))

    def test_unknown_state_rejected(self):
        with self.assertRaises(ValueError):
            cards.card_from_state("CREW-7", State(status="HEALTHY"))

    def test_missing_measurements_rejected(self):
        with self.assertRaises(ValueError):
            cards.card_from_state("CREW-7", object())

    def test_invalid_subject_rejected(self):
        for ident in ("", " " * 4, "x" * 81):
            with self.subTest(ident=ident), self.assertRaises(ValueError):
                cards.card_from_state(ident, State())


if __name__ == "__main__":
    unittest.main()
