from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ScenarioCoverageTests(unittest.TestCase):
    def test_seven_scenarios_cover_required_risks(self):
        text = (ROOT / "tests" / "fixtures" / "scenarios.md").read_text(encoding="utf-8")
        self.assertEqual(text.count("## Scenario "), 7)
        for phrase in (
            "一句故事點子",
            "一張虛構角色圖",
            "已核准角色圖",
            "只改一顆失敗鏡頭",
            "生成入口不明",
            "真人肖像或聲音授權不明",
            "工具不可用",
            "禁止行為",
            "完成證據",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
