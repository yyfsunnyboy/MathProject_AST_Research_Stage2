# Gemini encoding and alternating extraction forensic — 2026-07-14

## Scope and immutable inputs

This is an offline forensic of
`results/gemini_ab1_ab2d_l1_seed_20260714_diagnostic.jsonl`.  No provider,
Gemini, Ollama, or other API call was made; no diagnostic row was rerun; and
the stored JSONL was not changed.

The file is valid UTF-8 JSONL with eight rows: four `Ab1`, four `Ab2d`, and
two rows for each of the four frozen task families.  Every row has
`model_tag = gemini-3.5-flash`, `request_count = 1`, `retry_count = 0`, and
`healer_used = false`.  The relevant stored prompt, raw-output, and candidate
fields contain no U+FFFD replacement character.

## Encoding finding

The diagnostic runner explicitly reads and writes JSONL using UTF-8, writes
with `ensure_ascii=False`, and its candidate subprocess uses `-X utf8`,
`PYTHONUTF8=1`, `PYTHONIOENCODING=utf-8`, and `encoding="utf-8"`.  The frozen
Ab2d final prompt contains intact Chinese skill text.  The same prompt and the
stored task data therefore rule out Big5/CP950 corruption in the prompt
builder, provider handoff, JSONL writer, or candidate subprocess.

PowerShell display mojibake is a console-rendering concern, not evidence that
the stored UTF-8 JSONL or provider prompt was corrupted.  No runner encoding
change is warranted.  A pre-existing `??` in the runner's human-readable
summary title is outside the prompt/evaluation path and was left untouched.

## Alternating output forensic

| condition | stored outcome | raw-output finding | offline conclusion |
|---|---|---|---|
| Ab1 | `parse_minor` | Starts with `0` and explanatory prose; ends mid-sentence at `within the`; no `def generate` exists. | Incomplete prose, not Python source. |
| Ab2d | `parse_minor` | Starts with a prose heading and Markdown explanation; ends at a list marker; no `def generate` exists. | Incomplete prose, not Python source. |

Both rows were classified as `parse_minor` because the canonical plain-text
extractor preserved unfenced text and the classifier passed that prose to
`ast.parse`.  There is no hidden Markdown fence, source prefix, executable
candidate, schema return, oracle payload, or correct answer available to
recover.  The 3-second candidate timeout was not reached in either row.

The minimal classifier repair accepts a `def generate` source block following
leading prose, but reports prose-only output as `extraction_failure` instead
of a misleading Python parse error.  It does not synthesize code, modify raw
output, relax the schema, or alter oracle comparison.  Under the corrected
offline classification, both alternating rows are `extraction_failure`; they
remain non-evaluable and non-passing.

## Qualification and limits

The existing stored results have Ab1 2/4 oracle passes and Ab2d 3/4 oracle
passes.  The corrected offline classifier does **not** justify a cloud
qualification of Ab1 3/4 or Ab2d 4/4: neither alternating response contains
candidate source that can be executed or compared with the oracle.  This is
an output-completion/format failure, not an encoding defect or a correctable
answer-extraction edge case.

## Regression coverage

`tests/test_gemini_ab1_ab2d_diagnostic.py` covers the two frozen raw outputs,
plain Python, fenced Python, prose followed by a generator, and prose-only
output.  Targeted tests passed:

```text
19 passed
```

The run emitted one unrelated pytest cache warning because the existing
`.pytest_cache` path could not be created; it did not affect test execution.
