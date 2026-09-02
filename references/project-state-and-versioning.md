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
