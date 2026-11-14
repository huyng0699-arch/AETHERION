#!/usr/bin/env python3
"""Read-only Windows package inventory for AETHERION (Q-0009).

Report actual file sizes, SHA-256 and imported PE DLL names. No execution,
network requests, invented build artifacts, or assumption about Windows runtime.
A source checkout is not a Windows release package.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import struct

PE_SUFFIXES = frozenset({".exe", ".dll", ".pyd"})
MAX_IMPORTS = 2048


def _u16(data: bytes, offset: int) -> int:
    return struct.unpack_from("<H", data, offset)[0]


def _u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def pe_imports(path: Path) -> tuple[str, list[str]]:
    """Read the PE Import Directory, using file offsets with strict bounds.

    This reads imported names only (not delay-load imports or runtime LoadLibrary),
    so absence of a DLL here never proves a runtime dependency is unnecessary.
    """
    length = path.stat().st_size
    with path.open("rb") as handle:
        header = handle.read(min(length, 65536))
        if len(header) < 64 or header[:2] != b"MZ":
            return "NOT_PE", []
        try:
            pe = _u32(header, 0x3C)
            if pe < 64 or pe + 24 > len(header) or header[pe:pe + 4] != b"PE\x00\x00":
                return "INVALID_PE", []
            sections_count = _u16(header, pe + 6)
            optional_length = _u16(header, pe + 20)
            optional = pe + 24
            if sections_count > 96 or optional + optional_length > len(header):
                return "INVALID_PE", []
            magic = _u16(header, optional)
            if magic not in (0x10B, 0x20B):
                return "INVALID_PE", []
            directory_base = optional + (96 if magic == 0x10B else 112)
            directory = directory_base + 8
            if directory + 8 > optional + optional_length:
                return "INVALID_PE", []
            import_rva, import_size = struct.unpack_from("<II", header, directory)
            if not import_rva or not import_size:
                return "PARSED_NO_IMPORTS", []
            if import_size > 2_000_000:
                return "INVALID_PE", []
            table_start = optional + optional_length
            sections = []
            for index in range(sections_count):
                section = table_start + index * 40
                if section + 40 > len(header):
                    return "INVALID_PE", []
                virtual_size = _u32(header, section + 8)
                virtual_address = _u32(header, section + 12)
                raw_size = _u32(header, section + 16)
                raw_pointer = _u32(header, section + 20)
                sections.append((virtual_address, max(virtual_size, raw_size), raw_pointer, raw_size))

            def offset_for(rva: int) -> int:
                for virtual_address, virtual_extent, raw_pointer, raw_size in sections:
                    delta = rva - virtual_address
                    if 0 <= delta < virtual_extent and delta < raw_size:
                        file_offset = raw_pointer + delta
                        if file_offset < length:
                            return file_offset
                raise ValueError("unmapped PE import RVA")

            start = offset_for(import_rva)
            names: list[str] = []
            for index in range(min(MAX_IMPORTS, import_size // 20)):
                off = start + index * 20
                if off + 20 > length:
                    return "INVALID_PE", []
                handle.seek(off)
                desc = handle.read(20)
                if len(desc) != 20:
                    return "INVALID_PE", []
                if desc == b"\x00" * 20:
                    return "PARSED_IMPORTS", sorted(set(names), key=str.casefold)
                name_rva = struct.unpack_from("<I", desc, 12)[0]
                handle.seek(offset_for(name_rva))
                name_bytes = handle.read(260).split(b"\x00", 1)[0]
                name = name_bytes.decode("ascii", errors="strict")
                if not name or len(name_bytes) > 259 or any(ord(c) < 32 for c in name):
                    return "INVALID_PE", []
                names.append(name)
            return "INVALID_PE", []  # unterminated directory: fail closed
        except (ValueError, UnicodeError, struct.error, OSError):
            return "INVALID_PE", []


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def audit_package(root: Path) -> dict:
    """Create a deterministic inventory; reject path escapes and missing roots."""
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Package root must be an existing directory")
    binaries = []
    ignored_symlinks = []
    total_bytes = 0
    total_files = 0
    exe_count = 0
    file_names: set[str] = set()
    for directory, dirs, files in os.walk(root, followlinks=False):
        parent = Path(directory)
        for name in list(dirs):
            if (parent / name).is_symlink():
                ignored_symlinks.append((parent / name).relative_to(root).as_posix())
                dirs.remove(name)
        for name in files:
            path = parent / name
            rel = path.relative_to(root).as_posix()
            if path.is_symlink():
                ignored_symlinks.append(rel)
                continue
            if not path.is_file():
                continue
            size = path.stat().st_size
            total_files += 1
            total_bytes += size
            file_names.add(name.casefold())
            if path.suffix.lower() not in PE_SUFFIXES:
                continue
            if path.suffix.lower() == ".exe":
                exe_count += 1
            pe_state, imports = pe_imports(path)
            binaries.append({"path": rel, "size_bytes": size, "sha256": sha256_file(path),
                             "pe_state": pe_state, "imported_dlls": imports})
    binaries.sort(key=lambda r: r["path"].casefold())
    qt_binaries = [x for x in binaries if x["path"].split("/")[-1].lower().startswith(
        ("qt5", "qt6", "pyside", "shiboken"))]
    qt_imports = sorted({dll for b in binaries for dll in b["imported_dlls"]
                         if dll.casefold().startswith(("qt5", "qt6", "pyside", "shiboken"))},
                        key=str.casefold)
    missing_qt = [name for name in qt_imports if name.casefold() not in file_names]
    invalid_pe = [b["path"] for b in binaries if b["pe_state"] in {"NOT_PE", "INVALID_PE"}]
    return {
        "schema_version": "1.0", "package_root": str(root),
        "provenance": "LOCAL_FILES_ACTUALLY_READ_NOT_RELEASE_CERTIFICATION",
        "reader": "stdlib PE import table; excludes delay-load/dynamic LoadLibrary",
        "total_files": total_files, "total_bytes": total_bytes,
        "binary_count": len(binaries), "binary_bytes": sum(b["size_bytes"] for b in binaries),
        "exe_count": exe_count, "binaries": binaries,
        "qt_binary_count": len(qt_binaries),
        "qt_binary_bytes": sum(x["size_bytes"] for x in qt_binaries),
        "qt_imports": qt_imports, "qt_imports_missing_from_package": missing_qt,
        "invalid_pe_files": invalid_pe, "ignored_symlinks": sorted(ignored_symlinks),
        "release_assessment": "INCOMPLETE_NO_EXE" if not exe_count else
                              "INSPECTION_ONLY_NOT_WINDOWS_ACCEPTANCE",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package_root", type=Path, help="Built Windows --onedir output (not source tree)")
    parser.add_argument("--output", type=Path, help="Optional JSON evidence file outside the package")
    args = parser.parse_args(argv)
    try:
        report = audit_package(args.package_root)
        rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            output = args.output.resolve()
            if output.is_relative_to(Path(report["package_root"])):
                parser.error("Output must be outside the scanned package for reproducibility")
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        # A missing EXE or corrupt PE must never be interpreted as package PASS.
        return 2 if report["exe_count"] == 0 or report["invalid_pe_files"] else 0
    except (OSError, ValueError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
