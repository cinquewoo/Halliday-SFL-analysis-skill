#!/usr/bin/env python3
"""Regression tests for private source archive safety using synthetic files."""

from __future__ import annotations

import contextlib
import io
import json
import stat
import tempfile
from pathlib import Path

import source_archive


def mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


def main() -> int:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / "synthetic.txt"
        source.write_text("synthetic fixture only\n", encoding="utf-8")
        source.chmod(0o644)
        manifest = root / "manifest.json"
        manifest.write_text(
            json.dumps(
                {
                    "version": 1,
                    "sources": [
                        {
                            "id": "safe-source",
                            "title": "Synthetic Source",
                            "path": str(source),
                            "kind": "txt",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        archive = root / "private-archive"
        output_manifest = root / "archived.local.json"
        with contextlib.redirect_stdout(io.StringIO()):
            source_archive.archive_sources(
                manifest, archive, output_manifest, "copy"
            )
        archived = json.loads(output_manifest.read_text(encoding="utf-8"))
        archived_path = Path(archived["sources"][0]["path"])
        assert archived_path.read_text(encoding="utf-8") == "synthetic fixture only\n"
        assert mode(archive) == 0o700
        assert mode(archived_path.parent) == 0o700
        assert mode(archived_path) == 0o600
        assert source_archive.verify_manifest(output_manifest) == 0

        unsafe = root / "unsafe.json"
        unsafe.write_text(
            json.dumps(
                {
                    "version": 1,
                    "sources": [
                        {
                            "id": "../../outside",
                            "title": "Unsafe Synthetic Source",
                            "path": str(source),
                            "kind": "txt",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        try:
            source_archive.load_manifest(unsafe)
        except ValueError as error:
            assert "Unsafe source id" in str(error)
        else:
            raise AssertionError("Path-traversing source IDs must be rejected")

        public_archive = root / "public-archive"
        public_archive.mkdir(mode=0o755)
        public_archive.chmod(0o755)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                source_archive.archive_sources(
                    manifest, public_archive, root / "public.json", "copy"
                )
        except ValueError as error:
            assert "mode 0700" in str(error)
        else:
            raise AssertionError("A non-private archive destination must be rejected")
        assert mode(public_archive) == 0o755
    print("source_archive regression tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
