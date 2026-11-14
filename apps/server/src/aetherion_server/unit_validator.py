"""Measurement unit compatibility validation for canonical AETHERION metrics (Q-0033)."""

from __future__ import annotations

METRIC_ALLOWED_UNITS: dict[str, frozenset[str]] = {
    "heart_rate": frozenset({"beats/min", "bpm"}),
    "spo2": frozenset({"%"}),
    "body_temperature": frozenset({"degC", "C", "degF", "F", "K"}),
    "body_mass": frozenset({"kg", "g", "lb"}),
    "cabin_co2": frozenset({"ppm", "mmHg", "kPa"}),
    "co2_partial_pressure": frozenset({"mmHg", "kPa", "ppm"}),
    "cabin_pressure": frozenset({"kPa", "hPa", "psi", "mmHg"}),
    "cabin_humidity": frozenset({"%"}),
    "cabin_temperature": frozenset({"degC", "C", "degF", "F", "K"}),
    "radiation_dose_rate": frozenset({"mSv/day", "uSv/h", "mGy/day"}),
    "sleep_duration": frozenset({"h", "min"}),
    "fatigue_score": frozenset({"scale_1_10", "score"}),
}


def validate_metric_unit(metric: str, unit: str) -> None:
    clean_unit = unit.strip()
    if not clean_unit:
        raise ValueError("unit must not be blank")
    allowed = METRIC_ALLOWED_UNITS.get(metric.strip().lower())
    if allowed is not None and clean_unit not in allowed:
        raise ValueError(
            f"Incompatible unit '{clean_unit}' for metric '{metric}'; expected one of {sorted(allowed)}"
        )
