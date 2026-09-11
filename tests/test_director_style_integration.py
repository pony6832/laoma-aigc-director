import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
STYLE_ROOT = ROOT / "references" / "director-styles"


class DirectorStyleIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.catalog = json.loads(
            (STYLE_ROOT / "catalog.json").read_text(encoding="utf-8")
        )

    def test_catalog_has_twenty_unique_lenses_including_required_directors(self):
        styles = self.catalog["styles"]
        self.assertEqual(len(styles), 20)
        slugs = [item["slug"] for item in styles]
        self.assertEqual(len(slugs), len(set(slugs)))
        self.assertIn("nolan", slugs)
        self.assertIn("wong-kar-wai", slugs)

    def test_every_lens_is_local_and_marked_as_community_synthesis(self):
        required = (
            "一句话镜头 / Lens in one line",
            "反例：这不是什么 / What this lens is NOT",
            "叙事方法",
            "镜头语言",
            "灯光与色彩",
            "剪辑节奏",
            "声音与音乐",
            "风格参数 / Style parameters",
            "可迁移拍摄清单",
        )
        for item in self.catalog["styles"]:
            self.assertEqual(item["evidence_status"], "community_synthesis")
            path = (STYLE_ROOT / item["path"]).resolve()
            self.assertEqual(path.parent, (STYLE_ROOT / "lenses").resolve())
            text = path.read_text(encoding="utf-8")
            for heading in required:
                self.assertIn(heading, text, f"{item['slug']}: {heading}")

    def test_routing_keeps_laoma_as_authority_and_forbids_direct_imitation(self):
        text = (ROOT / "references" / "director-style-routing.md").read_text(
            encoding="utf-8"
        )
        for phrase in (
            "一次只載入一個導演鏡頭",
            "不得覆蓋 PROJECT_STATE.json",
            "不得複製特定電影的鏡頭、台詞、角色或情節",
            "Gate 3",
            "Gate 4",
            "3／5",
        ):
            self.assertIn(phrase, text)

    def test_governance_separates_sources_synthesis_and_project_facts(self):
        text = (ROOT / "references" / "director-knowledge-governance.md").read_text(
            encoding="utf-8"
        )
        for phrase in (
            "原始來源層",
            "方法綜合層",
            "本案事實層",
            "每項可驗證主張都要附來源",
            "不得默默消除矛盾",
            "過時",
        ):
            self.assertIn(phrase, text)

    def test_review_template_requires_observable_style_evidence(self):
        text = (ROOT / "assets" / "director-style-review-template.md").read_text(
            encoding="utf-8"
        )
        for axis in ("敘事結構", "鏡頭與構圖", "燈光與色彩", "剪輯節奏", "聲音與表演"):
            self.assertIn(axis, text)
        for verdict in ("STYLE_LOCK_PASS", "STYLE_DRIFT", "INSUFFICIENT_EVIDENCE"):
            self.assertIn(verdict, text)


if __name__ == "__main__":
    unittest.main()
