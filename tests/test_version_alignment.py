"""Focused test for Q-0014: package versions, API version, and CHANGELOG agree on 0.2.0."""

from __future__ import annotations

from pathlib import Path
import re
import tomllib
import unittest

from aetherion_server.main import create_app

REPO_ROOT = Path(__file__).resolve().parents[1]


class VersionAlignmentTests(unittest.TestCase):
    def test_server_desktop_api_and_changelog_versions_match(self) -> None:
        server_meta = tomllib.loads((REPO_ROOT / "apps" / "server" / "pyproject.toml").read_text(encoding="utf-8"))
        desktop_meta = tomllib.loads((REPO_ROOT / "apps" / "desktop" / "pyproject.toml").read_text(encoding="utf-8"))
        server_ver = server_meta["project"]["version"]
        desktop_ver = desktop_meta["project"]["version"]

        self.assertEqual(server_ver, desktop_ver)

        app = create_app()
        self.assertEqual(app.version, server_ver)

        changelog = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        m = re.search(r"^## \[(\d+\.\d+\.\d+)\]", changelog, re.M)
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), server_ver)


if __name__ == "__main__":
    unittest.main()
