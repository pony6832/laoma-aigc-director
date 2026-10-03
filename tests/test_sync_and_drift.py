"""Tests for the 2026-10-03 fixes: cloud→local sync, freshness, drift audit, feedback loop."""

from datetime import date
import io
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
import zipfile

from scripts.build_evolving_library import SOURCE_ID, publish
from scripts.collect_knowledge_feedback import collect, mark_synced
from scripts.export_xlsx_snapshot import export
from scripts.init_project import create_project
from scripts.project_overview import overview
from scripts.query_prompt_library import main as query_main, query_library, snapshot_info
from scripts.validate_project import audit_project, validate_project

_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def _sheet_xml(rows):
    body = []
    for r, row in rows:
        cells = "".join(
            f'<c r="{col}{r}" t="inlineStr"><is><t>{value}</t></is></c>'
            if not isinstance(value, tuple)
            else f'<c r="{col}{r}" s="{value[1]}"><v>{value[0]}</v></c>'
            for col, value in row
        )
        body.append(f'<row r="{r}">{cells}</row>')
    return f'<worksheet xmlns="{_MAIN}"><sheetData>{"".join(body)}</sheetData></worksheet>'


def _write_xlsx(path: Path) -> None:
    """Minimal workbook: a catalog, a source sheet, a titled sheet and a hidden sheet."""
    header = [("A", "知識ID"), ("B", "中文名稱"), ("C", "主分類"), ("D", "來源ID"), ("E", "證據等級"),
              ("F", "實測狀態"), ("G", "生命週期"), ("H", "查核日期"), ("I", "複查日期")]
    sheets = {
        "02_提示詞總庫": [(1, header),
                     (2, [("A", "N1"), ("B", "自然窗光"), ("C", "影片燈光"), ("D", "S1"), ("E", "官方文件"),
                          ("F", "未實測"), ("G", "可參考"), ("H", "2026-09-11"), ("I", (46000, 1))])],
        "05_來源登錄": [(1, [("A", "來源ID"), ("B", "URL"), ("C", "類型")]), (2, [("A", "S1"), ("B", "https://example.org")])],
        "22_電影配樂與AI音樂": [(1, [("A", "第22頁標題")]), (2, [("A", "規則說明")]),
                         (3, [("A", "知識ID"), ("B", "中文名稱"), ("C", "核心目的")]),
                         (5, [("A", "MUS-001"), ("B", "故事功能"), ("C", "spotting 入點")])],
        "23_來源對照_配樂": [(1, [("A", "來源序號"), ("B", "x"), ("C", "y")])],
    }
    names = list(sheets)
    workbook = (f'<workbook xmlns="{_MAIN}" xmlns:r="{_REL}"><sheets>'
                + "".join(f'<sheet name="{n}" sheetId="{i + 1}" r:id="rId{i + 1}"'
                          + (' state="hidden"' if n.startswith("23") else "") + "/>"
                          for i, n in enumerate(names))
                + "</sheets></workbook>")
    rels = ('<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            + "".join(f'<Relationship Id="rId{i + 1}" Target="worksheets/sheet{i + 1}.xml" Type="ws"/>'
                      for i in range(len(names)))
            + "</Relationships>")
    styles = (f'<styleSheet xmlns="{_MAIN}"><cellXfs count="2"><xf numFmtId="0"/><xf numFmtId="14"/></cellXfs></styleSheet>')
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", rels)
        archive.writestr("xl/styles.xml", styles)
        for i, name in enumerate(names):
            archive.writestr(f"xl/worksheets/sheet{i + 1}.xml", _sheet_xml(sheets[name]))


class ExportAndPublishTests(unittest.TestCase):
    def test_export_keeps_visible_sheets_header_rows_dates_and_blank_rows(self):
        with tempfile.TemporaryDirectory() as d:
            xlsx = Path(d) / "master.xlsx"
            _write_xlsx(xlsx)
            payload = export(xlsx, "2026-10-03")
            names = [s["name"] for s in payload["sheets"]]
            self.assertEqual(names, ["02_提示詞總庫", "05_來源登錄", "22_電影配樂與AI音樂"])
            self.assertEqual(payload["spreadsheet_id"], SOURCE_ID)
            music = payload["sheets"][2]
            self.assertEqual(music["header_row"], 3)
            self.assertEqual(music["rows"][3], [], "interior blank row 4 must be preserved")
            catalog = payload["sheets"][0]
            self.assertEqual(catalog["rows"][1][8], "2025-12-09", "date-styled serial converts to ISO date")

    def test_published_snapshot_queries_titled_sheet_and_records_capture_date(self):
        with tempfile.TemporaryDirectory() as d:
            xlsx = Path(d) / "master.xlsx"
            _write_xlsx(xlsx)
            library = Path(d) / "lib"
            publish(export(xlsx, "2026-10-03"), library, "2026-10-03-r1")
            active = json.loads((library / "active.json").read_text(encoding="utf-8"))
            self.assertEqual(active, {"snapshot": "2026-10-03-r1", "captured_at": "2026-10-03"})
            hits = query_library(library, "spotting")
            self.assertEqual(hits[0]["sheet"], "22_電影配樂與AI音樂")
            self.assertEqual(hits[0]["record"]["知識ID"], "MUS-001")

    def test_invalid_header_row_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            xlsx = Path(d) / "master.xlsx"
            _write_xlsx(xlsx)
            payload = export(xlsx, "2026-10-03")
            payload["sheets"][2]["header_row"] = 99
            with self.assertRaisesRegex(ValueError, "invalid header_row"):
                publish(payload, Path(d) / "lib", "2026-10-03-r1")


class FreshnessTests(unittest.TestCase):
    def _library(self, d):
        xlsx = Path(d) / "master.xlsx"
        _write_xlsx(xlsx)
        library = Path(d) / "lib"
        publish(export(xlsx, "2026-10-03"), library, "2026-10-03-r1")
        return library

    def test_snapshot_info_reports_age_and_staleness(self):
        with tempfile.TemporaryDirectory() as d:
            library = self._library(d)
            self.assertFalse(snapshot_info(library, today=date(2026, 10, 5))["stale"])
            info = snapshot_info(library, today=date(2026, 10, 20))
            self.assertTrue(info["stale"])
            self.assertEqual(info["age_days"], 17)

    def test_review_overdue_flag(self):
        with tempfile.TemporaryDirectory() as d:
            library = self._library(d)
            hit = query_library(library, "自然窗光", today=date(2026, 10, 3))[0]
            self.assertTrue(hit["review_overdue"], "複查日期 2025-12-09 is before 2026-10-03")
            hit = query_library(library, "自然窗光", today=date(2025, 12, 1))[0]
            self.assertFalse(hit["review_overdue"])

    def test_cli_warns_on_stderr_but_keeps_json_clean(self):
        with tempfile.TemporaryDirectory() as d:
            library = self._library(d)
            active = library / "active.json"
            manifest = library / "2026-10-03-r1" / "manifest.json"
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["captured_at"] = "2020-01-01"
            manifest.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                code = query_main(["--library", str(library), "--query", "自然窗光", "--json"])
            self.assertEqual(code, 0)
            self.assertIn("days old", err.getvalue())
            json.loads(out.getvalue())
            self.assertTrue(active.is_file())


class DriftAuditTests(unittest.TestCase):
    def _project(self, d):
        return create_project(Path(d), "測試案")

    def _age_state(self, project, seconds):
        """Make the whole initialised project (state included) look old."""
        past = time.time() - seconds
        for path in project.rglob("*"):
            if path.is_file():
                os.utime(path, (past, past))

    def test_fresh_project_has_no_warnings(self):
        with tempfile.TemporaryDirectory() as d:
            project = self._project(d)
            self.assertEqual(validate_project(project), [])
            self.assertEqual(audit_project(project), [])

    def test_work_after_state_is_reported_as_stale(self):
        with tempfile.TemporaryDirectory() as d:
            project = self._project(d)
            self._age_state(project, 2 * 86400)
            (project / "02_character_and_look" / "test_v01.mp4").write_bytes(b"x")
            warnings = audit_project(project)
            self.assertTrue(any("may be stale" in w for w in warnings), warnings)

    def test_tool_internal_and_feedback_files_do_not_count_as_work(self):
        with tempfile.TemporaryDirectory() as d:
            project = self._project(d)
            self._age_state(project, 2 * 86400)
            (project / "01_inputs" / "canvas.sqlite-wal").write_bytes(b"x")
            (project / "09_reports_and_qc" / "KNOWLEDGE_FEEDBACK.jsonl").write_text("", encoding="utf-8")
            self.assertEqual(audit_project(project), [])

    def test_generated_media_under_inputs_is_reported(self):
        with tempfile.TemporaryDirectory() as d:
            project = self._project(d)
            out = project / "01_inputs" / "canvas" / "outputs" / "videos"
            out.mkdir(parents=True)
            (out / "generated-1.mp4").write_bytes(b"x")
            (project / "01_inputs" / "reference.png").write_bytes(b"x")
            warnings = audit_project(project)
            self.assertEqual(len(warnings), 1)
            self.assertIn("1 generated media file", warnings[0])

    def test_nonstandard_outputs_warn_before_gate_four(self):
        with tempfile.TemporaryDirectory() as d:
            project = self._project(d)
            state_path = project / "PROJECT_STATE.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["asset_status"]["outputs"] = [{"role": "package", "path": "04_shot_design", "count": 3}]
            state_path.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
            self.assertEqual(validate_project(project), [])
            self.assertTrue(any("blocks Gate 4" in w for w in audit_project(project)))

    def test_overview_skips_archive_folders(self):
        with tempfile.TemporaryDirectory() as d:
            self._project(d)
            archive = Path(d) / "_封存"
            archive.mkdir()
            create_project(archive, "舊案")
            rows = overview(Path(d))
            self.assertEqual([r["project"] for r in rows], ["測試案_V01"])


class FeedbackTests(unittest.TestCase):
    def _entry(self, **changes):
        entry = {"回饋ID": "案_V01#FB-001", "來源案件": "案_V01", "平台": "H3", "假說": "h",
                 "驗收條件": "a", "輸出與證據": "e", "結果": "實測失敗", "日期": "2026-10-03", "已同步": ""}
        entry.update(changes)
        return entry

    def _write(self, root, entries):
        path = Path(root) / "案_V01" / "09_reports_and_qc" / "KNOWLEDGE_FEEDBACK.jsonl"
        path.parent.mkdir(parents=True)
        path.write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in entries), encoding="utf-8")
        return path

    def test_collect_then_mark_synced(self):
        with tempfile.TemporaryDirectory() as d:
            self._write(d, [self._entry(), self._entry(**{"回饋ID": "案_V01#FB-002", "結果": "實測通過"})])
            self.assertEqual(len(collect(Path(d))), 2)
            self.assertEqual(mark_synced(Path(d), {"案_V01#FB-001"}, "2026-10-04"), 1)
            remaining = collect(Path(d))
            self.assertEqual([e["回饋ID"] for e in remaining], ["案_V01#FB-002"])
            self.assertEqual(len(collect(Path(d), include_synced=True)), 2)

    def test_invalid_result_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            self._write(d, [self._entry(結果="成功")])
            with self.assertRaisesRegex(ValueError, "invalid 結果"):
                collect(Path(d))


if __name__ == "__main__":
    unittest.main()
