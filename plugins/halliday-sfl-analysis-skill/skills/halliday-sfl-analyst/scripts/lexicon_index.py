#!/usr/bin/env python3
"""Build and query a private index of bracket-headed Chinese dictionaries."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
import tempfile
import unicodedata
from pathlib import Path


SCHEMA_VERSION = 1
MAX_RESULTS = 50
MAX_ENTRY_CHARS = 4000
SUPPORTED_FORMATS = {"bracket-entry-lines"}
ENTRY_RE = re.compile(r"^\s*【(?P<headword>[^】\n]+)】(?P<body>.*)$")
SECTION_RE = re.compile(r"^\s*〔(?P<section>[^〕\n]+)〕\s*$")
POS_RE = re.compile(r"(?:〈([^〉]{1,12})〉|（([^）]{1,12})）)")
SUPERSCRIPT_DIGITS = "⁰¹²³⁴⁵⁶⁷⁸⁹"
KNOWN_POS = {
    "名",
    "动",
    "形",
    "副",
    "介",
    "连",
    "代",
    "数",
    "量",
    "助",
    "叹",
    "拟声",
    "区别",
    "词组",
}
CODEX_HOME = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()
GLOBAL_LEXICON_ROOT = (
    CODEX_HOME / "halliday-sfl-analysis-sources" / "lexicons"
)


def configured_path(
    environment_name: str, candidates: list[Path], fallback: Path
) -> Path:
    configured = os.environ.get(environment_name)
    if configured:
        return Path(configured).expanduser()
    return next((path for path in candidates if path.is_file()), fallback)


DEFAULT_MANIFEST = configured_path(
    "HALLIDAY_SFL_LEXICON_MANIFEST",
    [
        Path(".agents/halliday-lexicons.archived.local.json"),
        Path(".agents/halliday-lexicons.local.json"),
        GLOBAL_LEXICON_ROOT / "manifest.local.json",
    ],
    Path(".agents/halliday-lexicons.local.json"),
)
DEFAULT_DATABASE = configured_path(
    "HALLIDAY_SFL_LEXICON_DB",
    [
        Path(".agents/cache/halliday-lexicons.sqlite3"),
        GLOBAL_LEXICON_ROOT / "index.sqlite3",
    ],
    Path(".agents/cache/halliday-lexicons.sqlite3"),
)
SCHEMA = f"""
PRAGMA foreign_keys = ON;
CREATE TABLE metadata (schema_version INTEGER NOT NULL);
INSERT INTO metadata VALUES ({SCHEMA_VERSION});
CREATE TABLE lexicon_source (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    full_citation TEXT NOT NULL,
    path TEXT NOT NULL,
    format TEXT NOT NULL,
    entry_count INTEGER NOT NULL,
    file_size INTEGER NOT NULL,
    mtime_ns INTEGER NOT NULL,
    sha256 TEXT NOT NULL
);
CREATE TABLE entry (
    rowid INTEGER PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES lexicon_source(id),
    entry_number INTEGER NOT NULL,
    headword TEXT NOT NULL,
    normalized_headword TEXT NOT NULL,
    body TEXT NOT NULL,
    raw_entry TEXT NOT NULL,
    line_start INTEGER NOT NULL,
    line_end INTEGER NOT NULL,
    section TEXT NOT NULL,
    sense_marker TEXT NOT NULL,
    editorial_asterisk INTEGER NOT NULL,
    definition_status TEXT NOT NULL,
    pos_labels TEXT NOT NULL,
    frequency_stars INTEGER NOT NULL,
    UNIQUE(source_id, entry_number)
);
CREATE INDEX entry_exact ON entry(normalized_headword, source_id);
CREATE INDEX entry_source_order ON entry(source_id, entry_number);
CREATE TABLE online_source (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    full_citation TEXT NOT NULL,
    homepage TEXT NOT NULL,
    query_url TEXT NOT NULL,
    results_url TEXT NOT NULL,
    usage_note TEXT NOT NULL
);
"""


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_headword(text: str) -> str:
    raw = text.strip()
    if raw.startswith("【") and raw.endswith("】"):
        raw = raw[1:-1].strip()
    raw = re.sub(rf"[*＊{SUPERSCRIPT_DIGITS}]+\Z", "", raw).strip()
    normalized = unicodedata.normalize("NFKC", raw)
    normalized = re.sub(r"\s+", "", normalized)
    return normalized.casefold()


def clean_text(text: str) -> str:
    return text.replace("\x00", " ").replace("\r\n", "\n").replace("\r", "\n")


def extract_pos_labels(body: str) -> list[str]:
    labels: list[str] = []
    for match in POS_RE.finditer(body[:160]):
        candidate = (match.group(1) or match.group(2) or "").strip()
        for label in re.split(r"[/、，,\s]+", candidate):
            if label in KNOWN_POS and label not in labels:
                labels.append(label)
    return labels


def classify_definition(body: str) -> str:
    compact = re.sub(r"\s+", "", body)
    if not compact:
        return "ENTRY_WITHOUT_DEFINITION"
    candidate = compact
    for match in POS_RE.finditer(compact[:160]):
        label_text = (match.group(1) or match.group(2) or "").strip()
        labels = re.split(r"[/、，,\s]+", label_text)
        if any(label in KNOWN_POS for label in labels):
            candidate = compact[match.end() :]
            break
    cross_reference = re.fullmatch(
        r"(?:"
        r"见下"
        r"|见(?:\d+页)?【[^】]+】(?:的?[^。]*)?"
        r"|参见(?:\d+页)?【[^】]+】(?:的?[^。]*)?"
        r"|同(?:“[^”]+”|\"[^\"]+\"|‘[^’]+’|'[^']+'|【[^】]+】)"
        r")[。.]?",
        candidate,
    )
    if len(candidate) <= 90 and cross_reference:
        return "CROSS_REFERENCE_ONLY"
    return "DEFINITION_PRESENT"


def parse_entries(path: Path) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    current_section = ""
    with path.open("r", encoding="utf-8-sig", errors="strict") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = clean_text(raw_line).rstrip("\n")
            section_match = SECTION_RE.match(line)
            if section_match:
                if current:
                    entries.append(current)
                    current = None
                current_section = section_match.group("section").strip()
                continue
            match = ENTRY_RE.match(line)
            if match:
                if current:
                    entries.append(current)
                headword = match.group("headword").strip()
                body = match.group("body").strip()
                marker_match = re.search(rf"([{SUPERSCRIPT_DIGITS}]+)\Z", headword)
                current = {
                    "entry_number": len(entries) + 1,
                    "headword": headword,
                    "normalized_headword": normalize_headword(headword),
                    "section": current_section,
                    "sense_marker": marker_match.group(1) if marker_match else "",
                    "editorial_asterisk": int(bool(re.search(r"[*＊]\Z", headword))),
                    "body_lines": [body] if body else [],
                    "raw_lines": [line],
                    "line_start": line_number,
                    "line_end": line_number,
                }
            elif current and line.strip():
                current["body_lines"].append(line.strip())  # type: ignore[union-attr]
                current["raw_lines"].append(line)  # type: ignore[union-attr]
                current["line_end"] = line_number
    if current:
        entries.append(current)

    for entry in entries:
        body = "\n".join(entry.pop("body_lines")).strip()  # type: ignore[arg-type]
        raw_entry = "\n".join(entry.pop("raw_lines")).strip()  # type: ignore[arg-type]
        entry["body"] = body
        entry["raw_entry"] = raw_entry
        entry["definition_status"] = classify_definition(body)
        entry["pos_labels"] = extract_pos_labels(body)
        entry["frequency_stars"] = body[:120].count("★")
    return entries


def load_manifest(path: Path) -> tuple[list[dict[str, object]], list[dict[str, str]]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("version") not in (1, 2) or not isinstance(data.get("sources"), list):
        raise ValueError("Manifest must contain version 1 or 2 and a sources array")

    seen: set[str] = set()
    sources: list[dict[str, object]] = []
    for raw in data["sources"]:
        required = ("id", "title", "full_citation", "path", "format")
        missing = [key for key in required if not raw.get(key)]
        if missing:
            raise ValueError(f"Lexicon source is missing {', '.join(missing)}: {raw!r}")
        source_id = str(raw["id"])
        if source_id in seen:
            raise ValueError(f"Duplicate lexicon source id: {source_id}")
        seen.add(source_id)
        source_format = str(raw["format"])
        if source_format not in SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported lexicon format for {source_id}: {source_format}")
        sources.append(
            {
                "id": source_id,
                "title": str(raw["title"]),
                "full_citation": str(raw["full_citation"]),
                "path": str(Path(str(raw["path"])).expanduser().resolve()),
                "format": source_format,
                "sha256": str(raw.get("sha256") or ""),
                "expected_entry_count": raw.get("expected_entry_count"),
            }
        )

    online_sources: list[dict[str, str]] = []
    online_seen: set[str] = set()
    for raw in data.get("online_sources", []):
        required = (
            "id",
            "title",
            "full_citation",
            "homepage",
            "query_url",
            "results_url",
            "usage_note",
        )
        missing = [key for key in required if not raw.get(key)]
        if missing:
            raise ValueError(f"Online source is missing {', '.join(missing)}: {raw!r}")
        source_id = str(raw["id"])
        if source_id in online_seen:
            raise ValueError(f"Duplicate online source id: {source_id}")
        online_seen.add(source_id)
        online_sources.append({key: str(raw[key]) for key in required})
    return sources, online_sources


def build_index(manifest: Path, database: Path) -> None:
    sources, online_sources = load_manifest(manifest)
    database.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        prefix=f".{database.name}.", suffix=".tmp", dir=database.parent, delete=False
    ) as handle:
        temporary = Path(handle.name)
    try:
        connection = sqlite3.connect(temporary)
        connection.executescript(SCHEMA)
        for source_number, source in enumerate(sources, start=1):
            source_path = Path(str(source["path"]))
            if not source_path.is_file():
                raise FileNotFoundError(f"Missing lexicon for {source['id']}: {source_path}")
            actual_digest = sha256_file(source_path)
            if source["sha256"] and source["sha256"] != actual_digest:
                raise ValueError(
                    f"SHA-256 mismatch for {source['id']}: "
                    f"expected {source['sha256']}, found {actual_digest}"
                )
            entries = parse_entries(source_path)
            if not entries:
                raise ValueError(f"No bracket-headed entries found in {source_path}")
            expected_entry_count = source.get("expected_entry_count")
            if expected_entry_count is not None and (
                not isinstance(expected_entry_count, int)
                or expected_entry_count < 1
                or len(entries) != expected_entry_count
            ):
                raise ValueError(
                    f"Entry-count mismatch for {source['id']}: "
                    f"expected {expected_entry_count}, found {len(entries)}"
                )
            stat = source_path.stat()
            connection.execute(
                "INSERT INTO lexicon_source VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    source["id"],
                    source["title"],
                    source["full_citation"],
                    str(source_path),
                    source["format"],
                    len(entries),
                    stat.st_size,
                    stat.st_mtime_ns,
                    actual_digest,
                ),
            )
            connection.executemany(
                """
                INSERT INTO entry(
                    source_id, entry_number, headword, normalized_headword, body,
                    raw_entry, line_start, line_end, section, sense_marker,
                    editorial_asterisk, definition_status, pos_labels, frequency_stars
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    (
                        source["id"],
                        entry["entry_number"],
                        entry["headword"],
                        entry["normalized_headword"],
                        entry["body"],
                        entry["raw_entry"],
                        entry["line_start"],
                        entry["line_end"],
                        entry["section"],
                        entry["sense_marker"],
                        entry["editorial_asterisk"],
                        entry["definition_status"],
                        json.dumps(entry["pos_labels"], ensure_ascii=False),
                        entry["frequency_stars"],
                    )
                    for entry in entries
                ),
            )
            connection.commit()
            print(
                f"[{source_number}/{len(sources)}] indexed {source['id']}: "
                f"{len(entries)} entries",
                flush=True,
            )
        connection.executemany(
            "INSERT INTO online_source VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                (
                    source["id"],
                    source["title"],
                    source["full_citation"],
                    source["homepage"],
                    source["query_url"],
                    source["results_url"],
                    source["usage_note"],
                )
                for source in online_sources
            ),
        )
        connection.commit()
        connection.close()
        temporary.replace(database)
        print(f"Index written to {database}")
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def connect_readonly(database: Path) -> sqlite3.Connection:
    if not database.is_file():
        raise FileNotFoundError(
            f"Index not found: {database}. Build it from {DEFAULT_MANIFEST} first."
        )
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        version = connection.execute("SELECT schema_version FROM metadata").fetchone()
    except sqlite3.Error as error:
        connection.close()
        raise ValueError("Legacy lexicon index detected; rebuild it") from error
    if not version or version[0] != SCHEMA_VERSION:
        connection.close()
        raise ValueError(
            f"Unsupported lexicon schema {version[0] if version else 'unknown'}; rebuild required"
        )
    return connection


def validate_output_bounds(limit: int, max_chars: int) -> None:
    if not 1 <= limit <= MAX_RESULTS:
        raise ValueError(f"limit must be between 1 and {MAX_RESULTS}")
    if not 1 <= max_chars <= MAX_ENTRY_CHARS:
        raise ValueError(f"max_chars must be between 1 and {MAX_ENTRY_CHARS}")


def online_fallbacks(connection: sqlite3.Connection) -> list[dict[str, object]]:
    return [dict(row) for row in connection.execute("SELECT * FROM online_source ORDER BY id")]


def source_ids(connection: sqlite3.Connection) -> list[str]:
    return [
        str(row["id"])
        for row in connection.execute("SELECT id FROM lexicon_source ORDER BY id")
    ]


def checked_source_ids(
    connection: sqlite3.Connection, requested_source: str | None
) -> list[str]:
    available = source_ids(connection)
    if requested_source and requested_source not in available:
        raise ValueError(
            f"Unknown lexicon source {requested_source!r}; "
            f"available sources: {', '.join(available)}"
        )
    return [requested_source] if requested_source else available


def locator(headword: str, line_start: int, line_end: int) -> str:
    line_text = (
        f"TXT line {line_start}"
        if line_start == line_end
        else f"TXT lines {line_start}-{line_end}"
    )
    return (
        f"entry 【{headword}】; {line_text}; "
        "printed page unavailable from the supplied TXT"
    )


def row_result(row: sqlite3.Row, max_chars: int | None = None) -> dict[str, object]:
    raw_entry = str(row["raw_entry"])
    truncated = bool(max_chars and len(raw_entry) > max_chars)
    if truncated and max_chars:
        raw_entry = raw_entry[:max_chars].rstrip() + "…"
    return {
        "source_id": row["source_id"],
        "title": row["title"],
        "citation": row["full_citation"],
        "entry_number": row["entry_number"],
        "headword": row["headword"],
        "normalized_headword": row["normalized_headword"],
        "pos_labels": json.loads(row["pos_labels"]),
        "frequency_stars": row["frequency_stars"],
        "line_start": row["line_start"],
        "line_end": row["line_end"],
        "section": row["section"],
        "sense_marker": row["sense_marker"],
        "editorial_asterisk": bool(row["editorial_asterisk"]),
        "definition_status": row["definition_status"],
        "location": locator(row["headword"], row["line_start"], row["line_end"]),
        "entry_text": raw_entry,
        "entry_text_truncated": truncated,
    }


def lookup(
    database: Path, term: str, source_id: str | None, limit: int, max_chars: int
) -> None:
    validate_output_bounds(limit, max_chars)
    connection = connect_readonly(database)
    normalized = normalize_headword(term)
    if not normalized:
        raise ValueError("Lookup term is empty after normalization")
    checked = checked_source_ids(connection, source_id)
    params: list[object] = [normalized]
    source_clause = ""
    if source_id:
        source_clause = " AND e.source_id = ?"
        params.append(source_id)
    coverage_rows = list(
        connection.execute(
            f"""
            SELECT e.source_id,
                   COUNT(*) AS match_count,
                   MAX(CASE WHEN e.definition_status = 'DEFINITION_PRESENT'
                            THEN 1 ELSE 0 END) AS has_usable_definition
            FROM entry AS e
            WHERE e.normalized_headword = ?{source_clause}
            GROUP BY e.source_id
            """,
            params,
        )
    )
    row_params = [*params, limit]
    rows = list(
        connection.execute(
            f"""
            SELECT e.*, s.title, s.full_citation
            FROM entry AS e JOIN lexicon_source AS s ON s.id = e.source_id
            WHERE e.normalized_headword = ?{source_clause}
            ORDER BY e.source_id, e.entry_number LIMIT ?
            """,
            row_params,
        )
    )
    matched_sources = sorted({str(row["source_id"]) for row in coverage_rows})
    usable_sources = sorted(
        {
            str(row["source_id"])
            for row in coverage_rows
            if row["has_usable_definition"]
        }
    )
    total_count = sum(int(row["match_count"]) for row in coverage_rows)
    fallback_recommended = not usable_sources
    normalized_raw_query = unicodedata.normalize("NFKC", term).strip().casefold()
    results: list[dict[str, object]] = []
    for row in rows:
        item = row_result(row, max_chars)
        raw_normalized = unicodedata.normalize("NFKC", str(row["headword"])).casefold()
        item["match_type"] = (
            "LOCAL_EXACT"
            if raw_normalized == normalized_raw_query
            else "LOCAL_NORMALIZED_ALIAS"
        )
        results.append(item)
    result = {
        "status": "found" if total_count else "not_found",
        "query": term,
        "normalized_query": normalized,
        "match_count": total_count,
        "returned_count": len(rows),
        "truncated": total_count > len(rows),
        "sources_checked": checked,
        "sources_without_exact_match": [
            source for source in checked if source not in matched_sources
        ],
        "sources_without_usable_definition": [
            source for source in checked if source not in usable_sources
        ],
        "results": results,
        "online_fallback_recommended": fallback_recommended,
        "online_fallbacks": online_fallbacks(connection),
        "interpretive_warning": (
            "Dictionary inclusion, exclusion, or part-of-speech labels are lexical evidence, "
            "not sufficient proof for or against grammatical metaphor."
        ),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


def search(
    database: Path,
    query: str,
    source_id: str | None,
    field: str,
    limit: int,
    max_chars: int,
) -> None:
    validate_output_bounds(limit, max_chars)
    connection = connect_readonly(database)
    normalized = normalize_headword(query)
    if not normalized:
        raise ValueError("Search query is empty after normalization")
    checked_source_ids(connection, source_id)
    clauses: list[str] = []
    params: list[object] = []
    if field in {"headword", "all"}:
        clauses.append("instr(e.normalized_headword, ?) > 0")
        params.append(normalized)
    if field in {"definition", "all"}:
        clauses.append("instr(lower(e.body), lower(?)) > 0")
        params.append(query)
    source_clause = ""
    if source_id:
        source_clause = " AND e.source_id = ?"
        params.append(source_id)
    coverage_params = list(params)
    params.append(limit)
    coverage = connection.execute(
        f"""
        SELECT COUNT(*) AS match_count,
               MAX(CASE WHEN e.definition_status = 'DEFINITION_PRESENT'
                        THEN 1 ELSE 0 END) AS has_usable_definition
        FROM entry AS e
        WHERE ({' OR '.join(clauses)}){source_clause}
        """,
        coverage_params,
    ).fetchone()
    rows = list(
        connection.execute(
            f"""
            SELECT e.*, s.title, s.full_citation
            FROM entry AS e JOIN lexicon_source AS s ON s.id = e.source_id
            WHERE ({' OR '.join(clauses)}){source_clause}
            ORDER BY
                CASE WHEN e.normalized_headword = ? THEN 0 ELSE 1 END,
                length(e.normalized_headword), e.source_id, e.entry_number
            LIMIT ?
            """,
            [*params[:-1], normalized, params[-1]],
        )
    )
    result = {
        "status": "found" if coverage["match_count"] else "not_found",
        "query": query,
        "field": field,
        "match_count": int(coverage["match_count"]),
        "returned_count": len(rows),
        "truncated": int(coverage["match_count"]) > len(rows),
        "results": [row_result(row, max_chars) for row in rows],
        "online_fallback_recommended": not bool(
            coverage["has_usable_definition"]
        ),
        "online_fallbacks": online_fallbacks(connection),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


def show_entry(database: Path, source_id: str, entry_number: int) -> None:
    connection = connect_readonly(database)
    row = connection.execute(
        """
        SELECT e.*, s.title, s.full_citation
        FROM entry AS e JOIN lexicon_source AS s ON s.id = e.source_id
        WHERE e.source_id = ? AND e.entry_number = ?
        """,
        (source_id, entry_number),
    ).fetchone()
    if not row:
        raise LookupError(f"No entry {entry_number} in {source_id}")
    print(json.dumps(row_result(row), ensure_ascii=False, indent=2))


def show_status(database: Path, verify_files: bool) -> None:
    connection = connect_readonly(database)
    for row in connection.execute("SELECT * FROM lexicon_source ORDER BY id"):
        result = dict(row)
        if verify_files:
            path = Path(str(row["path"]))
            result["file_present"] = path.is_file()
            result["integrity_ok"] = path.is_file() and sha256_file(path) == row["sha256"]
        print(json.dumps(result, ensure_ascii=False))
    for row in connection.execute("SELECT * FROM online_source ORDER BY id"):
        print(json.dumps({"online_source": dict(row)}, ensure_ascii=False))


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)

    build = commands.add_parser("build", help="Build a fresh private lexicon index")
    build.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    build.add_argument("--database", type=Path, default=DEFAULT_DATABASE)

    lookup_parser = commands.add_parser("lookup", help="Look up an exact headword")
    lookup_parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    lookup_parser.add_argument("--term", required=True)
    lookup_parser.add_argument("--source")
    lookup_parser.add_argument("--limit", type=int, default=20)
    lookup_parser.add_argument("--max-chars", type=int, default=1600)

    search_parser = commands.add_parser(
        "search", help="Search headwords, definitions, or both"
    )
    search_parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    search_parser.add_argument("--query", required=True)
    search_parser.add_argument("--source")
    search_parser.add_argument(
        "--field", choices=("headword", "definition", "all"), default="all"
    )
    search_parser.add_argument("--limit", type=int, default=20)
    search_parser.add_argument("--max-chars", type=int, default=1200)

    entry_parser = commands.add_parser(
        "entry", help="Print one complete indexed entry for verification"
    )
    entry_parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    entry_parser.add_argument("--source", required=True)
    entry_parser.add_argument("--entry-number", type=int, required=True)

    status_parser = commands.add_parser("status", help="List indexed lexical sources")
    status_parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    status_parser.add_argument("--verify-files", action="store_true")
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "build":
            build_index(args.manifest, args.database)
        elif args.command == "lookup":
            lookup(args.database, args.term, args.source, args.limit, args.max_chars)
        elif args.command == "search":
            search(
                args.database,
                args.query,
                args.source,
                args.field,
                args.limit,
                args.max_chars,
            )
        elif args.command == "entry":
            show_entry(args.database, args.source, args.entry_number)
        elif args.command == "status":
            show_status(args.database, args.verify_files)
    except (FileNotFoundError, LookupError, ValueError, UnicodeError, sqlite3.Error) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
