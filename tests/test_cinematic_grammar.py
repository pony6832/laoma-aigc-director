import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "query_cinematic_grammar.py"


def load_module():
    spec = importlib.util.spec_from_file_location("query_cinematic_grammar", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class CinematicGrammarTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.catalog = self.module.load_catalog(
            ROOT / "references" / "cinematic-grammar.json"
        )

    def test_routes_abstract_emotion_to_visible_performance_method(self):
        results = self.module.search(self.catalog, "角色很緊張但表演空泛", limit=3)
        self.assertEqual(results[0]["id"], "CRAFT-06")
        self.assertIn("身體", results[0]["output_contract"])

    def test_routes_unmotivated_camera_move_to_motion_method(self):
        results = self.module.search(self.catalog, "運鏡只是在炫技，沒有敘事動機", limit=3)
        self.assertEqual(results[0]["id"], "CRAFT-04")
        self.assertIn("動機", results[0]["output_contract"])

    def test_routes_fight_request_to_physical_feedback_method(self):
        results = self.module.search(self.catalog, "打鬥追逐要有碰撞與環境反應", limit=3)
        self.assertEqual(results[0]["id"], "CRAFT-08")
        self.assertIn("物理回饋", results[0]["output_contract"])

    def test_catalog_excludes_stale_platform_capability_claims(self):
        serialized = str(self.catalog).casefold()
        for product in ("seedance", "kling", "higgsfield", "可靈", "可灵"):
            self.assertNotIn(product.casefold(), serialized)

    def test_empty_query_returns_no_unrequested_method(self):
        self.assertEqual(self.module.search(self.catalog, "   "), [])


if __name__ == "__main__":
    unittest.main()
