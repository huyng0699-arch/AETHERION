"""Fail-closed Personal Today -> 3D Anatomy handoff preserving subject identity (Q-0082)."""
from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from .identity import checked_personal_handoff

REPO_ROOT = Path(__file__).resolve().parents[6]
DEFAULT_APPROVED_MODELS_PATH = REPO_ROOT / "knowledge" / "anatomy" / "approved_models.json"

BODY_REGION_TO_ANATOMY: dict[str, dict[str, str]] = {
    "head_craniofacial_mandible": {
        "anatomical_id": "mandible_visible_human_male",
        "title_vi": "Xương hàm dưới & vùng sọ mặt",
        "title_en": "Mandible & Craniofacial Region",
    },
    "mandible": {
        "anatomical_id": "mandible_visible_human_male",
        "title_vi": "Xương hàm dưới",
        "title_en": "Mandible",
    },
    "cervical_spine": {
        "anatomical_id": "vertebra_c1_visible_human_male",
        "title_vi": "Cột sống cổ (Đốt sống C1 Atlas)",
        "title_en": "Cervical Spine (C1 Atlas)",
    },
    "lumbar_spine": {
        "anatomical_id": "vertebra_l1_visible_human_male",
        "title_vi": "Cột sống thắt lưng (Đốt sống L1)",
        "title_en": "Lumbar Spine (L1)",
    },
    "lower_extremity_femur": {
        "anatomical_id": "femur_right_visible_human_male",
        "title_vi": "Chi dưới – Xương đùi phải",
        "title_en": "Lower Extremity – Right Femur",
    },
    "lower_extremity_tibia": {
        "anatomical_id": "tibia_right_visible_human_male",
        "title_vi": "Chi dưới – Xương chày phải",
        "title_en": "Lower Extremity – Right Tibia",
    },
    "upper_extremity_humerus": {
        "anatomical_id": "humerus_right_visible_human_male",
        "title_vi": "Chi trên – Xương cánh tay phải",
        "title_en": "Upper Extremity – Right Humerus",
    },
    "upper_extremity_clavicle": {
        "anatomical_id": "clavicle_right_visible_human_male",
        "title_vi": "Vùng vai – Xương đòn phải",
        "title_en": "Shoulder – Right Clavicle",
    },
}


@dataclass(frozen=True)
class AnatomyHandoff:
    status: str
    subject_id: str | None
    body_region: str
    anatomical_id: str | None
    model_entry: dict[str, Any] | None
    title_vi: str
    title_en: str
    return_route: str
    diagnostic_claim: bool = False
    educational_reference_only: bool = True


def _load_approved_models(path: Path = DEFAULT_APPROVED_MODELS_PATH) -> dict[str, dict[str, Any]]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    models = payload.get("models", [])
    result: dict[str, dict[str, Any]] = {}
    for entry in models:
        if not isinstance(entry, dict):
            continue
        aid = entry.get("anatomical_id")
        lic = str(entry.get("license", ""))
        if (
            isinstance(aid, str)
            and aid
            and entry.get("rights_status") == "APPROVED"
            and "nc" not in lic.lower()
        ):
            result[aid] = entry
    return result


def build_anatomy_handoff(
    subject_id: str,
    access_token: str,
    body_region: str,
    approved_models_path: Path = DEFAULT_APPROVED_MODELS_PATH,
) -> AnatomyHandoff:
    """Resolve a Today body-region selection into a subject-preserving Anatomy handoff."""
    try:
        checked_subject, _token = checked_personal_handoff(subject_id, access_token)
        if any(unicodedata.category(ch) in {"Cc", "Cf"} for ch in checked_subject):
            raise ValueError("control or format characters are not allowed in subject_id")
    except ValueError:
        return AnatomyHandoff(
            status="DENIED",
            subject_id=None,
            body_region=str(body_region or "").strip().lower(),
            anatomical_id=None,
            model_entry=None,
            title_vi="Chưa xác thực danh tính hoặc phiên làm việc",
            title_en="Missing authenticated subject or session",
            return_route="/personal/today",
        )

    safe_query = urlencode({"subject_id": checked_subject})
    region_key = str(body_region or "").strip().lower()
    mapping = BODY_REGION_TO_ANATOMY.get(region_key)
    if not mapping:
        return AnatomyHandoff(
            status="NO_DATA",
            subject_id=checked_subject,
            body_region=region_key,
            anatomical_id=None,
            model_entry=None,
            title_vi="Chưa có mô hình giải phẫu cho vùng cơ thể này",
            title_en="No approved anatomy model for this body region",
            return_route=f"/personal/today?{safe_query}",
        )

    approved = _load_approved_models(approved_models_path)
    aid = mapping["anatomical_id"]
    model = approved.get(aid)
    if model is None:
        return AnatomyHandoff(
            status="NO_DATA",
            subject_id=checked_subject,
            body_region=region_key,
            anatomical_id=aid,
            model_entry=None,
            title_vi=mapping["title_vi"],
            title_en=mapping["title_en"],
            return_route=f"/personal/today?{safe_query}",
        )

    return AnatomyHandoff(
        status="READY",
        subject_id=checked_subject,
        body_region=region_key,
        anatomical_id=aid,
        model_entry=model,
        title_vi=mapping["title_vi"],
        title_en=mapping["title_en"],
        return_route=f"/personal/today?{safe_query}",
    )
