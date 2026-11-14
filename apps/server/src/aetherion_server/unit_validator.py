"""Measurement unit compatibility and physical range validation (Q-0033, Q-0048)."""

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

# Physical/engineering plausibility bounds (not clinical thresholds).
METRIC_UNIT_BOUNDS: dict[tuple[str, str], tuple[float, float]] = {
    ("heart_rate", "beats/min"): (0.0, 350.0),
    ("heart_rate", "bpm"): (0.0, 350.0),
    ("spo2", "%"): (0.0, 100.0),
    ("cabin_humidity", "%"): (0.0, 100.0),
    ("body_mass", "kg"): (1.0, 500.0),
    ("cabin_co2", "ppm"): (0.0, 100000.0),
    ("sleep_duration", "h"): (0.0, 48.0),
    ("fatigue_score", "scale_1_10"): (1.0, 10.0),
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


def validate_metric_range(metric: str, value: float, unit: str) -> None:
    bounds = METRIC_UNIT_BOUNDS.get((metric.strip().lower(), unit.strip()))
    if bounds is None:
        return
    low, high = bounds
    if value < low or value > high:
        raise ValueError(
            f"Out-of-range value {value} {unit} for metric '{metric}'; allowed range is [{low}, {high}]"
        )
