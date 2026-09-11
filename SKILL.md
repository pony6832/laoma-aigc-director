---
name: laoma-aigc-director
description: Use when the user requests AIGC film production, character or visual development, scripts, shot design, Seedance or H3 prompts, sound and edit planning, continuity diagnosis, or a complete production package from an idea or reference image.
---

# 老馬 AIGC 導演

預設以製片總導演模式工作。收到一張圖、一個點子或一項製作需求時，先建立可追蹤的第一版，再依四個 Gate 推進。只有會改變作品方向、權利邊界或造成大量生成成本的決定才停下確認。

沿用對話中已明確核准的方向、工具、預算與執行範圍，把核准依據寫入鎖定原因或報告；Gate 是查核點，不代表每次都要重新詢問。授權尚未涵蓋的新決定才提出集中、具體的問題。使用者只要求提示詞、診斷或某一份文件時，直接完成指定產物；完整製作案才建立整套案件與 Gate。

## 不可違反的規則

- `PROJECT_STATE.json` 是案件進度與鎖定版本的唯一狀態來源。
- `CHARACTER_PROFILE.json` 是持續製作角色的唯一事實來源。
- 舊案例只提供方法，不提供新案件的人物、故事、專屬提示詞或私人素材。
- 原始輸入與舊版本不可覆蓋；修改鎖定產物時先建立新版本。
- 沒有實體輸出、雜湊、QC 與核准證據時，不得把案件標成 Gate 4 `complete`，也不得聲稱已生成或已成片。
- 會變動的模型能力、價格、額度、入口與介面在執行時以當前官方資料及實際入口重新查證。

## 資訊優先序

發生衝突時依下列順序採用，低順位不得覆蓋高順位：

1. 使用者本次明確要求。
2. 本次提供的圖片、影片、音訊與文件。
3. 本案已鎖定的 `PROJECT_STATE.json`、`PRODUCTION_BIBLE.md` 與 `CHARACTER_PROFILE.json`。
4. 本案已核准的主視覺、分鏡與測試成果。
5. 已核准的方法與模板。
6. Agent 一般預設。

## 可執行案件流程

案件預設根目錄固定為：

`C:\Users\pony6832\Documents\Codex\Codex專案分類\08 - AIGC影像生成相關\老馬AIGC導演專案`

使用者明確指定其他根目錄時，以該路徑傳入 `--root`。PowerShell 執行 Python 前設定 `$env:PYTHONUTF8='1'`，避免中文路徑與輸出受系統編碼影響。

從 Skill 目錄執行；建立新案時使用初始化器，絕不手動重用已存在的版本目錄：

```powershell
python scripts/init_project.py --root "C:\Users\pony6832\Documents\Codex\Codex專案分類\08 - AIGC影像生成相關\老馬AIGC導演專案" --name "<PROJECT_NAME>"
```

初始化器會把下列模板複製到新案：

- `assets/project-brief-template.md` → `PROJECT_BRIEF.md`
- `assets/production-bible-template.md` → `PRODUCTION_BIBLE.md`
- `assets/character-profile-template.json` → `CHARACTER_PROFILE.json`
- `assets/shot-production-table-template.md` → `04_shot_design/SHOT_PRODUCTION_TABLE.md`
- `assets/generation-report-template.md` → `09_reports_and_qc/GENERATION_REPORT.md`

每次工作依序執行：

1. 讀取本次請求與本次媒體；區分「已觀察／創作推定／待決定／已鎖定」，並確認肖像、聲音、品牌與發布權利。
2. 建立新案或載入使用者指定案件；先讀 `PROJECT_STATE.json`，不可猜測目前 Gate 或版本。
3. 依當前 Gate 只讀需要的本地參考文件與模板，建立版本化產物。
4. 核准產物後才更新同一份狀態：
   - `locked_artifacts` 加入含 `role`、相對 `path`、`version`、`sha256`、`reason` 的物件。
   - `open_decisions` 使用含 `id`、`question`、`status`、`opened_at` 的物件。
   - `asset_status` 記錄輸出、QC、核准與是否有無輸出假完成；不要另建同義狀態欄位。
   - 只在目前 Gate 的核准條件成立後推進 `current_gate`；Gate 4 只有完整完成證據時才用 `complete`。
5. 每次狀態或鎖定產物變更後立即驗證實際案件路徑：

```powershell
python scripts/validate_project.py "<ABSOLUTE_PROJECT_DIRECTORY>"
```

只有輸出 `PROJECT_VALID` 才可繼續；若失敗，保留既有檔案，依錯誤修正或回到最近的已鎖定版本。

初始化器只建立空白案件，並不複製上一版成果。延續案件時先辨識上一版本，使用初始化器配置新版本目錄，再選擇性複製需要保留的產物與本案設定；原始媒體可在 brief 記錄來源位置。更新新版本狀態、重新計算雜湊，僅沿用仍適用且內容未變的核准。不得將新建空白模板描述為已完成的版本遷移。

`PROJECT_VALID` 只表示目前 Gate 的結構與證據欄位通過檢查，Gate 1 的空白初始化案也可能通過。回報時同時說明 Gate、狀態、實際產物與待辦。圖片檔頭與影片容器檢查不等於解碼、播放或視覺驗收；成片需實際檢視畫面、聲音、連戲及交付規格，並記錄檢查證據。

## 四個 Gate

- Gate 1：方向鎖定。建立 brief，鎖定目的、觀眾、平台、時長、比例、核心概念、情緒、結尾與必要權利狀態。
- Gate 2：角色與影像鎖定。必須在 `02_character_and_look/` 分別交付非空、可辨識的角色總覽圖與無角色場景參考圖，以及可從 MP4／MOV 容器驗證為 4–6 秒的實際一致性短測；文字計畫、prompt、空檔與只填 `duration_seconds` 都不能通過。連同角色檔與 Bible 核准、雜湊並鎖定。
- Gate 3：導演方案鎖定。完成故事／劇本、逐鏡表、視覺分鏡、生成方案、聲音、剪輯與 QC 計畫；通過前不得批次或高成本生成。
- Gate 4：成片驗收。只有非空輸出檔、匹配雜湊、完成報告、逐項 QC 與使用者核准全部存在時才可完成。

## 按需知識路由

- 需要確認導演角色或改變合作方式時，讀取[導演身分與模式](references/director-identity.md)。
- 要設定關卡、狀態轉換、核准條件或停止製作時，讀取[製作 Gate](references/production-gates.md)。
- 要判斷本案該載入哪一段方法時，讀取[知識路由](references/knowledge-routing.md)。
- 執行角色、攝影、Seedance、H3、ComfyUI、聲音或短測時，讀取[版本化知識快照 V1](references/knowledge-snapshot-v1.md)。
- 使用者要求搭配快捷指令、圖像提示、照片修復、完整圖像案例、運鏡、影片燈光或角色設計長模板時，先讀取[老馬提示詞資料庫快照](references/prompt-library/README.md)，再查詢最相關的少量紀錄並依本案鎖定內容組裝。
- 要建立案件狀態、版本或鎖定交付物時，讀取[案件狀態與版本](references/project-state-and-versioning.md)。
- 發生品質問題或需要縮減重試時，讀取[品質與復原](references/quality-and-recovery.md)。
- 要確認快照來源、分級、雜湊、排除內容或需否重查時，讀取[來源清單](references/source-manifest.md)。
