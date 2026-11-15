"""The source-bound chat contract; the upstream model is deliberately stubbed."""
from pathlib import Path
import sys

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

SERVER_SRC = Path(__file__).resolve().parents[1] / "apps" / "server" / "src"
sys.path.insert(0, str(SERVER_SRC))

from aetherion_server import assistant_chat


@pytest.fixture
def client(monkeypatch):
    def identity():
        return ({"role": "crew", "username": "test"}, "test-token")

    app = FastAPI()
    app.include_router(assistant_chat.build_assistant_router(lambda: Path("unused.sqlite"), identity))
    monkeypatch.setattr(assistant_chat, "read_ai_settings", lambda db: {
        "mode": "local_only",
        "local_model": "local-test-model",
        "local_url": "http://127.0.0.1:11434",
        "timeout_seconds": 10,
    })
    monkeypatch.setattr(assistant_chat, "probe_local_ai", lambda settings: {"model_ready": True})
    return TestClient(app)


def _post(client, article_id="CLIFF-001", **kwargs):
    return client.post("/api/v1/assistant/chat", json={
        "provider": "local",
        "messages": [{"role": "user", "content": "What does the source say?"}],
        "source_article_id": article_id,
        **kwargs,
    })


def test_selected_source_reaches_provider_and_returns_traceable_citation(client, monkeypatch):
    article = {
        "summary": {"title": "Selected NASA record", "content_state": "EXTRACTED"},
        "source": {
            "source_id": "NASA-test",
            "source_url": "https://www.nasa.gov/test",
            "verification_state": "ARCHIVE_CLAIM",
        },
        "sections": [{"heading": "Evidence", "text_content": "NASA_TEXT " + "x" * 18000}],
    }
    monkeypatch.setattr(assistant_chat.knowledge_catalog, "article", lambda article_id: article)
    calls = []

    def stub_provider(url, payload, headers, *, timeout):
        calls.append(payload)
        return {"message": {"content": "Source-grounded test reply."}}

    monkeypatch.setattr(assistant_chat, "_invoke", stub_provider)
    response = _post(client)
    assert response.status_code == 200
    answer = response.json()
    assert answer["reply"] == "Source-grounded test reply."
    assert answer["sources"][0]["source_id"] == "NASA-test"
    assert answer["sources"][0]["url"] == "https://www.nasa.gov/test"
    assert answer["sources"][0]["independent_pdf_verification"] is False
    assert answer["sources"][0]["excerpt_truncated"] is True
    assert "truncated excerpt" in answer["notice"]
    system = calls[0]["messages"][0]["content"]
    assert "NASA_TEXT" in system
    assert "truncated" in system
    assert "Reply in English" in system
    assert len(system) < 20000


@pytest.mark.parametrize("sections", [[], [{"heading": "Empty", "text_content": "  "}]])
def test_empty_source_never_calls_model(client, monkeypatch, sections):
    monkeypatch.setattr(assistant_chat.knowledge_catalog, "article", lambda article_id: {
        "summary": {"title": "Empty record"}, "sections": sections, "source": {},
    })
    called = []
    monkeypatch.setattr(assistant_chat, "_invoke", lambda *args, **kwargs: called.append(True))
    response = _post(client)
    assert response.status_code == 422
    assert called == []


def test_invalid_or_missing_source_never_calls_model(client, monkeypatch):
    monkeypatch.setattr(assistant_chat.knowledge_catalog, "article", lambda article_id: None)
    called = []
    monkeypatch.setattr(assistant_chat, "_invoke", lambda *args, **kwargs: called.append(True))
    assert _post(client, article_id="CLIFF-999").status_code == 404
    assert _post(client, article_id="../secret").status_code == 422
    assert called == []


def test_cloud_request_without_consent_is_rejected_before_network(client, monkeypatch):
    called = []
    monkeypatch.setattr(assistant_chat, "_invoke", lambda *args, **kwargs: called.append(True))
    response = _post(client, article_id=None, provider="cloud", cloud_consent=False)
    assert response.status_code == 422
    assert called == []


def test_unavailable_local_model_returns_error_without_generated_reply(client, monkeypatch):
    monkeypatch.setattr(assistant_chat, "probe_local_ai", lambda settings: {"model_ready": False})
    called = []
    monkeypatch.setattr(assistant_chat, "_invoke", lambda *args, **kwargs: called.append(True))
    response = _post(client, article_id=None)
    assert response.status_code == 503
    assert "reply" not in response.json()
    assert called == []
