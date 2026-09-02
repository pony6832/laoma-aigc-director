# 品質與復原

## QC 分類

- `identity_drift`：角色身分或核心外觀漂移。
- `wardrobe_drift`：定裝、配件或材質連續性漂移。
- `spatial_error`：人物、物件、場景或軸線的空間關係錯誤。
- `camera_error`：景別、運鏡、視角或鏡頭動機不符。
- `motion_error`：動作節奏、物理接觸或時序失真。
- `anatomy_error`：肢體、手指、關節或表情結構錯誤。
- `audio_error`：人聲、嘴型、音效、音樂或同步錯誤。
- `prompt_pollution`：輸入混入舊案、無關參考或互相衝突的指令。

## 復原順序

1. 回到最近鎖定版本，確認未把失敗輸出帶回新一輪輸入。
2. 縮短時長。
3. 降低動作複雜度。
4. 一次只改一個主變數。
5. 通過單鏡 QC 後，再擴大鏡頭數、時長或後製層次。

## 驗收案例的復原證據

針對失敗重試或工具不可用的案件，驗收者必須能找到：失敗版本仍保留、錯誤分類與時間、實際採用的單一變更、可回退的 checkpoint，以及是否真的產生可播放輸出。沒有輸出檔、工具紀錄或 QC 結果時，狀態只能標為阻擋／待處理，不得標為已生成或 Gate 4 完成。

案例中的 `spatial_error`、`anatomy_error`、`prompt_pollution`、`audio_error` 與 `rights_unclear` 應分別記錄；權利不明先停在 Gate 1／Gate 2，工具不可用先停在 Gate 3，且不得以替代工具自動繞過核准。

## Gate 4 結構化完成證據

文字宣稱、報告標題、`已知限制` 四個字、job ID、排隊成功或空白模板都不是完成證據。`complete` 必須同時具備：

1. `06_generated_assets/` 內至少一個非空輸出，並在 `asset_status.outputs` 記錄相對路徑、版本、種類與匹配 SHA-256。
2. 已填寫的 generation report；其內容不得仍與原始模板完全相同，並以 `generation_report` 角色鎖定。
3. `asset_status.qc.status="passed"`、含時區檢查時間、檢查者，以及非空的逐項 checks；每項都有 `status="passed"` 與具體 evidence。
4. `asset_status.approval.status="approved"`、含時區核准時間、核准者與非空 scope。
5. `claimed_complete_without_output=false` 且 `open_decisions=[]`。

最後以 `scripts/validate_project.py` 重算鎖定檔及輸出雜湊。驗證器通過只證明結構與所記錄檔案一致；它不會自行判讀影片美學，也不代表第三方生成真的發生，QC 證據仍須來自實際檢查。
