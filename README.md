# MathProject_AST_Research_Stage2

**Updated**: 2026-07-25 | **Status**: Stage2 research ongoing; H1 frozen, H2/H3/demo-print development candidates

---

## Research Overview

Stage2 investigates the failure chain in AI-generated programs on public benchmarks (HumanEval+, MBPP+), and how far deterministic Healer can safely repair without guessing at algorithms.

**Key Finding**: Deterministic local repair's value lies in removing verifiable structural blockers (syntax, module load), making programs executable and diagnosable—not in guessing algorithm intent.

**Success Redefined**: No longer just FAIL→PASS count. Now: blocker removal, partial repair, verified rescue, regression, abstain—all tracked separately, never conflated.

---

## Current Status Summary

| Component | Status | Evidence | Details |
|-----------|--------|----------|---------|
| **H1** (Entry-point alias) | Frozen v1 | 9 verified rescue, 0 regression | Existing600 (600 cells); prospective qualification eligible |
| **H2** (Module-assert quarantine) | development candidate | 71 blocker removed, 46 partial repair, 0 regression | 91-cell cohort; awaits prospective validation |
| **H3** (Empty suite insertion) | development candidate | 3 parse rescue, 0 regression, 151 known-pass preserved | 691-cell deterministic replay; EvalPlus not executed |
| **Demo-print** (Candidate) | development candidate | 21 hit, 17 preserved PASS, 0 regression | 500-cell cohort; awaits prospective validation |

---

## Quick Links to Formal Documentation

- **Current Research Status**: [docs/CURRENT_STATUS.md](docs/CURRENT_STATUS.md) — H1/H2/H3/demo-print condensed results
- **Artifact Catalog**: [docs/ARTIFACT_INDEX.md](docs/ARTIFACT_INDEX.md) — all formal evidence paths & verification status
- **Pipeline & Outcome Classification**: [docs/RESEARCH_PIPELINE.md](docs/RESEARCH_PIPELINE.md) — flow diagram, outcome aggregation rules, correct/incorrect accounting
- **Master Governance Spec**: [docs/HumanEval+／MBPP+ 跨域 Scaffold × Healer 實驗啟動規格.md](docs/HumanEval+／MBPP+%20跨域%20Scaffold%20×%20Healer%20實驗啟動規格.md)

---

## What's in This Repo

### Public Benchmark Research Line
- **H0 Pipeline**: Extraction, normalization (no repair)
- **H1 Healer** (Frozen): Entry-point alias for unique arity
- **H2 Healer** (Development): Module-level assert quarantine
- **H3 Healer** (Development): Empty suite pass insertion
- **Demo-Print Candidate**: Top-level literal-only print quarantine
- **EvalPlus Integration**: Outcome accounting (paired analysis for H1; functional eval for H2/H3/demo-print)
- **0.6B Extended**: HumanEval/MBPP generation on smaller model (results archived; governance TBD)

### Key Datasets
- **Existing600**: 600 MBPP+ programs (H0↔H1 paired analysis, frozen)
- **4B Failure-Supply**: 200 MBPP+ candidates (taxonomy complete, Healer not applied)
- **9B Conditional23**: 23 assert-heavy cases (static audit frozen; H2 functional eval complete)
- **H2 Cohort**: Combined 4B+9B = 91 cells (independent from Existing600)

### NOT in This Repo
- Math16, HealerBoundary, CE115 projects (separate research line)
- Adaptivity/learning research
- Confirmatory benchmark (reserved for prospective phase)

---

## Three-Account Separation (Non-Negotiable)

1. **Raw (H0)**: Original model output, no intervention
2. **Pipeline-Corrected**: After extraction/normalization, before Healer
3. **Post-Healer (H1/H2/H3)**: After deterministic repair rules

Packaging fixes (Markdown, code fences) never counted as Healer rescue.

---

## Outcome Accuracy: What Counts

| What's Rescue | What's NOT Rescue |
|---|---|
| FAIL→PASS (strict) | FAIL→different FAIL (partial repair, fail-to-fail) |
| Blocker removed + executable | Blocker removed but answer still wrong |
| Deterministic, provable, no guessing | Task-specific repairs, heuristics, parameter tuning |
| Zero regression on evaluated cohort | Any PASS→FAIL (stops immediately) |

---

## Research Scope Boundaries

✓ **Included**:
- Deterministic local structural repair (H1/H2/H3)
- Strict PASS/FAIL evaluation (EvalPlus)
- Development-level evidence (same data for discovery + evaluation; prospective pending)
- Comparing Scaffold variants (Ab1 vs Ab2g)

✗ **Excluded**:
- Algorithm rewriting or semantic guessing
- Multi-model result conflation (4B ≠ 9B ≠ 0.6B)
- Confirmatory benchmark (reserved for prospective phase)
- Cross-repository result merging

---

## Next Steps

1. **Prospective Qualification**: Evaluate H1/H2/H3/demo-print on independent holdout data (not in discovery)
2. **0.6B Governance**: Integrate extraction/taxonomy for cross-model comparison
3. **H4+ Search**: Resume deterministic candidate discovery in 372-cell inventory (if new mechanism found)
4. **Confirmatory Phase**: Run full EvalPlus on holdout; support generalization claims

---

## References

- **Frozen evidence (Existing600 H1)**: `artifacts/public_benchmark_governance/healer_h0_h1_functional_evaluation_v1/`
- **H2 audit & evaluation**: `artifacts/public_benchmark_governance/h2_module_assert_quarantine_*_v1/`
- **H3 cumulative replay**: `agent_tools/finals_rebuild/mbpp_h3_empty_suite_pass_insertion.py`
- **Demo-print evaluation**: `artifacts/public_benchmark_governance/top_level_demo_print_quarantine_development_v1/`
- **372-cell inventory**: `artifacts/public_benchmark_governance/deterministic_healer_candidate_inventory_4b9b_v1/`

---

**Do not cite development evidence as confirmatory.** Prospective validation on holdout data required for external generalization claims.
