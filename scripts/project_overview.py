"""List every director project under a root with its gate, state and drift warnings.

Use this before reporting "where are my projects": the per-project validator
only answers for one folder, and a folder nobody opens never gets checked.
Folders whose names start with "_" (for example _封存) are skipped.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import sys

try:
    from scripts.validate_project import _is_tool_internal, audit_project, validate_project
except ImportError:  # run as `python scripts/project_overview.py`
    from validate_project import _is_tool_internal, audit_project, validate_project


def overview(root: Path) -> list[dict]:
    rows = []
    for project in sorted(Path(root).iterdir()):
        if not project.is_dir() or project.name.startswith("_"):
            continue
        state_path = project / "PROJECT_STATE.json"
        if not state_path.is_file():
            continue
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            state = {}
        files = [p for p in project.rglob("*") if p.is_file() and not _is_tool_internal(p)]
        last = max((p.stat().st_mtime for p in files), default=state_path.stat().st_mtime)
        errors = validate_project(project)
        rows.append(
            {
                "project": project.name,
                "gate": state.get("current_gate"),
                "status": state.get("status"),
                "locked": len(state.get("locked_artifacts") or []),
                "open_decisions": [
                    d.get("id")
                    for d in state.get("open_decisions") or []
                    if isinstance(d, dict) and d.get("status") == "open"
                ],
                "last_activity": datetime.fromtimestamp(last).strftime("%Y-%m-%d %H:%M"),
                "errors": errors,
                "warnings": [] if errors else audit_project(project),
            }
        )
    return rows


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    rows = overview(args.root)
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0
    for row in rows:
        verdict = "INVALID" if row["errors"] else ("DRIFT" if row["warnings"] else "OK")
        decisions = ",".join(row["open_decisions"]) or "-"
        print(
            f"{verdict:7} Gate {row['gate']} {row['status']:<17} locks={row['locked']:<2} "
            f"open={decisions:<12} last={row['last_activity']}  {row['project']}"
        )
        for message in row["errors"]:
            print(f"        ERROR: {message}")
        for message in row["warnings"]:
            print(f"        WARNING: {message}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
