import tempfile
import unittest
from pathlib import Path

from scripts import lint_python


class LintPythonTests(unittest.TestCase):
    def test_repo_python_files_pass_lint(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        checked, errors = lint_python.lint_paths([repo_root])
        self.assertGreater(checked, 0)
        self.assertEqual(errors, [])

    def test_syntax_error_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad_syntax.py"
            bad.write_text("def broken(:\n    pass\n", encoding="utf-8")
            exit_code = lint_python.main([str(bad)])
            self.assertEqual(exit_code, 1)

    def test_mixed_tab_space_indentation_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad_indent.py"
            bad.write_text("def f():\n\tx = 1\n    y = 2\n", encoding="utf-8")
            exit_code = lint_python.main([str(bad)])
            self.assertEqual(exit_code, 1)


if __name__ == "__main__":
    unittest.main()
