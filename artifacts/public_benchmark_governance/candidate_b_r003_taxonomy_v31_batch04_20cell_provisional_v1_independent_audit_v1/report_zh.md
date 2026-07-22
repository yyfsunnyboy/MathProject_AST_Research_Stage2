# Candidate B r003 taxonomy v3.1：Batch04 provisional v1 獨立audit

**狀態：`INDEPENDENT_STATIC_AUDIT_COMPLETE_MATERIAL_FINDINGS`**

- AFFIRMED：19
- NON_MATERIAL：0
- MATERIAL：1

唯一MATERIAL finding為mechanism方向錯誤（rank 10 / Mbpp/777）：candidate只計出現一次的值，
公開結果要求distinct值各計一次；原tag `dedupe_instead_of_unique_occurrence` 描述相反方向。
建議改為 `frequency_one_instead_of_distinct_value`，保留L5、HIGH、VALID_MODEL_OUTCOME、abstain與
`semantic_goal_drift`。

- audit後Primary：{'L4': 1, 'L5': 10, 'UNRESOLVED': 9}
- audit後Secondary：{'L5': 1, 'empty': 19}
- audit後Healer：{'eligible': 0, 'conditional': 0, 'abstain': 20}
- 9格UNRESOLVED、1格L4（含rank14 secondary=L5）、10格L5 layer及20格Healer abstain均獨立affirm。
- eligible=0、conditional=0符合安全門檻。

未執行candidate、imports、tests、EvalPlus、diagnostics、validation、Healer或模型；
未修改provisional/roster/remaining21/taxonomy/frozen；未建立v2、未開始Batch05。

欄位級差異：mechanism_tags_json @ batch_rank=10
