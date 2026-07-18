# Candidate A operator interruption recovery 操作指南（Milestone 2E-R）

## 事故治理

Candidate A `mbpp_q35_9b_ca_exp40_r001` 因 operator Ctrl+C 標記為 `permanently_invalidated_operator_interrupt`。r001 的2個journals只作事故證據，formal valid generation=0；不得刪除、修改、移動、resume、retry、selective retry、補跑、合併至r002或納入paired analysis。可能存在未持久化的in-flight request，但磁碟無法證明或恢復，formal credit=0。

P0 `mbpp_q35_9b_p0_exp40_r001` 已完整200/200、retry=0、protocol violations=0，保持有效且不得重跑。Candidate A必須以全新 `mbpp_q35_9b_ca_exp40_r002` 從第一格完整重新生成200格，不得沿用r001 response。Candidate A仍是 `frozen_experimental_candidate_not_official_v1`，不是正式v1。

Milestone 2E-R 不得執行以下正式命令；本輪不呼叫模型、EvalPlus或paired analysis，也不建立r002目錄。

## Windows 唯讀 preflight（可執行，不呼叫模型）

```powershell
py -3.12 -B .\scripts\run_mbpp_candidate_a_expansion.py preflight
```

## Windows Candidate A r002 generation（本輪未執行）

```powershell
py -3.12 -B .\scripts\run_mbpp_candidate_a_expansion.py generate --treatment candidate_a --run-id mbpp_q35_9b_ca_exp40_r002 --base-url http://127.0.0.1:11434 --timeout-seconds 600
```

不得再次執行P0 generation；r002每格exactly one attempt，任何中斷均停止，不得retry/resume。

## WSL EvalPlus（本輪未執行）

```bash
cd /mnt/c/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2
/home/yehya/.venvs/ast_evalplus/bin/python scripts/run_mbpp_candidate_a_expansion.py evaluate --treatment p0 --run-id mbpp_q35_9b_p0_exp40_r001 --parallel 4
/home/yehya/.venvs/ast_evalplus/bin/python scripts/run_mbpp_candidate_a_expansion.py evaluate --treatment candidate_a --run-id mbpp_q35_9b_ca_exp40_r002 --parallel 4
```

P0若已評估則不得重跑evaluation；所有evaluation outputs仍遵守overwrite禁止。

## Paired analysis（本輪未執行）

```bash
/home/yehya/.venvs/ast_evalplus/bin/python scripts/analyze_mbpp_candidate_a_expansion.py --p0-run-id mbpp_q35_9b_p0_exp40_r001 --candidate-run-id mbpp_q35_9b_ca_exp40_r002
```

paired analysis只能使用P0 r001完整200格與Candidate A r002完整200格；Candidate A r001貢獻0格。
