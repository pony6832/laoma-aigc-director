# 老馬 AIGC 導演 V1 驗證報告

- 驗證日期：2026-09-02（Asia/Taipei）
- 分支：`feature/laoma-aigc-director-v1`
- 部署前被驗證 commit：`816daf17b037c63a196b92edc4ed7e4b5dcbe962`
- 證據標籤：下列 source tests、acceptance、安裝與 smoke 證據都在上述 commit 執行。寫入本報告的後續 commit 不自動等同已驗證 commit；提交報告後，必須在精確 final HEAD 重跑完整 suite，該 final HEAD 與結果另記於 `.superpowers/sdd/2026-09-02-laoma-aigc-director-v1/final-fix-report.md`。
- Python：`Python 3.11.15`

## Source tests 與靜態檢查

命令：

```powershell
$env:PYTHONUTF8='1'; python -m unittest discover -s tests -v
```

結果：`Ran 55 tests in 1.339s`、`OK`；通過 55、失敗 0、錯誤 0、跳過 0。涵蓋 project state／Gate completion、鎖定檔與雜湊、safe sync fault injection、source-inside-staging、runtime／snapshot 契約及七案驗收。

命令：

```powershell
$env:PYTHONUTF8='1'; python tests/acceptance_validator.py --contracts tests/fixtures/acceptance-contracts.json --results tests/acceptance
```

結果：`ACCEPTANCE_VALID: 7 scenarios`。七個 bundle 均由本次執行 Agent 依 `director-methods-v1.0.0` 建立；validator 驗證 mode、Gate、status、必要 roles、非空檔案、安全相對路徑、SHA-256、facts、禁止行為、claims、limitations 與 completion evidence，不比對固定措辭。

命令：

```powershell
$env:PYTHONUTF8='1'; python "C:\Users\pony6832\.codex\skills\.system\skill-creator\scripts\quick_validate.py" .
```

結果：`Skill is valid!`

命令：

```powershell
git diff --check
rg -n "T[B]D|T[O]DO|FIX[M]E|claimed complete|已經成片" SKILL.md agents references assets scripts tests
```

結果：`git diff --check` 無輸出、exit code 0；掃描無匹配、exit code 1，記錄為 `PLACEHOLDER_SCAN_CLEAN`。

## Safe replace 與備份保留

安裝前唯讀盤點確認正式目錄存在，且 smoke `V1_驗收短片_V01` 存在。替換命令：

```powershell
$env:PYTHONUTF8='1'; python scripts/sync_skill.py --source . --destination-root "C:\Users\pony6832\.codex\skills" --replace
```

輸出：

```text
C:\Users\pony6832\.codex\skills\laoma-aigc-director
```

本次 retained backup：`C:\Users\pony6832\.codex\skills\laoma-aigc-director.backup-20260902-194403`。備份 manifest 重算命令使用與下節相同的 Python 標準函式庫邏輯，結果：

```text
backup=laoma-aigc-director.backup-20260902-194403 files=17 missing=0 mismatch=0
backup_SKILL.md_sha256=bf0a8f866dbb3a7025a737be71c57b0fead51b64bb3c1c28b5254e73daca2ff6
```

本次 staging 檢查：`staging_exists=False`。成功替換後沒有刪除 retained backup。

## 已安裝副本與 manifest

命令：

```powershell
$env:PYTHONUTF8='1'; python "C:\Users\pony6832\.codex\skills\.system\skill-creator\scripts\quick_validate.py" "C:\Users\pony6832\.codex\skills\laoma-aigc-director"
```

結果：`Skill is valid!`

逐檔重算命令：

```powershell
python -c 'import hashlib,json,pathlib; r=pathlib.Path(r"C:\Users\pony6832\.codex\skills\laoma-aigc-director"); d=json.loads((r/".source-manifest.json").read_text(encoding="utf-8")); missing=[p for p in d["files"] if not (r/p).is_file()]; mismatch=[p for p,h in d["files"].items() if (r/p).is_file() and hashlib.sha256((r/p).read_bytes()).hexdigest()!=h]; print("skill={} files={} missing={} mismatch={}".format(d["skill"],len(d["files"]),len(missing),len(mismatch))); print("SKILL.md_sha256={}".format(d["files"]["SKILL.md"]))'
```

輸出：

```text
skill=laoma-aigc-director files=18 missing=0 mismatch=0
SKILL.md_sha256=48a8833eebd9211304e6f1b15b6e378566be476f112114e22ac9e9420b42c200
```

manifest 路徑：`C:\Users\pony6832\.codex\skills\laoma-aigc-director\.source-manifest.json`。

## 新版 Smoke Project 與 V01 保存證據

使用已安裝 initializer：

```powershell
python "C:\Users\pony6832\.codex\skills\laoma-aigc-director\scripts\init_project.py" --root "C:\Users\pony6832\Documents\Codex\Codex專案分類\08 - AIGC影像生成相關\老馬AIGC導演專案" --name "V1_驗收短片"
```

輸出：

```text
C:\Users\pony6832\Documents\Codex\Codex專案分類\08 - AIGC影像生成相關\老馬AIGC導演專案\V1_驗收短片_V02
```

使用已安裝 validator：

```powershell
python "C:\Users\pony6832\.codex\skills\laoma-aigc-director\scripts\validate_project.py" "C:\Users\pony6832\Documents\Codex\Codex專案分類\08 - AIGC影像生成相關\老馬AIGC導演專案\V1_驗收短片_V02"
```

結果：`PROJECT_VALID`。

V01 在初始化前後都存在且有 6 個檔案。以「相對路徑 + 每檔 SHA-256」排序串接後再算 SHA-256，前後皆為：

```text
17cdbda28e838bfdb3d09bf601d7442760b802433d8f81790a267813a2d72607
```

結果：`V01_PRESERVED=True`。initializer 建立 V02，沒有覆寫 V01。

## 驗證限制

本次完成標準函式庫程式、狀態／檔案完整性、skill 結構、七案文件行為、safe replace、manifest 與案件骨架驗證。沒有連接或付費呼叫第三方影像／影片生成平台，沒有生成、剪輯、播放或驗收任何實際成片。七案 validator 對已提交 bundle 的結構不變量具有決定性，但不代表不同模型或未來 Agent 回覆具有模型無關的決定性，也不代表真實影片已生成。
