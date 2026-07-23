# Candidate B r003 198格失敗分類與Healer安全邊界統整報告

> 報告性質：由正式 frozen records 確定性重建的研究統整；不重新裁決、不執行 candidate、不使用隱藏測試或 oracle 答案。

## 一、研究摘要

本階段研究問題是：面對已失敗的 AI 生成 Python 程式，哪些錯誤能在不猜答案、不改演算法語意的前提下安全交給 deterministic Healer，哪些只能等待更多證據，哪些應拒絕修改？198格分類的目的，是把failure layer、具體 mechanism、證據解析度、責任歸因與 Healer disposition 分開記錄，建立可稽核的安全邊界。研究重點不是要求每個失敗程式都能被修復。

- 資料直接顯示：198格已全部完成治理閉合；program與cell各198個，source為155個，remaining為0。
- 資料直接顯示：最多的primary為`L4`；L5為54格（27.3%），UNRESOLVED為67格（33.8%）。
- 資料直接顯示：Healer eligible=0、conditional=23、abstain=175；這是安全門檻的裁決分布，不是修復執行成敗。
- 資料直接顯示：VALID_MODEL_OUTCOME=198格（100.0%）；outcome validity與failure layer是兩個不同維度。
- 資料直接顯示：`algorithm_reconstruction_required`出現31格；這些個案不可稱為deterministic Healer的局部修復。
- 合理解釋：source只有155個而cell/program各有198個，反映相同生成來源可依法形成不同seed、條件或治理cell；共享source不等於重複cell。

## 二、資料與實驗單位

正式集合為N=198個cell、198個program、155個source與50個task。集合關係為198=177+21，duplicate program=0、duplicate cell=0、omission=0、remaining=0。

### Benchmark分布

分母：N=198。

| 類別 | N | 百分比 |
|---|---:|---:|
| `HumanEval+` | 0 | 0.0% |
| `MBPP+` | 198 | 100.0% |

### 正式條件分布

分母：N=198。

| 類別 | N | 百分比 |
|---|---:|---:|
| `Candidate_B/H0` | 198 | 100.0% |
| `Candidate_B/H1` | 0 | 0.0% |

### Seed分布

分母：N=198。

| 類別 | N | 百分比 |
|---|---:|---:|
| `11` | 37 | 18.7% |
| `22` | 40 | 20.2% |
| `33` | 41 | 20.7% |
| `44` | 37 | 18.7% |
| `55` | 43 | 21.7% |

資料直接顯示：正式 frozen records 中沒有 scaffold-like 欄位；recorded N=0、unrecorded N=198，因此本報告不事後推定Scaffold-like／非Scaffold-like，也不做該交叉比較。

同source多cell共有25組，涉及68格。合法原因是研究單位是cell，cell identity還包含task、seed、condition或治理身分；source相同不會抹除不同cell/program身分。Candidate B r003位於生成後的development replay、保存評測結果、靜態taxonomy裁決與Healer安全門檻之間；本報告不是新的validation或confirmatory run。

## 三、分類方法

- L0：研究基礎設施或pipeline失敗，通常不能公平歸因模型。
- L1：無法取得唯一可解析candidate，或Python語法／AST建立失敗。
- L2：可解析但違反明文contract，例如entry point、signature或output packaging。
- L3：明文Domain API／tool-use／required assembly契約的誤用。
- L4：不存在更早L2/L3阻斷時的一般runtime、control-flow或assembly失敗。
- L5：可解析、可執行且介面成立，但答案、公式、邊界或演算法錯誤。
- UNRESOLVED：已完成審查，但合法靜態證據不足以閉合至單一L0–L5；它不是L6，也不是PENDING_REVIEW。

`primary`是互斥的最早可證明主層；`secondary`保留後續可證明層。`confidence`描述裁決把握度，`outcome_validity`描述結果能否公平歸因模型，兩者都不能代替failure layer。`failure_chain`按順序保存暴露路徑，`mechanism_tags`則可多選並跨層。

Truncation只是一個跨層mechanism：截斷後無法解析才是L1；若entry point缺失可能是L2，runtime資料流缺失可能是L4，可執行但內容不完整可能是L5。Entry-point根因固定歸L2，但只有唯一結構相容候選與唯一alias／rename／薄wrapper，且不改主體與資料流時，才可能eligible。

Healer `eligible`要求唯一、局部、deterministic、answer-free、task-agnostic、invariant-supported、tested、frozen、evaluator-blind與可重評估；`conditional`表示明確guard尚待閉合；其他一律`abstain`。隱藏測試、Plus failure或oracle答案不得反推出修法。修後PASS屬於Healer outcome，不會改寫raw failure classification。

## 四、198格完整統計

### Primary failure layer

分母：N=198。

| 類別 | N | 百分比 |
|---|---:|---:|
| `L0` | 0 | 0.0% |
| `L1` | 0 | 0.0% |
| `L2` | 7 | 3.5% |
| `L3` | 0 | 0.0% |
| `L4` | 70 | 35.4% |
| `L5` | 54 | 27.3% |
| `UNRESOLVED` | 67 | 33.8% |

### Secondary failure layers

分母：N=198；empty=154 (77.8%)。Secondary可多選，因此各層百分比不要求加總為100.0%。

| Secondary layer | N | 百分比 |
|---|---:|---:|
| `L4` | 2 | 1.0% |
| `L5` | 42 | 21.2% |

### Confidence

分母：N=198。

| 類別 | N | 百分比 |
|---|---:|---:|
| `HIGH` | 126 | 63.6% |
| `MEDIUM` | 5 | 2.5% |
| `LOW` | 67 | 33.8% |

### Outcome validity

分母：N=198。

| 類別 | N | 百分比 |
|---|---:|---:|
| `VALID_MODEL_OUTCOME` | 198 | 100.0% |
| `INVALID_EVALUATOR` | 0 | 0.0% |
| `INVALID_CONTRACT` | 0 | 0.0% |
| `INVALID_INFRASTRUCTURE` | 0 | 0.0% |
| `PENDING_REVIEW` | 0 | 0.0% |

### Healer disposition

分母：N=198。

| 類別 | N | 百分比 |
|---|---:|---:|
| `eligible` | 0 | 0.0% |
| `conditional` | 23 | 11.6% |
| `abstain` | 175 | 88.4% |

### Mechanism tags完整分布

分母：N=198格。每格可有多個active tag，百分比不互斥；帶`REJECTED`狀態的假說不計入已成立mechanism。

| Mechanism tag | N | 佔198格 |
|---|---:|---:|
| `diagnostic_execution_required` | 49 | 24.7% |
| `public_examples_non_discriminating` | 49 | 24.7% |
| `module_execution_exception` | 48 | 24.2% |
| `plus_failure_not_localized` | 38 | 19.2% |
| `algorithm_reconstruction_required` | 31 | 15.7% |
| `module_level_executable_assertion` | 28 | 14.1% |
| `model_assembly_failure` | 27 | 13.6% |
| `algorithmic_error` | 21 | 10.6% |
| `return_shape_mismatch` | 20 | 10.1% |
| `return_shape_observed` | 20 | 10.1% |
| `semantic_goal_drift` | 17 | 8.6% |
| `incorrect_formula` | 14 | 7.1% |
| `packaging_or_scaffold_residue` | 14 | 7.1% |
| `mathematical_error` | 8 | 4.0% |
| `wrong_boundary_condition` | 8 | 4.0% |
| `control_flow_failure` | 7 | 3.5% |
| `explicit_value_error_guard` | 7 | 3.5% |
| `unbound_name` | 7 | 3.5% |
| `duplicate_definition_override` | 6 | 3.0% |
| `edge_case_omission` | 6 | 3.0% |
| `memory_error` | 6 | 3.0% |
| `aggregation_axis_mismatch` | 5 | 2.5% |
| `combinatorial_explosion` | 5 | 2.5% |
| `duplicate_value_semantics` | 5 | 2.5% |
| `extra_wrapper_or_output` | 5 | 2.5% |
| `stdlib_complex_type_incompatibility` | 5 | 2.5% |
| `strict_inequality_boundary` | 5 | 2.5% |
| `unbound_name_stats` | 5 | 2.5% |
| `zero_division` | 5 | 2.5% |
| `incorrect_ordering_semantics` | 4 | 2.0% |
| `median_index_error` | 4 | 2.0% |
| `merge_logic_error` | 4 | 2.0% |
| `negative_number_boundary` | 4 | 2.0% |
| `output_schema_mismatch` | 4 | 2.0% |
| `sublist_semantics_ambiguous` | 4 | 2.0% |
| `capital_boundary_detection_error` | 3 | 1.5% |
| `complex_dp_without_public_trace` | 3 | 1.5% |
| `dual_delete_bug` | 3 | 1.5% |
| `formula_mismatch` | 3 | 1.5% |
| `frequency_one_instead_of_distinct_value` | 3 | 1.5% |
| `incorrect_pair_domain` | 3 | 1.5% |
| `index_invalidation` | 3 | 1.5% |
| `order_sensitive_counter` | 3 | 1.5% |
| `parameter_semantics_swap` | 3 | 1.5% |
| `type_error` | 3 | 1.5% |
| `value_error_without_visible_guard` | 3 | 1.5% |
| `broken_collection_construction` | 2 | 1.0% |
| `complex_sqrt_path` | 2 | 1.0% |
| `date_normalization_boundary` | 2 | 1.0% |
| `dedupe_instead_of_unique_occurrence` | 2 | 1.0% |
| `element_type_counting_semantics` | 2 | 1.0% |
| `expression_character_domain` | 2 | 1.0% |
| `incorrect_search_bound` | 2 | 1.0% |
| `incorrect_surface_area_formula` | 2 | 1.0% |
| `multiple_plausible_root_causes` | 2 | 1.0% |
| `partition_error` | 2 | 1.0% |
| `precision_validation_error` | 2 | 1.0% |
| `public_example_non_discriminating` | 2 | 1.0% |
| `runtime_vs_semantic_not_closed` | 2 | 1.0% |
| `schema_mismatch` | 2 | 1.0% |
| `task_semantics_misread_as_membership_predicate` | 2 | 1.0% |
| `wrong_parameter_semantics` | 2 | 1.0% |
| `algorithmic_logic_error` | 1 | 0.5% |
| `binary_search_missing_final_return` | 1 | 0.5% |
| `binary_search_pair_alignment_error` | 1 | 0.5% |
| `code_bloat` | 1 | 0.5% |
| `decimal_precision_boundary` | 1 | 0.5% |
| `decimal_validation_expression_error` | 1 | 0.5% |
| `diagnostic_infrastructure_failure` | 1 | 0.5% |
| `difference_of_squares_condition_error` | 1 | 0.5% |
| `embedded_assert_contract_drift` | 1 | 0.5% |
| `end_index_off_by_one` | 1 | 0.5% |
| `exception_swallowed_to_wrong_answer` | 1 | 0.5% |
| `generator_instead_of_list` | 1 | 0.5% |
| `hardcoded_public_example` | 1 | 0.5% |
| `incorrect_recurrence` | 1 | 0.5% |
| `incorrect_trapezium_median_formula` | 1 | 0.5% |
| `index_error` | 1 | 0.5% |
| `lowercase_letter_class_underconstrained` | 1 | 0.5% |
| `mixed_type_comparison_exception` | 1 | 0.5% |
| `nontermination` | 1 | 0.5% |
| `numeric_domain_boundary` | 1 | 0.5% |
| `pairwise_divisibility_nontransitive_dp` | 1 | 0.5% |
| `partition_index_error` | 1 | 0.5% |
| `predicate_instead_of_nth_value` | 1 | 0.5% |
| `runtime_type_error` | 1 | 0.5% |
| `second_parameter_semantics` | 1 | 0.5% |
| `self_recursive_override` | 1 | 0.5% |
| `state_invariant_broken` | 1 | 0.5% |
| `stdlib_regex_pattern_construction` | 1 | 0.5% |
| `test_execution_failure_signal` | 1 | 0.5% |
| `text_parsing_control_flow_failure` | 1 | 0.5% |
| `tuple_pair_normalization_omitted` | 1 | 0.5% |
| `unsupported_input_guard` | 1 | 0.5% |
| `wrong_aggregation_operator` | 1 | 0.5% |
| `xor_accumulate_instead_of_sum` | 1 | 0.5% |

### Failure-chain主要型態

非空chain=198 (100.0%)。

| Primary／secondary型態 | N | 百分比 |
|---|---:|---:|
| `L2` | 1 | 0.5% |
| `L2 + secondary L4` | 2 | 1.0% |
| `L2 + secondary L5` | 4 | 2.0% |
| `L4` | 32 | 16.2% |
| `L4 + secondary L5` | 38 | 19.2% |
| `L5` | 54 | 27.3% |
| `UNRESOLVED` | 67 | 33.8% |

### 指定機制族群（非互斥）

| 族群 | N | 百分比 |
|---|---:|---:|
| `truncation` | 0 | 0.0% |
| `entry_point` | 0 | 0.0% |
| `import_or_dependency` | 0 | 0.0% |
| `syntax_or_extraction` | 0 | 0.0% |
| `runtime_or_assembly` | 80 | 40.4% |
| `semantic_or_algorithm` | 109 | 55.1% |

`algorithm_reconstruction_required`=31；truncation／possible_truncation=0；entry-point相關=0；import/dependency相關=0；syntax/extraction相關=0；runtime/assembly相關=80；semantic/algorithm相關=109。這些mechanism族群可重疊，不得相加成198。

## 五、交叉分析

### Benchmark × Primary

| 分組（列分母） | L0 | L1 | L2 | L3 | L4 | L5 | UNRESOLVED |
|---|---:|---:|---:|---:|---:|---:|---:|
| `HumanEval+`（N=0） | NA | NA | NA | NA | NA | NA | NA |
| `MBPP+`（N=198） | 0 (0.0%) | 0 (0.0%) | 7 (3.5%) | 0 (0.0%) | 70 (35.4%) | 54 (27.3%) | 67 (33.8%) |

### Benchmark × Healer

| 分組（列分母） | eligible | conditional | abstain |
|---|---:|---:|---:|
| `HumanEval+`（N=0） | NA | NA | NA |
| `MBPP+`（N=198） | 0 (0.0%) | 23 (11.6%) | 175 (88.4%) |

### Condition × Primary

| 分組（列分母） | L0 | L1 | L2 | L3 | L4 | L5 | UNRESOLVED |
|---|---:|---:|---:|---:|---:|---:|---:|
| `Candidate_B/H0`（N=198） | 0 (0.0%) | 0 (0.0%) | 7 (3.5%) | 0 (0.0%) | 70 (35.4%) | 54 (27.3%) | 67 (33.8%) |
| `Candidate_B/H1`（N=0） | NA | NA | NA | NA | NA | NA | NA |

### Condition × Healer

| 分組（列分母） | eligible | conditional | abstain |
|---|---:|---:|---:|
| `Candidate_B/H0`（N=198） | 0 (0.0%) | 23 (11.6%) | 175 (88.4%) |
| `Candidate_B/H1`（N=0） | NA | NA | NA |

### Failure layer × Healer

| 分組（列分母） | eligible | conditional | abstain |
|---|---:|---:|---:|
| `L2`（N=7） | 0 (0.0%) | 0 (0.0%) | 7 (100.0%) |
| `L4`（N=70） | 0 (0.0%) | 23 (32.9%) | 47 (67.1%) |
| `L5`（N=54） | 0 (0.0%) | 0 (0.0%) | 54 (100.0%) |
| `UNRESOLVED`（N=67） | 0 (0.0%) | 0 (0.0%) | 67 (100.0%) |

### Confidence × Healer

| 分組（列分母） | eligible | conditional | abstain |
|---|---:|---:|---:|
| `HIGH`（N=126） | 0 (0.0%) | 20 (15.9%) | 106 (84.1%) |
| `LOW`（N=67） | 0 (0.0%) | 0 (0.0%) | 67 (100.0%) |
| `MEDIUM`（N=5） | 0 (0.0%) | 3 (60.0%) | 2 (40.0%) |

### Outcome validity × Failure layer

| 分組（列分母） | L0 | L1 | L2 | L3 | L4 | L5 | UNRESOLVED |
|---|---:|---:|---:|---:|---:|---:|---:|
| `VALID_MODEL_OUTCOME`（N=198） | 0 (0.0%) | 0 (0.0%) | 7 (3.5%) | 0 (0.0%) | 70 (35.4%) | 54 (27.3%) | 67 (33.8%) |

### Mechanism × Healer

| Mechanism（列分母） | eligible | conditional | abstain |
|---|---:|---:|---:|
| `aggregation_axis_mismatch`（N=5） | 0 (0.0%) | 0 (0.0%) | 5 (100.0%) |
| `algorithm_reconstruction_required`（N=31） | 0 (0.0%) | 0 (0.0%) | 31 (100.0%) |
| `algorithmic_error`（N=21） | 0 (0.0%) | 12 (57.1%) | 9 (42.9%) |
| `algorithmic_logic_error`（N=1） | 0 (0.0%) | 0 (0.0%) | 1 (100.0%) |
| `binary_search_missing_final_return`（N=1） | 0 (0.0%) | 0 (0.0%) | 1 (100.0%) |
| `binary_search_pair_alignment_error`（N=1） | 0 (0.0%) | 0 (0.0%) | 1 (100.0%) |
| `broken_collection_construction`（N=2） | 0 (0.0%) | 0 (0.0%) | 2 (100.0%) |
| `capital_boundary_detection_error`（N=3） | 0 (0.0%) | 0 (0.0%) | 3 (100.0%) |
| `code_bloat`（N=1） | 0 (0.0%) | 0 (0.0%) | 1 (100.0%) |
| `combinatorial_explosion`（N=5） | 0 (0.0%) | 0 (0.0%) | 5 (100.0%) |
| `complex_dp_without_public_trace`（N=3） | 0 (0.0%) | 0 (0.0%) | 3 (100.0%) |
| `complex_sqrt_path`（N=2） | 0 (0.0%) | 0 (0.0%) | 2 (100.0%) |
| `control_flow_failure`（N=7） | 0 (0.0%) | 4 (57.1%) | 3 (42.9%) |
| `date_normalization_boundary`（N=2） | 0 (0.0%) | 0 (0.0%) | 2 (100.0%) |
| `decimal_precision_boundary`（N=1） | 0 (0.0%) | 0 (0.0%) | 1 (100.0%) |
| `decimal_validation_expression_error`（N=1） | 0 (0.0%) | 0 (0.0%) | 1 (100.0%) |
| `dedupe_instead_of_unique_occurrence`（N=2） | 0 (0.0%) | 0 (0.0%) | 2 (100.0%) |
| `diagnostic_execution_required`（N=49） | 0 (0.0%) | 0 (0.0%) | 49 (100.0%) |
| `diagnostic_infrastructure_failure`（N=1） | 0 (0.0%) | 0 (0.0%) | 1 (100.0%) |
| `difference_of_squares_condition_error`（N=1） | 0 (0.0%) | 0 (0.0%) | 1 (100.0%) |
| `dual_delete_bug`（N=3） | 0 (0.0%) | 0 (0.0%) | 3 (100.0%) |
| `duplicate_definition_override`（N=6） | 0 (0.0%) | 0 (0.0%) | 6 (100.0%) |
| `duplicate_value_semantics`（N=5） | 0 (0.0%) | 0 (0.0%) | 5 (100.0%) |
| `edge_case_omission`（N=6） | 0 (0.0%) | 3 (50.0%) | 3 (50.0%) |
| `element_type_counting_semantics`（N=2） | 0 (0.0%) | 0 (0.0%) | 2 (100.0%) |
| `embedded_assert_contract_drift`（N=1） | 0 (0.0%) | 0 (0.0%) | 1 (100.0%) |
| `end_index_off_by_one`（N=1） | 0 (0.0%) | 0 (0.0%) | 1 (100.0%) |
| `exception_swallowed_to_wrong_answer`（N=1） | 0 (0.0%) | 0 (0.0%) | 1 (100.0%) |
| `explicit_value_error_guard`（N=7） | 0 (0.0%) | 0 (0.0%) | 7 (100.0%) |
| `expression_character_domain`（N=2） | 0 (0.0%) | 0 (0.0%) | 2 (100.0%) |
| `extra_wrapper_or_output`（N=5） | 0 (0.0%) | 0 (0.0%) | 5 (100.0%) |
| `formula_mismatch`（N=3） | 0 (0.0%) | 0 (0.0%) | 3 (100.0%) |
| `frequency_one_instead_of_distinct_value`（N=3） | 0 (0.0%) | 0 (0.0%) | 3 (100.0%) |
| `generator_instead_of_list`（N=1） | 0 (0.0%) | 0 (0.0%) | 1 (100.0%) |
| `hardcoded_public_example`（N=1） | 0 (0.0%) | 0 (0.0%) | 1 (100.0%) |
| `incorrect_formula`（N=14） | 0 (0.0%) | 0 (0.0%) | 14 (100.0%) |
| `incorrect_ordering_semantics`（N=4） | 0 (0.0%) | 0 (0.0%) | 4 (100.0%) |
| `incorrect_pair_domain`（N=3） | 0 (0.0%) | 0 (0.0%) | 3 (100.0%) |
| `incorrect_recurrence`（N=1） | 0 (0.0%) | 0 (0.0%) | 1 (100.0%) |
| `incorrect_search_bound`（N=2） | 0 (0.0%) | 0 (0.0%) | 2 (100.0%) |
| `incorrect_surface_area_formula`（N=2） | 0 (0.0%) | 0 (0.0%) | 2 (100.0%) |
| `incorrect_trapezium_median_formula`（N=1） | 0 (0.0%) | 0 (0.0%) | 1 (100.0%) |
| `index_error`（N=1） | 0 (0.0%) | 0 (0.0%) | 1 (100.0%) |
| `index_invalidation`（N=3） | 0 (0.0%) | 0 (0.0%) | 3 (100.0%) |
| `lowercase_letter_class_underconstrained`（N=1） | 0 (0.0%) | 0 (0.0%) | 1 (100.0%) |
| `mathematical_error`（N=8） | 0 (0.0%) | 8 (100.0%) | 0 (0.0%) |
| `median_index_error`（N=4） | 0 (0.0%) | 0 (0.0%) | 4 (100.0%) |
| `memory_error`（N=6） | 0 (0.0%) | 0 (0.0%) | 6 (100.0%) |
| `merge_logic_error`（N=4） | 0 (0.0%) | 0 (0.0%) | 4 (100.0%) |
| `mixed_type_comparison_exception`（N=1） | 0 (0.0%) | 0 (0.0%) | 1 (100.0%) |
| `model_assembly_failure`（N=27） | 0 (0.0%) | 23 (85.2%) | 4 (14.8%) |
| `module_execution_exception`（N=48） | 0 (0.0%) | 0 (0.0%) | 48 (100.0%) |
| `module_level_executable_assertion`（N=28） | 0 (0.0%) | 23 (82.1%) | 5 (17.9%) |
| `multiple_plausible_root_causes`（N=2） | 0 (0.0%) | 0 (0.0%) | 2 (100.0%) |
| `negative_number_boundary`（N=4） | 0 (0.0%) | 0 (0.0%) | 4 (100.0%) |
| `nontermination`（N=1） | 0 (0.0%) | 0 (0.0%) | 1 (100.0%) |
| `numeric_domain_boundary`（N=1） | 0 (0.0%) | 0 (0.0%) | 1 (100.0%) |
| `order_sensitive_counter`（N=3） | 0 (0.0%) | 0 (0.0%) | 3 (100.0%) |
| `output_schema_mismatch`（N=4） | 0 (0.0%) | 0 (0.0%) | 4 (100.0%) |
| `packaging_or_scaffold_residue`（N=14） | 0 (0.0%) | 0 (0.0%) | 14 (100.0%) |
| `pairwise_divisibility_nontransitive_dp`（N=1） | 0 (0.0%) | 0 (0.0%) | 1 (100.0%) |
| `parameter_semantics_swap`（N=3） | 0 (0.0%) | 3 (100.0%) | 0 (0.0%) |
| `partition_error`（N=2） | 0 (0.0%) | 0 (0.0%) | 2 (100.0%) |
| `partition_index_error`（N=1） | 0 (0.0%) | 0 (0.0%) | 1 (100.0%) |
| `plus_failure_not_localized`（N=38） | 0 (0.0%) | 0 (0.0%) | 38 (100.0%) |
| `precision_validation_error`（N=2） | 0 (0.0%) | 0 (0.0%) | 2 (100.0%) |
| `predicate_instead_of_nth_value`（N=1） | 0 (0.0%) | 0 (0.0%) | 1 (100.0%) |
| `public_example_non_discriminating`（N=2） | 0 (0.0%) | 0 (0.0%) | 2 (100.0%) |
| `public_examples_non_discriminating`（N=49） | 0 (0.0%) | 0 (0.0%) | 49 (100.0%) |
| `return_shape_mismatch`（N=20） | 0 (0.0%) | 0 (0.0%) | 20 (100.0%) |
| `return_shape_observed`（N=20） | 0 (0.0%) | 0 (0.0%) | 20 (100.0%) |
| `runtime_type_error`（N=1） | 0 (0.0%) | 0 (0.0%) | 1 (100.0%) |
| `runtime_vs_semantic_not_closed`（N=2） | 0 (0.0%) | 0 (0.0%) | 2 (100.0%) |
| `schema_mismatch`（N=2） | 0 (0.0%) | 0 (0.0%) | 2 (100.0%) |
| `second_parameter_semantics`（N=1） | 0 (0.0%) | 0 (0.0%) | 1 (100.0%) |
| `self_recursive_override`（N=1） | 0 (0.0%) | 0 (0.0%) | 1 (100.0%) |
| `semantic_goal_drift`（N=17） | 0 (0.0%) | 5 (29.4%) | 12 (70.6%) |
| `state_invariant_broken`（N=1） | 0 (0.0%) | 0 (0.0%) | 1 (100.0%) |
| `stdlib_complex_type_incompatibility`（N=5） | 0 (0.0%) | 0 (0.0%) | 5 (100.0%) |
| `stdlib_regex_pattern_construction`（N=1） | 0 (0.0%) | 0 (0.0%) | 1 (100.0%) |
| `strict_inequality_boundary`（N=5） | 0 (0.0%) | 0 (0.0%) | 5 (100.0%) |
| `sublist_semantics_ambiguous`（N=4） | 0 (0.0%) | 0 (0.0%) | 4 (100.0%) |
| `task_semantics_misread_as_membership_predicate`（N=2） | 0 (0.0%) | 0 (0.0%) | 2 (100.0%) |
| `test_execution_failure_signal`（N=1） | 0 (0.0%) | 0 (0.0%) | 1 (100.0%) |
| `text_parsing_control_flow_failure`（N=1） | 0 (0.0%) | 0 (0.0%) | 1 (100.0%) |
| `tuple_pair_normalization_omitted`（N=1） | 0 (0.0%) | 0 (0.0%) | 1 (100.0%) |
| `type_error`（N=3） | 0 (0.0%) | 0 (0.0%) | 3 (100.0%) |
| `unbound_name`（N=7） | 0 (0.0%) | 0 (0.0%) | 7 (100.0%) |
| `unbound_name_stats`（N=5） | 0 (0.0%) | 0 (0.0%) | 5 (100.0%) |
| `unsupported_input_guard`（N=1） | 0 (0.0%) | 0 (0.0%) | 1 (100.0%) |
| `value_error_without_visible_guard`（N=3） | 0 (0.0%) | 0 (0.0%) | 3 (100.0%) |
| `wrong_aggregation_operator`（N=1） | 0 (0.0%) | 0 (0.0%) | 1 (100.0%) |
| `wrong_boundary_condition`（N=8） | 0 (0.0%) | 0 (0.0%) | 8 (100.0%) |
| `wrong_parameter_semantics`（N=2） | 0 (0.0%) | 0 (0.0%) | 2 (100.0%) |
| `xor_accumulate_instead_of_sum`（N=1） | 0 (0.0%) | 0 (0.0%) | 1 (100.0%) |
| `zero_division`（N=5） | 0 (0.0%) | 0 (0.0%) | 5 (100.0%) |

HumanEval+與H1的列分母為0時，表內百分比顯示NA；本資料不能據此比較benchmark或H0/H1效果。Scaffold-like欄位未正式記錄，該比較同樣NA。小樣本mechanism只做描述，不進行因果或泛化推論。

## 六、可修與不可修邊界

### 1. 可安全確定性修復

資料直接顯示：eligible=0格。
沒有eligible案例時，不能用本批宣稱Healer已有安全修復或verified rescue。

### 2. 需要額外診斷後才可能修復

資料直接顯示：conditional=23格。代表案例：
- `program=f85bb6c1efa6…`／`cell=077f1bf7c9d6…`／`Mbpp/125`：primary=`L4`、Healer=`conditional`；mechanism=`algorithmic_error`、`edge_case_omission`、`model_assembly_failure`、`module_level_executable_assertion`。
- `program=7738db7659ec…`／`cell=27db6ce43b7b…`／`Mbpp/739`：primary=`L4`、Healer=`conditional`；mechanism=`algorithmic_error`、`model_assembly_failure`、`module_level_executable_assertion`。
- `program=225def7e7fc2…`／`cell=2c8a29019edd…`／`Mbpp/581`：primary=`L4`、Healer=`conditional`；mechanism=`mathematical_error`、`model_assembly_failure`、`module_level_executable_assertion`。
Conditional不是已核准修復；只有原裁決要求的guard／契約證據閉合後，才可另建revision評估。

### 3. 應直接abstain

資料直接顯示：abstain=175格。代表案例：
- `program=7545d939bbed…`／`cell=0092d498eb44…`／`Mbpp/473`：primary=`L4`、Healer=`abstain`；mechanism=`broken_collection_construction`、`module_execution_exception`、`type_error`。
- `program=ece76238dc23…`／`cell=01382bbb873b…`／`Mbpp/721`：primary=`L5`、Healer=`abstain`；mechanism=`algorithm_reconstruction_required`、`incorrect_formula`。
- `program=fe973455ae8a…`／`cell=039cb0be9494…`／`Mbpp/722`：primary=`L4`、Healer=`abstain`；mechanism=`module_execution_exception`、`strict_inequality_boundary`、`unbound_name`、`unbound_name_stats`。

### 4. 需要重建演算法、不可稱為Healer修復

`algorithm_reconstruction_required`共31格。代表案例：
- `program=ece76238dc23…`／`cell=01382bbb873b…`／`Mbpp/721`：primary=`L5`、Healer=`abstain`；mechanism=`algorithm_reconstruction_required`、`incorrect_formula`。
- `program=bfa80269cd8a…`／`cell=0b022ac7499d…`／`Mbpp/103`：primary=`L5`、Healer=`abstain`；mechanism=`algorithm_reconstruction_required`、`incorrect_formula`。
- `program=578c5bf9895c…`／`cell=21c08b508eee…`／`Mbpp/769`：primary=`L5`、Healer=`abstain`；mechanism=`algorithm_reconstruction_required`、`incorrect_ordering_semantics`。
即使人工能寫出正確演算法，也不等於Healer完成唯一、局部、oracle-independent修復。

## 七、Scaffold與Healer的研究發現

Scaffold處理生成前約束；Healer處理生成後、已定位且修法唯一的局部錯誤。兩者不可合併計功，prompt/scaffold已避免的錯誤也不得再算Healer rescue。本198格沒有正式scaffold-like欄位，且eligible只有0格，因此對Scaffold效果與Healer實際rescue均尚無證據。本報告也不宣稱Healer能修復語意或演算法錯誤。

## 八、UNRESOLVED的意義

UNRESOLVED=67格（33.8%）。它不等於L5、不等於沒有錯誤，而是審查已完成但現有合法靜態證據不足以安全定位。代表案例：
- `program=b7f7b3ad0cd0…`／`cell=08b8b9d40d64…`／`Mbpp/244`：primary=`UNRESOLVED`、Healer=`abstain`；mechanism=`module_execution_exception`、`packaging_or_scaffold_residue`、`value_error_without_visible_guard`。
- `program=e46a657fce3e…`／`cell=106ea34c17e5…`／`Mbpp/473`：primary=`UNRESOLVED`、Healer=`abstain`；mechanism=`packaging_or_scaffold_residue`、`return_shape_observed`。
- `program=a63f9d97cba1…`／`cell=1df0c8bb6add…`／`Mbpp/287`：primary=`UNRESOLVED`、Healer=`abstain`；mechanism=`diagnostic_execution_required`、`plus_failure_not_localized`、`public_examples_non_discriminating`。
後續diagnostics應只取得能區分competing explanations的最小觀察，並預先登錄輸入與判準；尚未取得的診斷結果不能寫成既成結論。

## 九、研究限制

- 只涵蓋Candidate B r003；共同taxonomy可用於MBPP+與HumanEval+，但本198格實際只有MBPP+，不能做跨benchmark效果比較。
- 結果受單一model run、prompt、sampling seeds與development資料分布限制。
- 靜態taxonomy能保護不猜測原則，但動態diagnostics可能提供不同解析度；兩者證據不得混用。
- 25組多cell共享source，cell統計不是完全獨立source樣本；推論時不可把N=198當成155個以上互相獨立來源。
- 高中專題規模、AI-assisted與人工審查資源有限；早期legacy frozen schema與後期v3.1 schema細節不同，本報告只正規化欄位，不重裁決。
- abstain=175格是安全政策結果，不等於Healer已嘗試後失敗，因此abstain率不能直接解釋成Healer失敗率。

## 十、可直接用於成果報告的結論

### 正式學術版

本研究以Candidate B r003的198個正式凍結cell為分析單位，在198個program與155個unique source上，依taxonomy v3.1分離failure layer、mechanism、evidence resolution、outcome validity與Healer disposition。資料顯示VALID_MODEL_OUTCOME=198格，L5=54格，UNRESOLVED=67格；Healer eligible=0、conditional=23、abstain=175。結果支持「錯誤層級不等於可安全修復性」：只有根因已定位且修法唯一、局部、deterministic與oracle-independent時，才應考慮Healer介入；語意、演算法或證據未閉合個案應拒絕修改。此結論限於本development資料，不外推至所有LLM。

### 高中生口頭報告版

我們把198個失敗程式逐一分類，不只是問「錯在哪裡」，也問「電腦能不能在不偷看答案的情況下安全修」。結果有0個可以直接列為安全候選、23個還需要額外條件、175個應該先不要改。這表示好的Healer不是什麼都修，而是知道什麼時候證據不夠、應該停手。

## 十一、後續實驗（僅提出，不執行）

- 對UNRESOLVED格預先登錄最小diagnostics，再建立新證據revision。
- 依eligible十項規則建置deterministic Healer rule pack。
- 用frozen replay檢驗rescue、partial progress與regression。
- 將prompt／scaffold的生成前效果與Healer生成後效果分離。
- 進行跨模型與HumanEval+／MBPP+外部驗證。

## 十二、證據治理附錄

- 凍結鏈：legacy frozen97 → Batch01–04後frozen177 → Final Batch05 21格 → complete 198格。
- 集合：198=177+21；program=198、cell=198、source=155；overlap=0、duplicate=0、omission=0、remaining=0。
- Zero execution：model、candidate execution/import、public/hidden tests、EvalPlus、diagnostics、validation、Healer與programs executed均為0。
- Builder與targeted governance tests會重建summary與report並逐byte比較；百分比統一到小數點後1位，分母0顯示NA。
- Taxonomy SHA：`93908ec8e4721f0039acc779fb948988b6c25e712c29890bd98aa7c21a8422a0`。
- Complete ledger SHA：`7d18c8a04ef47ae3725feeb84636ec2f6fe46490367010851003618db1622bd3`。
- Complete manifest SHA：`749f19fb4464d1a17536d2fd55beae2e0771bdec72a8ddaf92b1364d8ea59b66`。
- Builder SHA：`c67148f5542427eaf601fc6c46eb0c929608eef3e5f58acc60f28a0e3ecc4a5e`。

### 權威檔案清單

| 路徑 | SHA-256 | Byte verified |
|---|---|---:|
| `C:/Users/yehya/Downloads/AI_生成程式共同失敗分類標準_實際使用版_v3.1.md` | `93908ec8e4721f0039acc779fb948988b6c25e712c29890bd98aa7c21a8422a0` | 是 |
| `artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v3_formal_classification_preparation_v1/classification_preparation.csv` | `5b0106b93f2d192d89c740659f83021956c15113397f1a54b70e65b7cc7a128c` | 是 |
| `artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/mbpp_q35_9b_candidate_b_development60_replay_r003/h0_h1_accounts.jsonl` | `b1313615bf41840bc1c45c36d2b8ac9b544f37fb5bb801c104aad1657ca2c2ec` | 是 |
| `artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_complete_198cell_closure_v1/complete_cumulative_frozen_identity_ledger.csv` | `7d18c8a04ef47ae3725feeb84636ec2f6fe46490367010851003618db1622bd3` | 是 |
| `artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_complete_198cell_closure_v1/manifest.json` | `749f19fb4464d1a17536d2fd55beae2e0771bdec72a8ddaf92b1364d8ea59b66` | 是 |
| `artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v3_g2_module_researcher_review_v1/researcher_review_worksheet.csv` | `38694d644d7916aa14a716bfbfdbdb1eaed4b1c2557865bde3aee1d215d2b820` | 是 |
| `artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v3_g2_module_researcher_review_v1/manifest.json` | `5e4c7d7c8704902086533cfba8d70b6a7d1382c303687e505481cfc456e68f53` | 是 |
| `artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v3_remaining171_module_exception_provisional_v1/ai_provisional_adjudication.csv` | `8b32d0561c0d42efe07c1bf89bd3bcaf4b7a42657f54bee25922f0be2aca6ab7` | 是 |
| `artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v3_remaining171_module_exception_provisional_v1/manifest.json` | `72b02ab7da59e65db2d5e09cee9344c3d52940a717ea3dfea05310e0529d76c1` | 是 |
| `artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v3_remaining134_multiple_signal_chain13_provisional_v1/ai_provisional_adjudication.csv` | `dc2e7202c048400d32e019fed6940051f65ca1a67b865727152d94dccf302d70` | 是 |
| `artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v3_remaining134_multiple_signal_chain13_provisional_v1/manifest.json` | `fd26fdbd103ad216e2a38c8e16b839c9e2b72a242e360713edee8d7762f59336` | 是 |
| `artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v3_remaining121_output_contract_shape20_frozen_v1/frozen_adjudication.csv` | `eda69f61051228ff9d976ec57f6dcd9febea95a2c541095edac19f55074eac1f` | 是 |
| `artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v3_remaining121_output_contract_shape20_frozen_v1/manifest.json` | `a9bc5d19e4a4aa4d3fde4db23a296cb1b2d32b9e51c6ebe9ace5c548691f8eab` | 是 |
| `artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_frozen_v1/frozen_adjudication.csv` | `8f2410122205610f41d4e7dfbbc4b958d05c1e3da40176b9dc9269880512c0cb` | 是 |
| `artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_frozen_v1/manifest.json` | `8cbed23b396ba7149fac485abf30160327ad6b483166ca22cccb3a6e1e4210ae` | 是 |
| `artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_batch02_20cell_frozen_v1/frozen_adjudication.csv` | `dc6d4a4fa0f0027eb87e3af48b3567c72443255fcda2e2779acf7fe0fbf70f04` | 是 |
| `artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_batch02_20cell_frozen_v1/manifest.json` | `41f8f76edf2669ee37494a03cf9d05ec0464bb7379d6ada58a6e2921fbeafee6` | 是 |
| `artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_batch03_20cell_frozen_v1/frozen_adjudication_records.csv` | `d0f59af50c2e433c7d02546da04a3d3802641077b75c649144f953f3c2b4d80f` | 是 |
| `artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_batch03_20cell_frozen_v1/manifest.json` | `af9becc880d45e6969074cf5e2e53e47a3b87b4cbf6a6ecab0cb4b69963f51d9` | 是 |
| `artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_batch04_20cell_frozen_v1/frozen_adjudication_records.csv` | `03cf83d8f295815f5f5f66dbdc3eb347556606245e542d052d88d0a50d945028` | 是 |
| `artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_batch04_20cell_frozen_v1/manifest.json` | `b56f1796c9b97bdbb854a5699dcdce38326c26300d9ad7bb8411c9d0499e5ea4` | 是 |
| `artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_final_batch05_21cell_frozen_v1/frozen_adjudication_records.csv` | `22faba56d483e172064338f2649533e4758bfd1110e64467d8ce6eff2a47cf34` | 是 |
| `artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_final_batch05_21cell_frozen_v1/manifest.json` | `f7d36575b55bb5dc9c3cb94458b0489c4dfcfa7ff99890927f844d5f56f32b9d` | 是 |

### 解讀層級

- **資料直接顯示**：summary與frozen records可逐格重建的數量、比例與交叉表。
- **合理解釋**：只描述本樣本的安全邊界與治理含義，不宣稱因果。
- **後續假設**：diagnostics、Healer replay與外部驗證尚未執行。

最終狀態：`READY_FOR_198CELL_REPORT_INDEPENDENT_AUDIT`
