from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ScenarioCoverageTests(unittest.TestCase):
    def test_seven_scenarios_cover_required_risks(self):
        text = (ROOT / "tests" / "fixtures" / "scenarios.md").read_text(encoding="utf-8")
        blocks = re.split(r"(?m)^## Scenario \d+｜", text)[1:]
        self.assertEqual(len(blocks), 7)

        required_headings = (
            "使用者請求",
            "預期模式與當前 Gate",
            "必要產物",
            "禁止行為",
            "完成證據",
        )
        scenario_expectations = (
            ("一句故事點子", ("Gate 1", "brief", "禁止偷用舊角色", "pending_approval")),
            (
                "一張虛構角色圖",
                (
                    "Gate 2",
                    "CHARACTER_PROFILE.json",
                    "角色總覽板",
                    "無角色場景參考板",
                    "4–6 秒一致性短測",
                    "禁止補入任何舊案件角色",
                    "核准",
                ),
            ),
            ("已核准角色圖", ("Gate 3", "Seedance", "跳過 Gate 3", "gate: 3 / approved")),
            ("只改一顆失敗鏡頭", ("失敗回復模式", "只新增第二鏡頭修正版", "覆蓋舊版", "單鏡 QC")),
            ("生成入口不明", ("阻擋模式", "generation_entry_unknown", "不猜測平台", "沒有生成 job ID")),
            ("真人肖像或聲音授權不明", ("rights_unclear", "停在 Gate 1／Gate 2", "禁止下載", "真人檔案未進入輸入清單")),
            ("工具不可用", ("tool_unavailable", "工具失敗回復模式", "偽造輸出檔", "沒有可播放鏡頭")),
        )

        for index, (block, (topic, semantic_phrases)) in enumerate(
            zip(blocks, scenario_expectations), start=1
        ):
            self.assertTrue(block.startswith(topic), f"Scenario {index} topic is misplaced")
            for heading in required_headings:
                self.assertGreaterEqual(
                    block.count(f"### {heading}"),
                    1,
                    f"Scenario {index} missing subsection: {heading}",
                )
            for phrase in semantic_phrases:
                self.assertIn(phrase, block, f"Scenario {index} missing invariant: {phrase}")


if __name__ == "__main__":
    unittest.main()
