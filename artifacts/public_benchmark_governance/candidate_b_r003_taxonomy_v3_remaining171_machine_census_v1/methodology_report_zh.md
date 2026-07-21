# Candidate B r003 taxonomy v3：remaining171 machine census v1

**明確聲明：`MACHINE_CENSUS_NOT_TAXONOMY_ADJUDICATION`**

本 revision 只建立不可變 fixed roster 與 deterministic machine census／operational clusters。
**尚未**完成 L0–L5 逐格裁決；cluster **不是** failure taxonomy；**尚未**判定 Healer eligibility。
未使用 hidden expected／actual，未使用 H1 結果選樣或反推，未進行 correctness 重評。

## 母體裁定

- 正式母體：taxonomy v3 unresolved **198**
  （`classification_preparation.csv` ≡ `coarse_diagnostics.csv`）
- 排除：`phase == G2_module` → **27**
- remaining fixed roster：**171**
- 開合：`198 = 27 + 171`
- 不納入 P0；不使用 H1 結果選樣；僅採用 unresolved198−G2_module=remaining171

## Phase 分布（171）

| Phase | Cells |
|---|---:|
| `G2_base` | 19 |
| `G2_plus` | 29 |
| `completed` | 121 |
| `infrastructure` | 2 |

## Observed machine signals（非互斥）

| Signal | Cells |
|---|---:|
| `import_or_name_resolution_signal` | 7 |
| `missing_or_ambiguous_entry_point_signal` | 6 |
| `module_execution_exception_signal` | 48 |
| `no_decisive_machine_signal` | 2 |
| `output_or_contract_shape_signal` | 119 |
| `packaging_or_scaffold_residue_signal` | 38 |
| `test_execution_failure_signal` | 2 |

## Operational clusters（互斥工作佇列）

| Cluster | Cells |
|---|---:|
| `parse_or_compile_signal` | 0 |
| `missing_or_ambiguous_entry_point_signal` | 0 |
| `import_or_name_resolution_signal` | 0 |
| `module_execution_exception_signal` | 37 |
| `timeout_or_nontermination_signal` | 0 |
| `test_execution_failure_signal` | 0 |
| `output_or_contract_shape_signal` | 119 |
| `no_decisive_machine_signal` | 2 |
| `multiple_signal_chain` | 13 |

## 方法學邊界

- `primary_failure_layer`／`secondary_failure_layers`／`healer_eligibility` 欄位保留空白
- exception class／phase 不直接等同 taxonomy layer
- truncation 僅為 mechanism candidate
- import 區分 STDLIB 與 THIRD_PARTY_OR_LOCAL，不自動等同 Domain API
- 不執行模型、EvalPlus、diagnostics、validation、Healer
