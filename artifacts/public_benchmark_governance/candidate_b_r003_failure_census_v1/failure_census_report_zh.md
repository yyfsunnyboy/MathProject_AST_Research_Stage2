# Candidate B r003 failure census（development60）

## 範圍與方法

本 census 完整納入 Candidate B r003 的 300 個 H0 programs：76 pass 作 negative controls，224 fail 進入失敗 census。分析以程式批次讀取 evaluation source 並建立 AST 特徵；本報告與 CSV 不輸出 source，也沒有逐格複述程式。沒有呼叫模型、沒有重跑 EvalPlus、沒有讀取 r001/r002 response、沒有操作 untouched20 validation。

逐格 `evaluator_hash` 使用 frozen evaluation manifest SHA-256 作治理身分，該 manifest 綁定 EvalPlus 0.3.1 與 evaluator engine；repository 未凍結 package source hash，因此不能把此值解讀為 evaluator package code hash。

## 保守分類結果

Primary layer/count：`{"PASSED": 76, "L0": 0, "L1": 20, "L2": 6, "L3": 0, "L4": 0, "L5": 0, "UNRESOLVED": 198}`。

Outcome validity/count：`{"PENDING_REVIEW": 198, "VALID_MODEL_OUTCOME": 102}`。

Failure subtype/count：`{"AGGREGATE_EVALPLUS_FAILURE_NO_DIAGNOSTIC": 198, "GENERATION_TRUNCATED": 3, "PYTHON_PARSE_FAILURE": 17, "REQUIRED_FUNCTION_MISSING_AMBIGUOUS": 1, "REQUIRED_FUNCTION_MISSING_UNIQUE_ALIAS": 2, "REQUIRED_SIGNATURE_INCOMPATIBLE": 3}`。

只有公開 contract 與 AST 能直接證明的 parse/required-function/signature/return 問題才定案 L1/L2。缺標準函式庫 import 但沒有 traceback 的格子只列為 L4 candidate，不直接定案；其餘 aggregate EvalPlus failures 維持 `UNRESOLVED/PENDING_REVIEW`。尤其 base-pass/plus-fail 不能自動視為 L5，因為 plus input 下仍可能發生 runtime/data-flow failure。

## Healer eligibility

Repairability tier/count：`{"CANDIDATE_REVIEW": 24, "ELIGIBLE_EXACT": 2, "INELIGIBLE": 76, "UNRESOLVED": 198}`。

`ELIGIBLE_EXACT` 只代表既有 v0 entry-point alias guard 的公開契約/AST資格，不代表功能 rescue；r003 正式 paired analysis 已顯示兩個 changed windows 均 fail→fail。本輪沒有修改或新增任何 Healer rule。

## Candidate rule families

- `ENTRYPOINT_ALIAS_UNIQUE_ARITY_COMPATIBLE_V0`：2 cells／1 tasks；ELIGIBLE_EXACT；low syntax/packaging risk; observed functional rescue may remain zero。
- `STDLIB_MODULE_IMPORT_GUARDED_CANDIDATE`：0 cells／0 tasks；CANDIDATE_REVIEW；medium; import can alter name resolution or hide deeper semantic failure。
- `PARSE_OR_TRUNCATION_MECHANICAL_REVIEW`：20 cells／10 tasks；CANDIDATE_REVIEW；high unless repair is uniquely mechanical。
- `SIGNATURE_CONTRACT_REVIEW`：4 cells／2 tasks；CANDIDATE_REVIEW；high; may change intended semantics。

這些 families 不使用答案、task-specific knowledge 或 hidden tests。缺 import family 仍有 execution-path、dynamic binding、shadowing與深層語義錯誤風險；signature/parse repair 的語義歧義更高，均不可直接升為 production rule。

## Human review queue

Queue 共 21 個代表案例，只提供公開 contract/AST evidence、EvalPlus aggregate status 與 source hash，不包含 source。選樣規則是 feature stratum 後依 program_id，並非依 task_id 或答案挑選。未取得 traceback 或更完整 gate evidence 的案例維持 `PENDING_REVIEW`，沒有為湊齊分類而猜成 L5。

## 治理結論

本 census 可定位少量明確 contract/packaging failures，並提出需獨立評估的 guarded rule families；但大多數 formal failures 缺少逐格 execution diagnostics，不能可靠拆成 L4 與 L5。結論只屬 development evidence，不授權修改 Prompt、Pipeline、Healer v0，亦不授權實作 Healer v1 或啟動 validation。

- model_calls=0
- evalplus_executions=0
- healer_rules_modified=false
- validation_not_executed=true
