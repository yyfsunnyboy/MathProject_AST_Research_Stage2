# Stage2 Research Status as of 2026-07-25

## H1: Entry-point Alias Alias for Unique Arity
**Rule ID**: `entrypoint_alias_unique_arity_compatible_v0`  
**Status**: Frozen (formal Healer v1)

**Existing600 Evidence** (development-only):
| Metric | Value |
|--------|------:|
| Verified Rescue | **9** |
| Regression | **0** |
| Programs Transformed | 41/600 |
| Pass Preservation | 151/151 ✓ |

**Verdict**: Delivers 9 verified rescues with zero regression on 600-program cohort. Frozen status justified by strict development evidence.

---

## H2: Module-Level Assert Quarantine
**Rule ID**: `module_assert_entrypoint_selftest_quarantine_v0`  
**Status**: `development_candidate_not_frozen` (criterion B met: safe blocker removal, zero regression)

**Combined Cohort** (4B failure-supply 68 + 9B Conditional23 23 = **91 cells**):
| Metric | Value |
|--------|------:|
| Transformed | 71 |
| Abstained | 20 |
| Blocker Removed | 71 |
| Partial Repair | 46 |
| Preserved Raw PASS | 25 |
| Verified Rescue | **0** |
| Regression | **0** |

**Key Finding**: H2 safely removes module-load blocking asserts (71 cells), enabling deeper diagnostic of remaining failures (46 partial repairs). No execution-level rescue in development data (EvalPlus not re-run).

**Rationale for Not Frozen**: No verified rescue in cohort; requires prospective validation before freezing.

**Important Separation**: 
- Do NOT aggregate Existing600 (600) + H2 roster (91): different corpora
- 4B contribution: 68 cells (48 transformed, 20 abstain)
- 9B Conditional23: 23 cells (23 assert removals, 23 partial repairs)

---

## H3: Empty Suite Pass Insertion
**Rule ID**: `empty_suite_pass_insertion_v0`  
**Status**: `development_candidate_not_frozen` (criterion A met: deterministic, zero regression)

**Existing600 Evidence** (600 cells):
| Metric | Value |
|--------|------:|
| Triggered | 3 |
| Transformed (parse rescue) | 3 |
| Transformed Known-Pass | **0** |
| Preserved Known-Pass | **151** |
| Known-Pass Regression | **0** |
| EvalPlus Executed | **false** |
| New Verified Rescue | **0** |
| New Execution Regression | **not_evaluated** |

**Mechanism**: Inserts single `pass` statement into compound statements (if/for/while/try) when SyntaxError uniquely indicates "expected an indented block". Deterministic; 14-guard eligibility.

**H2 Roster (91 cells)**: H3 triggered 0 (no SyntaxError in this cohort).

**Rationale for Not Frozen**: 
- 3 parse rescues (syntactic recovery) demonstrated
- Zero regression confirmed on 691-cell combined dataset
- No execution-level rescue (EvalPlus not executed)
- Eligible for prospective validation

---

## Top-Level Demo Print Quarantine (Candidate)
**Rule ID**: `top_level_literal_only_demo_print_quarantine_v0`  
**Status**: `development_candidate_not_frozen` (criterion A met: deterministic, zero regression)

**Development Eval** (4B 200 + 9B 300 = 500 cells):
| Metric | Value |
|--------|------:|
| Static Hit | 21 |
| Abstained | 479 |
| Preserved Raw PASS | 17 |
| Unchanged Failure | 4 |
| Verified Rescue | **0** |
| Regression | **0** |

**Mechanism**: Quarantines module-level demo `print()` (literal arguments, adjacent to assert) behind `if __name__ == "__main__":`.

**Rationale for Not Frozen**: Deterministic and safe; zero regression. No verified rescue in development data; awaits prospective validation.

---

## Ab2g: Generic Scaffold Enhancement
**qwen3.5 Performance**:
| Benchmark | Base | Plus |
|-----------|---:|---:|
| HumanEval | 44/164 (26.83%) | N/A |
| MBPP | 176/378 (46.56%) | 129/378 (34.13%) |

**Status**: Deployed; serves as baseline for H1/H2/H3 assessment.

---

## Ab2A & Ab2gA-short-v1: Adaptation Variants
**Status**: Results generated but not prioritized for Stage2 consolidation.

---

## 0.6B Extended Experiment (qwen3.5:0.6b)
**Status**: Generated across HumanEval/MBPP; results entry but governance not yet integrated.

| Model | HumanEval Plus | MBPP Plus |
|-------|---:|---:|
| Ab1 | 2/164 (1.22%) | 31/378 (8.20%) |
| Ab2g | 34/164 (20.73%) | 129/378 (34.13%) |

**Governance Note**: Cannot substitute for 4B/9B conclusions; awaits extraction/taxonomy integration.

---

## 20-Task Validation Subset
**Coverage**: 20 representative problems for manual validation.  
**Status**: Maintained for spot-check verification.

---

## Confirmatory Benchmark
**Status**: Not yet executed.  
**Next Step**: Only after H1/H2/H3 candidates complete prospective qualification on independent holdout data.

---

## Three-Account Separation (Maintained)
1. **Raw/H0**: Original generation output
2. **Pipeline-Corrected**: After extraction/normalization (no repair)
3. **Post-Healer**: After deterministic transformation (H1→H2→H3)

Packaging fixes (Markdown, code fences) never counted as Healer rescue.

---

## Key Rules Enforced
- ✓ Verified rescue = strict FAIL→PASS only
- ✓ Partial repair ≠ PASS; never conflated with rescue
- ✓ Abstain is safety-first design, not gap
- ✓ Regression independently accounted (never offset against rescue)
- ✓ Development evidence ≠ confirmatory (prospective needed)
- ✓ No cross-layer statistical aggregation (Existing600 ≠ H2 roster)
