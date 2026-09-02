# 老馬 AIGC 導演 Agent V1 設計規格

日期：2026-09-02  
狀態：使用者已核准第一版方向，細節可在實作與真實案件中版本化修正

## 1. 目標

建立一個獨立、可重複啟用的 Codex Skill／Agent：`laoma-aigc-director`。它預設擔任「製片總導演」，收到一張參考圖、一個點子或一項製作需求後，主動把案件推進到完整 AIGC 影片製作包；只有在會改變作品方向或造成大量生成成本的關鍵 Gate 停下確認。

V1 的成功標準不是只產生一段長 Prompt，而是讓角色、故事、攝影、聲音、生成與剪輯使用同一套版本化事實，並清楚區分已生成成果、待生成材料與未驗證假設。

## 2. 已核准的產品選擇

- 技術形態：獨立 Agent／Skill，不只是單一聊天視窗，也不直接擴充既有 `ai-video-learning-mentor`。
- 預設身份：製片總導演，而非純教學助理。
- 預設交付：完整製作包；可用工具存在且授權範圍允許時，直接生成必要圖像與影音資產。
- 知識策略：整合已核准的 AI 影音導師方法與共同工作經驗，但不沿用舊案件的私人素材、人物事實、故事或專屬提示詞。
- 演進策略：V1 先固定主流程；真實案件中的有效修正以版本方式加入，不靜默改寫舊規格。

## 3. 架構

### 3.1 獨立 Agent 套件

預計建立：

```text
laoma-aigc-director/
  SKILL.md
  agents/
    openai.yaml
  references/
    director-identity.md
    production-gates.md
    knowledge-routing.md
    knowledge-snapshot-v1.md
    project-state-and-versioning.md
    quality-and-recovery.md
    source-manifest.md
  assets/
    project-brief-template.md
    production-bible-template.md
    character-profile-template.json
    shot-production-table-template.md
    generation-report-template.md
  scripts/
    init_project.py
    validate_project.py
  docs/
    superpowers/
      specs/
      plans/
```

`SKILL.md` 只保存人格、模式選擇、資訊優先序、四個 Gate 與參考文件路由。模型／平台細節、模板與驗收量表放在對應資源，避免入口檔案過長。

### 3.2 知識核心

新 Agent 使用本套件內的 `director-methods-v1.0.0` 版本化知識快照，從現有 AI 影音學習導師選取已核准方法。快照本身必須包含可執行步驟，不能只列分類或要求執行時回頭讀取來源技能：

- Production Bible 與專案資料夾規格
- `CHARACTER_PROFILE.json` 角色唯一事實來源
- 角色總覽板、場景參考板、視覺分鏡板的獨立交付與驗收
- 敘事用途、走位、構圖、運鏡、節奏與連續性護欄
- Seedance、MiniMax H3、ComfyUI 與圖像生成的入口路由
- 4–6 秒短測、單變數 A/B、失敗標籤與縮減重試
- 官方／平台／社群假設的來源分級

`source-manifest.md` 以每項方法為單位記錄來源檔案、來源快照日期／SHA-256 或版本、來源等級、適用版本／入口、同步日期與排除內容。新 Agent 不直接依賴另一個技能資料夾的相對路徑，避免來源技能更新或搬移後失效；易變產品數字與可用性不匯入為固定事實，執行時重查。

### 3.3 案件輸出與 Agent 本體分離

Agent 程式與知識放在 Skill 套件；實際作品放在：

```text
C:\Users\pony6832\Documents\Codex\Codex專案分類\08 - AIGC影像生成相關\老馬AIGC導演專案\<PROJECT_NAME>_V1\
```

預設案件結構：

```text
<PROJECT_NAME>_V1/
  PROJECT_STATE.json
  PRODUCTION_BIBLE.md
  CHARACTER_PROFILE.json
  01_inputs/
  02_character_and_look/
  03_story_and_script/
  04_shot_design/
  05_generation_prompts/
  06_generated_assets/
  07_sound_and_music/
  08_edit_and_delivery/
  09_reports_and_qc/
```

原始輸入不覆蓋；衍生檔案使用明確版本號。`PROJECT_STATE.json` 記錄當前 Gate、已鎖定版本、未決事項與資產狀態。V1 僅支援 `schema_version="1.0"`；`project_version` 必須符合 `VNN` 並與 `<project_name>_<project_version>` 目錄一致，所有時間必須是含時區 ISO 8601。

`locked_artifacts` 每項至少包含 `role`、案件內相對 `path`、`version`、`sha256` 與 `reason`；驗證時解析實際路徑、拒絕越界，要求檔案存在並重算雜湊。`open_decisions` 使用含識別碼、問題、狀態與開啟時間的物件。`asset_status` 固定包含 `claimed_complete_without_output`、輸出清單、逐項 QC 與使用者核准，不建立同義狀態欄位。

## 4. 預設工作流程

### Gate 1｜方向鎖定

Agent 盤點素材並區分「可直接觀察」「創作推定」「需要決定」，提出最多三個差異明確的方向並推薦一個。鎖定目的、觀眾、平台、類型、時長、比例、核心概念、情緒曲線、結尾及必要的權利狀態。

### Gate 2｜角色與影像鎖定

Agent 建立角色事實檔、服裝與道具規則、場景、色彩、燈光、材質、焦段與畫面質感；交付角色總覽板、定裝／主視覺、無角色場景參考板，以及 4–6 秒一致性短測方案。長片、多人案或真人角色未通過短測時，不進入大量生成。

### Gate 3｜導演方案鎖定

Agent 完成故事、劇本、導演拆戲、Shot List、視覺分鏡、表演與走位、逐鏡攝影設計、聲音設計、剪輯節奏、逐鏡提示詞及連戲規則。確認後才進入批次或高成本生成。

### Gate 4｜成片驗收

Agent 使用當前可用且符合授權範圍的工具生成資產，檢查人物、服裝、道具、空間、動作、鏡頭、時間、聲音及剪輯連續性。最後交付成片，或在影片平台不可直接操作時交付可立即執行的完整生成／剪輯包。沒有產生可驗證輸出時，不得聲稱已成片。

### Gate／status 狀態矩陣

- Gate 1–3 可用 `draft|awaiting_approval|approved|blocked`，不可用 `complete`。
- Gate 4 可用 `draft|awaiting_approval|blocked|complete`；實體輸出、QC 與核准完整後直接完成，不使用含義重疊的 `approved`。
- 進入下一 Gate 代表上一 Gate 已核准，必須能以結構化鎖定產物證明。
- Gate 4 `complete` 必須具備 `06_generated_assets/` 內非空輸出、匹配輸出雜湊、非空白 generation report、全數通過且有證據的 QC、具名／含時區／有範圍的核准、無未決事項，以及 `claimed_complete_without_output=false`。

## 5. 資訊與決策優先序

發生衝突時依序採用：

1. 使用者本次明確要求。
2. 本次提供的圖片、影片、音訊與文件。
3. 本案已鎖定的 `PROJECT_STATE.json`、`PRODUCTION_BIBLE.md` 與 `CHARACTER_PROFILE.json`。
4. 本案已核准的主視覺、分鏡與測試成果。
5. 已核准的個人工作方法與模板。
6. Agent 一般預設。

舊案件只提供方法與失敗經驗，不提供新案件的人物或故事事實。

## 6. 模式與口令

預設為「製片總導演模式」。V1 另保留兩個顯式切換口令：

- `切換共同導演模式`：每個主要階段都先討論再執行。
- `切換導師模式`：以診斷、示範、練習與回饋為主，不以代做取代學習。

模式只改變互動密度，不改變角色一致性、來源查證、版本管理或驗收標準。

## 7. 工具與模型路由

- 圖像生成、角色板與分鏡：使用當前可用的內建圖像工具；生成前標明每張參考圖的唯一職責。
- Seedance／MiniMax H3／ComfyUI：依實際入口、版本、素材類型與目標時長選擇，不跨入口混用參數。
- 影片平台無可操作工具時：交付逐鏡提示詞、共用鎖定詞、參考素材對照、設定、檔名與驗收表。
- 音樂、語音或第三方平台：先處理授權、肖像、聲音與公開揭露需求；不得要求使用者在聊天中貼出金鑰。
- 會變動的模型規格、價格、限制與介面：執行時以官方來源重新查證，不把知識快照當作永久現況。

## 8. 失敗處理

- 資訊不足：標示假設並先做最小可驗證版本，不因非關鍵空缺停止整案。
- 角色或畫面漂移：回到最近一次已鎖定資產，縮短時長、減少遮擋或高速動作，每次只改一個主要變數。
- Prompt 污染：建立乾淨版本，不在原 Prompt 上無限堆疊否定詞。
- 工具不可用：保留完整可執行製作包，明示缺少的實際生成步驟與補救方式。
- 規格衝突：記錄來源、日期、入口與差異，保留待測狀態，不自行選一個說成確定事實。
- 權利不明：可繼續做不涉及外傳的企劃與草稿，但在真人肖像、聲音、品牌或商業發布前停止相應動作。
- 成本或大量生成：必須通過 Gate 3；遵守工具或平台當下需要的確認規則。

## 9. 驗證策略

### 結構驗證

- Skill frontmatter、名稱、連結與 `agents/openai.yaml` 通過技能驗證器。
- `init_project.py` 可重複建立案件，不覆蓋既有版本。
- `validate_project.py` 能辨識缺少的 Gate 產物、錯誤版本引用和未通過狀態。
- `validate_project.py` 驗證精確 schema、Gate/status 矩陣、目錄版本、含時區時間、鎖定檔安全路徑與 SHA-256，以及 Gate 4 的實體輸出、QC、核准和假完成旗標；不可用固定文字或空白模板作為完成證據。
- `sync_skill.py` 在本次複製、manifest 或推進失敗時清除本次 staging；若既有安裝已改名而推進失敗，還原舊安裝。成功替換後保留時間戳備份。

### 行為情境

至少測試：

1. 只提供一句故事點子。
2. 提供一張虛構角色圖並要求短片。
3. 提供已核准角色圖並要求直接製作。
4. 要求只改一顆失敗鏡頭。
5. Seedance、H3 或 ComfyUI 入口不明。
6. 真人肖像或聲音授權不明。
7. 工具不可用但仍需完整生成包。

七案必須由執行 Agent 讀取最終 runtime 指示後，在隔離目錄實際產生 response／artifact bundle。另一個標準函式庫 validator 依每案的模式、Gate、狀態、必要產物與雜湊、禁止行為和完成證據驗收；驗證重點是決策與產物，不測固定措辭，也不宣稱模型行為與實際影片生成具模型無關的決定性。

## 10. V1 完成定義

V1 只有在以下條件全部成立時才算完成：

- 獨立 Skill 安裝後可被正確發現與啟用。
- 能由一句點子或一張圖建立新案件與 `PROJECT_STATE.json`。
- 四個 Gate、資訊優先序與模式切換運作一致。
- 能產生角色、故事、分鏡、提示詞、聲音、剪輯與 QC 的完整文件骨架。
- 不混用舊角色資料，不覆蓋舊版本，不把未生成內容描述為成片。
- 相關驗證腳本與代表性情境測試通過。
- 正式 Skill 與可攜式來源副本的版本和雜湊可對照。
- 七個實際 Agent 情境 bundle 與其決定性產物驗證器全部通過。

## 11. V1 不包含

- 自建雲端後端、帳號系統或素材資料庫。
- 自動購買生成額度或繞過第三方平台確認。
- 未經核准的公開發布、上傳或素材分享。
- 將所有平台參數硬寫成永久不變規格。
- 自動把每個新案例寫入長期個人方法庫；案例提煉仍需使用者核准。
