# 🏆 MathProject_AST_Research_Stage2

本 Repository 的 **Stage2 HumanEval+／MBPP+ 公開 benchmark 研究線**與數學出題主軸並行。公開基準線目前以 MBPP+ development-only 證據為中心，服務 Scaffold × Healer 安全邊界定案，不混入 Math16／HealerBoundary／CE115／適性學習專案。

上位規範：[`docs/HumanEval+／MBPP+ 跨域 Scaffold × Healer 實驗啟動規格.md`](docs/HumanEval+／MBPP+%20跨域%20Scaffold%20×%20Healer%20實驗啟動規格.md)

---

## 📌 1. 兩條研究軌（現況）

1. **公開基準軌（本 README 目前狀態重點）**
   - 對象：HumanEval+／MBPP+（EvalPlus）
   - 主模型：`qwen3.5:9b`；transfer／failure-supply pilot 模型：`qwen3.5:4b`（一般 public execution 仍關閉，僅 development-only pilot waiver）
   - 已凍結：`frozen_split.csv`、active 20 development tasks、development60 Candidate B r003、198 格 taxonomy v3.1、Conditional23 跨題搜尋結論
2. **數學出題程式軌**
   - 對象：CE115 等數學出題任務；與公開基準線分帳，不互相覆蓋結論

---

## 🔬 2. Scaffold 生成條件 ≠ Pipeline-corrected

必須分開記帳，不可寫成同一件事：

| 階段 | 介入時間 | 含義 |
|---|---|---|
| **Scaffold 生成條件**（Ab1 bare／Ab2g generic scaffold） | 生成前 | 改變模型輸入條件 |
| **Pipeline-corrected** | 生成後、Healer 前 | 抽取／正規化等 pipeline 處理，不是 Scaffold，也不是 Healer rescue |
| **Post-Healer** | pipeline 之後 | 僅在安全窗口內的 deterministic local repair |

三帳分列：Observed（raw）／Pipeline-corrected／Post-Healer。

---

## 📊 3. 198 格與 Conditional23 邊界結論（已定案）

詳見 [`docs/決賽文件/7月23Candidate_B_r003_198格失敗分類與Healer安全邊界報告.md`](docs/決賽文件/7月23Candidate_B_r003_198格失敗分類與Healer安全邊界報告.md)。

Coverage（重算核對）：

- 合法 development 母體 **116** 題；development60 實際涵蓋 **60** 題（未完整搜尋 116）
- H0 總格 **300**；H0 失敗格 **224**；H0 通過格 **76**（不得把總格數寫成失敗格數）
- Conditional23 coverage = **23**

正式結論：

- `TASK_SPECIFIC_REPAIR_ONLY`／`NO_SAFE_GENERALIZABLE_RULE_FOUND`／`GENERAL_HEALER_ABSTAIN`
- 現有 Healer **凍結**，不修改任何 repair 規則
- 多 seed 可重現 ≠ 跨題泛化；不得把 Task ID 白名單寫進通用 Healer
- 限縮主張：在本輪指定機制及實際可用 development evidence 範圍內，未找到安全跨題規則；**不宣稱已窮盡所有可能 Healer 機制**

---

## 🧪 4. 4B development-only failure-supply pilot（預登錄完成，尚未執行）

Governance：`artifacts/public_benchmark_governance/candidate_b_4b_development_failure_supply_pilot_preregistration_v1/`

| 項目 | 凍結值 |
|---|---|
| Model | `qwen3.5:4b`／digest `2a654d98…eefd`／`Q4_K_M` |
| Tasks | 凍結 active20（`frozen_split` SHA `3bb00bab…f9d4`） |
| Seeds | 11, 22, 33, 44, 55 |
| Conditions | `Ab1_H0`（bare）與 `Ab2g_H1`（Generic Code Scaffold v0） |
| Cells | 20 × 5 × 2 = **200** raw programs |
| 狀態 | **執行配套與預登錄完成；尚未呼叫模型、尚未產生結果、尚未找到新 Healer 規則** |

入口：

- Freeze：`scripts/freeze_candidate_b_4b_development_failure_supply_pilot_v1.py`
- Preflight：`scripts/preflight_candidate_b_4b_development_failure_supply_pilot_v1.py`
- Runner（本輪 generate 仍 gated）：`scripts/run_candidate_b_4b_development_failure_supply_pilot_v1.py`

---

## 🚀 5. 快速入口

- 跨域規格：[`docs/HumanEval+／MBPP+ 跨域 Scaffold × Healer 實驗啟動規格.md`](docs/HumanEval+／MBPP+%20跨域%20Scaffold%20×%20Healer%20實驗啟動規格.md)
- 生成協議：[`configs/public_benchmark_generation_protocol_v1.json`](configs/public_benchmark_generation_protocol_v1.json)
- 公開基準 runner：[`agent_tools/finals_rebuild/public_benchmark_runner.py`](agent_tools/finals_rebuild/public_benchmark_runner.py)
- 決賽 Rebuild 測試：[`tests/finals_rebuild/`](tests/finals_rebuild/)
