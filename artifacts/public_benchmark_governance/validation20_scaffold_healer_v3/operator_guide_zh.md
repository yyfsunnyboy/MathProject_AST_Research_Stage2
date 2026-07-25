# Validation20 Scaffold × Healer v3 Operator Guide

## Authoritative WSL commands

Replace `MODEL` with exactly one of:
`qwen3.5:4b` | `qwen3.5:9b` | `qwen3:0.6b`

### Generation preflight (zero model call)

```bash
cd /mnt/c/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2
python3 scripts/preflight_mbpp_validation20_generation_v1.py --model MODEL
```

### Generation resume (single model)

```bash
python3 scripts/run_mbpp_validation20_generation_v1.py \
  --model MODEL \
  --resume \
  --acknowledgement I_ACKNOWLEDGE_THIS_WILL_CALL_THE_PINNED_VALIDATION20_MODEL
```

### EvalPlus preflight (zero candidate execution)

```bash
python3 scripts/run_mbpp_validation20_evalplus_qualification_v1.py \
  --model MODEL \
  --preflight
```

### EvalPlus formal execute / resume (WSL only)

```bash
python3 scripts/run_mbpp_validation20_evalplus_qualification_v1.py \
  --model MODEL \
  --execute \
  --parallel 1 \
  --acknowledgement I_ACKNOWLEDGE_VALIDATION20_EVALPLUS_FORMAL_EXECUTION
```

```bash
python3 scripts/run_mbpp_validation20_evalplus_qualification_v1.py \
  --model MODEL \
  --resume \
  --parallel 1 \
  --acknowledgement I_ACKNOWLEDGE_VALIDATION20_EVALPLUS_FORMAL_EXECUTION
```

## PowerShell wrapper (calls the same WSL command)

```powershell
powershell -ExecutionPolicy Bypass -File scripts\invoke_mbpp_validation20_wsl.ps1 -Model qwen3.5:4b -Action generation-preflight
```

Supported `-Action` values:
`generation-preflight`, `generation-resume`, `evalplus-preflight`, `evalplus-execute`, `evalplus-resume`
