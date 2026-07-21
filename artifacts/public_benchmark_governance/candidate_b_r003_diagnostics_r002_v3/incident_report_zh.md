# Candidate B r003 diagnostics v2 formal preflight incident 與 v3 freeze

## 結論

v2 calibration 為有效的 8/8 development controls，原目錄、bytes、SHA-256、mtime 與內容均保留。本事件是 `ZERO_EXECUTION_FORMAL_PREFLIGHT_LOGIC_INCIDENT`：formal 嘗試在任何 worker 啟動前，被「calibration 必須不存在」與後續「calibration 必須存在」的矛盾 preflight 阻擋；formal cells executed = 0。

v3 只修正 mode-specific state transition。formal mode 要求 v2 calibration directory 存在，並逐項驗證固定 execution-manifest hash、results hash、receipt、8-row results、cohort identities、protocol hash與v2 source-manifest hash；只要求新的 v3 formal output 不存在。worker、per-cell procedure、timeouts、result schema與198-cell identity ledger均未修改，因此不重跑 calibration。

本輪未執行 calibration、formal198、模型、EvalPlus correctness、Healer或validation。
