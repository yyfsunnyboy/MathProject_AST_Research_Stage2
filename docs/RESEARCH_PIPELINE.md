# Stage2 Research Pipeline & Outcome Classification

## End-to-End Pipeline Flow

```
Prompt
  ↓
Raw Generation (Model)
  ├─→ Ab1 (baseline)
  ├─→ Ab2g (generic scaffold)
  ├─→ Ab2A / Ab2gA-short-v1 (variants)
  └─→ 0.6B extended (model variant)
  ↓
H0: Pipeline-Normalized Source (extraction, formatting correction, no repair)
  ↓
H1: Entry-Point Alias Transformation
  Rule: entrypoint_alias_unique_arity_compatible_v0 (FROZEN)
  Decision: Apply if unique single entry point detected
  ↓
H2: Module-Level Assert Quarantine
  Rule: module_assert_entrypoint_selftest_quarantine_v0 (development_candidate_not_frozen)
  Decision: Quarantine self-test assert behind if __name__ == "__main__"
  ↓
H3: Empty Suite Pass Insertion
  Rule: empty_suite_pass_insertion_v0 (development_candidate_not_frozen)
  Decision: Insert pass into compound statement (if/for/while/try) on empty-suite SyntaxError
  ↓
Future Expansion (H4+): Not yet implemented
  Status: TBD (requires new deterministic candidate discovery)
  ↓
EvalPlus: Strict Pass/Fail Evaluation
  (NOT re-run for cumulative pipeline in this phase; reserved for prospective validation)
```

---

## Outcome Classification

Each program's journey maps to exactly one outcome per stage.

### H1 Outcomes

| Outcome | Definition | Example |
|---------|-----------|---------|
| **Transformed** | Entry point created or aliased; source changed | `def helper(x): ...` → `def solve(x): ...; solve = helper` |
| **Abstained** | Entry point found and correct arity; no change needed | Entry point already exists with compatible arity |
| **No-op** | Rule not triggered (rare; see: correct program) | No rule-triggering condition met |

**Paired Outcome** (Existing600, development-only):
- **Verified Rescue**: H0 strict FAIL → H1 strict PASS (9 cases)
- **Regression**: H0 strict PASS → H1 strict FAIL (0 cases)
- **Preserved Pass**: H0 PASS → H1 PASS (151 cases)
- **Unchanged Failure**: H0 FAIL → H1 FAIL (440 cases)

---

### H2 Outcomes

| Outcome | Definition | Count |
|---------|-----------|-------|
| **Transformed (Blocker Removed)** | Module-level assert quarantined; source changed | 71 |
| **Abstained** | Cannot safely quarantine (multiple asserts, etc.) | 20 |

**Execution Outcome** (H2 roster, 91 cells):
- **Partial Repair**: H2 blocks removed, but execution still fails (46 cases)
- **Preserved Pass**: Raw PASS unchanged by H2 (25 cases)
- **Unchanged Failure**: H2 did not transform; remains fail (20 cases)
- **Verified Rescue**: Would require strict FAIL→PASS at H2 level (0 cases in development)

**Critical**: Do NOT conflate:
- Blocker removed (71) ≠ Verified rescue (0)
- Partial repair (46) ≠ PASS (only 25 raw PASS preserved)

---

### H3 Outcomes

| Outcome | Definition | Count (Existing600) |
|---------|-----------|-------|
| **Transformed (Parse Rescue)** | Pass inserted into empty suite; syntactic error fixed | 3 |
| **Abstained** | SyntaxError not uniquely empty-suite, or 14 guards fail | 597 |

**Execution Outcome** (691 cells: 600 Existing600 + 91 H2 roster):
- **Deterministic Transformation**: 3 cells (Existing600 only)
- **Parse Recovery**: SyntaxError → ast.parse success (3 cases)
- **Known-Pass Transformed**: 0 (none of 3 transformed were raw PASS)
- **Known-Pass Preserved**: 151 (all Existing600 PASS abstained by H3)
- **Known-Pass Regression**: 0 (no PASS → SyntaxError)
- **EvalPlus Validation**: Not executed (evalplus_executed=false)
- **Verified Rescue**: 0 (no strict FAIL→PASS at execution level; would require EvalPlus)
- **New Execution Regression**: Not evaluated (EvalPlus not re-run)

**Critical**: Do NOT claim:
- 691 cells "executed successfully" (only 691 deterministic transformations replayed; H3 itself 0 execution impact on 91 H2 roster)
- "zero execution regression" (should be "zero known-pass regression", and note "execution regression not evaluated")
- Parse rescue (3) as verified rescue (requires execution validation)

---

### Future H4+ Outcomes

**Status**: No new deterministic candidate discovered and implemented as of 2026-07-25.

**Planning Criteria**:
1. Must identify new deterministic local repair mechanism
2. Must find in existing 372-cell inventory or new corpus analysis
3. Must have 14+ guard conditions like H1/H2/H3
4. Must prove zero regression on development cohort
5. Cannot be semantic/algorithm repair (abstain boundary)
6. Cannot reuse Task ID white-list (reject task-specific rules)

**Next Step**: Prospective validation of H1/H2/H3 candidates on independent holdout data before attempting H4 implementation.

---

## Outcome Aggregation Rules

### Correct Aggregation

✓ **By Stage** (mutually exclusive within each):
```
Existing600 (600):
  H1_ONLY: 41
  H2_ONLY: 114
  H3_ONLY: 3
  UNCHANGED: 442
  Total: 600
```

✓ **By Cohort** (H2 roster independent from Existing600):
```
H2 Roster (91):
  H1_AND_H2: 0
  H1_ONLY: 7
  H2_ONLY: 71
  H3_ONLY: 0
  UNCHANGED: 13
  Total: 91
```

✓ **By Outcome Class** (non-overlapping):
```
Verified Rescue (Existing600 only): 9 (H1 only, frozen evidence)
Parse Rescue (H3 only, Existing600): 3 (deterministic; EvalPlus not executed)
Partial Repair (H2 roster only): 46 (asynchronous with H1 rescue count)
Preserved Pass (across all): 151 + 25 = 176 (no duplication)
Regression: 0 (consistent across all stages)
```

### Incorrect Aggregation

✗ `442 (Existing600 UNCHANGED) + 597 (H3 abstained on all 600)` = double-count same cells  
✗ `71 (H2 blocker removed) = 71 (verified rescue)` = confusing mechanism with outcome  
✗ `46 (partial repair) + 9 (verified rescue) = 55 total rescue` = conflating categories  
✗ `691 (600 + 91) execution regressions = 0` = should specify "known-pass regression"; "execution regression not evaluated"  
✗ `3 parse rescue + 0 verified = 3 total rescue` = if said without caveat that EvalPlus not executed

---

## Coloring by Evidence Level & Freeze Status

### Frozen Evidence (Existing600 H1 only)

| Level | H1 Status | Evidence Base |
|-------|-----------|---|
| Paired Analysis | Frozen | 600 paired (H0 → H1) + EvalPlus outcome |
| Verified Rescue | Frozen | 9 FAIL → PASS strict |
| Regression | Frozen | 0 PASS → FAIL strict |

**Why Frozen**: Original Existing600 H1 decision completed; prospective qualification deferred for future holdout.

### Development Evidence (H2, H3, demo-print)

| Level | Status | Validation | Next Step |
|-------|--------|------------|-----------|
| H2: 71 blocker removed, 0 regression | `development_candidate_not_frozen` | ✓ Zero regression; no verified rescue | Prospective on holdout |
| H3: 3 parse rescue, 0 regression | `development_candidate_not_frozen` | ✓ Deterministic replay; EvalPlus not executed | Prospective on holdout |
| Demo-print: 21 hit, 0 regression | `development_candidate_not_frozen` | ✓ Zero regression; no verified rescue | Prospective on holdout |

**Why Not Frozen**: Development-level evidence sufficient for safety (zero regression, deterministic, guards sound), but no verified rescue in development data. Prospective validation on independent holdout required before v1 freeze.

---

## Key Principles (Non-Negotiable)

1. **FAIL→PASS Only**: Only strict H0 FAIL → post-Healer strict PASS counts as `verified_rescue`.
2. **Partial Repair ≠ Rescue**: Blocker removed but answer still wrong = fail-to-fail improvement, NOT rescue.
3. **Three Accounts**: Raw ≠ Pipeline-Corrected ≠ Post-Healer. Packaging fixes never count as Healer rescue.
4. **Abstain is Victory**: When uncertain, do NOT transform. Safety > rescue count.
5. **No Cross-Cohort Merge**: Existing600 (600) and H2 roster (91) are independent; never sum them as "691 cells" without specifying cohort.
6. **Development ≠ Confirmatory**: Multiple seeds replicating = good for development; orthogonal data required for confirmatory claim.
7. **No Stage Bleeding**: Do not sum abstain counts across stages (442 + 597 ≠ meaningful aggregate).

---

## Transition to Prospective Validation

Once H1/H2/H3 reach `development_candidate_not_frozen` status:

1. **Scope**: New independent holdout dataset (not used in rule design or parameter tuning).
2. **Execution**: Full EvalPlus run to measure execution-level rescue.
3. **Success Criteria**:
   - Zero regression on holdout
   - At least 1 verified rescue (or established policy: blocker removal alone sufficient)
   - Consistent decision-making (idempotence, no flips)
4. **Outcome**: Supports upgrade to frozen v1 (if successful) or revision to candidate (if issues found).

---

## Current Phase Status

- ✓ H1: Frozen (9 verified rescue, 0 regression; Existing600 development)
- ✓ H2: Development candidate (71 blocker removed, 0 regression; 91-cell cohort; prospective TBD)
- ✓ H3: Development candidate (3 parse rescue, 0 regression; 691-cell replay; EvalPlus deferred; prospective TBD)
- ✓ Demo-print: Development candidate (21 hit, 0 regression; 500-cell cohort; prospective TBD)
- ✗ H4+: Not yet identified or implemented
- ✗ Prospective Validation: Not yet executed (all candidates waiting)
- ✗ Confirmatory Benchmark: Not yet executed (reserved for post-prospective)
