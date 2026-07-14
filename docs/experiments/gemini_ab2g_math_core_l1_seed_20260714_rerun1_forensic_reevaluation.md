# Ab2g-math-core rerun1 forensic re-evaluation — 2026-07-14

## Scope

This offline re-evaluation reads the four raw outputs in
`results/gemini_ab2g_math_core_l1_seed_20260714_rerun1.jsonl`.  It makes no
provider call, does not rewrite the source JSONL, and does not repair a model
candidate.

## RPM: `rpm_circumference_to_kph`

The raw response is a complete module beginning with `import math` followed by
`generate()`.  The stored candidate was 13 characters shorter and began at
`def generate`, so the extraction path removed the import.  The sandbox does
compile and execute the entire extracted module; it does not execute only a
function body.  The `name 'math' is not defined` runtime error therefore came
from the removed module prelude.

The extractor now preserves an already parseable full module, including imports,
and only strips leading text when the whole response is unparsable.  Re-running
the stored raw output locally produces `passed`; no candidate source was edited.

- Taxonomy: `extraction_bug`
- Ab3 eligible: no (pipeline correction already resolves it)

## Alternating: `alternating_training_progression_threshold`

Raw and extracted source are byte-identical (550 characters).  The final 500
characters end with:

```text
    # An alternating sequence of laps:
    # Session 0 (
```

The response has 161 output tokens, well below the 4096 output-token limit,
and has no unmatched Markdown fence.  Provider truncation is not established.
The source parses because the unfinished text is a comment, but `generate()`
contains only assignments/comments and implicitly returns `None`.  The schema
check therefore fails at the first requirement: the return value is not a dict;
consequently all required top-level keys (`question_text`, `correct_answer`,
`oracle_payload`) are absent.  Local re-evaluation remains `schema_failure`.

- Taxonomy: `incomplete_generation / semantic_content_missing`
- Ab3 eligible: no.  The main progression, cumulative-distance computation,
  threshold decision, and return logic are absent; supplying them would create
  mathematical semantics rather than perform a deterministic nonsemantic repair.

## Re-evaluation matrix

| task_family | original outcome | offline re-evaluation |
|---|---|---|
| polynomial_division_quotient_remainder | passed | passed |
| largest_proper_divisor_reasoning | passed | passed |
| rpm_circumference_to_kph | runtime_failure | passed |
| alternating_training_progression_threshold | schema_failure | schema_failure |

The original observed Ab2g score is 2/4.  The pipeline-corrected Ab2g score is
3/4, the model-valid Ab2g score is 3/4, and Ab3-eligible failures are 0.  The
original artifact remains the record of the
initial execution; this report is an offline forensic correction only.
