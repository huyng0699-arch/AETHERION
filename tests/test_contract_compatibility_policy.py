"""Contract and breaking-change detection tests for Q-0030 API compatibility policy."""

from copy import deepcopy
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "packages" / "contracts" / "compatibility_policy.json"
OPENAPI_PATH = ROOT / "packages" / "contracts" / "openapi.json"


def detect_breaking_changes(baseline: dict, candidate: dict) -> list[str]:
    issues: list[str] = []
    base_paths = baseline.get("paths", {})
    cand_paths = candidate.get("paths", {})

    for path, methods in base_paths.items():
        if path not in cand_paths:
            issues.append(f"removed path: {path}")
            continue
        for method in methods:
            if method.lower() in {"get", "post", "put", "patch", "delete"} and method not in cand_paths[path]:
                issues.append(f"removed method: {method.upper()} {path}")

    base_schemas = baseline.get("components", {}).get("schemas", {})
    cand_schemas = candidate.get("components", {}).get("schemas", {})
    for name, schema in base_schemas.items():
        if name not in cand_schemas:
            issues.append(f"removed schema: {name}")
            continue
        base_req = set(schema.get("required", []))
        cand_req = set(cand_schemas[name].get("required", []))
        added_req = cand_req - base_req
        if added_req:
            issues.append(f"added required fields to {name}: {sorted(added_req)}")
    return issues


class CompatibilityPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        self.openapi = json.loads(OPENAPI_PATH.read_text(encoding="utf-8"))

    def test_published_openapi_uses_versioned_prefix_and_is_self_compatible(self) -> None:
        prefix = self.policy["path_prefix"]
        api_paths = [p for p in self.openapi["paths"] if p.startswith("/api/")]
        self.assertTrue(api_paths)
        for path in api_paths:
            self.assertTrue(path.startswith(prefix), f"unversioned api path: {path}")
        self.assertEqual(detect_breaking_changes(self.openapi, self.openapi), [])

    def test_additive_optional_field_allowed_while_breaking_changes_detected(self) -> None:
        additive = deepcopy(self.openapi)
        additive["paths"]["/api/v1/health_ping"] = {"get": {"responses": {"200": {"description": "ok"}}}}
        self.assertEqual(detect_breaking_changes(self.openapi, additive), [])

        breaking = deepcopy(self.openapi)
        breaking["paths"].pop("/api/v1/observations", None)
        issues = detect_breaking_changes(self.openapi, breaking)
        self.assertIn("removed path: /api/v1/observations", issues)


if __name__ == "__main__":
    unittest.main()
