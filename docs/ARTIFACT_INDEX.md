# Stage2 Artifact Index

This document catalogues all formal evidence artifacts produced during Stage2 research. Paths are verified to exist as of 2026-07-25.

## H1 Evidence

### Existing600 Paired Analysis (H0↔H1)
**Path**: `artifacts/public_benchmark_governance/healer_h0_h1_functional_evaluation_v1/paired_analysis_run_001/`  
**Purpose**: Pairwise outcome analysis of 600 programs under H0 (raw) and H1 (post-healer).  
**Dataset**: MBPP+ Existing600 (60 tasks × 10 seeds)  
**Cohort**: 600 cells (1200 accounts)  
**Evidence Level**: Development-only (paired analysis complete; prospective validation pending)  
**Execution Status**: ✓ Complete (EvalPlus re-run)  
**Freeze Status**: Frozen (Criterion A: 9 verified rescue, 0 regression)  
**Authoritative Files**:
- `paired_analysis_report_zh.md` (narrative)
- `paired_cell_results.csv` (ledger)
- `changed_h1_eval_input.jsonl` (frozen H1 outputs)

---

## H2 Evidence

### H2 Module-Assert Quarantine: Static Audit
**Path**: `artifacts/public_benchmark_governance/h2_module_assert_quarantine_development_static_audit_v1/`  
**Purpose**: AST-level static analysis of assert quarantine eligibility (zero execution).  
**Dataset**: 4B 200 + 9B Conditional23 23 = 91 cells  
**Evidence Level**: Static; determinism verified without runtime  
**Execution Status**: ✓ Complete (AST-only; no model calls)  
**Freeze Status**: Development (static audit pass; functional eval pending)  
**Authoritative Files**:
- `decision_ledger.csv` (per-cell decisions, guards, reasons)
- `README.md` (methodology)

### H2 Module-Assert Quarantine: Functional Evaluation
**Path**: `artifacts/public_benchmark_governance/h2_module_assert_quarantine_functional_evaluation_v1/`  
**Purpose**: Execution-level outcome accounting (71 blocker removed, 46 partial repair, 0 rescue, 0 regression).  
**Dataset**: 4B 200 + 9B Conditional23 23 = 91 cells  
**Cohort**: 91 cells (independent from Existing600)  
**Evidence Level**: Development-only (post-hoc EvalPlus on prior generation; confirmatory holdout needed)  
**Execution Status**: ✓ Complete (EvalPlus re-run)  
**Freeze Status**: Development candidate not frozen  
**Authoritative Files**:
- `aggregate_summary.json` (outcome counts, cohort breakdown)
- `research_report_zh.md` (narrative with partial_repair definition)
- `paired_ledger.csv` (per-cell outcome accounting)

---

## H3 Evidence

### H3 Empty Suite Pass Insertion: Cumulative Pipeline
**Path**: `agent_tools/finals_rebuild/`  
**Purpose**: Implementation and replay of H1→H2→H3 deterministic transformation pipeline.  
**Dataset**: Existing600 (600) + H2 roster (91) = 691 total cells (non-overlapping)  
**Evidence Level**: Development-only (deterministic transformation; execution validation pending)  
**Execution Status**: ✓ Complete (cumulative replay; no model re-run; no EvalPlus)  
**Freeze Status**: Development candidate not frozen  
**Authoritative Files**:
- `mbpp_h3_empty_suite_pass_insertion.py` (H3 rule, 14-guard eligibility)
- `mbpp_h1_h2_cumulative_pipeline.py` (H1→H2→H3 orchestration)
- `H3_IMPLEMENTATION_SUMMARY.md` (H3 validation report)

### H3 Validation (Cumulative Replay Results)
**Path**: `scripts/run_mbpp_h1_h2_cumulative_pipeline_v1.py`  
**Purpose**: Deterministic replay of H1→H2→H3 on development artifacts without re-running models or EvalPlus.  
**Evidence**:
- Existing600: 3 H3 triggered, 3 transformed (parse rescue), 0 regression
- H2 roster: 0 H3 triggered
- Combined: 691 cells, 151 known-pass preserved, 0 regression
- EvalPlus: not executed (evalplus_executed=false)

**Authoritative**: Replay JSON output (frozen development evidence)

---

## 4B Failure-Supply Pilot

### 4B 200 Cells: Comprehensive Analysis
**Path**: `artifacts/public_benchmark_governance/candidate_b_4b_failure_supply_pilot_analysis_v1/`  
**Purpose**: Failure taxonomy and execution analysis of 200 4B-generated candidates.  
**Dataset**: MBPP+ 4B failure supply (20 tasks × 5 seeds × 2 conditions, after dedup)  
**Cohort**: 200 cells (186 uniquely extractable, 14 extraction ambiguity)  
**Evidence Level**: Development-only (analysis complete; Healer not applied)  
**Execution Status**: ✓ Complete (ITT EvalPlus; taxonomy ADJUDICATED)  
**Freeze Status**: Analysis frozen; no Healer claim  
**Authoritative Files**:
- `aggregate_summary.json` (ITT PASS counts: 52 plus, 68 base)
- `h0_evalplus_input.jsonl` (raw H0 completions)
- `research_report_zh.md` (taxonomy detail, ADJUDICATED classification)

---

## 9B Candidate B r003: Conditional23

### Conditional23 Static Diagnostics (AST-only)
**Path**: `artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_conditional23_diagnostics_v1/`  
**Purpose**: AST-level proof of module-level assert structure and location.  
**Dataset**: 9B Candidate B r003 failure set; filtered to 23 assert-relevant cells  
**Cohort**: 23 cells (zero candidate import/compile/execution)  
**Evidence Level**: Static AST; structure provable without runtime  
**Execution Status**: ✓ Complete (AST analysis only)  
**Freeze Status**: Frozen (approved for downstream H2 functional eval)  
**Authoritative Files**:
- `diagnostics_report_zh.md` (AST findings)
- `diagnostics.jsonl` (per-cell AST structure)

---

## Full Taxonomy: 372-Cell Inventory

### 4B 148 + 9B 224 Deterministic Candidate Inventory
**Path**: `artifacts/public_benchmark_governance/deterministic_healer_candidate_inventory_4b9b_v1/`  
**Purpose**: Read-only static inventory of 372 failure cells, categorized by feasibility for deterministic repair.  
**Dataset**: 4B 200 (148 non-PASS) + 9B Candidate B r003 (224 non-PASS) = 372 failure cells  
**Cohort**: 372 (non-overlapping subsets)  
**Evidence Level**: Development-only (static analysis, no execution)  
**Execution Status**: ✓ Complete (inventory frozen)  
**Freeze Status**: Inventory frozen; candidates identified but not all implemented  
**Authoritative Files**:
- `report_zh.md` (categorization: 73 packaging, 64 H2-assert, 23 truncation, 202 semantic, 2 entry-point, 2 demo-print)
- `inventory.jsonl` (per-cell categorization)

---

## Demo-Print Candidate

### Top-Level Demo Print Quarantine: Functional Evaluation
**Path**: `artifacts/public_benchmark_governance/top_level_demo_print_quarantine_development_v1/`  
**Purpose**: Execution-level outcome for literal-only module-level print quarantine (21 hit, 17 PASS preserved, 0 rescue).  
**Dataset**: 4B 200 + 9B 300 = 500 cells  
**Cohort**: 500 cells (development evaluation)  
**Evidence Level**: Development-only (post-hoc EvalPlus; confirmatory holdout needed)  
**Execution Status**: ✓ Complete (EvalPlus re-run)  
**Freeze Status**: Development candidate not frozen  
**Authoritative Files**:
- `aggregate_summary.json` (outcome counts)
- `research_report_zh.md` (narrative, known-pass preservation proof)
- `decision_ledger.csv` (per-cell decision, guards, reason)

---

## 0.6B Extended Experiment

### HumanEval 0.6B Runs
**Path**: `runs/he_qwen06/`  
**Dataset**: HumanEval 164 (qwen3.5:0.6b)  
**Conditions**: Ab1-raw, Ab1-H2, Ab2g-raw, Ab2g-H2  
**Execution Status**: ✓ Generated and EvalPlus complete  
**Result**: Ab1 1.22%, Ab2g 20.73% plus PASS  
**Governance**: Results archived; cross-model governance pending

### MBPP 0.6B Runs
**Path**: `runs/mb_qwen06/`  
**Dataset**: MBPP 378 (qwen3.5:0.6b)  
**Conditions**: Ab1, Ab2g + EvalPlus  
**Execution Status**: ✓ Generated and EvalPlus complete  
**Result**: Ab1 8.20%, Ab2g 34.13% plus PASS  
**Governance**: Results archived; cross-model governance pending

---

## qwen06 × H2 Full Replay Runner

### qwen06 H2 Full Evaluation Pipeline
**Path**: `artifacts/public_benchmark_governance/qwen06_h2_full_replay_evaluation_v1/`  
**Purpose**: Wiring and synthetic smoke for full H2 replay on 0.6B generation.  
**Dataset**: qwen3.5:0.6b HumanEval/MBPP generation  
**Status**: 
- Wiring: ✓ Complete
- Synthetic smoke: ✓ Passed
- Full replay (542 tasks × 2168 ITT + EvalPlus): **not yet executed** (manual_run_001 pending)

**Freeze Status**: Runner wired; formal evaluation deferred  
**Authoritative Files**:
- `runner_config.json` (H2 replay configuration)
- `smoke_test_results.json` (synthetic validation pass)

---

## Reference Configurations & Infrastructure

### Generation Protocol
**Path**: `configs/public_benchmark_generation_protocol_v1.json`  
**Purpose**: Specification for model inference (temperature, max_tokens, stop tokens, etc.)  
**Status**: Authoritative for all generation runs

### Public Benchmark Runner
**Path**: `agent_tools/finals_rebuild/public_benchmark_runner.py`  
**Purpose**: Orchestration and EvalPlus integration  
**Status**: Current version (reference for implementation)

### Test Suite
**Path**: `tests/finals_rebuild/`  
**Purpose**: Integration and regression tests for pipeline  
**Status**: ✓ Passing (10/10 core tests)

---

## Cross-Reference: Stage2 Research Narrative Documents

### Master Guideline
**Path**: `docs/HumanEval+／MBPP+ 跨域 Scaffold × Healer 實驗啟動規格.md`  
**Purpose**: Original governance specification (authoritative for scope/definitions)

### 198-Cell Safety Boundary Report
**Path**: `docs/決賽文件/7月23Candidate_B_r003_198格失敗分類與Healer安全邊界報告.md`  
**Purpose**: Taxonomy v3.1 methodology and Conditional23 rationale

### Local Research Narrative (Not in Repo)
**Path**: `docs/決賽文件/20260725_Stage2_Healer標準放寬與目前成果(1).md`  
**Purpose**: Progress summary as of 2026-07-25 (not committed; referenced for historical context only)

---

## Verification Checklist

- ✓ All listed artifact paths verified to exist as of commit `18ff5147`
- ✓ No moved, renamed, or deleted artifacts
- ✓ H1/H2/H3/demo-print all evidence-backed
- ✓ 0.6B results archived without governance integration
- ✓ Confirmatory benchmark not yet executed
- ✓ Three-account separation maintained throughout
