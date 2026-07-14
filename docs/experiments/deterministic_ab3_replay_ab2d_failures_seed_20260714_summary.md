# Deterministic Ab3 replay of Ab2d failures — 2026-07-14

This engineering diagnostic calls the existing `derive_ab3()` once for each pre-extracted candidate. No model or Ollama request was made.

| source_model | task_family | pre_failure_type | applicability | healer_changed_source | post_evaluable | post_oracle_pass | repair_success | post_failure |
|---|---|---|---|---|---|---|---|---|
| qwen3:4b-instruct-2507-q4_K_M | polynomial_division_quotient_remainder | prompt_contract_misunderstanding | applicable | False | True | False | False | answer_incorrect |
| qwen3:4b-instruct-2507-q4_K_M | largest_proper_divisor_reasoning | model_logic_error | applicable | False | True | False | False | answer_incorrect |
| qwen3:4b-instruct-2507-q4_K_M | rpm_circumference_to_kph | runtime_or_api_misuse | applicable | False | True | False | False | runtime_failure |
| qwen3:4b-instruct-2507-q4_K_M | alternating_training_progression_threshold | model_logic_error | applicable | False | True | False | False | answer_incorrect |
| qwen3:8b | polynomial_division_quotient_remainder | extraction_and_schema_failure | not_applicable_pre_extraction | None | None | None | False | None |
| qwen3:8b | largest_proper_divisor_reasoning | extraction_and_schema_failure | not_applicable_pre_extraction | None | None | None | False | None |
| qwen3:8b | alternating_training_progression_threshold | model_logic_error | applicable | False | True | False | False | answer_incorrect |

## Counts

- Applicable cases: 5
- Not applicable pre-extraction: 2
- Successful repairs / applicable: 0 / 5
- No-op cases: 5
- Changed-but-still-failed cases: 0
- Contract/schema repairs: 0 / 1
- Runtime/API repairs: 0 / 1
- Model-logic repairs: 0 / 3

## Intervention boundary

`derive_ab3()` accepts a pre-existing source path and applies `UnifiedCleanupHealer` after extraction. It cannot intervene before extraction; the two 8B ambiguous-fence records therefore remain not applicable without selecting or rewriting a candidate.

`UnifiedCleanupHealer` is a structural cleanup pass. This replay records whether it changed each source and evaluates the result through the unchanged production sandbox and independent oracle; it does not supply a capability claim beyond these seven records.
