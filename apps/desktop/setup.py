"""Include the *actual repository JSON* in built AETHERION Desktop wheels.

Editable checkouts read science sources from the same repository; wheel builds
copy original JSON bytes into package data, never invent missing NASA articles.
The included audit manifest records file-level SHA-256 (of the JSON copies)
but does NOT certify independent integrity of the source NASA PDF binaries.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py as _build_py

ROOT = Path(__file__).resolve().parents[2]
SOURCES = ROOT / "knowledge"
PACKAGE = Path("aetherion_desktop/features/demo/data")


class build_py(_build_py):
    """Copy complete locally present source JSON into distributable wheel."""

    def run(self):
        super().run()
        target = Path(self.build_lib) / PACKAGE
        source_sets = (
            (SOURCES / "nasa/cliff_119_2023/records", target / "cliff",
             "CLIFF-???.json", "cliff"),
            (SOURCES / "nasa/hazards", target / "hazards",
             "*.json", "hazards"),
            (SOURCES / "symptoms", target,
             "ASTRA_819_REFERENCE.json", "symptoms"),
        )
        bundled = []
        states = {"cliff": 0, "hazards": 0, "symptoms": 0}
        for origin, output, glob, kind in source_sets:
            if not origin.is_dir():
                continue
            output.mkdir(parents=True, exist_ok=True)
            for path in sorted(origin.glob(glob)):
                if not path.is_file() or path.stat().st_size > 2_000_000:
                    continue
                filename = "symptoms.json" if kind == "symptoms" else path.name
                content = path.read_bytes()
                dest = output / filename
                dest.write_bytes(content)
                states[kind] += 1
                bundled.append({
                    "path": dest.relative_to(target).as_posix(),
                    "sha256": hashlib.sha256(content).hexdigest(),
                    "size": len(content),
                    "kind": kind,
                })
        target.mkdir(parents=True, exist_ok=True)
        summary = {
            "schema": "aetherion-nasa-demo-package-v1",
            "source": "AETHERION checkout knowledge JSON (not verified NASA PDFs)",
            "counts": states,
            "files": bundled,
            "missing_cliff_count": max(0, 119 - states["cliff"]),
            "no_synthetic_measurements": True,
        }
        manifest = target / "snapshot.json"
        manifest.write_text(json.dumps(summary, indent=2) + "\n",encoding="utf-8")
        self._science_outputs = [str(target / item["path"]) for item in bundled]
        self._science_outputs.append(str(manifest))

    def get_outputs(self, include_bytecode=1):
        return super().get_outputs(include_bytecode) + list(
            getattr(self, "_science_outputs", ())
        )


setup(cmdclass={"build_py": build_py})
