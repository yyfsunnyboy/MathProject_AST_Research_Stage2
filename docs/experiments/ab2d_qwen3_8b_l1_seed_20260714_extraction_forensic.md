# Ab2d 8B extraction-failure forensic — 2026-07-14

## Scope and method

This read-only review covers only the two `extraction_failure` records in
`docs/experiments/results/ab2d_qwen3_8b_l1_seed_20260714_smoke.jsonl`:
`polynomial_division_quotient_remainder` and
`largest_proper_divisor_reasoning`.  No model request, extraction rewrite,
candidate replay, evaluator run, or result-file modification was performed.

For each raw response, the existing `extract_code` function was called only to
inspect its reported structure.  Both raw responses contain exactly three
closed, `python`-labelled fences.  The extractor's declared winning priority is
the `python` fences; more than one winner returns `ambiguous`, with no selected
`candidate_extracted`.  This is intentionally fail-visible behavior, not an
AST or execution rejection.

## Task: polynomial_division_quotient_remainder

**Task:** `ce115_q07_polynomial_division_l1` / `polynomial_division_quotient_remainder`.

**Task parameters:** `{"dividend_coefficients": [3, -5, -2], "divisor_root": 2}`.

**Oracle expected:** not materialized in the record because classification
stopped before execution.  From the stored oracle contract and parameters, the
expected answer is `{"quotient_coefficients": [3, 1], "remainder": 0}`:
`3x² - 5x - 2 = (x - 2)(3x + 1)`.

**Answer contract / final prompt:** the stored Ab2d prompt embeds the frozen
payload and directs the model to output only complete Python source, define one
`generate(level=1, **kwargs)`, and return exactly the keys `question_text`,
`correct_answer`, and `oracle_payload`.  The polynomial answer contract requires
`correct_answer.quotient_coefficients` and scalar `correct_answer.remainder`.

**Raw-output structure:**

1. A prose planning preamble ending in “Final Code Implementation”, followed
   by a `python` fence.  This first fence parses and contains exactly one
   `generate()`.
2. Prose headed “Example Output”, then “Given the input”, followed by a second
   `python` fence containing only the two input assignments.  It parses and has
   zero `generate()` definitions.
3. Prose headed “Answer”, followed by a third `python` fence containing only a
   result dictionary.  It parses and has zero `generate()` definitions; prose
   after it is “Notes”.

All three fence language labels are exactly `python`; all are closed.  There is
no truncation, malformed fence label, missing fence, or AST parsing failure.
The raw first-attempt output and all fence contents remain unchanged in the
tracked JSONL.  `candidate_extracted` is `null`; `parse_status` and
`failure_category` are both `extraction_failure`; `failure_detail` is `null`.

**Production extraction rule:** `extract_code` treats `python`/`py` fences as
the highest-priority candidate set and returns `ambiguous` if that set has more
than one member.  It does not use nearby headings or choose a “best” code
fence.  Actual diagnostics are `total_fenced_blocks=3`,
`python_fenced_blocks=3`, `other_fenced_blocks=0`, and ambiguity reason
`3 python-fenced blocks found`.

**Exact rejection point:** the multiple-python-fence ambiguity branch in
`agent_tools.finals_rebuild.extraction.extract_code`; `classify_response` maps
the non-`extracted` result to `extraction_failure` before AST validation.

**Mathematical correctness:** the first fence's intended division arithmetic is
correct: it calls `PolynomialOps.div_qr([3, -5, -2], [1, -2])` and takes the
first remainder coefficient, yielding quotient `[3, 1]` and remainder `0`.

**Program correctness:** not contract-correct even if the first fence were
selected: it returns top-level keys `question`, `answer`, and
`oracle_payload`, not the required `question_text`, `correct_answer`, and
`oracle_payload`.  It would therefore fail production schema validation.

**Scaffold usage:** partial.  It uses the supplied `PolynomialOps.div_qr`
primitive correctly, but ignores the output-only/one-fence scaffold and the
three-key return contract.

**Would pass if extracted:** no.  Deterministically selecting the first fence
would avoid ambiguity but lead to `schema_failure`; the harness must not make
that non-contractual selection.

**Root-cause classification:** `prompt_contract_misunderstanding`.

**Responsible layer:** `model`.

**Evidence:** valid Python candidate content was wrapped with two additional
`python` example fences, and its top-level schema contradicts the stored
contract.  The extractor rejected exactly the currently documented ambiguous
shape, so this is not `harness_extraction_bug`.

**Recommended next action:** `clarify_scaffold_only`.

**Confidence:** high.

## Task: largest_proper_divisor_reasoning

**Task:** `ce115_q20_largest_proper_divisor_l1` /
`largest_proper_divisor_reasoning`.

**Task parameters:** `{"largest_proper_divisors": {"A": 10}, "claims": [{"subject": "A", "candidate_factor": 2, "asks_necessity": true}]}`.

**Oracle expected:** not materialized in the record because classification
stopped before execution.  The stored oracle evaluates all compatible values;
for largest proper divisor 10, the compatible value is 20 and factor 2 is
necessary.  Expected answer: `{"claims": [true]}`.

**Answer contract / final prompt:** the stored Ab2d prompt embeds the frozen
payload, requires only complete Python source and exactly one three-key return,
and defines `correct_answer` as `{"claims": list[bool]}` in frozen claim order.

**Raw-output structure:**

1. A prose explanation and “Final Code Implementation” followed by a first
   `python` fence.  It parses and contains exactly one `generate()`.
2. An “Example Usage” prose section followed by a second `python` fence
   containing the example payload only.  It parses with zero `generate()`.
3. Prose “The function will return” followed by a third `python` fence with an
   example output dictionary.  It parses with zero `generate()`; “Summary”
   prose follows it.

All three labels are `python`, all fences are closed, and the raw output is not
truncated.  `candidate_extracted` is `null`; `parse_status` and
`failure_category` are `extraction_failure`; `failure_detail` is `null`.
Extractor diagnostics are again three total/three Python/zero other fences and
the exact ambiguity reason `3 python-fenced blocks found`.

**Production extraction rule:** identical deterministic highest-priority fence
rule.  The extractor must not infer that “Final Code Implementation” makes the
first block preferred, and it cannot merge or discard the two example fences.

**Exact rejection point:** the multiple-python-fence ambiguity branch of
`extract_code`, before `classify_response` parses the candidate AST or invokes
`generate()`.

**Mathematical correctness:** the explanatory/example answer `[True]` is
correct for this frozen instance.  However, the first candidate's stated rule
assumes every actual value is `largest_proper_divisor * 2`; that is not the
oracle's general compatible-number rule and is only coincidentally suitable for
this even value.

**Program correctness:** no under production invocation.  The sole
`generate()` reads all values from `kwargs`, while the evaluator invokes
`generate()` with no arguments.  If selected, it would use empty values and
return `{"claims": []}` with an empty `oracle_payload`, violating the frozen
payload/schema requirement.  Its general arithmetic assumption is also not
robust beyond the incidental example.

**Scaffold usage:** no relevant supplied primitive is used; the candidate
replaces the frozen-payload contract with empty `kwargs` defaults and an
unjustified `* 2` shortcut.

**Would pass if extracted:** no.  Selecting the first fence would produce a
schema failure from the empty payload before a correct oracle result; selecting
the third example dictionary would be an unsupported manual choice and is not
a candidate function.

**Root-cause classification:** `prompt_contract_misunderstanding`.

**Responsible layer:** `model`.

**Evidence:** three same-priority Python fences violate the output-only
contract.  Additionally, the executable fence does not embed or return the
frozen parameters needed by the no-argument evaluator.  The extractor's
rejection is correct; the model's example answer does not make the overall
output executable under the contract.

**Recommended next action:** `clarify_scaffold_only`.

**Confidence:** high.

## Summary

| task_family | math_correct | program_correct | scaffold_used | would_pass_if_extracted | responsible_layer | root_cause |
|---|---:|---:|---:|---:|---|---|
| polynomial_division_quotient_remainder | yes | no | partial | no | model | prompt_contract_misunderstanding |
| largest_proper_divisor_reasoning | partial (instance yes) | no | no | no | model | prompt_contract_misunderstanding |

There is no `harness_extraction_bug`: both raw responses violate the
extractor's documented single-winning-fence requirement.  There is no basis to
mark either record passed without changing raw output or choosing among
ambiguous fences, both of which are outside production semantics.
