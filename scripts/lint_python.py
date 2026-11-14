#!/usr/bin/env python3
"""Deterministic Python syntax and indentation lint checker for AETHERION."""

from __future__ import annotations

import argparse
import ast
import io
import sys
import tokenize
from pathlib import Path

EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "build",
    "dist",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}


def discover_python_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(root.rglob("*.py")):
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        if path.is_file():
            files.append(path)
    return files


def check_file(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        source = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        return [f"{path}: UTF-8 decode error: {exc}"]

    try:
        ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        errors.append(f"{path}:{exc.lineno or 0}:{exc.offset or 0}: SyntaxError: {exc.msg}")
        return errors

    try:
        for _ in tokenize.generate_tokens(io.StringIO(source).readline):
            pass
    except (tokenize.TokenError, IndentationError, TabError) as exc:
        errors.append(f"{path}: Token/Indentation error: {exc}")

    return errors


def lint_paths(paths: list[Path]) -> tuple[int, list[str]]:
    all_errors: list[str] = []
    checked = 0
    for target in paths:
        if target.is_dir():
            for py_file in discover_python_files(target):
                checked += 1
                all_errors.extend(check_file(py_file))
        elif target.is_file():
            checked += 1
            all_errors.extend(check_file(target))
        else:
            all_errors.append(f"{target}: path does not exist")
    return checked, all_errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check Python syntax and indentation.")
    parser.add_argument(
        "paths",
        nargs="*",
        default=["."],
        help="Files or directories to check (defaults to repository root).",
    )
    args = parser.parse_args(argv)
    targets = [Path(p) for p in args.paths]
    checked, errors = lint_paths(targets)
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        print(f"FAIL: Checked {checked} Python file(s), found {len(errors)} error(s).", file=sys.stderr)
        return 1
    print(f"OK: Checked {checked} Python file(s), 0 errors.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
