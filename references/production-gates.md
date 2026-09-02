# 製作 Gate

`current_gate` 表示正在工作的 Gate，`status` 表示該 Gate 的狀態。推進 Gate 前，先鎖定上一 Gate 的產物；不得用 `complete` 代替逐關核准。

## Gate／status 矩陣

| current_gate | 允許 status | 意義 |
|---:|---|---|
| 1 | `draft`、`awaiting_approval`、`approved`、`blocked` | 方向提案、等待、核准或因目標／權利阻擋 |
| 2 | `draft`、`awaiting_approval`、`approved`、`blocked` | 角色與影像開發、等待、核准或阻擋 |
| 3 | `draft`、`awaiting_approval`、`approved`、`blocked` | 導演方案開發、等待、核准或阻擋 |
| 4 | `draft`、`awaiting_approval`、`blocked`、`complete` | 生成／後製、等待成片核准、阻擋或完成 |

Gate 1–3 不可使用 `complete`；Gate 4 不使用 `approved`，因為實體輸出、QC 與核准完整後直接記為 `complete`。阻擋時把具體問題寫入結構化 `open_decisions`，不得虛構上一 Gate 已通過。

## Gate 1：方向鎖定

- 輸入：本次創作需求、本次媒體、受眾、發布平台與限制。
- 最低產物：`PROJECT_BRIEF.md`，包含目的、訊息、受眾、平台、時長、比例、情緒曲線、結尾、成本／時程假設與權利狀態。
- 通過條件：使用者核准方向與限制，並以 `project_brief` 角色將 brief 的版本、SHA-256 與鎖定原因寫入 `locked_artifacts`。
- 停止條件：作品目的、重要權利或會改變方向／成本的決定不明。

進入 Gate 2 代表 Gate 1 已核准；驗證器會要求 `project_brief` 鎖定證據。

## Gate 2：角色與影像鎖定

- 輸入：已鎖定 brief、角色／產品參考與視覺方向。
- 最低產物：
  - 核准的 `CHARACTER_PROFILE.json`。
  - `PRODUCTION_BIBLE.md`。
  - 一張角色總覽板，角色、服裝、道具與外觀錨點清楚。
  - 一張無角色場景參考板，只鎖定空間、光線、材質、色彩與環境狀態。
  - 一個 4–6 秒一致性短測；長片、多人或高一致性角色不可略過。
- 通過條件：身分、定裝、場景、視覺基準與短測可驗證；以上六個角色 `production_bible`、`character_profile`、`character_overview_board`、`character_free_scene_board`、`consistency_test`（連同上一 Gate 的 `project_brief`）全部以檔案雜湊鎖定。短測另記 `duration_seconds`，必須介於 4 與 6。
- 停止條件：參考權利不明、事實衝突，或短測未通過。

進入 Gate 3 代表 Gate 2 已核准；不得拿角色圖代替場景板，也不得拿提示詞或測試計畫代替實際短測輸出。

## Gate 3：導演方案鎖定

- 輸入：Gate 2 的全部鎖定產物。
- 最低產物：完整故事／劇本、視覺分鏡、逐鏡表、生成方案、聲音設計、剪輯節奏與 QC 計畫。
- 通過條件：每個鏡頭都有敘事用途、走位、構圖焦點、運鏡、節奏、連續性、可執行輸入、聲音與驗收點；至少把 `story_script`、`shot_production_table`、`generation_plan` 三個角色以 SHA-256 鎖定。
- 停止條件：敘事、鏡頭、生成入口或成本尚未核准。

Gate 3 通過前不得進入批次或高成本生成。只修失敗鏡頭時，保留其他鏡頭雜湊，只新增失敗鏡頭版本。

## Gate 4：成片驗收

- 輸入：Gate 3 的鎖定方案、實際生成鏡頭、聲音與後製版本。
- 最低產物：
  - `06_generated_assets/` 內至少一個實際存在且非空的輸出檔。
  - `asset_status.outputs` 中每個輸出的相對路徑、版本、種類與匹配 SHA-256。
  - 已填寫且不等於原始空白模板的 `GENERATION_REPORT.md`，並以 `generation_report` 角色鎖定。
  - `asset_status.qc` 中非空檢查清單；每項為 `passed` 且有證據、檢查者與含時區時間。
  - `asset_status.approval` 中使用者核准者、含時區時間與非空核准範圍。
  - `claimed_complete_without_output=false`，且沒有未決 `open_decisions`。
- 通過條件：輸出檔、雜湊、報告、QC 與核准全部通過 `scripts/validate_project.py`。
- 停止條件：缺少實體輸出、雜湊不符、任何 QC 未通過、輸出規格不符、權利阻擋或核准被撤回。

工具不可操作時可以交付完整可執行生成／剪輯包，但案件停在 Gate 3 或 Gate 4 `blocked`，不可標為 `complete`。

## 更新與驗證

每次 Gate 變更都先寫出新版產物、計算 SHA-256、更新同一份 `PROJECT_STATE.json`，最後執行：

```powershell
python scripts/validate_project.py "<ABSOLUTE_PROJECT_DIRECTORY>"
```

只有 `PROJECT_VALID` 才能繼續。驗證失敗不刪檔、不覆蓋鎖定版本，依診斷回復或阻擋。
