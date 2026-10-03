"""Verify and publish a read-back cloud snapshot for the director knowledge library."""
import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import re

SOURCE_ID = "1E9MrvDlFdCEpLQ8RbARLi8gSomQaYWb25Kxik_xIIdc"

def publish(payload, library, version):
    library = Path(library)
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}-[A-Za-z0-9_-]+", version):
        raise ValueError("invalid snapshot version")
    date.fromisoformat(version[:10])
    if payload.get("spreadsheet_id") != SOURCE_ID:
        raise ValueError("wrong cloud source")
    sheets = payload["sheets"]
    names = [s["name"] for s in sheets]
    if len(names) != len(set(names)):
        raise ValueError("duplicate sheet")
    by_name = {s["name"]: s for s in sheets}
    for required_sheet in ("02_提示詞總庫", "05_來源登錄"):
        if required_sheet not in by_name:
            raise ValueError(f"missing required sheet: {required_sheet}")
    catalog = by_name["02_提示詞總庫"]
    sources = by_name["05_來源登錄"]
    source_header = sources.get("header_row", 1)
    source_ids = {r[0] for r in sources["rows"][source_header:] if r}
    catalog_header = catalog.get("header_row", 1)
    headers = catalog["rows"][catalog_header - 1]
    required = ["知識ID", "中文名稱", "主分類", "來源ID", "證據等級", "實測狀態", "生命週期", "查核日期"]
    if any(k not in headers for k in required):
        raise ValueError("missing required column")
    seen = set()
    for row in catalog["rows"][catalog_header:]:
        if not any(row):
            continue
        record = dict(zip(headers, row))
        if any(not record.get(k) for k in required):
            raise ValueError("missing provenance")
        if record["知識ID"] in seen:
            raise ValueError("duplicate knowledge id")
        seen.add(record["知識ID"])
        if record["來源ID"] not in source_ids:
            raise ValueError("unknown source id")
        if record["生命週期"] not in {"可參考", "待查證", "停用"}:
            raise ValueError("invalid lifecycle")
        if record["實測狀態"] not in {"未實測", "實測通過", "實測失敗"}:
            raise ValueError("invalid test status")
        if record["主分類"] == "通用指令":
            raise ValueError("office general command is not allowed in director snapshot")
    target = library / version
    if target.exists():
        raise FileExistsError(target)
    target.mkdir(parents=True)
    manifest = {"schema_version":"2.0", "spreadsheet_id":SOURCE_ID,
                "captured_at":payload["captured_at"], "version":version, "sheets":[]}
    for i, sheet in enumerate(sheets):
        filename = f"sheet-{i:02d}.json"
        header_row = sheet.get("header_row", 1)
        if not isinstance(header_row, int) or not 1 <= header_row <= max(1, len(sheet["rows"])):
            raise ValueError(f"invalid header_row for sheet: {sheet['name']}")
        content = dict(sheet, header_row=header_row)
        path = target / filename
        path.write_text(json.dumps(content, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        manifest["sheets"].append({"name":sheet["name"], "file":filename,
             "sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
    (target / "manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
    active = library / "active.json"
    pending = library / "active.pending.json"
    pending.write_text(json.dumps({"snapshot":version, "captured_at":payload["captured_at"]},ensure_ascii=False)+"\n",encoding="utf-8",newline="\n")
    pending.replace(active)
    return target

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--version", required=True)
    args=parser.parse_args()
    print(publish(json.loads(args.input.read_text(encoding="utf-8")), args.library, args.version))

if __name__ == "__main__":
    main()
