# 案件狀態與版本

## 唯一狀態來源

`PROJECT_STATE.json` 是案件進度與鎖定版本的唯一狀態來源。V1 唯一支援的 `schema_version` 是 `1.0`；不可建立 `project_id`、`current_version`、`locked_files` 等同義欄位。

初始化器建立的合法空白狀態如下：

```json
{
  "schema_version": "1.0",
  "project_name": "string",
  "project_version": "V01",
  "current_gate": 1,
  "status": "draft",
  "locked_artifacts": [],
  "open_decisions": [],
  "asset_status": {
    "claimed_complete_without_output": false,
    "outputs": [],
    "qc": {
      "status": "not_started",
      "checked_at": null,
      "checked_by": "",
      "checks": []
    },
    "approval": {
      "status": "not_requested",
      "approved_at": null,
      "approved_by": "",
      "scope": []
    }
  },
  "created_at": "2026-09-02T08:00:00+08:00"
}
```

## 版本與時間契約

- `project_version` 使用大寫 `V` 加至少兩位數字，例如 `V01`、`V12`。
- 案件資料夾名稱必須精確為 `<project_name>_<project_version>`；狀態與目錄後綴不一致即失敗。
- 產物版本使用小寫 `v` 加至少兩位數字，例如 `v01`。
- `created_at`、QC 與核准時間都使用含時區的 ISO 8601；不接受無時區時間。
- 新案與新版遞增版號，不覆蓋舊資料夾或舊產物。

## locked_artifacts

每一項都是物件，至少含下列欄位；所有 `path` 都是案件根目錄內的相對路徑，使用者提供的絕對路徑、`..` 越界、遺失檔與雜湊不符都必須拒絕。

```json
{
  "role": "character_profile",
  "path": "CHARACTER_PROFILE.json",
  "version": "v01",
  "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
  "reason": "Gate 2 使用者核准角色外觀與不可變欄位"
}
```

角色 `role` 用於 Gate 驗證，不是另一份狀態來源。固定角色包括：

- Gate 1：`project_brief`。
- Gate 2：`production_bible`、`character_profile`、`character_overview_board`、`character_free_scene_board`、`consistency_test`。兩張 board 必須是 `02_character_and_look/` 內非空、可辨識的圖像；短測必須是該目錄內非空 MP4／MOV，另加與容器實際時長相符且介於 4–6 的 `duration_seconds`。文字計畫、空檔或只填宣告時長不可代替這些媒體。
- Gate 3：`story_script`、`shot_production_table`、`generation_plan`。
- Gate 4：`generation_report`。

鎖定時先確認檔案存在，再以檔案位元組計算 SHA-256。任何後續修改都使舊雜湊失效；先另存新版、重新核准，再以新物件取代目前鎖定角色，舊檔仍保留。

## open_decisions

每項未決問題都使用可追蹤物件：

```json
{
  "id": "D001",
  "question": "使用 Seedance 還是已核准的本機入口？",
  "status": "open",
  "opened_at": "2026-09-02T08:10:00+08:00"
}
```

`status` 只用 `open` 或 `resolved`。完成案件不得仍有未決項；需要保留歷史時把已解決紀錄移入版本化報告，不建立第二個狀態陣列。

## asset_status

`asset_status` 保存 Gate 4 的可機器驗證證據：

```json
{
  "claimed_complete_without_output": false,
  "outputs": [
    {
      "path": "06_generated_assets/final_v01.mp4",
      "version": "v01",
      "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
      "kind": "video"
    }
  ],
  "qc": {
    "status": "passed",
    "checked_at": "2026-09-02T12:00:00+08:00",
    "checked_by": "reviewer-name",
    "checks": [
      {
        "name": "playable_output",
        "status": "passed",
        "evidence": "本機播放與技術檢查紀錄路徑"
      }
    ]
  },
  "approval": {
    "status": "approved",
    "approved_at": "2026-09-02T12:05:00+08:00",
    "approved_by": "project-owner",
    "scope": ["final_v01.mp4"]
  }
}
```

- `outputs` 的路徑正規化後必須仍指向 `06_generated_assets/` 內非空檔案並重算匹配 SHA-256；拒絕絕對路徑與 `..` 逃逸。
- QC `status` 可為 `not_started|pending|passed|failed`；每項 check 為 `pending|passed|failed`。
- approval `status` 可為 `not_requested|pending|approved|rejected`。
- Gate 4 `complete` 只接受 QC 全部通過、核准完成、有非空 scope、無未決項及 `claimed_complete_without_output=false`。

## Gate 更新順序

1. 讀取目前狀態與所有鎖定檔案，先執行一次驗證。
2. 建立新版本產物，不原地修改鎖定檔。
3. 取得使用者核准或記錄明確阻擋。
4. 計算 SHA-256，更新 `locked_artifacts`、`open_decisions`、`asset_status`、`status` 與 `current_gate`。
5. 執行 `python scripts/validate_project.py "<ABSOLUTE_PROJECT_DIRECTORY>"`；失敗時不前進 Gate。

## 可重現 Skill 安裝

在可攜式來源根目錄執行：

```powershell
python scripts/sync_skill.py --source . --destination-root "C:\Users\pony6832\.codex\skills"
```

工具只同步 `SKILL.md`、`agents`、`references`、`assets` 與 `scripts`；不同步 `.git`、`tests` 或 `docs`。安裝後的 `.source-manifest.json` 記錄每個執行期檔案的 SHA-256。

若目的目錄已存在，預設拒絕覆寫。明確加入 `--replace` 時，先在 staging 完成複製與 manifest，再把既有安裝改名成時間戳備份並推進新版本：

```powershell
python scripts/sync_skill.py --source . --destination-root "C:\Users\pony6832\.codex\skills" --replace
```

本次執行在複製、manifest 或推進失敗時會清除自己建立的 staging；若既有安裝已改名而新版本推進失敗，會先把備份還原成正式安裝。成功替換後則永久保留時間戳備份，不自動刪除。
