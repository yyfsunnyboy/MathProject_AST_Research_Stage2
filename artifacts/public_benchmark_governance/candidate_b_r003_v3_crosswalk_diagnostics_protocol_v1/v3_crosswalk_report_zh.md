# Candidate B r003 v3 derived crosswalk 與 unresolved198 diagnostics freeze

## Derived crosswalk

此目錄是 development evidence 的衍生 view，不覆寫既有 census、21 案 adjudication、統計、manifest 或 hash。輸出逐欄保存原 census，並以 `legacy_adjudication_*` 保存 21 案裁決；所有 v3 欄位另加前綴。

- L1：20。依既有 G1／parse evidence crosswalk；truncation 僅作 mechanism tag。
- L2：6。皆由 G3e entry-point／signature evidence crosswalk。
- PASSED controls：76，不配置 failure layer。
- PENDING_REVIEW：198，`v3_primary_failure_layer` 保持 CSV null（空值），沒有猜成 L4 或 L5。

21 案 adjudication 仍完整保留為 legacy evidence。即使其中曾提出更細的人工診斷，本 revision 也不以少數代表案回填 198 格；必須等待 frozen coarse diagnostics 後另建 revision。

## Healer 三欄

`healer_eligibility`、`healer_decision`、`healer_outcome` 已拆開。兩個既有 unique alias 為 eligible／transformed／unchanged_fail；其他已裁決 L1/L2 不符合完整 v3 安全條件。198 unresolved 的 eligibility 為 undetermined，實際 v0 decision 與 paired outcome仍依 frozen artifact記錄。

## Diagnostics freeze

protocol 的判定順序固定為 infrastructure → G1 → G3e → G2 → G3s → G3a → G4。runner 只輸出 allowlisted 粗粒度欄位，不保存輸入、expected/actual、訊息或 traceback；不執行 EvalPlus correctness，且結果永遠不得成為 Healer runtime input。本輪 diagnostics executions 為 0。
