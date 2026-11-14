"""Scope classification and metric-to-scope boundary validation (Q-0020)."""

from __future__ import annotations

PERSON_SCOPES = frozenset({"CREW", "crew", "personal"})
ENVIRONMENT_SCOPES = frozenset({"CABIN", "VEHICLE", "habitat"})
ALL_ALLOWED_SCOPES = PERSON_SCOPES | ENVIRONMENT_SCOPES | frozenset({"engineering_test"})

ENVIRONMENT_METRICS = frozenset(
    {
        "cabin_co2",
        "co2_partial_pressure",
        "cabin_pressure",
        "cabin_humidity",
        "cabin_temperature",
        "radiation_dose_rate",
    }
)

PERSON_METRICS = frozenset(
    {
        "heart_rate",
        "spo2",
        "body_temperature",
        "body_mass",
        "fatigue_score",
        "sleep_duration",
    }
)


def validate_metric_scope(metric: str, scope: str) -> None:
    if scope not in ALL_ALLOWED_SCOPES:
        raise ValueError(f"Unsupported scope '{scope}'")
    normalized_metric = metric.strip().lower()
    if normalized_metric in ENVIRONMENT_METRICS and scope in PERSON_SCOPES:
        raise ValueError(
            f"Environmental metric '{metric}' cannot be assigned to person scope '{scope}'; use CABIN, VEHICLE, or habitat"
        )
    if normalized_metric in PERSON_METRICS and scope in ENVIRONMENT_SCOPES:
        raise ValueError(
            f"Person metric '{metric}' cannot be assigned to environment scope '{scope}'; use CREW, crew, or personal"
        )
