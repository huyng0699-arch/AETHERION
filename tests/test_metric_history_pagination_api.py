"""Focused API verification test for Q-0051: metric history filtering, interval, and cursor pagination."""

from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile
import unittest

from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER_SRC = REPO_ROOT / "apps" / "server" / "src"
if str(SERVER_SRC) not in sys.path:
    sys.path.insert(0, str(SERVER_SRC))

from aetherion_server.main import create_app


class MetricHistoryPaginationApiTests(unittest.TestCase):
    def test_metric_interval_filtering_and_stable_cursor_pagination(self) -> None:
        old_env = {
            k: os.environ.get(k)
            for k in ("AETHERION_BOOTSTRAP_USER", "AETHERION_BOOTSTRAP_PASSWORD", "AETHERION_BOOTSTRAP_ROLE")
        }
        os.environ["AETHERION_BOOTSTRAP_USER"] = "hist_ops"
        os.environ["AETHERION_BOOTSTRAP_PASSWORD"] = "hist-password-123"
        os.environ["AETHERION_BOOTSTRAP_ROLE"] = "operator"
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                app = create_app(db_path=Path(tmpdir) / "hist.sqlite3")
                with TestClient(app) as client:
                    token = client.post(
                        "/api/v1/auth/login",
                        json={"username": "hist_ops", "password": "hist-password-123"},
                    ).json()["access_token"]
                    headers = {"Authorization": f"Bearer {token}"}

                    # Ingest 4 heart_rate + 1 spo2 across timestamps
                    samples = [
                        ("heart_rate", 68.0, "beats/min", "2026-11-14T08:00:00+00:00"),
                        ("heart_rate", 72.0, "beats/min", "2026-11-14T09:00:00+00:00"),
                        ("spo2", 98.0, "%", "2026-11-14T09:30:00+00:00"),
                        ("heart_rate", 75.0, "beats/min", "2026-11-14T10:00:00+00:00"),
                        ("heart_rate", 79.0, "beats/min", "2026-11-14T11:00:00+00:00"),
                    ]
                    for metric, val, unit, ts in samples:
                        r = client.post(
                            "/api/v1/observations",
                            headers=headers,
                            json={
                                "subject_id": "CREW-01",
                                "scope": "CREW",
                                "metric": metric,
                                "value": val,
                                "unit": unit,
                                "source_id": "pulse_ox_1",
                                "observed_at": ts,
                                "quality": "READY",
                            },
                        )
                        self.assertEqual(r.status_code, 201, r.text)

                    # Page 1: filter metric=heart_rate, interval 08:30..11:30, limit=2, order=asc
                    p1 = client.get(
                        "/api/v1/observations",
                        headers=headers,
                        params={
                            "subject_id": "CREW-01",
                            "metric": "heart_rate",
                            "since": "2026-11-14T08:30:00+00:00",
                            "until": "2026-11-14T11:30:00+00:00",
                            "order": "asc",
                            "limit": 2,
                        },
                    )
                    self.assertEqual(p1.status_code, 200, p1.text)
                    b1 = p1.json()
                    self.assertTrue(b1["has_more"])
                    self.assertIsNotNone(b1["next_cursor"])
                    self.assertEqual([o["value"] for o in b1["observations"]], [72.0, 75.0])

                    # Page 2 using next_cursor
                    p2 = client.get(
                        "/api/v1/observations",
                        headers=headers,
                        params={
                            "subject_id": "CREW-01",
                            "metric": "heart_rate",
                            "since": "2026-11-14T08:30:00+00:00",
                            "until": "2026-11-14T11:30:00+00:00",
                            "order": "asc",
                            "cursor": b1["next_cursor"],
                            "limit": 2,
                        },
                    )
                    self.assertEqual(p2.status_code, 200, p2.text)
                    b2 = p2.json()
                    self.assertFalse(b2["has_more"])
                    self.assertEqual([o["value"] for o in b2["observations"]], [79.0])

                    # Negative test: malformed cursor -> 422
                    bad = client.get(
                        "/api/v1/observations",
                        headers=headers,
                        params={"subject_id": "CREW-01", "cursor": "not-a-valid-cursor"},
                    )
                    self.assertEqual(bad.status_code, 422)
        finally:
            for k, v in old_env.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v


if __name__ == "__main__":
    unittest.main()
