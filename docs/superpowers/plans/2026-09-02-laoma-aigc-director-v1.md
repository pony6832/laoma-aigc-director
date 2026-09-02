# 老馬 AIGC 導演 Agent V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立、驗證並安裝一個獨立的 `laoma-aigc-director` Codex Skill，使它能以製片總導演模式把一句點子或一張圖推進為版本化的完整 AIGC 影片製作包。

**Architecture:** 可攜式 Git 專案是唯一可編輯來源，正式 Codex Skill 是由同步腳本產生的安裝副本。`SKILL.md` 負責身份、可執行流程、資訊優先序、四個 Gate 與本地參考路由；版本化知識快照、狀態規格、模板與失敗回復各自獨立，Python 3.11 標準函式庫腳本負責案件初始化、結構／完整性／完成證據驗證與來源／安裝副本雜湊比對。

**Tech Stack:** Markdown、YAML、JSON、Python 3.11 標準函式庫、PowerShell、Git、Codex Skill validator

## Global Constraints

- 技術形態：獨立 Agent／Skill，不只是單一聊天視窗，也不直接擴充既有 `ai-video-learning-mentor`。
- 預設身份：製片總導演；預設交付完整製作包。
- 四個 Gate 固定為方向鎖定、角色與影像鎖定、導演方案鎖定、成片驗收。
- 舊案件只提供方法與失敗經驗，不提供新案件的人物、故事或私人素材。
- `CHARACTER_PROFILE.json` 是持續製作角色的唯一事實來源；`PROJECT_STATE.json` 是案件進度與鎖定版本的唯一狀態來源。
- 原始輸入與舊版本不得覆蓋；衍生檔案使用明確版本號。
- 沒有可驗證輸出時不得聲稱已生成或已成片。
- 模型、平台、價格、限制和入口資訊在執行時以官方來源重查。
- V1 只用 Python 3.11 標準函式庫，不新增第三方執行期依賴。
- 可攜式來源位於 `C:\Users\pony6832\Documents\Codex\Codex專案分類\08 - AIGC影像生成相關\github-release\laoma-aigc-director`。
- 正式安裝目標位於 `C:\Users\pony6832\.codex\skills\laoma-aigc-director`。
- 案件預設根目錄位於 `C:\Users\pony6832\Documents\Codex\Codex專案分類\08 - AIGC影像生成相關\老馬AIGC導演專案`。

## Final-review contract（2026-09-02）

本節更新並優先於下方最初的逐步實作描述：

- V1 唯一狀態 schema 為 `1.0`；`project_version` 使用 `VNN` 並與 `<project_name>_<project_version>` 目錄精確一致；時間必須是含時區 ISO 8601。
- `locked_artifacts` 是含 `role/path/version/sha256/reason` 的物件清單；驗證器拒絕越界、遺失與雜湊不符。`open_decisions` 與 `asset_status` 也使用文件化結構，不新增同義欄位。
- Gate 1–3 不可 `complete`；Gate 4 `complete` 要求非空輸出、匹配雜湊、非空白報告、全數通過且有證據的 QC、具名且含時區的核准、無未決項與 false-completion 旗標為 false。任何固定詞句都不是完成證據。
- Gate 2 核准必須鎖定 `02_character_and_look/` 內非空、可辨識的角色總覽圖與無角色場景參考圖，以及能從 MP4／MOV 容器驗證且宣告時長相符的實際 4–6 秒一致性測試；不能用文字、空檔、prompt、計畫或自行宣告時長代替。
- 知識路由使用套件內 `director-methods-v1.0.0` 快照；`source-manifest.md` 逐方法記錄來源檔案、SHA-256／版本、來源等級、適用入口、同步日期及排除內容，不在 runtime 依賴來源技能資料夾。
- 七案由執行 Agent 讀取最終 runtime 後在隔離目錄建立 response／artifact bundles，再由獨立標準函式庫 validator 驗證結構不變量，並交叉檢查 `project-state.json`、前置 Gate 鎖定角色／雜湊與回覆中的明確完成聲明；這不代表模型輸出本身具模型無關的決定性，也不代表已生成影片。
- `sync_skill.py` 清理本次失敗 staging；若 promotion 在舊安裝改名後失敗，還原舊安裝；成功替換後保留備份。
- 驗證報告分開記錄「被驗證 commit」與後續報告／修復 commit；只有在精確 final head 重跑才可稱 final head 已驗證。

---

## File Map

| File | Responsibility |
|---|---|
| `SKILL.md` | 入口身份、模式、四個 Gate、資訊優先序與參考路由 |
| `agents/openai.yaml` | Codex UI 名稱、說明與預設啟動提示 |
| `references/director-identity.md` | 製片總導演、共同導演、導師三種互動模式 |
| `references/production-gates.md` | 每個 Gate 的輸入、產物、通過條件和停止條件 |
| `references/knowledge-routing.md` | 角色、故事、攝影、Seedance、H3、ComfyUI、聲音及後製的按需路由 |
| `references/knowledge-snapshot-v1.md` | 自包含、版本化且可執行的角色／導演／生成入口／聲音／短測 QC 方法 |
| `references/project-state-and-versioning.md` | `PROJECT_STATE.json`、鎖定狀態、版本命名和資料夾契約 |
| `references/quality-and-recovery.md` | QC 量表、失敗標籤、單變數重試與誠實完成規則 |
| `references/source-manifest.md` | 從影音導師匯入的方法、來源版本、同步日期與排除內容 |
| `assets/project-brief-template.md` | Gate 1 案件簡報模板 |
| `assets/production-bible-template.md` | 全案共同創意、視覺、攝影、聲音與連戲規則 |
| `assets/character-profile-template.json` | 角色唯一事實來源模板 |
| `assets/shot-production-table-template.md` | Gate 3 逐鏡製作表 |
| `assets/generation-report-template.md` | Gate 4 生成、重試、QC 與交付紀錄 |
| `scripts/init_project.py` | 安全建立新案件骨架與初始狀態 |
| `scripts/validate_project.py` | 驗證 Gate、必要檔案、狀態與版本引用 |
| `scripts/sync_skill.py` | 將可攜式來源安全同步到 Codex Skill 目錄並寫入雜湊 manifest |
| `tests/test_skill_contract.py` | Skill 入口與 UI metadata 契約 |
| `tests/test_reference_contract.py` | 參考文件存在、路由與來源隔離契約 |
| `tests/test_templates.py` | JSON／Markdown 模板契約 |
| `tests/test_init_project.py` | 初始化、不覆蓋與版本命名行為 |
| `tests/test_validate_project.py` | Gate 完整度與錯誤診斷行為 |
| `tests/test_sync_skill.py` | 安裝、副本內容與拒絕覆蓋行為 |
| `tests/fixtures/scenarios.md` | 七個代表性真實請求和人工行為驗收條件 |
| `tests/fixtures/acceptance-contracts.json` | 七案結構化模式、Gate、產物、禁止行為與證據不變量 |
| `tests/acceptance/` | 執行 Agent 依最終 runtime 產生的七組 response／artifact bundles |
| `tests/acceptance_validator.py` | 獨立驗證 bundle 產物、雜湊、事實與完成證據 |

---

### Task 1: 建立 Skill 入口與 UI 身份

**Files:**
- Create: `SKILL.md`
- Create: `agents/openai.yaml`
- Create: `tests/test_skill_contract.py`

**Interfaces:**
- Consumes: 已核准設計中的模式、四個 Gate 與資訊優先序。
- Produces: Codex 可發現的 `laoma-aigc-director` Skill；後續參考文件使用固定相對連結。

- [ ] **Step 1: 寫入會失敗的入口契約測試**

```python
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SkillContractTests(unittest.TestCase):
    def test_skill_frontmatter_and_core_contract(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertRegex(text, r"(?s)^---\s+name: laoma-aigc-director\s+description: .+?\s+---")
        for phrase in (
            "製片總導演模式",
            "Gate 1",
            "Gate 2",
            "Gate 3",
            "Gate 4",
            "PROJECT_STATE.json",
            "CHARACTER_PROFILE.json",
        ):
            self.assertIn(phrase, text)

    def test_openai_metadata_matches_skill(self):
        text = (ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn("display_name: 老馬 AIGC 導演", text)
        self.assertIn("default_prompt:", text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 執行測試並確認缺少檔案而失敗**

Run: `python -m unittest tests.test_skill_contract -v`  
Expected: FAIL，指出 `SKILL.md` 或 `agents/openai.yaml` 不存在。

- [ ] **Step 3: 建立最小但完整的 Skill 入口**

`SKILL.md` 必須包含以下實際契約：

```markdown
---
name: laoma-aigc-director
description: Plan, direct, produce, diagnose, and package complete AIGC video projects from one idea, image, or production request. Use for character and look development, story, shot design, Seedance or H3 prompts, sound, edit planning, continuity QC, and complete production delivery.
---

# 老馬 AIGC 導演

預設以製片總導演模式工作。收到一張圖、一個點子或一項製作需求時，先產出可討論第一版，再依四個 Gate 推進完整製作包。

## 不可違反的規則

- 使用者本次要求優先於所有預設。
- `PROJECT_STATE.json` 是案件進度的唯一狀態來源。
- `CHARACTER_PROFILE.json` 是持續製作角色的唯一事實來源。
- 舊案例只提供方法，不提供新案件的人物、故事或私人素材。
- 不覆蓋原始輸入或舊版本。
- 沒有可驗證輸出時，不得聲稱已生成或已成片。

## 四個 Gate

- Gate 1：方向鎖定。
- Gate 2：角色與影像鎖定。
- Gate 3：導演方案鎖定。
- Gate 4：成片驗收。

詳細規格依任務按需讀取 `references/` 中的對應文件。
```

`agents/openai.yaml` 使用：

```yaml
interface:
  display_name: 老馬 AIGC 導演
  short_description: 從點子或參考圖推進到完整 AIGC 影片製作包
  default_prompt: 請以製片總導演模式，從我提供的點子、圖片或需求開始建立第一版製作方案。
```

- [ ] **Step 4: 執行入口契約與官方 Skill validator**

Run: `python -m unittest tests.test_skill_contract -v`  
Expected: PASS。

Run: `python "C:\Users\pony6832\.codex\skills\.system\skill-creator\scripts\quick_validate.py" .`  
Expected: 顯示 Skill 驗證成功，沒有 frontmatter、命名或 scaffold placeholder 錯誤。

- [ ] **Step 5: 提交入口與測試**

```powershell
git add SKILL.md agents/openai.yaml tests/test_skill_contract.py
git commit -m "feat: add AIGC director skill entry"
```

---

### Task 2: 建立版本化知識核心與路由

**Files:**
- Create: `references/director-identity.md`
- Create: `references/production-gates.md`
- Create: `references/knowledge-routing.md`
- Create: `references/knowledge-snapshot-v1.md`
- Create: `references/project-state-and-versioning.md`
- Create: `references/quality-and-recovery.md`
- Create: `references/source-manifest.md`
- Modify: `SKILL.md`
- Create: `tests/test_reference_contract.py`

**Interfaces:**
- Consumes: `SKILL.md` 的相對連結；既有影音導師中已核准的製片方法。
- Produces: `REFERENCE_FILES: tuple[str, ...]` 測試常數所驗證的六份參考文件；後續模板與腳本依據的 Gate／狀態規格。

- [ ] **Step 1: 寫入參考文件路由測試**

```python
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
)


class ReferenceContractTests(unittest.TestCase):
    def test_all_routed_references_exist(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        links = re.findall(r"\]\((references/[^)]+\.md)\)", skill)
        self.assertEqual({Path(link).name for link in links}, set(REFERENCE_FILES))
        for link in links:
            self.assertTrue((ROOT / link).is_file(), link)

    def test_source_manifest_records_isolation_and_date(self):
        text = (ROOT / "references" / "source-manifest.md").read_text(encoding="utf-8")
        self.assertIn("同步日期：2026-09-02", text)
        self.assertIn("只提煉方法", text)
        self.assertIn("不匯入私人素材", text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 執行測試並確認六份參考文件尚未建立**

Run: `python -m unittest tests.test_reference_contract -v`  
Expected: FAIL，原因為路由連結或參考文件不存在。

- [ ] **Step 3: 建立六份聚焦參考文件並補上 SKILL 路由**

每份文件使用以下確定內容邊界：

```text
director-identity.md
  - 製片總導演為預設
  - 共同導演與導師模式的顯式切換口令
  - 模式只改互動密度，不降低事實、版本與 QC 標準

production-gates.md
  - Gate 1 至 Gate 4 的輸入、最低產物、通過條件、停止條件
  - Gate 3 通過前不得進入大量或高成本生成

knowledge-routing.md
  - 角色／定裝、故事／劇本、攝影／分鏡、Seedance、H3、ComfyUI、聲音／後製的觸發條件
  - 每個分類路由到套件內 `knowledge-snapshot-v1.md` 的可執行方法，不依賴來源技能
  - 只讀取當前案件需要的專科

project-state-and-versioning.md
  - PROJECT_STATE schema、狀態值 draft|awaiting_approval|approved|blocked|complete
  - 檔名 `_v01` 起跳，不覆蓋舊版；鎖定檔案使用 SHA-256

quality-and-recovery.md
  - identity_drift、wardrobe_drift、spatial_error、camera_error、motion_error、anatomy_error、audio_error、prompt_pollution
  - 回到最近鎖定版本、縮短時長、降低動作複雜度、一次只改一個主變數

source-manifest.md
  - 同步日期 2026-09-02
  - 每項方法逐列記錄來源檔案、來源 SHA-256／版本、來源等級、適用入口、同步日期與排除內容
  - 只提煉方法；不匯入私人素材、舊角色事實、舊故事或專屬提示詞
  - 會變動的產品規格不匯入為固定事實，執行時重新查證
```

在 `SKILL.md` 中加入六個 Markdown 相對連結，並說明各自何時讀取。

- [ ] **Step 4: 執行參考文件測試與連結掃描**

Run: `python -m unittest tests.test_reference_contract -v`  
Expected: PASS。

Run: `rg -n "T[B]D|T[O]DO|FIX[M]E|舊角色姓名|私人素材路徑" SKILL.md references`  
Expected: 只有 `source-manifest.md` 中的排除規則可提到私人素材，不得出現 placeholder。

- [ ] **Step 5: 提交知識核心**

```powershell
git add SKILL.md references tests/test_reference_contract.py
git commit -m "feat: add versioned director knowledge core"
```

---

### Task 3: 建立 Production Bible 與交付模板

**Files:**
- Create: `assets/project-brief-template.md`
- Create: `assets/production-bible-template.md`
- Create: `assets/character-profile-template.json`
- Create: `assets/shot-production-table-template.md`
- Create: `assets/generation-report-template.md`
- Create: `tests/test_templates.py`

**Interfaces:**
- Consumes: `production-gates.md` 與 `project-state-and-versioning.md`。
- Produces: `init_project.py` 複製到案件中的五個固定模板；JSON 必須能由 `json.loads()` 讀取。

- [ ] **Step 1: 寫入模板契約測試**

```python
from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TemplateTests(unittest.TestCase):
    def test_character_profile_is_valid_and_versioned(self):
        data = json.loads((ROOT / "assets" / "character-profile-template.json").read_text(encoding="utf-8"))
        self.assertEqual(data["schema_version"], "1.0")
        self.assertEqual(data["status"], "draft")
        self.assertEqual(data["identity"]["anchors"], [])
        self.assertEqual(data["locked_fields"], [])

    def test_markdown_templates_cover_their_gate(self):
        expected = {
            "project-brief-template.md": ("作品目的", "發布平台", "權利狀態"),
            "production-bible-template.md": ("視覺規則", "攝影規則", "聲音規則", "連戲規則"),
            "shot-production-table-template.md": ("時間碼", "焦段", "運鏡", "連續性", "影片提示詞"),
            "generation-report-template.md": ("輸入雜湊", "生成入口", "QC", "已知限制"),
        }
        for name, phrases in expected.items():
            text = (ROOT / "assets" / name).read_text(encoding="utf-8")
            for phrase in phrases:
                self.assertIn(phrase, text, f"{name}: {phrase}")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 執行測試並確認模板缺失**

Run: `python -m unittest tests.test_templates -v`  
Expected: FAIL，指出第一個缺少的模板。

- [ ] **Step 3: 建立五個可直接使用的模板**

`character-profile-template.json` 使用以下合法 JSON：

```json
{
  "schema_version": "1.0",
  "profile_version": "v01",
  "status": "draft",
  "identity": {
    "name": "",
    "type": "fictional_or_authorized",
    "anchors": []
  },
  "appearance": {
    "face": [],
    "hair": [],
    "body_proportions": []
  },
  "wardrobe": [],
  "props": [],
  "performance": [],
  "reference_roles": [],
  "locked_fields": [],
  "assumptions": [],
  "source_hashes": []
}
```

四份 Markdown 模板必須具備測試列出的欄位，並以 `已觀察／創作推定／待決定／已鎖定` 區分事實狀態；逐鏡表每列另含敘事用途、人物走位、構圖焦點、燈光、表演、聲音與預期結尾狀態。

- [ ] **Step 4: 執行模板測試**

Run: `python -m unittest tests.test_templates -v`  
Expected: PASS。

- [ ] **Step 5: 提交模板**

```powershell
git add assets tests/test_templates.py
git commit -m "feat: add production bible and delivery templates"
```

---

### Task 4: 實作安全案件初始化器

**Files:**
- Create: `scripts/init_project.py`
- Create: `tests/test_init_project.py`

**Interfaces:**
- Consumes: `assets/` 五個模板。
- Produces: `create_project(projects_root: Path, project_name: str) -> Path`；建立 `<slug>_V01` 並回傳絕對路徑。

- [ ] **Step 1: 寫入初始化器失敗測試**

```python
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from scripts.init_project import create_project


class InitProjectTests(unittest.TestCase):
    def test_creates_versioned_project_without_overwriting(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = create_project(root, "台北孤城")
            second = create_project(root, "台北孤城")
            self.assertEqual(first.name, "台北孤城_V01")
            self.assertEqual(second.name, "台北孤城_V02")
            self.assertTrue((first / "PROJECT_STATE.json").is_file())
            self.assertTrue((first / "CHARACTER_PROFILE.json").is_file())
            state = json.loads((first / "PROJECT_STATE.json").read_text(encoding="utf-8"))
            self.assertEqual(state["current_gate"], 1)
            self.assertEqual(state["status"], "draft")

    def test_rejects_path_separators(self):
        with TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "project_name"):
                create_project(Path(tmp), "bad/name")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 執行測試並確認匯入失敗**

Run: `python -m unittest tests.test_init_project -v`  
Expected: FAIL，顯示 `scripts.init_project` 不存在。

- [ ] **Step 3: 實作 `create_project` 與 CLI**

實作必須：

```python
PROJECT_DIRS = (
    "01_inputs",
    "02_character_and_look",
    "03_story_and_script",
    "04_shot_design",
    "05_generation_prompts",
    "06_generated_assets",
    "07_sound_and_music",
    "08_edit_and_delivery",
    "09_reports_and_qc",
)

TEMPLATE_TARGETS = {
    "project-brief-template.md": "PROJECT_BRIEF.md",
    "production-bible-template.md": "PRODUCTION_BIBLE.md",
    "character-profile-template.json": "CHARACTER_PROFILE.json",
    "shot-production-table-template.md": "04_shot_design/SHOT_PRODUCTION_TABLE.md",
    "generation-report-template.md": "09_reports_and_qc/GENERATION_REPORT.md",
}
```

名稱驗證拒絕空字串、`.`、`..`、`/`、`\` 和 Windows 禁用字元。版本從 `_V01` 起尋找第一個不存在的目錄，以 `mkdir(exist_ok=False)` 建立。`PROJECT_STATE.json` 寫入 `schema_version="1.0"`、`project_name`、`project_version`、`current_gate=1`、`status="draft"`、`locked_artifacts=[]`、`open_decisions=[]`、`asset_status={}` 與 ISO 8601 `created_at`。

CLI：

```text
python scripts/init_project.py --root <projects-root> --name <project-name>
```

成功時只輸出新案件的絕對路徑；失敗時回傳非零 exit code 並保留既有目錄。

- [ ] **Step 4: 執行初始化測試與一次暫存目錄 smoke test**

Run: `python -m unittest tests.test_init_project -v`  
Expected: PASS。

Run: `python scripts/init_project.py --root "$env:TEMP\laoma-aigc-director-smoke" --name "測試短片"`  
Expected: 輸出以 `測試短片_V01` 或下一個可用版本結尾的絕對路徑。

- [ ] **Step 5: 提交初始化器**

```powershell
git add scripts/init_project.py tests/test_init_project.py
git commit -m "feat: add safe AIGC project initializer"
```

---

### Task 5: 實作 Gate 與專案結構驗證器

**Files:**
- Create: `scripts/validate_project.py`
- Create: `tests/test_validate_project.py`

**Interfaces:**
- Consumes: Task 4 建立的案件目錄與 `PROJECT_STATE.json`。
- Produces: `validate_project(project_dir: Path) -> list[str]`；空清單代表通過，字串清單提供可執行診斷。

- [ ] **Step 1: 寫入 Gate 驗證失敗測試**

```python
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from scripts.init_project import create_project
from scripts.validate_project import validate_project


class ValidateProjectTests(unittest.TestCase):
    def test_fresh_project_passes_gate_one_structure(self):
        with TemporaryDirectory() as tmp:
            project = create_project(Path(tmp), "測試片")
            self.assertEqual(validate_project(project), [])

    def test_gate_two_requires_locked_character_profile(self):
        with TemporaryDirectory() as tmp:
            project = create_project(Path(tmp), "測試片")
            state_path = project / "PROJECT_STATE.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["current_gate"] = 2
            state["status"] = "approved"
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
            errors = validate_project(project)
            self.assertIn("Gate 2 requires approved CHARACTER_PROFILE.json", errors)

    def test_missing_input_directory_is_reported(self):
        with TemporaryDirectory() as tmp:
            project = create_project(Path(tmp), "測試片")
            (project / "01_inputs").rmdir()
            self.assertIn("missing directory: 01_inputs", validate_project(project))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 執行測試並確認驗證器尚未存在**

Run: `python -m unittest tests.test_validate_project -v`  
Expected: FAIL，顯示 `scripts.validate_project` 不存在。

- [ ] **Step 3: 實作結構與 Gate 驗證**

`validate_project()` 按固定順序檢查：

```python
VALID_STATUSES = {"draft", "awaiting_approval", "approved", "blocked", "complete"}
REQUIRED_ROOT_FILES = (
    "PROJECT_STATE.json",
    "PROJECT_BRIEF.md",
    "PRODUCTION_BIBLE.md",
    "CHARACTER_PROFILE.json",
)
GATE_REQUIREMENTS = {
    1: ("PROJECT_BRIEF.md",),
    2: ("CHARACTER_PROFILE.json", "02_character_and_look"),
    3: ("03_story_and_script", "04_shot_design/SHOT_PRODUCTION_TABLE.md"),
    4: ("09_reports_and_qc/GENERATION_REPORT.md",),
}
```

驗證器先檢查精確 `schema_version="1.0"`、`VNN` 專案版本、目錄後綴、含時區 ISO 8601、Gate/status 矩陣與三個結構化集合。每個 `locked_artifacts` 物件至少含 `role/path/version/sha256/reason`；路徑解析後必須仍在案件內、檔案存在且重算 SHA-256 相符。

進入 Gate 2 要有 `project_brief` 鎖定；Gate 2 核准或進入 Gate 3 要有核准角色檔、Bible、`02_character_and_look/` 內非空可辨識的角色總覽圖與無角色場景圖，以及能由 MP4／MOV 容器驗證、宣告時長相符的實際 4–6 秒一致性測試鎖定證據；Gate 3 核准或進入 Gate 4 要鎖定故事／劇本、逐鏡表與生成方案。Gate 4 `complete` 要有正規化後仍位於 `06_generated_assets/` 的非空輸出、`asset_status.outputs` 匹配雜湊、已填寫且鎖定的 generation report、逐項通過 QC、結構化使用者核准、無未決項及 `claimed_complete_without_output=false`。不可用報告內固定文字、空白模板、job ID、口頭宣稱或自行宣告時長通過。

CLI：

```text
python scripts/validate_project.py <project-directory>
```

通過輸出 `PROJECT_VALID` 並回傳 0；失敗逐行輸出 `ERROR: <message>` 並回傳 1。

- [ ] **Step 4: 執行驗證器測試**

Run: `python -m unittest tests.test_validate_project -v`  
Expected: PASS。

- [ ] **Step 5: 提交驗證器**

```powershell
git add scripts/validate_project.py tests/test_validate_project.py
git commit -m "feat: validate production gates and project state"
```

---

### Task 6: 建立可重現的 Skill 安裝與雜湊比對

**Files:**
- Create: `scripts/sync_skill.py`
- Create: `tests/test_sync_skill.py`
- Modify: `references/project-state-and-versioning.md`

**Interfaces:**
- Consumes: 可攜式來源根目錄。
- Produces: `sync_skill(source: Path, destination_root: Path, replace: bool = False) -> Path`；安裝目錄內的 `.source-manifest.json`。

- [ ] **Step 1: 寫入同步安全測試**

```python
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from scripts.sync_skill import sync_skill


class SyncSkillTests(unittest.TestCase):
    def test_installs_runtime_files_and_manifest(self):
        source = Path(__file__).resolve().parents[1]
        with TemporaryDirectory() as tmp:
            installed = sync_skill(source, Path(tmp))
            self.assertTrue((installed / "SKILL.md").is_file())
            self.assertTrue((installed / "references" / "production-gates.md").is_file())
            self.assertFalse((installed / ".git").exists())
            self.assertFalse((installed / "tests").exists())
            manifest = json.loads((installed / ".source-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["skill"], "laoma-aigc-director")
            self.assertIn("SKILL.md", manifest["files"])

    def test_refuses_existing_install_without_replace(self):
        source = Path(__file__).resolve().parents[1]
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            sync_skill(source, root)
            with self.assertRaises(FileExistsError):
                sync_skill(source, root)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 執行測試並確認同步模組不存在**

Run: `python -m unittest tests.test_sync_skill -v`  
Expected: FAIL，顯示 `scripts.sync_skill` 不存在。

- [ ] **Step 3: 實作 staging、替換與 manifest**

只同步以下執行期路徑：

```python
RUNTIME_ENTRIES = ("SKILL.md", "agents", "references", "assets", "scripts")
SKILL_NAME = "laoma-aigc-director"
```

同步流程必須先複製到 `destination_root/.laoma-aigc-director.staging`，計算每個檔案的 SHA-256，寫入 `.source-manifest.json`，再改名為正式目錄。正式目錄已存在且 `replace=False` 時拋出 `FileExistsError`；`replace=True` 時先改名為同層的 `laoma-aigc-director.backup-YYYYMMDD-HHMMSS`，安裝成功後保留備份，不自動刪除。複製、manifest 或 promotion 失敗時清除本次建立的 staging；若 promotion 在備份改名後失敗，先把備份還原為正式安裝。來源與 destination、staging 任一方向重疊（包含來源直接位於 staging 內）時，在任何 mutation 前拒絕。

CLI：

```text
python scripts/sync_skill.py --source . --destination-root "C:\Users\pony6832\.codex\skills"
python scripts/sync_skill.py --source . --destination-root "C:\Users\pony6832\.codex\skills" --replace
```

- [ ] **Step 4: 執行同步測試**

Run: `python -m unittest tests.test_sync_skill -v`  
Expected: PASS，且暫存目錄未留下 staging 資料夾。

- [ ] **Step 5: 提交同步工具**

```powershell
git add scripts/sync_skill.py tests/test_sync_skill.py references/project-state-and-versioning.md
git commit -m "feat: add safe skill sync and source manifest"
```

---

### Task 7: 執行真實請求行為驗收

**Files:**
- Create: `tests/fixtures/scenarios.md`
- Create: `tests/fixtures/acceptance-contracts.json`
- Create: `tests/acceptance/`
- Create: `tests/acceptance_validator.py`
- Create: `tests/test_acceptance_validator.py`
- Create: `tests/test_scenario_coverage.py`
- Modify: `references/quality-and-recovery.md`

**Interfaces:**
- Consumes: 最終 `SKILL.md`、四個 Gate、版本化知識快照、工具路由和失敗回復規則。
- Produces: 七組由本次執行 Agent 實際建立的隔離 response／artifact bundles；每案含請求、結構化決策、實際檔案、雜湊、限制與完成證據，另由獨立 validator 檢查。

- [ ] **Step 1: 寫入案例與 bundle validator 的失敗測試**

```python
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ScenarioCoverageTests(unittest.TestCase):
    def test_seven_scenarios_cover_required_risks(self):
        text = (ROOT / "tests" / "fixtures" / "scenarios.md").read_text(encoding="utf-8")
        self.assertEqual(text.count("## Scenario "), 7)
        for phrase in (
            "一句故事點子",
            "一張虛構角色圖",
            "已核准角色圖",
            "只改一顆失敗鏡頭",
            "生成入口不明",
            "真人肖像或聲音授權不明",
            "工具不可用",
            "禁止行為",
            "完成證據",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 執行測試並確認 validator／bundle 尚未存在而失敗**

Run: `python -m unittest tests.test_scenario_coverage tests.test_acceptance_validator -v`
Expected: FAIL，指出結構化 contract、validator 或 bundle 尚未存在。

- [ ] **Step 3: 定義七案結構化不變量**

每個案例固定包含：

```markdown
## Scenario 1｜一句故事點子

### 使用者請求
### 預期模式與當前 Gate
### 必要產物
### 禁止行為
### 完成證據
```

七案依序使用：一句故事點子、一張虛構角色圖、已核准角色圖、只改一顆失敗鏡頭、生成入口不明、真人肖像或聲音授權不明、工具不可用。`acceptance-contracts.json` 逐案指定模式、Gate、status、必要 artifact roles、必要結構化 facts、禁止 action／flag 與 completion evidence；禁止行為至少覆蓋偷用舊角色、跳過 Gate 3 直接大量生成、混用平台參數、覆蓋舊版、未生成卻聲稱成片。

- [ ] **Step 4: 本次執行 Agent 讀取最終 runtime 並建立七組隔離 bundle**

每組至少含原請求、Agent response、`decision.json`、`project-state.json` 與一個以上 Gate 對應產物。產物 manifest 使用安全相對路徑與 SHA-256；`decision.json` 結構化記錄 mode、Gate、status、actions、facts、forbidden flags、completion evidence、claims 與 limitations。Validator 必須交叉檢查 state 的 schema、Gate/status、前置 Gate 鎖定角色／雜湊及回覆中的明確完成聲明。缺少真實案件 state／鎖定證據時，只能保留誠實的實際 Gate 並阻擋推進，即使仍可交付目標 Gate 的製作包。這是實際 Agent 判斷與文件交付練習，不是固定 phrase fixture，不呼叫付費影片平台，也不偽造影片輸出。

- [ ] **Step 5: 獨立驗證七組 bundle**

Run: `python tests/acceptance_validator.py --contracts tests/fixtures/acceptance-contracts.json --results tests/acceptance`
Expected: `ACCEPTANCE_VALID: 7 scenarios`。Validator 檢查模式、Gate、status、必要 roles、實際檔案、非空內容、SHA-256、必要 facts、禁止行為、claims、limitations、completion evidence，以及 `project-state.json` 與前置 Gate 鎖定不變量；並拒絕回覆中與 false 完成聲明矛盾的明確機器標記，不要求固定回覆措辭或聲稱能判斷任意自然語言語意。

- [ ] **Step 6: 執行案例覆蓋與 focused tests**

Run: `python -m unittest discover -s tests -v`  
Expected: 所有測試 PASS。

- [ ] **Step 7: 提交行為案例與驗證器**

```powershell
git add tests/fixtures tests/acceptance tests/acceptance_validator.py tests/test_acceptance_validator.py tests/test_scenario_coverage.py references/quality-and-recovery.md
git commit -m "test: execute AIGC director acceptance scenarios"
```

---

### Task 8: 完整驗證、正式替換安裝與新版 Smoke Project

**Files:**
- Create: `docs/verification/2026-09-02-v1-verification.md`
- Create outside repository: `C:\Users\pony6832\.codex\skills\laoma-aigc-director\`
- Preserve outside repository: `C:\Users\pony6832\Documents\Codex\Codex專案分類\08 - AIGC影像生成相關\老馬AIGC導演專案\V1_驗收短片_V01\`
- Create outside repository: 初始化器回傳的下一個 `V1_驗收短片_VNN`（不得覆蓋 V01）

**Interfaces:**
- Consumes: Tasks 1–7 的可攜式來源、測試、初始化器、驗證器與同步器。
- Produces: 已驗證的正式 Skill 安裝副本、第一個可檢查案件骨架、可追蹤驗證報告。

- [ ] **Step 1: 執行完整靜態與單元驗證**

Run: `python -m unittest discover -s tests -v`  
Expected: 全部 PASS，無 skipped 或 error。

Run: `python "C:\Users\pony6832\.codex\skills\.system\skill-creator\scripts\quick_validate.py" .`  
Expected: Skill 驗證成功。

Run: `git diff --check`  
Expected: 無輸出且 exit code 0。

Run: `rg -n "T[B]D|T[O]DO|FIX[M]E|claimed complete|已經成片" SKILL.md agents references assets scripts tests`  
Expected: 沒有 placeholder；若測試案例刻意包含禁止用語，驗證報告需註明其位置與用途。

- [ ] **Step 2: 安裝正式 Skill 副本**

Run: `python scripts/sync_skill.py --source . --destination-root "C:\Users\pony6832\.codex\skills" --replace`
Expected: 以安全 staging 更新 `C:\Users\pony6832\.codex\skills\laoma-aigc-director`，並保留本次替換前的 `laoma-aigc-director.backup-YYYYMMDD-HHMMSS`；不得刪除任何既有備份。

- [ ] **Step 3: 驗證安裝副本**

Run: `python "C:\Users\pony6832\.codex\skills\.system\skill-creator\scripts\quick_validate.py" "C:\Users\pony6832\.codex\skills\laoma-aigc-director"`  
Expected: 安裝副本驗證成功。

Run: `python -c "import json,pathlib; p=pathlib.Path(r'C:\Users\pony6832\.codex\skills\laoma-aigc-director\.source-manifest.json'); d=json.loads(p.read_text(encoding='utf-8')); print(d['skill'], len(d['files']))"`  
Expected: 第一欄為 `laoma-aigc-director`，檔案數大於 10。

另外逐一重算 manifest 內所有安裝檔案的 SHA-256，要求 missing=0、mismatch=0，並確認本次 retained backup 仍存在且含 `SKILL.md`。

- [ ] **Step 4: 保留 V01，建立並驗證下一個 Smoke Project**

Run: `python scripts/init_project.py --root "C:\Users\pony6832\Documents\Codex\Codex專案分類\08 - AIGC影像生成相關\老馬AIGC導演專案" --name "V1_驗收短片"`  
Expected: 保留既有 `_V01`，建立下一個可用版本並輸出絕對路徑。

Run: `python scripts/validate_project.py "<INITIALIZER_ACTUAL_OUTPUT_PATH>"`
Expected: `PROJECT_VALID`，且 `_V01` 仍存在、原有內容未被初始化器覆蓋。

- [ ] **Step 5: 寫入可追蹤驗證報告**

`docs/verification/2026-09-02-v1-verification.md` 記錄：

```markdown
# 老馬 AIGC 導演 V1 驗證報告

- 被驗證 commit：每次驗證前的 `git rev-parse HEAD`
- 報告／修復 commit：寫入報告後另列；除非在該精確 head 重跑，不把它描述為已驗證 head
- Python：`python --version`
- 單元測試：通過數、失敗數、跳過數
- Skill validator：可攜式來源與正式安裝副本的結果
- 安裝 manifest：路徑、檔案數及 `SKILL.md` SHA-256
- Smoke Project：實際建立路徑與 `PROJECT_VALID` 結果
- 驗證限制：尚未以付費第三方平台執行實際影片生成；不得把靜態驗證描述為成片驗證
```

- [ ] **Step 6: 提交報告，取得 final head 後重跑一次完整 suite 與靜態驗證**

```powershell
git add docs/verification/2026-09-02-v1-verification.md
git commit -m "chore: verify and install AIGC director V1"
python -m unittest discover -s tests -v
git status --short --branch
```

Expected: final committed head 的完整測試通過，`## feature/laoma-aigc-director-v1` 沒有未提交檔案；驗證報告清楚區分先前驗證 commit 與 final report commit。完成整體審查後再決定是否合併到 `main`。
