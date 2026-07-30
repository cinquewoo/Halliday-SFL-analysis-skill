#!/usr/bin/env python3
"""Archive and verify user-supplied Halliday PDF/PPTX/EPUB/TXT sources privately."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


SUPPORTED_KINDS = {"pdf", "pptx", "epub", "txt"}
SOURCE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def infer_kind(path: Path, declared: object | None = None) -> str:
    kind = str(declared or path.suffix.lstrip(".")).lower()
    if kind not in SUPPORTED_KINDS:
        raise ValueError(f"Unsupported source type for {path}: {kind or 'unknown'}")
    return kind


def load_manifest(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("version") not in (1, 2) or not isinstance(data.get("sources"), list):
        raise ValueError("Manifest must contain version 1 or 2 and a sources array")
    seen: set[str] = set()
    for raw in data["sources"]:
        if not isinstance(raw, dict):
            raise ValueError(f"Manifest source must be an object: {raw!r}")
        missing = [key for key in ("id", "title", "path") if not raw.get(key)]
        if missing:
            raise ValueError(f"Manifest source is missing {', '.join(missing)}: {raw!r}")
        source_id = str(raw["id"])
        if not SOURCE_ID_RE.fullmatch(source_id):
            raise ValueError(
                f"Unsafe source id {source_id!r}; use 1-128 ASCII letters, "
                "digits, dots, underscores, or hyphens, beginning with a letter or digit"
            )
        if source_id in seen:
            raise ValueError(f"Duplicate source id: {source_id}")
        seen.add(source_id)
    return data


def atomic_json_write(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as output:
            json.dump(data, output, ensure_ascii=False, indent=2)
            output.write("\n")
        temporary.replace(path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def clone_or_copy(source: Path, destination: Path, mode: str) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    destination.parent.chmod(0o700)
    temporary = destination.with_name(f".{destination.name}.{os.getpid()}.tmp")
    temporary.unlink(missing_ok=True)
    method = "copy"
    try:
        if mode in ("auto", "clone") and Path("/bin/cp").is_file():
            result = subprocess.run(
                ["/bin/cp", "-c", "-p", str(source), str(temporary)],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                method = "clone"
            elif mode == "clone":
                raise OSError(result.stderr.strip() or "APFS clone failed")
        if not temporary.exists():
            shutil.copy2(source, temporary)
        temporary.chmod(0o600)
        temporary.replace(destination)
        destination.chmod(0o600)
        return method
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def archive_sources(
    manifest_path: Path, destination: Path, output_manifest: Path, mode: str
) -> None:
    data = load_manifest(manifest_path)
    destination = destination.expanduser().resolve()
    if destination.exists():
        if not destination.is_dir():
            raise ValueError(f"Archive destination is not a directory: {destination}")
        if stat.S_IMODE(destination.stat().st_mode) & 0o077:
            raise ValueError(
                f"Archive destination must already be private (mode 0700): {destination}"
            )
    else:
        destination.mkdir(parents=True, mode=0o700)
    archived_sources: list[dict[str, object]] = []
    archived_at = datetime.now(timezone.utc).isoformat()

    for number, raw in enumerate(data["sources"], start=1):
        source = Path(str(raw["path"])).expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError(f"Missing source for {raw['id']}: {source}")
        kind = infer_kind(source, raw.get("kind"))
        digest = sha256_file(source)
        target = (
            destination / str(raw["id"]) / f"{digest}.{kind}"
        ).resolve(strict=False)
        if not target.is_relative_to(destination):
            raise ValueError(f"Archive target escapes destination: {target}")
        copy_method = "existing"
        if not target.is_file():
            copy_method = clone_or_copy(source, target, mode)
        target_digest = sha256_file(target)
        if target_digest != digest:
            target.unlink(missing_ok=True)
            raise OSError(f"Integrity check failed after archiving {raw['id']}")
        target.parent.chmod(0o700)
        target.chmod(0o600)

        archived = dict(raw)
        archived.update(
            {
                "kind": kind,
                "path": str(target),
                "original_path": str(source),
                "original_filename": source.name,
                "sha256": digest,
                "byte_size": source.stat().st_size,
                "archived_at": archived_at,
            }
        )
        archived_sources.append(archived)
        print(
            f"[{number}/{len(data['sources'])}] {raw['id']}: "
            f"{copy_method}, sha256={digest[:12]}..., {source.stat().st_size} bytes",
            flush=True,
        )

    output = {
        key: value
        for key, value in data.items()
        if key not in {"version", "archive_root", "generated_at", "sources"}
    }
    output.update(
        {
            "version": 2,
            "archive_root": str(destination),
            "generated_at": archived_at,
            "sources": archived_sources,
        }
    )
    atomic_json_write(output_manifest, output)
    print(f"Archived manifest written to {output_manifest}")


def verify_manifest(manifest_path: Path) -> int:
    data = load_manifest(manifest_path)
    failures = 0
    for raw in data["sources"]:
        path = Path(str(raw["path"])).expanduser()
        expected = str(raw.get("sha256") or "")
        if not path.is_file():
            failures += 1
            print(f"MISSING {raw['id']}: {path}")
            continue
        actual = sha256_file(path)
        if not expected:
            failures += 1
            print(f"NO_DIGEST {raw['id']}: sha256={actual}")
        elif actual != expected:
            failures += 1
            print(f"MISMATCH {raw['id']}: expected={expected} actual={actual}")
        else:
            print(f"OK {raw['id']}: sha256={actual}")
    return 1 if failures else 0


def list_manifest(manifest_path: Path) -> None:
    data = load_manifest(manifest_path)
    for raw in data["sources"]:
        print(
            json.dumps(
                {
                    "id": raw["id"],
                    "title": raw["title"],
                    "kind": raw.get("kind") or Path(str(raw["path"])).suffix.lstrip("."),
                    "byte_size": raw.get("byte_size"),
                    "sha256": raw.get("sha256"),
                    "path": raw["path"],
                },
                ensure_ascii=False,
            )
        )


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)

    archive = commands.add_parser("archive", help="Create a content-addressed private archive")
    archive.add_argument("--manifest", type=Path, required=True)
    archive.add_argument("--destination", type=Path, required=True)
    archive.add_argument("--output-manifest", type=Path, required=True)
    archive.add_argument("--copy-mode", choices=("auto", "clone", "copy"), default="auto")

    verify = commands.add_parser("verify", help="Verify every archived SHA-256 digest")
    verify.add_argument("--manifest", type=Path, required=True)

    listing = commands.add_parser("list", help="List sources in a manifest")
    listing.add_argument("--manifest", type=Path, required=True)
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "archive":
            archive_sources(args.manifest, args.destination, args.output_manifest, args.copy_mode)
        elif args.command == "verify":
            return verify_manifest(args.manifest)
        elif args.command == "list":
            list_manifest(args.manifest)
    except (FileNotFoundError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
