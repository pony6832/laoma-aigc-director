from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TemplateTests(unittest.TestCase):
    def test_character_profile_is_valid_and_versioned(self):
        data = json.loads((ROOT / "assets" / "character-profile-template.json").read_text(encoding="utf-8"))
        self.assertEqual(data["schema_version"], "1.0")
        self.assertEqual(data["status"], "draft")
        self.assertEqual(data["identity"]["anchors"], [])
        self.assertEqual(data["locked_fields"], [])

    def test_markdown_templates_cover_their_gate(self):
        expected = {
            "project-brief-template.md": ("作品目的", "發布平台", "權利狀態"),
            "production-bible-template.md": ("視覺規則", "攝影規則", "聲音規則", "連戲規則"),
            "shot-production-table-template.md": ("時間碼", "焦段", "運鏡", "連續性", "影片提示詞"),
            "generation-report-template.md": ("輸入雜湊", "生成入口", "QC", "已知限制"),
        }
        for name, phrases in expected.items():
            text = (ROOT / "assets" / name).read_text(encoding="utf-8")
            for phrase in phrases:
                self.assertIn(phrase, text, f"{name}: {phrase}")


if __name__ == "__main__":
    unittest.main()
