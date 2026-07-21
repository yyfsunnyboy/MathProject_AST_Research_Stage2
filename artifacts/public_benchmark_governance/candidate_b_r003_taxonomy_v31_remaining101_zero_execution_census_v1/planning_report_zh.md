# Candidate B r003 taxonomy v3.1：remaining101 零執行 census 與批次規劃

**狀態：`ZERO_EXECUTION_CENSUS_PLANNING_NOT_TAXONOMY_ADJUDICATION`**

**規劃註記：`NON_ADJUDICATIVE_PLANNING_ONLY`**

## 範圍與禁止事項

- 本輪僅做母體盤點與下一批規劃，不進行正式逐格裁決。
- 不凍結新分類；不執行 candidate／diagnostics／EvalPlus／validation／Healer。
- 不將 UNRESOLVED 視為 L6；不混用 PENDING_REVIEW 與 UNRESOLVED。
- 不因 v3.1 重新裁決既有 97 格；v3.1 僅作外部 planning reference。
- 正式欄位 primary_layer／healer_eligibility 等保持空白。

## 母體 closure

- 正式母體：198
- 已凍結：97（G2 27 + module_exception 37 + multiple_signal 13 + output_contract_shape 20）
- 剩餘：101
- remaining101 roster SHA-256：`8fe0f5d95e7c6e86cda5f18dabfecae486120c50eeaf1baad6fe6c12b23143f6`
- unique program_id：101
- unique source_sha256：78
- unique task_id：36

## Evaluator outcome 分布

- `INVALID_INFRASTRUCTURE`：2
- `evalplus_base=fail;evalplus_plus=fail`：45
- `evalplus_base=pass;evalplus_plus=fail`：54

## 靜態 signal 統計（可重疊，非互斥分類）

- parse/L1 候選格：0
- contract/L2 候選格：99
- runtime 既有證據候選格：0
- semantic 強訊號候選格：99
- import 子類訊號格：0
- multiple-signal 格（≥2 signals）：101
- evidence-gap 格：101
- 無明顯靜態訊號格：0

### 各 signal 出現次數

- `entry_point_unique_candidate`：99
- `oracle_payload_shape_mismatch`：99
- `parseable_complete_but_incorrect`：99
- `public_examples_non_discriminating`：99
- `return_shape_mismatch`：99
- `extra_wrapper_or_output`：24
- `diagnostic_execution_required`：2
- `helper_defined_but_not_connected`：2
- `insufficient_static_evidence`：2

## Proposed primary batch（互斥，合計 101）

- `A_parse_tokenize_failure_candidates`：0
- `B_entry_signature_return_shape_import_candidates`：99
- `C_existing_runtime_evidence_candidates`：0
- `D_strong_semantic_indicator_candidates`：0
- `E_multiple_signal_or_evidence_gap_cases`：2

## 建議下一個正式裁決批次

- 規模：20 格
- 批次 roster SHA-256：`a22f086ba7d61995de98dafd57edcbdcb01fe46e780bd595163a6eabf813eb91`
- 目標 primary batch：`B_entry_signature_return_shape_import_candidates`
- Selection rule（統計前固定）：
  1. 僅取 `proposed_primary_batch=B_entry_signature_return_shape_import_candidates`
  2. 若 `dedupe_by_source=True`，僅取 source representative
  3. 若 `round_robin_return_type=True`，依 return_type_bucket 輪詢至目標 20 格
  4. 選後以 program_id 穩定排序
  5. 不以 Healer 可修性或預期成功率選樣
- 本輪不得開始裁決該批。

## v3.1 外部參考

- 檔名：`AI_生成程式共同失敗分類標準_實際使用版_v3.1.md`
- SHA-256：`93908ec8e4721f0039acc779fb948988b6c25e712c29890bd98aa7c21a8422a0`
- 狀態：`EXTERNAL_PLANNING_REFERENCE_NOT_INGESTED_INTO_REPO_GOVERNANCE`

## Execution counts

- 全部為 0（model／candidate／EvalPlus／diagnostics／validation／Healer／programs）。

