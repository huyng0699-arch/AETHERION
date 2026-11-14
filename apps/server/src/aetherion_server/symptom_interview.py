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


def _recognized(symptoms: list[str]) -> tuple[list[str], set[str], list[dict], list[str]]:
    """Prefer exact accented medical terms; never silently collapse aliases.

    For ambiguous unaccented or duplicate labels return ALL candidates. They
    must be resolved by the person, not arbitrarily selected by dictionary order.
    """
    import unicodedata

    def exact(value: str) -> str:
        return " ".join(unicodedata.normalize("NFC", str(value)).casefold().split())

    by_id: dict[str, list[dict]] = {}
    by_name: dict[str, list[dict]] = {}
    by_alias: dict[str, list[dict]] = {}
    by_loose: dict[str, list[dict]] = {}

    def add(target: dict[str, list[dict]], key: str, entry: dict) -> None:
        matches = target.setdefault(key, [])
        if entry not in matches:
            matches.append(entry)

    for entry in symptom_source()["entries"]:
        for ident in entry.get("ids", []):
            add(by_id, exact(ident), entry)
        add(by_name, exact(entry.get("name", "")), entry)
        for alias in entry.get("aliases", []):
            add(by_alias, exact(alias), entry)
        for text in [entry.get("name", ""), *entry.get("aliases", [])]:
            add(by_loose, normalized(text), entry)

    names: list[str] = []
    routes: set[str] = set()
    ambiguous: list[dict] = []
    unrecognized: list[str] = []
    for raw in symptoms[:20]:
        key = exact(raw)
        # An exact canonical label outranks a colliding alias; an unaccented
        # approximation never outranks an exact accented medical expression.
        found = by_id.get(key) or by_name.get(key) or by_alias.get(key)
        if found is None:
            found = by_loose.get(normalized(raw), [])
        if not found:
            unrecognized.append(str(raw)[:120])
        elif len(found) != 1:
            ambiguous.append({
                "input": str(raw)[:120],
                "candidates": sorted({str(entry["name"]) for entry in found}),
            })
        else:
            entry = found[0]
            if entry["name"] not in names:
                names.append(entry["name"])
                routes.update(entry.get("routes", []))
    return names, routes, ambiguous, unrecognized


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
            base = os.environ.get("AETHERION_OLLAMA_BASE_URL", "http://127.0.0.1:11434").strip().rstrip("/")
            if not (
                base.startswith("http://127.0.0.1:")
                or base == "http://127.0.0.1"
                or base.startswith("http://localhost:")
                or base == "http://localhost"
                or base.startswith("http://[::1]:")
            ):
                return None, "MODEL_UNAVAILABLE"
            url = f"{base}/api/chat"
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
    """Return one contextual question, preserving uncertainty and safety exits."""
    names, routes, ambiguous, unrecognized = _recognized(symptom_ids)
    base = {
        "recognized": names,
        "clinical_validation": False,
        "stored_by_server": False,
        "triage_decision": "NOT_CLINICALLY_VALIDATED",
        "model_provider": "disabled",
    }
    if ambiguous:
        return {**base, "state": "AMBIGUOUS_SYMPTOM",
                "ambiguous": ambiguous, "unrecognized": unrecognized,
                "next_question": None, "model_status": "NOT_CALLED",
                "red_flags_reported": [],
                "recommendation": "Clarify the ambiguous symptom before continuing."}
    if unrecognized or not names:
        return {**base, "state": "UNKNOWN_SYMPTOM",
                "unrecognized": unrecognized, "next_question": None,
                "model_status": "NOT_CALLED", "red_flags_reported": [],
                "recommendation": "Select a recognized symptom; absence of a match is not reassurance."}

    invalid = [str(key)[:80] for key, val in answers.items()
               if key not in BY_ID or not isinstance(val, str)
               or val.upper() not in BY_ID[key]["answers"]]
    if invalid:
        return {**base, "state": "INVALID_ANSWER",
                "invalid_question_ids": invalid, "next_question": None,
                "model_status": "NOT_CALLED", "red_flags_reported": [],
                "recommendation": "Correct or remove unsupported answers before continuing."}

    accepted = {key: val.upper() for key, val in answers.items()}
    urgent_answers = sorted(key for key in CRITICAL if accepted.get(key) == "YES")
    if urgent_answers:
        # Independent of AI availability, and never continue routine prompts
        # after an explicit directly reported red-flag answer.
        return {**base, "state": "WITNESSED_RED_FLAG_REPORTED",
                "answered": len(accepted), "remaining": 0,
                "next_question": None, "model_status": "SAFETY_STOP",
                "red_flags_reported": urgent_answers,
                "needs_human_help": True,
                "recommendation": (
                    "A serious warning sign was explicitly reported. Seek immediate "
                    "qualified human assistance. This is not a medical diagnosis."
                )}

    candidates = [q for q in QUESTIONS if q["id"] not in accepted
                  and (not q["routes"] or bool(set(q["routes"]) & routes))]
    critical_questions = [q for q in candidates if q["id"] in CRITICAL]
    allowed = critical_questions if critical_questions else candidates
    chosen = allowed[0] if allowed else None
    model_state = "NOT_REQUESTED"
    if use_ai and allowed:
        selected, model_state = _pick_with_ai(names, accepted, allowed, allow_cloud)
        if selected is not None:
            chosen = BY_ID[selected]
    return {
        **base,
        "state": "MORE_INFORMATION_REQUIRED" if chosen else "INTAKE_COMPLETED_UNVALIDATED",
        "answered": len(accepted), "remaining": len(candidates),
        "next_question": (
            {key: chosen[key] for key in ("id", "text", "answers")}
            if chosen else None
        ),
        "model_status": model_state,
        "model_provider": ai_status()["provider"] if use_ai else "disabled",
        "red_flags_reported": [],
        "needs_human_help": False,
        "recommendation": (
            "An unreviewed structured intake, not a diagnosis or proof of safety. "
            "For a health concern, consult a qualified professional."
        ),
    }
