"""Tests for Q-0143 unverified content flags."""

from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from knowledge.medical.unverified_content_guard import classify_content_provenance

VALID_SHA = "b" * 64


def test_author_generated_text_cannot_be_labeled_official_nasa() -> None:
    entry = {
        "entry_id": "ENT-1",
        "origin_type": "AUTHOR_GENERATED",
        "verification_state": "READY",
        "source_url": "https://www.nasa.gov/hrp/",
        "source_sha256": VALID_SHA,
    }
    flags = classify_content_provenance(entry)
    assert flags["is_official_nasa_article"] is False
    assert flags["is_author_generated"] is True
    assert flags["is_unverified"] is True
    assert flags["badge"] == "AUTHOR_GENERATED_NOT_OFFICIAL_NASA"

    spoofed = dict(entry)
    spoofed["label_as_nasa"] = True
    with pytest.raises(ValueError, match="official NASA article"):
        classify_content_provenance(spoofed)


def test_unverified_or_non_nasa_source_exposes_unverified_flag() -> None:
    unverified_nasa = {
        "entry_id": "ENT-2",
        "origin_type": "NASA_ORIGINAL",
        "verification_state": "NO_DATA",
        "source_url": "https://www.nasa.gov/integrated-medical-model-documentation/",
        "source_sha256": "",
    }
    flags = classify_content_provenance(unverified_nasa)
    assert flags["is_official_nasa_article"] is False
    assert flags["is_unverified"] is True
    assert flags["badge"] == "UNVERIFIED_NO_DATA"


def test_verified_nasa_original_passes_strict_checks() -> None:
    verified = {
        "entry_id": "ENT-3",
        "origin_type": "NASA_ORIGINAL",
        "verification_state": "READY",
        "source_url": "https://osdr.nasa.gov/bio/repo/data/studies/OSD-575",
        "source_sha256": VALID_SHA,
        "label_as_nasa": True,
    }
    flags = classify_content_provenance(verified)
    assert flags["is_official_nasa_article"] is True
    assert flags["is_unverified"] is False
    assert flags["warning_banner"] is None
