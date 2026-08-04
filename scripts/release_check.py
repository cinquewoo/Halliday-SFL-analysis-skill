#!/usr/bin/env python3
"""Check public-plugin structure, metadata consistency, and release hygiene."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "halliday-sfl-analysis-skill"
SKILL = PLUGIN / "skills" / "halliday-sfl-analyst"
CORE_VERSION = re.compile(r"^(\d+\.\d+\.\d+)(?:\+codex\.\d{14})?$")
VERSION_MARKER = re.compile(r"<!--\s*plugin-version:\s*([^\s]+)\s*-->")
FORBIDDEN_EXTENSIONS = {".pdf", ".ppt", ".pptx", ".epub", ".doc", ".docx", ".sqlite", ".sqlite3", ".db"}
FORBIDDEN_PARTS = {
    "__pycache__",
    "node_modules",
    ".tmp",
    "tmp",
    "build",
    "dist",
    "private-sources",
}
PLACEHOLDER_HOMES = {"example", "username", "user", "name", "you"}
MAX_PUBLIC_FILE_BYTES = 2_000_000


def load_json(path: Path) -> object:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def core_version(value: object, label: str, errors: list[str]) -> str:
    if not isinstance(value, str):
        fail(errors, f"{label} must be a string")
        return ""
    match = CORE_VERSION.fullmatch(value)
    if not match:
        fail(errors, f"{label} has unsupported version {value!r}")
        return ""
    return match.group(1)


def check_skill_frontmatter(errors: list[str]) -> None:
    path = SKILL / "SKILL.md"
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, flags=re.DOTALL)
    if not match:
        fail(errors, "SKILL.md is missing YAML frontmatter")
        return
    frontmatter = match.group(1)
    if "name: halliday-sfl-analyst" not in frontmatter:
        fail(errors, "SKILL.md frontmatter name is inconsistent")
    description = re.search(r"^description:\s*(.+)$", frontmatter, flags=re.MULTILINE)
    if not description or len(description.group(1).strip()) < 40:
        fail(errors, "SKILL.md needs a substantive one-line description")
    for required in ("**explain**", "**annotate**", "**research**"):
        if required not in text:
            fail(errors, f"SKILL.md is missing work mode {required}")


def check_metadata(errors: list[str]) -> None:
    manifest = load_json(PLUGIN / ".codex-plugin" / "plugin.json")
    marketplace = load_json(ROOT / ".agents" / "plugins" / "marketplace.json")
    package = load_json(ROOT / "package.json")
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        fail(errors, "plugin manifest must be an object")
        return
    required_manifest = {
        "name",
        "version",
        "description",
        "author",
        "homepage",
        "repository",
        "keywords",
        "skills",
        "interface",
    }
    missing_manifest = sorted(required_manifest - manifest.keys())
    if missing_manifest:
        fail(errors, f"plugin manifest is missing: {', '.join(missing_manifest)}")
    if manifest.get("name") != "halliday-sfl-analysis-skill":
        fail(errors, "plugin manifest name is inconsistent")
    if manifest.get("skills") != "./skills/":
        fail(errors, "plugin manifest skills path must be './skills/'")
    interface = manifest.get("interface")
    if not isinstance(interface, dict):
        fail(errors, "plugin manifest interface must be an object")
    else:
        prompts = interface.get("defaultPrompt")
        if (
            not isinstance(prompts, list)
            or not 1 <= len(prompts) <= 3
            or any(not isinstance(prompt, str) or len(prompt) > 128 for prompt in prompts)
        ):
            fail(errors, "plugin starter prompts must contain 1-3 strings of at most 128 chars")
    manifest_core = core_version(manifest.get("version"), "plugin manifest", errors)
    versions = {
        "pyproject.toml": pyproject.get("project", {}).get("version"),
        "package.json": package.get("version") if isinstance(package, dict) else None,
    }
    for label, value in versions.items():
        if core_version(value, label, errors) != manifest_core:
            fail(errors, f"{label} version {value!r} does not match {manifest_core!r}")
    for readme_name in ("README.md", "README.zh-CN.md"):
        text = (ROOT / readme_name).read_text(encoding="utf-8")
        marker = VERSION_MARKER.search(text)
        if not marker or marker.group(1) != manifest_core:
            fail(errors, f"{readme_name} plugin-version marker must be {manifest_core}")
    plugins = marketplace.get("plugins") if isinstance(marketplace, dict) else None
    if not isinstance(plugins, list) or len(plugins) != 1:
        fail(errors, "marketplace must contain exactly one plugin entry")
    else:
        entry = plugins[0]
        if entry.get("name") != manifest.get("name"):
            fail(errors, "marketplace and manifest plugin names differ")
        source = entry.get("source", {})
        if source.get("source") != "local" or source.get("path") != "./plugins/halliday-sfl-analysis-skill":
            fail(errors, "marketplace plugin source path is inconsistent")


def public_paths() -> list[Path]:
    """Return tracked and publishable untracked paths, excluding ignored private data."""

    result = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [ROOT / item.decode() for item in result.stdout.split(b"\0") if item]


def check_public_tree(errors: list[str]) -> None:
    for path in public_paths():
        relative = path.relative_to(ROOT)
        if any(
            part in FORBIDDEN_PARTS or part.endswith(".egg-info")
            for part in relative.parts
        ):
            fail(errors, f"temporary/private path must not be published: {relative}")
            continue
        if path.is_symlink():
            if not path.resolve().exists() or ROOT not in path.resolve().parents:
                fail(errors, f"symlink escapes or is broken: {relative}")
            continue
        if not path.is_file():
            continue
        if not path.exists():
            continue
        if path.suffix.lower() in FORBIDDEN_EXTENSIONS:
            fail(errors, f"source binary/private index must not be published: {relative}")
        size = path.stat().st_size
        if size > MAX_PUBLIC_FILE_BYTES:
            fail(errors, f"public file exceeds 2 MB: {relative}")
        if size > MAX_PUBLIC_FILE_BYTES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for match in re.finditer(r"/(?:Users|home)/([A-Za-z0-9._-]+)/", text):
            if match.group(1).casefold() not in PLACEHOLDER_HOMES:
                fail(errors, f"private absolute home path in {relative}: {match.group(0)!r}")
        if re.search(
            r"[A-Za-z]:\\Users\\(?!example\\|username\\|user\\)",
            text,
            re.IGNORECASE,
        ):
            fail(errors, f"private Windows home path in {relative}")


def main() -> int:
    errors: list[str] = []
    required = (
        PLUGIN / ".codex-plugin" / "plugin.json",
        SKILL / "SKILL.md",
        SKILL / "references" / "gm-annotation-v3.schema.json",
        SKILL / "references" / "gm-candidate-rules.yaml",
        SKILL / "scripts" / "validate_gm_annotation.py",
        SKILL / "tests" / "fixtures" / "gm-gold-v3.json",
    )
    for path in required:
        if not path.exists():
            fail(errors, f"required release file is missing: {path.relative_to(ROOT)}")
    if not errors:
        check_skill_frontmatter(errors)
        check_metadata(errors)
    check_public_tree(errors)
    if errors:
        for message in errors:
            print(f"ERROR: {message}", file=sys.stderr)
        print(f"Release check failed with {len(errors)} error(s)", file=sys.stderr)
        return 1
    for pending in ("LICENSE", "CITATION.cff"):
        if not (ROOT / pending).exists():
            print(f"WARN: {pending} awaits repository-owner confirmation")
    print("Release check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
