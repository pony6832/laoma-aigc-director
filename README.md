# 老馬 AIGC 導演

一個給 Codex 使用的獨立 AIGC 影片製片總導演 Skill。它能從點子、參考圖或製作需求開始，建立可追蹤的製作案，並以四個 Gate 管理角色與視覺、導演方案、生成、後製及驗收。

## 能做什麼

- 建立 Project Brief、Production Bible 與角色設定檔。
- 規劃故事、分鏡、逐鏡生成提示、聲音、剪輯與 QC。
- 未指定導演時，先以八項通用電影鏡頭方法處理劇本、機位、焦段、運鏡、構圖、燈光、表演、聲畫與動作物理；需要鮮明作者取向時再疊加導演風格模組。
- 路由 Seedance、MiniMax H3、ComfyUI 等工作方法，執行時重新查證會變動的平台能力。
- 以 `PROJECT_STATE.json`、版本與 SHA-256 鎖定核准產物。
- 診斷生成失敗並保留可回退版本。
- 防止在缺少輸出、QC 或核准證據時誤稱已完成成片。

## 四個 Gate

1. 方向鎖定：目的、觀眾、平台、時長、比例、概念與權利。
2. 角色與影像鎖定：角色檔、視覺基準、場景板與 4–6 秒一致性短測。
3. 導演方案鎖定：故事、逐鏡表、生成方案、聲音、剪輯與 QC 計畫。
4. 成片驗收：實際輸出、雜湊、報告、QC 與使用者核准。

## 安裝

需要 Python 3.11。於解壓後的專案根目錄執行：

```powershell
$env:PYTHONUTF8='1'
python scripts/sync_skill.py --source . --destination-root "$env:USERPROFILE\.codex\skills"
```

目的目錄已有舊版時，明確加入 `--replace`。同步器會先建立帶時間戳的備份，再安裝新版本：

```powershell
python scripts/sync_skill.py --source . --destination-root "$env:USERPROFILE\.codex\skills" --replace
```

安裝後可這樣開始：

> 請用老馬 AIGC 導演模式，把這個想法發展成完整的 AIGC 影片製作案：……

也可查詢可重用的電影鏡頭方法：

```powershell
$env:PYTHONUTF8='1'
python scripts/query_cinematic_grammar.py "把角色的抽象焦慮改成可拍攝的表演"
```

## 開發驗證

```powershell
$env:PYTHONUTF8='1'
python -m unittest discover -s tests
python tests/acceptance_validator.py --contracts tests/fixtures/acceptance-contracts.json --results tests/acceptance
```

最新的 GPT-6 Astra 檢查與修正結果見 [2026-09-09-astra-review.md](docs/verification/2026-09-09-astra-review.md)。

## 驗證界線

`PROJECT_VALID` 表示目前 Gate 的目錄、狀態與證據欄位符合契約。圖片檔頭或影片容器通過檢查，不等於影片已實際播放或視覺品質合格；成片仍須完成畫面、聲音、連戲與交付規格驗收。
