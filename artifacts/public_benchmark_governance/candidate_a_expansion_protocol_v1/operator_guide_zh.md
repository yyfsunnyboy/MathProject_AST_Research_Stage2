# MBPP+ Candidate A expansion prospective protocol 操作指南（Milestone 2E）

## 現在的治理狀態

本文件凍結未來正式命令；Milestone 2E 不得執行以下 generation、EvalPlus 或 paired analysis 命令。Candidate A 狀態為 `frozen_experimental_candidate_not_official_v1`，不是正式 Scaffold v1。不得 retry、resume、selective retry、overwrite 或建置 Healer。

- P0 logical run：`mbpp_q35_9b_p0_exp40_r001`；physical：`artifacts/pbd/mbpp_e40/p0/r001`。
- Candidate A logical run：`mbpp_q35_9b_ca_exp40_r001`；physical：`artifacts/pbd/mbpp_e40/ca/r001`。
- 每組：40 tasks × 5 seeds = 200 cells；合計 400 cells。
- Candidate A SHA-256：`bffa1e7e3d1ff77b0de326083bf6c7fd441b2f3b050b45e205a5ba51be87f058`。
- Observed 與 Pipeline-corrected 分帳；Pipeline correction 不是 Healer。
- Transport-complete 的 protocol violation 仍納入 ITT；不得靜默移除 thinking、不得因此重生。

## Windows 生成指令（未執行）

先執行唯讀 preflight：

```powershell
py -3.12 -B .\scripts\run_mbpp_candidate_a_expansion.py preflight
```

P0：

```powershell
py -3.12 -B .\scripts\run_mbpp_candidate_a_expansion.py generate --treatment p0 --run-id mbpp_q35_9b_p0_exp40_r001 --base-url http://127.0.0.1:11434 --timeout-seconds 600
```

Candidate A（只能在 P0 完成後依預註冊順序執行）：

```powershell
py -3.12 -B .\scripts\run_mbpp_candidate_a_expansion.py generate --treatment candidate_a --run-id mbpp_q35_9b_ca_exp40_r001 --base-url http://127.0.0.1:11434 --timeout-seconds 600
```

每格 exactly one attempt。若不完整，停止並依事故治理處理；不得 retry 或 selective retry。

## WSL EvalPlus 評估指令（未執行）

```powershell
wsl -d Ubuntu
```

```bash
cd /mnt/c/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2

/home/yehya/.venvs/ast_evalplus/bin/python scripts/run_mbpp_candidate_a_expansion.py evaluate --treatment p0 --run-id mbpp_q35_9b_p0_exp40_r001 --parallel 4

/home/yehya/.venvs/ast_evalplus/bin/python scripts/run_mbpp_candidate_a_expansion.py evaluate --treatment candidate_a --run-id mbpp_q35_9b_ca_exp40_r001 --parallel 4
```

兩組各自必須先有完整200個 raw 與 Pipeline identities，且 evaluation outputs 不存在，才能評估。

## Paired analysis 指令（未執行）

```bash
/home/yehya/.venvs/ast_evalplus/bin/python scripts/analyze_mbpp_candidate_a_expansion.py --p0-run-id mbpp_q35_9b_p0_exp40_r001 --candidate-run-id mbpp_q35_9b_ca_exp40_r001
```

分析必須揭露全部 Pipeline regressions、獨立統計 reasoning leakage，並套用預先凍結的 promotion gates。若 Candidate A 失敗，不得修改後重跑同40題，也不得混入 Candidate B。
