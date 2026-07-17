# Milestone 1D: Scaffold / Healer evidence review packet

## Scope and accounting

- Scope: frozen MBPP+ active development subset (20 tasks), run `mbpp_qwen35_9b_ab1_dev_run_003` only.
- Scaffold ledger: 100 generation cells.
- Verified Pipeline rescues: 30 Observed-fail / Pipeline-pass cells.
- Pipeline extraction failures: 21 cells.
- Pipeline-extracted / evaluation-fail: 49 cells.
- Healer evidence review: 70 Pipeline-fail cells across 19 tasks.

The 30 rescues are verified Pipeline correction outcomes, not Healer outcomes. No generation, evaluation, Scaffold construction, Healer construction, or evaluator-guided program edit was performed.

## Failure signature clusters

| Signature | Category | Cells | Tasks | Proposed action | Risk |
|---|---|---:|---:|---|---|
| `extraction_ambiguous_multiple_python_fences` | `extraction_or_format_failure` | 20 | 11 | `scaffold_only` | `low` |
| `extraction_ambiguous_other_fences` | `extraction_or_format_failure` | 1 | 1 | `scaffold_only` | `low` |
| `syntax_fstring_parse_error` | `syntax_failure` | 1 | 1 | `manual_review` | `high` |
| `syntax_unterminated_string` | `syntax_failure` | 2 | 1 | `manual_review` | `high` |
| `syntax_invalid_plain_text` | `syntax_failure` | 3 | 1 | `manual_review` | `high` |
| `entrypoint_unique_arity_compatible_candidate` | `missing_or_wrong_entry_point` | 16 | 7 | `healer_candidate` | `high` |
| `entrypoint_no_unique_candidate` | `missing_or_wrong_entry_point` | 1 | 1 | `manual_review` | `high` |
| `unknown_eval_failure_single_top_level_function` | `unknown` | 24 | 13 | `manual_review` | `high` |
| `unknown_eval_failure_multiple_top_level_functions` | `unknown` | 2 | 2 | `manual_review` | `high` |

## Human decisions required

Syntax errors remain manual-review items: a parse error does not establish a semantically safe edit. Entry-point cells are Healer candidates only when one top-level function exists, every model-visible positional call arity is accepted, and the proposed operation is name/alias-only without a function-body or control-flow rewrite.

### `syntax_fstring_parse_error`

- Cells: 1; unique tasks: 1
- Evidence: AST parser reports a saved f-string syntax error; syntax failure alone is not safe repair evidence
- Do not repair: do not rewrite an f-string unless intended interpolation and formatting semantics are independently established
- Representative cells: `5ec420e9306fc9694f324eede18e3a4b8211d16547c96f4513bded0f831c6236`

### `syntax_unterminated_string`

- Cells: 2; unique tasks: 1
- Evidence: AST parser reports an unterminated string literal; the intended continuation is not saved
- Do not repair: do not add a quote when the intended string boundary or truncated content is unknown
- Representative cells: `2c6144ec8aa6c99e467627f1a2d76937d47e6ea9e340d1206d465997fd792de8`, `c697f6a9d305bf1f36804d67fc7c58b1ee7298e5c09d874697e3d9b86123db16`

### `syntax_invalid_plain_text`

- Cells: 3; unique tasks: 1
- Evidence: plain_text extraction and AST parser invalid-syntax outcome are saved; semantic repair is unverified
- Do not repair: do not delete leading text as a Healer edit without proving the remaining payload is the unique intended program
- Representative cells: `ca7cc722b6b61f61457b1916bef7cc96a152845e1b2d39e8e374e322746ddf6f`, `d4e5f573460f264317b5f7ded27457d401f51bdb0b194d817e1405a71c316ef8`, `f848ad22e32a56a34e3b335bbf63656f5eb19bcbd7a0295082749e4caaa31619`

### `entrypoint_no_unique_candidate`

- Cells: 1; unique tasks: 1
- Evidence: expected entry point is absent and the unique arity-compatible candidate requirement is not met
- Do not repair: do not synthesize an entry point when there is no unique arity-compatible top-level function
- Representative cells: `5e1ddb942c589b3cd0704c1e70db1c93f0a175fb4c8d84e47ef350de174215d3`

### `unknown_eval_failure_single_top_level_function`

- Cells: 24; unique tasks: 13
- Evidence: compile passes and expected entry point exists, but saved EvalPlus outcome is generic failure with one top-level function
- Do not repair: do not repair from a generic evaluator failure; saved evidence does not distinguish assertion failure, import/name error, or runtime exception
- Representative cells: `a6ef147b860e80780abd4ae35e75c5793a57a3c2a7f6d00261e2054b935a893a`, `b7f13b1ba2c70c28e3ece359bcedf2468283e7151be4e3adb276df4f2f23ab74`, `3d7511e26f7c0c77d206c6412897c6145396f84c89b1854b07ebeed5292ede90`

### `unknown_eval_failure_multiple_top_level_functions`

- Cells: 2; unique tasks: 2
- Evidence: compile passes and expected entry point exists, but saved EvalPlus outcome is generic failure with multiple top-level functions
- Do not repair: do not delete, merge, or select functions based on evaluator failure; control-flow and binding intent are unresolved
- Representative cells: `0d84456a46e10c8225e58fad1b15ac72bba35b3e1bba016e773a879ace4b7de5`, `e8afb1f946e90ed24af7e5340816c48e8492bac5758c5db0e452ccfa75d48a1d`

## Candidate interpretation

- `scaffold_only`: 21 cells
- `healer_candidate`: 16 cells
- `manual_review`: 33 cells

Scaffold and Healer candidate labels are separate evidence annotations and may overlap conceptually. Neither label is a validated rule or authorization to modify a program.

Unknown evaluator failures default to manual review because saved diagnostics do not distinguish functional assertion failure, import/name failure, or runtime exception. Evaluator outcomes were not used to rewrite any program.
