# Tool Error Record

- 阻擋代碼：`tool_unavailable`
- 已知條件：使用者情境指出本機生成器啟動失敗或模型檔不可用，且沒有可驗證輸出。
- 本次可觀察環境：沒有生成器名稱、可執行檔、版本、命令、模型路徑、日誌或錯誤碼，故未執行工具，也不能宣稱已本機重現。
- 真實執行時必記：時間、OS／Python、GPU／VRAM（若相關）、工具 commit／版本、工作流版本、模型檔路徑與 SHA-256、完整命令、exit code、stderr 最小片段。
- 輸出檢查：本 bundle 沒有建立媒體檔、job ID 或成功截圖；`real_output_exists=false`。
- 禁止推論：節點名稱存在不代表模型可運算；排隊成功不代表輸出完成；文字規格不等於影片。
