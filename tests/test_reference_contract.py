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
    "knowledge-snapshot-v1.md",
    "source-manifest.md",
    "prompt-library/README.md",
    "weekly-evolution.md",
    "director-style-routing.md",
    "director-knowledge-governance.md",
    "cinematic-craft-foundation.md",
    "storyboard-output-formats.md",
)


class ReferenceContractTests(unittest.TestCase):
    def test_all_routed_references_exist(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        links = re.findall(r"\]\((references/[^)]+\.md)\)", skill)
        self.assertEqual(
            {link.removeprefix("references/") for link in links},
            set(REFERENCE_FILES),
        )
        for link in links:
            self.assertTrue((ROOT / link).is_file(), link)

    def test_source_manifest_records_isolation_and_date(self):
        text = (ROOT / "references" / "source-manifest.md").read_text(encoding="utf-8")
        self.assertIn("同步日期：2026-09-02", text)
        self.assertIn("只提煉方法", text)
        self.assertIn("不匯入私人素材", text)
        self.assertIn("| 方法 | 來源檔案 | 快照／雜湊或版本 | 來源等級 | 適用版本／入口 | 同步日期 | 排除內容 |", text)
        self.assertGreaterEqual(len(re.findall(r"\b[0-9a-f]{64}\b", text)), 8)

    def test_cloud_knowledge_root_is_a_fixed_cross_account_contract(self):
        folder_id = "1F0RPxifumzVJncvweJEzOZtWjbmTCqAY"
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        weekly = (ROOT / "references" / "weekly-evolution.md").read_text(encoding="utf-8")
        manifest = (ROOT / "references" / "source-manifest.md").read_text(encoding="utf-8")

        for text in (skill, weekly, manifest):
            self.assertIn(folder_id, text)
        self.assertIn("唯一雲端存放根目錄", weekly)
        self.assertIn("不得存到「我的雲端硬碟」根目錄", skill)
        self.assertIn("個人與公司版本", weekly)
        self.assertIn("parent_ids", weekly)

    def test_knowledge_snapshot_is_actionable_and_self_contained(self):
        text = (ROOT / "references" / "knowledge-snapshot-v1.md").read_text(
            encoding="utf-8"
        )
        for heading in (
            "角色與影像鎖定",
            "導演與攝影",
            "Seedance 路由",
            "MiniMax H3 路由",
            "ComfyUI 路由",
            "聲音與後製",
            "4–6 秒短測與 QC",
        ):
            self.assertIn(heading, text)
        self.assertNotIn("../ai-video-learning-mentor", text)

    def test_storyboard_output_format_has_triggerable_commercial_board_template(self):
        text = (ROOT / "references" / "storyboard-output-formats.md").read_text(encoding="utf-8")
        for required in (
            "商品廣告一頁式分鏡板",
            "12 格",
            "時間碼",
            "產品參考圖",
            "品牌簽版",
            "CTA",
            "不保證實際解析度",
            "不虛構功效宣稱",
        ):
            self.assertIn(required, text)

    def test_project_state_reference_matches_initializer_schema(self):
        text = (ROOT / "references" / "project-state-and-versioning.md").read_text(encoding="utf-8")
        for field in (
            "schema_version", "project_name", "project_version", "current_gate", "status",
            "locked_artifacts", "open_decisions", "asset_status", "created_at",
        ):
            self.assertIn(f'"{field}"', text)
        for obsolete in ("project_id", "current_version", "locked_files"):
            self.assertNotIn(f'"{obsolete}"', text)


if __name__ == "__main__":
    unittest.main()
