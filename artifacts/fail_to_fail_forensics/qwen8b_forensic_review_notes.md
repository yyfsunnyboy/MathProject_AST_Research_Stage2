# Qwen8B fail→fail forensic review notes

Draft input: `qwen8b_forensic_classified_draft.csv` (not overwritten).
Reviewed output: `qwen8b_forensic_reviewed.csv`.

## Scope reviewed

- All `code_changed=true`: **83**
- Specials: Mbpp/279, Mbpp/732
- `missing_program` (3): Mbpp/16, Mbpp/233, Mbpp/732
- `multiple_errors` (1): Mbpp/260
- Special `rules_triggered` (regex/antidup/pre.fence/empty_output_reverted): **9**
  - `qwen8b_mbpp_Mbpp_113__s0` rules=`regex;ast` → why=wrong_transformation, elig=eligible
  - `qwen8b_mbpp_Mbpp_16__s0` rules=`pre.fence;regex;ast` → why=missing_program, elig=ineligible
  - `qwen8b_mbpp_Mbpp_255__s0` rules=`pre.fence;regex;ast` → why=wrong_transformation, elig=eligible
  - `qwen8b_mbpp_Mbpp_260__s0` rules=`ast;antidup` → why=multiple_errors, elig=ineligible
  - `qwen8b_mbpp_Mbpp_267__s0` rules=`ast;antidup` → why=semantic_error, elig=ineligible
  - `qwen8b_mbpp_Mbpp_278__s0` rules=`ast;antidup` → why=semantic_error, elig=ineligible
  - `qwen8b_mbpp_Mbpp_279__s0` rules=`ast;antidup` → why=wrong_transformation, elig=eligible
  - `qwen8b_mbpp_Mbpp_722__s0` rules=`regex;ast` → why=wrong_transformation, elig=eligible
  - `qwen8b_mbpp_Mbpp_732__s0` rules=`ast;post.empty_output_reverted` → why=missing_program, elig=uncertain
- `code_changed=false` random sample (seed=20260714): **10**
  - `qwen8b_humaneval_HumanEval_115__s0` draft=semantic_error/ineligible → reviewed=semantic_error/ineligible
  - `qwen8b_humaneval_HumanEval_134__s0` draft=semantic_error/ineligible → reviewed=semantic_error/ineligible
  - `qwen8b_humaneval_HumanEval_142__s0` draft=semantic_error/ineligible → reviewed=semantic_error/ineligible
  - `qwen8b_humaneval_HumanEval_163__s0` draft=semantic_error/ineligible → reviewed=semantic_error/ineligible
  - `qwen8b_mbpp_Mbpp_124__s0` draft=semantic_error/ineligible → reviewed=semantic_error/ineligible
  - `qwen8b_mbpp_Mbpp_306__s0` draft=semantic_error/ineligible → reviewed=semantic_error/ineligible
  - `qwen8b_mbpp_Mbpp_453__s0` draft=semantic_error/ineligible → reviewed=semantic_error/ineligible
  - `qwen8b_mbpp_Mbpp_603__s0` draft=semantic_error/ineligible → reviewed=semantic_error/ineligible
  - `qwen8b_mbpp_Mbpp_72__s0` draft=semantic_error/ineligible → reviewed=semantic_error/ineligible
  - `qwen8b_mbpp_Mbpp_79__s0` draft=semantic_error/ineligible → reviewed=semantic_error/ineligible

**Total cases with any classification-field edit:** 87 / 154
**why_fail_to_fail label flips:** 59
**eligibility label flips:** 18

## Change-kind census (all 154)

- `unchanged`: 71
- `cosmetic_same_ast`: 62
- `import_strip`: 9
- `xor_to_pow`: 4
- `safety_loop`: 2
- `dup_identical_plus_safety`: 1
- `dup_keep_first`: 1
- `import_spam_cleanup`: 1
- `math_scaffold_inject`: 1
- `sign_charset_narrow`: 1
- `wrong_extraction`: 1

## Distributions

### eligibility

| value | draft | reviewed |
|---|---:|---:|
| eligible | 1 | 18 |
| ineligible | 152 | 134 |
| uncertain | 1 | 2 |

### why_fail_to_fail

| value | draft | reviewed |
|---|---:|---:|
| missing_program | 3 | 3 |
| multiple_errors | 1 | 1 |
| semantic_error | 73 | 132 |
| wrong_transformation | 77 | 18 |

## Key finding: draft over-labeled wrong_transformation

Draft marked **77/83** `code_changed=true` cases as `wrong_transformation`. Review found **62** cases with identical `ast.dump` (format-only). Per rule 「純格式變動且未造成新錯誤 → semantic_error」, those were reclassified to `semantic_error`.

## Hard wrong_transformation clusters (kept / tightened)

### 1) BitXor `^` → Pow `**` (eligible)
- `qwen8b_mbpp_Mbpp_311__s0`: fail: base=fail,plus=fail → fail: base=fail,plus=fail; elig=eligible
- `qwen8b_mbpp_Mbpp_633__s0`: fail: base=pass,plus=fail → fail: base=fail,plus=fail; elig=eligible
- `qwen8b_mbpp_Mbpp_6__s0`: fail: base=pass,plus=fail → fail: base=fail,plus=fail; elig=eligible
- `qwen8b_mbpp_Mbpp_735__s0`: fail: base=fail,plus=fail → fail: base=fail,plus=fail; elig=eligible

### 2) Referenced import stripped (eligible)
- `qwen8b_humaneval_HumanEval_129__s0`: fail: base=fail,plus=fail → fail: base=fail,plus=fail; elig=eligible
- `qwen8b_mbpp_Mbpp_108__s0`: fail: base=fail,plus=fail → fail: base=fail,plus=fail; elig=eligible
- `qwen8b_mbpp_Mbpp_237__s0`: fail: base=fail,plus=fail → fail: base=fail,plus=fail; elig=eligible
- `qwen8b_mbpp_Mbpp_255__s0`: fail: base=pass,plus=fail → fail: base=fail,plus=fail; elig=eligible
- `qwen8b_mbpp_Mbpp_410__s0`: fail: base=pass,plus=fail → fail: base=fail,plus=fail; elig=eligible
- `qwen8b_mbpp_Mbpp_462__s0`: fail: base=fail,plus=fail → fail: base=fail,plus=fail; elig=eligible
- `qwen8b_mbpp_Mbpp_597__s0`: fail: base=fail,plus=fail → fail: base=fail,plus=fail; elig=eligible
- `qwen8b_mbpp_Mbpp_620__s0`: fail: base=fail,plus=fail → fail: base=fail,plus=fail; elig=eligible
- `qwen8b_mbpp_Mbpp_777__s0`: fail: base=fail,plus=fail → fail: base=fail,plus=fail; elig=eligible

### 3) Safety-loop rewrite (eligible except Mbpp/260 mixed)
- `qwen8b_humaneval_HumanEval_39__s0`: why=wrong_transformation, elig=eligible
- `qwen8b_mbpp_Mbpp_260__s0`: why=multiple_errors, elig=ineligible
- `qwen8b_mbpp_Mbpp_739__s0`: why=wrong_transformation, elig=eligible

### 4) Other kept wrong_transformation
- Mbpp/113: `'+-'` charset narrowed to `'-'` (eligible)
- Mbpp/722: math-scaffold injection into MBPP solution (eligible)
- Mbpp/279: antidup kept first/wrong def instead of last/corrected (eligible)

## Mbpp/279 duplicate-function deep dive

Raw:
1. `is_num_decagonal` wrong (`==27`)
2. `nth_decagonal_number`
3. `is_num_decagonal` corrected inverse formula
4. `nth_decagonal_number` (identical)

- At runtime Python would use the **last** `is_num_decagonal` (corrected), but worker_error blocks execution because entry_point count=2.
- Healer antidup deleted the **later** corrected def and kept the **first** wrong def → semantic destruction relative to Python shadowing semantics.
- Classification remains **`wrong_transformation` + `eligible`** (keep-LAST rule).

### Can keep-LAST be generalized?

Across all 154 Qwen8B fail→fail raw sources, top-level duplicate defs found:
- `qwen8b_mbpp_Mbpp_260__s0` dups=['newman_prime'] identical_bodies={'newman_prime': True}
- `qwen8b_mbpp_Mbpp_279__s0` dups=['is_num_decagonal', 'nth_decagonal_number'] identical_bodies={'is_num_decagonal': False, 'nth_decagonal_number': True}

Only **Mbpp/279** has non-identical duplicate bodies. Mbpp/260 duplicates are identical (keep first or last equivalent for behavior). Therefore keep-LAST is still a **rule candidate**, strongly motivated by Python shadowing + this self-correction pattern, but divergent-body empirical support in this cell is **N=1**.

## missing_program / multiple_errors

- `qwen8b_mbpp_Mbpp_16__s0`: why=missing_program, elig=ineligible, conf=high
  - root: Raw is catastrophic: truncated/repetitive text_lowercase_underscore bodies plus `</think>` leakage and a later unrelated helper. Healer fence/regex/ast extraction kept only is_ascii_and_printable (+ prints), so required entry_point remains undefined in both raw and healed.
- `qwen8b_mbpp_Mbpp_233__s0`: why=missing_program, elig=uncertain, conf=medium
  - root: Source (raw==healed) defines lateralsurface_cylinder (correct spelling) while the harness expects misspelled lateralsuface_cylinder; worker_error reports entry_point count=0. Healer did not rename.
- `qwen8b_mbpp_Mbpp_732__s0`: why=missing_program, elig=uncertain, conf=low
  - root: Source text contains def replace_specialchar but literal `str.maketrans(' ,.', '':':')` is syntactically garbled, so the module does not parse; worker reports entry_point count=0. AST healer produced empty output and post.empty_output_reverted restored the pre-heal input (code_changed=false).
- `qwen8b_mbpp_Mbpp_260__s0`: why=multiple_errors, elig=ineligible, conf=high
  - root: At least two independent residual problems: (1) identical duplicate newman_prime defs (antidup correctly collapsed them); (2) Healer still injected a safety-loop + `return (0, 0)` rewriting `while True`; (3) underlying NSW-prime formula/search remains incorrect, so tests still fail after dedup.

## Still needs human adjudication

- `qwen8b_mbpp_Mbpp_233__s0`: why=missing_program, elig=uncertain, conf=medium
  - candidate (needs adjudication): if exactly one top-level def and Levenshtein(name, expected_entry_point)<=2, rename to expected entry_point
- `qwen8b_mbpp_Mbpp_732__s0`: why=missing_program, elig=uncertain, conf=low
  - manual adjudication / richer traceback needed before claiming a deterministic string fix

## Reviewer method notes

- Compared raw/healed paths, normalized diffs, generation traces, official errors.
- Did not read reference solutions; did not run models / Healer / EvalPlus.
- Did not modify draft CSV.
