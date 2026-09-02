from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_FILES = (
    "director-identity.md",
    "production-gates.md",
    "knowledge-routing.md",
    "project-state-and-versioning.md",
    "quality-and-recovery.md",
    "source-manifest.md",
)


class ReferenceContractTests(unittest.TestCase):
    def test_all_routed_references_exist(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        links = re.findall(r"\]\((references/[^)]+\.md)\)", skill)
        self.assertEqual({Path(link).name for link in links}, set(REFERENCE_FILES))
        for link in links:
            self.assertTrue((ROOT / link).is_file(), link)

    def test_source_manifest_records_isolation_and_date(self):
        text = (ROOT / "references" / "source-manifest.md").read_text(encoding="utf-8")
        self.assertIn("同步日期：2026-09-02", text)
        self.assertIn("只提煉方法", text)
        self.assertIn("不匯入私人素材", text)


if __name__ == "__main__":
    unittest.main()
