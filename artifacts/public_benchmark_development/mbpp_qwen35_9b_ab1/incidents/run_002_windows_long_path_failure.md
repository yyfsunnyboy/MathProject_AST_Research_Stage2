# Run 002 Windows Long-Path Persistence Failure

- Incident date: 2026-07-17
- Run ID: `mbpp_qwen35_9b_ab1_dev_run_002`
- Starting commit: `77875e2c8437c21ce70a556fdca8b2bc58333df4`
- Batch disposition: permanently invalidated
- Valid generations: 0
- EvalPlus executed: no
- Run 003 started: no

## What Happened

The first model response returned, but the completed cell could not be published
to its immutable per-cell journal. The failure occurred before any response was
accepted as research data and before a second generation was started.

The run directory was 157 characters long and the generation journal directory
was 176 characters long. The 64-character generation ID produced a 246-character
target path. The former same-directory temporary-file prefix copied the complete
target filename, producing a temporary path of 260 characters against the traditional
approximately 259-character usable Windows limit. On Windows, creation or publication of that temporary file failed with
`FileNotFoundError: [Errno 2] No such file or directory`.

A synthetic test using standard Windows CPython 3.12 reproduced the same failure
without calling a model. This identifies the root cause as the Windows long-path
limit, not Ollama, model generation, MBPP+, HumanEval+, or EvalPlus.

## Research Disposition

Run 002 has zero valid generations and is permanently invalid. It must not be
resumed, overwritten, or selectively retried. EvalPlus was not executed. No
output from Run 002 may be incorporated into research results.

Run 003 has not been started and no model request has been issued for it.

## Corrective Action

The durable writer retains the 64-character generation ID and final journal
filename, but uses a short `.tmp-` prefix for the same-directory temporary file.
The durability sequence remains unchanged: write, flush, `os.fsync`, close,
atomic rename, immediate read-back, JSON validation, and SHA-256 verification.

A Windows-path regression test fixes the journal directory length at 176
characters, verifies the 246-character final path and the former 260-character
temporary-path condition, and confirms successful durable persistence with the
short prefix.
