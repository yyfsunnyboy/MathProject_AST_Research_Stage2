# Candidate Healer / Healer-vNext counterfactual replay

## Outcome

Mbpp/279 is rescued in the isolated structural and runtime-semantics sense. The Candidate Healer removes the duplicate entry points while retaining the last module-level definitions, matching normal Python name-binding semantics. This is not an official EvalPlus or pass@1 result.

Original Ab3 retained the first `is_num_decagonal`, where `n=5` evaluates to false. Raw Python semantics bind the later inverse-formula definition, where `n=5` evaluates to true. The Candidate output retains that later AST and leaves exactly one `is_num_decagonal`.

## Census

The scan covered all 154 rows in `qwen8b_forensic_reviewed.csv`. A column-0 lexical census found three duplicate-function cases; two are AST-parseable and eligible for this rule:

- Mbpp/16: duplicate `text_lowercase_underscore`; the raw source does not parse, so the existing AST parse gate returns it unchanged and the candidate rule is not applied.
- Mbpp/260: duplicate `newman_prime`; bodies are identical, so keep-last is behaviorally equivalent to keep-first.
- Mbpp/279: duplicate `is_num_decagonal` bodies differ; duplicate `nth_decagonal_number` bodies are identical.

No other raw source contained column-0 duplicate functions. Three raw sources (Mbpp/16, Mbpp/255, and Mbpp/732) failed AST parsing; only Mbpp/16 had a lexical duplicate. No raw files were missing.

## Gates

The candidate rule applies only to module-level functions whose decorators are structurally consistent across all same-name definitions. Nested functions and class methods are not deduplicated. Decorator mismatch fails closed and preserves the source.

Duplicate-class handling and all non-duplicate Healer rules are unchanged.

## Regression Check

No regression was detected in the AST-eligible duplicate-function cohort. Mbpp/16 remains unchanged at the parse gate, and Mbpp/260 remains behaviorally equivalent because its duplicate bodies are identical. The targeted suite covers keep-last, identical bodies, different names, nested functions, class methods, decorator mismatch, the Mbpp/279 replay, and the full `derive_ab3` duplicate-function fixture path.

Validation result: 13 passed, 0 failed.

Official Ab3 files, official Excel files, and original pass@1 outputs were not modified. No model or EvalPlus run was performed.
