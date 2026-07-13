# CE115 Math Pilot Task Design

This pilot records four abstracted, externally anchored mathematics task specifications. It does not reproduce examination wording, diagrams, answer choices, or solutions verbatim.

| Task | Anchor | Domain | Oracle |
| --- | --- | --- | --- |
| `ce115_q07_polynomial_division` | Item 7 | polynomials | exact quotient and remainder |
| `ce115_q20_largest_proper_divisor` | Item 20 | number theory | finite necessity claims |
| `ce115_q24_rotation_speed_conversion` | Item 24 | measurement and linear relationships | exact Fraction conversion |
| `ce115_cr01_training_sequence_threshold` | Review item 1 | sequences and word problems | twice-weekly strict threshold crossing |

The manifest is immutable pilot input. It contains no fixed source-item numeric payload, model, treatment, prompt, Healer rule, generated code, or generated answer. Each task instead declares bounded `parameter_ranges`, a local seeded-RNG contract, and K12 hand-calculability constraints. A future generator must construct its own `oracle_payload` from those bounds and return it with the generated answer.

The randomization contract requires local seeded RNG use: the same seed must reproduce the same sampled parameters, while different seeds are expected to vary them. The constraints prohibit degenerate, ambiguous, oversized, or impractical values; they are metadata requirements for a future generator, not an implementation in this commit.

Each oracle operates only on a generated `oracle_payload` and a submitted answer; it neither imports generator code nor calls `generate()`.

All entries use `copyright_handling = abstracted_task_specification_not_verbatim_reproduction`. The sources are anchors for task-family provenance, not stored exam questions. This commit does not run generation, Healer derivation, evaluator execution, or a research batch.
