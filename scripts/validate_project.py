"""Validate a Laoma AIGC director project's structure and production gates."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import BinaryIO, Iterator
from xml.etree import ElementTree


SUPPORTED_SCHEMA_VERSION = "1.0"
VALID_STATUSES = {"draft", "awaiting_approval", "approved", "blocked", "complete"}
GATE_STATUS_MATRIX = {
    1: {"draft", "awaiting_approval", "approved", "blocked"},
    2: {"draft", "awaiting_approval", "approved", "blocked"},
    3: {"draft", "awaiting_approval", "approved", "blocked"},
    4: {"draft", "awaiting_approval", "blocked", "complete"},
}
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
GATE_TWO_LOCK_ROLES = (
    "project_brief",
    "production_bible",
    "character_profile",
    "character_overview_board",
    "character_free_scene_board",
    "consistency_test",
)
GATE_THREE_LOCK_ROLES = (
    "story_script",
    "shot_production_table",
    "generation_plan",
)
_PROJECT_VERSION = re.compile(r"^V\d{2,}$")
_ARTIFACT_VERSION = re.compile(r"^v\d{2,}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_ROLE = re.compile(r"^[a-z][a-z0-9_]*$")
_GATE_TWO_IMAGE_ROLES = {
    "character_overview_board",
    "character_free_scene_board",
}
_IMAGE_SUFFIXES = {".bmp", ".gif", ".jpeg", ".jpg", ".png", ".svg", ".tif", ".tiff", ".webp"}
_CONSISTENCY_MEDIA_SUFFIXES = {".mov", ".mp4"}


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


def _is_nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_timezone_aware_iso8601(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _is_inside(target: Path, root: Path) -> bool:
    try:
        target.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _is_supported_image_file(path: Path) -> bool:
    suffix = path.suffix.lower()
    if suffix not in _IMAGE_SUFFIXES or path.stat().st_size == 0:
        return False
    if suffix == ".svg":
        try:
            root = ElementTree.parse(path).getroot()
        except (ElementTree.ParseError, OSError):
            return False
        return root.tag.rsplit("}", 1)[-1].lower() == "svg"
    with path.open("rb") as stream:
        head = stream.read(16)
        if suffix == ".png":
            return head.startswith(b"\x89PNG\r\n\x1a\n")
        if suffix in {".jpg", ".jpeg"}:
            return head.startswith(b"\xff\xd8\xff")
        if suffix == ".gif":
            return head.startswith((b"GIF87a", b"GIF89a"))
        if suffix == ".bmp":
            return head.startswith(b"BM")
        if suffix in {".tif", ".tiff"}:
            return head.startswith((b"II*\x00", b"MM\x00*"))
        if suffix == ".webp":
            return head.startswith(b"RIFF") and head[8:12] == b"WEBP"
    return False


def _iter_iso_bmff_boxes(
    stream: BinaryIO, start: int, end: int
) -> Iterator[tuple[bytes, int, int]]:
    position = start
    while position + 8 <= end:
        stream.seek(position)
        header = stream.read(8)
        if len(header) != 8:
            return
        size = int.from_bytes(header[:4], "big")
        box_type = header[4:8]
        header_size = 8
        if size == 1:
            extended = stream.read(8)
            if len(extended) != 8:
                return
            size = int.from_bytes(extended, "big")
            header_size = 16
        elif size == 0:
            size = end - position
        if size < header_size or position + size > end:
            return
        yield box_type, position + header_size, position + size
        position += size


def _read_iso_bmff_duration(path: Path) -> float | None:
    try:
        with path.open("rb") as stream:
            stream.seek(0, 2)
            file_size = stream.tell()
            top_level = list(_iter_iso_bmff_boxes(stream, 0, file_size))
            has_ftyp = any(box_type == b"ftyp" for box_type, _, _ in top_level)
            has_media_data = any(
                box_type == b"mdat" and payload_end > payload_start
                for box_type, payload_start, payload_end in top_level
            )
            moov = next(
                (
                    (payload_start, payload_end)
                    for box_type, payload_start, payload_end in top_level
                    if box_type == b"moov"
                ),
                None,
            )
            if not has_ftyp or not has_media_data or moov is None:
                return None
            moov_children = list(_iter_iso_bmff_boxes(stream, *moov))
            if not any(box_type == b"trak" for box_type, _, _ in moov_children):
                return None
            mvhd = next(
                (
                    (payload_start, payload_end)
                    for box_type, payload_start, payload_end in moov_children
                    if box_type == b"mvhd"
                ),
                None,
            )
            if mvhd is None:
                return None
            stream.seek(mvhd[0])
            version_flags = stream.read(4)
            if len(version_flags) != 4:
                return None
            if version_flags[0] == 0:
                fields = stream.read(16)
                if len(fields) != 16:
                    return None
                timescale = int.from_bytes(fields[8:12], "big")
                duration = int.from_bytes(fields[12:16], "big")
            elif version_flags[0] == 1:
                fields = stream.read(28)
                if len(fields) != 28:
                    return None
                timescale = int.from_bytes(fields[16:20], "big")
                duration = int.from_bytes(fields[20:28], "big")
            else:
                return None
            if timescale <= 0 or duration <= 0:
                return None
            return duration / timescale
    except OSError:
        return None


def _resolve_project_file(
    project_dir: Path,
    relative_path: object,
    label: str,
    errors: list[str],
) -> Path | None:
    if not _is_nonempty_string(relative_path):
        errors.append(f"invalid {label} path: expected non-empty string")
        return None
    if Path(relative_path).is_absolute():
        errors.append(f"unsafe {label} path: {relative_path}")
        return None
    root = project_dir.resolve()
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        errors.append(f"unsafe {label} path: {relative_path}")
        return None
    if not candidate.is_file():
        errors.append(f"{label} file does not exist: {relative_path}")
        return None
    return candidate


def _validate_open_decisions(open_decisions: list, errors: list[str]) -> None:
    for index, decision in enumerate(open_decisions):
        label = f"open_decisions[{index}]"
        if not isinstance(decision, dict):
            errors.append(f"invalid {label}: expected object")
            continue
        for field in ("id", "question", "status", "opened_at"):
            if field not in decision:
                errors.append(f"missing {label} field: {field}")
        if "id" in decision and not _is_nonempty_string(decision["id"]):
            errors.append(f"invalid {label}.id: expected non-empty string")
        if "question" in decision and not _is_nonempty_string(decision["question"]):
            errors.append(f"invalid {label}.question: expected non-empty string")
        if "status" in decision and decision["status"] not in {"open", "resolved"}:
            errors.append(f"invalid {label}.status: expected 'open' or 'resolved'")
        if "opened_at" in decision and not _is_timezone_aware_iso8601(decision["opened_at"]):
            errors.append(
                f"invalid {label}.opened_at: expected timezone-aware ISO 8601"
            )


def _validate_check_items(checks: object, errors: list[str]) -> None:
    if not isinstance(checks, list):
        errors.append("invalid asset_status.qc.checks: expected list")
        return
    for index, check in enumerate(checks):
        label = f"asset_status.qc.checks[{index}]"
        if not isinstance(check, dict):
            errors.append(f"invalid {label}: expected object")
            continue
        for field in ("name", "status", "evidence"):
            if field not in check:
                errors.append(f"missing {label} field: {field}")
        if "name" in check and not _is_nonempty_string(check["name"]):
            errors.append(f"invalid {label}.name: expected non-empty string")
        if "status" in check and check["status"] not in {"pending", "passed", "failed"}:
            errors.append(f"invalid {label}.status")
        if "evidence" in check and not isinstance(check["evidence"], str):
            errors.append(f"invalid {label}.evidence: expected str")


def _validate_asset_status_shape(asset_status: dict, errors: list[str]) -> None:
    for field in ("claimed_complete_without_output", "outputs", "qc", "approval"):
        if field not in asset_status:
            errors.append(f"missing asset_status field: {field}")

    claimed = asset_status.get("claimed_complete_without_output")
    if "claimed_complete_without_output" in asset_status and not isinstance(claimed, bool):
        errors.append(
            "invalid asset_status.claimed_complete_without_output: expected bool"
        )
    outputs = asset_status.get("outputs")
    if "outputs" in asset_status and not isinstance(outputs, list):
        errors.append("invalid asset_status.outputs: expected list")

    qc = asset_status.get("qc")
    if "qc" in asset_status and not isinstance(qc, dict):
        errors.append("invalid asset_status.qc: expected object")
    elif isinstance(qc, dict):
        for field in ("status", "checked_at", "checked_by", "checks"):
            if field not in qc:
                errors.append(f"missing asset_status.qc field: {field}")
        if "status" in qc and qc["status"] not in {
            "not_started",
            "pending",
            "passed",
            "failed",
        }:
            errors.append("invalid asset_status.qc.status")
        if "checked_at" in qc and qc["checked_at"] is not None and not _is_timezone_aware_iso8601(qc["checked_at"]):
            errors.append(
                "invalid asset_status.qc.checked_at: expected null or timezone-aware ISO 8601"
            )
        if "checked_by" in qc and not isinstance(qc["checked_by"], str):
            errors.append("invalid asset_status.qc.checked_by: expected str")
        if "checks" in qc:
            _validate_check_items(qc["checks"], errors)

    approval = asset_status.get("approval")
    if "approval" in asset_status and not isinstance(approval, dict):
        errors.append("invalid asset_status.approval: expected object")
    elif isinstance(approval, dict):
        for field in ("status", "approved_at", "approved_by", "scope"):
            if field not in approval:
                errors.append(f"missing asset_status.approval field: {field}")
        if "status" in approval and approval["status"] not in {
            "not_requested",
            "pending",
            "approved",
            "rejected",
        }:
            errors.append("invalid asset_status.approval.status")
        if "approved_at" in approval and approval["approved_at"] is not None and not _is_timezone_aware_iso8601(approval["approved_at"]):
            errors.append(
                "invalid asset_status.approval.approved_at: expected null or timezone-aware ISO 8601"
            )
        if "approved_by" in approval and not isinstance(approval["approved_by"], str):
            errors.append("invalid asset_status.approval.approved_by: expected str")
        if "scope" in approval and not isinstance(approval["scope"], list):
            errors.append("invalid asset_status.approval.scope: expected list")


def _validate_locked_artifacts(
    project_dir: Path,
    locked_artifacts: list,
    errors: list[str],
) -> dict[str, dict]:
    roles: dict[str, dict] = {}
    for index, artifact in enumerate(locked_artifacts):
        label = f"locked_artifacts[{index}]"
        if not isinstance(artifact, dict):
            errors.append(f"invalid {label}: expected object")
            continue
        for field in ("role", "path", "version", "sha256", "reason"):
            if field not in artifact:
                errors.append(f"missing {label} field: {field}")

        role = artifact.get("role")
        if "role" in artifact and (
            not _is_nonempty_string(role) or _ROLE.fullmatch(role) is None
        ):
            errors.append(f"invalid {label}.role: expected snake_case string")
        elif isinstance(role, str):
            if role in roles:
                errors.append(f"duplicate locked artifact role: {role}")
            else:
                roles[role] = artifact

        version = artifact.get("version")
        if "version" in artifact and (
            not isinstance(version, str) or _ARTIFACT_VERSION.fullmatch(version) is None
        ):
            errors.append(f"invalid {label}.version: expected v followed by at least two digits")

        reason = artifact.get("reason")
        if "reason" in artifact and not _is_nonempty_string(reason):
            errors.append(f"invalid {label}.reason: expected non-empty string")

        expected_hash = artifact.get("sha256")
        hash_is_valid = isinstance(expected_hash, str) and _SHA256.fullmatch(expected_hash) is not None
        if "sha256" in artifact and not hash_is_valid:
            errors.append(f"invalid {label}.sha256: expected lowercase SHA-256")

        path_value = artifact.get("path")
        target = None
        if "path" in artifact:
            target = _resolve_project_file(project_dir, path_value, label, errors)
        if target is not None and hash_is_valid and _sha256(target) != expected_hash:
            errors.append(f"{label} sha256 mismatch: {path_value}")

        if role in _GATE_TWO_IMAGE_ROLES and target is not None:
            if not _is_inside(target, project_dir / "02_character_and_look"):
                errors.append(
                    f"{role} path must be inside 02_character_and_look"
                )
            if target.stat().st_size == 0:
                errors.append(f"{role} file is empty: {path_value}")
            elif not _is_supported_image_file(target):
                errors.append(f"{role} path must be a supported image file")

        if role == "consistency_test":
            duration = artifact.get("duration_seconds")
            if (
                not isinstance(duration, (int, float))
                or isinstance(duration, bool)
                or not 4 <= duration <= 6
            ):
                errors.append(
                    "consistency_test duration_seconds must be between 4 and 6"
                )
            if target is not None:
                if not _is_inside(target, project_dir / "02_character_and_look"):
                    errors.append(
                        "consistency_test path must be inside 02_character_and_look"
                    )
                if target.stat().st_size == 0:
                    errors.append(f"consistency_test file is empty: {path_value}")
                elif target.suffix.lower() not in _CONSISTENCY_MEDIA_SUFFIXES:
                    errors.append(
                        "consistency_test path must be an MP4 or MOV media file"
                    )
                else:
                    measured_duration = _read_iso_bmff_duration(target)
                    if measured_duration is None:
                        errors.append(
                            "consistency_test media duration could not be verified "
                            "from MP4/MOV container"
                        )
                    else:
                        if not 4 <= measured_duration <= 6:
                            errors.append(
                                "consistency_test media duration must be between 4 and 6"
                            )
                        if (
                            isinstance(duration, (int, float))
                            and not isinstance(duration, bool)
                            and abs(float(duration) - measured_duration) > 0.05
                        ):
                            errors.append(
                                "consistency_test duration_seconds does not match media duration"
                            )
    return roles


def _validate_output_entries(
    project_dir: Path,
    outputs: list,
    errors: list[str],
) -> None:
    for index, output in enumerate(outputs):
        label = f"asset_status.outputs[{index}]"
        if not isinstance(output, dict):
            errors.append(f"invalid {label}: expected object")
            continue
        for field in ("path", "version", "sha256", "kind"):
            if field not in output:
                errors.append(f"missing {label} field: {field}")

        path_value = output.get("path")
        target = None
        if "path" in output:
            target = _resolve_project_file(project_dir, path_value, label, errors)
        if target is not None and not _is_inside(
            target, project_dir / "06_generated_assets"
        ):
            errors.append(f"{label} path must be inside 06_generated_assets")

        version = output.get("version")
        if "version" in output and (
            not isinstance(version, str) or _ARTIFACT_VERSION.fullmatch(version) is None
        ):
            errors.append(f"invalid {label}.version: expected v followed by at least two digits")
        kind = output.get("kind")
        if "kind" in output and not _is_nonempty_string(kind):
            errors.append(f"invalid {label}.kind: expected non-empty string")
        expected_hash = output.get("sha256")
        hash_is_valid = isinstance(expected_hash, str) and _SHA256.fullmatch(expected_hash) is not None
        if "sha256" in output and not hash_is_valid:
            errors.append(f"invalid {label}.sha256: expected lowercase SHA-256")
        if target is not None:
            if target.stat().st_size == 0:
                errors.append(f"Gate 4 complete output is empty: {path_value}")
            if hash_is_valid and _sha256(target) != expected_hash:
                errors.append(f"{label} sha256 mismatch: {path_value}")


def _validate_state_shape(state: dict) -> list[str]:
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


def _validate_state_details(
    project_dir: Path,
    state: dict,
    errors: list[str],
) -> dict[str, dict]:
    if state["schema_version"] != SUPPORTED_SCHEMA_VERSION:
        errors.append(
            "unsupported PROJECT_STATE schema_version: "
            f"{state['schema_version']!r} (expected {SUPPORTED_SCHEMA_VERSION!r})"
        )

    project_version = state["project_version"]
    version_is_valid = _PROJECT_VERSION.fullmatch(project_version) is not None
    if not version_is_valid:
        errors.append(
            f"invalid project_version: {project_version!r} "
            "(expected V followed by at least two digits)"
        )
    elif _is_nonempty_string(state["project_name"]):
        expected_name = f"{state['project_name']}_{project_version}"
        if project_dir.name != expected_name:
            errors.append(
                f"project directory mismatch: expected {expected_name}, found {project_dir.name}"
            )

    if not _is_timezone_aware_iso8601(state["created_at"]):
        errors.append(
            "invalid PROJECT_STATE timestamp: created_at "
            "(expected timezone-aware ISO 8601)"
        )

    current_gate = state["current_gate"]
    status = state["status"]
    if status not in GATE_STATUS_MATRIX[current_gate]:
        errors.append(
            f"invalid gate/status transition: Gate {current_gate} cannot use status {status!r}"
        )

    _validate_open_decisions(state["open_decisions"], errors)
    _validate_asset_status_shape(state["asset_status"], errors)
    return _validate_locked_artifacts(project_dir, state["locked_artifacts"], errors)


def _require_locked_roles(
    gate_label: str,
    roles: dict[str, dict],
    required_roles: tuple[str, ...],
    errors: list[str],
) -> None:
    for role in required_roles:
        if role not in roles:
            errors.append(f"{gate_label} requires locked artifact role: {role}")


def _validate_gate_four_completion(
    project_dir: Path,
    state: dict,
    roles: dict[str, dict],
    errors: list[str],
) -> None:
    _require_locked_roles("Gate 4 complete", roles, ("generation_report",), errors)
    if state["open_decisions"]:
        errors.append("Gate 4 complete requires open_decisions to be empty")

    asset_status = state["asset_status"]
    if asset_status.get("claimed_complete_without_output") is not False:
        errors.append("Gate 4 complete cannot set claimed_complete_without_output=true")

    outputs = asset_status.get("outputs")
    if not isinstance(outputs, list) or not outputs:
        errors.append("Gate 4 complete requires at least one hashed output")
    elif isinstance(outputs, list):
        _validate_output_entries(project_dir, outputs, errors)

    qc = asset_status.get("qc")
    if not isinstance(qc, dict) or qc.get("status") != "passed":
        errors.append("Gate 4 complete requires asset_status.qc.status='passed'")
    elif isinstance(qc, dict):
        if not _is_timezone_aware_iso8601(qc.get("checked_at")):
            errors.append("Gate 4 complete requires a valid asset_status.qc.checked_at")
        if not _is_nonempty_string(qc.get("checked_by")):
            errors.append("Gate 4 complete requires asset_status.qc.checked_by")
        checks = qc.get("checks")
        if not isinstance(checks, list) or not checks:
            errors.append("Gate 4 complete requires non-empty asset_status.qc.checks")
        elif any(
            not isinstance(check, dict)
            or check.get("status") != "passed"
            or not _is_nonempty_string(check.get("evidence"))
            for check in checks
        ):
            errors.append("Gate 4 complete requires every QC check to pass with evidence")

    approval = asset_status.get("approval")
    if not isinstance(approval, dict) or approval.get("status") != "approved":
        errors.append("Gate 4 complete requires asset_status.approval.status='approved'")
    elif isinstance(approval, dict):
        if not _is_timezone_aware_iso8601(approval.get("approved_at")):
            errors.append(
                "Gate 4 complete requires a valid asset_status.approval.approved_at"
            )
        if not _is_nonempty_string(approval.get("approved_by")):
            errors.append("Gate 4 complete requires asset_status.approval.approved_by")
        scope = approval.get("scope")
        if not isinstance(scope, list) or not scope or not all(
            _is_nonempty_string(item) for item in scope
        ):
            errors.append("Gate 4 complete requires non-empty asset_status.approval.scope")

    report_path = project_dir / "09_reports_and_qc" / "GENERATION_REPORT.md"
    template_path = Path(__file__).resolve().parents[1] / "assets" / "generation-report-template.md"
    if report_path.is_file() and template_path.is_file():
        try:
            if report_path.read_bytes() == template_path.read_bytes():
                errors.append(
                    "Gate 4 complete requires a completed generation report, "
                    "not the untouched template"
                )
        except OSError as exc:
            errors.append(f"unable to compare GENERATION_REPORT.md: {exc}")


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

    shape_errors = _validate_state_shape(state)
    errors.extend(shape_errors)
    if shape_errors:
        return errors

    roles = _validate_state_details(project_dir, state, errors)
    current_gate = state["current_gate"]
    status = state["status"]

    for gate in range(1, current_gate + 1):
        for requirement in GATE_REQUIREMENTS[gate]:
            _require_path(project_dir, requirement, errors)

    if current_gate >= 2 or (current_gate == 1 and status == "approved"):
        _require_locked_roles("Gate 1 approval", roles, ("project_brief",), errors)

    gate_two_is_approved = current_gate >= 3 or (
        current_gate == 2 and status == "approved"
    )
    if gate_two_is_approved:
        profile_path = project_dir / "CHARACTER_PROFILE.json"
        if profile_path.is_file():
            profile = _load_json(profile_path, "CHARACTER_PROFILE.json", errors)
            if profile is not None and profile.get("status") != "approved":
                errors.append("Gate 2 approval requires approved CHARACTER_PROFILE.json")
        _require_locked_roles(
            "Gate 2 approval", roles, GATE_TWO_LOCK_ROLES, errors
        )

    gate_three_is_approved = current_gate >= 4 or (
        current_gate == 3 and status == "approved"
    )
    if gate_three_is_approved:
        _require_locked_roles(
            "Gate 3 approval", roles, GATE_THREE_LOCK_ROLES, errors
        )

    if current_gate == 4 and status == "complete":
        _validate_gate_four_completion(project_dir, state, roles, errors)

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
