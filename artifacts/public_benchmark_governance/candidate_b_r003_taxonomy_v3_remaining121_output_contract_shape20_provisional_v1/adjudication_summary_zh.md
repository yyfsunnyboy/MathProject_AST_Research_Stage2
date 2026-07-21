# AI-assisted provisional adjudication summary（output/contract-shape 20-cell）

**狀態：`AI_ASSISTED_PROVISIONAL_ADJUDICATION_NOT_FORMAL_HUMAN_REVIEW`**

本 revision **不是** ground truth、formal human review 或 Healer 驗證。

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

- UNRESOLVED=12

## Secondary layer

| Layer | Mentions |
|---|---:|
| _(none)_ | 0 |

## Mechanism tags

| Tag | Mentions |
|---|---:|
| `binary_search_missing_final_return` | 1 |
| `complex_dp_without_public_trace` | 3 |
| `dedupe_instead_of_unique_occurrence` | 1 |
| `generator_instead_of_list` | 1 |
| `incorrect_surface_area_formula` | 2 |
| `incorrect_trapezium_median_formula` | 1 |
| `order_sensitive_counter` | 2 |
| `packaging_or_scaffold_residue` | 6 |
| `return_shape_observed` | 20 |

## Outcome validity / Healer / Confidence

- outcome_validity：{'VALID_MODEL_OUTCOME': 20}
- healer_eligibility：{'abstain': 18, 'conditional': 2}
- confidence：{'HIGH': 8, 'LOW': 12}

## 5 格 pre-audit conditional 對象處理

- Mbpp/603：`yield` vs public list → **L2**（contract），healer abstain
- Mbpp/119：public 追蹤回傳 None≠3 → **L5**，healer abstain
- Mbpp/237×2：order-insensitive Counter mismatch → **L5**，healer conditional
- Mbpp/103 seed55：mixed return / DP → **UNRESOLVED**，abstain

## 邊界

- 未執行 candidate / EvalPlus / diagnostics / validation / Healer / model
- 未查看 hidden expected/actual 或 traceback
- 適合作為 post-adjudication adversarial audit 輸入；**尚未凍結**
