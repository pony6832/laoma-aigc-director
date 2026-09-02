# 案件狀態與版本

## PROJECT_STATE schema

`PROJECT_STATE.json` 必須至少包含：

```json
{
  "schema_version": "1.0",
  "project_name": "string",
  "project_version": "V01",
  "current_gate": 1,
  "status": "draft|awaiting_approval|approved|blocked|complete",
  "locked_artifacts": [],
  "open_decisions": [],
  "asset_status": {},
  "created_at": "ISO 8601 timestamp"
}
```

狀態值為 `draft`、`awaiting_approval`、`approved`、`blocked`、`complete`。只有核准者可將等待核准的產物推進為 `approved`；無法安全繼續時使用 `blocked` 並記錄原因。

## 版本與鎖定

- 案件目錄從 `_V01` 起跳，例如 `台北孤城_V01`。
- 新版遞增版號，不覆蓋舊版。
- 鎖定產物使用 SHA-256，並把檔名、雜湊與鎖定原因記入 `locked_artifacts`。
- 修改鎖定產物前，先建立新版本並重新驗收。

## 可重現 Skill 安裝

在可攜式來源根目錄執行以下命令，先建立暫存副本、寫入每個執行期檔案的 SHA-256，最後才將其改名為安裝目錄：

```powershell
python scripts/sync_skill.py --source . --destination-root "C:\Users\pony6832\.codex\skills"
```

工具只同步 `SKILL.md`、`agents`、`references`、`assets` 與 `scripts`；不會同步 `.git`、`tests` 或 `docs`。安裝後的 `.source-manifest.json` 可用於檔案完整性比對。若目的目錄已存在，預設會拒絕覆寫。明確加入 `--replace` 時，既有安裝會先保留為 `laoma-aigc-director.backup-YYYYMMDD-HHMMSS`，且不會被工具自動刪除：

```powershell
python scripts/sync_skill.py --source . --destination-root "C:\Users\pony6832\.codex\skills" --replace
```
