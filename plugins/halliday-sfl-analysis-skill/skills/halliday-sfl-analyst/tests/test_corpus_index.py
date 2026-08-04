#!/usr/bin/env python3
"""Independent regression tests for corpus_index.py using synthetic sources."""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


TEST_DIR = Path(__file__).resolve().parent
SCRIPT_DIR = TEST_DIR.parent / "scripts"
CORPUS_SCRIPT = SCRIPT_DIR / "corpus_index.py"
sys.path.insert(0, str(SCRIPT_DIR))

import corpus_index  # noqa: E402

try:
    from pypdf import PdfWriter
except ModuleNotFoundError:
    PdfWriter = None


def write_minimal_pptx(path: Path) -> None:
    slide = """<?xml version="1.0" encoding="UTF-8"?>
<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
       xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <p:cSld><p:spTree><p:sp><p:txBody><a:p><a:r><a:t>Synthetic alpha process</a:t></a:r></a:p></p:txBody></p:sp></p:spTree></p:cSld>
</p:sld>"""
    notes = """<?xml version="1.0" encoding="UTF-8"?>
<p:notes xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
         xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <p:cSld><p:spTree><p:sp><p:txBody><a:p><a:r><a:t>Synthetic speaker note</a:t></a:r></a:p></p:txBody></p:sp></p:spTree></p:cSld>
</p:notes>"""
    rels = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide" Target="../notesSlides/notesSlide1.xml"/>
</Relationships>"""
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("ppt/slides/slide1.xml", slide)
        archive.writestr("ppt/slides/_rels/slide1.xml.rels", rels)
        archive.writestr("ppt/notesSlides/notesSlide1.xml", notes)


def write_minimal_epub(path: Path) -> None:
    container = """<?xml version="1.0"?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">
  <rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>"""
    opf = """<?xml version="1.0"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="c1" href="chapter.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine><itemref idref="c1"/></spine>
</package>"""
    nav = """<html xmlns="http://www.w3.org/1999/xhtml"><body><nav><ol><li><a href="chapter.xhtml#sec">Synthetic chapter</a></li></ol></nav></body></html>"""
    chapter = """<html xmlns="http://www.w3.org/1999/xhtml"><body><h1 id="sec">Synthetic chapter</h1><p>Beta relation appears here.</p></body></html>"""
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("META-INF/container.xml", container)
        archive.writestr("OEBPS/content.opf", opf)
        archive.writestr("OEBPS/nav.xhtml", nav)
        archive.writestr("OEBPS/chapter.xhtml", chapter)


def write_manifest(path: Path, sources: list[dict[str, object]]) -> None:
    path.write_text(json.dumps({"version": 2, "sources": sources}), encoding="utf-8")


class CorpusIndexTests(unittest.TestCase):
    def test_help_has_no_optional_pdf_dependency(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-S", str(CORPUS_SCRIPT), "--help"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Build and query", completed.stdout)

    def test_pptx_build_search_page_status_and_unusual_database_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "synthetic.pptx"
            manifest = root / "manifest.json"
            database = root / "index?#.sqlite3"
            write_minimal_pptx(source)
            write_manifest(
                manifest,
                [
                    {
                        "id": "slides",
                        "title": "Synthetic Slides",
                        "full_citation": "Synthetic Slides, test fixture.",
                        "path": str(source),
                        "kind": "pptx",
                    }
                ],
            )
            with contextlib.redirect_stdout(io.StringIO()):
                corpus_index.build_index(manifest, database)
            connection = corpus_index.connect_readonly(database)
            try:
                row = connection.execute("SELECT page_label_mode FROM source").fetchone()
                self.assertEqual(row[0], "none")
            finally:
                connection.close()
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                corpus_index.search_index(database, "alpha process", "slides", 5, "all")
            result = json.loads(output.getvalue())
            self.assertEqual(result["slide"], 1)
            self.assertEqual(result["citation"], "Synthetic Slides, test fixture.")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                corpus_index.show_page(database, "slides", 1, None, "pptx")
            self.assertIn("Synthetic speaker note", output.getvalue())
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                corpus_index.show_source(database, "slides")
                corpus_index.show_status(database)
            self.assertIn("Synthetic Slides", output.getvalue())

    def test_epub_section_and_locator(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "synthetic.epub"
            manifest = root / "manifest.json"
            database = root / "epub.sqlite3"
            write_minimal_epub(source)
            write_manifest(
                manifest,
                [{"id": "book", "title": "Synthetic Book", "path": str(source)}],
            )
            with contextlib.redirect_stdout(io.StringIO()):
                corpus_index.build_index(manifest, database)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                corpus_index.search_index(database, "Beta relation", "book", 5, "phrase")
            result = json.loads(output.getvalue())
            self.assertEqual(result["epub_unit"], 1)
            self.assertIn("chapter.xhtml#sec", result["epub_section"])
            self.assertIn("printed page unavailable", result["location"])
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                corpus_index.show_page(database, "book", 1, None, "epub")
            self.assertIn("[p2] Beta relation appears here.", output.getvalue())

    def test_manifest_structure_digest_and_page_label_validation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "synthetic.pptx"
            write_minimal_pptx(source)
            cases = [
                ([], "root must be a JSON object"),
                ({"version": 2, "sources": ["bad"]}, "source must be a JSON object"),
                (
                    {
                        "version": 2,
                        "sources": [
                            {
                                "id": "bad",
                                "title": "Bad",
                                "path": str(source),
                                "sha256": "not-a-digest",
                            }
                        ],
                    },
                    "Invalid SHA-256",
                ),
                (
                    {
                        "version": 2,
                        "sources": [
                            {
                                "id": "bad",
                                "title": "Bad",
                                "path": str(source),
                                "page_label_mode": "offset",
                                "printed_page_start": 1,
                                "printed_page_pdf_start": 1,
                            }
                        ],
                    },
                    "only for PDF",
                ),
            ]
            for index, (payload, message) in enumerate(cases):
                manifest = root / f"bad-{index}.json"
                manifest.write_text(json.dumps(payload), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, message):
                    corpus_index.load_manifest(manifest)
            valid_digest = hashlib.sha256(source.read_bytes()).hexdigest()
            manifest = root / "valid.json"
            write_manifest(
                manifest,
                [{"id": "ok", "title": "OK", "path": str(source), "sha256": valid_digest}],
            )
            self.assertEqual(corpus_index.load_manifest(manifest)[0]["sha256"], valid_digest)

    def test_query_bounds_unknown_source_and_unknown_kind(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "synthetic.pptx"
            manifest = root / "manifest.json"
            database = root / "index.sqlite3"
            write_minimal_pptx(source)
            write_manifest(manifest, [{"id": "slides", "title": "Slides", "path": str(source)}])
            with contextlib.redirect_stdout(io.StringIO()):
                corpus_index.build_index(manifest, database)
            for limit in (0, -1, 1001):
                with self.assertRaisesRegex(ValueError, "between 1 and 1000"):
                    corpus_index.search_index(database, "alpha", None, limit, "all")
            with self.assertRaisesRegex(LookupError, "Unknown source"):
                corpus_index.search_index(database, "alpha", "missing", 5, "all")
            with self.assertRaisesRegex(ValueError, "Unsupported source type"):
                corpus_index.location_fields("txt", 1, "")

    def test_missing_pdf_extra_is_reported_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "synthetic.pdf"
            source.write_bytes(b"%PDF-1.4\n% synthetic fixture\n")
            manifest = root / "manifest.json"
            database = root / "index.sqlite3"
            write_manifest(manifest, [{"id": "pdf", "title": "Synthetic PDF", "path": str(source)}])
            completed = subprocess.run(
                [
                    sys.executable,
                    "-S",
                    str(CORPUS_SCRIPT),
                    "build",
                    "--manifest",
                    str(manifest),
                    "--database",
                    str(database),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertIn("optional dependency 'pypdf'", completed.stderr)
            self.assertNotIn("Traceback", completed.stderr)

    @unittest.skipUnless(PdfWriter is not None, "optional pypdf extra is not installed")
    def test_pdf_indexing_with_optional_extra(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "synthetic.pdf"
            writer = PdfWriter()
            writer.add_blank_page(width=100, height=100)
            with source.open("wb") as handle:
                writer.write(handle)
            manifest = root / "manifest.json"
            database = root / "pdf.sqlite3"
            write_manifest(manifest, [{"id": "pdf", "title": "Synthetic PDF", "path": str(source)}])
            with contextlib.redirect_stdout(io.StringIO()):
                corpus_index.build_index(manifest, database)
            connection = corpus_index.connect_readonly(database)
            try:
                row = connection.execute(
                    "SELECT kind, unit_count, page_label_mode FROM source WHERE id='pdf'"
                ).fetchone()
                self.assertEqual(tuple(row), ("pdf", 1, "encoded"))
            finally:
                connection.close()

    def test_positive_integer_parser(self) -> None:
        self.assertEqual(corpus_index.positive_int("2"), 2)
        with self.assertRaises(Exception):
            corpus_index.positive_int("0")


if __name__ == "__main__":
    unittest.main()
