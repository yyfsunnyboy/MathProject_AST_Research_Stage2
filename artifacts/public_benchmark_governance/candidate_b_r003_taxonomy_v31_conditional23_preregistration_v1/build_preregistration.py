import sys
import csv
import json
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parents[3]))

from scripts.build_candidate_b_r003_198cell_taxonomy_report import load_normalized_records

# Define tag sets for mechanical derivation of secondary-error grouping
ALGO_TAGS = {"algorithmic_error", "edge_case_omission"}
MATH_TAGS = {"mathematical_error", "parameter_semantics_swap"}
FLOW_TAGS = {"control_flow_failure", "semantic_goal_drift"}

def get_provisional_family_and_tags(r):
    mechs = r["mechanisms"]
    matched_algo = sorted(list(set(mechs) & ALGO_TAGS))
    matched_math = sorted(list(set(mechs) & MATH_TAGS))
    matched_flow = sorted(list(set(mechs) & FLOW_TAGS))
    
    all_matched = sorted(list(set(matched_algo + matched_math + matched_flow)))
    
    # Priority hierarchy rules:
    # 1. ALGO: If any algorithm-related tag matches.
    # 2. MATH: Else if any math-related tag matches.
    # 3. FLOW: Else if any flow-related tag matches (or as fallback).
    if matched_algo:
        family = "MECH_FAMILY_ASSERT_MASKED_ALGO"
    elif matched_math:
        family = "MECH_FAMILY_ASSERT_MASKED_MATH"
    else:
        family = "MECH_FAMILY_ASSERT_MASKED_FLOW"
        
    return family, all_matched

def build():
    # 1. Load normalized records from official builder
    records, _ = load_normalized_records()
    conditional_records = [r for r in records if r["healer"] == "conditional"]
    
    # Sort conditional records by cell_identity_sha256 to ensure byte-level determinism
    conditional_records = sorted(conditional_records, key=lambda x: x["cell_identity_sha256"])
    
    assert len(conditional_records) == 23, f"Expected 23 conditional records, got {len(conditional_records)}"
    
    # 2. Establish Evidence Clusters
    # Group by source_sha256
    clusters = {}
    for r in conditional_records:
        src_sha = r["source_sha256"]
        if src_sha not in clusters:
            clusters[src_sha] = []
        clusters[src_sha].append(r["cell_identity_sha256"])
    
    sorted_src_shas = sorted(list(clusters.keys()))
    cluster_mapping = {}
    for idx, src_sha in enumerate(sorted_src_shas):
        cluster_id = f"EVID_CLUSTER_{idx+1:03d}"
        cluster_mapping[src_sha] = cluster_id
        
    # Write evidence cluster ledger
    out_dir = Path(__file__).parent
    ledger_path = out_dir / "evidence_cluster_ledger.csv"
    with open(ledger_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["evidence_cluster_id", "task_id", "source_hash", "cell_count", "cell_ids"])
        for src_sha in sorted_src_shas:
            cluster_id = cluster_mapping[src_sha]
            cells_in_cluster = sorted(clusters[src_sha])
            # Find task_id (from first matching cell)
            task_id = next(r["task_id"] for r in conditional_records if r["source_sha256"] == src_sha)
            writer.writerow([cluster_id, task_id, src_sha, len(cells_in_cluster), json.dumps(cells_in_cluster)])
            
    # 3. Build conditional23 candidate roster (removed redundant source_id column)
    roster_path = out_dir / "conditional23_candidate_roster.csv"
    with open(roster_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "cell_id", "dataset", "condition", "task_id", "source_hash", "seed",
            "pipeline_corrected_artifact_path", "artifact_sha256", "taxonomy_version",
            "primary_layer", "secondary_tags", "outcome_status", "exception_class",
            "original_conditional_reason", "algorithm_reconstruction_required",
            "evidence_cluster_id", "provisional_mechanism_family_id", "matched_tags", "source_record_path"
        ])
        for r in conditional_records:
            cell_id = r["cell_identity_sha256"]
            dataset = "MBPP+"
            condition = "H0"
            task_id = r["task_id"]
            source_hash = r["source_sha256"]
            seed = r["seed"]
            # Path to pipeline normalized jsonl
            corrected_path = f"artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/{r['model_run']}/h0_h1_accounts.jsonl"
            artifact_sha = r["source_sha256"]
            tax_ver = "v3.1"
            primary_layer = r["primary"]
            secondary_tags = json.dumps(r["secondary"])
            outcome_status = r["outcome_validity"]
            exception_class = "module_level_executable_assertion"
            reason = r["reason"]
            
            # Dynamic calculation of algorithm_reconstruction_required
            algo_recon = str("algorithm_reconstruction_required" in r["mechanisms"])
            
            cluster_id = cluster_mapping[r["source_sha256"]]
            family_id, matched_tags = get_provisional_family_and_tags(r)
            source_rec = Path(r["authority_record"]).resolve().relative_to(Path(__file__).resolve().parents[3]).as_posix()
            
            writer.writerow([
                cell_id, dataset, condition, task_id, source_hash, seed,
                corrected_path, artifact_sha, tax_ver, primary_layer, secondary_tags,
                outcome_status, exception_class, reason, algo_recon, cluster_id,
                family_id, json.dumps(matched_tags), source_rec
            ])

    # 4. Build mechanism-family registry
    family_registry = {
        "status": "DRAFT_AWAITING_INDEPENDENT_AUDIT",
        "description": "Registry of provisional secondary-error grouping derived from mechanisms tags priority hierarchy.",
        "grouping_rules": {
            "priority_hierarchy": [
                "1. MECH_FAMILY_ASSERT_MASKED_ALGO: Matches algorithmic_error or edge_case_omission",
                "2. MECH_FAMILY_ASSERT_MASKED_MATH: Matches mathematical_error or parameter_semantics_swap",
                "3. MECH_FAMILY_ASSERT_MASKED_FLOW: Matches control_flow_failure or semantic_goal_drift (or fallback)"
            ],
            "overlap_handling": "Cells matching multiple sets of tags are assigned to the highest priority family. All matched tags are tracked in the matched_tags roster column."
        },
        "provisional_families": {
            "MECH_FAMILY_ASSERT_MASKED_ALGO": {
                "family_id": "MECH_FAMILY_ASSERT_MASKED_ALGO",
                "description": "Provisional secondary-error grouping: assertion-masked algorithmic logic or edge case omissions.",
                "mechanism_hypothesis": "Model-injected top-level assertions fail during module import, masking underlying algorithmic logic or edge case omissions in the core functions.",
                "member_cell_ids": [],
                "distinct_tasks": [],
                "distinct_sources": [],
                "evidence_cluster_count": 0,
                "existing_supporting_evidence": "All member cells contain 'module_level_executable_assertion' and 'algorithmic_error' or 'edge_case_omission'.",
                "unresolved_ambiguities": "Exact semantic correction requires context-dependent code transformations that are not uniquely defined.",
                "algorithm_reconstruction_overlap": [],
                "current_status": "INSUFFICIENT_EXISTING_EVIDENCE",
                "transformation_template": "ABSTAIN",
                "transformation_spec": "NONE_UNDER_CURRENT_EVIDENCE"
            },
            "MECH_FAMILY_ASSERT_MASKED_MATH": {
                "family_id": "MECH_FAMILY_ASSERT_MASKED_MATH",
                "description": "Provisional secondary-error grouping: assertion-masked mathematical errors or formula swaps.",
                "mechanism_hypothesis": "Model-injected top-level assertions fail during module import, masking underlying mathematical errors or formula swaps in the core functions.",
                "member_cell_ids": [],
                "distinct_tasks": [],
                "distinct_sources": [],
                "evidence_cluster_count": 0,
                "existing_supporting_evidence": "All member cells contain 'module_level_executable_assertion' and 'mathematical_error' or 'parameter_semantics_swap'.",
                "unresolved_ambiguities": "Formulas or floating-point limits are not uniquely restorable without looking at canonical solutions/hidden tests.",
                "algorithm_reconstruction_overlap": [],
                "current_status": "INSUFFICIENT_EXISTING_EVIDENCE",
                "transformation_template": "ABSTAIN",
                "transformation_spec": "NONE_UNDER_CURRENT_EVIDENCE"
            },
            "MECH_FAMILY_ASSERT_MASKED_FLOW": {
                "family_id": "MECH_FAMILY_ASSERT_MASKED_FLOW",
                "description": "Provisional secondary-error grouping: assertion-masked control flow failures or goal drift.",
                "mechanism_hypothesis": "Model-injected top-level assertions fail during module import, masking control flow failures or goal drift under non-numeric input bounds.",
                "member_cell_ids": [],
                "distinct_tasks": [],
                "distinct_sources": [],
                "evidence_cluster_count": 0,
                "existing_supporting_evidence": "All member cells contain 'module_level_executable_assertion' and 'control_flow_failure' or 'semantic_goal_drift'.",
                "unresolved_ambiguities": "Handling loop terminations and exception blocks requires custom control logic design.",
                "algorithm_reconstruction_overlap": [],
                "current_status": "INSUFFICIENT_EXISTING_EVIDENCE",
                "transformation_template": "ABSTAIN",
                "transformation_spec": "NONE_UNDER_CURRENT_EVIDENCE"
            }
        }
    }
    
    for r in conditional_records:
        family_id, _ = get_provisional_family_and_tags(r)
        fam = family_registry["provisional_families"][family_id]
        fam["member_cell_ids"].append(r["cell_identity_sha256"])
        fam["distinct_tasks"].append(r["task_id"])
        fam["distinct_sources"].append(r["source_sha256"])
        
        # Dynamic calculation of algorithm_reconstruction overlap inside members of family
        if "algorithm_reconstruction_required" in r["mechanisms"]:
            fam["algorithm_reconstruction_overlap"].append(r["cell_identity_sha256"])
        
    for fam in family_registry["provisional_families"].values():
        fam["member_cell_ids"] = sorted(list(set(fam["member_cell_ids"])))
        fam["distinct_tasks"] = sorted(list(set(fam["distinct_tasks"])))
        fam["distinct_sources"] = sorted(list(set(fam["distinct_sources"])))
        fam["evidence_cluster_count"] = len(fam["distinct_sources"])
        fam["algorithm_reconstruction_overlap"] = sorted(list(set(fam["algorithm_reconstruction_overlap"])))
        
    registry_path = out_dir / "mechanism_family_registry.json"
    with open(registry_path, "w", encoding="utf-8") as f:
        json.dump(family_registry, f, indent=2, ensure_ascii=False)
        
    # 5. Build decision schema
    decision_schema = {
        "status": "DRAFT_AWAITING_INDEPENDENT_AUDIT",
        "description": "Rules governing the state transitions of provisional mechanism grouping families.",
        "promotion_rules": {
            "to_eligible_for_implementation": {
                "required_conditions": [
                    "Deterministic transformation template is uniquely defined",
                    "Safety guards cover all 4 layers (Identity, Detection, Uniqueness, Semantic-risk)",
                    "Evidence matches cross-task requirement (at least 2 distinct tasks, 2 distinct sources)",
                    "No algorithm reconstruction required in any member cell",
                    "Answer-free and evaluator-blind validation passes",
                    "All member cells resolved to zero semantic-risk"
                ]
            }
        },
        "retention_rules": {
            "keep_as_provisional": {
                "conditions": [
                    "Underlying mechanisms are verified, but a deterministic transformation is not yet established",
                    "Insufficient independent evidence exists (e.g., covers only 1 task or 1 source)",
                    "Diagnostics require further data collection/execution trace without violating semantic safety"
                ]
            }
        },
        "elimination_rules": {
            "to_abstain_or_ineligible": {
                "conditions": [
                    "Correcting the failure requires algorithm reconstruction (e.g., rewriting loops, conditionals, or data structures)",
                    "Fixing the bug requires guessing the model intent or hardcoding constants",
                    "Removal of surface exception exposes unresolvable logical flaws"
                ]
            }
        }
    }
    with open(out_dir / "decision_schema.json", "w", encoding="utf-8") as f:
        json.dump(decision_schema, f, indent=2, ensure_ascii=False)

    # 6. Dynamically write diagnostics_guard_preregistration.md
    algo_tasks_str = ", ".join(family_registry["provisional_families"]["MECH_FAMILY_ASSERT_MASKED_ALGO"]["distinct_tasks"])
    math_tasks_str = ", ".join(family_registry["provisional_families"]["MECH_FAMILY_ASSERT_MASKED_MATH"]["distinct_tasks"])
    flow_tasks_str = ", ".join(family_registry["provisional_families"]["MECH_FAMILY_ASSERT_MASKED_FLOW"]["distinct_tasks"])

    algo_cell_count = len(family_registry["provisional_families"]["MECH_FAMILY_ASSERT_MASKED_ALGO"]["member_cell_ids"])
    math_cell_count = len(family_registry["provisional_families"]["MECH_FAMILY_ASSERT_MASKED_MATH"]["member_cell_ids"])
    flow_cell_count = len(family_registry["provisional_families"]["MECH_FAMILY_ASSERT_MASKED_FLOW"]["member_cell_ids"])

    md_template = """# Diagnostics & Guard Preregistration Card Suite

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
3. **Supporting Members**: {algo_cell_count} cell IDs ({algo_tasks}).
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
3. **Supporting Members**: {math_cell_count} cell IDs ({math_tasks}).
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
3. **Supporting Members**: {flow_cell_count} cell IDs ({flow_tasks}).
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
"""
    md_content = md_template.format(
        algo_cell_count=algo_cell_count,
        algo_tasks=algo_tasks_str,
        math_cell_count=math_cell_count,
        math_tasks=math_tasks_str,
        flow_cell_count=flow_cell_count,
        flow_tasks=flow_tasks_str
    )
    
    with open(out_dir / "diagnostics_guard_preregistration.md", "w", encoding="utf-8") as f:
        f.write(md_content)

    print("Preregistration draft files written successfully.")

if __name__ == "__main__":
    build()
