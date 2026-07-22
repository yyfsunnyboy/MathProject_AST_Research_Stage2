# Candidate B r003 taxonomy v3.1：Batch03 provisional v1 獨立audit

**狀態：`INDEPENDENT_STATIC_AUDIT_COMPLETE_MATERIAL_FINDINGS`**

- AFFIRMED：18
- NON_MATERIAL：0
- MATERIAL：2

兩個MATERIAL finding均為同一方向性mechanism錯誤：candidate只計出現一次的值，公開結果要求distinct值各計一次；
原tag `dedupe_instead_of_unique_occurrence` 描述的是相反方向。建議改為 `frequency_one_instead_of_distinct_value`，
保留L5、HIGH、VALID_MODEL_OUTCOME、abstain與`semantic_goal_drift`。

- audit後Primary：{'L2': 1, 'L5': 12, 'UNRESOLVED': 7}
- audit後Healer：{'eligible': 0, 'conditional': 0, 'abstain': 20}
- 7格UNRESOLVED、12格L5 layer、1格L2及20格Healer disposition其餘均獨立affirm。

未執行candidate、imports、tests、EvalPlus、diagnostics、validation、Healer或模型；未修改provisional。
