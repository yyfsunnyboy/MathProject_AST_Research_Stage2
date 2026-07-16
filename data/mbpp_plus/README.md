# MBPP+ Official Task Export

`tasks.jsonl` is exported from the official EvalPlus MBPP+ loader,
`evalplus.data.get_mbpp_plus`, through the repository's existing
`evalplus_bridge.load_evalplus_dataset("mbpp", None)` interface.

The export is pinned to:

- `evalplus==0.3.1`
- `MBPP_PLUS_VERSION=v0.2.0`
- the dataset hash recorded in `dataset_manifest.json`

Each JSONL row contains only the fields a model may receive:
`task_id`, `prompt`, and `entry_point`. The export does not store official
tests, base or Plus inputs, canonical solutions, contracts, or expected
outputs. Falling back to the original non-Plus MBPP dataset is forbidden.

## Rebuild in the existing WSL environment

From the repository root mounted in WSL, run:

```bash
MBPP_PLUS_VERSION=v0.2.0 \
  /home/yehya/.venvs/ast_evalplus/bin/python \
  scripts/prepare_mbpp_plus_tasks.py
```

The script fails closed unless the existing environment provides
EvalPlus 0.3.1, the pinned MBPP+ version resolves successfully, all 378 tasks
have unique `Mbpp/<number>` IDs, and every task has a non-empty official
`prompt` and `entry_point`.
