"""Admin-controlled local AI question selection, preserving deterministic safety.

One existing interview engine and one server-owned SQLite setting store.
LLM may ONLY select a known next-question ID. It cannot change red-flag
outcomes, recommend treatment or create any patient record.
"""
from __future__ import annotations

import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, HTTPRedirectHandler, ProxyHandler

from .admin_control import probe_local_ai, read_ai_settings, validate_local_url
from .symptom_interview import BY_ID, CRITICAL, QUESTIONS, _recognized, next_question


def model_status(db_path: str | Path) -> dict:
    config = read_ai_settings(db_path)
    if config["mode"] != "local_only":
        return {"configured": False, "provider": "disabled", "model": None,
                "source": "server_admin", "reason": "AI_DISABLED"}
    result = probe_local_ai(config)
    return {
        "configured": bool(result["model_ready"]),
        "provider": "ollama", "model": config["local_model"],
        "source": "server_admin", "connection": result["connection"],
        "reason": None if result["model_ready"] else (result.get("error") or "MODEL_NOT_INSTALLED"),
    }


def _model_select(choices: list[dict], names: list[str], answers: dict[str, str],
                  config: dict) -> tuple[str | None, str]:
    """Bound the output to an approved static question ID, never a medical rule."""
    if not choices:
        return None, "NO_MORE_QUESTIONS"
    allowed_ids = [choice["id"] for choice in choices]
    prompt = {
        "symptoms": names,
        "answers": answers,
        "allowed_question_ids": allowed_ids,
    }
    system = (
        "You only select a question ID from the provided list for a NON-DIAGNOSTIC "
        "intake. Output a JSON object with the single key next_question_id. "
        "Do not diagnose, triage, advise treatment, infer consciousness, or invent IDs."
    )
    payload = {
        "model": config["local_model"], "stream": False, "format": "json",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
        ],
        "options": {"temperature": 0, "num_predict": 64},
    }
    class RejectRedirect(HTTPRedirectHandler):
        def redirect_request(self, request, fp, code, msg, headers, newurl):
            return None
    try:
        url = validate_local_url(config["local_url"]) + "/api/chat"
        req = Request(url, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                      headers={"Content-Type": "application/json"}, method="POST")
        opener = build_opener(ProxyHandler({}), RejectRedirect())
        with opener.open(req, timeout=int(config["timeout_seconds"])) as response:
            if response.status != 200:
                return None, "MODEL_UNAVAILABLE"
            body = json.loads(response.read(32768))
        message = (body.get("message") or {}).get("content")
        if not isinstance(message, str) or len(message) > 1024:
            return None, "INVALID_MODEL_SELECTION"
        response_json = json.loads(message)
        if not isinstance(response_json, dict) or set(response_json) != {"next_question_id"}:
            return None, "INVALID_MODEL_SELECTION"
        selected = response_json["next_question_id"]
        if not isinstance(selected, str) or selected not in allowed_ids:
            return None, "INVALID_MODEL_SELECTION"
        return selected, "MODEL_SELECTED"
    except (OSError, ValueError, TypeError, KeyError, HTTPError, URLError):
        return None, "MODEL_UNAVAILABLE"


def interview_next(
    db_path: str | Path,
    symptoms: list[str],
    answers: dict[str, str],
    *,
    use_ai: bool,
    allow_cloud: bool,
) -> dict:
    # Run unmodified, deterministic clinical boundaries FIRST; no AI call on
    # unknown symptom, invalid answers, red flags, or completed intake.
    result = next_question(symptoms, answers, use_ai=False, allow_cloud=False)
    if not use_ai or result.get("state") != "MORE_INFORMATION_REQUIRED":
        return result
    config = read_ai_settings(db_path)
    if config["mode"] != "local_only":
        return {**result, "model_status": "ADMIN_DISABLED", "model_provider": "disabled"}
    # Cloud consent is never sufficient to activate a Cloud provider. Local-only
    # remains local even if the UI sends allow_cloud=True.
    availability = probe_local_ai(config)
    if not availability["model_ready"]:
        return {**result, "model_status": "MODEL_UNAVAILABLE", "model_provider": "ollama"}

    names, routes, ambiguous, unknown = _recognized(symptoms)
    if ambiguous or unknown or not names:
        return result
    normalized_answers = {k: v.upper() for k, v in answers.items()}
    candidates = [q for q in QUESTIONS if q["id"] not in normalized_answers
                  and (not q["routes"] or bool(set(q["routes"]) & routes))]
    critical = [q for q in candidates if q["id"] in CRITICAL]
    allowed = critical if critical else candidates
    ident, model_state = _model_select(allowed, names, normalized_answers, config)
    if ident is None:
        return {**result, "model_status": model_state, "model_provider": "ollama"}
    selected = BY_ID[ident]
    # Keep all deterministic metadata and human safety gates, only change
    # which pre-existing question is asked next.
    return {
        **result,
        "next_question": {k: selected[k] for k in ("id", "text", "answers")},
        "model_status": model_state,
        "model_provider": "ollama",
    }
