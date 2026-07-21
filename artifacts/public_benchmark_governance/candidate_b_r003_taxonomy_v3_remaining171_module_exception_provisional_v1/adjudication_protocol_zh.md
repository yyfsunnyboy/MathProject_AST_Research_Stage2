# Adjudication protocol（module_execution_exception_signal provisional v1）

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
- 不修改 machine census 或 G2 provisional 產物

## 輸出

- 37 列 ai_provisional_adjudication.csv
- fixed_cluster_roster.csv 與 summary / manifest / provenance
