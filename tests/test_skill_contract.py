from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SkillContractTests(unittest.TestCase):
    def test_skill_frontmatter_and_core_contract(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertRegex(text, r"(?s)^---\s+name: laoma-aigc-director\s+description: .+?\s+---")
        for phrase in (
            "製片總導演模式",
            "Gate 1",
            "Gate 2",
            "Gate 3",
            "Gate 4",
            "PROJECT_STATE.json",
            "CHARACTER_PROFILE.json",
        ):
            self.assertIn(phrase, text)

    def test_openai_metadata_matches_skill(self):
        text = (ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn("display_name: 老馬 AIGC 導演", text)
        self.assertIn("default_prompt:", text)

    def test_runtime_entry_routes_executable_project_workflow(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("scripts/init_project.py", text)
        self.assertIn("scripts/validate_project.py", text)
        self.assertIn(
            r"C:\Users\pony6832\Documents\Codex\Codex專案分類\08 - AIGC影像生成相關\老馬AIGC導演專案",
            text,
        )
        for template in (
            "project-brief-template.md",
            "production-bible-template.md",
            "character-profile-template.json",
            "shot-production-table-template.md",
            "generation-report-template.md",
        ):
            self.assertIn(f"assets/{template}", text)

    def test_information_priority_keeps_approved_design_order(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        phrases = (
            "使用者本次明確要求",
            "本次提供的圖片、影片、音訊與文件",
            "已鎖定的 `PROJECT_STATE.json`、`PRODUCTION_BIBLE.md` 與 `CHARACTER_PROFILE.json`",
            "已核准的主視覺、分鏡與測試成果",
            "已核准的方法與模板",
            "一般預設",
        )
        positions = [text.index(phrase) for phrase in phrases]
        self.assertEqual(positions, sorted(positions))


if __name__ == "__main__":
    unittest.main()
