# MBPP+ Generic Code Scaffold v0 操作說明

## 凍結範圍

- P0：`mbpp_qwen35_9b_ab1_dev_run_003`
- P1：`mbpp_qwen35_9b_scaffold_v0_dev_run_001`
- Cells：20 tasks × 5 seeds = 100
- Model：`qwen3.5:9b` / `6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7` / `Q4_K_M`
- Scaffold SHA-256：`31969abe8799b1846c488d3f7fca558af79875c7eb90ab76db7a6b62ad263305`
- `think=false`；sampling parameters 與 P0 frozen protocol 完全相同。
- Retry、selective retry、resume、overwrite 與 Healer 全部禁止。
- Observed 與 Pipeline-corrected 是分離評估帳；Pipeline correction 不是 Healer。

本 Milestone 只凍結協定。以下命令本輪未執行，之後僅由使用者按順序手動執行。

## 唯一 generation command（Windows PowerShell）

```powershell
& '.\.venv\Scripts\python.exe' 'scripts\run_mbpp_scaffold_v0_development.py' generate --run-id mbpp_qwen35_9b_scaffold_v0_dev_run_001 --timeout-seconds 300
```

## 唯一 WSL evaluation command

```powershell
wsl.exe bash -lc 'cd /mnt/c/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2 && python3 scripts/run_mbpp_scaffold_v0_development.py evaluate --run-id mbpp_qwen35_9b_scaffold_v0_dev_run_001 --parallel 4'
```

Generation 成功且完整產生 100/100 cells 前，不得執行 evaluation。任何中斷或不完整 run 均不得 retry、resume、selective retry 或 overwrite；應停止並保留 journal 供稽核。
