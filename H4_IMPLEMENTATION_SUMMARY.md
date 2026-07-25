# H4 Top-Level Demo/Print Quarantine — Implementation Summary (corrected)

**Date**: 2026-07-25
**Status**: Development Candidate — Implementation Complete (stage-interface corrected)
**Rule ID**: `top_level_demo_print_quarantine_v0`
**Rule Status**: `development_candidate_not_frozen`

This revision replaces an earlier draft of this file that described the
first H4 implementation as "transformed=0 is correct by design." That
description was wrong and has been withdrawn; see "What was wrong" below.

---

## What was wrong in the first draft

The first H4 draft reapplied the pre-existing, independently frozen
`top_level_literal_only_demo_print_quarantine_v0` guard set (which requires
a top-level `assert`) *after* H2 in the fixed `H1 -> H2 -> H3 -> H4` order.
That rule's own preregistration
(`artifacts/public_benchmark_governance/top_level_demo_print_quarantine_development_v1/preregistration.json`)
records `"composition_order": "demo_print_then_H2"` — it was validated
running *before* H2, while the assert was still top-level. H2 relocates any
top-level assert satisfying essentially the same selftest-safety guards into
`if __name__ == "__main__":` before H4 ever saw the source, so applying the
unmodified guard set after H2 abstained on all 691 replayed cells by
construction — a stage-interface collision, not a validated safety
property. The first draft's fingerprint set was also built by parsing the
frozen evidence's `transformed_sources.jsonl`, which contains exactly the
21 cells the original rule was already known to transform — i.e. eligibility
was reverse-engineered from known hits, which this project's methodology
forbids.

Both defects are fixed in this revision.

---

## Corrected stage contract

H4 (`agent_tools/finals_rebuild/mbpp_h4_top_level_demo_print_quarantine.py`,
function `quarantine_post_h2_top_level_demo_print`) requires **structural H2
provenance**:

1. H2's own `StageRecord.changed` must be `True` for this cell (no fallback
   to "any assert that looks top-level").
2. The resulting `if __name__ == "__main__":` guard's sole body statement
   must be, by `ast.dump` structural comparison (no position attributes),
   the exact Assert that was top-level in H2's own input source.

Without both, H4 abstains — an arbitrary pre-existing `__main__` guard never
triggers it (tested explicitly).

When provenance is confirmed, H4 looks at H2's *pre-transform* source for
the top-level `print` statement that was adjacent to that same assert,
re-validates literal/argument safety, and — only if every guard holds —
merges that print into the same guard H2 created, directly after the
assert. The print is moved, never deleted; statement order and content are
preserved.

`public_assert_fingerprints` are computed per task_id directly from
`data/mbpp_plus/tasks.jsonl`'s public prompt text via
`prepare_top_level_demo_print_quarantine_development_v1.public_assert_fingerprints(prompt)`
— the same function the original frozen evidence used — never from
candidate output, never from any known-hit list.

Content-safety helpers (`_print_is_safe`, `_is_main_guard`,
`_function_segment_hashes`, `_unclassified_top_level_call_count`,
`assert_fingerprint`) are imported from the pre-existing
`mbpp_top_level_demo_print_quarantine.py` rather than duplicated.

---

## Guard list (post-H2 stage)

`extraction_unambiguous`, `source_complete`, `h2_reported_changed`,
`h2_input_parseable`, `h4_input_parseable`, `h2_guard_provenance_confirmed`,
`exactly_one_h2_input_top_level_print`, `print_adjacent_to_h2_input_assert`,
`assert_matches_public_selftest`, `print_still_top_level_in_h4_input`,
`print_arguments_safe`, `builtin_print_unshadowed`,
`no_other_unclassified_top_level_calls`, `output_parseable`,
`function_segments_unchanged`, `print_removed_from_top_level`.

Any guard failing aborts with a specific reason; no exceptions or fallbacks.

---

## Files

- `agent_tools/finals_rebuild/mbpp_h4_top_level_demo_print_quarantine.py` — rule (unchanged this round; no bug found in it)
- `agent_tools/finals_rebuild/mbpp_h1_h2_cumulative_pipeline.py` — `apply_h4_stage` passes H2's input source and H2's own `changed` flag through to H4, in addition to H3's output (unchanged this round)
- `tests/test_mbpp_h4_top_level_demo_print_quarantine.py` — 29 tests, including a genuine positive transform, H2-provenance-required tests, idempotence, and the full H1/H2/H3/H4/MULTI_STAGE/UNCHANGED transform-class matrix
- `scripts/run_mbpp_h1_h2_h3_h4_cumulative_replay_v1.py` — rewritten this round: precise eligible/candidate/transformed/abstained definitions, per-stage parse-rescue attribution, full triggered-cell ledger fields, formal artifact writer
- `artifacts/public_benchmark_governance/h4_top_level_demo_print_quarantine_development_replay_v1/` — formal development artifacts (summary.json, triggered_cell_ledger.csv, abstain_reason_distribution.json, replay_manifest.json), see that directory's replay_manifest.json for SHA-256 of each file

---

## Eligibility bookkeeping (governance-corrected terminology)

H4's guard chain never reads Raw PASS/FAIL, EvalPlus status, or any
execution outcome (verified by grep across
`mbpp_h4_top_level_demo_print_quarantine.py`: no match for
`status|outcome|evalplus|pass_status|raw_result`). Eligibility is purely
structural: H2 provenance plus AST content-safety guards.

| Cohort | size | h2_provenance_candidate | h4_eligible | h4_transformed | h4_abstained |
|---|---:|---:|---:|---:|---:|
| Existing600 | 600 | 114 | 35 | 35 | 565 |
| H2 roster | 91 | 71 | 13 | 13 | 78 |
| demo-print original cohort | 500 | 131 | 21 | 21 | 479 |

`h2_provenance_candidate` = cells where H2 itself reports `changed=True`
(the only cells H4 can possibly act on). `h4_eligible` = the subset passing
every H4 guard. In this deterministic AST rule there is no state where a
cell passes every guard but is not transformed, so `h4_eligible` is always
identical to `h4_transformed`; the replay script asserts this identity
rather than assuming it (`scripts/run_mbpp_h1_h2_h3_h4_cumulative_replay_v1.py::_cohort_stats`).

**H4_ONLY = structurally_impossible_under_current_stage_contract.** H4's
first gate is `h2_reported_changed is True`, so every transformation is
necessarily paired with an H2 change. All 69 observed transformations fall
under `H2_AND_H4`; the replay script asserts `H4_ONLY` count is 0 for each
cohort rather than stating this as an unverified claim.

The demo-print cohort's 21 H4-transformed `cell_id`s were independently
verified to be set-equal to the frozen evidence's 21 known-hit `cell_id`s —
computed with no knowledge of that list, using only per-task public-prompt
fingerprints and the corrected post-H2 provenance contract. This is a
convergence check, not a design goal.

**H4 is functionally demonstrated** (69 triggered cells across three
cohorts kept separate), replacing the withdrawn "0 triggered, correct by
design" claim in the first draft.

---

## Parse-rescue attribution, by stage (previous draft's "71" was wrong)

An earlier ad-hoc replay script counted a cell as "parse-rescued" whenever
its pipeline-normalized input was `None` (falsy) and the final output
happened to be an empty string (which trivially parses as an empty module).
That produced a spurious `parse_rescue=71` for Existing600. The corrected
script parses each stage's actual `output_source` individually and never
treats a missing/`None` source as vacuously parseable:

| Cohort | H1 rescues | H2 rescues | H3 rescues | H4 rescues | total |
|---|---:|---:|---:|---:|---:|
| Existing600 | 0 | 0 | 3 | 0 | 3 |
| H2 roster | 0 | 0 | 0 | 0 | 0 |
| demo-print cohort | 0 | 0 | 0 | 0 | 0 |

Existing600's 3 matches the frozen H3 evidence exactly. H1/H2/H4 cannot
structurally produce a parse rescue: each requires `ast.parse` to succeed on
its own input before doing anything, and abstains (output = unchanged input)
otherwise; only H3 (`insert_pass_for_empty_suite`) is designed to repair a
SyntaxError.

---

## Explicit status

```
evalplus_executed=false
new_verified_rescue=0
new_execution_regression=not_evaluated
qualification_status=development_candidate_not_frozen
engineering_status=functionally_demonstrated
execution_safety_status=not_established
```

Per cohort, of the triggered cells:

| Cohort | transformed_known_pass | preserved_known_pass (end-to-end unchanged bytes) |
|---|---:|---:|
| Existing600 | 16 | 99 |
| H2 roster | 10 | 3 |
| demo-print cohort | 17 | 75 |

`transformed_known_pass` = triggered cells whose raw status is known PASS
per that cohort's own authoritative source, and whose **source bytes**
changed. This is not a claim that Raw PASS is "preserved" — no EvalPlus ran
in this round, so PASS/FAIL after transformation is **not evaluated**.
`preserved_known_pass` above counts only cells whose *entire* H1–H4 output
is byte-identical to the input (a stricter, separate metric; a raw-PASS cell
outside this count may have been changed by H1/H2/H3 alone, unrelated to
H4). Every H4 transformation independently satisfies
`function_segments_unchanged` (H4's own structural guard) — the tested
function body is byte-identical before/after; only never-otherwise-executed
`if __name__` block content moved — but this is a structural guarantee, not
an execution-verified one.

Full per-cell ledger for all 69 triggered cells is written to
`artifacts/public_benchmark_governance/h4_top_level_demo_print_quarantine_development_replay_v1/triggered_cell_ledger.csv`
(cell_id, cohort, task_id, h2_provenance_candidate, h4_transformed,
raw_known_pass + authority, execution_safety_status, input/h2-input/post-h2/
post-h3/final SHA-256, h2_moved_assert_line, h4_moved_print_line,
public_fingerprint_evidence_path, h2_provenance_confirmed,
first_effective_rule, rules_applied, parse_before, and per-stage
parse_after_h1..h4). SHA-256 of this file and the other three artifacts is
recorded in `replay_manifest.json` in the same directory.

---

## Test status (relative to HEAD, not "all tests pass")

- H4 targeted tests: **29/29** (`tests/test_mbpp_h4_top_level_demo_print_quarantine.py`)
- H1/H2/H3 existing tests: **no new failures relative to HEAD=1f61dc10**
  (10/10 in `tests/test_mbpp_h1_h2_cumulative_pipeline_v1.py` excluding one
  pre-existing gap; 21/21 in `tests/test_mbpp_h3_empty_suite_pass_insertion.py`
  excluding one pre-existing gap)
- Two pre-existing HEAD gaps (present before any H4 work, confirmed via
  `git stash` against HEAD, not touched this round):
  - `test_transform_class_h1_and_h2_label_exists` — calls
    `classify_transform()` without the (already-required-at-HEAD)
    `h3_changed` keyword argument
  - `TestEdgeCases.test_invalid_entry_point` — pre-existing assertion
    failure in the H3 test suite unrelated to H4
