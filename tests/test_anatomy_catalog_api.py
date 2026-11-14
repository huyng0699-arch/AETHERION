"""Focused tests for Q-0467: server-controlled anatomical mesh catalog and delivery."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER_SRC = REPO_ROOT / "apps" / "server" / "src"
if str(SERVER_SRC) not in sys.path:
    sys.path.insert(0, str(SERVER_SRC))

from aetherion_server import anatomy_catalog
from aetherion_server.main import create_app


class AnatomyCatalogApiTests(unittest.TestCase):
    def test_empty_repo_catalog_returns_no_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(anatomy_catalog, "DEFAULT_CATALOG_PATH", Path(tmp) / "missing_approved_models.json"):
                app = create_app(db_path=Path(tmp) / "anat.sqlite3")
                with TestClient(app) as client:
                    resp = client.get("/api/v1/knowledge/anatomy/models")
                    self.assertEqual(resp.status_code, 200)
                    body = resp.json()
                    self.assertEqual(body["status"], "NO_DATA")
                    self.assertEqual(body["models"], [])
                    missing = client.get("/api/v1/knowledge/anatomy/models/heart_lod0/file")
                    self.assertEqual(missing.status_code, 404)

    def test_serves_only_approved_sha_verified_models_and_blocks_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mesh_bytes = b"solid test\nendsolid test\n"
            mesh_sha = hashlib.sha256(mesh_bytes).hexdigest()
            (root / "heart.stl").write_bytes(mesh_bytes)
            (root / "unapproved.stl").write_bytes(b"solid nope\n")

            catalog_path = root / "approved_models.json"
            catalog_path.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "models": [
                            {
                                "anatomical_id": "heart_lod0",
                                "filename": "heart.stl",
                                "sha256": mesh_sha,
                                "source_url": "https://example.org/heart.stl",
                                "author": "BodyParts3D",
                                "license": "CC-BY-SA-2.1-JP",
                                "rights_status": "APPROVED",
                                "derivative_license": "CC-BY-SA-2.1-JP",
                                "lod": {"level": 0, "triangles": 2},
                            },
                            {
                                "anatomical_id": "unapproved_mesh",
                                "filename": "unapproved.stl",
                                "sha256": hashlib.sha256(b"solid nope\n").hexdigest(),
                                "source_url": "https://example.org/u.stl",
                                "author": "Unknown",
                                "license": "ALL_RIGHTS_RESERVED",
                                "rights_status": "PENDING",
                                "derivative_license": "NONE",
                            },
                            {
                                "anatomical_id": "traversal_mesh",
                                "filename": "../secret.stl",
                                "sha256": mesh_sha,
                                "source_url": "https://example.org/s.stl",
                                "author": "Attacker",
                                "license": "CC0",
                                "rights_status": "APPROVED",
                                "derivative_license": "CC0",
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            app = create_app(db_path=root / "srv.sqlite3")
            with (
                patch.object(anatomy_catalog, "DEFAULT_CATALOG_PATH", catalog_path),
                TestClient(app) as client,
            ):
                lst = client.get("/api/v1/knowledge/anatomy/models")
                self.assertEqual(lst.status_code, 200)
                models = lst.json()["models"]
                self.assertEqual(len(models), 1)
                self.assertEqual(models[0]["anatomical_id"], "heart_lod0")
                self.assertEqual(models[0]["content_type"], "model/stl")
                self.assertEqual(models[0]["size_bytes"], len(mesh_bytes))

                dl = client.get("/api/v1/knowledge/anatomy/models/heart_lod0/file")
                self.assertEqual(dl.status_code, 200)
                self.assertEqual(dl.content, mesh_bytes)
                self.assertEqual(dl.headers["x-content-sha256"], mesh_sha)

                self.assertEqual(
                    client.get("/api/v1/knowledge/anatomy/models/unapproved_mesh/file").status_code,
                    404,
                )
                self.assertEqual(
                    client.get("/api/v1/knowledge/anatomy/models/traversal_mesh/file").status_code,
                    404,
                )


if __name__ == "__main__":
    unittest.main()
