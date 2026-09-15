import unittest

from scripts.query_visual_prompts import load_catalog, search


class VisualPromptCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_catalog()

    def test_normalizes_source_tiles_to_96_unique_concepts(self):
        self.assertEqual(len(self.catalog["items"]), 96)
        self.assertEqual(len({item["id"] for item in self.catalog["items"]}), 96)
        self.assertEqual(len({item["canonical_key"] for item in self.catalog["items"]}), 96)

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


if __name__ == "__main__":
    unittest.main()
