# r002 calibration operator guide

本輪未執行。唯一人工 calibration 指令：

```bash
cd /mnt/c/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2 && /home/yehya/.venvs/ast_evalplus/bin/python scripts/run_candidate_b_r003_diagnostics_r002.py --mode calibration --manifest artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v1/manifest.json --manifest-sha256 701b8117b45389cad827011eee26ce34b2b861aa509b1e6754a9985234027e5e --output-dir artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v1/manual_calibration_run_001 --execute-r002-diagnostics
```

正式198格維持鎖定；不得在 calibration 8/8 正常 returned 前執行。
