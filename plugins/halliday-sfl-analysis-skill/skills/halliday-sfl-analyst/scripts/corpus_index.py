#!/usr/bin/env python3
"""Build and query a private page/slide index of user-supplied SFL sources."""

from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
import re
import sqlite3
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from pypdf import PdfReader


SCHEMA_VERSION = 2
SUPPORTED_KINDS = {"pdf", "pptx"}
SCHEMA = f"""
CREATE TABLE metadata (schema_version INTEGER NOT NULL);
INSERT INTO metadata VALUES ({SCHEMA_VERSION});
CREATE TABLE source (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    full_citation TEXT NOT NULL,
    short_citation TEXT NOT NULL,
    path TEXT NOT NULL,
    kind TEXT NOT NULL,
    unit_count INTEGER NOT NULL,
    page_labels_encoded INTEGER NOT NULL,
    file_size INTEGER NOT NULL,
    mtime_ns INTEGER NOT NULL,
    sha256 TEXT NOT NULL
);
CREATE TABLE page (
    rowid INTEGER PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES source(id),
    unit_number INTEGER NOT NULL,
    unit_label TEXT NOT NULL,
    text TEXT NOT NULL,
    UNIQUE(source_id, unit_number)
);
CREATE VIRTUAL TABLE page_fts USING fts5(
    text,
    content='page',
    content_rowid='rowid',
    tokenize='unicode61 remove_diacritics 2'
);
"""


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


def load_manifest(path: Path) -> list[dict[str, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("version") not in (1, 2) or not isinstance(data.get("sources"), list):
        raise ValueError("Manifest must contain version 1 or 2 and a sources array")
    seen: set[str] = set()
    sources: list[dict[str, str]] = []
    for raw in data["sources"]:
        required = ("id", "title", "path")
        missing = [key for key in required if not raw.get(key)]
        if missing:
            raise ValueError(f"Manifest source is missing {', '.join(missing)}: {raw!r}")
        source_id = str(raw["id"])
        if source_id in seen:
            raise ValueError(f"Duplicate source id: {source_id}")
        seen.add(source_id)
        resolved_path = Path(str(raw["path"])).expanduser().resolve()
        source = {
            "id": source_id,
            "title": str(raw["title"]),
            "full_citation": str(raw.get("full_citation") or raw["title"]),
            "short_citation": str(raw.get("short_citation") or raw["title"]),
            "path": str(resolved_path),
            "kind": infer_kind(resolved_path, raw.get("kind")),
            "sha256": str(raw.get("sha256") or ""),
        }
        sources.append(source)
    return sources


def clean_text(text: str) -> str:
    return text.replace("\x00", " ").replace("\r\n", "\n").replace("\r", "\n")


def extract_pdf(path: Path) -> tuple[list[tuple[int, str, str]], bool]:
    reader = PdfReader(str(path), strict=False)
    page_labels_encoded = reader.root_object.get("/PageLabels") is not None
    labels = list(reader.page_labels) if page_labels_encoded else []
    if len(labels) != len(reader.pages):
        labels = [""] * len(reader.pages)
    units: list[tuple[int, str, str]] = []
    for page_index, page in enumerate(reader.pages):
        try:
            page_text = clean_text(page.extract_text() or "")
        except Exception as error:  # preserve the location when extraction fails
            page_text = f"[TEXT EXTRACTION ERROR: {type(error).__name__}: {error}]"
        units.append((page_index + 1, str(labels[page_index]), page_text))
    return units, page_labels_encoded


def xml_text(payload: bytes) -> str:
    root = ET.fromstring(payload)
    paragraphs: list[str] = []
    for paragraph in root.iter():
        if paragraph.tag.endswith("}p"):
            fragments = [
                element.text or ""
                for element in paragraph.iter()
                if element.tag.endswith("}t") and element.text
            ]
            text = "".join(fragments).strip()
            if text:
                paragraphs.append(text)
    if not paragraphs:
        paragraphs = [
            element.text.strip()
            for element in root.iter()
            if element.tag.endswith("}t") and element.text and element.text.strip()
        ]
    return clean_text("\n".join(paragraphs))


def slide_note_path(archive: zipfile.ZipFile, slide_path: str) -> str | None:
    slide_name = posixpath.basename(slide_path)
    relationships_path = f"ppt/slides/_rels/{slide_name}.rels"
    if relationships_path not in archive.namelist():
        return None
    root = ET.fromstring(archive.read(relationships_path))
    for relationship in root.iter():
        relation_type = relationship.attrib.get("Type", "")
        if relation_type.endswith("/notesSlide"):
            target = relationship.attrib.get("Target")
            if target:
                return posixpath.normpath(posixpath.join(posixpath.dirname(slide_path), target))
    return None


def extract_pptx(path: Path) -> tuple[list[tuple[int, str, str]], bool]:
    units: list[tuple[int, str, str]] = []
    with zipfile.ZipFile(path) as archive:
        slides: list[tuple[int, str]] = []
        for name in archive.namelist():
            match = re.fullmatch(r"ppt/slides/slide(\d+)\.xml", name)
            if match:
                slides.append((int(match.group(1)), name))
        slides.sort()
        if not slides:
            raise ValueError(f"No slides found in PPTX: {path}")
        for slide_number, slide_path in slides:
            text = xml_text(archive.read(slide_path))
            note_path = slide_note_path(archive, slide_path)
            if note_path and note_path in archive.namelist():
                notes = xml_text(archive.read(note_path))
                if notes:
                    text = f"{text}\n[Speaker notes]\n{notes}" if text else f"[Speaker notes]\n{notes}"
            units.append((slide_number, str(slide_number), text))
    return units, False


def extract_units(path: Path, kind: str) -> tuple[list[tuple[int, str, str]], bool]:
    if kind == "pdf":
        return extract_pdf(path)
    if kind == "pptx":
        return extract_pptx(path)
    raise ValueError(f"Unsupported source type: {kind}")


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
            document_path = Path(source["path"])
            if not document_path.is_file():
                raise FileNotFoundError(f"Missing source for {source['id']}: {document_path}")
            actual_digest = sha256_file(document_path)
            if source["sha256"] and source["sha256"] != actual_digest:
                raise ValueError(
                    f"SHA-256 mismatch for {source['id']}: "
                    f"expected {source['sha256']}, found {actual_digest}"
                )
            units, page_labels_encoded = extract_units(document_path, source["kind"])
            stat = document_path.stat()
            connection.execute(
                "INSERT INTO source VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    source["id"],
                    source["title"],
                    source["full_citation"],
                    source["short_citation"],
                    str(document_path),
                    source["kind"],
                    len(units),
                    int(page_labels_encoded),
                    stat.st_size,
                    stat.st_mtime_ns,
                    actual_digest,
                ),
            )
            connection.executemany(
                "INSERT INTO page(source_id, unit_number, unit_label, text) VALUES (?, ?, ?, ?)",
                ((source["id"], number, label, text) for number, label, text in units),
            )
            connection.commit()
            unit_name = "pages" if source["kind"] == "pdf" else "slides"
            print(
                f"[{source_number}/{len(sources)}] indexed {source['id']}: "
                f"{len(units)} {unit_name}",
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
    try:
        version = connection.execute("SELECT schema_version FROM metadata").fetchone()
    except sqlite3.Error as error:
        connection.close()
        raise ValueError("Legacy index detected; rebuild it with the current corpus_index.py") from error
    if not version or version[0] != SCHEMA_VERSION:
        connection.close()
        raise ValueError(
            f"Unsupported index schema {version[0] if version else 'unknown'}; rebuild required"
        )
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


def location_fields(kind: str, unit_number: int, unit_label: str) -> dict[str, object]:
    if kind == "pdf":
        printed = unit_label or None
        location = (
            f"printed p. {unit_label}; PDF p. {unit_number}"
            if unit_label
            else f"printed page unavailable; PDF p. {unit_number}"
        )
        return {
            "printed_page": printed,
            "pdf_page": unit_number,
            "slide": None,
            "location": location,
        }
    return {
        "printed_page": None,
        "pdf_page": None,
        "slide": unit_number,
        "location": f"PPTX slide {unit_number}",
    }


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
        SELECT p.source_id, s.title, s.full_citation, s.short_citation, s.kind,
               p.unit_number, p.unit_label,
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
                SELECT p.source_id, s.title, s.full_citation, s.short_citation, s.kind,
                       p.unit_number, p.unit_label, p.text AS full_text
                FROM page AS p JOIN source AS s ON s.id = p.source_id
                WHERE instr(lower(p.text), lower(?)) > 0{like_source_clause}
                ORDER BY p.source_id, p.unit_number LIMIT ?
                """,
                like_params,
            )
        )
    for row in rows:
        snippet = row["snippet"] if "snippet" in row.keys() else literal_snippet(row["full_text"], query)
        result = {
            "source_id": row["source_id"],
            "title": row["title"],
            "citation": row["full_citation"],
            "short_citation": row["short_citation"],
            "kind": row["kind"],
            **location_fields(row["kind"], row["unit_number"], row["unit_label"]),
            "snippet": re.sub(r"\s+", " ", snippet).strip(),
        }
        print(json.dumps(result, ensure_ascii=False))


def show_page(
    database: Path,
    source_id: str,
    unit_number: int | None,
    label: str | None,
    selector_kind: str | None,
) -> None:
    connection = connect_readonly(database)
    source = connection.execute("SELECT * FROM source WHERE id = ?", (source_id,)).fetchone()
    if not source:
        raise LookupError(f"Unknown source: {source_id}")
    if selector_kind and source["kind"] != selector_kind:
        raise ValueError(f"Source {source_id} is {source['kind']}, not {selector_kind}")
    if unit_number is not None:
        rows = list(
            connection.execute(
                "SELECT * FROM page WHERE source_id = ? AND unit_number = ?",
                (source_id, unit_number),
            )
        )
    else:
        rows = list(
            connection.execute(
                "SELECT * FROM page WHERE source_id = ? AND unit_label = ? ORDER BY unit_number",
                (source_id, label),
            )
        )
    if not rows:
        raise LookupError("No matching page or slide")
    for row in rows:
        location = location_fields(source["kind"], row["unit_number"], row["unit_label"])["location"]
        print(f"SOURCE: {source['id']} | {source['full_citation']} | {location}")
        print(row["text"])


def show_source(database: Path, source_id: str) -> None:
    connection = connect_readonly(database)
    row = connection.execute("SELECT * FROM source WHERE id = ?", (source_id,)).fetchone()
    if not row:
        raise LookupError(f"Unknown source: {source_id}")
    print(json.dumps(dict(row), ensure_ascii=False, indent=2))


def show_status(database: Path) -> None:
    connection = connect_readonly(database)
    rows = connection.execute(
        """
        SELECT s.id, s.title, s.full_citation, s.kind, s.unit_count,
               s.page_labels_encoded, s.sha256, s.path,
               SUM(CASE WHEN trim(p.text) = '' THEN 1 ELSE 0 END) AS empty_units,
               SUM(CASE WHEN p.text LIKE '[TEXT EXTRACTION ERROR:%' THEN 1 ELSE 0 END)
                   AS extraction_errors
        FROM source AS s LEFT JOIN page AS p ON p.source_id = s.id
        GROUP BY s.id ORDER BY s.id
        """
    )
    for row in rows:
        print(json.dumps(dict(row), ensure_ascii=False))


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)

    build = commands.add_parser("build", help="Build a fresh SQLite page/slide index")
    build.add_argument("--manifest", type=Path, required=True)
    build.add_argument("--database", type=Path, required=True)

    search = commands.add_parser("search", help="Search indexed page or slide text")
    search.add_argument("--database", type=Path, required=True)
    search.add_argument("--query", required=True)
    search.add_argument("--source")
    search.add_argument("--limit", type=int, default=12)
    search.add_argument("--mode", choices=("all", "phrase", "raw"), default="all")

    page = commands.add_parser("page", help="Print a complete page or slide for verification")
    page.add_argument("--database", type=Path, required=True)
    page.add_argument("--source", required=True)
    selector = page.add_mutually_exclusive_group(required=True)
    selector.add_argument("--pdf-page", type=int)
    selector.add_argument("--slide", type=int)
    selector.add_argument("--unit", type=int)
    selector.add_argument("--label")

    source = commands.add_parser("source", help="Show full source identity and integrity metadata")
    source.add_argument("--database", type=Path, required=True)
    source.add_argument("--source", required=True)

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
            unit_number = args.pdf_page or args.slide or args.unit
            selector_kind = "pdf" if args.pdf_page is not None else "pptx" if args.slide is not None else None
            show_page(args.database, args.source, unit_number, args.label, selector_kind)
        elif args.command == "source":
            show_source(args.database, args.source)
        elif args.command == "status":
            show_status(args.database)
    except (FileNotFoundError, LookupError, ValueError, zipfile.BadZipFile, ET.ParseError, sqlite3.Error) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
