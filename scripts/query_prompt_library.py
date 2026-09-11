"""Query the bundled, versioned prompt-library snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


def _load_manifest(library: Path) -> dict[str, Any]:
    manifest_path = library / "manifest.json"
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid prompt library manifest: {manifest_path}: {exc}") from exc


def _record_from_row(
    headers: list[Any], row: list[Any], header_overrides: dict[str, str]
) -> dict[str, Any]:
    record: dict[str, Any] = {}
    for index, value in enumerate(row):
        header = header_overrides.get(
            str(index + 1), headers[index] if index < len(headers) else None
        )
        key = str(header).strip() if header is not None else ""
        if key:
            record[key] = value
    return record


def _iter_records(library: Path, sheet: dict[str, Any]):
    path = (library / sheet["file"]).resolve()
    if library.resolve() not in path.parents:
        raise ValueError("snapshot file outside library")
    raw = path.read_bytes()
    if sheet.get("sha256") and hashlib.sha256(raw).hexdigest() != sheet["sha256"]:
        raise ValueError(f"hash mismatch: {path.name}")
    payload = json.loads(raw.decode("utf-8"))
    rows = payload.get("rows", [])
    header_row = payload.get("header_row")
    if header_row is None:
        for row_index, row in enumerate(rows, start=1):
            if row:
                yield row_index, {"內容": row[0]}
        return

    header_index = header_row - 1
    if not 0 <= header_index < len(rows):
        raise ValueError(f"invalid header_row for sheet: {sheet['name']}")
    headers = rows[header_index]
    for row_index, row in enumerate(rows[header_index + 1 :], start=header_row + 1):
        record = _record_from_row(headers, row, sheet.get("header_overrides", {}))
        if record and record.get("生命週期") != "停用":
            yield row_index, record


def query_library(
    library: Path, query: str, *, sheet_name: str | None = None, limit: int = 5
) -> list[dict[str, Any]]:
    if not query.strip():
        raise ValueError("query must not be empty")
    if limit < 1:
        raise ValueError("limit must be at least 1")

    library = Path(library).resolve()
    active = library / "active.json"
    if active.is_file():
        target = (library / json.loads(active.read_text(encoding="utf-8"))["snapshot"]).resolve()
        if library not in target.parents:
            raise ValueError("active snapshot outside library")
        library = target
    manifest = _load_manifest(library)
    sheets = manifest.get("sheets", [])
    known_names = {sheet["name"] for sheet in sheets}
    if sheet_name is not None and sheet_name not in known_names:
        raise ValueError(f"unknown sheet: {sheet_name}")
    selected = [s for s in sheets if sheet_name is None or s["name"] == sheet_name]

    needle = query.casefold().strip()
    matches: list[tuple[int, int, int, dict[str, Any]]] = []
    for sheet_order, sheet in enumerate(selected):
        for row_index, record in _iter_records(library, sheet):
            values = [str(value) for value in record.values() if value is not None]
            folded = [value.casefold() for value in values]
            if not any(needle in value for value in folded):
                continue
            if any(needle == value.strip() for value in folded):
                rank = 0
            elif any(value.strip().startswith(needle) for value in folded):
                rank = 1
            else:
                rank = 2
            matches.append(
                (
                    rank,
                    sheet_order,
                    row_index,
                    {
                        "sheet": sheet["name"],
                        "row": row_index,
                        "record": record,
                    },
                )
            )
    matches.sort(key=lambda item: item[:3])
    return [item[3] for item in matches[:limit]]


def main(argv: list[str] | None = None) -> int:
    # Machine-readable output must not depend on the active Windows code page.
    # The tests and downstream callers consume JSON as UTF-8 bytes.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--query", required=True)
    parser.add_argument("--sheet")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        results = query_library(
            args.library, args.query, sheet_name=args.sheet, limit=args.limit
        )
    except (OSError, ValueError, json.JSONDecodeError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for result in results:
            print(f"[{result['sheet']} row {result['row']}]")
            print(json.dumps(result["record"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
