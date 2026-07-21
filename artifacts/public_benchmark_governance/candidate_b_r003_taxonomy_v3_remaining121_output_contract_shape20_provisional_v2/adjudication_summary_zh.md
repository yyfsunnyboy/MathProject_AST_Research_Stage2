# AI-assisted provisional adjudication summary v2（output/contract-shape 20-cell）

**狀態：`AI_ASSISTED_PROVISIONAL_ADJUDICATION_NOT_FORMAL_HUMAN_REVIEW`**

本 revision **不是** ground truth、formal human review 或 Healer 驗證；**尚未凍結**。

## 相對 v1 的修訂範圍

- 僅套用 post-adjudication audit 核准的 **4 個 cell-field changes**（Mbpp/237×2）。
- `healer_eligibility`: conditional → abstain（2 格）
- `abstain_reason`: 對齊 abstain 理由（2 格）
- primary / secondary / mechanism / failure_chain / outcome / confidence / citations / identity **未改**
- provisional v1 保持逐 byte 不變

## 母體

- cells=20
- unique program_id=20
- unique source_sha256=20
- unique task_id=13
- 20 cells are 20 source-level evidence units across 13 tasks; do not describe as 20 independent tasks.

## Primary layer

| Layer | Cells |
|---|---:|
| `L2` | 1 |
| `L5` | 7 |
| `UNRESOLVED` | 12 |

- UNRESOLVED=12（全部 abstain）

## Healer eligibility

- {'abstain': 20}

## Outcome / Confidence

- outcome_validity：{'VALID_MODEL_OUTCOME': 20}
- confidence：{'HIGH': 8, 'LOW': 12}

## Sufficient 定義澄清（見 pre_audit_sufficiency_clarification_zh.md）

- pre-audit `sufficient` = 足以進行合法裁決（含 UNRESOLVED）
- `sufficient` ≠ 足以閉合至 L2/L3/L4/L5
- 12 格 UNRESOLVED：11 來自 sufficient、1 來自 conditional；不得再描述為「新增 7 格」
