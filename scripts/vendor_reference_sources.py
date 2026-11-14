#!/usr/bin/env python3
"""Import exact Git-tracked upstream sources into AETHERION as independent references.

All original tracked files (including binaries and dotfiles) are copied by blob
SHA, with original file mode preserved. Not a submodule, README link, or
dependency installation. Requires git, Python >=3.11, and network for import.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "Các mã nguồn mở tham khảo"
LOCK = VENDOR / "SOURCES.lock.json"


def run(*args: str, cwd: Path | None = None) -> bytes:
    return subprocess.check_output(list(args), cwd=cwd, stderr=subprocess.PIPE)


def git_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def get_raw(path: Path, mode: str) -> bytes:
    if mode == "120000":
        return os.fsencode(os.readlink(path))
    return path.read_bytes()


def safe_path(base: Path, path: str) -> Path:
    parts = path.replace("\\", "/").split("/")
    if not parts or any(p in ("", ".", "..", ".git") for p in parts):
        raise ValueError("Untrusted Git path: " + repr(path))
    return base.joinpath(*parts)


def verify_source(source: dict) -> dict:
    name = source["name"]
    dest = VENDOR / name
    manifest_file = VENDOR / ("MANIFEST_" + name + ".json")
    if not dest.is_dir() or not manifest_file.exists():
        raise RuntimeError(name + " has NOT been imported and verified")
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    if manifest["repository"] != source["repo"] or manifest["revision"] != source["commit"]:
        raise RuntimeError(name + " has wrong source revision")
    files = manifest["files"]
    if len(files) != source["expected_files"]:
        raise RuntimeError(name + " has incorrect tracked file count")
    expected = {file["path"] for file in files}
    for file in files:
        src = safe_path(dest, file["path"])
        if not (src.is_file() or src.is_symlink()):
            raise RuntimeError(name + " is missing " + file["path"])
        sha = git_sha(get_raw(src, file["mode"]))
        if sha != file["sha"]:
            raise RuntimeError(name + " modified or corrupted " + file["path"])
        if file["mode"] == "120000" and not src.is_symlink():
            raise RuntimeError(name + " lost symlink mode " + file["path"])
    actual = {str(x.relative_to(dest)).replace(os.sep, "/")
              for x in dest.rglob("*") if x.is_file() or x.is_symlink()}
    if actual != expected:
        raise RuntimeError(name + " extra/missing files: " + str(sorted(actual ^ expected)[:20]))
    return {"name": name, "revision": source["commit"], "status": "VERIFIED",
            "files": len(files)}


def tree_entries(gitdir: Path, sha: str) -> list[dict[str, str]]:
    output = run("git", "-C", str(gitdir), "ls-tree", "-rz", "--full-tree", sha)
    entries = []
    for row in output.split(b"\0"):
        if not row:
            continue
        fields, rawname = row.split(b"\t", 1)
        mode, kind, blob = fields.decode("ascii").split(" ")
        if kind != "blob":
            raise RuntimeError("Gitlinks/submodules are not supported as complete sources: "
                               + rawname.decode("utf-8", errors="replace"))
        path = rawname.decode("utf-8", errors="surrogateescape")
        safe_path(Path("."), path)
        entries.append({"path": path, "sha": blob, "mode": mode})
    return entries


def import_source(source: dict) -> dict:
    name = source["name"]
    dest = VENDOR / name
    if dest.exists() or dest.is_symlink():
        print("Existing source; checking exact SHA:", name, flush=True)
        return verify_source(source)

    with tempfile.TemporaryDirectory(prefix="aetherion-source-") as tmpname:
        clone_dir = Path(tmpname) / "repository"
        url = "https://github.com/" + source["repo"] + ".git"
        print("Cloning upstream:", url, source["commit"], flush=True)
        subprocess.check_call([
            "git", "clone", "--quiet", "--depth=1", "--no-checkout",
            "--branch", source["branch"], url, str(clone_dir),
        ])
        try:
            run("git", "-C", str(clone_dir), "cat-file", "-e",
                source["commit"] + "^{commit}")
        except subprocess.CalledProcessError:
            subprocess.check_call([
                "git", "-C", str(clone_dir), "fetch", "--quiet", "--depth=1",
                "origin", source["commit"],
            ])

        entries = tree_entries(clone_dir, source["commit"])
        if len(entries) != source["expected_files"]:
            raise RuntimeError(
                name + ": upstream tracked file count changed from lock "
                + str(source["expected_files"]) + " to " + str(len(entries))
            )

        # Do not use git archive: export-ignore can silently omit tracked files.
        stage = VENDOR / (".importing-" + name)
        if stage.exists():
            raise RuntimeError("Stale import staging directory: " + str(stage))
        stage.mkdir(parents=True)
        try:
            process = subprocess.Popen(
                ["git", "-C", str(clone_dir), "cat-file", "--batch"],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            assert process.stdin is not None and process.stdout is not None
            try:
                for entry in entries:
                    target = safe_path(stage, entry["path"])
                    target.parent.mkdir(parents=True, exist_ok=True)
                    process.stdin.write((entry["sha"] + "\n").encode("ascii"))
                    process.stdin.flush()
                    header = process.stdout.readline().decode("ascii").strip().split(" ")
                    if len(header) != 3 or header[0] != entry["sha"] or header[1] != "blob":
                        raise RuntimeError("Unexpected git cat-file header: " + repr(header))
                    data = process.stdout.read(int(header[2]))
                    if process.stdout.read(1) != b"\n" or git_sha(data) != entry["sha"]:
                        raise RuntimeError("Corrupted upstream Git blob: " + entry["path"])
                    if entry["mode"] == "120000":
                        os.symlink(os.fsdecode(data), target)
                    else:
                        target.write_bytes(data)
                        if entry["mode"] == "100755":
                            target.chmod(target.stat().st_mode | stat.S_IXUSR
                                         | stat.S_IXGRP | stat.S_IXOTH)
                process.stdin.close()
                if process.wait() != 0:
                    raise RuntimeError("git cat-file --batch failed")
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()

            os.rename(stage, dest)
            manifest = {"name": name, "repository": source["repo"],
                        "revision": source["commit"], "tracked_files": len(entries),
                        "files": entries}
            (VENDOR / ("MANIFEST_" + name + ".json")).write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        finally:
            if stage.exists():
                shutil.rmtree(stage)

    return verify_source(source)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["import", "verify"])
    parser.add_argument("--only", nargs="*", help="Source names (default: all)")
    args = parser.parse_args()
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    sources = [s for s in lock["sources"] if not args.only or s["name"] in args.only]
    if args.only and {s["name"] for s in sources} != set(args.only):
        parser.error("Unknown source name requested")
    report = []
    for source in sources:
        try:
            result = import_source(source) if args.command == "import" else verify_source(source)
            report.append(result)
            print("VERIFIED:", result["name"], result["files"], "files", flush=True)
        except Exception as exc:
            print("FAILED:", source["name"], str(exc), file=sys.stderr, flush=True)
            return 1
    if args.command == "import":
        (VENDOR / "IMPORT_REPORT.json").write_text(
            json.dumps({"entries": report, "note": "Tracked Git blobs only, no Git metadata"}, indent=2)
            + "\n", encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
