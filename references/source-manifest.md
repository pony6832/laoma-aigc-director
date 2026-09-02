# 來源清單

- 快照名稱：`director-methods-v1.0.0`
- 同步日期：2026-09-02
- 來源範圍：已安裝 `ai-video-learning-mentor` 於同步當下的可移植方法，以及本案已核准設計。
- 隔離規則：只提煉方法；不匯入私人素材、舊角色事實、舊故事、舊身分、專屬提示詞、憑證或來源媒體。
- 執行規則：本 Skill 使用本地[方法快照](knowledge-snapshot-v1.md)，不在執行時讀取來源技能資料夾。會變動的產品能力、價格、限制、地區、額度、節點與入口必須重新查證。

## 每項方法來源

| 方法 | 來源檔案 | 快照／雜湊或版本 | 來源等級 | 適用版本／入口 | 同步日期 | 排除內容 |
|---|---|---|---|---|---|---|
| 入口、資訊優先序與完整製片交付 | `ai-video-learning-mentor/SKILL.md` | SHA-256 `ba4af918906f83742b28d17712add835fc90f41164a1f8e8d1e388b6af2220f9` | A：已核准工作方法 | Laoma Director V1 全模式 | 2026-09-02 | 教學人格、舊案例內容、來源技能路徑依賴 |
| 一張圖／點子／需求的起步流程 | `ai-video-learning-mentor/references/personal-production-playbook.md` | SHA-256 `5ff768c0994a3fe98291f8ed09c3ebaa4f6c7b4a0c559042b92b7946c279d317` | A：已核准工作方法 | Gate 1–3 | 2026-09-02 | 私人案例、舊資料夾結構、舊角色與故事 |
| 角色檔、總覽板與一致性測試 | `ai-video-learning-mentor/references/character-package-system.md` | SHA-256 `b3f99a63438c7d232f40b5948ddae1e0743e1fe8ee50be5879ab60b34d9deebf` | A：已核准工作方法 | Gate 2；虛構／本人／已授權角色 | 2026-09-02 | 任何人物素材、姓名、服裝或身份事實；固定參考張數不當成平台保證 |
| 景別、運鏡、動作、時間與連戲 | `ai-video-learning-mentor/references/directing-language.md` | SHA-256 `06e7cfc68b47fe158c8646320567d67f08af6c3bfd4009379fc99a78c39e51df` | A：已核准工作方法 | Gate 3；平台中立 | 2026-09-02 | 特定舊鏡頭與題材 |
| 目的導向攝影設計與可測試骨架 | `ai-video-learning-mentor/references/cinematic-camera-grammar.md` | SHA-256 `65409faeb36e0d61a066bdf074afa7adc8a33cee8a7766bf63e15436d202cce0` | A：已核准工作方法 | Gate 2–3；平台中立 | 2026-09-02 | 導演姓名模仿、原片逐鏡複製、案例角色 |
| Seedance 模式、提示結構與容量規劃 | `ai-video-learning-mentor/references/seedance-core.md` | 來源快照日期 2026-08-10；SHA-256 `c16facde67c110260c55f49361e8c43d6477e7343f0d30dfaa194b3ae1883487` | B：官方衍生方法，現況需重查 | 使用者實際 Seedance 入口與顯示版本 | 2026-09-02 | 解析度、時長、數量、地區、價格與功能可用性等易變聲明 |
| H3 多模態素材分工與聲畫提示 | `ai-video-learning-mentor/references/minimax-h3.md` | 來源快照日期 2026-08-10；SHA-256 `780426a5a4255e9866b00372f6184a51b5b78a25fefde7fdf4f0f979708daf60` | B：官方衍生方法，現況需重查 | 使用者實際 MiniMax／Partner/API 入口 | 2026-09-02 | 固定解析度、時長、素材上限、價格、權重發布與本機部署聲明 |
| ComfyUI 四層路由、重現與除錯 | `ai-video-learning-mentor/references/comfyui-video-workflows.md` | 來源快照日期 2026-08-10；SHA-256 `76b0ced235e0dccf9e40c6778092a494edc8d03c96a30c71d0fa04c5fb2bce94` | B：官方衍生方法，節點現況需重查 | 實際 ComfyUI release／nightly 與已裝節點 | 2026-09-02 | 節點名、輸入上限、API 可用性、第三方節點信任與「節點等於本機模型」聲明 |
| 表演節拍、收音分層與後製鏈 | `ai-video-learning-mentor/references/performance-and-sound.md` | 來源快照日期 2026-08-03；SHA-256 `d502fdfe216dcd295d2b8b48b1d20c00284f407859aa7b1eecebf6f60e3cbce2` | A：已核准工作方法 | Gate 3–4；實拍與生成聲音 | 2026-09-02 | 真人聲紋、音樂、錄音與設備品牌偏好 |
| 分鏡、逐鏡提示與交付分離 | `ai-video-learning-mentor/references/storyboard-delivery-system.md` | SHA-256 `fd411ff924c0cddf93c631fa33dddd8c4c16cf3618e6fe93bf52b91d1d0545a2` | A：已核准工作方法 | Gate 3；平台中立後再轉入口格式 | 2026-09-02 | 舊分鏡畫面、角色、腳本與固定格數偏好 |
| 失敗分類與縮減階梯 | `ai-video-learning-mentor/references/failure-recovery.md` | SHA-256 `e9144859c9095eec1c2761d6ef4a485509a16b19295d32699a2154c6b710c763` | A：已核准工作方法 | Gate 2–4；所有入口 | 2026-09-02 | 舊失敗圖、舊提示詞、案例身分與素材 |
| QC 順序、失敗標籤與暫評邊界 | `ai-video-learning-mentor/references/diagnostics-and-assessment.md` | SHA-256 `d539b40aeef7f70728ee0e49313ed95f74f3f75dd2b232a73d44796abc725cf3` | A：已核准工作方法 | 短測、逐鏡與 Gate 4 | 2026-09-02 | 舊作品評分、個人資料與未觀看輸出的確定評語 |

## 來源等級

- A：已核准、平台中立或低漂移的共同工作方法，可直接依本快照執行。
- B：由帶日期的官方／入口資料提煉出的路由方法。只保留「如何查、如何分層、如何記錄」；易變產品數字與可用性未匯入，執行時重查。

來源雜湊只證明 2026-09-02 提煉時讀取的檔案版本，不代表來源內容永久正確，也不授權執行外部生成或公開發布。
