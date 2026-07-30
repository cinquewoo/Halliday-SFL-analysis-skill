#!/usr/bin/env python3
"""Regression tests for lexicon_index.py using synthetic dictionary entries."""

from __future__ import annotations

import contextlib
import io
import json
import tempfile
from pathlib import Path

import lexicon_index


def capture(function, *args) -> dict[str, object]:
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        function(*args)
    return json.loads(output.getvalue())


def main() -> int:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        first = root / "dictionary-one.txt"
        second = root / "dictionary-two.txt"
        third = root / "dictionary-three.txt"
        first.write_text(
            "synthetic fixture\n"
            "【云端】yúnduān〈名〉虚构释义一。\n"
            "【同形】tóngxíng〈名〉虚构名词义。\n",
            encoding="utf-8",
        )
        second.write_text(
            "synthetic fixture\n"
            "【云端*】 yúnduān ★★★（形）虚构释义二。\n"
            "〔附录〕\n"
            "【同形²】 tóngxíng ★★（动）虚构动词义。\n"
            "续行内容。\n",
            encoding="utf-8",
        )
        third.write_text(
            "synthetic fixture\n"
            "【空释义】\n"
            "【延后】\n"
            "【延后¹】yánhòu〈名〉后一个同形条目含有可用释义。\n"
            "【只见】zhǐjiàn〈动〉见1页【云端】。\n"
            "【共同】gòngtóng〈名〉共同完成的活动。\n",
            encoding="utf-8",
        )
        manifest = root / "manifest.json"
        manifest.write_text(
            json.dumps(
                {
                    "version": 1,
                    "sources": [
                        {
                            "id": "one",
                            "title": "Synthetic One",
                            "full_citation": "Synthetic One, test fixture.",
                            "path": str(first),
                            "format": "bracket-entry-lines",
                        },
                        {
                            "id": "two",
                            "title": "Synthetic Two",
                            "full_citation": "Synthetic Two, test fixture.",
                            "path": str(second),
                            "format": "bracket-entry-lines",
                        },
                        {
                            "id": "three",
                            "title": "Synthetic Three",
                            "full_citation": "Synthetic Three, test fixture.",
                            "path": str(third),
                            "format": "bracket-entry-lines",
                            "expected_entry_count": 5,
                        },
                    ],
                    "online_sources": [
                        {
                            "id": "online",
                            "title": "Synthetic Online",
                            "full_citation": "Synthetic Online, test fixture.",
                            "homepage": "https://example.invalid/",
                            "query_url": "https://example.invalid/query",
                            "results_url": "https://example.invalid/results",
                            "usage_note": "Test only.",
                        }
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        database = root / "index.sqlite3"
        with contextlib.redirect_stdout(io.StringIO()):
            lexicon_index.build_index(manifest, database)

        exact = capture(lexicon_index.lookup, database, "【云端】", None, 20, 1600)
        assert exact["status"] == "found"
        assert exact["match_count"] == 2
        assert exact["returned_count"] == 2
        assert exact["truncated"] is False
        assert {item["source_id"] for item in exact["results"]} == {"one", "two"}
        assert any(item["frequency_stars"] == 3 for item in exact["results"])

        homographs = capture(
            lexicon_index.lookup, database, "同形", None, 20, 1600
        )
        assert homographs["match_count"] == 2
        assert {tuple(item["pos_labels"]) for item in homographs["results"]} == {
            ("名",),
            ("动",),
        }
        assert any("续行内容" in item["entry_text"] for item in homographs["results"])
        assert any(item["sense_marker"] == "²" for item in homographs["results"])
        assert any(item["section"] == "附录" for item in homographs["results"])

        missing = capture(
            lexicon_index.lookup, database, "未收录", None, 20, 1600
        )
        assert missing["status"] == "not_found"
        assert missing["online_fallback_recommended"] is True
        assert missing["online_fallbacks"][0]["id"] == "online"

        empty = capture(
            lexicon_index.lookup, database, "空释义", None, 20, 1600
        )
        assert empty["status"] == "found"
        assert empty["results"][0]["definition_status"] == "ENTRY_WITHOUT_DEFINITION"
        assert empty["online_fallback_recommended"] is True

        delayed = capture(
            lexicon_index.lookup, database, "延后", "three", 1, 1600
        )
        assert delayed["match_count"] == 2
        assert delayed["returned_count"] == 1
        assert delayed["truncated"] is True
        assert delayed["online_fallback_recommended"] is False

        cross_reference = capture(
            lexicon_index.search,
            database,
            "只见",
            "three",
            "headword",
            20,
            1200,
        )
        assert cross_reference["match_count"] == 1
        assert cross_reference["online_fallback_recommended"] is True
        assert cross_reference["results"][0]["definition_status"] == "CROSS_REFERENCE_ONLY"

        ordinary = capture(
            lexicon_index.lookup, database, "共同", "three", 20, 1600
        )
        assert ordinary["results"][0]["definition_status"] == "DEFINITION_PRESENT"
        assert ordinary["online_fallback_recommended"] is False

        try:
            capture(
                lexicon_index.lookup,
                database,
                "云端",
                "typo-source",
                20,
                1600,
            )
        except ValueError as error:
            assert "Unknown lexicon source" in str(error)
        else:
            raise AssertionError("Unknown source IDs must be rejected")

        for bad_limit, bad_max_chars in ((-1, 1200), (1, 0)):
            try:
                capture(
                    lexicon_index.lookup,
                    database,
                    "云端",
                    None,
                    bad_limit,
                    bad_max_chars,
                )
            except ValueError:
                pass
            else:
                raise AssertionError("Unsafe output bounds must be rejected")

        search = capture(
            lexicon_index.search, database, "续行内容", None, "definition", 20, 1200
        )
        assert search["match_count"] == 1
        assert search["results"][0]["headword"] == "同形²"

        connection = lexicon_index.connect_readonly(database)
        second_source = connection.execute(
            "SELECT entry_count FROM lexicon_source WHERE id = 'two'"
        ).fetchone()
        assert second_source["entry_count"] == 2

        bad_manifest = root / "bad-manifest.json"
        bad_manifest.write_text(
            json.dumps(
                {
                    "version": 1,
                    "sources": [
                        {
                            "id": "bad",
                            "title": "Synthetic Bad Digest",
                            "full_citation": "Synthetic Bad Digest, test fixture.",
                            "path": str(first),
                            "format": "bracket-entry-lines",
                            "sha256": "0" * 64,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                lexicon_index.build_index(bad_manifest, root / "bad.sqlite3")
        except ValueError as error:
            assert "SHA-256 mismatch" in str(error)
        else:
            raise AssertionError("A manifest with a wrong SHA-256 must fail")
    print("lexicon_index regression tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
