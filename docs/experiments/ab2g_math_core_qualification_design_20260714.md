# Ab2g-math-core qualification design — 2026-07-14

## Treatments

The new isolated treatment is assembled as:

```text
Ab1              = task contract + frozen parameters
Ab2g-math-core   = math core scaffold + task contract + frozen parameters
Ab2d-local       = math core scaffold + task-local primitive + task contract + frozen parameters
```

`MATH_CORE_SCAFFOLD` is the same module constant for Ab2g-math-core and
Ab2d-local, so its shared prefix is byte-for-byte identical.  Ab2g-math-core
contains no task-family primitive, domain catalogue, skill markdown, Family
Catalogue, Sub-skill Graph, Generator Priority, LiveShow guidance, or examples.

## Core scaffold

The common text requires complete Python source, the exact `generate` entry
point, exactly `question_text`, `correct_answer`, and `oracle_payload`, exact
frozen payload equality, task-specific answer schema compliance, exact
arithmetic where needed, no unsafe/external operations, and exactly one attempt.

## Deterministic prompt metadata

Metadata uses character count, UTF-8 byte count, and whitespace-separated
approximate wordpiece count.  It is not a provider tokenizer count.

| Family | Ab2g chars | Ab2d-local chars | Difference |
|---|---:|---:|---:|
| polynomial | 2443 | 2816 | 373 |
| largest proper divisor | 2376 | 2730 | 354 |
| rpm | 2323 | 2652 | 329 |
| alternating | 2953 | 3378 | 425 |

## Qualification runner

`scripts/run_gemini_ab2g_math_core_qualification.py` is a new, separate
runner.  Its configured cloud path is fixed to four L1 families, seed
`20260714`, `gemini-3.5-flash`, condition `Ab2g-math-core`, one request per
cell, retry count zero, 120-second provider timeout, 3-second candidate timeout,
4096 output tokens, no Healer, and append/flush/fsync JSONL persistence.

The required outputs are the new Ab2g qualification JSONL and summary paths.
This implementation was validated only with `--dry-run`: it builds four planned
rows and reports task IDs, prompt condition, prompt-size metadata, model, and
fixed settings without constructing a provider client or writing JSONL/summary.

Cloud qualification is true only for exactly four rows with all cells evaluable
and oracle-passing, zero retries, and zero execution timeouts.  A 3/4 result,
parse/extraction/truncation failure, or partial JSONL is not qualified.

## Scope

No cloud/API call, model execution, Healer, existing runner, existing result
JSONL, summary, forensic record, task definition, task contract, frozen
parameter, sampler, oracle, evaluator semantics, provider configuration, or
dependency was changed.
