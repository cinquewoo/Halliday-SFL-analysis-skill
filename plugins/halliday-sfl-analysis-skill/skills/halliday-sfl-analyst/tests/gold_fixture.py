"""Helpers for expanding the compact, reviewable GM gold fixture."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any


FIXTURE = Path(__file__).parent / "fixtures" / "gm-gold-v3.json"


def load_gold() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    defaults = payload["defaults"]
    records: list[dict[str, Any]] = []
    for case in payload["cases"]:
        record = copy.deepcopy(defaults)
        record.update({key: value for key, value in case.items() if key != "coverage"})
        records.append(record)
    return payload, records
