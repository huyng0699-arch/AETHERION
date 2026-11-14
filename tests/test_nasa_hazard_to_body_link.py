from __future__ import annotations

import unittest

from knowledge.nasa.hazard_to_body_link import resolve_hazard_route


class TestNasaHazardToBodyLink(unittest.TestCase):
    def test_gravity_routes_to_musculoskeletal_and_cardiovascular_or_no_data(self) -> None:
        empty = resolve_hazard_route("gravity_fields", observations=[])
        self.assertEqual(empty.anatomy_systems, ["musculoskeletal", "cardiovascular"])
        self.assertEqual(empty.status, "NO_DATA")
        self.assertTrue(empty.primary_sources)

        with_obs = resolve_hazard_route(
            "gravity_fields",
            observations=[
                {"metric": "heart_rate_bpm", "value": 64, "unit": "bpm"},
                {"metric": "cabin_co2_ppm", "value": 900, "unit": "ppm"},
            ],
        )
        self.assertEqual(with_obs.status, "READY")
        self.assertEqual(len(with_obs.matched_observations), 1)
        self.assertEqual(with_obs.matched_observations[0]["metric"], "heart_rate_bpm")

    def test_habitat_hazard_does_not_match_personal_heart_rate(self) -> None:
        res = resolve_hazard_route(
            "hostile_closed_environments",
            observations=[{"metric": "heart_rate_bpm", "value": 70, "unit": "bpm"}],
        )
        self.assertEqual(res.status, "NO_DATA")
        self.assertEqual(res.matched_observations, [])

    def test_unknown_hazard_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            resolve_hazard_route("solar_unicorn")


if __name__ == "__main__":
    unittest.main()
