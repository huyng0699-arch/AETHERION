"""Contract checks for the public, source-preserving NASA mobile Demo."""
from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "server" / "src"))
from aetherion_server import demo_archive


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(demo_archive.router)
    with TestClient(app) as test_client:
        yield test_client


def test_public_archive_matches_original_mobile_bundle(client):
    original_path = ROOT / "apps" / "mobile" / "assets" / "ma7_source.json"
    assert demo_archive.ARCHIVE_PATH.read_bytes() == original_path.read_bytes()
    response = client.get("/api/v1/demo/nasa-ma7")
    assert response.status_code == 200
    assert response.json() == json.loads(original_path.read_text(encoding="utf-8"))
    assert response.json()["is_live"] is False
    assert response.json()["is_current_medical_record"] is False


class ArchiveText:
    def __init__(self, text):
        self.text = text

    def read_text(self, *, encoding):
        assert encoding == "utf-8"
        return self.text


def test_missing_archive_returns_503_without_fabricating_data(client, monkeypatch):
    class MissingArchive:
        def read_text(self, *, encoding):
            raise FileNotFoundError("No local source")

    monkeypatch.setattr(demo_archive, "ARCHIVE_PATH", MissingArchive())
    response = client.get("/api/v1/demo/nasa-ma7")
    assert response.status_code == 503
    assert response.json() == {"detail": "NASA archive unavailable"}


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("is_live", True),
        ("is_synthetic", True),
        ("is_current_medical_record", True),
        ("source_url", "https://www.nasa.gov.example.test/fake.pdf"),
        ("dataset_id", "other-dataset"),
        ("groups", None),
    ],
)
def test_invalid_provenance_or_tables_returns_503(client, monkeypatch, field, value):
    data = json.loads(demo_archive.ARCHIVE_PATH.read_text(encoding="utf-8"))
    data[field] = value
    monkeypatch.setattr(demo_archive, "ARCHIVE_PATH", ArchiveText(json.dumps(data)))
    response = client.get("/api/v1/demo/nasa-ma7")
    assert response.status_code == 503
    assert response.json() == {"detail": "NASA archive unavailable"}


def test_malformed_archive_returns_503(client, monkeypatch):
    monkeypatch.setattr(demo_archive, "ARCHIVE_PATH", ArchiveText("{"))
    assert client.get("/api/v1/demo/nasa-ma7").status_code == 503
