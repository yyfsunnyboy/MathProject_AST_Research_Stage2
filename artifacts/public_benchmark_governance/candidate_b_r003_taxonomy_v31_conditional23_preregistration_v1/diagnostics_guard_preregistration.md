# Diagnostics & Guard Preregistration Card Suite

status: DRAFT_AWAITING_INDEPENDENT_AUDIT
- **Revision**: artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_conditional23_preregistration_v1
- **Focus**: Pre-registered specifications, diagnostics, safety guards, and decision rules for the 23 conditional cells.

> [!WARNING]
> This suite represents a **provisional grouping draft** awaiting independent audit. Disabling/removing top-level assertions is NOT pre-determined as a safe correction. Due to semantic and regression risks, the planned transformation template for all families is **ABSTAIN** and marked as **規格待實作** (specification only, not implemented).
> No candidate-program import/compile/execution will be performed.

---

## 📋 Grouping Priority and Overlap Resolution Rules

The provisional grouping families are derived mechanically from the mechanisms tags priority hierarchy:
1. **Priority 1: `MECH_FAMILY_ASSERT_MASKED_ALGO`**
   - *Matching Criteria*: Triggered if the cell mechanisms contain `algorithmic_error` or `edge_case_omission`.
2. **Priority 2: `MECH_FAMILY_ASSERT_MASKED_MATH`**
   - *Matching Criteria*: Triggered if Priority 1 is not met, and the cell mechanisms contain `mathematical_error` or `parameter_semantics_swap`.
3. **Priority 3: `MECH_FAMILY_ASSERT_MASKED_FLOW`**
   - *Matching Criteria*: Triggered if Priority 1 and 2 are not met, and the cell mechanisms contain `control_flow_failure` or `semantic_goal_drift` (or fallback).

Any cells matching multiple sets of tags are assigned to the highest priority family. The roster records the full list of matched tags under the `matched_tags` column to ensure complete transparency of overlaps.

---

## 🛡️ 4-Layer Guard Specification

All candidate repairs must pass every guard tier sequentially. If any guard fails, the Healer must immediately ABSTAIN.

### A. Identity Guard
- **Specification**: Validates that the artifact SHA-256 matches the candidate program ID exactly, the task contract matches the MBPP+ specification, and the execution condition is H0 (no H1 modifications have been pre-applied). Any drift in version or identity aborts healing.

### B. Detection Guard
- **Specification**: Validates that the failure is purely caused by a top-level (module-level) assertion during import (`module_level_executable_assertion`). This is verified via AST parsing showing that the assert statement lies at the top-level block. Exception class names alone are insufficient.

### C. Uniqueness Guard
- **Specification**: Validates that there is exactly one option for healing (e.g. disabling the assertion statement). If multiple assertions exist or if parsing leaves multiple viable entry points or structural ambiguities, the guard aborts.

### D. Semantic-Risk Guard
- **Specification**: Excludes any repairs that require algorithm reconstruction, intent guessing, loop alteration, control-flow injection, or hardcoded constants. If removing the assertion exposes logical, mathematical, or flow errors (L5), the guard triggers an immediate ABSTAIN.

---

## 📇 Preregistration Cards by Provisional Family

### 1. MECH_FAMILY_ASSERT_MASKED_ALGO

1. **Family ID**: `MECH_FAMILY_ASSERT_MASKED_ALGO`
2. **Mechanism Hypothesis**: Model-injected top-level assertions fail during module import, masking underlying algorithmic logic or edge case omissions in the core functions.
3. **Supporting Members**: 12 cell IDs (Mbpp/125, Mbpp/138, Mbpp/440, Mbpp/735, Mbpp/739, Mbpp/777).
4. **Allowed Evidence**: Coarse diagnostics reports showing assertion execution failure on module load; AST structure containing module-level `Assert` nodes.
5. **Prohibited Evidence**: Hidden test logs, evaluator pass/fail results used to select code patterns.
6. **Planned Diagnostic Procedure**: Run an offline AST-check to verify the presence of top-level `assert` statements.
7. **Detection Predicate**: `has_top_level_assert(ast) == True` and `has_algorithmic_secondary_tag(ledger) == True`.
8. **Ambiguity Test**: Check if the top-level assert statement has side-effects (e.g., calling functions that mutate state). If so, it is ambiguous.
9. **Transformation Template**: `ABSTAIN` (Do not apply changes - **規格待實作**).
10. **Semantic Invariant**: The function signature and pure mathematical semantics must remain invariant.
11. **Identity Guards**: Check that cell hash matches and task belongs to MBPP+.
12. **Detection Guards**: Confirm `module_level_executable_assertion` is the unique cause of L4 import failure.
13. **Uniqueness Guards**: Ensure there is only one top-level assertion statement whose removal is under analysis.
14. **Semantic-Risk Guards**: Trigger abstain if the function logic contains incomplete loops or off-by-one indices.
15. **Abstention Triggers**: Any ambiguity in assertion context or secondary tags.
16. **Positive-Case Specification**: Top-level assert matches public test assertion text exactly.
17. **Near-Miss Negative Specification**: Assert statement is inside a helper function or conditional block.
18. **Do-Not-Repair Specification**: Algorithm requires boundary fixes or edge-case handling.
19. **Promotion Criteria**: Must define a deterministic template that proves safe execution on all test cases without guessing.
20. **Retention Criteria**: Retained as provisional if algorithmic errors remain unresolved.
21. **Elimination Criteria**: Eliminated if repair requires writing custom algorithm logic.
22. **Minimum Independent-Evidence Requirement**: At least 2 distinct tasks, 2 distinct sources.
23. **Expected Diagnostic Outputs**: AST node locations of top-level assert.
24. **Uncertainty Handling**: Default to ABSTAIN.

---

### 2. MECH_FAMILY_ASSERT_MASKED_MATH

1. **Family ID**: `MECH_FAMILY_ASSERT_MASKED_MATH`
2. **Mechanism Hypothesis**: Model-injected top-level assertions fail during module import, masking underlying mathematical errors or formula swaps in the core functions.
3. **Supporting Members**: 9 cell IDs (Mbpp/430, Mbpp/432, Mbpp/581, Mbpp/742).
4. **Allowed Evidence**: AST structure containing module-level `Assert` nodes; mathematical domain classification.
5. **Prohibited Evidence**: Evaluator feedback, oracle outputs.
6. **Planned Diagnostic Procedure**: Check for top-level asserts; evaluate if the math formula is complete.
7. **Detection Predicate**: `has_top_level_assert(ast) == True` and `has_mathematical_secondary_tag(ledger) == True`.
8. **Ambiguity Test**: Check if the assertion checks floating point values using exact inequality rather than float tolerance.
9. **Transformation Template**: `ABSTAIN` (Do not apply changes - **規格待實作**).
10. **Semantic Invariant**: Math truth bounds (e.g. root extraction, float rounding) must be preserved.
11. **Identity Guards**: Cell SHA-256 and task ID matches.
12. **Detection Guards**: Verify L4 import is blocked by top-level assert.
13. **Uniqueness Guards**: Verify only one formula is subject to the assertion.
14. **Semantic-Risk Guards**: High risk. Abstain because formula corrections require deep mathematical knowledge.
15. **Abstention Triggers**: Any mathematical error requiring a new constant or formula change.
16. **Positive-Case Specification**: Assert statement fails due to floating point precision drift.
17. **Near-Miss Negative Specification**: Assert statement checks valid input domain constraint.
18. **Do-Not-Repair Specification**: Tetrahedron or trapezium formula is fundamentally wrong.
19. **Promotion Criteria**: Requires deterministic arithmetic template proving zero-precision-loss.
20. **Retention Criteria**: Retained due to mathematical safety risks.
21. **Elimination Criteria**: Eliminated if the core formula is incorrect.
22. **Minimum Independent-Evidence Requirement**: At least 2 distinct tasks, 2 distinct sources.
23. **Expected Diagnostic Outputs**: Float comparison bounds.
24. **Uncertainty Handling**: Default to ABSTAIN.

---

### 3. MECH_FAMILY_ASSERT_MASKED_FLOW

1. **Family ID**: `MECH_FAMILY_ASSERT_MASKED_FLOW`
2. **Mechanism Hypothesis**: Model-injected top-level assertions fail during module import, masking control flow failures or goal drift under non-numeric input bounds.
3. **Supporting Members**: 2 cell IDs (Mbpp/138, Mbpp/410).
4. **Allowed Evidence**: AST structure containing module-level `Assert` nodes; control-flow tags.
5. **Prohibited Evidence**: LLM-generated code rewrites.
6. **Planned Diagnostic Procedure**: Trace top-level assert and look for conditional exit paths in AST.
7. **Detection Predicate**: `has_top_level_assert(ast) == True` and secondary tags contain control-flow errors.
8. **Ambiguity Test**: If control flow contains multiple exits, loops, or recursion blocks.
9. **Transformation Template**: `ABSTAIN` (Do not apply changes - **規格待實作**).
10. **Semantic Invariant**: Original control block flow is unchanged.
11. **Identity Guards**: Cell SHA-256 and task ID matches.
12. **Detection Guards**: Verify load blocked by assertion check.
13. **Uniqueness Guards**: Exactly one loop structure exits prematurely.
14. **Semantic-Risk Guards**: Premature exit leads to wrong type output. Abstain.
15. **Abstention Triggers**: Any modification to condition boundaries or helper branches.
16. **Positive-Case Specification**: Top-level assert blocks correct data structure generation.
17. **Near-Miss Negative Specification**: Assert statement is inside a try-except statement.
18. **Do-Not-Repair Specification**: Loop execution requires restructuring.
19. **Promotion Criteria**: Non-intrusive flow template exists.
20. **Retention Criteria**: Retained under insufficient evidence.
21. **Elimination Criteria**: Eliminated if loop reconstruction is required.
22. **Minimum Independent-Evidence Requirement**: At least 2 distinct tasks, 2 distinct sources.
23. **Expected Diagnostic Outputs**: Control flow exit branches.
24. **Uncertainty Handling**: Default to ABSTAIN.
