# Gemini Ab2d-local qualification summary

- condition: Ab2d-local
- model: gemini-3.5-flash
- seed: 20260714
- task_count: 4
- cloud_qualified: False

| task_family | evaluable | oracle_pass | evaluation_status | failure_category |
|---|---:|---:|---|---|
| polynomial_division_quotient_remainder | True | True | None | None |
| largest_proper_divisor_reasoning | True | True | None | None |
| rpm_circumference_to_kph | True | True | None | None |
| alternating_training_progression_threshold | False | False | None | extraction_failure |