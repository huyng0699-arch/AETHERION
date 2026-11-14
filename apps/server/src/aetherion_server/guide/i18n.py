"""Localized Vietnamese and English safety copy preserving source links (Q-0159)."""

from __future__ import annotations

from typing import Any

SAFETY_COPY: dict[str, dict[str, dict[str, str]]] = {
    "no_data_not_healthy": {
        "en": {
            "text": "Missing or unmeasured data does not indicate normal or healthy status.",
            "source_url": "https://www.spaceappschallenge.org/2026/challenges/health-monitoring-software/",
        },
        "vi": {
            "text": "Thiếu dữ liệu hoặc chưa đo không đồng nghĩa với trạng thái bình thường hay khỏe mạnh.",
            "source_url": "https://www.spaceappschallenge.org/2026/challenges/health-monitoring-software/",
        },
    },
    "research_not_live_telemetry": {
        "en": {
            "text": "NASA OSDR records are historical research datasets, not live astronaut telemetry.",
            "source_url": "https://osdr.nasa.gov/",
        },
        "vi": {
            "text": "Dữ liệu NASA OSDR là tập dữ liệu nghiên cứu lịch sử, không phải thông số sinh tồn thời gian thực của phi hành gia.",
            "source_url": "https://osdr.nasa.gov/",
        },
    },
    "not_medical_device": {
        "en": {
            "text": "AETHERION is an educational prototype, not a certified medical device or diagnostic authority.",
            "source_url": "https://www.spaceappschallenge.org/legal/",
        },
        "vi": {
            "text": "AETHERION là nguyên mẫu giáo dục, không phải thiết bị y tế được chứng nhận hay công cụ chẩn đoán lâm sàng.",
            "source_url": "https://www.spaceappschallenge.org/legal/",
        },
    },
}


def get_localized_safety_notice(key: str, lang: str = "en") -> dict[str, Any]:
    entry = SAFETY_COPY.get(key)
    if not entry:
        raise KeyError(f"Unknown safety copy key: {key}")
    normalized_lang = lang if lang in ("en", "vi") else "en"
    payload = entry[normalized_lang]
    return {
        "key": key,
        "lang": normalized_lang,
        "text": payload["text"],
        "source_url": payload["source_url"],
        "fallback_used": lang not in ("en", "vi"),
    }
