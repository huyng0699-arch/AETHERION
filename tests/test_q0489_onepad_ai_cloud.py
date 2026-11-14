"""Focused Q-0489 contracts; upstream HTTP is STUBBED, not live-model evidence.

These tests verify real endpoint and data shapes, server-only key ownership,
model-selected dispatch, explicit consent, authenticated Admin controls, and
honest tested state. A real Admin Test call is required for live inference.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError

_SERVER_SRC = Path(__file__).resolve().parents[1] / "apps" / "server" / "src"
if str(_SERVER_SRC) not in sys.path:
    sys.path.insert(0, str(_SERVER_SRC))

from aetherion_server import assistant_chat
from aetherion_server.admin_api import build_admin_router
from aetherion_server.cloud_ai_runtime import (
    clear_cloud_configuration, cloud_public_status, set_cloud_configuration,
)


@pytest.fixture(autouse=True)
def isolated_cloud(monkeypatch):
    for name in (
        "AETHERION_ALLOW_CLOUD_AI", "AETHERION_ENABLE_CLOUD_CHAT",
        "AETHERION_CHAT_CLOUD_MODEL", "AETHERION_CHAT_CLOUD_PROVIDER",
        "AETHERION_GEMINI_API_KEY", "AETHERION_OPENAI_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)
    clear_cloud_configuration()
    yield
    clear_cloud_configuration()


def _chat(*messages):
    return assistant_chat.FreeChatRequest(
        provider="cloud", cloud_consent=True, locale="en",
        messages=[assistant_chat.ChatLine(role=role, content=text)
                  for role, text in messages],
    )


def test_gemini_dispatch_preserves_chat_turns_and_never_leaks_key(monkeypatch, tmp_path):
    secret = "fixture-gemini-key-12345"
    set_cloud_configuration(provider="gemini", model="gemini-2.5-flash", api_key=secret)
    requests = []

    def fake_invoke(url, payload, headers, *, timeout):
        requests.append((url, payload, headers, timeout))
        return {"candidates": [{"content": {"parts": [{"text": "Model "}, {"text": "reply"}]}}]}

    monkeypatch.setattr(assistant_chat, "_invoke", fake_invoke)
    result = assistant_chat.ask_model(tmp_path / "unused.sqlite", _chat(
        ("user", "Hello"), ("assistant", "Hi"), ("user", "Second question"),
    ))
    assert result["reply"] == "Model reply" and result["provider"] == "cloud"
    assert result["cloud_provider"] == "gemini"
    assert result["stored_by_server"] is False
    assert secret not in str(result)
    assert len(requests) == 1
    url, data, headers, timeout = requests[0]
    assert url == "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
    assert headers["x-goog-api-key"] == secret
    assert [item["role"] for item in data["contents"]] == ["user", "model", "user"]
    assert "systemInstruction" in data and timeout <= 30


def test_openai_dispatch_uses_supported_token_parameter(monkeypatch, tmp_path):
    secret = "fixture-openai-key-67890"
    set_cloud_configuration(provider="openai", model="gpt-4o-mini", api_key=secret)
    calls = []
    def fake_invoke(url, payload, headers, *, timeout):
        calls.append((url, payload, headers))
        return {"choices": [{"message": {"content": "OpenAI real-shape response"}}]}
    monkeypatch.setattr(assistant_chat, "_invoke", fake_invoke)
    result = assistant_chat.ask_model(tmp_path / "unused.sqlite", _chat(("user", "Hi")))
    assert result["reply"] == "OpenAI real-shape response"
    assert result["cloud_provider"] == "openai"
    assert secret not in str(result)
    url, payload, headers = calls[0]
    assert url == "https://api.openai.com/v1/chat/completions"
    assert payload["max_completion_tokens"] == 750
    assert "max_tokens" not in payload and payload["store"] is False
    assert headers["Authorization"] == "Bearer " + secret


def test_missing_consent_rejected_before_any_network(monkeypatch, tmp_path):
    set_cloud_configuration(provider="gemini", model="gemini-2.5-flash",
                            api_key="fixture-key-no-consent-123")
    with pytest.raises(ValidationError):
        assistant_chat.FreeChatRequest(
            provider="cloud", cloud_consent=False,
            messages=[assistant_chat.ChatLine(role="user", content="private question")],
        )


def test_admin_test_is_real_inference_gate_and_resets_on_new_key(monkeypatch, tmp_path):
    set_cloud_configuration(provider="gemini", model="gemini-2.5-flash",
                            api_key="fixture-current-model-key")
    assert cloud_public_status()["tested"] is False
    monkeypatch.setattr(assistant_chat, "_invoke", lambda *a, **kw: {
        "candidates": [{"content": {"parts": [{"text": "connection_ok"}]}}]
    })
    result = assistant_chat.test_cloud_connection(tmp_path / "unused.sqlite")
    assert result["status"] == "READY" and result["actual_inference"] is True
    assert cloud_public_status()["tested"] is True
    set_cloud_configuration(provider="gemini", model="gemini-2.5-flash",
                            api_key="fixture-rotated-model-key")
    assert cloud_public_status()["tested"] is False


def test_failures_cannot_create_a_fake_reply_or_tested_status(monkeypatch, tmp_path):
    set_cloud_configuration(provider="openai", model="gpt-4o-mini",
                            api_key="fixture-server-only-key")
    def failure(*a, **kw):
        raise HTTPException(status_code=503, detail="Provider unavailable")
    monkeypatch.setattr(assistant_chat, "_invoke", failure)
    with pytest.raises(HTTPException):
        assistant_chat.ask_model(tmp_path / "unused.sqlite", _chat(("user", "Hello")))
    assert cloud_public_status()["tested"] is False


def test_admin_role_and_secret_redaction_on_config_endpoints(tmp_path):
    def viewer():
        return ({"role": "crew", "username": "viewer"}, "fake-session")
    app_viewer = FastAPI()
    app_viewer.include_router(build_admin_router(lambda: tmp_path / "unused.sqlite", viewer))
    viewer_client = TestClient(app_viewer)
    payload = {
        "provider": "gemini", "model": "gemini-2.5-flash",
        "api_key": "fixture-admin-secret-123", "enabled": True,
    }
    assert viewer_client.put("/api/v1/admin/ai/cloud/settings", json=payload).status_code == 403

    def administrator():
        return ({"role": "admin", "username": "tester"}, "fake-session")
    app_admin = FastAPI()
    app_admin.include_router(build_admin_router(lambda: tmp_path / "unused.sqlite", administrator))
    admin_client = TestClient(app_admin)
    response = admin_client.put("/api/v1/admin/ai/cloud/settings", json=payload)
    assert response.status_code == 200
    get_response = admin_client.get("/api/v1/admin/ai/cloud/settings")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["provider"] == "gemini" and data["key_configured"] is True
    assert payload["api_key"] not in get_response.text
    assert "api_key" not in data
    assert admin_client.delete("/api/v1/admin/ai/cloud/settings").status_code == 200
