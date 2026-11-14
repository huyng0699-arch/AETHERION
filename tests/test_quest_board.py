"""Check that AETHERION's 300-task ledger remains structurally valid."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("aetherion_quest_board", ROOT / "scripts" / "quest_board.py")
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class QuestBoardTests(unittest.TestCase):
    def test_count_and_dependencies(self):
        tasks = module.load_all()
        self.assertEqual(len(tasks), 300)
        self.assertEqual(module.verify(tasks), [])

    def test_every_stream_is_nonempty(self):
        tasks = module.load_all()
        streams = {meta["stream"] for meta in tasks.values()}
        self.assertEqual(len(streams), 20)

    def test_no_premature_done(self):
        tasks = module.load_all()
        for ident, meta in tasks.items():
            if meta["status"] == "DONE":
                self.assertEqual(meta.get("review"), "APPROVED", ident)


if __name__ == "__main__":
    unittest.main()
