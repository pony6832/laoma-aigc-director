import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / "references" / "prompt-library"
QUERY_SCRIPT = ROOT / "scripts" / "query_prompt_library.py"


class PromptLibraryTests(unittest.TestCase):
    def query(self, text: str, *, sheet: str | None = None, limit: int = 5):
        command = [
            sys.executable,
            str(QUERY_SCRIPT),
            "--library",
            str(LIBRARY),
            "--query",
            text,
            "--limit",
            str(limit),
            "--json",
        ]
        if sheet:
            command.extend(["--sheet", sheet])
        completed = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            check=False,
        )
        stderr = completed.stderr.decode("utf-8", errors="replace")
        stdout = completed.stdout.decode("utf-8", errors="replace")
        self.assertEqual(completed.returncode, 0, stderr)
        return json.loads(stdout)

    def test_exact_shortcut_query_returns_actionable_photo_prompt(self):
        results = self.query(
            "/RESTOREPHOTO", sheet="照片修復與影像優化提示詞", limit=1
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["record"]["快捷提示詞"], "/RESTOREPHOTO")
        self.assertIn("人物身份", results[0]["record"]["必須保留"])
        self.assertIn("不新增人物", results[0]["record"]["完整提示詞"])

    def test_keyword_query_can_find_video_lighting_by_chinese_name(self):
        results = self.query("自然窗光", sheet="影片燈光與環境光源提示詞")
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0]["record"]["中文名稱"], "自然窗光")
        self.assertIn("側窗", results[0]["record"]["光源方向／位置"])
        self.assertIn("多鏡頭請固定世界座標", results[0]["record"]["內容"])
        self.assertFalse(
            any(key.startswith("本頁收錄152組") for key in results[0]["record"])
        )

    def test_misc_character_template_is_retrievable_without_a_header(self):
        results = self.query("嚴格臉部一致性模式", sheet="雜項紀錄", limit=1)
        self.assertEqual(len(results), 1)
        self.assertIn("角色設計圖", results[0]["record"]["內容"])

    def test_unknown_sheet_is_rejected_instead_of_silently_searching_all(self):
        completed = subprocess.run(
            [
                sys.executable,
                str(QUERY_SCRIPT),
                "--library",
                str(LIBRARY),
                "--query",
                "窗光",
                "--sheet",
                "不存在",
                "--json",
            ],
            cwd=ROOT,
            capture_output=True,
            check=False,
        )
        stderr = completed.stderr.decode("utf-8", errors="replace")
        self.assertEqual(completed.returncode, 2)
        self.assertIn("unknown sheet", stderr)


if __name__ == "__main__":
    unittest.main()
