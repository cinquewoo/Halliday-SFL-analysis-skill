#!/usr/bin/env python3
"""Build and query a private page/slide/EPUB-section index of SFL sources."""

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
from typing import Any


SCHEMA_VERSION = 4
SUPPORTED_KINDS = {"pdf", "pptx", "epub"}
SHA256_PATTERN = re.compile(r"[0-9a-fA-F]{64}")
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
    page_label_mode TEXT NOT NULL,
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


class MissingOptionalDependency(RuntimeError):
    """Raised only when a requested source kind needs an uninstalled extra."""


def load_pdf_reader() -> type[Any]:
    """Import pypdf only for PDF extraction, keeping every other command usable."""

    try:
        from pypdf import PdfReader
    except ModuleNotFoundError as error:
        if error.name != "pypdf":
            raise
        raise MissingOptionalDependency(
            "PDF indexing requires the optional dependency 'pypdf'; install it with "
            "`python -m pip install 'pypdf>=4'` or the project's `pdf` extra"
        ) from error
    return PdfReader


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


def load_manifest(path: Path) -> list[dict[str, object]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Manifest root must be a JSON object")
    if data.get("version") not in (1, 2) or not isinstance(data.get("sources"), list):
        raise ValueError("Manifest must contain version 1 or 2 and a sources array")
    seen: set[str] = set()
    sources: list[dict[str, object]] = []
    for raw in data["sources"]:
        if not isinstance(raw, dict):
            raise ValueError("Every manifest source must be a JSON object")
        required = ("id", "title", "path")
        missing = [key for key in required if not raw.get(key)]
        if missing:
            raise ValueError(f"Manifest source is missing {', '.join(missing)}: {raw!r}")
        source_id = str(raw["id"])
        if source_id in seen:
            raise ValueError(f"Duplicate source id: {source_id}")
        seen.add(source_id)
        resolved_path = Path(str(raw["path"])).expanduser().resolve()
        kind = infer_kind(resolved_path, raw.get("kind"))
        page_label_mode = str(
            raw.get("page_label_mode") or ("encoded" if kind == "pdf" else "none")
        )
        if page_label_mode not in {"encoded", "none", "offset"}:
            raise ValueError(
                f"Unsupported page_label_mode for {source_id}: {page_label_mode}"
            )
        printed_page_start = raw.get("printed_page_start")
        printed_page_pdf_start = raw.get("printed_page_pdf_start")
        if page_label_mode == "offset":
            if kind != "pdf":
                raise ValueError(
                    f"page_label_mode=offset is supported only for PDF sources: {source_id}"
                )
            if not isinstance(printed_page_start, int) or printed_page_start < 1:
                raise ValueError(
                    f"printed_page_start must be a positive integer for {source_id}"
                )
            if not isinstance(printed_page_pdf_start, int) or printed_page_pdf_start < 1:
                raise ValueError(
                    f"printed_page_pdf_start must be a positive integer for {source_id}"
                )
        declared_sha256 = str(raw.get("sha256") or "")
        if declared_sha256 and not SHA256_PATTERN.fullmatch(declared_sha256):
            raise ValueError(f"Invalid SHA-256 for {source_id}: expected 64 hexadecimal digits")
        source: dict[str, object] = {
            "id": source_id,
            "title": str(raw["title"]),
            "full_citation": str(raw.get("full_citation") or raw["title"]),
            "short_citation": str(raw.get("short_citation") or raw["title"]),
            "path": str(resolved_path),
            "kind": kind,
            "sha256": declared_sha256.lower(),
            "page_label_mode": page_label_mode,
            "printed_page_start": printed_page_start,
            "printed_page_pdf_start": printed_page_pdf_start,
        }
        sources.append(source)
    return sources


def clean_text(text: str) -> str:
    return text.replace("\x00", " ").replace("\r\n", "\n").replace("\r", "\n")


def pdf_page_labels(reader: Any, source: dict[str, object]) -> tuple[list[str], bool]:
    encoded = reader.root_object.get("/PageLabels") is not None
    mode = str(source["page_label_mode"])
    if mode == "none":
        return [""] * len(reader.pages), encoded
    if mode == "offset":
        printed_start = int(source["printed_page_start"])
        pdf_start = int(source["printed_page_pdf_start"])
        labels = [
            str(printed_start + pdf_page - pdf_start) if pdf_page >= pdf_start else ""
            for pdf_page in range(1, len(reader.pages) + 1)
        ]
        return labels, encoded
    labels = list(reader.page_labels) if encoded else []
    if len(labels) != len(reader.pages):
        labels = [""] * len(reader.pages)
    return [str(label) for label in labels], encoded


def extract_pdf(
    path: Path, source: dict[str, object]
) -> tuple[list[tuple[int, str, str]], bool]:
    PdfReader = load_pdf_reader()
    reader = PdfReader(str(path), strict=False)
    labels, page_labels_encoded = pdf_page_labels(reader, source)
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


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def epub_rootfile(archive: zipfile.ZipFile) -> str:
    container_path = "META-INF/container.xml"
    if container_path not in archive.namelist():
        raise ValueError("EPUB has no META-INF/container.xml")
    root = ET.fromstring(archive.read(container_path))
    for element in root.iter():
        if local_name(element.tag) == "rootfile":
            full_path = element.attrib.get("full-path")
            if full_path:
                return posixpath.normpath(full_path)
    raise ValueError("EPUB container does not identify an OPF rootfile")


def epub_toc_labels(
    archive: zipfile.ZipFile,
    opf_path: str,
    manifest: dict[str, dict[str, str]],
    spine_toc_id: str | None,
) -> dict[str, str]:
    labels: dict[str, str] = {}
    opf_dir = posixpath.dirname(opf_path)

    toc_item = manifest.get(spine_toc_id or "")
    if toc_item:
        toc_path = posixpath.normpath(posixpath.join(opf_dir, toc_item["href"]))
        if toc_path in archive.namelist():
            root = ET.fromstring(archive.read(toc_path))
            for nav_point in root.iter():
                if local_name(nav_point.tag) != "navPoint":
                    continue
                label = ""
                href = ""
                for child in nav_point.iter():
                    name = local_name(child.tag)
                    if name == "text" and child.text and not label:
                        label = " ".join(child.text.split())
                    elif name == "content" and not href:
                        href = child.attrib.get("src", "")
                if label and href:
                    resolved = posixpath.normpath(
                        posixpath.join(posixpath.dirname(toc_path), href.split("#", 1)[0])
                    )
                    labels.setdefault(resolved, label)

    for item in manifest.values():
        properties = item.get("properties", "").split()
        if "nav" not in properties:
            continue
        nav_path = posixpath.normpath(posixpath.join(opf_dir, item["href"]))
        if nav_path not in archive.namelist():
            continue
        root = ET.fromstring(archive.read(nav_path))
        for anchor in root.iter():
            if local_name(anchor.tag) != "a":
                continue
            href = anchor.attrib.get("href", "")
            label = " ".join("".join(anchor.itertext()).split())
            if href and label:
                resolved = posixpath.normpath(
                    posixpath.join(posixpath.dirname(nav_path), href.split("#", 1)[0])
                )
                labels.setdefault(resolved, label)
    return labels


def epub_xhtml_text(payload: bytes, href: str, toc_label: str | None) -> tuple[str, str]:
    root = ET.fromstring(payload)
    block_names = {
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "p",
        "li",
        "figcaption",
        "blockquote",
        "td",
        "th",
    }
    lines: list[str] = []
    first_anchor = ""
    heading = ""
    paragraph_number = 0
    for element in root.iter():
        name = local_name(element.tag).lower()
        if name not in block_names:
            continue
        text = " ".join("".join(element.itertext()).split())
        if not text:
            continue
        if not first_anchor:
            for descendant in element.iter():
                if descendant.attrib.get("id"):
                    first_anchor = descendant.attrib["id"]
                    break
        if not heading and name.startswith("h"):
            heading = text
        paragraph_number += 1
        lines.append(f"[p{paragraph_number}] {text}")
    if not lines:
        fallback = " ".join("".join(root.itertext()).split())
        if fallback:
            lines.append(f"[p1] {fallback}")
    section_title = toc_label or heading or posixpath.basename(href)
    anchored_href = f"{href}#{first_anchor}" if first_anchor else href
    prefix = f"[EPUB section: {section_title}]\n[EPUB href: {anchored_href}]"
    body = "\n".join(lines)
    return clean_text(f"{prefix}\n{body}" if body else prefix), anchored_href


def extract_epub(path: Path) -> tuple[list[tuple[int, str, str]], bool]:
    units: list[tuple[int, str, str]] = []
    with zipfile.ZipFile(path) as archive:
        opf_path = epub_rootfile(archive)
        if opf_path not in archive.namelist():
            raise ValueError(f"EPUB OPF rootfile is missing: {opf_path}")
        root = ET.fromstring(archive.read(opf_path))
        manifest: dict[str, dict[str, str]] = {}
        spine_ids: list[str] = []
        spine_toc_id: str | None = None
        for element in root.iter():
            name = local_name(element.tag)
            if name == "item" and element.attrib.get("id") and element.attrib.get("href"):
                manifest[element.attrib["id"]] = {
                    "href": element.attrib["href"],
                    "media-type": element.attrib.get("media-type", ""),
                    "properties": element.attrib.get("properties", ""),
                }
            elif name == "spine":
                spine_toc_id = element.attrib.get("toc")
                for itemref in element:
                    if local_name(itemref.tag) == "itemref" and itemref.attrib.get("idref"):
                        spine_ids.append(itemref.attrib["idref"])
        if not spine_ids:
            raise ValueError(f"No spine items found in EPUB: {path}")
        toc_labels = epub_toc_labels(archive, opf_path, manifest, spine_toc_id)
        opf_dir = posixpath.dirname(opf_path)
        for item_id in spine_ids:
            item = manifest.get(item_id)
            if not item:
                raise ValueError(f"EPUB spine references missing manifest item: {item_id}")
            href = posixpath.normpath(posixpath.join(opf_dir, item["href"]))
            media_type = item.get("media-type", "")
            if media_type not in {"application/xhtml+xml", "text/html"}:
                continue
            if href not in archive.namelist():
                raise ValueError(f"EPUB spine content is missing: {href}")
            text, anchored_href = epub_xhtml_text(
                archive.read(href), href, toc_labels.get(href)
            )
            section_title = toc_labels.get(href)
            label = f"{section_title} | {anchored_href}" if section_title else anchored_href
            units.append((len(units) + 1, label, text))
    if not units:
        raise ValueError(f"No XHTML spine content found in EPUB: {path}")
    return units, False


def extract_units(
    path: Path, kind: str, source: dict[str, object]
) -> tuple[list[tuple[int, str, str]], bool]:
    if kind == "pdf":
        return extract_pdf(path, source)
    if kind == "pptx":
        return extract_pptx(path)
    if kind == "epub":
        return extract_epub(path)
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
            document_path = Path(str(source["path"]))
            if not document_path.is_file():
                raise FileNotFoundError(f"Missing source for {source['id']}: {document_path}")
            actual_digest = sha256_file(document_path)
            if source["sha256"] and source["sha256"] != actual_digest:
                raise ValueError(
                    f"SHA-256 mismatch for {source['id']}: "
                    f"expected {source['sha256']}, found {actual_digest}"
                )
            source_kind = str(source["kind"])
            units, page_labels_encoded = extract_units(document_path, source_kind, source)
            stat = document_path.stat()
            connection.execute(
                "INSERT INTO source VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    source["id"],
                    source["title"],
                    source["full_citation"],
                    source["short_citation"],
                    str(document_path),
                    source_kind,
                    len(units),
                    int(page_labels_encoded),
                    source["page_label_mode"],
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
            unit_name = {
                "pdf": "pages",
                "pptx": "slides",
                "epub": "EPUB sections",
            }[source_kind]
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
    connection = sqlite3.connect(f"{database.resolve().as_uri()}?mode=ro", uri=True)
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
            "epub_unit": None,
            "epub_section": None,
            "location": location,
        }
    if kind == "pptx":
        return {
            "printed_page": None,
            "pdf_page": None,
            "slide": unit_number,
            "epub_unit": None,
            "epub_section": None,
            "location": f"PPTX slide {unit_number}",
        }
    if kind == "epub":
        return {
            "printed_page": None,
            "pdf_page": None,
            "slide": None,
            "epub_unit": unit_number,
            "epub_section": unit_label,
            "location": (
                f"EPUB section {unit_label}; printed page unavailable from this EPUB"
            ),
        }
    raise ValueError(f"Unsupported source type: {kind}")


def search_index(
    database: Path, query: str, source_id: str | None, limit: int, mode: str
) -> None:
    if limit < 1 or limit > 1000:
        raise ValueError("Search limit must be between 1 and 1000")
    connection = connect_readonly(database)
    if source_id and not connection.execute(
        "SELECT 1 FROM source WHERE id = ?", (source_id,)
    ).fetchone():
        connection.close()
        raise LookupError(f"Unknown source: {source_id}")
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
        raise LookupError("No matching page, slide, or EPUB section")
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
               s.page_labels_encoded, s.page_label_mode, s.sha256, s.path,
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

    build = commands.add_parser(
        "build", help="Build a fresh SQLite page/slide/EPUB-section index"
    )
    build.add_argument("--manifest", type=Path, required=True)
    build.add_argument("--database", type=Path, required=True)

    search = commands.add_parser(
        "search", help="Search indexed page, slide, or EPUB-section text"
    )
    search.add_argument("--database", type=Path, required=True)
    search.add_argument("--query", required=True)
    search.add_argument("--source")
    search.add_argument("--limit", type=int, default=12)
    search.add_argument("--mode", choices=("all", "phrase", "raw"), default="all")

    page = commands.add_parser(
        "page", help="Print a complete page, slide, or EPUB section for verification"
    )
    page.add_argument("--database", type=Path, required=True)
    page.add_argument("--source", required=True)
    selector = page.add_mutually_exclusive_group(required=True)
    selector.add_argument("--pdf-page", type=positive_int)
    selector.add_argument("--slide", type=positive_int)
    selector.add_argument("--epub-unit", type=positive_int)
    selector.add_argument("--unit", type=positive_int)
    selector.add_argument("--label")

    source = commands.add_parser("source", help="Show full source identity and integrity metadata")
    source.add_argument("--database", type=Path, required=True)
    source.add_argument("--source", required=True)

    status = commands.add_parser("status", help="List indexed sources")
    status.add_argument("--database", type=Path, required=True)
    return root


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be a positive integer")
    return parsed


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "build":
            build_index(args.manifest, args.database)
        elif args.command == "search":
            search_index(args.database, args.query, args.source, args.limit, args.mode)
        elif args.command == "page":
            unit_number = next(
                (
                    value
                    for value in (
                        args.pdf_page,
                        args.slide,
                        args.epub_unit,
                        args.unit,
                    )
                    if value is not None
                ),
                None,
            )
            selector_kind = (
                "pdf"
                if args.pdf_page is not None
                else "pptx"
                if args.slide is not None
                else "epub"
                if args.epub_unit is not None
                else None
            )
            show_page(args.database, args.source, unit_number, args.label, selector_kind)
        elif args.command == "source":
            show_source(args.database, args.source)
        elif args.command == "status":
            show_status(args.database)
    except (
        FileNotFoundError,
        LookupError,
        MissingOptionalDependency,
        ValueError,
        zipfile.BadZipFile,
        ET.ParseError,
        sqlite3.Error,
    ) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
