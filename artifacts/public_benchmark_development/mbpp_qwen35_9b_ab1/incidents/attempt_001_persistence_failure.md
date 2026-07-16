# Attempt 001 Persistence Failure

- Incident date: 2026-07-16
- Milestone: 1B
- Starting commit: `2f377b5f0e89a967dae59a2b281fac58b8a08068`
- Batch disposition: invalidated in full
- Valid generations: 0
- EvalPlus executed: no

## What Happened

The first model request returned a response, but the response was not persisted.
The process stopped before issuing the second request. The failing operation was
the attempt to reopen the newly created empty `raw_generations.jsonl` in append
mode:

```text
PermissionError: [Errno 13] Permission denied:
'.../artifacts/public_benchmark_development/mbpp_qwen35_9b_ab1/raw_generations.jsonl'
```

The driver had created and closed the empty target with `open("x")`, then tried
to reopen that target with `open("a")` for the first record. Windows denied the
second open. The old flow had no same-directory temporary file, `os.fsync`,
atomic publish, or immediate JSON/SHA-256 read-back verification.

The returned response was never incorporated into research data, inspected for
model-answer selection, evaluated, repaired, or supplied to another model. The
empty raw file and original generation plan are retained unchanged as evidence:

- `generation_plan.json`: SHA-256 `a5cc2fc55235d5307425651027595f021688d5689293fdff492ac8c7e98cce3a`
- `raw_generations.jsonl`: 0 bytes, SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

## Recovery Rule

Attempt 001 is permanently invalid. It must not be resumed, overwritten, or
selectively retried. After the persistence repair, generation may restart only
as a new `run_id` and must execute a complete fresh 100-cell batch under the
unchanged frozen task, seed, model, digest, and sampling protocol.

That future action is a whole-batch infrastructure restart. It is not a retry
chosen from model answers or evaluator outcomes. No model or public benchmark
execution occurred during Milestone 1B-R.

## Persistence Repair

Future runs write each completed cell to an immutable per-cell journal through
a same-directory temporary file. The writer flushes and calls `os.fsync`, closes
the temporary handle before rename, refuses existing targets, then immediately
reads the published file back to validate UTF-8 JSON and SHA-256. Consolidated
JSONL is created only after all 100 journal records are complete and validated.
Permission failures are raised explicitly and are never treated as success.
