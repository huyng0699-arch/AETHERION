"""E2E test for Q-0247: NASA evidence interaction -> documented care action."""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER_SRC = REPO_ROOT / "apps" / "server" / "src"
for p in (str(REPO_ROOT), str(SERVER_SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

from aetherion_server.care.episode import CareEpisodeStore  # noqa: E402
from aetherion_server.main import create_app  # noqa: E402


class NasaEvidenceInteractionE2ETests(unittest.TestCase):
    def test_hazard_science_lookup_links_to_documented_care_action(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "nasa_e2e.sqlite3"
            app = create_app(db_path=db_path)
            with TestClient(app) as client:
                # 1. Search hazard-sourced NASA CliFF science
                search_resp = client.get(
                    "/api/v1/knowledge/articles",
                    params={"query": "seizure", "limit": 10},
                )
                self.assertEqual(search_resp.status_code, 200)
                items = search_resp.json()["items"]
                self.assertTrue(any(item["article_id"] == "CLIFF-061" for item in items))

                # 2. Fetch full NASA CliFF-061 evidence record
                art_resp = client.get("/api/v1/knowledge/articles/CLIFF-061")
                self.assertEqual(art_resp.status_code, 200)
                art = art_resp.json()
                self.assertTrue(art["read_only"])
                self.assertFalse(art["clinical_decision_support"])
                self.assertTrue(art["source"]["source_url"].startswith("https://"))
                self.assertGreater(len(art["sections"]), 0)
                self.assertGreater(len(art["references"]), 0)

                # 3. Record documented action in CareEpisodeStore citing the exact NASA article & source URL
                care_store = CareEpisodeStore(Path(tmpdir) / "care.sqlite")
                ep = care_store.start_episode(
                    subject_id="CREW-02",
                    actor_id="cmo-01",
                    chief_concern="Suspected seizure event",
                    source="symptom_intake",
                    recorded_at="2026-11-14T10:20:00+00:00",
                )
                care_store.advance_phase(
                    ep["episode_id"],
                    next_phase="EVALUATE",
                    actor_id="cmo-01",
                    source="nasa_cliff:CLIFF-061",
                    summary=f"Consulted {art['summary'].get('title', 'CLIFF-061')} ({art['source']['source_url']})",
                    recorded_at="2026-11-14T10:21:00+00:00",
                    payload={
                        "article_id": "CLIFF-061",
                        "source_url": art["source"]["source_url"],
                        "section_count": len(art["sections"]),
                    },
                )
                updated = care_store.advance_phase(
                    ep["episode_id"],
                    next_phase="ACT",
                    actor_id="cmo-01",
                    source="human_clinician",
                    summary="Airway protection and crew monitoring per documented CLIFF-061 reference",
                    recorded_at="2026-11-14T10:22:00+00:00",
                    human_confirmed=True,
                    payload={"referenced_article_id": "CLIFF-061"},
                )
                self.assertEqual(updated["current_phase"], "ACT")
                self.assertEqual(updated["events"][1]["payload"]["article_id"], "CLIFF-061")


if __name__ == "__main__":
    unittest.main()
