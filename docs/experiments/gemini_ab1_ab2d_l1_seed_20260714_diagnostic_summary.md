# Gemini Ab1 vs Ab2d-v1 L1 diagnostic — 2026-07-14

| task_family | Gemini Ab1 outcome | Gemini Ab2d outcome |
|---|---|---|
| polynomial_division_quotient_remainder | passed | passed |
| largest_proper_divisor_reasoning | catastrophic_truncation | passed |
| rpm_circumference_to_kph | passed | passed |
| alternating_training_progression_threshold | parse_minor | parse_minor |

- Ab1 evaluable / 4: 2 / 4
- Ab1 oracle pass / 4: 2 / 4
- Ab2d evaluable / 4: 3 / 4
- Ab2d oracle pass / 4: 3 / 4
- Ab1 extraction/runtime/answer failures: {'extraction_failure': 0, 'runtime_failure': 0, 'answer_incorrect': 0}
- Ab2d extraction/runtime/answer failures: {'extraction_failure': 0, 'runtime_failure': 0, 'answer_incorrect': 0}
- Interpretation: Gemini Ab2d outperformed Ab1
