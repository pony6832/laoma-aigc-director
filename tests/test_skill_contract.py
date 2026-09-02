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


if __name__ == "__main__":
    unittest.main()
