# Math failure-boundary — Stage A pilot

Stage A is an adaptive Ab1-only pilot: five ordered CE115 tasks, paired 4B/8B
models, and three frozen task-seed payloads per task (30 cells).  The order is
D1 polynomial division L1, D2 rotation conversion L1, D3 rotation conversion
L2, D4 largest proper divisor L3, and D5 training sequence threshold L3.

The runner writes `manifest.json`, `frozen_payloads.jsonl`,
`cell_results.jsonl`, `summary.json`, and `failure_examples.jsonl`. Every cell
records the prompt, raw answer, extraction, source hash, timing, token metrics,
and one mechanical outcome: passed, empty_response, catastrophic_truncation,
extraction_failure, parse_minor, missing_entry_point, schema_failure,
runtime_failure, answer_incorrect, intrinsic_safety, or infrastructure_failure.

Run after validation:

```powershell
.\.venv\Scripts\python.exe agent_tools/finals_rebuild/math_boundary_pilot.py --task-manifest tests/finals_rebuild/fixtures/math_generation_tasks_ce115_pilot.jsonl --output-root artifacts/finals_rebuild/math_boundary_pilot
```

Stage A does not run Ab2g, any Healer, or retries. Its results select candidate
marginal cells for a later Stage B; they are not confirmatory evidence.
