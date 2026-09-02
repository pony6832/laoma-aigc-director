# 老馬 AIGC 導演 V1 驗證報告

- 驗證日期：2026-09-02（Asia/Taipei）
- 分支：`feature/laoma-aigc-director-v1`
- 最新部署時被檢出的 commit：`5c4afe8e8975e4657e82c47fedf9bb6c856685b2`
- 證據標籤：下列第二次 source／acceptance 驗證、正式 replace、manifest 與 V03 smoke 對應 `5c4afe8`。寫入本報告的後續 commit 不自動等同已驗證 commit；精確 final HEAD 的完整 suite 與靜態檢查另記於 `.superpowers/sdd/2026-09-02-laoma-aigc-director-v1/final-fix-report.md`。
- Python：`Python 3.11.15`

## Source tests 與靜態檢查

提交 `5c4afe8` 前，在同一份索引內容執行：

```powershell
$env:PYTHONUTF8='1'; python -m unittest discover -s tests -v
```

結果：`Ran 65 tests in 1.669s`、`OK`；通過 65、失敗 0、錯誤 0、跳過 0。新增負例覆蓋 Gate 4 正規化路徑逃逸、Gate 2 空檔／文字假媒體／無效容器／宣告時長不符，以及七案 state、前置 Gate locks 與回覆完成聲明矛盾。

聚焦命令：

```powershell
$env:PYTHONUTF8='1'; python -m unittest tests.test_validate_project tests.test_acceptance_validator tests.test_scenario_coverage -v
```

結果：`Ran 43 tests in 1.085s`、`OK`。

七案獨立 validator：

```powershell
$env:PYTHONUTF8='1'; python tests/acceptance_validator.py --contracts tests/fixtures/acceptance-contracts.json --results tests/acceptance
```

結果：`ACCEPTANCE_VALID: 7 scenarios`。Validator 檢查 mode、Gate、status、必要 roles、實際檔案、安全相對路徑、SHA-256、facts、禁止行為、claims、limitations、completion evidence，並交叉檢查 `project-state.json` 與前置 Gate lock 不變量。

portable source validator 與 placeholder 掃描：

```powershell
$env:PYTHONUTF8='1'; python "C:\Users\pony6832\.codex\skills\.system\skill-creator\scripts\quick_validate.py" .
git diff --check
rg -n "T[B]D|T[O]DO|FIX[M]E|claimed complete|已經成片" SKILL.md agents references assets scripts tests
```

結果：`Skill is valid!`；掃描無匹配、exit code 1，記為 `PLACEHOLDER_SCAN_CLEAN`。`git diff --check` 無錯誤；Windows checkout 僅顯示 LF→CRLF informational warnings。

## Safe replace 與備份保留

替換前正式安裝存在，`SKILL.md` SHA-256 為 `48a8833eebd9211304e6f1b15b6e378566be476f112114e22ac9e9420b42c200`，且既有 backup `laoma-aigc-director.backup-20260902-194403` 仍存在。只在 source tests 通過並提交 `5c4afe8` 後執行：

```powershell
$env:PYTHONUTF8='1'; python scripts/sync_skill.py --source . --destination-root "C:\Users\pony6832\.codex\skills" --replace
```

輸出：

```text
C:\Users\pony6832\.codex\skills\laoma-aigc-director
```

本次 retained backup：

```text
C:\Users\pony6832\.codex\skills\laoma-aigc-director.backup-20260902-202354
```

成功替換後兩代備份都保留，且 `STAGING_LEFT=0`。新備份保存 replace 前版本：

```text
laoma-aigc-director.backup-20260902-202354 files=18 missing=0 mismatch=0
SKILL.md_sha256=48a8833eebd9211304e6f1b15b6e378566be476f112114e22ac9e9420b42c200
laoma-aigc-director.backup-20260902-194403 files=17 missing=0 mismatch=0
SKILL.md_sha256=bf0a8f866dbb3a7025a737be71c57b0fead51b64bb3c1c28b5254e73daca2ff6
```

## 已安裝副本與 manifest

```powershell
$env:PYTHONUTF8='1'; python "C:\Users\pony6832\.codex\skills\.system\skill-creator\scripts\quick_validate.py" "C:\Users\pony6832\.codex\skills\laoma-aigc-director"
```

結果：`Skill is valid!`

逐檔重算命令（同一段也對兩代 backup 執行）：

```powershell
$roots=@('C:\Users\pony6832\.codex\skills\laoma-aigc-director','C:\Users\pony6832\.codex\skills\laoma-aigc-director.backup-20260902-202354','C:\Users\pony6832\.codex\skills\laoma-aigc-director.backup-20260902-194403')
foreach($root in $roots){
  $manifest=Get-Content -Raw -LiteralPath (Join-Path $root '.source-manifest.json') | ConvertFrom-Json
  $entries=@($manifest.files.PSObject.Properties); $missing=0; $mismatch=0
  foreach($entry in $entries){
    $path=Join-Path $root ($entry.Name.Replace('/','\'))
    if(-not (Test-Path -LiteralPath $path -PathType Leaf)){$missing++}
    elseif((Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLower() -ne [string]$entry.Value){$mismatch++}
  }
  "root=$root files=$($entries.Count) missing=$missing mismatch=$mismatch"
}
"SOURCE_SKILL_HASH=$((Get-FileHash -Algorithm SHA256 -LiteralPath 'SKILL.md').Hash.ToLower())"
```

結果：

```text
root=C:\Users\pony6832\.codex\skills\laoma-aigc-director files=18 missing=0 mismatch=0
SKILL.md_sha256=a0c966961b49ec0a065ecfe0c29914b59c086b0cb99f863c56d585ed3f58a8f7
SOURCE_SKILL_HASH=a0c966961b49ec0a065ecfe0c29914b59c086b0cb99f863c56d585ed3f58a8f7
```

manifest：`C:\Users\pony6832\.codex\skills\laoma-aigc-director\.source-manifest.json`。

## 新版 Smoke Project 與 V01 保存證據

使用已安裝 initializer：

```powershell
$env:PYTHONUTF8='1'; python "C:\Users\pony6832\.codex\skills\laoma-aigc-director\scripts\init_project.py" --root "C:\Users\pony6832\Documents\Codex\Codex專案分類\08 - AIGC影像生成相關\老馬AIGC導演專案" --name "V1_驗收短片"
```

輸出：`...\V1_驗收短片_V03`。使用已安裝 validator：

```powershell
$env:PYTHONUTF8='1'; python "C:\Users\pony6832\.codex\skills\laoma-aigc-director\scripts\validate_project.py" "C:\Users\pony6832\Documents\Codex\Codex專案分類\08 - AIGC影像生成相關\老馬AIGC導演專案\V1_驗收短片_V03"
```

結果：`PROJECT_VALID`。同一 validator 也回報 V02 `PROJECT_VALID`。

V01 在 replace／V03 初始化前後都存在且仍為 6 個檔案。以排序後「UTF-8 相對路徑 + NUL + 每檔 SHA-256 bytes」再雜湊，前後皆為：

```powershell
$env:PYTHONUTF8='1'; python -c "from pathlib import Path; import hashlib; root=Path(r'C:\Users\pony6832\Documents\Codex\Codex專案分類\08 - AIGC影像生成相關\老馬AIGC導演專案\V1_驗收短片_V01'); files=sorted(p for p in root.rglob('*') if p.is_file()); d=hashlib.sha256(); [d.update(p.relative_to(root).as_posix().encode('utf-8')+b'\0'+hashlib.sha256(p.read_bytes()).digest()) for p in files]; print(f'V01_FILES={len(files)}'); print(f'V01_TREE_SHA256={d.hexdigest()}')"
```

```text
V01_FILES=6
V01_TREE_SHA256=902f60d1faaf19fd2129424f9d490fe39b917282f0f0b422778eabaa60ff724e
```

現存版本：V01、V02、V03；沒有覆寫或刪除 V01/V02。V01 是強化 schema 前的 legacy smoke，若直接用新 validator 會正確回報 `asset_status` 缺少四個結構化欄位；依保存契約未就地升級或修改它，新建立的 V03 才是本次強化 initializer 的驗證對象。

## 驗證限制

- 沒有連接或付費呼叫第三方影像／影片生成平台，沒有生成、剪輯、播放或美學驗收實際成片。
- Gate 2 媒體驗證以標準函式庫檢查圖像簽名及 MP4／MOV ISO-BMFF 容器結構與宣告時長；不等同完整解碼或人工觀看。
- 七案 validator 對已提交 bundle 的結構不變量與明確機器標記具有決定性，但不宣稱可判斷任意自然語言矛盾，也不代表不同模型或未來 Agent 回覆具有模型無關決定性。
