# Stage2 通用鷹架 × 演算法鷹架 × 累積 Healer Validation 20 題預登錄規格 v3

> 版本日期：2026-07-25  
> 專案：`MathProject_AST_Research_Stage2`  
> 狀態：**plans frozen / not executed**（本輪僅凍結計畫與 runner；尚未生成 1200 candidates、尚未正式 EvalPlus）  
> 本版取代 v2；v2 的 2B 模型軸已取消

---

## 〇、與 v2 的差異摘要

1. **取消 2B**。不得下載、設定或執行任何 2B 模型。
2. 正式模型軸改為 **`qwen3.5:4b` / `qwen3.5:9b` / `qwen3:0.6b`**。
3. 規模改為 20 × 5 × 4 × **3 models = 1200** immutable candidates；EvalPlus stage cells = **3600**。
4. 執行分工：我方 4B+9B（800／2400），同學 0.6B（400／1200）。
5. H4 engineering implementation 已於 commit `8954a257` 封存；規則檔 SHA-256：
   `1aabe131b7312c9bc1e0b34b20540bef6f7d3ec858c2c2994cf84bc84f85a513`。
6. `implementation_frozen_for_validation=true`（Validation 期間不得改規則）。
7. 明確：`development replay ≠ EvalPlus qualification`；`evalplus_executed=false`；
   `execution_safety_status=not_established`。
8. 正式底帳採非互斥多維標籤；八類互斥摘要僅為機械推導。
9. 唯一正式 Evaluator 環境：WSL/Linux + `evalplus==0.3.1` + MBPP+ `v0.2.0` /
   hash `ee43ecabebf20deef4bb776a405ac5b1`。

---

## 一、研究問題（沿用）

1. 通用方法論層級的演算法自我檢查提示，能否在生成前預先減少後續殘留的演算法層失敗？
2. 通用鷹架與演算法鷹架是否存在交互作用？
3. 累積版 Healer（H1→H2→H3→H4）在四種 prompt 條件、三種模型下的 repair depth 與
   execution transition 分佈為何？
4. 套用鷹架與 Healer 之後，殘餘失敗組成如何隨條件改變？

---

## 二、實驗設計

### 2.1 因子

| 因子 | 水準 |
|---|---|
| 通用鷹架 | 有 / 無 |
| 演算法鷹架 | 有 / 無 |
| 模型 | `qwen3.5:4b` / `qwen3.5:9b` / `qwen3:0.6b` |
| Healer 狀態 | Raw / Post-Healer（同一份程式的配對前後處理） |

另獨立列帳 **Pipeline-corrected**（責任歸屬帳，不額外生成）。

### 2.2 Prompt 條件

| Prompt 條件 | 通用鷹架 | 演算法鷹架 |
|---|:---:|:---:|
| `Ab1` | ✗ | ✗ |
| `Ab2g` | ✓ | ✗ |
| `Ab2A` | ✗ | ✓ |
| `Ab2gA-factorial-v1` | ✓ | ✓ |

`Ab2gA-factorial-v1` = frozen Ab2g 原文 + 空行 + frozen Ab2A 原文。  
**不得**與 `Ab2gA-short-v1` 混用。

### 2.3 資料規模

| 項目 | 規模 |
|---|---:|
| Validation tasks | 20 |
| Seeds | 5（11／22／33／44／55） |
| Prompt 條件 | 4 |
| Models | 3 |
| **Immutable candidates** | **1200** |
| 我方（4B+9B） | 800 |
| 同學（0.6B） | 400 |
| 主要比較帳（Raw vs Post-Healer） | 2400 |
| Pipeline 責任歸屬帳 | 1200 |
| **EvalPlus stage evaluations** | **3600** |

### 2.4 固定 Validation20 task IDs

```
Mbpp/4, Mbpp/86, Mbpp/130, Mbpp/132, Mbpp/247,
Mbpp/264, Mbpp/265, Mbpp/281, Mbpp/405, Mbpp/418,
Mbpp/425, Mbpp/456, Mbpp/459, Mbpp/564, Mbpp/569,
Mbpp/580, Mbpp/586, Mbpp/611, Mbpp/755, Mbpp/775
```

權威來源：`artifacts/public_benchmark_governance/frozen_split.csv`
（`proposed_role=validation`）。  
Existing600／H2-91／demo-print-500 **僅** development evidence，不得混入 Validation20 正式結果。

---

## 三、模型身分（machine-verified；不得猜測）

### 3.1 本機已核對（build host，Ollama `/api/tags`）

| 欄位 | qwen3.5:4b | qwen3.5:9b |
|---|---|---|
| digest | `2a654d98e6fba55d452b7043684e9b57a947e393bbffa62485a7aac05ee4eefd` | `6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7` |
| parameter_size | 4.7B | 9.7B |
| quantization_level | Q4_K_M | Q4_K_M |
| family | qwen35 | qwen35 |
| format | gguf | gguf |
| identity_status | machine_verified_on_build_host | machine_verified_on_build_host |

正式生成前，執行電腦仍須再次 `ollama list` / `ollama show` / `/api/tags` 核對。

### 3.2 同學機器待核對

| 欄位 | qwen3:0.6b |
|---|---|
| digest | **pending_machine_verification** |
| parameter_size | pending |
| quantization_level | pending |
| family | pending |
| format | pending |

schema 已預留 machine-verified identity 欄位；**正式 generate 前必須填齊**。  
本輪建置不因 0.6B digest 尚未取得而停止。

生成參數（三模型相同）：

```json
{
  "temperature": 0.2,
  "top_p": 0.95,
  "top_k": 20,
  "num_predict": 2048,
  "num_ctx": 8192,
  "thinking": false,
  "stream": false
}
```

---

## 四、累積 Healer（凍結）

```
Raw
→ Pipeline correction (extract_code)
→ H1 entry-point unique arity-compatible alias
→ H2 module-level assert quarantine
→ H3 empty-suite pass insertion
→ H4 top-level demo/print quarantine
→ EvalPlus
```

| 規則 | implementation_frozen_for_validation | 備註 |
|---|:---:|---|
| H1 | true | development qualification 已有證據；Validation 期間不得改 |
| H2 | true | development_candidate_not_frozen（qualification 另計） |
| H3 | true | development_candidate_not_frozen |
| H4 | true | 封存於 `8954a257`；SHA `1aabe131…f85a513` |

`implementation_frozen_for_validation=true` ≠ 已通過 EvalPlus qualification。  
`qualification_status` 仍為 `development_candidate_not_frozen`，直到 Validation20 正式評測完成。

---

## 五、結果帳目

### 5.1 正式底帳（非互斥多維）

- `decision`：`transformed` / `abstained`
- `transition`：Raw→Post-Healer PASS/FAIL 配對
- `repair_depth`：可複選（含 `parse_rescue`、`partial_repair` 等）
- `rule_trace`：`first_effective_rule` + `rules_applied`

### 5.2 互斥摘要（機械推導，固定優先序）

1. `invalid_or_missing_candidate`
2. `evaluator_infrastructure_failure`
3. `verified_rescue`
4. `execution_regression`
5. `transformed_known_pass_preserved`
6. `partial_repair`
7. `unchanged_pass`
8. `unchanged_failure`

`partial_repair`／`parse_rescue`／execution rescue **不得**計為 `verified_rescue`。  
只有修後通過完整 EvalPlus，才能算 `verified_rescue`。

---

## 六、執行環境

唯一正式 Evaluator：

- WSL / Linux
- `evalplus==0.3.1`
- MBPP+ `v0.2.0`
- dataset hash `ee43ecabebf20deef4bb776a405ac5b1`

禁止 native Windows Python 執行 EvalPlus bridge。  
允許 PowerShell 僅作為 `wsl.exe` 包裝入口。

---

## 七、工件入口

- Master：`artifacts/public_benchmark_governance/validation20_scaffold_healer_v3/`
- Per-model manifests：`.../models/{qwen35_4b,qwen35_9b,qwen3_0_6b}/`
- Generation runner：`scripts/run_mbpp_validation20_generation_v1.py`
- Derivatives：`scripts/run_mbpp_validation20_derivatives_v1.py`
- EvalPlus qualification：`scripts/run_mbpp_validation20_evalplus_qualification_v1.py`
- Cross-machine merge：`scripts/merge_mbpp_validation20_cross_machine_results_v1.py`

---

## 八、本輪明確未做

- 未生成 1200 candidates
- 未執行正式 EvalPlus
- 未呼叫模型
- 未修改 H1／H2／H3／H4 規則
- 未 commit／push
