from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import json
import unittest
from unittest.mock import patch

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

    def test_copy_failure_cleans_current_staging_and_preserves_install(self):
        source = Path(__file__).resolve().parents[1]
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            installed = sync_skill(source, root)
            marker = installed / "preserve-me.txt"
            marker.write_text("old install", encoding="utf-8")

            with patch(
                "scripts.sync_skill._copy_runtime_entry",
                side_effect=OSError("injected copy failure"),
            ), self.assertRaisesRegex(OSError, "injected copy failure"):
                sync_skill(source, root, replace=True)

            self.assertEqual(marker.read_text(encoding="utf-8"), "old install")
            self.assertFalse((root / f".{SKILL_NAME}.staging").exists())
            self.assertEqual(list(root.glob(f"{SKILL_NAME}.backup-*")), [])

    def test_manifest_failure_cleans_current_staging_and_preserves_install(self):
        source = Path(__file__).resolve().parents[1]
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            installed = sync_skill(source, root)
            marker = installed / "preserve-me.txt"
            marker.write_text("old install", encoding="utf-8")

            with patch(
                "scripts.sync_skill._write_manifest",
                side_effect=OSError("injected manifest failure"),
            ), self.assertRaisesRegex(OSError, "injected manifest failure"):
                sync_skill(source, root, replace=True)

            self.assertEqual(marker.read_text(encoding="utf-8"), "old install")
            self.assertFalse((root / f".{SKILL_NAME}.staging").exists())
            self.assertEqual(list(root.glob(f"{SKILL_NAME}.backup-*")), [])

    def test_promotion_failure_restores_prior_install_and_cleans_staging(self):
        source = Path(__file__).resolve().parents[1]
        original_rename = Path.rename

        def fail_staging_promotion(path: Path, target: Path) -> Path:
            if path.name == f".{SKILL_NAME}.staging":
                raise OSError("injected promotion failure")
            return original_rename(path, target)

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            installed = sync_skill(source, root)
            marker = installed / "preserve-me.txt"
            marker.write_text("old install", encoding="utf-8")

            with patch.object(
                Path, "rename", autospec=True, side_effect=fail_staging_promotion
            ), self.assertRaisesRegex(OSError, "injected promotion failure"):
                sync_skill(source, root, replace=True)

            self.assertEqual(marker.read_text(encoding="utf-8"), "old install")
            self.assertFalse((root / f".{SKILL_NAME}.staging").exists())
            self.assertEqual(list(root.glob(f"{SKILL_NAME}.backup-*")), [])

    def test_promotion_failure_without_prior_install_cleans_staging(self):
        source = Path(__file__).resolve().parents[1]
        original_rename = Path.rename

        def fail_staging_promotion(path: Path, target: Path) -> Path:
            if path.name == f".{SKILL_NAME}.staging":
                raise OSError("injected promotion failure")
            return original_rename(path, target)

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(
                Path, "rename", autospec=True, side_effect=fail_staging_promotion
            ), self.assertRaisesRegex(OSError, "injected promotion failure"):
                sync_skill(source, root)

            self.assertFalse((root / SKILL_NAME).exists())
            self.assertFalse((root / f".{SKILL_NAME}.staging").exists())

    def test_rejects_source_inside_staging_without_deleting_source(self):
        with TemporaryDirectory() as tmp:
            destination_root = Path(tmp) / "installed"
            source = destination_root / f".{SKILL_NAME}.staging" / "source"
            source.mkdir(parents=True)
            skill_file = source / "SKILL.md"
            skill_file.write_text("source inside staging", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "overlap"):
                sync_skill(source, destination_root, replace=True)

            self.assertEqual(
                skill_file.read_text(encoding="utf-8"), "source inside staging"
            )
            self.assertTrue(source.is_dir())
            self.assertEqual(list(destination_root.glob(f"{SKILL_NAME}.backup-*")), [])


if __name__ == "__main__":
    unittest.main()
