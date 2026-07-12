# HumanEval+ official task provenance

This directory stores the official EvalPlus HumanEval+ task prompts used by the
`finals_rebuild` public-benchmark runner.

## Source

- Repository: [evalplus/humanevalplus_release](https://github.com/evalplus/humanevalplus_release)
- Release: `v0.1.10`
- Asset: `HumanEvalPlus.jsonl.gz`
- License: Apache-2.0

The full release asset is retained under `source/` for reproducibility. The
runner consumes `tasks.jsonl`, which contains only:

- `task_id`
- `prompt`
- `entry_point`

Hidden EvalPlus tests, canonical solutions, and contracts are **not** included in
`tasks.jsonl`.

## Regenerate

```powershell
python scripts/fetch_humaneval_plus.py --write-fetch-metadata
python scripts/prepare_humaneval_plus_tasks.py --expected-source-sha256 <sha256>
```

`prepare_humaneval_plus_tasks.py` is offline-only and fail-closed on task-count,
duplicate `task_id`, missing fields, or optional source SHA mismatch.

## Notes

- No fallback to original HumanEval.
- `artifacts/ollama_generation_smoke/humaneval/tasks.json` is a legacy 2-task
  engineering fixture and must not be used as the formal dataset source.
