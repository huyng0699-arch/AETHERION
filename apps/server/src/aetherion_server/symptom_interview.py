"""Structured symptom questioning with optional REAL local/cloud LLM question selection.

Not an autonomous diagnosis or treatment system. Legacy ASTRA severity tags are never
used for clinical escalation. Only explicit patient/witness answers inform escalation.
No session/patient data is saved or sent to a cloud model by default.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from .knowledge_catalog import normalized, symptom_source

QUESTIONS = (
    {"id": "present_now", "text": "Triệu chứng còn đang xảy ra ngay lúc này?", "answers": ["YES", "NO", "UNKNOWN"], "routes": []},
    {"id": "onset", "text": "Triệu chứng bắt đầu khi nào: đột ngột, từ từ hay không rõ?", "answers": ["SUDDEN", "GRADUAL", "UNKNOWN"], "routes": []},
    {"id": "progression", "text": "Triệu chứng đang nặng lên, ổn định hay giảm?", "answers": ["WORSE", "SAME", "BETTER", "UNKNOWN"], "routes": []},
    {"id": "witnessed_unresponsive", "text": "Người chứng kiến có trực tiếp thấy bệnh nhân không đáp ứng hoặc mất ý thức hiện tại không?", "answers": ["YES", "NO", "UNKNOWN"], "routes": ["unconscious", "faint"]},
    {"id": "breathing_at_rest", "text": "Người bệnh có khó thở rõ lúc nghỉ hoặc không thể nói trọn câu không?", "answers": ["YES", "NO", "UNKNOWN"], "routes": ["breathing", "chest", "allergy", "choke", "environment"]},
    {"id": "active_heavy_bleeding", "text": "Có chảy máu nhiều đang tiếp diễn và không kiểm soát được không?", "answers": ["YES", "NO", "UNKNOWN"], "routes": ["bleeding", "injury", "wound", "reproductive"]},
    {"id": "new_one_sided_weakness", "text": "Có yếu một bên mới xuất hiện hoặc nói khó đột ngột không?", "answers": ["YES", "NO", "UNKNOWN"], "routes": ["neuro", "dizzy", "headache"]},
    {"id": "environment_exposure", "text": "Có tiếp xúc với khói, khí bất thường, giảm áp hoặc phơi nhiễm môi trường đáng ngờ không?", "answers": ["YES", "NO", "UNKNOWN"], "routes": ["environment", "heat", "breathing", "headache"]},
    {"id": "fever_measurement", "text": "Đã đo thân nhiệt bằng thiết bị thực hay chỉ có cảm giác sốt?", "answers": ["MEASURED", "SELF_REPORTED", "UNKNOWN"], "routes": ["fever", "infection", "skin"]},
    {"id": "injury_mechanism", "text": "Có chấn thương trực tiếp, ngã hoặc lực va đập trước khi xuất hiện triệu chứng?", "answers": ["YES", "NO", "UNKNOWN"], "routes": ["injury", "headache", "joint", "dental", "eye"]},
    {"id": "duration", "text": "Triệu chứng kéo dài trong khoảng nào?", "answers": ["MINUTES", "HOURS", "DAYS", "LONGER", "UNKNOWN"], "routes": []},
    {"id": "prior_history", "text": "Người bệnh từng có đợt tương tự hoặc bệnh nền liên quan?", "answers": ["YES", "NO", "UNKNOWN"], "routes": []},
    {"id": "medications_allergies", "text": "Có sử dụng thuốc gần đây hoặc có tiền sử dị ứng cần báo nhân viên y tế không?", "answers": ["YES", "NO", "UNKNOWN"], "routes": []},
)
BY_ID = {q["id"]: q for q in QUESTIONS}
CRITICAL = {"witnessed_unresponsive", "breathing_at_rest", "active_heavy_bleeding", "new_one_sided_weakness"}


def _recognized(symptoms: list[str]) -> tuple[list[str], set[str]]:
    data = symptom_source()
    by_id = {}
    by_name = {}
    for entry in data["entries"]:
        for item_id in entry.get("ids", []):
            by_id[str(item_id).casefold()] = entry
        by_name[normalized(entry.get("name", ""))] = entry
        for alias in entry.get("aliases", []):
            by_name[normalized(alias)] = entry
    names, routes = [], set()
    for raw in symptoms[:20]:
        item = by_id.get(str(raw).casefold()) or by_name.get(normalized(raw))
        if item and item["name"] not in names:
            names.append(item["name"])
            routes.update(item.get("routes", []))
    return names, routes


def ai_status() -> dict:
    provider = os.environ.get("AETHERION_INTERVIEW_AI_PROVIDER", "disabled").lower()
    if provider not in ("ollama", "openai"):
        return {"configured": False, "provider": "disabled", "model": None}
    model = os.environ.get("AETHERION_INTERVIEW_AI_MODEL", "").strip()
    if provider == "openai" and not os.environ.get("AETHERION_OPENAI_API_KEY"):
        return {"configured": False, "provider": "openai", "model": model or None, "reason": "API_KEY_NOT_SET"}
    return {"configured": bool(model), "provider": provider, "model": model or None}


def _pick_with_ai(names: list[str], answers: dict[str, str], choices: list[dict],
                  allow_cloud: bool) -> tuple[str | None, str]:
    config = ai_status()
    if not config["configured"]:
        return None, "NOT_CONFIGURED"
    provider = config["provider"]
    if provider == "openai":
        if os.environ.get("AETHERION_ALLOW_CLOUD_AI", "").strip().lower() in ("0", "false", "no", "off"):
            return None, "CLOUD_DISABLED_BY_SERVER_CONFIG"
        if not allow_cloud:
            return None, "CLOUD_CONSENT_REQUIRED"
    if not choices:
        return None, "NO_MORE_QUESTIONS"
    # The model can only select a listed ID; cannot invent a treatment, urgency,
    # unreviewed clinical rule, tool action or external source.
    question_ids = [q["id"] for q in choices]
    system = (
        "You select the NEXT anamnesis question ID for a NON-DIAGNOSTIC structured interview. "
        "Output ONLY valid JSON object with key next_question_id, a string exactly matching one "
        "allowed ID. Never diagnose, infer severity, give treatment/dose, cite fabricated evidence, "
        "or add extra fields. Choose the question most useful to clarify uncertainty."
    )
    payload = json.dumps({"symptoms": names, "answers": answers, "allowed_question_ids": question_ids},
                         ensure_ascii=False)
    try:
        if provider == "ollama":
            url = "http://127.0.0.1:11434/api/chat"
            request = {"model": config["model"], "stream": False, "format": "json",
                       "messages": [{"role": "system", "content": system},
                                    {"role": "user", "content": payload}], "options": {"temperature": 0}}
            headers = {"Content-Type": "application/json"}
        else:
            url = "https://api.openai.com/v1/chat/completions"
            request = {"model": config["model"], "temperature": 0, "max_tokens": 80,
                       "response_format": {"type": "json_object"},
                       "messages": [{"role": "system", "content": system},
                                    {"role": "user", "content": payload}]}
            headers = {"Content-Type": "application/json",
                       "Authorization": "Bearer " + os.environ["AETHERION_OPENAI_API_KEY"]}
        req = urllib.request.Request(url, data=json.dumps(request).encode("utf-8"), headers=headers, method="POST")
        if (
            provider == "ollama"
            and urllib.request.urlopen.__module__ == "urllib.request"
            and (os.environ.get("HTTP_PROXY") or os.environ.get("HTTPS_PROXY"))
        ):
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with opener.open(req, timeout=8) as result:
                raw = result.read(32768)
        else:
            with urllib.request.urlopen(req, timeout=8) as result:
                raw = result.read(32768)
        response = json.loads(raw)
        message = (response.get("message") or {}).get("content", "") if provider == "ollama" else response["choices"][0]["message"]["content"]
        if not isinstance(message, str) or len(message) > 1024:
            return None, "MODEL_RESPONSE_TOO_LARGE"
        decision = json.loads(message)
        if not isinstance(decision, dict):
            return None, "INVALID_MODEL_SELECTION"
        ident = decision.get("next_question_id")
        if not isinstance(ident, str) or ident not in question_ids:
            return None, "INVALID_MODEL_SELECTION"
        return ident, "MODEL_SELECTED"
    except (OSError, ValueError, KeyError, IndexError, TypeError, urllib.error.URLError):
        return None, "MODEL_UNAVAILABLE"


def build_session_history_summary(accepted: dict[str, str]) -> list[dict[str, Any]]:
    """Build an ephemeral per-session structured history without writing to disk."""
    history: list[dict[str, Any]] = []
    for q in QUESTIONS:
        qid = q["id"]
        if qid in accepted:
            ans = accepted[qid]
            history.append(
                {
                    "question_id": qid,
                    "question_text": q["text"],
                    "answer": ans,
                    "is_unknown": ans == "UNKNOWN",
                    "is_critical": qid in CRITICAL,
                }
            )
    return history


def next_question(symptom_ids: list[str], answers: dict[str, str], *,
                  use_ai: bool = False, allow_cloud: bool = False) -> dict[str, Any]:
    names, routes = _recognized(symptom_ids)
    if not names:
        return {"state": "UNKNOWN_SYMPTOM", "recognized": [], "next_question": None,
                "model_status": "NOT_CALLED", "cloud_used": False,
                "session_history": [], "unknown_answers_count": 0,
                "stored_by_server": False, "persistence_requires_consent": True,
                "warning": "Select a recognized symptom first."}
    accepted = {str(k): str(v).upper() for k, v in answers.items() if k in BY_ID and
                isinstance(v, str) and str(v).upper() in BY_ID[k]["answers"]}
    session_history = build_session_history_summary(accepted)
    unknown_count = sum(1 for item in session_history if item["is_unknown"])
    candidates = [q for q in QUESTIONS if q["id"] not in accepted and
                  (not q["routes"] or bool(set(q["routes"]) & routes))]
    # Place explicit critical clarifications first. No final classification
    # is derived from the unreviewed ASTRA legacy tier.
    candidates.sort(key=lambda q: (0 if q["id"] in CRITICAL else 1))
    chosen = candidates[0] if candidates else None
    model_state = "NOT_REQUESTED"
    if use_ai and candidates:
        selected, model_state = _pick_with_ai(names, accepted, candidates, allow_cloud)
        if selected:
            chosen = BY_ID[selected]
    status_info = ai_status()
    cloud_used = bool(
        use_ai and allow_cloud and status_info["provider"] == "openai" and model_state == "MODEL_SELECTED"
    )
    emergency_yes = [k for k in CRITICAL if accepted.get(k) == "YES"]
    state = "WITNESSED_RED_FLAG_REPORTED" if emergency_yes else (
        "MORE_INFORMATION_REQUIRED" if chosen else "INTAKE_COMPLETED_UNVALIDATED"
    )
    return {
        "state": state,
        "recognized": names,
        "answered": len(accepted),
        "remaining": len(candidates),
        "session_history": session_history,
        "unknown_answers_count": unknown_count,
        "next_question": (
            {key: chosen[key] for key in ("id", "text", "answers")} if chosen else None
        ),
        "model_status": model_state,
        "model_provider": status_info["provider"] if use_ai else "disabled",
        "cloud_used": cloud_used,
        "red_flags_reported": emergency_yes,
        "recommendation": (
            "A serious symptom has been explicitly reported. Seek immediate qualified human assistance."
            if emergency_yes else
            "These are unreviewed symptom descriptions, not a diagnosis or a validated safety clearance."
        ),
        "clinical_validation": False,
        "stored_by_server": False,
        "persistence_requires_consent": True,
    }
