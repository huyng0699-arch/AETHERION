"""Public, read-only access to the bundled historical NASA MA-7 archive."""
from __future__ import annotations

import json
import math
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import APIRouter, HTTPException

REPOSITORY = Path(__file__).resolve().parents[4]
ARCHIVE_PATH = REPOSITORY / "knowledge" / "nasa" / "ma7" / "ma7_source.json"

router = APIRouter(prefix="/api/v1/demo", tags=["NASA historical archive"])


def _localized(value: object) -> bool:
    return isinstance(value, dict) and all(isinstance(value.get(lang), str) and value[lang] for lang in ("en", "vi"))


def _validated_archive(data: object) -> dict:
    if not isinstance(data, dict):
        raise ValueError("Archive must be an object")
    if (data.get("dataset_id") != "NASA-MA7-MERCURY-1962"
            or data.get("data_type") != "HISTORICAL_ACTUAL_REPORTED_MEASUREMENTS"
            or data.get("is_live") is not False
            or data.get("is_synthetic") is not False
            or data.get("is_inspiration4") is not False
            or data.get("is_current_medical_record") is not False):
        raise ValueError("Archive identity or historical status is invalid")
    source_url = data.get("source_url")
    if not isinstance(source_url, str):
        raise ValueError("NASA source is missing")
    source = urlsplit(source_url)
    if (source.scheme != "https" or source.hostname != "www.nasa.gov"
            or source.username or source.password or source.port or not source.path):
        raise ValueError("NASA source is invalid")
    if not str(data.get("source_publisher") or "").startswith("NASA ") or not data.get("source_title"):
        raise ValueError("NASA attribution is incomplete")

    groups, metrics = data.get("groups"), data.get("metric_names")
    if (not isinstance(groups, list) or not groups or not isinstance(metrics, dict)
            or not metrics or not isinstance(data.get("unavailable_metrics"), list)):
        raise ValueError("Archive tables are missing")
    if not all(_localized(label) for label in metrics.values()):
        raise ValueError("Archive metric labels are invalid")
    for group in groups:
        if (not isinstance(group, dict) or not group.get("id") or not group.get("table")
                or not _localized(group.get("title")) or not _localized(group.get("note"))
                or not isinstance(group.get("records"), list) or not group["records"]):
            raise ValueError("Archive group is invalid")
        for record in group["records"]:
            if (not isinstance(record, dict) or not record.get("id") or not _localized(record.get("title"))
                    or not isinstance(record.get("measures"), dict) or not record["measures"]):
                raise ValueError("Archive record is invalid")
            for metric, measure in record["measures"].items():
                if metric not in metrics or not isinstance(measure, dict) or "value" not in measure:
                    raise ValueError("Archive measure is invalid")
                value = measure["value"]
                if value is None:
                    if not measure.get("missing"):
                        raise ValueError("Missing value has no source status")
                elif isinstance(value, bool) or not isinstance(value, (int, float, str)):
                    raise ValueError("Archive value has an invalid type")
                elif isinstance(value, (int, float)) and not math.isfinite(value):
                    raise ValueError("Archive value must be finite")
    return data


@router.get("/nasa-ma7")
def nasa_ma7_archive() -> dict:
    """Return the exact published bundle, never fabricated replacement values."""
    try:
        return _validated_archive(json.loads(ARCHIVE_PATH.read_text(encoding="utf-8")))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError, TypeError, OverflowError) as exc:
        raise HTTPException(status_code=503, detail="NASA archive unavailable") from exc
