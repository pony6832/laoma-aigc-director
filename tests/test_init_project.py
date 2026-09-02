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
            self.assertEqual(state["current_gate"], 1)
            self.assertEqual(state["status"], "draft")

    def test_rejects_path_separators(self):
        with TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "project_name"):
                create_project(Path(tmp), "bad/name")


if __name__ == "__main__":
    unittest.main()
