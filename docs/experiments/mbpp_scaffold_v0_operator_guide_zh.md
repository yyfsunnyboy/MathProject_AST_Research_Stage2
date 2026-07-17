# MBPP+ Generic Code Scaffold v0 操作說明

## 凍結範圍

- P0：`mbpp_qwen35_9b_ab1_dev_run_003`
- P1：`mbpp_qwen35_9b_scaffold_v0_dev_run_002`
- Permanently invalidated incident：`mbpp_qwen35_9b_scaffold_v0_dev_run_001`（有效 generation=0，不得 delete/modify/resume/overwrite/selective retry）
- Physical storage：`artifacts/pbd/mbpp_sv0/r002`；journal directory：`j`
- Windows path budget：≤ 240 characters；不依賴 registry long-path 設定。
- Cells：20 tasks × 5 seeds = 100
- Model：`qwen3.5:9b` / `6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7` / `Q4_K_M`
- Scaffold SHA-256：`31969abe8799b1846c488d3f7fca558af79875c7eb90ab76db7a6b62ad263305`
- `think=false`；sampling parameters 與 P0 frozen protocol 完全相同。
- Retry、selective retry、resume、overwrite 與 Healer 全部禁止。
- Observed 與 Pipeline-corrected 是分離評估帳；Pipeline correction 不是 Healer。

## First-attempt ITT recovery

- run_002 已完成一次且僅一次的 100-cell generation；不得再次執行 generation command。
- 一個 HTTP 200、`done=true` 的完整 first-attempt response 因 `message.content` 含 reasoning leakage 而被舊狀態模型誤列為 generation incomplete。
- 該 response 逐字保留於 Observed 帳，另列 `protocol_compliant=false` 與 `reasoning_leakage_in_message_content`。
- Recovery 只從既有 journal 聚合，沒有 retry、resume、regeneration、Healer 或 Pipeline rescue，也未使用 evaluator。
- Pipeline 僅使用事故前凍結的通用 extraction；不得加入 think-tag stripping 或 case-specific 規則。
- 違規輸出仍屬 ITT cell，不得從 100-cell denominator 排除。

以下 generation command 是已執行的凍結歷史命令，僅供稽核，**不得再次執行**。

## 唯一 generation command（Windows PowerShell）

```powershell
py -3.12 -B .\scripts\run_mbpp_scaffold_v0_development.py generate --run-id mbpp_qwen35_9b_scaffold_v0_dev_run_002 --base-url http://127.0.0.1:11434 --timeout-seconds 600
```

## WSL evaluation 正式環境

```powershell
wsl -d Ubuntu
```

進入後：

```bash
cd /mnt/c/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2

/home/yehya/.venvs/ast_evalplus/bin/python scripts/run_mbpp_scaffold_v0_development.py evaluate \
  --run-id mbpp_qwen35_9b_scaffold_v0_dev_run_002 \
  --parallel 4
```

只有 recovery manifest、Observed 與 Pipeline-corrected 三者均為 100/100 identities 時才可執行 evaluation。任何 retry、resume、selective retry、overwrite 或 regeneration 仍然禁止。
