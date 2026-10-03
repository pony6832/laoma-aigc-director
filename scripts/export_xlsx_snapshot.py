"""Convert an .xlsx export of the cloud master sheet into a snapshot payload.

The weekly job exports the personal master spreadsheet from Google Drive as
.xlsx, runs this script, then feeds the JSON to build_evolving_library.py.
Only visible sheets are managed knowledge; hidden sheets (source mapping,
archives) stay in the cloud for provenance and are not loaded by the agent.

Standard library only: the scheduled job may run under a Python without
openpyxl, and a missing package must not silently stop the local sync.
"""

from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta
import json
from pathlib import Path, PurePosixPath
import re
import sys
import zipfile
from xml.etree import ElementTree

try:
    from scripts.build_evolving_library import SOURCE_ID
except ImportError:  # run as `python scripts/export_xlsx_snapshot.py`
    from build_evolving_library import SOURCE_ID

_NS = {
    "m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}
_BUILTIN_DATE_FORMATS = set(range(14, 23)) | {45, 46, 47}
_CELL_REF = re.compile(r"^([A-Z]+)(\d+)$")
_EPOCH = datetime(1899, 12, 30)


def _column_index(letters: str) -> int:
    index = 0
    for char in letters:
        index = index * 26 + (ord(char) - 64)
    return index - 1


def _column_letter(index: int) -> str:
    letters = ""
    index += 1
    while index:
        index, rem = divmod(index - 1, 26)
        letters = chr(65 + rem) + letters
    return letters


def _text(node) -> str:
    return "".join(t.text or "" for t in node.iter(f"{{{_NS['m']}}}t"))


def _is_date_format(code: str) -> bool:
    stripped = re.sub(r'"[^"]*"|\[[^\]]*\]|\\.', "", code)
    return bool(re.search(r"[yd]", stripped, re.IGNORECASE)) or "mm/" in stripped.lower()


def _date_styles(archive: zipfile.ZipFile) -> set[int]:
    try:
        root = ElementTree.fromstring(archive.read("xl/styles.xml"))
    except KeyError:
        return set()
    custom = {
        int(fmt.get("numFmtId")): fmt.get("formatCode", "")
        for fmt in root.iter(f"{{{_NS['m']}}}numFmt")
    }
    styles = set()
    xfs = root.find("m:cellXfs", _NS)
    for index, xf in enumerate(xfs if xfs is not None else []):
        fmt_id = int(xf.get("numFmtId", "0"))
        if fmt_id in _BUILTIN_DATE_FORMATS or (fmt_id in custom and _is_date_format(custom[fmt_id])):
            styles.add(index)
    return styles


def _number(raw: str, is_date: bool) -> str:
    value = float(raw)
    if is_date:
        moment = _EPOCH + timedelta(days=value)
        return moment.date().isoformat() if value.is_integer() else moment.isoformat()
    if value.is_integer():
        return str(int(value))
    return raw


def _read_sheet(archive, path, shared, date_styles) -> tuple[list[list[str]], int]:
    root = ElementTree.fromstring(archive.read(path))
    cells: dict[int, dict[int, str]] = {}
    max_col = 0
    for cell in root.iter(f"{{{_NS['m']}}}c"):
        match = _CELL_REF.match(cell.get("r", ""))
        if not match:
            continue
        col, row = _column_index(match.group(1)), int(match.group(2))
        kind = cell.get("t", "n")
        value_node = cell.find("m:v", _NS)
        raw = value_node.text if value_node is not None and value_node.text is not None else ""
        if kind == "s":
            value = shared[int(raw)] if raw else ""
        elif kind == "inlineStr":
            inline = cell.find("m:is", _NS)
            value = _text(inline) if inline is not None else ""
        elif kind == "b":
            value = "TRUE" if raw == "1" else ("FALSE" if raw else "")
        elif kind in ("str", "e"):
            value = raw
        else:
            value = _number(raw, int(cell.get("s", "0")) in date_styles) if raw else ""
        if value != "":
            cells.setdefault(row, {})[col] = value
            max_col = max(max_col, col + 1)
    last_row = max(cells, default=0)
    rows = []
    for row in range(1, last_row + 1):
        values = cells.get(row, {})
        width = max(values, default=-1) + 1
        rows.append([values.get(col, "") for col in range(width)])
    return rows, max_col


def _header_row(rows: list[list[str]]) -> int:
    """Return the 1-based header row: the first row with at least three cells.

    Sheets 19 and 22 start with merged title/rule rows; their table header is
    the first row that actually spans several columns.
    """
    for index, row in enumerate(rows, start=1):
        if sum(1 for cell in row if cell.strip()) >= 3:
            return index
    return 1


def export(xlsx: Path, captured_at: str, include_hidden: bool = False) -> dict:
    date.fromisoformat(captured_at)
    with zipfile.ZipFile(xlsx) as archive:
        try:
            shared = [
                _text(item)
                for item in ElementTree.fromstring(archive.read("xl/sharedStrings.xml")).findall("m:si", _NS)
            ]
        except KeyError:
            shared = []
        date_styles = _date_styles(archive)
        rels = {
            rel.get("Id"): rel.get("Target")
            for rel in ElementTree.fromstring(archive.read("xl/_rels/workbook.xml.rels")).findall("rel:Relationship", _NS)
        }
        workbook = ElementTree.fromstring(archive.read("xl/workbook.xml"))
        sheets = []
        for sheet in workbook.find("m:sheets", _NS):
            if sheet.get("state", "visible") != "visible" and not include_hidden:
                continue
            target = rels[sheet.get(f"{{{_NS['r']}}}id")]
            path = target.lstrip("/") if target.startswith("/") else str(PurePosixPath("xl") / target)
            rows, max_col = _read_sheet(archive, path, shared, date_styles)
            sheets.append(
                {
                    "name": sheet.get("name"),
                    "source_range": f"A1:{_column_letter(max(0, max_col - 1))}{max(1, len(rows))}",
                    "header_row": _header_row(rows),
                    "rows": rows,
                }
            )
    return {"spreadsheet_id": SOURCE_ID, "captured_at": captured_at, "sheets": sheets}


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xlsx", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--captured-at", default=date.today().isoformat())
    parser.add_argument("--include-hidden", action="store_true")
    args = parser.parse_args(argv)
    payload = export(args.xlsx, args.captured_at, args.include_hidden)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    for sheet in payload["sheets"]:
        print(f"{sheet['name']}\theader_row={sheet['header_row']}\trows={len(sheet['rows'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
