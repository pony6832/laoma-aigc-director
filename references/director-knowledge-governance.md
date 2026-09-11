# 導演知識治理

本規則參考 Cinecraft 的可追溯知識庫方法，經老馬 Agent 改寫後用於導演、攝影與審片知識。

## 三層資料

- 原始來源層：外部文件或固定版本的上游檔案，只讀保存，不在整理時改寫。
- 方法綜合層：本 Skill 的路由、比較、摘要與可執行規則；每項可驗證主張都要附來源，並標示是來源原文、網頁資料或 Agent 綜合／推論。
- 本案事實層：`PROJECT_STATE.json` 與案件鎖定產物；只描述這部作品，不反向污染通用方法。

## 證據等級與衝突

導演鏡頭庫目前標為 `community_synthesis`：可做創作假設與測試起點，但不是已核實史實。精確技術主張要補導演／攝影師訪談、正式幕後資料、出版品或可信研究，才可升級為 `verified_primary` 或 `verified_secondary`。資料不足時明說推論，不得默默消除矛盾；保留兩方主張、來源、日期與影響，交由使用者或新證據裁決。

## 索引、更新與健康檢查

每次新增或更新都同步 `catalog.json`、來源 commit、授權、檢查日期與相關路由。週期檢查：失效連結、孤立條目、重複主題、矛盾、缺來源、已被新資料取代或可能過時的產品／技術主張。創作判斷衝突只提出方案，不自行改寫已核准案件事實。

## 本次上游快照

- DirectorSKILL 2.1.0，commit `c65ae0d14457053efb1e354c7e7f7e120d97fad1`，MIT；20 份鏡頭模組原樣保存於 `director-styles/lenses/`。
- Cinecraft，commit `519311207eae74cf91243fda9b03f74dcbeacb0d`，MIT；只改寫採用其來源／綜合／專案分層與 lint 方法，未把其整套 Skill 嵌入執行路由。
- 授權文字保存於 `director-styles/DIRECTORSKILL_LICENSE.txt` 與 `director-styles/CINECRAFT_LICENSE.txt`。
