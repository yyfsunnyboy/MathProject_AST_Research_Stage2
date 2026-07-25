# MathProject_AST_Research_Stage2

更新日期：2026-07-25

本 Repository 的 **Stage2 HumanEval+／MBPP+ 公開 benchmark 研究線**與數學出題主軸並行。公開基準線服務 Scaffold × Pipeline × Healer 的安全邊界定案與分層評估，**不混入** Math16、HealerBoundary、CE115 或適性學習專案成果。

上位規範：[`docs/HumanEval+／MBPP+ 跨域 Scaffold × Healer 實驗啟動規格.md`](docs/HumanEval+／MBPP+%20跨域%20Scaffold%20×%20Healer%20實驗啟動規格.md)

研究進度敘事稿（本地，尚未追蹤入庫）：`docs/決賽文件/20260725_Stage2_Healer標準放寬與目前成果(1).md`。
若敘事稿與正式 artifact 不一致，**以 formal JSON／JSONL／manifest／summary 為準**。

---

## 1. 專案定位與研究問題

Stage2 研究 AI 生成程式在公開基準上的失敗鏈，以及 deterministic Healer 能安全做到哪一步。

研究問題已由單一的「FAIL→PASS 數量」擴充為**分層評估**，但**沒有降低** verified rescue 的標準：

1. 安全解除非演算法性的語法、結構或執行阻斷。
2. 讓原本無法執行／難以診斷的候選程式進入可執行、可診斷狀態。
3. 嚴格區分 blockage removed、partial repair、verified rescue、regression、abstain。
4. **只有** Healer 前 strict FAIL、Healer 後通過完整 evaluator／oracle，才能稱為 `verified_rescue`。
5. Healer 後能執行但答案仍錯，只能記 `partial_repair`（或 fail-to-fail improvement），**不能**算 PASS，也**不能**併入 rescue。
6. 演算法錯誤原則上保留給 evaluator 診斷；Healer 不得猜測作者意圖或重寫演算法。
7. 截斷、核心內容遺失、缺少整段演算法、需要猜測意圖者原則上 `abstain`。

核心主張（development evidence）：deterministic local repair 的安全窗口很窄；它最可靠的角色是在嚴格 guards 下移除可證明的結構阻斷，使程式可測、可診斷，而不是大量把錯誤程式「猜對」。

---

## 2. 研究資料集與兩條研究軌

| 研究軌 | 對象 | 現況重點 | 證據層級 |
|---|---|---|---|
| **公開基準軌**（本 README 重點） | HumanEval+／MBPP+（EvalPlus） | 9B development、4B failure-supply、H2／demo-print candidates、0.6B 延伸 | development-only 為主；不得寫成 confirmatory |
| **數學出題程式軌** | CE115 等 | 與公開基準線分帳 | 不互相覆蓋結論 |

主要模型（不得互相代替結果）：

| 模型（artifact 標籤） | 角色 | 狀態 |
|---|---|---|
| `qwen3.5:9b` | development60／Candidate B r003／Existing600 | 已完成多項 formal development 分析 |
| `qwen3.5:4b` | failure-supply pilot（20 tasks × 5 seeds × 2 conditions） | **200 格已完成**（`analysis_complete`） |
| `qwen3:0.6b` | HumanEval／MBPP Ab1／Ab2g／Ab3 延伸供給 | 生成與 EvalPlus 結果已入庫；跨模型治理比較尚待整合 |

---

## 3. Scaffold／Pipeline／Healer 三帳分列

必須分開記帳，不可寫成同一件事：

| 階段 | 介入時間 | 含義 |
|---|---|---|
| **Scaffold 生成條件**（Ab1 bare／Ab2g generic scaffold） | 生成前 | 改變模型輸入條件 |
| **Pipeline-corrected** | 生成後、Healer 前 | 抽取／正規化等 packaging；不是 Scaffold，也不是 Healer rescue |
| **Post-Healer** | pipeline 之後 | 僅在安全窗口內的 deterministic local repair |

三帳：Observed（raw）／Pipeline-corrected／Post-Healer。Markdown／code-fence 等格式問題不得冒充 Healer rescue。

---

## 4. Healer 新的分層成功標準

| 結果類別 | 定義 | 可否稱為完整救援 |
|---|---|---:|
| `blocker_removed`／executable transition | 指定阻斷已移除，或修後可進入更深層測試 | 否 |
| `partial_repair` | 阻斷解除後仍未 strict PASS；後續錯誤已可觀察 | 否 |
| `verified_rescue` | Raw／H0 strict FAIL → Post-Healer／H1 strict PASS | **是** |
| `preserved_pass` | 原本 strict PASS，修後仍 PASS | 否（屬安全證據） |
| `unchanged_failure` | 未觸發或無可證明改善 | 否 |
| `abstain` | 證據不足／候選不唯一／可能改語意 → 不修改 | 否 |
| `regression` | 原本 strict PASS → 修後 strict FAIL | 否（安全失敗） |

記帳原則：完整成功標準不降級；可執行 ≠ 答案正確；regression 獨立列帳；有歧義就 abstain。

---

## 5. 已完成的正式實驗與主要結果

### 5.1 Existing600：600 programs／1200 accounts（development-only）

| 指標 | 結果 |
|---|---:|
| Programs／Accounts | 600／1200 |
| H0／H1 strict PASS | 151／160 |
| Verified rescue | **9** |
| Regression | **0** |
| Fail→Fail／Pass→Pass | 440／151 |
| Healer 實際修改 | 41／600 |
| 狀態 | `paired_analysis_complete_development_only`；資格為獨立 prospective qualification，**非** confirmatory |

證據：[`artifacts/public_benchmark_governance/healer_h0_h1_functional_evaluation_v1/paired_analysis_run_001/`](artifacts/public_benchmark_governance/healer_h0_h1_functional_evaluation_v1/paired_analysis_run_001/)

### 5.2 Candidate B r003：198 格 taxonomy v3.1（已關閉）

| 項目 | 結果 |
|---|---|
| 正式失敗格 | **198**（`COMPLETE_198_CELL_TAXONOMY_SET_CLOSED`） |
| Healer labels | abstain 175／conditional 23／eligible **0** |
| Coverage（重算） | 合法 development 母體 **116**；development60 實際涵蓋 **60**；H0 總格 300；H0 失敗 **224**；H0 通過 **76**；Conditional23 = **23** |
| 安全結論 | `TASK_SPECIFIC_REPAIR_ONLY`／`NO_SAFE_GENERALIZABLE_RULE_FOUND`／`GENERAL_HEALER_ABSTAIN` |
| 既有 Healer | **凍結**既有規則；多 seed 可重現 ≠ 跨題泛化；不得把 Task ID 白名單寫進通用 Healer |

證據：[`docs/決賽文件/7月23Candidate_B_r003_198格失敗分類與Healer安全邊界報告.md`](docs/決賽文件/7月23Candidate_B_r003_198格失敗分類與Healer安全邊界報告.md)、[`.../candidate_b_r003_taxonomy_v31_complete_198cell_closure_v1/`](artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_complete_198cell_closure_v1/)

### 5.3 Conditional23 靜態診斷（已凍結）

- 23／23 格完成；**零** candidate import／compile／execution（AST-only）
- 證明的是 top-level assert 的結構位置與遮蔽機制，**不是**動態執行通過
- 治理狀態：`FROZEN_APPROVED`（之後才另行進入 H2 功能評測）

證據：[`artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_conditional23_diagnostics_v1/README.md`](artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_conditional23_diagnostics_v1/README.md)

### 5.4 4B failure-supply pilot：200 格（已完成）

> **已過期資訊已移除**：舊 README 將 4B pilot 寫成「runner 已啟用但結果未產生／未評測」已不正確。以 analysis artifact 為準。

| 指標 | 結果 |
|---|---:|
| 狀態 | **`analysis_complete`**（independent audit PASS） |
| 生成完成 | **200／200** |
| 可唯一抽取／歧義 | 186／14（歧義 fail-closed，未評測但仍留 ITT 分母） |
| ITT Base+Plus PASS | **52／200（26%）** |
| ITT Base PASS | **68／200（34%）** |
| Taxonomy（非 PASS） | ADJUDICATED 148；L1=22、L2=15、UNRESOLVED=97、L0=14 |
| Healer | `healer_applied=false`；本輪未套用新 Healer；eligibility 全數 abstain |

證據：[`artifacts/public_benchmark_governance/candidate_b_4b_failure_supply_pilot_analysis_v1/aggregate_summary.json`](artifacts/public_benchmark_governance/candidate_b_4b_failure_supply_pilot_analysis_v1/aggregate_summary.json)、[`research_report_zh.md`](artifacts/public_benchmark_governance/candidate_b_4b_failure_supply_pilot_analysis_v1/research_report_zh.md)

### 5.5 H2：module-level assert quarantine（development candidate）

目的：隔離會在模組載入時先執行的 entry-point self-test `assert`；**不猜答案**。

| 指標 | Combined（4B + 9B Conditional23） |
|---|---:|
| Roster | 91 |
| Transformed／Abstained | 71／20 |
| Blocker removed | 71 |
| Partial repair | 46 |
| Preserved pass | 25 |
| Verified rescue | **0** |
| Regression | **0** |
| 凍結決策 | **`development_candidate_not_frozen`**（criterion B） |

若只看 pass rate，H2 像「0 救援」；依 failure chain，則確認阻斷解除與更深層錯誤暴露。不得把 blocker removed 寫成 verified rescue。

證據：[`.../h2_module_assert_quarantine_functional_evaluation_v1/`](artifacts/public_benchmark_governance/h2_module_assert_quarantine_functional_evaluation_v1/)

### 5.6 372 格 deterministic candidate 盤點 + demo-print 規則

對 4B 148 + 9B 224 = **372** 個既有 development 錯誤格做只讀靜態盤點：

| 機制／結論 | 數量 |
|---|---:|
| Packaging／Markdown／extractor（歸 Scaffold／Pipeline） | 73 |
| Module-level assert（既有 H2） | 64 |
| Truncation（原則 abstain） | 23 |
| Semantic／algorithm／無唯一局部機制 | 202 |
| Unique entry-point mismatch（既有 H1） | 2 |
| Top-level demo print（新 candidate） | 2 |

唯一新候選：`top_level_literal_only_demo_print_quarantine_v0`。功能評測（4B 200 + 9B 300 = 500 格）：

| 指標 | 結果 |
|---|---:|
| Static hit／abstain | 21／479 |
| Preserved pass／Verified rescue／Regression | 17／**0**／**0** |
| Unchanged failure（命中且 Raw FAIL） | 4 |
| 決策 | `development_candidate_not_frozen` |

證據：[`.../deterministic_healer_candidate_inventory_4b9b_v1/`](artifacts/public_benchmark_governance/deterministic_healer_candidate_inventory_4b9b_v1/)、[`.../top_level_demo_print_quarantine_development_v1/`](artifacts/public_benchmark_governance/top_level_demo_print_quarantine_development_v1/)

### 5.7 `qwen3:0.6b` Ab1／Ab2g／Ab3 延伸（已入庫，尚待治理整合）

| Benchmark／條件 | EvalPlus plus PASS（ITT） |
|---|---:|
| HumanEval Ab1 | 2／164（1.22%） |
| HumanEval Ab2g | 34／164（20.73%） |
| MBPP Ab1 | 31／378（8.20%） |
| MBPP Ab2g | 129／378（34.13%） |

Ab3 summary：HumanEval 164 與 MBPP 378 的 core／spec changed 皆為 0，syntax／execution rescue 皆為 0。
初步可說：0.6B 提高低品質供給；Ab2g 明顯優於 Ab1；既有 Ab3 在本批完整輸出上無觸發／救援。**不得**以 0.6B 結果代替 4B／9B 結論；跨模型比較尚待 extraction／ITT／taxonomy／治理審查。

證據：`runs/he_qwen06/`、`runs/mb_qwen06/`（含 `public_benchmark_raw/*/evalplus/*_eval_results.json` 與 `summary.json`）

### 5.8 qwen06 × H2 全基準 replay（runner 已接線，正式評測尚待執行）

- 接線與 synthetic smoke：**已完成**
- 完整 542 題／2168 ITT states × EvalPlus：`manual_run_001` **尚未執行**
- H2 規則狀態仍為 `development_candidate_not_frozen`

證據：[`.../qwen06_h2_replay_pipeline_v1/`](artifacts/public_benchmark_governance/qwen06_h2_replay_pipeline_v1/)、[`.../qwen06_h2_full_replay_evaluation_v1/`](artifacts/public_benchmark_governance/qwen06_h2_full_replay_evaluation_v1/)

---

## 6. 目前可安全處理的錯誤類型

在嚴格 guards、provenance 與 idempotence 下，development evidence 支持：

1. **窄規則 H1 類**（Existing600）：少數可驗證的局部修復 → 9 個 verified rescue、0 regression（development-only）。
2. **H2 module-assert quarantine**：移除唯一可辨識的 module-load self-test assert → blocker removed／partial repair；regression=0；**無** verified rescue → 未凍結。
3. **Top-level literal-only demo print quarantine**：命中格可 deterministic 轉換並保留 Raw PASS；**無** verified rescue → 未凍結。
4. **Abstain 本身是安全設計**：歧義、截斷、語意不清時不修改。

---

## 7. 必須 abstain 的邊界

- Task-specific／ambiguous repair；不可用 Task ID 白名單偽裝通用規則
- 截斷、核心演算法遺失、需猜測作者意圖
- 抽取歧義或 source completeness 未知
- 多個 module-level assert、entry point 缺失／不唯一、assert 非 entry-point self-test
- Hidden tests／canonical solution／執行結果反推規則
- Packaging 問題應交 Scaffold／Pipeline，不計入 Healer rescue

---

## 8. 目前限制與不可外推範圍

- Stage2 公開基準線不得混入 Math16／HealerBoundary／CE115／適性學習成果
- development-only ≠ confirmatory；多 seed 重現 ≠ 跨題泛化
- 不得聲稱已窮盡所有 Healer 機制
- 不得把 4B、9B、0.6B 結果互相代替
- 不得把 partial repair／blocker removed 寫成 verified rescue
- 不得修改已凍結歷史結論；本 README 只補充後續進展
- H2／demo-print 仍為 `development_candidate_not_frozen`
- 0.6B 延伸尚未完成與 4B／9B 同規格的 failure taxonomy 整合

---

## 9. 下一階段工作

1. 在 WSL／Linux 執行 qwen06 × H2 全基準 replay（Ab1-Raw／Ab1-H2／Ab2g-Raw／Ab2g-H2 + EvalPlus），產出 paired ledger（`manual_run_001` 尚待執行）。
2. 對 0.6B 做 extraction／ITT／failure taxonomy 與治理審查後，再談跨模型比較。
3. 尋找下一條**可唯一判定**的 deterministic candidate（來源優先：372 盤點中仍未解決、但非 semantic／truncation 的結構錯誤）；不夠唯一則 abstain。
4. 對已有 development candidates（H2、demo-print）規劃獨立 prospective qualification，而非在同一 development 資料上反覆調參。
5. 維持三帳分列與分層成功標準；新規則未達 verified rescue 時不得凍結為正式 Healer v1。

---

## 10. 正式證據與快速入口

| 主題 | 入口 |
|---|---|
| 跨域規格 | [`docs/HumanEval+／MBPP+ 跨域 Scaffold × Healer 實驗啟動規格.md`](docs/HumanEval+／MBPP+%20跨域%20Scaffold%20×%20Healer%20實驗啟動規格.md) |
| 2026-07-25 進度敘事 | `docs/決賽文件/20260725_Stage2_Healer標準放寬與目前成果(1).md`（本地未入庫；數字以 artifacts 為準） |
| 198 格安全邊界報告 | [`docs/決賽文件/7月23Candidate_B_r003_198格失敗分類與Healer安全邊界報告.md`](docs/決賽文件/7月23Candidate_B_r003_198格失敗分類與Healer安全邊界報告.md) |
| Existing600 paired | [`.../healer_h0_h1_functional_evaluation_v1/paired_analysis_run_001/`](artifacts/public_benchmark_governance/healer_h0_h1_functional_evaluation_v1/paired_analysis_run_001/) |
| Conditional23 diagnostics | [`.../candidate_b_r003_taxonomy_v31_conditional23_diagnostics_v1/`](artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_conditional23_diagnostics_v1/) |
| 4B 200 格 analysis | [`.../candidate_b_4b_failure_supply_pilot_analysis_v1/`](artifacts/public_benchmark_governance/candidate_b_4b_failure_supply_pilot_analysis_v1/) |
| H2 functional eval | [`.../h2_module_assert_quarantine_functional_evaluation_v1/`](artifacts/public_benchmark_governance/h2_module_assert_quarantine_functional_evaluation_v1/) |
| 372 格 inventory | [`.../deterministic_healer_candidate_inventory_4b9b_v1/`](artifacts/public_benchmark_governance/deterministic_healer_candidate_inventory_4b9b_v1/) |
| Demo-print eval | [`.../top_level_demo_print_quarantine_development_v1/`](artifacts/public_benchmark_governance/top_level_demo_print_quarantine_development_v1/) |
| 0.6B runs | [`runs/he_qwen06/`](runs/he_qwen06/)、[`runs/mb_qwen06/`](runs/mb_qwen06/) |
| qwen06 H2 full runner | [`.../qwen06_h2_full_replay_evaluation_v1/`](artifacts/public_benchmark_governance/qwen06_h2_full_replay_evaluation_v1/) |
| 生成協議 | [`configs/public_benchmark_generation_protocol_v1.json`](configs/public_benchmark_generation_protocol_v1.json) |
| 公開基準 runner | [`agent_tools/finals_rebuild/public_benchmark_runner.py`](agent_tools/finals_rebuild/public_benchmark_runner.py) |
| 決賽 Rebuild 測試 | [`tests/finals_rebuild/`](tests/finals_rebuild/) |
