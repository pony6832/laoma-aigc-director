"""Safely initialize a versioned Laoma AIGC director project."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_DIRS = (
    "01_inputs",
    "02_character_and_look",
    "03_story_and_script",
    "04_shot_design",
    "05_generation_prompts",
    "06_generated_assets",
    "07_sound_and_music",
    "08_edit_and_delivery",
    "09_reports_and_qc",
)

TEMPLATE_TARGETS = {
    "project-brief-template.md": "PROJECT_BRIEF.md",
    "production-bible-template.md": "PRODUCTION_BIBLE.md",
    "character-profile-template.json": "CHARACTER_PROFILE.json",
    "shot-production-table-template.md": "04_shot_design/SHOT_PRODUCTION_TABLE.md",
    "generation-report-template.md": "09_reports_and_qc/GENERATION_REPORT.md",
}

_WINDOWS_FORBIDDEN = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_WINDOWS_RESERVED = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}


def _validate_project_name(project_name: str) -> None:
    if not isinstance(project_name, str) or not project_name.strip():
        raise ValueError("project_name must not be empty")
    if project_name in {".", ".."} or _WINDOWS_FORBIDDEN.search(project_name):
        raise ValueError("project_name contains invalid path characters")
    if project_name[-1] in {".", " "}:
        raise ValueError("project_name contains invalid trailing characters")
    if project_name.split(".", 1)[0].upper() in _WINDOWS_RESERVED:
        raise ValueError("project_name uses a reserved Windows device name")


def create_project(projects_root: Path, project_name: str) -> Path:
    """Create and return the first unused ``<name>_VNN`` project directory."""
    _validate_project_name(project_name)
    root = Path(projects_root).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    template_root = Path(__file__).resolve().parents[1] / "assets"

    for version in range(1, 1000):
        version_label = f"V{version:02d}"
        project_dir = root / f"{project_name}_{version_label}"
        try:
            project_dir.mkdir(exist_ok=False)
        except FileExistsError:
            continue

        try:
            for directory in PROJECT_DIRS:
                (project_dir / directory).mkdir()
            for source_name, target_name in TEMPLATE_TARGETS.items():
                source = template_root / source_name
                target = project_dir / target_name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
            state = {
                "schema_version": "1.0",
                "project_name": project_name,
                "project_version": version_label,
                "current_gate": 1,
                "status": "draft",
                "locked_artifacts": [],
                "open_decisions": [],
                "asset_status": {},
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            (project_dir / "PROJECT_STATE.json").write_text(
                json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
        except Exception:
            # Do not touch any pre-existing project; remove only our new shell.
            shutil.rmtree(project_dir, ignore_errors=True)
            raise
        return project_dir
    raise RuntimeError("no available project version")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path, dest="projects_root")
    parser.add_argument("--name", required=True, dest="project_name")
    args = parser.parse_args(argv)
    try:
        print(create_project(args.projects_root, args.project_name))
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
