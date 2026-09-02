"""Validate a Laoma AIGC director project's structure and production gates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


VALID_STATUSES = {"draft", "awaiting_approval", "approved", "blocked", "complete"}
REQUIRED_DIRECTORIES = (
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
REQUIRED_ROOT_FILES = (
    "PROJECT_STATE.json",
    "PROJECT_BRIEF.md",
    "PRODUCTION_BIBLE.md",
    "CHARACTER_PROFILE.json",
)
GATE_REQUIREMENTS = {
    1: ("PROJECT_BRIEF.md",),
    2: ("CHARACTER_PROFILE.json", "02_character_and_look"),
    3: ("03_story_and_script", "04_shot_design/SHOT_PRODUCTION_TABLE.md"),
    4: ("09_reports_and_qc/GENERATION_REPORT.md",),
}
STATE_FIELD_TYPES = (
    ("schema_version", str, "str"),
    ("project_name", str, "str"),
    ("project_version", str, "str"),
    ("locked_artifacts", list, "list"),
    ("open_decisions", list, "list"),
    ("asset_status", dict, "object"),
    ("created_at", str, "str"),
)


def _load_json(path: Path, label: str, errors: list[str]) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid JSON: {label} ({exc})")
        return None
    if not isinstance(data, dict):
        errors.append(f"invalid JSON object: {label}")
        return None
    return data


def _require_path(project_dir: Path, requirement: str, errors: list[str]) -> None:
    path = project_dir / requirement
    kind = "directory" if requirement in REQUIRED_DIRECTORIES else "file"
    if (path.is_dir() if kind == "directory" else path.is_file()):
        return
    errors.append(f"missing {kind}: {requirement}")


def _validate_state(state: dict) -> list[str]:
    errors: list[str] = []
    for field in ("schema_version", "project_name", "project_version"):
        if field not in state:
            errors.append(f"missing PROJECT_STATE field: {field}")
        elif not isinstance(state[field], str):
            errors.append(f"invalid PROJECT_STATE field: {field} (expected str)")

    current_gate = state.get("current_gate")
    if "current_gate" not in state:
        errors.append("missing PROJECT_STATE field: current_gate")
    elif not isinstance(current_gate, int) or isinstance(current_gate, bool) or current_gate not in GATE_REQUIREMENTS:
        errors.append("invalid PROJECT_STATE field: current_gate (expected int from 1 to 4)")

    status = state.get("status")
    if "status" not in state:
        errors.append("missing PROJECT_STATE field: status")
    elif not isinstance(status, str):
        errors.append("invalid project status: expected str")
    elif status not in VALID_STATUSES:
        errors.append(f"invalid project status: {status!r}")

    for field, expected_type, expected_name in STATE_FIELD_TYPES[3:]:
        if field not in state:
            errors.append(f"missing PROJECT_STATE field: {field}")
        elif not isinstance(state[field], expected_type):
            errors.append(f"invalid PROJECT_STATE field: {field} (expected {expected_name})")
    return errors


def validate_project(project_dir: Path) -> list[str]:
    """Return actionable validation errors for ``project_dir`` in stable order."""
    project_dir = Path(project_dir)
    errors: list[str] = []

    for directory in REQUIRED_DIRECTORIES:
        if not (project_dir / directory).is_dir():
            errors.append(f"missing directory: {directory}")
    for filename in REQUIRED_ROOT_FILES:
        if not (project_dir / filename).is_file():
            errors.append(f"missing file: {filename}")

    state_path = project_dir / "PROJECT_STATE.json"
    if not state_path.is_file():
        return errors
    state = _load_json(state_path, "PROJECT_STATE.json", errors)
    if state is None:
        return errors

    errors.extend(_validate_state(state))
    if errors:
        return errors

    current_gate = state["current_gate"]
    status = state["status"]

    for gate in range(1, current_gate + 1):
        for requirement in GATE_REQUIREMENTS[gate]:
            _require_path(project_dir, requirement, errors)

    if current_gate >= 2:
        profile_path = project_dir / "CHARACTER_PROFILE.json"
        if profile_path.is_file():
            profile = _load_json(profile_path, "CHARACTER_PROFILE.json", errors)
            if profile is not None and profile.get("status") != "approved":
                errors.append("Gate 2 requires approved CHARACTER_PROFILE.json")

    if current_gate >= 3:
        locked_artifacts = state.get("locked_artifacts")
        for artifact in ("PRODUCTION_BIBLE.md", "CHARACTER_PROFILE.json"):
            if artifact not in locked_artifacts:
                errors.append(f"Gate 3 requires locked artifact: {artifact}")

    if current_gate >= 4 and status == "complete":
        report_path = project_dir / "09_reports_and_qc" / "GENERATION_REPORT.md"
        if report_path.is_file():
            try:
                report = report_path.read_text(encoding="utf-8")
            except OSError as exc:
                errors.append(f"unable to read GENERATION_REPORT.md: {exc}")
            else:
                if "已知限制" not in report:
                    errors.append("Gate 4 complete project requires GENERATION_REPORT.md to contain 已知限制")
        asset_status = state.get("asset_status")
        if asset_status.get("claimed_complete_without_output") is True:
            errors.append("Gate 4 complete project cannot claim complete without output")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_directory", type=Path)
    args = parser.parse_args(argv)
    errors = validate_project(args.project_directory)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("PROJECT_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
