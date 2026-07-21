# r002 v2 calibration operator guide

本輪未執行。唯一人工 WSL calibration 指令：

```bash
cd /mnt/c/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2 && /home/yehya/.venvs/ast_evalplus/bin/python scripts/run_candidate_b_r003_diagnostics_r002_v2.py --mode calibration --manifest artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v2/manifest.json --manifest-sha256 1e69e02b0a434cbcaa88f899896805d803bd8dfa3b21c0d7134e1033dc89acf2 --output-dir artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v2/manual_calibration_run_001 --execute-r002-diagnostics
```

formal CLI 的 calibration hash 參數固定為 `--calibration-execution-manifest-sha256`，其值是 calibration output `execution_manifest.json` 檔案 bytes 的 SHA-256；receipt 內 `source_manifest_sha256` 是另一個獨立驗證欄位。正式198格維持鎖定。
