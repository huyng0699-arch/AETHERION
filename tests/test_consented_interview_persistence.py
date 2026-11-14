"""Focused tests for Q-0447: consented interview persistence, subject isolation, and audit trail."""

from pathlib import Path
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER_SRC = REPO_ROOT / "apps" / "server" / "src"
if str(SERVER_SRC) not in sys.path:
    sys.path.insert(0, str(SERVER_SRC))

from aetherion_server.care.interview_persistence import (
    ConsentRequiredError,
    ConsentedInterviewStore,
    SubjectIsolationError,
)


class ConsentedInterviewPersistenceTests(unittest.TestCase):
    def test_requires_consent_and_enforces_subject_isolation(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ConsentedInterviewStore(Path(tmp) / "care.sqlite")

            with self.assertRaises(ConsentRequiredError):
                store.save_consented_episode(
                    subject_id="SUBJ-1",
                    actor_id="user-1",
                    consent_granted=False,
                    symptoms=["Khó thở"],
                    answers_with_provenance=[{"question_id": "breathing_at_rest", "answer": "NO"}],
                    interview_state="MORE_INFORMATION_REQUIRED",
                )

            saved = store.save_consented_episode(
                subject_id="SUBJ-1",
                actor_id="user-1",
                consent_granted=True,
                symptoms=["Khó thở"],
                answers_with_provenance=[
                    {
                        "question_id": "breathing_at_rest",
                        "answer": "NO",
                        "recorded_at_utc": "2026-11-14T09:35:00Z",
                    }
                ],
                interview_state="MORE_INFORMATION_REQUIRED",
            )
            self.assertFalse(saved["cloud_exported"])

            with self.assertRaises(SubjectIsolationError):
                store.list_subject_episodes(subject_id="SUBJ-1", requesting_subject_id="SUBJ-2")

            episodes = store.list_subject_episodes(subject_id="SUBJ-1", requesting_subject_id="SUBJ-1")
            self.assertEqual(len(episodes), 1)
            self.assertEqual(episodes[0]["answers_with_provenance"][0]["source_actor_id"], "user-1")

            audits = store.list_audit_events(saved["episode_id"])
            self.assertEqual(len(audits), 1)
            self.assertEqual(audits[0]["action"], "PERSIST_CONSENTED_INTERVIEW")


if __name__ == "__main__":
    unittest.main()
