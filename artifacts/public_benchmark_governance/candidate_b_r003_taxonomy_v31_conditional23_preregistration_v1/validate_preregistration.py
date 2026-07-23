import sys
import csv
import json
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parents[3]))

from scripts.build_candidate_b_r003_198cell_taxonomy_report import load_normalized_records

# Define tag sets for mechanical derivation verification
ALGO_TAGS = {"algorithmic_error", "edge_case_omission"}
MATH_TAGS = {"mathematical_error", "parameter_semantics_swap"}
FLOW_TAGS = {"control_flow_failure", "semantic_goal_drift"}

def run_validation():
    # 1. Zero candidate-program import/compile/execution confirmation:
    # No candidate-program import/compile/execution will be performed.
    # The validator purely inspects static files (CSV, JSON, Markdown).
    
    out_dir = Path(__file__).parent
    roster_path = out_dir / "conditional23_candidate_roster.csv"
    ledger_path = out_dir / "evidence_cluster_ledger.csv"
    registry_path = out_dir / "mechanism_family_registry.json"
    schema_path = out_dir / "decision_schema.json"
    doc_path = out_dir / "diagnostics_guard_preregistration.md"
    
    assert roster_path.exists(), "Roster file missing"
    assert ledger_path.exists(), "Ledger file missing"
    assert registry_path.exists(), "Registry file missing"
    assert schema_path.exists(), "Schema file missing"
    assert doc_path.exists(), "MD doc file missing"
    
    # 2. Read Roster
    with open(roster_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        roster_rows = list(reader)
        
    assert len(roster_rows) == 23, f"Roster must have exactly 23 cells, got {len(roster_rows)}"
    
    cell_ids = [row["cell_id"] for row in roster_rows]
    assert len(set(cell_ids)) == 23, "Cell IDs must be unique"
    
    # 3. Load 198-cell ledger records from official builder and verify cross-check
    records, _ = load_normalized_records()
    official_cond_cells = {r["cell_identity_sha256"]: r for r in records if r["healer"] == "conditional"}
    
    assert len(official_cond_cells) == 23, "Official conditional cells count mismatch"
    
    for row in roster_rows:
        cell_id = row["cell_id"]
        assert cell_id in official_cond_cells, f"Cell {cell_id} not found in official conditional cells"
        official = official_cond_cells[cell_id]
        
        # Verify alignment of key attributes
        assert row["task_id"] == official["task_id"], f"Task mismatch for {cell_id}"
        assert row["source_hash"] == official["source_sha256"], f"Source hash mismatch for {cell_id}"
        assert row["seed"] == str(official["seed"]), f"Seed mismatch for {cell_id}"
        assert row["primary_layer"] == official["primary"], f"Primary layer mismatch for {cell_id}"
        assert row["outcome_status"] == official["outcome_validity"], f"Outcome status mismatch for {cell_id}"
        assert row["dataset"] == "MBPP+", "Dataset must be MBPP+"
        assert row["condition"] == "H0", "Condition must be H0"
        
        # Verify dynamic calculation of algorithm_reconstruction_required
        expected_algo_recon = str("algorithm_reconstruction_required" in official["mechanisms"])
        assert row["algorithm_reconstruction_required"] == expected_algo_recon, f"Algorithm reconstruction flag mismatch for {cell_id}"
        assert "module_level_executable_assertion" in official["mechanisms"], "Must contain module_level_executable_assertion"
        
        # Verify matched tags and priority grouping alignment
        mechs = official["mechanisms"]
        matched_algo = sorted(list(set(mechs) & ALGO_TAGS))
        matched_math = sorted(list(set(mechs) & MATH_TAGS))
        matched_flow = sorted(list(set(mechs) & FLOW_TAGS))
        expected_matched = sorted(list(set(matched_algo + matched_math + matched_flow)))
        
        assert json.loads(row["matched_tags"]) == expected_matched, f"Matched tags mismatch for {cell_id}"
        
        if matched_algo:
            expected_family = "MECH_FAMILY_ASSERT_MASKED_ALGO"
        elif matched_math:
            expected_family = "MECH_FAMILY_ASSERT_MASKED_MATH"
        else:
            expected_family = "MECH_FAMILY_ASSERT_MASKED_FLOW"
            
        assert row["provisional_mechanism_family_id"] == expected_family, f"Family ID mapping mismatch for {cell_id}"
        
    # 4. Validate evidence clusters
    with open(ledger_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cluster_rows = list(reader)
        
    assert len(cluster_rows) == 20, f"Expected 20 evidence clusters (distinct sources), got {len(cluster_rows)}"
    
    # Verify that cells listed in clusters are exactly the 23 conditional cells
    cluster_cells = []
    for crow in cluster_rows:
        cells = json.loads(crow["cell_ids"])
        cluster_cells.extend(cells)
    assert sorted(cluster_cells) == sorted(cell_ids), "Cluster cells do not match roster cell IDs"
    
    # 5. Validate registry and families
    with open(registry_path, "r", encoding="utf-8") as f:
        registry = json.load(f)
        
    assert registry["status"] == "DRAFT_AWAITING_INDEPENDENT_AUDIT", "Status must be DRAFT_AWAITING_INDEPENDENT_AUDIT"
    families = registry["provisional_families"]
    assert len(families) == 3, "Expected 3 provisional families"
    
    total_family_members = []
    for fam_id, fam in families.items():
        assert fam["current_status"] in ["INSUFFICIENT_EXISTING_EVIDENCE", "PROVISIONAL_INELIGIBLE"], "Prohibited status found"
        assert fam["transformation_template"] == "ABSTAIN", "Prohibited transformation template found"
        assert fam["transformation_spec"] == "NONE_UNDER_CURRENT_EVIDENCE", "Prohibited transformation spec found"
        total_family_members.extend(fam["member_cell_ids"])
        
        # Verify count mapping
        assert fam["evidence_cluster_count"] == len(fam["distinct_sources"]), "Evidence cluster count drift"
        
        # Verify dynamic overlap matches
        for mcell in fam["member_cell_ids"]:
            official = official_cond_cells[mcell]
            has_algo_recon = "algorithm_reconstruction_required" in official["mechanisms"]
            if has_algo_recon:
                assert mcell in fam["algorithm_reconstruction_overlap"], "Overlap cell missing"
            else:
                assert mcell not in fam["algorithm_reconstruction_overlap"], "False overlap cell included"
        
    assert sorted(total_family_members) == sorted(cell_ids), "Family membership total does not match conditional cells"
    
    # 6. Validate Markdown Preregistration Cards, Counts, and Guards
    md_content = doc_path.read_text(encoding="utf-8")
    assert "status: DRAFT_AWAITING_INDEPENDENT_AUDIT" in md_content, "Status declaration missing from Markdown"
    
    # Verify MD counts and task lists against registry
    for fam_id, fam in families.items():
        count = len(fam["member_cell_ids"])
        tasks_str = ", ".join(fam["distinct_tasks"])
        expected_line = f"**Supporting Members**: {count} cell IDs ({tasks_str})."
        assert expected_line in md_content, f"Supporting members line mismatch in Markdown for {fam_id}. Expected: '{expected_line}'"
    
    # Verify exact required counts: ALGO=12, MATH=9, FLOW=2
    algo_count = len(families["MECH_FAMILY_ASSERT_MASKED_ALGO"]["member_cell_ids"])
    math_count = len(families["MECH_FAMILY_ASSERT_MASKED_MATH"]["member_cell_ids"])
    flow_count = len(families["MECH_FAMILY_ASSERT_MASKED_FLOW"]["member_cell_ids"])
    assert algo_count == 12, f"Expected ALGO=12, got {algo_count}"
    assert math_count == 9, f"Expected MATH=9, got {math_count}"
    assert flow_count == 2, f"Expected FLOW=2, got {flow_count}"
    assert algo_count + math_count + flow_count == 23, f"Expected sum=23, got {algo_count + math_count + flow_count}"
    
    # Ensure mandatory guards are declared
    mandatory_guards = ["Identity Guard", "Detection Guard", "Uniqueness Guard", "Semantic-Risk Guard"]
    for guard in mandatory_guards:
        assert guard in md_content, f"Mandatory guard check failed: '{guard}' not found in documentation"
        
    print("Zero-model validation passed successfully!")

if __name__ == "__main__":
    run_validation()
