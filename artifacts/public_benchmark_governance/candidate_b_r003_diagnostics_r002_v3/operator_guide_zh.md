# r002 v3 formal operator guide

本輪未執行。唯一人工 WSL formal 指令：

```bash
cd /mnt/c/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2 && /home/yehya/.venvs/ast_evalplus/bin/python scripts/run_candidate_b_r003_diagnostics_r002_v3.py --mode formal --manifest artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v3/manifest.json --manifest-sha256 f37c0daa9fb4f3a18d7a2d7fed983f57f2ee0057ef202220643cf7919e362234 --output-dir artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v3/manual_formal_diagnostics_run_001 --calibration-execution-manifest-sha256 5be126a2c0465691db3a2be690dbb8c6054f86b7154b34e6ca06de32e01dcf37 --execute-r002-diagnostics
```

`--calibration-execution-manifest-sha256` 的值是既有 v2 calibration output `execution_manifest.json` 檔案 bytes 的固定 SHA-256。v3 會另外驗證 receipt、results、cohort、protocol及source-manifest identity；不得以其他 hash 取代。
