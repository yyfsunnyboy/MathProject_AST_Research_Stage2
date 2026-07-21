# Pre-adjudication adversarial audit（remaining121 output/contract-shape 20-cell）

**狀態：`PRE_ADJUDICATION_ADVERSARIAL_AUDIT_NOT_FORMAL_ADJUDICATION`**

**Audit verdict：`READY_FOR_20_CELL_AI_ASSISTED_PROVISIONAL_ADJUDICATION`**

## 固定 roster 驗證

- cells=20
- unique program_id=20
- unique source_sha256=20
- unique task_id=13
- processed77 交集=0
- condition 全為 Candidate_B/H0
- next_batch_roster SHA256=`b020499fdff42b94bcfc9efa1af0ad7011a59ad5c20184c7fc5468bcc3d1f804`

## 逐格證據充分性

| Sufficiency | Cells |
|---|---:|
| `sufficient` | 15 |
| `conditional` | 5 |
| `insufficient` | 0 |

## L2/L3/L4/L5 混淆風險

| Risk | Cells |
|---|---:|
| `HIGH` | 0 |
| `MEDIUM` | 5 |
| `LOW` | 15 |

## Hidden oracle 依賴

| Dependency | Cells |
|---|---:|
| `no` | 15 |
| `conditional` | 5 |
| `yes` | 0 |

## return_type 輪詢選樣偏差

| return_type | population_share | batch_share | note |
|---|---:|---:|---|
| `bool` | 26.1% | 15.0% | representative_or_under |
| `dict` | 4.2% | 10.0% | oversampled |
| `float` | 6.7% | 15.0% | oversampled |
| `int` | 26.1% | 10.0% | representative_or_under |
| `list` | 8.4% | 10.0% | representative_or_under |
| `mixed` | 11.8% | 10.0% | representative_or_under |
| `other` | 0.8% | 5.0% | representative_or_under |
| `set` | 1.7% | 10.0% | oversampled |
| `str` | 13.4% | 10.0% | representative_or_under |
| `tuple` | 0.8% | 5.0% | representative_or_under |

## 審查結論

- 20 格皆具完整 public prompt/spec、candidate source SHA、completed+return-shape 公開訊號。
- 現有證據僅證明「輸出形狀異常」，不足以直接鎖定 root cause；正式裁決必須允許 UNRESOLVED 與 abstain。
- L2 contract 與 L5 semantic incorrectness 最易混淆；不得將 return-shape mismatch 直接等同 L2 或 L5。
- duplicate task 但不同 source_sha256 仍視為不同 source-level evidence（6 個 task 在批內有多 source）。
- return_type 輪詢刻意 oversample 稀有型別（tuple/other/set/dict），bool/int 相對 under-sample；此偏差可接受但不得把 20 格描述為 20 個獨立 task。
- 未使用 hidden expected/actual、traceback 或重新執行程式。
