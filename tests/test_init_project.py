from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from scripts.init_project import create_project


class InitProjectTests(unittest.TestCase):
    def test_creates_versioned_project_without_overwriting(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = create_project(root, "台北孤城")
            second = create_project(root, "台北孤城")
            self.assertEqual(first.name, "台北孤城_V01")
            self.assertEqual(second.name, "台北孤城_V02")
            self.assertTrue((first / "PROJECT_STATE.json").is_file())
            self.assertTrue((first / "CHARACTER_PROFILE.json").is_file())
            state = json.loads((first / "PROJECT_STATE.json").read_text(encoding="utf-8"))
            self.assertEqual(
                set(state),
                {
                    "schema_version", "project_name", "project_version", "current_gate",
                    "status", "locked_artifacts", "open_decisions", "asset_status", "created_at",
                },
            )
            self.assertEqual(state["schema_version"], "1.0")
            self.assertEqual(state["project_name"], "台北孤城")
            self.assertEqual(state["project_version"], "V01")
            self.assertEqual(state["current_gate"], 1)
            self.assertEqual(state["status"], "draft")
            self.assertEqual(state["locked_artifacts"], [])
            self.assertEqual(state["open_decisions"], [])
            self.assertEqual(state["asset_status"], {})
            self.assertRegex(state["created_at"], r"^20\d\d-\d\d-\d\dT")

            required_dirs = (
                "01_inputs", "02_character_and_look", "03_story_and_script", "04_shot_design",
                "05_generation_prompts", "06_generated_assets", "07_sound_and_music",
                "08_edit_and_delivery", "09_reports_and_qc",
            )
            for directory in required_dirs:
                self.assertTrue((first / directory).is_dir(), directory)
            for source, target in {
                "project-brief-template.md": "PROJECT_BRIEF.md",
                "production-bible-template.md": "PRODUCTION_BIBLE.md",
                "character-profile-template.json": "CHARACTER_PROFILE.json",
                "shot-production-table-template.md": "04_shot_design/SHOT_PRODUCTION_TABLE.md",
                "generation-report-template.md": "09_reports_and_qc/GENERATION_REPORT.md",
            }.items():
                self.assertEqual(
                    (first / target).read_bytes(),
                    (Path(__file__).parents[1] / "assets" / source).read_bytes(),
                    target,
                )

    def test_rejects_invalid_project_names(self):
        with TemporaryDirectory() as tmp:
            for name in ("", ".", "..", "bad/name", "bad\\name", "bad:name", "bad*name", "bad?name"):
                with self.subTest(name=name), self.assertRaisesRegex(ValueError, "project_name"):
                    create_project(Path(tmp), name)


if __name__ == "__main__":
    unittest.main()
