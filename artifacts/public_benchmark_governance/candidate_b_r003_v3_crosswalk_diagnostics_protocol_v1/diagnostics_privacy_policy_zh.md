# Candidate B r003 unresolved198 diagnostics privacy policy

本政策適用於 `candidate_b_r003_unresolved198_coarse_diagnostics_v1`。本輪僅凍結，沒有執行 diagnostics。

## 允許保存

每格只可保存：phase、exception class、最後一個 model-source frame 的行號與 AST node kind、entry-point／callable／signature binding 結果、termination、return type bucket、return shape bucket，以及 program/source/task/evaluator/protocol identity hashes。

## 絕對禁止保存

不得保存 hidden 或 public test input、expected/actual value、return value、exception/assertion message、traceback、stdout/stderr 內容、candidate source、reference solution 或 evaluator frame。CSV header 與每個值都必須通過 allowlist；出現未知欄位、換行文字或未允許內容即 fail-closed，且不得建立 output directory。

## 使用隔離

diagnostic 結果只供後續人工分類 revision 使用，不得成為 Healer runtime input、rule trigger、transformation parameter、答案推導資料或 validation 選擇訊號。任何新 mechanism／rule family 必須另行版本化，具至少跨兩個不同 task 的證據，並同時滿足 Local、Deterministic、Answer-free、Task-agnostic、Unique、Invariant-supported、Tested、Frozen、Evaluator-blind；否則 abstain。

## 執行紀律

僅能在 WSL/Linux、固定 Python/EvalPlus dataset loader 版本、parallel=1、無 retry/resume/overwrite 下，以 manifest 中唯一 output path 人工執行一次。runner 不執行 EvalPlus correctness、不寫 G4 結論，也不修改 census、adjudication、Prompt、Healer、Pipeline 或 validation。
