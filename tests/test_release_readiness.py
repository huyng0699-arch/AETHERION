"""Synthetic Quest fixtures only: never real Windows release attestation."""

from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from release_readiness import GATES, classify, evaluate, main, quest_metadata


class ReleaseGateTests(unittest.TestCase):
    def test_missing_file_does_not_pass(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(quest_metadata(Path(d) / "missing.md"), {})
            self.assertEqual(classify({}), "MISSING_QUEST")

    def test_running_and_pending_are_not_pass(self):
        self.assertEqual(classify({"status": "RUNNING", "review": "APPROVED"}), "NOT_COMPLETE")
        self.assertEqual(classify({"status": "DONE", "review": "PENDING"}), "REVIEW_PENDING")

    def test_self_review_is_not_independent(self):
        base = {"status": "DONE", "review": "APPROVED", "owner": "Agent/x", "reviewer": "Agent/x (self-verified headless test pass)", "tested_commit": "a" * 40, "evidence": "[test log]"}
        self.assertEqual(classify(base), "SELF_OR_UNVERIFIED_REVIEW")
        base["reviewer"] = "Reviewer/y"
        self.assertEqual(classify(base), "RECORDED_ACCEPTANCE_NOT_RETESTED")

    def test_sha_and_evidence_must_exist(self):
        base = {"status": "DONE", "review": "APPROVED", "owner": "Implementer/x", "reviewer": "Reviewer/y"}
        self.assertEqual(classify(base), "MISSING_TESTED_COMMIT")
        base["tested_commit"] = "b" * 40
        self.assertEqual(classify(base), "MISSING_EVIDENCE")

    def test_demo_report_never_authorizes_release(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            root_quests = root / "quests" / "v1"
            root_quests.mkdir(parents=True)
            for ident, _, scopes in GATES:
                if "demo" in scopes:
                    (root_quests / f"{ident}.md").write_text(f"---\nid: {ident}\nstatus: DONE\nreview: APPROVED\nowner: Implementer/x\nreviewer: Reviewer/y\ntested_commit: {'a' * 40}\nevidence: [observed run log]\n---\n", encoding="utf-8")
            report = evaluate(root, "demo")
            self.assertTrue(report["documentary_gates_complete"])
            self.assertFalse(report["release_authorized"])
            (root_quests / "Q-0002.md").write_text("---\nstatus: READY\n---\n", encoding="utf-8")
            self.assertFalse(evaluate(root, "demo")["documentary_gates_complete"])

    def test_cli_fails_closed_on_unmet_gates(self):
        with tempfile.TemporaryDirectory() as d:
            import contextlib
            import io
            report = Path(d) / "report.json"
            with contextlib.redirect_stdout(io.StringIO()):
                code = main(["--repo", d, "--scope", "demo", "--output", str(report)])
            self.assertEqual(code, 2)
            self.assertIn('"release_authorized": false', report.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
