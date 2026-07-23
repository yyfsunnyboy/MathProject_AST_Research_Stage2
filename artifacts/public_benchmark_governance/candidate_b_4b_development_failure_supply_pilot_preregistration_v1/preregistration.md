# 4B Development-only Failure-supply Pilot Preregistration

## Status

`4B_DEVELOPMENT_FAILURE_SUPPLY_PILOT_PREREGISTERED_NOT_EXECUTED`

本輪僅完成執行配套與預登錄，**尚未呼叫模型、尚未產生任何 4B raw program、尚未修改 Healer**。

## Research Boundary

- Scope：HumanEval+／MBPP+ Stage2 development-only
- Model：`qwen3.5:4b` digest `2a654d98e6fba55d452b7043684e9b57a947e393bbffa62485a7aac05ee4eefd`
- Quantization：`Q4_K_M`；parameter size：`4.7B`
- Protocol role：`frozen_transfer_model`（一般 public-benchmark execution 仍為 false）
- Pilot waiver：`development_only_failure_supply_pilot_v1`（僅授權本 development-only failure-supply pilot）
- Protocol Ollama pin：`0.32.0`；prereg 當下本機觀察：`0.32.1`

## Fixed Design

- Tasks：凍結 `active_development_generation_subset` 20 題
- Frozen split SHA-256：`3bb00bab0d9476412d03c67923c1db4ab1352f551f0e8020ee7e8cb7a367f9d4`
- Seeds：`[11, 22, 33, 44, 55]`
- Conditions：`Ab1_H0`（bare／H0 mapping）與 `Ab2g_H1`（Generic Code Scaffold v0／H1 mapping）
- Cells：20 × 5 × 2 = **200** raw programs
- Scaffold SHA-256：`31969abe8799b1846c488d3f7fca558af79875c7eb90ab76db7a6b62ad263305`
- Generation options 與 9B 對照保持一致；計畫內主要差異僅模型改為 `qwen3.5:4b`

## Active Development Tasks

- `Mbpp/633`
- `Mbpp/769`
- `Mbpp/453`
- `Mbpp/259`
- `Mbpp/739`
- `Mbpp/124`
- `Mbpp/72`
- `Mbpp/792`
- `Mbpp/435`
- `Mbpp/597`
- `Mbpp/732`
- `Mbpp/721`
- `Mbpp/765`
- `Mbpp/777`
- `Mbpp/473`
- `Mbpp/420`
- `Mbpp/742`
- `Mbpp/279`
- `Mbpp/125`
- `Mbpp/603`

## Output Isolation

- Pilot run directory：`artifacts/public_benchmark_development/mbpp_qwen35_4b_failure_supply_pilot/runs/mbpp_q35_4b_dev20_failure_supply_pilot_r001`
- 不得覆寫 9B 或其他既有 artifact
- resume 僅在 cell identity、model fingerprint、prompt SHA、condition、seed 與完成旗標全部吻合時 skip；任一不符 fail-closed

## Stop / Expansion Gates

- 先完成 200 格試點，不得自動擴展至 60 題
- pipeline-corrected failures < 20 或涵蓋 < 5 distinct tasks → 停止後續規則搜尋
- 候選通用規則至少需 2 個不同 task 的獨立證據
- detector 不得依賴 Task ID、答案或修後 PASS
- repair 必須唯一、局部、決定性，並具備答案無關 safety guard
- 未通過門檻即 ABSTAIN，不得修改 Healer

## Explicit Non-claims

- 本文件不宣稱 4B 已產生結果
- 本文件不宣稱已找到新的通用 Healer 規則
- Conditional23 正式結論維持 ABSTAIN／現有 Healer 凍結
