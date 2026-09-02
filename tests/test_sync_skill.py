from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import json
import unittest

from scripts.sync_skill import SKILL_NAME, sync_skill


class SyncSkillTests(unittest.TestCase):
    def test_installs_runtime_files_with_hash_manifest_and_no_staging_directory(self):
        source = Path(__file__).resolve().parents[1]
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            installed = sync_skill(source, root)

            self.assertTrue((installed / "SKILL.md").is_file())
            self.assertTrue((installed / "references" / "production-gates.md").is_file())
            self.assertFalse((installed / ".git").exists())
            self.assertFalse((installed / "tests").exists())
            self.assertFalse((root / ".laoma-aigc-director.staging").exists())

            manifest = json.loads((installed / ".source-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["skill"], "laoma-aigc-director")
            self.assertIn("SKILL.md", manifest["files"])
            self.assertEqual(
                manifest["files"]["SKILL.md"],
                hashlib.sha256((source / "SKILL.md").read_bytes()).hexdigest(),
            )

    def test_refuses_existing_install_without_replace(self):
        source = Path(__file__).resolve().parents[1]
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            sync_skill(source, root)
            with self.assertRaises(FileExistsError):
                sync_skill(source, root)

    def test_replace_preserves_existing_install_in_timestamped_backup(self):
        source = Path(__file__).resolve().parents[1]
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = sync_skill(source, root)
            (first / "preserve-me.txt").write_text("old install", encoding="utf-8")

            installed = sync_skill(source, root, replace=True)

            backups = list(root.glob("laoma-aigc-director.backup-????????-??????"))
            self.assertEqual(len(backups), 1)
            self.assertEqual((backups[0] / "preserve-me.txt").read_text(encoding="utf-8"), "old install")
            self.assertFalse((installed / "preserve-me.txt").exists())

    def test_rejects_source_and_install_path_overlap_without_mutating_source(self):
        for name in ("same", "destination_descendant", "source_descendant"):
            with self.subTest(name=name), TemporaryDirectory() as tmp:
                root = Path(tmp)
                if name == "same":
                    source, destination_root = root / SKILL_NAME, root
                elif name == "destination_descendant":
                    source, destination_root = root / "source", root / "source"
                else:
                    source, destination_root = root / SKILL_NAME / "nested-source", root
                with self.subTest(name=name):
                    source.mkdir(parents=True)
                    skill_file = source / "SKILL.md"
                    skill_file.write_text(name, encoding="utf-8")

                    with self.assertRaisesRegex(ValueError, "overlap"):
                        sync_skill(source, destination_root, replace=True)

                    self.assertEqual(skill_file.read_text(encoding="utf-8"), name)
                    self.assertFalse((destination_root / f".{SKILL_NAME}.staging").exists())
                    self.assertEqual(list(destination_root.glob(f"{SKILL_NAME}.backup-*")), [])

    def test_excludes_mixed_case_non_runtime_directories(self):
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            (source / "scripts" / "Docs").mkdir(parents=True)
            (source / "scripts" / "Tests").mkdir()
            (source / "scripts" / ".GIT").mkdir()
            (source / "scripts" / "runtime").mkdir()
            (source / "SKILL.md").write_text("skill", encoding="utf-8")
            (source / "scripts" / "Docs" / "private.md").write_text("no", encoding="utf-8")
            (source / "scripts" / "Tests" / "test.py").write_text("no", encoding="utf-8")
            (source / "scripts" / ".GIT" / "config").write_text("no", encoding="utf-8")
            (source / "scripts" / "runtime" / "tool.py").write_text("yes", encoding="utf-8")

            installed = sync_skill(source, Path(tmp) / "installed")

            self.assertTrue((installed / "scripts" / "runtime" / "tool.py").is_file())
            self.assertFalse((installed / "scripts" / "Docs").exists())
            self.assertFalse((installed / "scripts" / "Tests").exists())
            self.assertFalse((installed / "scripts" / ".GIT").exists())


if __name__ == "__main__":
    unittest.main()
