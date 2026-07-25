# qwen06 H2 replay pipeline v1

Status: `H2_REPLAY_PIPELINE_WIRED_SMOKE_ONLY_NOT_FULL_ITT`

H2 is wired after the fixed extractor completion and before any evaluator. Conditions: Ab1-Raw, Ab1-H2, Ab2g-Raw, Ab2g-H2.

This packaging round only materializes synthetic smoke + preflight artifacts. Full 0.6B ITT H2 replay and EvalPlus are intentionally not executed here. H2 remains `development_candidate_not_frozen`.
