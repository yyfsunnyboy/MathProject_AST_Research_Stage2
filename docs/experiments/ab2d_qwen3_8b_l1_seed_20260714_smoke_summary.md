# Ab2d qwen3:8b L1 Minimal Smoke — 2026-07-14

One generation per required L1 family; retry=0 and Healer disabled.

| task_family | generation | extraction | evaluable | oracle_pass | failure_category |
|---|---|---|---|---|---|
| polynomial_division_quotient_remainder | done | extraction_failure | False | False | extraction_failure |
| largest_proper_divisor_reasoning | done | extraction_failure | False | False | extraction_failure |
| rpm_circumference_to_kph | done | passed | True | True | none |
| alternating_training_progression_threshold | done | answer_incorrect | True | False | answer_incorrect |

- Tasks attempted: 4
- Tasks completed: 4
- Evaluable: 2
- Oracle pass: 1
- Retry used: 0
- Healer used: no
- run_status: engineering_diagnostic_rerun
- prior_unrecorded_attempts: 2
- itt_first_attempt_claim: False


## 4B comparison

| task_family | 4B outcome | 8B outcome |
|---|---|---|
| polynomial_division_quotient_remainder | answer_incorrect | extraction_failure |
| largest_proper_divisor_reasoning | answer_incorrect | extraction_failure |
| rpm_circumference_to_kph | runtime_failure | passed |
| alternating_training_progression_threshold | answer_incorrect | answer_incorrect |

execution_timeout was added post-run as deterministic schema completion; no model output or outcome was changed.
