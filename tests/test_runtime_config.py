"""Focused, negative-case configuration checks for Q-0005 (no real patient data)."""

import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "apps" / "server" / "src"
sys.path.insert(0, str(SRC))

from aetherion_server.runtime_config import DEFAULT_PORT, read_runtime_config


class RuntimeConfigTests(unittest.TestCase):
    def test_safe_default(self):
        config = read_runtime_config({})
        self.assertEqual((config.version, config.profile, config.host, config.port), (1, "development", "127.0.0.1", DEFAULT_PORT))

    def test_dev_override_loopback(self):
        result = read_runtime_config({"AETHERION_CONFIG_VERSION": "1", "AETHERION_PROFILE": "development", "AETHERION_HOST": "::1", "AETHERION_PORT": "9000"})
        self.assertEqual((result.host, result.port), ("::1", 9000))

    def test_public_and_ambiguous_hosts_fail_closed(self):
        for host in ["0.0.0.0", "::", "10.0.0.1", "localhost", "127.0.0.1.example.com", "", " 0.0.0.0 "]:
            with self.subTest(host=host), self.assertRaisesRegex(ValueError, "loopback"):
                read_runtime_config({"AETHERION_HOST": host})

    def test_invalid_version_profile_port_and_ttl(self):
        bad = [
            {"AETHERION_CONFIG_VERSION": "2"},
            {"AETHERION_PROFILE": "production"},
            {"AETHERION_PORT": "0"},
            {"AETHERION_PORT": "65536"},
            {"AETHERION_PORT": "http"},
            {"AETHERION_SESSION_TTL_SECONDS": "0"},
            {"AETHERION_SESSION_TTL_SECONDS": "abc"},
            {"AETHERION_SESSION_TTL_SECONDS": "86401"},
        ]
        for item in bad:
            with self.subTest(item=item), self.assertRaises(ValueError):
                read_runtime_config(item)

    def test_release_requires_explicit_absolute_database(self):
        for db_path in ["", "relative.sqlite3", "../test.sqlite", "db/aetherion.sqlite3"]:
            with self.subTest(db_path=db_path), self.assertRaisesRegex(ValueError, "absolute"):
                read_runtime_config({"AETHERION_PROFILE": "release", "AETHERION_DB_PATH": db_path})
        self.assertEqual(read_runtime_config({"AETHERION_PROFILE": "release", "AETHERION_DB_PATH": "/var/lib/aetherion/store.sqlite3"}).profile, "release")
        self.assertEqual(read_runtime_config({"AETHERION_PROFILE": "release", "AETHERION_DB_PATH": r"C:\AETHERION\store.sqlite3"}).profile, "release")

    def test_release_disallows_environment_bootstrap(self):
        base = {"AETHERION_PROFILE": "release", "AETHERION_DB_PATH": "/var/lib/aetherion/store.sqlite3"}
        for key in ["AETHERION_BOOTSTRAP_USER", "AETHERION_BOOTSTRAP_PASSWORD"]:
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "prohibits"):
                read_runtime_config({**base, key: "secret"})

    def test_command_line_rejects_public_bind(self):
        env = dict(os.environ, AETHERION_HOST="0.0.0.0", PYTHONPATH=str(SRC))
        proc = subprocess.run([sys.executable, "-m", "aetherion_server.runtime_config", "--check"], env=env, capture_output=True, text=True, timeout=5)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("public bind is prohibited", proc.stderr)
        self.assertNotIn("secret", proc.stderr)

    def test_command_line_accepts_local_dev(self):
        env = dict(os.environ, AETHERION_HOST="127.0.0.1", AETHERION_PROFILE="development", AETHERION_CONFIG_VERSION="1", AETHERION_PORT="8765", PYTHONPATH=str(SRC))
        for key in ("AETHERION_SESSION_TTL_SECONDS", "AETHERION_BOOTSTRAP_USER", "AETHERION_BOOTSTRAP_PASSWORD"):
            env.pop(key, None)
        proc = subprocess.run([sys.executable, "-m", "aetherion_server.runtime_config", "--check"], env=env, capture_output=True, text=True, timeout=5)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("loopback only", proc.stdout)


if __name__ == "__main__":
    unittest.main()
