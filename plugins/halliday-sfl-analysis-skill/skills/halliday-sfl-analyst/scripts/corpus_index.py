#!/usr/bin/env python3
"""Build and query a private page-level index of user-supplied Halliday PDFs."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import tempfile
from pathlib import Path

from pypdf import PdfReader


SCHEMA = """
CREATE TABLE source (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    short_citation TEXT NOT NULL,
    path TEXT NOT NULL,
    page_count INTEGER NOT NULL,
    page_labels_encoded INTEGER NOT NULL,
    file_size INTEGER NOT NULL,
    mtime_ns INTEGER NOT NULL
);
CREATE TABLE page (
    rowid INTEGER PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES source(id),
    pdf_page INTEGER NOT NULL,
    page_label TEXT NOT NULL,
    text TEXT NOT NULL,
    UNIQUE(source_id, pdf_page)
);
CREATE VIRTUAL TABLE page_fts USING fts5(
    text,
    content='page',
    content_rowid='rowid',
    tokenize='unicode61 remove_diacritics 2'
);
"""


def load_manifest(path: Path) -> list[dict[str, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("version") != 1 or not isinstance(data.get("sources"), list):
        raise ValueError("Manifest must contain version 1 and a sources array")
    seen: set[str] = set()
    sources: list[dict[str, str]] = []
    for raw in data["sources"]:
        required = ("id", "title", "short_citation", "path")
        missing = [key for key in required if not raw.get(key)]
        if missing:
            raise ValueError(f"Manifest source is missing {', '.join(missing)}: {raw!r}")
        source_id = str(raw["id"])
        if source_id in seen:
            raise ValueError(f"Duplicate source id: {source_id}")
        seen.add(source_id)
        source = {key: str(raw[key]) for key in required}
        source["path"] = str(Path(source["path"]).expanduser().resolve())
        sources.append(source)
    return sources


def clean_text(text: str) -> str:
    return text.replace("\x00", " ").replace("\r\n", "\n").replace("\r", "\n")


def build_index(manifest: Path, database: Path) -> None:
    sources = load_manifest(manifest)
    database.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        prefix=f".{database.name}.", suffix=".tmp", dir=database.parent, delete=False
    ) as handle:
        temporary = Path(handle.name)
    try:
        connection = sqlite3.connect(temporary)
        connection.executescript(SCHEMA)
        for source_number, source in enumerate(sources, start=1):
            pdf_path = Path(source["path"])
            if not pdf_path.is_file():
                raise FileNotFoundError(f"Missing PDF for {source['id']}: {pdf_path}")
            reader = PdfReader(str(pdf_path), strict=False)
            page_labels_encoded = reader.root_object.get("/PageLabels") is not None
            labels = list(reader.page_labels) if page_labels_encoded else []
            if len(labels) != len(reader.pages):
                labels = [""] * len(reader.pages)
            stat = pdf_path.stat()
            connection.execute(
                "INSERT INTO source VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    source["id"],
                    source["title"],
                    source["short_citation"],
                    str(pdf_path),
                    len(reader.pages),
                    int(page_labels_encoded),
                    stat.st_size,
                    stat.st_mtime_ns,
                ),
            )
            for page_index, page in enumerate(reader.pages):
                try:
                    page_text = clean_text(page.extract_text() or "")
                except Exception as error:  # preserve the page location even if extraction fails
                    page_text = f"[TEXT EXTRACTION ERROR: {type(error).__name__}: {error}]"
                connection.execute(
                    "INSERT INTO page(source_id, pdf_page, page_label, text) VALUES (?, ?, ?, ?)",
                    (source["id"], page_index + 1, str(labels[page_index]), page_text),
                )
            connection.commit()
            print(
                f"[{source_number}/{len(sources)}] indexed {source['id']}: {len(reader.pages)} pages",
                flush=True,
            )
        connection.execute("INSERT INTO page_fts(page_fts) VALUES ('rebuild')")
        connection.commit()
        connection.close()
        temporary.replace(database)
        print(f"Index written to {database}")
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def connect_readonly(database: Path) -> sqlite3.Connection:
    if not database.is_file():
        raise FileNotFoundError(f"Index not found: {database}")
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def fts_query(query: str, mode: str) -> str:
    if mode == "raw":
        return query
    tokens = re.findall(r"[^\W_]+", query, flags=re.UNICODE)
    if not tokens:
        raise ValueError("Search query has no searchable terms")
    escaped = [f'"{token.replace(chr(34), chr(34) * 2)}"' for token in tokens]
    if mode == "phrase":
        return f'"{query.replace(chr(34), chr(34) * 2)}"'
    return " AND ".join(escaped)


def literal_snippet(text: str, query: str, width: int = 220) -> str:
    flat = re.sub(r"\s+", " ", text).strip()
    location = flat.casefold().find(query.casefold())
    if location < 0:
        return flat[:width]
    start = max(0, location - width // 2)
    end = min(len(flat), location + len(query) + width // 2)
    prefix = "..." if start else ""
    suffix = "..." if end < len(flat) else ""
    return f"{prefix}{flat[start:end]}{suffix}"


def search_index(
    database: Path, query: str, source_id: str | None, limit: int, mode: str
) -> None:
    connection = connect_readonly(database)
    params: list[object] = [fts_query(query, mode)]
    source_clause = ""
    if source_id:
        source_clause = " AND p.source_id = ?"
        params.append(source_id)
    params.append(limit)
    sql = f"""
        SELECT p.source_id, s.short_citation, p.pdf_page, p.page_label,
               snippet(page_fts, 0, '[', ']', ' ... ', 32) AS snippet
        FROM page_fts
        JOIN page AS p ON p.rowid = page_fts.rowid
        JOIN source AS s ON s.id = p.source_id
        WHERE page_fts MATCH ?{source_clause}
        ORDER BY bm25(page_fts)
        LIMIT ?
    """
    try:
        rows = list(connection.execute(sql, params))
    except sqlite3.OperationalError as error:
        raise ValueError(f"Invalid FTS query: {error}") from error
    if not rows:
        like_params: list[object] = [query]
        like_source_clause = ""
        if source_id:
            like_source_clause = " AND p.source_id = ?"
            like_params.append(source_id)
        like_params.append(limit)
        rows = list(
            connection.execute(
                f"""
                SELECT p.source_id, s.short_citation, p.pdf_page, p.page_label,
                       p.text AS full_text
                FROM page AS p JOIN source AS s ON s.id = p.source_id
                WHERE instr(lower(p.text), lower(?)) > 0{like_source_clause}
                ORDER BY p.source_id, p.pdf_page LIMIT ?
                """,
                like_params,
            )
        )
    for row in rows:
        snippet = row["snippet"] if "snippet" in row.keys() else literal_snippet(row["full_text"], query)
        print(
            json.dumps(
                {
                    "source_id": row["source_id"],
                    "citation": row["short_citation"],
                    "printed_page": row["page_label"] or None,
                    "pdf_page": row["pdf_page"],
                    "snippet": re.sub(r"\s+", " ", snippet).strip(),
                },
                ensure_ascii=False,
            )
        )


def show_page(database: Path, source_id: str, pdf_page: int | None, label: str | None) -> None:
    connection = connect_readonly(database)
    if pdf_page is not None:
        rows = list(
            connection.execute(
                """
                SELECT p.*, s.short_citation FROM page AS p
                JOIN source AS s ON s.id = p.source_id
                WHERE p.source_id = ? AND p.pdf_page = ?
                """,
                (source_id, pdf_page),
            )
        )
    else:
        rows = list(
            connection.execute(
                """
                SELECT p.*, s.short_citation FROM page AS p
                JOIN source AS s ON s.id = p.source_id
                WHERE p.source_id = ? AND p.page_label = ? ORDER BY p.pdf_page
                """,
                (source_id, label),
            )
        )
    if not rows:
        raise LookupError("No matching page")
    for row in rows:
        print(
            f"SOURCE: {row['source_id']} | {row['short_citation']} | "
            f"{format_printed_page(row['page_label'])} | PDF p. {row['pdf_page']}"
        )
        print(row["text"])


def show_status(database: Path) -> None:
    connection = connect_readonly(database)
    rows = connection.execute(
        """
        SELECT s.id, s.title, s.page_count, s.page_labels_encoded, s.path,
               SUM(CASE WHEN trim(p.text) = '' THEN 1 ELSE 0 END) AS empty_pages,
               SUM(CASE WHEN p.text LIKE '[TEXT EXTRACTION ERROR:%' THEN 1 ELSE 0 END)
                   AS extraction_errors
        FROM source AS s LEFT JOIN page AS p ON p.source_id = s.id
        GROUP BY s.id, s.title, s.page_count, s.page_labels_encoded, s.path ORDER BY s.id
        """
    )
    for row in rows:
        print(
            json.dumps(
                {
                    "source_id": row["id"],
                    "title": row["title"],
                    "pages": row["page_count"],
                    "page_labels_encoded": bool(row["page_labels_encoded"]),
                    "empty_pages": row["empty_pages"],
                    "extraction_errors": row["extraction_errors"],
                    "path": row["path"],
                },
                ensure_ascii=False,
            )
        )


def format_printed_page(label: str) -> str:
    return f"printed p. {label}" if label else "printed page unavailable"


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)

    build = commands.add_parser("build", help="Build a fresh SQLite page index")
    build.add_argument("--manifest", type=Path, required=True)
    build.add_argument("--database", type=Path, required=True)

    search = commands.add_parser("search", help="Search indexed page text")
    search.add_argument("--database", type=Path, required=True)
    search.add_argument("--query", required=True)
    search.add_argument("--source")
    search.add_argument("--limit", type=int, default=12)
    search.add_argument("--mode", choices=("all", "phrase", "raw"), default="all")

    page = commands.add_parser("page", help="Print a complete page for verification")
    page.add_argument("--database", type=Path, required=True)
    page.add_argument("--source", required=True)
    selector = page.add_mutually_exclusive_group(required=True)
    selector.add_argument("--pdf-page", type=int)
    selector.add_argument("--label")

    status = commands.add_parser("status", help="List indexed sources")
    status.add_argument("--database", type=Path, required=True)
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "build":
            build_index(args.manifest, args.database)
        elif args.command == "search":
            search_index(args.database, args.query, args.source, args.limit, args.mode)
        elif args.command == "page":
            show_page(args.database, args.source, args.pdf_page, args.label)
        elif args.command == "status":
            show_status(args.database)
    except (FileNotFoundError, LookupError, ValueError, sqlite3.Error) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
