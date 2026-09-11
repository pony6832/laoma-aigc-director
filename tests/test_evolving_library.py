import copy
import json
from pathlib import Path
import tempfile
import unittest
from scripts.build_evolving_library import publish, SOURCE_ID
from scripts.query_prompt_library import query_library

class EvolvingLibraryTests(unittest.TestCase):
    def fixture(self):
        return {"spreadsheet_id":SOURCE_ID,"captured_at":"2026-09-11","sheets":[
          {"name":"02_提示詞總庫","rows":[
             ["知識ID","中文名稱","主分類","來源ID","證據等級","實測狀態","生命週期","查核日期"],
             ["N1","自然窗光","影片燈光","S1","官方文件","未實測","可參考","2026-09-11"],
             ["N2","自然窗光舊方法","影片燈光","S1","官方文件","未實測","停用","2026-09-11"]]},
          {"name":"05_來源登錄","rows":[["來源ID","URL"],["S1","https://example.org"]]}]}
    def test_publish_and_query_excludes_retired_records(self):
        with tempfile.TemporaryDirectory() as d:
            publish(self.fixture(),d,"2026-09-11-test")
            result=query_library(Path(d),"自然窗光",sheet_name="02_提示詞總庫")
            self.assertEqual([r["record"]["知識ID"] for r in result],["N1"])
    def test_duplicate_id_rejected_without_switching_active(self):
        with tempfile.TemporaryDirectory() as d:
            publish(self.fixture(),d,"2026-09-11-first")
            before=(Path(d)/"active.json").read_bytes()
            bad=self.fixture()
            bad["sheets"][0]["rows"][2][0]="N1"
            with self.assertRaisesRegex(ValueError,"duplicate knowledge"):
                publish(bad,d,"2026-09-11-second")
            self.assertEqual(before,(Path(d)/"active.json").read_bytes())
    def test_unknown_source_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            bad=self.fixture()
            bad["sheets"][0]["rows"][1][3]="MISSING"
            with self.assertRaisesRegex(ValueError,"unknown source"):
                publish(bad,d,"2026-09-11-test")
    def test_existing_snapshot_is_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            publish(self.fixture(),d,"2026-09-11-test")
            with self.assertRaises(FileExistsError):
                publish(self.fixture(),d,"2026-09-11-test")
    def test_changed_snapshot_fails_hash_check(self):
        with tempfile.TemporaryDirectory() as d:
            target=publish(self.fixture(),d,"2026-09-11-test")
            (target/"sheet-00.json").write_text("{}",encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"hash mismatch"):
                query_library(Path(d),"自然窗光")

    def test_publisher_uses_lf_line_endings(self):
        with tempfile.TemporaryDirectory() as d:
            target = publish(self.fixture(), d, "2026-09-11-test")
            self.assertNotIn(b"\r\n", (Path(d) / "active.json").read_bytes())
            self.assertNotIn(b"\r\n", (target / "manifest.json").read_bytes())
