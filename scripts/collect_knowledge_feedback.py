"""Collect real test results from projects so the weekly job can write them to sheet 06.

Each project may keep ``09_reports_and_qc/KNOWLEDGE_FEEDBACK.jsonl``: one JSON
object per line, written when a short test or Gate 4 QC finishes (pass OR
fail).  Keys match the cloud sheet ``06_實測與失敗`` so rows copy across without
re-interpretation, plus provenance keys:

    回饋ID, 來源案件, 平台, 知識ID, 假說, 固定條件, 唯一變量, 驗收條件,
    輸出與證據, 結果, 日期, 教訓, 已同步

``結果`` is one of 實測通過 / 實測失敗 / 部分通過.  ``已同步`` stays empty until the
weekly job has written the row to the personal master AND read it back; only
then is it marked with ``--mark-synced``.
"""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import sys

FEEDBACK_FILE = Path("09_reports_and_qc") / "KNOWLEDGE_FEEDBACK.jsonl"
REQUIRED = ("回饋ID", "來源案件", "平台", "假說", "驗收條件", "輸出與證據", "結果", "日期")
RESULTS = {"實測通過", "實測失敗", "部分通過"}


def _read(path: Path) -> list[dict]:
    entries = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        entry = json.loads(line)
        missing = [key for key in REQUIRED if not str(entry.get(key) or "").strip()]
        if missing:
            raise ValueError(f"{path}:{number} missing {', '.join(missing)}")
        if entry["結果"] not in RESULTS:
            raise ValueError(f"{path}:{number} invalid 結果: {entry['結果']}")
        entries.append(entry)
    return entries


def collect(root: Path, include_synced: bool = False) -> list[dict]:
    found = []
    for project in sorted(Path(root).iterdir()):
        path = project / FEEDBACK_FILE
        if project.is_dir() and not project.name.startswith("_") and path.is_file():
            for entry in _read(path):
                if include_synced or not entry.get("已同步"):
                    found.append(entry)
    ids = [entry["回饋ID"] for entry in found]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate 回饋ID across projects")
    return found


def mark_synced(root: Path, feedback_ids: set[str], synced_at: str) -> int:
    marked = 0
    for project in sorted(Path(root).iterdir()):
        path = project / FEEDBACK_FILE
        if not (project.is_dir() and path.is_file()):
            continue
        entries = _read(path)
        changed = False
        for entry in entries:
            if entry["回饋ID"] in feedback_ids and not entry.get("已同步"):
                entry["已同步"] = synced_at
                changed = True
                marked += 1
        if changed:
            path.write_text(
                "".join(json.dumps(entry, ensure_ascii=False) + "\n" for entry in entries),
                encoding="utf-8",
                newline="\n",
            )
    return marked


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--all", action="store_true", help="include already-synced entries")
    parser.add_argument("--mark-synced", nargs="+", metavar="回饋ID")
    parser.add_argument("--synced-at", default=date.today().isoformat())
    args = parser.parse_args(argv)
    try:
        if args.mark_synced:
            count = mark_synced(args.root, set(args.mark_synced), args.synced_at)
            print(f"marked {count} entr{'y' if count == 1 else 'ies'} as synced")
            return 0 if count == len(set(args.mark_synced)) else 1
        print(json.dumps(collect(args.root, args.all), ensure_ascii=False, indent=2))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
