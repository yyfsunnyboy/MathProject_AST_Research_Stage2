# Candidate B r003 diagnostics r002 v2 preflight schema incident

## 結論

本事件是 `ZERO_EXECUTION_PREFLIGHT_SCHEMA_INCIDENT`，不是 calibration run incident。v1 frozen manifest 缺少 runner 所要求的 `diagnostic_executions`，因此在 dataset initialization 與 worker start 之前即以 `KeyError` 結束；worker processes started = 0、calibration cells executed = 0、diagnostic executions = 0。

v1 目錄與 manifest bytes 原樣保留。v2 由 materializer 明確產生整數 `diagnostic_executions: 0`；runner 對欄位缺失、bool、其他非整數、非零與任何 frozen hash drift 均 fail-closed。

## calibration manifest SHA 語意

舊 `_calibration_all_passed()` 實際計算的是 calibration output `execution_manifest.json` **檔案 bytes 的 SHA-256**，並非 receipt 內的 `source_manifest_sha256`。v2 將參數與 formal CLI 統一命名為 `calibration_execution_manifest_sha256` / `--calibration-execution-manifest-sha256`。receipt 的 `source_manifest_sha256` 另行要求等於 frozen r002 v2 manifest SHA-256；兩種 hash 不得互換。

## 執行狀態

本輪只做靜態 materialization、zero-execution manifest preflight 與 tests，未執行 calibration 或 formal198，也未呼叫模型或 EvalPlus correctness。
