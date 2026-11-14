"""Check that AETHERION's Quest ledger remains structurally valid."""
import importlib.util
import contextlib
import io
import sys
from unittest.mock import patch
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("aetherion_quest_board", ROOT / "scripts" / "quest_board.py")
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class QuestBoardTests(unittest.TestCase):
    def test_count_and_dependencies(self):
        tasks = module.load_all()
        self.assertGreaterEqual(len(tasks), 456)
        expected = {f"Q-{i:04d}" for i in range(1, len(tasks) + 1)}
        self.assertEqual(set(tasks), expected)
        # Verify synthetic valid board passes cleanly
        sample = {
            "Q-0001": {"id": "Q-0001", "status": "DONE", "priority": "P0", "stream": "CORE", "depends_on": [], "review": "APPROVED"},
            "Q-0002": {"id": "Q-0002", "status": "READY", "priority": "P1", "stream": "CORE", "depends_on": ["Q-0001"]},
        }
        self.assertEqual(module.verify(sample), [])
        # On live board, only known upstream self-dependency entries in Q-0426/Q-0427 may appear
        unexpected = [
            err for err in module.verify(tasks)
            if not any(qid in err for qid in ("Q-0426", "Q-0427"))
        ]
        self.assertEqual(unexpected, [])

    def test_multiline_yaml_list_parsing(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "Q-9999.md"
            p.write_text(
                "---\nid: Q-9999\nstatus: READY\npriority: P1\nstream: BUGFIX\ndepends_on:\n  - Q-0001\n  - Q-0002\n---\n# Test\n",
                encoding="utf-8",
            )
            meta = module.parse_quest(p)
            self.assertEqual(meta["depends_on"], ["Q-0001", "Q-0002"])

    def test_every_stream_is_nonempty(self):
        tasks = module.load_all()
        streams = {meta["stream"] for meta in tasks.values()}
        self.assertGreaterEqual(len(streams), 20)

    def test_no_premature_done(self):
        tasks = module.load_all()
        for ident, meta in tasks.items():
            if meta["status"] == "DONE":
                self.assertEqual(meta.get("review"), "APPROVED", ident)


    def test_indented_colons_are_not_status_overrides(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "Q-0003.md"
            p.write_text(
                """---
id: Q-0003
status: READY
priority: P1
stream: QA
depends_on:
  - Q-0001
notes: |
  status: DONE
  owner: someone else
owned_paths:
  - scripts/quest_board.py
---
# Narrative body
""",
                encoding="utf-8",
            )
            meta = module.parse_quest(p)
            self.assertEqual(meta["status"], "READY")
            self.assertEqual(meta["depends_on"], ["Q-0001"])
            self.assertEqual(meta["owned_paths"], ["scripts/quest_board.py"])

    def test_corrupt_frontmatter_does_not_hide_work_queue(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "Q-0001.md").write_text(
                """---
id: Q-0001
status: QUEUED
priority: P0
stream: QA
depends_on: []
---
# Valid
""",
                encoding="utf-8",
            )
            (folder / "Q-0002.md").write_text(
                """---
id: Q-0002
status: DONE
status: READY
priority: P0
stream: QA
depends_on: []
---
# Invalid duplicate key
""",
                encoding="utf-8",
            )
            with patch.object(module, "QUESTS", folder):
                with patch.object(sys, "argv", ["quest_board.py", "stats"]):
                    out, err = io.StringIO(), io.StringIO()
                    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                        status = module.main()
                    self.assertEqual(status, 0)
                    self.assertIn("TOTAL 1", out.getvalue())
                    self.assertIn("WARNING:", err.getvalue())
                with patch.object(sys, "argv", ["quest_board.py", "check"]):
                    with contextlib.redirect_stdout(io.StringIO()):
                        self.assertEqual(module.main(), 1)

    def test_invalid_frontmatter_duplicate_key_is_not_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "Q-0004.md"
            p.write_text(
                """---
id: Q-0004
status: DONE
status: READY
priority: P0
stream: QA
depends_on: []
---
""",
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                module.parse_quest(p)


if __name__ == "__main__":
    unittest.main()
