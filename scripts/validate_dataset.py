#!/usr/bin/env python3
"""CI validation for the exercises dataset.

1. Validates data/exercises.json against data/exercises.schema.json (Draft 2020-12).
2. Checks that the EXERCISES blob embedded in index.html is identical to
   data/exercises.json (the dataset is intentionally duplicated there so the
   browser works offline; the two copies must never drift apart).

Exits non-zero on any failure. Requires: pip install jsonschema
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "exercises.json"
SCHEMA_PATH = ROOT / "data" / "exercises.schema.json"
INDEX_PATH = ROOT / "index.html"

MAX_ERRORS_SHOWN = 20


def error(msg: str) -> None:
    # ::error:: makes the message show up as a GitHub Actions annotation
    print(f"::error::{msg}" if "GITHUB_ACTIONS" in __import__("os").environ else f"ERROR: {msg}")


def validate_schema(data: list) -> int:
    from jsonschema import Draft202012Validator

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)

    count = 0
    for err in validator.iter_errors(data):
        count += 1
        if count <= MAX_ERRORS_SHOWN:
            error(f"schema violation at $.{err.json_path.lstrip('$.')}: {err.message[:300]}")
    if count > MAX_ERRORS_SHOWN:
        error(f"...and {count - MAX_ERRORS_SHOWN} more schema violations")
    if count == 0:
        print(f"OK: {len(data)} records validate against {SCHEMA_PATH.name}")
    return count


def extract_embedded(html: str) -> list:
    # The blob is a single line: "  const EXERCISES = [...];" — greedy match
    # backtracks to the final "];" on that line, so "];" inside instruction
    # strings cannot cut the capture short.
    m = re.search(r"const EXERCISES = (\[.*\]);", html)
    if not m:
        raise ValueError("could not find 'const EXERCISES = [...];' in index.html")
    return json.loads(m.group(1))


def first_diff(a: dict, b: dict) -> str:
    keys = [k for k in {**a, **b} if a.get(k) != b.get(k)]
    return ", ".join(sorted(keys))


def check_sync(data: list) -> int:
    try:
        embedded = extract_embedded(INDEX_PATH.read_text(encoding="utf-8"))
    except (ValueError, json.JSONDecodeError) as exc:
        error(f"index.html EXERCISES blob: {exc}")
        return 1

    if data == embedded:
        print(f"OK: index.html EXERCISES blob is in sync ({len(embedded)} records)")
        return 0

    failures = 0
    if len(data) != len(embedded):
        error(
            f"record count mismatch: data/exercises.json has {len(data)}, "
            f"index.html EXERCISES has {len(embedded)}"
        )
        failures += 1

    json_ids = {r.get("id") for r in data}
    blob_ids = {r.get("id") for r in embedded}
    for label, missing in (
        ("missing from index.html", sorted(json_ids - blob_ids)),
        ("missing from data/exercises.json", sorted(blob_ids - json_ids)),
    ):
        if missing:
            error(f"ids {label}: {missing[:10]}{' ...' if len(missing) > 10 else ''}")
            failures += 1

    blob_by_id = {r.get("id"): r for r in embedded}
    shown = 0
    for rec in data:
        other = blob_by_id.get(rec.get("id"))
        if other is not None and rec != other:
            failures += 1
            shown += 1
            if shown <= MAX_ERRORS_SHOWN:
                error(f"record {rec.get('id')!r} differs in field(s): {first_diff(rec, other)}")
    if shown > MAX_ERRORS_SHOWN:
        error(f"...and {shown - MAX_ERRORS_SHOWN} more out-of-sync records")

    if not failures:  # equality failed but nothing above caught it (e.g. record order)
        error("copies contain the same records but in a different order")
        failures = 1
    return failures


def main() -> int:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        error("data/exercises.json is not a JSON array")
        return 1

    failures = validate_schema(data)
    failures += check_sync(data)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
