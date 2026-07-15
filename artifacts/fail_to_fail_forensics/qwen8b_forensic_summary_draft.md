# Qwen3-8B Fail-to-Fail Forensic Classification Summary (Draft)

Total cases classified: **154 / 154**

## Eligibility census

- eligible: 1
- ineligible: 152
- uncertain: 1

By dataset:

| dataset | eligible | ineligible | uncertain |
|---|---|---|---|
| humaneval | 0 | 38 | 0 |
| mbpp | 1 | 114 | 1 |

## why_fail_to_fail distribution

- wrong_transformation: 77
- semantic_error: 73
- missing_program: 3
- multiple_errors: 1

## failure_layer distribution

- algorithmic_semantic: 150
- extraction: 1
- task_spec: 1
- structural_contract: 1
- syntax: 1

## classification_confidence distribution

- medium: 149
- high: 4
- low: 1

## code_changed vs eligibility

| code_changed | eligible | ineligible | uncertain |
|---|---|---|---|
| true | 1 | 82 | 0 |
| false | 0 | 70 | 1 |

## Per-rule breakdown (rules_triggered, split on ';')

| rule | total | eligible | ineligible | uncertain |
|---|---|---|---|---|
| ast | 153 | 1 | 151 | 1 |
| regex | 4 | 0 | 4 | 0 |
| antidup | 4 | 1 | 3 | 0 |
| pre.fence | 2 | 0 | 2 | 0 |
| (none) | 1 | 0 | 1 | 0 |
| post.empty_output_reverted | 1 | 0 | 0 | 1 |

## Safe-rule candidate cases (eligible = 1)

**Proposed rule:** candidate for new AST/antidup rule: when a top-level function name is defined more than once in the same module, keep the LAST definition (later definitions in Python already shadow earlier ones at runtime; LLM self-correction pattern means the later block is almost always the intended one), not the first
- qwen8b_mbpp_Mbpp_279__s0: Raw code defines is_num_decagonal twice: an incorrect first version (`n*(3*n-1)==27`, a hard-coded/wrong check) followed by a corrected second version using the proper decagonal-number inverse formula; antidup/AST healer collapsed the duplicate but kept the FIRST (wrong) definition instead of the LAST (self-corrected, intended) one

## Must-refuse cases (ineligible = 152)

Recurring failure categories (why_fail_to_fail among ineligible cases):

- wrong_transformation: 76
- semantic_error: 73
- missing_program: 2
- multiple_errors: 1

Full table (case_id, why_fail_to_fail, one-line reason):

| case_id | why_fail_to_fail | reason |
|---|---|---|
| qwen8b_humaneval_HumanEval_10__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_humaneval_HumanEval_103__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_humaneval_HumanEval_108__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_humaneval_HumanEval_113__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_humaneval_HumanEval_115__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_humaneval_HumanEval_117__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_humaneval_HumanEval_118__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_humaneval_HumanEval_119__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_humaneval_HumanEval_122__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_humaneval_HumanEval_129__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_humaneval_HumanEval_130__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_humaneval_HumanEval_132__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_humaneval_HumanEval_134__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_humaneval_HumanEval_135__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_humaneval_HumanEval_142__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_humaneval_HumanEval_144__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_humaneval_HumanEval_145__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_humaneval_HumanEval_154__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_humaneval_HumanEval_158__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_humaneval_HumanEval_163__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_humaneval_HumanEval_19__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_humaneval_HumanEval_22__s0 | semantic_error | healer applied a purely cosmetic/structural AST normalization (e.g. redundant-parenthesization or blank-line/whitespace adjustment) that doe... |
| qwen8b_humaneval_HumanEval_26__s0 | semantic_error | healer applied a purely cosmetic/structural AST normalization (e.g. redundant-parenthesization or blank-line/whitespace adjustment) that doe... |
| qwen8b_humaneval_HumanEval_32__s0 | semantic_error | healer applied a purely cosmetic/structural AST normalization (e.g. redundant-parenthesization or blank-line/whitespace adjustment) that doe... |
| qwen8b_humaneval_HumanEval_33__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_humaneval_HumanEval_39__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_humaneval_HumanEval_46__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_humaneval_HumanEval_54__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_humaneval_HumanEval_59__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_humaneval_HumanEval_65__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_humaneval_HumanEval_76__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_humaneval_HumanEval_81__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_humaneval_HumanEval_83__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_humaneval_HumanEval_91__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_humaneval_HumanEval_93__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_humaneval_HumanEval_96__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_humaneval_HumanEval_97__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_humaneval_HumanEval_99__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_102__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_103__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_108__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_11__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_113__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=regex;ast) but the change was insufficient or unrelated to the actual functional... |
| qwen8b_mbpp_Mbpp_118__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_119__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_123__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_124__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_125__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_126__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_137__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_138__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_14__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_16__s0 | missing_program | Model output contains leaked chain-of-thought ('</think>' marker) and a garbled, massively repetitive boolean expression; the healer's extra... |
| qwen8b_mbpp_Mbpp_162__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_20__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_223__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_232__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_233__s0 | missing_program | Raw and healed code correctly define lateralsurface_cylinder (correct spelling), but the benchmark's expected entry_point is the misspelled ... |
| qwen8b_mbpp_Mbpp_235__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_237__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_239__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_244__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_251__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_255__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=pre.fence;regex;ast) but the change was insufficient or unrelated to the actual ... |
| qwen8b_mbpp_Mbpp_259__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_260__s0 | multiple_errors | Raw code defines newman_prime twice (identical duplicate blocks); antidup collapsed the duplicate (resolving the worker_error) but the under... |
| qwen8b_mbpp_Mbpp_267__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_278__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_286__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_287__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_290__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_300__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_301__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_305__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_306__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_310__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_311__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_388__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_389__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_391__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_392__s0 | semantic_error | healer applied a purely cosmetic/structural AST normalization (e.g. redundant-parenthesization or blank-line/whitespace adjustment) that doe... |
| qwen8b_mbpp_Mbpp_398__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_406__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_410__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_415__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_419__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_420__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_422__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_427__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_430__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_432__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_435__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_440__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_448__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_451__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_453__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_462__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_468__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_473__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_559__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_572__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_576__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_577__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_581__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_589__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_590__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_593__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_597__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_6__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_602__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_603__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_607__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_608__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_610__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_615__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_620__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_622__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_626__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_63__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_630__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_631__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_633__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_639__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_67__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_72__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_721__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_722__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=regex;ast) but the change was insufficient or unrelated to the actual functional... |
| qwen8b_mbpp_Mbpp_735__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_737__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_739__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_742__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_743__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_748__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_752__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_759__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_765__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_769__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_771__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_777__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_780__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_781__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_786__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_787__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_79__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_790__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_792__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_794__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_801__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_806__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |
| qwen8b_mbpp_Mbpp_84__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_92__s0 | wrong_transformation | healer's AST layer modified code structure (rules_triggered=ast) but the change was insufficient or unrelated to the actual functional defec... |
| qwen8b_mbpp_Mbpp_99__s0 | semantic_error | raw code is syntactically well-formed and the healer made no changes (code_changed=false); the residual test failure reflects a pre-existing... |

## Uncertain cases (uncertain = 1)

| case_id | why evidence insufficient |
|---|---|
| qwen8b_mbpp_Mbpp_732__s0 | raw/healed identical: `return s.translate(str.maketrans(' ,.', '':':'))`; worker_error 'entry_point replace_specialchar 在 solution 中應恰好定義 1 次，實際 0 次' implies th... |

## Total case count confirmation

154/154 qwen3-8b fail-to-fail cases classified (38 humaneval + 116 mbpp).
