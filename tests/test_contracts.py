import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER_SRC = ROOT / "apps" / "server" / "src"
if str(SERVER_SRC) not in sys.path:
    sys.path.insert(0, str(SERVER_SRC))


class ContractsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.openapi_path = ROOT / "packages" / "contracts" / "openapi.json"
        self.readme_path = ROOT / "packages" / "contracts" / "README.md"

    def test_openapi_contract_exists_and_declares_canonical_routes(self) -> None:
        self.assertTrue(self.openapi_path.is_file(), "packages/contracts/openapi.json must exist")
        spec = json.loads(self.openapi_path.read_text(encoding="utf-8"))
        self.assertTrue(spec["openapi"].startswith("3.1"))
        self.assertIn("/health", spec["paths"])
        self.assertIn("/api/v1/observations", spec["paths"])
        obs_path = spec["paths"]["/api/v1/observations"]
        self.assertIn("get", obs_path)
        self.assertIn("post", obs_path)

        obs_schema = spec["components"]["schemas"]["ObservationIn"]
        for field in ("subject_id", "metric", "value", "unit", "observed_at"):
            self.assertIn(field, obs_schema["properties"])
            self.assertIn(field, obs_schema["required"])
        for prop in ("source", "source_id", "scope", "quality", "verification_state"):
            self.assertIn(prop, obs_schema["properties"])

        readme = self.readme_path.read_text(encoding="utf-8")
        self.assertIn("openapi.json", readme)
        self.assertIn("/api/v1/observations", readme)

    def test_openapi_matches_live_fastapi_app_when_pydantic_v2_available(self) -> None:
        import pydantic

        major = int(pydantic.__version__.split(".")[0])
        spec = json.loads(self.openapi_path.read_text(encoding="utf-8"))
        if major >= 2:
            from aetherion_server.main import app

            self.assertEqual(spec, app.openapi())
        else:
            # Even on minimal system Python with Pydantic v1, verify ValidationError schema is present.
            self.assertIn("HTTPValidationError", spec["components"]["schemas"])


if __name__ == "__main__":
    unittest.main()
