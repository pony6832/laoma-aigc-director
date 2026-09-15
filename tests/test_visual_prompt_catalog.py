import unittest

from scripts.query_visual_prompts import load_catalog, search


class VisualPromptCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_catalog()

    def test_normalizes_two_source_sets_to_173_unique_concepts(self):
        self.assertEqual(len(self.catalog["items"]), 173)
        self.assertEqual(len({item["id"] for item in self.catalog["items"]}), 173)
        self.assertEqual(len({item["canonical_key"] for item in self.catalog["items"]}), 173)

    def test_duplicate_wide_angle_tiles_merge_without_losing_provenance(self):
        results = search("wide angle", self.catalog)
        self.assertEqual(results[0]["canonical_key"], "wide-angle")
        self.assertEqual(results[0]["source_numbers"], [14, 41])
        self.assertIn("鏡位與視角", results[0]["source_sections"])
        self.assertIn("攝影與鏡頭效果", results[0]["source_sections"])

    def test_resolution_terms_do_not_claim_real_output_resolution(self):
        result = search("4K", self.catalog)[0]
        self.assertIn("不保證", result["risk_qc"])
        self.assertIn("輸出尺寸", result["risk_qc"])

    def test_source_numbering_anomaly_is_recorded(self):
        anomalies = self.catalog["source_audit"]["numbering_anomalies"]
        self.assertTrue(any("High Key" in item and "Low Key" in item for item in anomalies))
        self.assertTrue(any("60" in item and "Surreal" in item for item in anomalies))

    def test_chinese_category_query_returns_actionable_prompts(self):
        results = search("天氣 氛圍", self.catalog, limit=10)
        self.assertTrue(any(item["canonical_key"] == "fog" for item in results))
        self.assertTrue(all(item["prompt_fragment"] for item in results))
        self.assertTrue(all(item["invocation_zh"].startswith("老馬，使用 ") for item in results))

    def test_second_source_set_keeps_aliases_and_temporal_boundaries(self):
        self.assertEqual(self.catalog["source_audits"][1]["observed_tiles"], 100)
        self.assertEqual(self.catalog["source_audits"][1]["new_unique_concepts"], 77)
        self.assertEqual(search("OTS", self.catalog)[0]["canonical_key"], "over-the-shoulder")
        self.assertEqual(search("softlight", self.catalog)[0]["canonical_key"], "soft-lighting")
        speed_ramp = search("speed ramp", self.catalog)[0]
        self.assertEqual(speed_ramp["canonical_key"], "speed-ramp")
        self.assertIn("單張", speed_ramp["risk_qc"])
        self.assertIn("序列", speed_ramp["risk_qc"])

    def test_new_categories_cover_ads_action_surreal_editorial_and_bts(self):
        expected = {
            "商品與廣告",
            "動作與動態",
            "超現實與不可能",
            "攝影與編輯",
            "幕後與製作",
        }
        self.assertTrue(expected.issubset({item["category"] for item in self.catalog["items"]}))


if __name__ == "__main__":
    unittest.main()
