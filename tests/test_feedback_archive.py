import json
from pathlib import Path
import tempfile
import unittest
from scripts.collect_knowledge_feedback import collect, mark_synced
from scripts.build_evolving_library import publish
from scripts.export_xlsx_snapshot import export
from tests.test_sync_and_drift import _write_xlsx


class ArchiveFeedbackTests(unittest.TestCase):
    def test_partial_test_result_can_be_published_without_claiming_pass(self):
        with tempfile.TemporaryDirectory() as d:
            xlsx = Path(d) / "test.xlsx"
            _write_xlsx(xlsx)
            payload = export(xlsx, "2026-10-18")
            payload["sheets"][0]["rows"][1][5] = "部分通過"
            target = publish(payload, Path(d) / "library", "2026-10-18-r1")
            saved = json.loads((target / "sheet-00.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["rows"][1][5], "部分通過")

    def test_category_root_collects_chinese_qc_and_marks_same_file(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            path = root / "05_影片_Video" / "20261018_測試_V01" / "09_報告與QC" / "KNOWLEDGE_FEEDBACK.jsonl"
            path.parent.mkdir(parents=True)
            row = dict(zip(("回饋ID", "來源案件", "平台", "假說", "驗收條件", "輸出與證據", "結果", "日期"),
                           ("case#1", "case", "local", "test", "qc", "report", "部分通過", "2026-10-18")))
            path.write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")
            self.assertEqual([r["回饋ID"] for r in collect(root)], ["case#1"])
            self.assertEqual(mark_synced(root, {"case#1"}, "2026-10-18"), 1)
            self.assertEqual(collect(root), [])

    def test_archived_nested_cases_are_not_marked(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            path = root / "_封存" / "case" / "09_reports_and_qc" / "KNOWLEDGE_FEEDBACK.jsonl"
            path.parent.mkdir(parents=True)
            path.write_text("invalid archived content", encoding="utf-8")
            self.assertEqual(collect(root), [])
            self.assertEqual(mark_synced(root, {"case#1"}, "2026-10-18"), 0)
