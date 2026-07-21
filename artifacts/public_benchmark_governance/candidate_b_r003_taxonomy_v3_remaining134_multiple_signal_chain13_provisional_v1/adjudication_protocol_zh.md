# Adjudication protocol（multiple_signal_chain provisional v1）

**狀態：`AI_ASSISTED_PROVISIONAL_ADJUDICATION_NOT_FORMAL_HUMAN_REVIEW`**

## 輸入

- frozen machine census v1（manifest SHA 釘選）
- remaining171 fixed roster
- coarse diagnostics phase / exception_class / model_source_line
- H0 evaluation_source（AST parse only）
- public task contract（prompt + entry point）

## 禁止

- 不執行程式、EvalPlus、diagnostics、Healer
- 不載入 H1、hidden expected/actual、exception message、traceback
- 不修改 machine census、G2 provisional 或 module_exception provisional 產物

## Mechanism tag 政策

- specific mechanism tags 恆保留（如 unbound_name_stats、self_recursive_override）
- 另加 generic `module_execution_exception` **iff** frozen diagnostic phase 在 {G2_base, G2_plus} 且 termination 為 raised
- phase=completed 的 cell（如 Mbpp/125 find_length、c0c3cb xor_accumulate）不加 module_execution_exception

## Secondary layer 政策

- L5 secondary 僅在 public arithmetic 可證時標記（如 Mbpp/722 filter_data 五格）
- L4 primary cell 不得無 public 證據猜測 L5 secondary

## Outcome validity

- outcome_validity ≠ taxonomy layer 確定性
- VALID_MODEL_OUTCOME 表示模型失敗路徑有效，不強制 primary layer 閉合

## 輸出

- 13 列 ai_provisional_adjudication.csv
- fixed_cluster_roster.csv、healer_candidate_detail.csv 與 summary / manifest / provenance
- pre_freeze_adversarial_audit.csv / pre_freeze_adversarial_audit_zh.md
