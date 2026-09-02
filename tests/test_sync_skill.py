from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import json
import unittest

from scripts.sync_skill import sync_skill


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


if __name__ == "__main__":
    unittest.main()
