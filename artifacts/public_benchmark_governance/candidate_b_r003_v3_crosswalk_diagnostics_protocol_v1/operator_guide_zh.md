# unresolved198 coarse diagnostics operator guide

本輪未執行 diagnostics。下列是唯一允許的人工 WSL 指令；禁止 retry、resume、overwrite、parallel>1 或其他 output path。

```bash
cd /mnt/c/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2 && /home/yehya/.venvs/ast_evalplus/bin/python scripts/run_candidate_b_r003_unresolved_diagnostics.py --manifest artifacts/public_benchmark_governance/candidate_b_r003_v3_crosswalk_diagnostics_protocol_v1/manifest.json --manifest-sha256 3e605bec8f126900f89af757f237063db4800329dd3d99cda1218a581985b9a8 --parallel 1 --output-dir artifacts/public_benchmark_governance/candidate_b_r003_v3_crosswalk_diagnostics_protocol_v1/manual_diagnostics_run_001 --execute-frozen-diagnostics
```
