# Candidate B r003 taxonomy v3.1：Batch04 provisional adjudication v2

**狀態：`AUDIT_REVISED_PROVISIONAL_ADJUDICATION_V2`**

## Audit-approved revisions

- Rank 10 `9dbe9166f6ac22cedfafb269276c88ee25a37cf84044e736f7be00d8089464ba`：`dedupe_instead_of_unique_occurrence` → `frequency_one_instead_of_distinct_value`

僅修改mechanism tag及其確定性note；primary、secondary、confidence、outcome、Healer、evidence、citation與identity均不變。
其餘19格records逐欄等同v1。

- Primary：{'L4': 1, 'L5': 10, 'UNRESOLVED': 9}
- Secondary：{'L5': 1, 'empty': 19}
- Confidence：{'HIGH': 11, 'LOW': 9}
- Outcome：{'VALID_MODEL_OUTCOME': 20}
- Healer：{'eligible': 0, 'conditional': 0, 'abstain': 20}
- `dedupe_instead_of_unique_occurrence`：0；`frequency_one_instead_of_distinct_value`：1；`semantic_goal_drift`：3

未重新裁決、未audit v2，亦未執行candidate、imports、tests、EvalPlus、diagnostics、validation、Healer或模型；未freeze、未開始Batch05。
