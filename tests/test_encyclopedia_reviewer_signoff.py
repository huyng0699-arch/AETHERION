"""Tests for Q-0149 reviewer sign-off process."""

from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from knowledge.medical.reviewer_signoff import (
    create_reviewer_signoff,
    evaluate_signoff_status,
)


def test_reviewer_signoff_tracks_date_version_grade_and_staleness() -> None:
    signoff = create_reviewer_signoff(
        condition_id="COND-111111111111",
        reviewer_name="Dr. Placeholder Reviewer",
        reviewer_credentials="MD, Aerospace Medicine",
        reviewed_at_utc="2026-11-14T04:10:00Z",
        content_version="1.0.0",
        evidence_grade="LEVEL_2_NASA_HRP_EVIDENCE",
        decision="APPROVED",
        notes="Matches NASA HRP evidence summary.",
    )
    assert evaluate_signoff_status(signoff, current_version="1.0.0") == "READY"
    assert evaluate_signoff_status(signoff, current_version="1.1.0") == "STALE"
    assert evaluate_signoff_status(None, current_version="1.0.0") == "NO_DATA"


def test_ungraded_approval_or_bad_timestamp_is_rejected() -> None:
    with pytest.raises(ValueError, match="UNGRADED"):
        create_reviewer_signoff(
            condition_id="COND-111111111111",
            reviewer_name="Dr. Placeholder",
            reviewer_credentials="MD",
            reviewed_at_utc="2026-11-14T04:10:00Z",
            content_version="1.0.0",
            evidence_grade="UNGRADED",
            decision="APPROVED",
        )

    with pytest.raises(ValueError, match="UTC"):
        create_reviewer_signoff(
            condition_id="COND-111111111111",
            reviewer_name="Dr. Placeholder",
            reviewer_credentials="MD",
            reviewed_at_utc="2026-11-14",
            content_version="1.0.0",
            evidence_grade="LEVEL_3_COHORT_OR_OSDR",
            decision="NEEDS_REVISION",
        )
