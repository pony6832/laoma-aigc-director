from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from scripts.init_project import create_project
from scripts.validate_project import validate_project


class ValidateProjectTests(unittest.TestCase):
    def test_fresh_project_passes_gate_one_structure(self):
        with TemporaryDirectory() as tmp:
            project = create_project(Path(tmp), "測試片")
            self.assertEqual(validate_project(project), [])

    def test_gate_two_requires_locked_character_profile(self):
        with TemporaryDirectory() as tmp:
            project = create_project(Path(tmp), "測試片")
            state_path = project / "PROJECT_STATE.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["current_gate"] = 2
            state["status"] = "approved"
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
            errors = validate_project(project)
            self.assertIn("Gate 2 requires approved CHARACTER_PROFILE.json", errors)

    def test_missing_input_directory_is_reported(self):
        with TemporaryDirectory() as tmp:
            project = create_project(Path(tmp), "測試片")
            (project / "01_inputs").rmdir()
            self.assertIn("missing directory: 01_inputs", validate_project(project))

    def test_gate_three_requires_both_locked_artifacts(self):
        with TemporaryDirectory() as tmp:
            project = create_project(Path(tmp), "測試片")
            profile_path = project / "CHARACTER_PROFILE.json"
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
            profile["status"] = "approved"
            profile_path.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
            state_path = project / "PROJECT_STATE.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["current_gate"] = 3
            state["locked_artifacts"] = ["CHARACTER_PROFILE.json"]
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
            self.assertIn("Gate 3 requires locked artifact: PRODUCTION_BIBLE.md", validate_project(project))

    def test_gate_three_requires_shot_table_to_be_a_file(self):
        with TemporaryDirectory() as tmp:
            project = create_project(Path(tmp), "測試片")
            profile_path = project / "CHARACTER_PROFILE.json"
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
            profile["status"] = "approved"
            profile_path.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
            state_path = project / "PROJECT_STATE.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state.update({
                "current_gate": 3,
                "locked_artifacts": ["PRODUCTION_BIBLE.md", "CHARACTER_PROFILE.json"],
            })
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
            shot_table = project / "04_shot_design" / "SHOT_PRODUCTION_TABLE.md"
            shot_table.unlink()
            shot_table.mkdir()
            self.assertIn("missing file: 04_shot_design/SHOT_PRODUCTION_TABLE.md", validate_project(project))

    def test_completed_gate_four_requires_known_limitations(self):
        with TemporaryDirectory() as tmp:
            project = create_project(Path(tmp), "測試片")
            profile_path = project / "CHARACTER_PROFILE.json"
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
            profile["status"] = "approved"
            profile_path.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
            state_path = project / "PROJECT_STATE.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state.update({
                "current_gate": 4,
                "status": "complete",
                "locked_artifacts": ["PRODUCTION_BIBLE.md", "CHARACTER_PROFILE.json"],
            })
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
            report_path = project / "09_reports_and_qc" / "GENERATION_REPORT.md"
            report_path.write_text("Generation report", encoding="utf-8")
            self.assertIn("Gate 4 complete project requires GENERATION_REPORT.md to contain 已知限制", validate_project(project))

    def test_unhashable_status_values_return_diagnostics(self):
        for status in ([], {}):
            with self.subTest(status=status), TemporaryDirectory() as tmp:
                project = create_project(Path(tmp), "測試片")
                state_path = project / "PROJECT_STATE.json"
                state = json.loads(state_path.read_text(encoding="utf-8"))
                state["status"] = status
                state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
                self.assertEqual(validate_project(project), ["invalid project status: expected str"])

    def test_missing_canonical_state_fields_are_reported_in_schema_order(self):
        with TemporaryDirectory() as tmp:
            project = create_project(Path(tmp), "測試片")
            state_path = project / "PROJECT_STATE.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            for field in (
                "schema_version", "project_name", "project_version", "current_gate", "status",
                "locked_artifacts", "open_decisions", "asset_status", "created_at",
            ):
                del state[field]
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
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

    def test_wrong_typed_canonical_state_fields_are_reported(self):
        with TemporaryDirectory() as tmp:
            project = create_project(Path(tmp), "測試片")
            state_path = project / "PROJECT_STATE.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state.update({
                "schema_version": 1,
                "project_name": [],
                "project_version": {},
                "current_gate": True,
                "status": [],
                "locked_artifacts": {},
                "open_decisions": "open",
                "asset_status": [],
                "created_at": 0,
            })
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
            self.assertEqual(
                validate_project(project),
                [
                    "invalid PROJECT_STATE field: schema_version (expected str)",
                    "invalid PROJECT_STATE field: project_name (expected str)",
                    "invalid PROJECT_STATE field: project_version (expected str)",
                    "invalid PROJECT_STATE field: current_gate (expected int from 1 to 4)",
                    "invalid project status: expected str",
                    "invalid PROJECT_STATE field: locked_artifacts (expected list)",
                    "invalid PROJECT_STATE field: open_decisions (expected list)",
                    "invalid PROJECT_STATE field: asset_status (expected object)",
                    "invalid PROJECT_STATE field: created_at (expected str)",
                ],
            )


if __name__ == "__main__":
    unittest.main()
