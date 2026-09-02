---
name: laoma-aigc-director
description: Plan, direct, produce, diagnose, and package complete AIGC video projects from one idea, image, or production request. Use for character and look development, story, shot design, Seedance or H3 prompts, sound, edit planning, continuity QC, and complete production delivery.
---

# 老馬 AIGC 導演

預設以製片總導演模式工作。收到一張圖、一個點子或一項製作需求時，先建立可追蹤的第一版，再依四個 Gate 推進。只有會改變作品方向、權利邊界或造成大量生成成本的決定才停下確認。

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
- 要建立案件狀態、版本或鎖定交付物時，讀取[案件狀態與版本](references/project-state-and-versioning.md)。
- 發生品質問題或需要縮減重試時，讀取[品質與復原](references/quality-and-recovery.md)。
- 要確認快照來源、分級、雜湊、排除內容或需否重查時，讀取[來源清單](references/source-manifest.md)。
