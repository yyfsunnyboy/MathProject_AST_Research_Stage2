# Healer-vNext Official EvalPlus Single-Task Replay

## Outcome

The nine requested eval-ready samples were materialized successfully for Mbpp/255, Mbpp/279, and Mbpp/410 under Raw, Original Ab3, and Candidate Healer-vNext conditions. SHA256, source paths, entry points, EvalPlus version, MBPP+ version, and the exact Linux command are recorded in `replay_manifest.csv`.

The official EvalPlus replay could not execute in the current environment. EvalPlus 0.3.1 and the repository's official runner require Linux/WSL POSIX resource and interval-timer semantics. This machine has no installed WSL distribution and no Docker runtime. The native-Windows EvalPlus import is additionally blocked at the pyarrow DLL by application-control policy.

No Candidate base/plus result exists, so no `full rescue`, `base-regression recovery`, `structural-only recovery`, or `no recovery` classification is assigned.

## Historical Baselines

These are copied from the reviewed official forensic records and were not rerun in this replay:

| Task | Raw base | Raw plus | Original Ab3 base | Original Ab3 plus |
|---|---|---|---|---|
| Mbpp/279 | not run (duplicate-entry-point worker error) | not run | fail | fail |
| Mbpp/255 | pass | fail | fail | fail |
| Mbpp/410 | pass | fail | fail | fail |

Candidate outcomes remain unknown until the command in `commands.txt` is run in WSL/Linux. Therefore Mbpp/279 full rescue and Mbpp/255 or Mbpp/410 base recovery are not claimed.

## Sample Validation

- Nine materialized files have recorded SHA256 values.
- Candidate entry-point count is exactly one for all three tasks.
- Raw Mbpp/279 intentionally has two `is_num_decagonal` definitions, matching its historical worker error.
- Candidate diffs are stored separately and no official Raw or Original Ab3 file was overwritten.

## Required Handoff

Install or provide a WSL/Linux environment with EvalPlus 0.3.1 and its dependencies, then run the single command recorded in `commands.txt`. It filters the official runner to exactly the three task IDs and three isolated strategies and writes any Excel output only beneath this replay artifact directory, never to the official result workbook.
