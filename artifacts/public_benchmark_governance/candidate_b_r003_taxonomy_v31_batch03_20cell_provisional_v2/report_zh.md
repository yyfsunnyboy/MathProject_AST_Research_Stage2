# Candidate B r003 taxonomy v3.1：Batch03 provisional adjudication v2

**狀態：`AUDIT_REVISED_PROVISIONAL_ADJUDICATION_V2`**

## Audit-approved revisions

- Rank 4 `3b802dcce09d236485df19d1c985675e091e74cbb5fcbf6e73f753d873f62e88`：`dedupe_instead_of_unique_occurrence` → `frequency_one_instead_of_distinct_value`
- Rank 14 `71012956073b53a6d9d9341681ec221238d2d1fe8cdd2dfc5a82291b2fb7d44f`：`dedupe_instead_of_unique_occurrence` → `frequency_one_instead_of_distinct_value`

兩格只修改mechanism tag及其確定性note；primary、secondary、confidence、outcome、Healer、evidence、citation與identity均不變。
其餘18格records逐欄等同v1。

- Primary：{'L2': 1, 'L5': 12, 'UNRESOLVED': 7}
- Secondary：{'L5': 1, 'empty': 19}
- Confidence：{'HIGH': 13, 'LOW': 7}
- Outcome：{'VALID_MODEL_OUTCOME': 20}
- Healer：{'eligible': 0, 'conditional': 0, 'abstain': 20}
- `dedupe_instead_of_unique_occurrence`：0；`frequency_one_instead_of_distinct_value`：2；`semantic_goal_drift`：4

未重新裁決、未audit v2，亦未執行candidate、imports、tests、EvalPlus、diagnostics、validation、Healer或模型。
