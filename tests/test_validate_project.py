from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import json
import unittest

from scripts.init_project import create_project
from scripts.validate_project import validate_project


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _locked_artifact(
    project: Path,
    path: str,
    role: str,
    *,
    content: bytes | None = None,
    duration_seconds: float | None = None,
) -> dict:
    target = project / path
    if content is not None:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    artifact = {
        "role": role,
        "path": path,
        "version": "v01",
        "sha256": _sha256(target),
        "reason": f"approved {role}",
    }
    if duration_seconds is not None:
        artifact["duration_seconds"] = duration_seconds
    return artifact


def _prepare_gate_two(project: Path) -> list[dict]:
    profile_path = project / "CHARACTER_PROFILE.json"
    profile = _read_json(profile_path)
    profile["status"] = "approved"
    _write_json(profile_path, profile)
    return [
        _locked_artifact(project, "PROJECT_BRIEF.md", "project_brief"),
        _locked_artifact(project, "PRODUCTION_BIBLE.md", "production_bible"),
        _locked_artifact(project, "CHARACTER_PROFILE.json", "character_profile"),
        _locked_artifact(
            project,
            "02_character_and_look/CHARACTER_OVERVIEW_BOARD_v01.png",
            "character_overview_board",
            content=b"character-board",
        ),
        _locked_artifact(
            project,
            "02_character_and_look/SCENE_REFERENCE_BOARD_v01.png",
            "character_free_scene_board",
            content=b"scene-board-without-character",
        ),
        _locked_artifact(
            project,
            "02_character_and_look/CONSISTENCY_TEST_v01.mp4",
            "consistency_test",
            content=b"four-to-six-second-test",
            duration_seconds=5.0,
        ),
    ]


def _prepare_gate_three(project: Path, locked: list[dict]) -> None:
    locked.extend(
        [
            _locked_artifact(
                project,
                "03_story_and_script/STORY_SCRIPT_v01.md",
                "story_script",
                content=b"# approved story\n",
            ),
            _locked_artifact(
                project,
                "04_shot_design/SHOT_PRODUCTION_TABLE.md",
                "shot_production_table",
            ),
            _locked_artifact(
                project,
                "05_generation_prompts/GENERATION_PLAN_v01.md",
                "generation_plan",
                content=b"# approved generation plan\n",
            ),
        ]
    )


def _prepare_complete_gate_four(project: Path) -> dict:
    locked = _prepare_gate_two(project)
    _prepare_gate_three(project, locked)
    report_path = project / "09_reports_and_qc" / "GENERATION_REPORT.md"
    report_path.write_text(
        "# Generation Report v01\n\nValidated output, QC evidence, approval, and limitations recorded.\n",
        encoding="utf-8",
    )
    locked.append(
        _locked_artifact(
            project,
            "09_reports_and_qc/GENERATION_REPORT.md",
            "generation_report",
        )
    )
    output_path = project / "06_generated_assets" / "final_v01.mp4"
    output_path.write_bytes(b"verified-playable-output-fixture")
    state_path = project / "PROJECT_STATE.json"
    state = _read_json(state_path)
    state.update(
        {
            "current_gate": 4,
            "status": "complete",
            "locked_artifacts": locked,
            "open_decisions": [],
            "asset_status": {
                "claimed_complete_without_output": False,
                "outputs": [
                    {
                        "path": "06_generated_assets/final_v01.mp4",
                        "version": "v01",
                        "sha256": _sha256(output_path),
                        "kind": "video",
                    }
                ],
                "qc": {
                    "status": "passed",
                    "checked_at": "2026-09-02T12:00:00+08:00",
                    "checked_by": "acceptance-reviewer",
                    "checks": [
                        {
                            "name": "playable_output",
                            "status": "passed",
                            "evidence": "local playback check recorded",
                        }
                    ],
                },
                "approval": {
                    "status": "approved",
                    "approved_at": "2026-09-02T12:05:00+08:00",
                    "approved_by": "project-owner",
                    "scope": ["final_v01.mp4"],
                },
            },
        }
    )
    _write_json(state_path, state)
    return state


class ValidateProjectTests(unittest.TestCase):
    def test_fresh_project_passes_gate_one_structure(self):
        with TemporaryDirectory() as tmp:
            project = create_project(Path(tmp), "測試片")
            self.assertEqual(validate_project(project), [])

    def test_gate_status_matrix_rejects_complete_before_gate_four(self):
        with TemporaryDirectory() as tmp:
            project = create_project(Path(tmp), "測試片")
            state_path = project / "PROJECT_STATE.json"
            state = _read_json(state_path)
            state["status"] = "complete"
            _write_json(state_path, state)
            self.assertIn(
                "invalid gate/status transition: Gate 1 cannot use status 'complete'",
                validate_project(project),
            )

    def test_rejects_unsupported_schema_version(self):
        with TemporaryDirectory() as tmp:
            project = create_project(Path(tmp), "測試片")
            state_path = project / "PROJECT_STATE.json"
            state = _read_json(state_path)
            state["schema_version"] = "0.9"
            _write_json(state_path, state)
            self.assertIn(
                "unsupported PROJECT_STATE schema_version: '0.9' (expected '1.0')",
                validate_project(project),
            )

    def test_rejects_bad_project_version_and_directory_mismatch(self):
        with TemporaryDirectory() as tmp:
            project = create_project(Path(tmp), "測試片")
            state_path = project / "PROJECT_STATE.json"
            state = _read_json(state_path)
            state["project_version"] = "v1"
            _write_json(state_path, state)
            self.assertIn(
                "invalid project_version: 'v1' (expected V followed by at least two digits)",
                validate_project(project),
            )

            state["project_version"] = "V02"
            _write_json(state_path, state)
            self.assertIn(
                "project directory mismatch: expected 測試片_V02, found 測試片_V01",
                validate_project(project),
            )

    def test_rejects_invalid_or_timezone_naive_created_at(self):
        for timestamp in ("not-a-date", "2026-09-02T12:00:00"):
            with self.subTest(timestamp=timestamp), TemporaryDirectory() as tmp:
                project = create_project(Path(tmp), "測試片")
                state_path = project / "PROJECT_STATE.json"
                state = _read_json(state_path)
                state["created_at"] = timestamp
                _write_json(state_path, state)
                self.assertIn(
                    "invalid PROJECT_STATE timestamp: created_at (expected timezone-aware ISO 8601)",
                    validate_project(project),
                )

    def test_open_decisions_are_structured(self):
        with TemporaryDirectory() as tmp:
            project = create_project(Path(tmp), "測試片")
            state_path = project / "PROJECT_STATE.json"
            state = _read_json(state_path)
            state["open_decisions"] = ["pick a platform"]
            _write_json(state_path, state)
            self.assertIn(
                "invalid open_decisions[0]: expected object",
                validate_project(project),
            )

    def test_open_decision_requires_identity_status_question_and_timestamp(self):
        with TemporaryDirectory() as tmp:
            project = create_project(Path(tmp), "測試片")
            state_path = project / "PROJECT_STATE.json"
            state = _read_json(state_path)
            state["open_decisions"] = [{"id": "D001"}]
            _write_json(state_path, state)
            errors = validate_project(project)
            for field in ("question", "status", "opened_at"):
                self.assertIn(f"missing open_decisions[0] field: {field}", errors)

    def test_asset_status_requires_structured_completion_sections(self):
        with TemporaryDirectory() as tmp:
            project = create_project(Path(tmp), "測試片")
            state_path = project / "PROJECT_STATE.json"
            state = _read_json(state_path)
            state["asset_status"] = {}
            _write_json(state_path, state)
            errors = validate_project(project)
            for field in ("claimed_complete_without_output", "outputs", "qc", "approval"):
                self.assertIn(f"missing asset_status field: {field}", errors)

    def test_gate_two_approved_requires_complete_visual_lock_set(self):
        with TemporaryDirectory() as tmp:
            project = create_project(Path(tmp), "測試片")
            state_path = project / "PROJECT_STATE.json"
            state = _read_json(state_path)
            state.update(
                {
                    "current_gate": 2,
                    "status": "approved",
                    "locked_artifacts": _prepare_gate_two(project)[:-1],
                }
            )
            _write_json(state_path, state)
            self.assertIn(
                "Gate 2 approval requires locked artifact role: consistency_test",
                validate_project(project),
            )

    def test_consistency_test_duration_must_be_four_to_six_seconds(self):
        with TemporaryDirectory() as tmp:
            project = create_project(Path(tmp), "測試片")
            state_path = project / "PROJECT_STATE.json"
            state = _read_json(state_path)
            locked = _prepare_gate_two(project)
            locked[-1]["duration_seconds"] = 7
            state.update(
                {"current_gate": 2, "status": "approved", "locked_artifacts": locked}
            )
            _write_json(state_path, state)
            self.assertIn(
                "consistency_test duration_seconds must be between 4 and 6",
                validate_project(project),
            )

    def test_locked_artifact_rejects_unsafe_path(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = create_project(root, "測試片")
            outside = root / "outside.md"
            outside.write_text("outside", encoding="utf-8")
            state_path = project / "PROJECT_STATE.json"
            state = _read_json(state_path)
            state["locked_artifacts"] = [
                {
                    "role": "project_brief",
                    "path": "../outside.md",
                    "version": "v01",
                    "sha256": _sha256(outside),
                    "reason": "should never escape",
                }
            ]
            _write_json(state_path, state)
            self.assertIn(
                "unsafe locked_artifacts[0] path: ../outside.md",
                validate_project(project),
            )

    def test_locked_artifacts_are_structured_objects_with_required_fields(self):
        with TemporaryDirectory() as tmp:
            project = create_project(Path(tmp), "測試片")
            state_path = project / "PROJECT_STATE.json"
            state = _read_json(state_path)
            state["locked_artifacts"] = ["PROJECT_BRIEF.md", {"path": "PROJECT_BRIEF.md"}]
            _write_json(state_path, state)
            errors = validate_project(project)
            self.assertIn("invalid locked_artifacts[0]: expected object", errors)
            for field in ("role", "version", "sha256", "reason"):
                self.assertIn(
                    f"missing locked_artifacts[1] field: {field}",
                    errors,
                )

    def test_locked_artifact_requires_existing_file(self):
        with TemporaryDirectory() as tmp:
            project = create_project(Path(tmp), "測試片")
            state_path = project / "PROJECT_STATE.json"
            state = _read_json(state_path)
            state["locked_artifacts"] = [
                {
                    "role": "project_brief",
                    "path": "missing.md",
                    "version": "v01",
                    "sha256": "0" * 64,
                    "reason": "approved",
                }
            ]
            _write_json(state_path, state)
            self.assertIn(
                "locked_artifacts[0] file does not exist: missing.md",
                validate_project(project),
            )

    def test_locked_artifact_rejects_hash_mismatch(self):
        with TemporaryDirectory() as tmp:
            project = create_project(Path(tmp), "測試片")
            state_path = project / "PROJECT_STATE.json"
            state = _read_json(state_path)
            state["locked_artifacts"] = [
                {
                    "role": "project_brief",
                    "path": "PROJECT_BRIEF.md",
                    "version": "v01",
                    "sha256": "0" * 64,
                    "reason": "approved",
                }
            ]
            _write_json(state_path, state)
            self.assertIn(
                "locked_artifacts[0] sha256 mismatch: PROJECT_BRIEF.md",
                validate_project(project),
            )

    def test_gate_four_complete_rejects_empty_generated_assets(self):
        with TemporaryDirectory() as tmp:
            project = create_project(Path(tmp), "測試片")
            state = _prepare_complete_gate_four(project)
            output = project / "06_generated_assets" / "final_v01.mp4"
            output.write_bytes(b"")
            state["asset_status"]["outputs"][0]["sha256"] = _sha256(output)
            _write_json(project / "PROJECT_STATE.json", state)
            self.assertIn(
                "Gate 4 complete output is empty: 06_generated_assets/final_v01.mp4",
                validate_project(project),
            )

    def test_gate_four_complete_rejects_output_hash_mismatch(self):
        with TemporaryDirectory() as tmp:
            project = create_project(Path(tmp), "測試片")
            state = _prepare_complete_gate_four(project)
            state["asset_status"]["outputs"][0]["sha256"] = "0" * 64
            _write_json(project / "PROJECT_STATE.json", state)
            self.assertIn(
                "asset_status.outputs[0] sha256 mismatch: 06_generated_assets/final_v01.mp4",
                validate_project(project),
            )

    def test_gate_four_complete_rejects_untouched_report_template(self):
        with TemporaryDirectory() as tmp:
            project = create_project(Path(tmp), "測試片")
            state = _prepare_complete_gate_four(project)
            report_path = project / "09_reports_and_qc" / "GENERATION_REPORT.md"
            template = Path(__file__).parents[1] / "assets" / "generation-report-template.md"
            report_path.write_bytes(template.read_bytes())
            for artifact in state["locked_artifacts"]:
                if artifact["role"] == "generation_report":
                    artifact["sha256"] = _sha256(report_path)
            _write_json(project / "PROJECT_STATE.json", state)
            self.assertIn(
                "Gate 4 complete requires a completed generation report, not the untouched template",
                validate_project(project),
            )

    def test_gate_four_complete_rejects_incomplete_qc_and_approval(self):
        with TemporaryDirectory() as tmp:
            project = create_project(Path(tmp), "測試片")
            state = _prepare_complete_gate_four(project)
            state["asset_status"]["qc"] = {
                "status": "not_started",
                "checked_at": None,
                "checked_by": "",
                "checks": [],
            }
            state["asset_status"]["approval"] = {
                "status": "not_requested",
                "approved_at": None,
                "approved_by": "",
                "scope": [],
            }
            _write_json(project / "PROJECT_STATE.json", state)
            errors = validate_project(project)
            self.assertIn("Gate 4 complete requires asset_status.qc.status='passed'", errors)
            self.assertIn(
                "Gate 4 complete requires asset_status.approval.status='approved'", errors
            )

    def test_gate_four_complete_rejects_false_completion_flag(self):
        with TemporaryDirectory() as tmp:
            project = create_project(Path(tmp), "測試片")
            state = _prepare_complete_gate_four(project)
            state["asset_status"]["claimed_complete_without_output"] = True
            _write_json(project / "PROJECT_STATE.json", state)
            self.assertIn(
                "Gate 4 complete cannot set claimed_complete_without_output=true",
                validate_project(project),
            )

    def test_gate_four_complete_accepts_hashed_outputs_qc_and_approval(self):
        with TemporaryDirectory() as tmp:
            project = create_project(Path(tmp), "測試片")
            _prepare_complete_gate_four(project)
            self.assertEqual(validate_project(project), [])

    def test_missing_input_directory_is_reported(self):
        with TemporaryDirectory() as tmp:
            project = create_project(Path(tmp), "測試片")
            (project / "01_inputs").rmdir()
            self.assertIn("missing directory: 01_inputs", validate_project(project))

    def test_unhashable_status_values_return_diagnostics(self):
        for status in ([], {}):
            with self.subTest(status=status), TemporaryDirectory() as tmp:
                project = create_project(Path(tmp), "測試片")
                state_path = project / "PROJECT_STATE.json"
                state = _read_json(state_path)
                state["status"] = status
                _write_json(state_path, state)
                self.assertIn("invalid project status: expected str", validate_project(project))

    def test_missing_canonical_state_fields_are_reported_in_schema_order(self):
        with TemporaryDirectory() as tmp:
            project = create_project(Path(tmp), "測試片")
            state_path = project / "PROJECT_STATE.json"
            state = _read_json(state_path)
            for field in (
                "schema_version",
                "project_name",
                "project_version",
                "current_gate",
                "status",
                "locked_artifacts",
                "open_decisions",
                "asset_status",
                "created_at",
            ):
                del state[field]
            _write_json(state_path, state)
            self.assertEqual(
                validate_project(project),
                [
                    "missing PROJECT_STATE field: schema_version",
                    "missing PROJECT_STATE field: project_name",
                    "missing PROJECT_STATE field: project_version",
                    "missing PROJECT_STATE field: current_gate",
                    "missing PROJECT_STATE field: status",
                    "missing PROJECT_STATE field: locked_artifacts",
                    "missing PROJECT_STATE field: open_decisions",
                    "missing PROJECT_STATE field: asset_status",
                    "missing PROJECT_STATE field: created_at",
                ],
            )

    def test_initializer_timestamp_is_timezone_aware_iso_8601(self):
        with TemporaryDirectory() as tmp:
            project = create_project(Path(tmp), "測試片")
            created_at = _read_json(project / "PROJECT_STATE.json")["created_at"]
            parsed = datetime.fromisoformat(created_at)
            self.assertIsNotNone(parsed.tzinfo)
            self.assertIsNotNone(parsed.utcoffset())


if __name__ == "__main__":
    unittest.main()
