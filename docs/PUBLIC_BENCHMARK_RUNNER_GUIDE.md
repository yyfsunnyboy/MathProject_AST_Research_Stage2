# Full Public Benchmark Generation, Replay & EvalPlus Audit & Execution Guide

本文件紀錄 `qwen3.5:4b` 已實際完成之 full public benchmark 執行資產、稽核結果、重現/Resume 方式，以及另一台電腦執行 `qwen3.5:9b` 的標準步驟與指令。

---

## 1. 核心 Runner 路徑與模組

* **Generation Runner**: [`scripts/run_public_benchmark_generation_v1.py`](file:///C:/Projects/MathProject_AST_Research_Stage2/scripts/run_public_benchmark_generation_v1.py)
  * 底層通訊與採樣: [`agent_tools/finals_rebuild/ollama_generation_runner.py`](file:///C:/Projects/MathProject_AST_Research_Stage2/agent_tools/finals_rebuild/ollama_generation_runner.py)
* **H2 Replay Runner**: [`scripts/run_public_benchmark_h2_replay_v1.py`](file:///C:/Projects/MathProject_AST_Research_Stage2/scripts/run_public_benchmark_h2_replay_v1.py)
* **EvalPlus Runner**: [`scripts/run_public_benchmark_h2_evalplus_v1.py`](file:///C:/Projects/MathProject_AST_Research_Stage2/scripts/run_public_benchmark_h2_evalplus_v1.py)

---

## 2. 4B 已完成結果與參數設定

### 2.1 參數設定 (Frozen Parameters)
- **Datasets**: HumanEval (164 題) + MBPP (378 題) = 542 題
- **Treatments**: Ab1 (Bare Prompt), Ab2g (Generic Safety-and-Format Scaffold Prompt)
- **Seed**: `0` (或相容 preset `20260712`)
- **Decoding**: `temperature=0.0`, `top_p=1.0`, `top_k=40` (或 1), `think=false`, `num_predict=1024` (cap 2048)

### 2.2 完成格數統計 (4B)
- **Raw Generations**: **1,084 / 1,084** (HumanEval: 328, MBPP: 756)
- **H2 Replay Journals**: **2,168 / 2,168** (HumanEval: 656, MBPP: 1,512)
- **EvalPlus Evaluated Cells**: **2,168 / 2,168** (HumanEval: 656, MBPP: 1,512)

### 2.3 Output Artifact 路徑 (4B)
- **HumanEval Raw Generations**: [`runs/he_qwen35_4b/`](file:///C:/Projects/MathProject_AST_Research_Stage2/runs/he_qwen35_4b)
- **MBPP Raw Generations**: [`runs/mb_qwen35_4b/`](file:///C:/Projects/MathProject_AST_Research_Stage2/runs/mb_qwen35_4b)
- **H2 Replay Governance**: [`artifacts/public_benchmark_governance/qwen35_4b_h2_full_replay_v1/`](file:///C:/Projects/MathProject_AST_Research_Stage2/artifacts/public_benchmark_governance/qwen35_4b_h2_full_replay_v1)
- **EvalPlus Governance**: [`artifacts/public_benchmark_governance/qwen35_4b_h2_full_evalplus_v1/`](file:///C:/Projects/MathProject_AST_Research_Stage2/artifacts/public_benchmark_governance/qwen35_4b_h2_full_evalplus_v1)

---

## 3. 9B 執行指令指南 (另一台電腦 git pull 後執行)

另一台電腦完成 `git pull` 後，僅需將模型名稱指定為 `qwen3.5:9b`，依照以下順序執行即可完成 9B 的 Generation、Replay 與 EvalPlus 評測：

### Step 1: 9B Raw Generation (需開 Ollama 服務)
```powershell
python scripts/run_public_benchmark_generation_v1.py --model qwen3.5:9b --dataset all --treatment all --resume --parallel 1 --acknowledgement I_ACKNOWLEDGE_THIS_WILL_CALL_THE_PINNED_FULL_BENCHMARK_MODEL
```
> **Resume 方式**: 加 `--resume` 旗標即可自動跳過已有完整 `persisted_complete` 的任務，實現中斷恢復。

### Step 2: 9B H2 Full Replay (離線，不呼叫 LLM)
```powershell
python scripts/run_public_benchmark_h2_replay_v1.py --model qwen3.5:9b --dataset all --resume --parallel 1
```

### Step 3: 9B EvalPlus 評測 (離線，不呼叫 LLM)
```powershell
python scripts/run_public_benchmark_h2_evalplus_v1.py --model qwen3.5:9b --dataset all --resume --parallel 1
```

---

## 4. 當前資產與未生成狀態總結

- **已完整生成並評測完成**: `qwen3.5:4b`（包含 Raw 1084 份、Replay 2168 格、EvalPlus 2168 格）
- **尚未生成 / 待在新機器執行**: `qwen3.5:9b`（等待執行上列 9B 指令）
