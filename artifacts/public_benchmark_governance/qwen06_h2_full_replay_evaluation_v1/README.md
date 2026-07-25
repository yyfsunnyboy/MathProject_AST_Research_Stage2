# qwen06 H2 full replay evaluation v1

Status: `RUNNER_ENABLED_NOT_EXECUTED`

Unique entrypoint (zero model calls; reads saved Ab1/Ab2g only):

```bash
python scripts/run_qwen06_h2_replay_pipeline_v1.py run-full-benchmark \
  --dataset all \
  --output-dir artifacts/public_benchmark_governance/qwen06_h2_full_replay_evaluation_v1/manual_run_001 \
  --parallel 1
```

Dry-run (materialize 2,168 ITT states + samples; no EvalPlus):

```bash
python scripts/run_qwen06_h2_replay_pipeline_v1.py run-full-benchmark \
  --dataset all \
  --output-dir /tmp/qwen06_h2_full_dry_run \
  --parallel 1 \
  --dry-run
```

Formal EvalPlus requires WSL/Linux. This packaging round does **not** execute `manual_run_001`.
