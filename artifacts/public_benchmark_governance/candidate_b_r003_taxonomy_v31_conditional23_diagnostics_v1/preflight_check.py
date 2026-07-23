import sys
import json
import csv
import hashlib
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parents[3]))

def compute_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def validate_evidence_format(ev: dict, expected_fingerprint: str):
    # Schema check based on diagnostics_schema.json
    required_keys = ["cell_id", "task_id", "source_hash", "fingerprint", "preflight_passed", "ast_diagnostics", "execution_diagnostics", "decision"]
    for k in required_keys:
        assert k in ev, f"Missing key: {k}"
        
    # Check types and values
    assert isinstance(ev["cell_id"], str)
    assert isinstance(ev["task_id"], str)
    assert isinstance(ev["source_hash"], str)
    assert isinstance(ev["preflight_passed"], bool)
    assert isinstance(ev["ast_diagnostics"], dict)
    assert isinstance(ev["execution_diagnostics"], dict)
    assert isinstance(ev["decision"], dict)
    
    # Fingerprint validation
    fp = ev["fingerprint"]
    assert isinstance(fp, str), "Fingerprint must be a string"
    assert len(fp) == 64, "Fingerprint must be 64 characters long"
    assert all(c in "0123456789abcdef" for c in fp), "Fingerprint must be a valid hex string"
    assert fp == expected_fingerprint, f"Fingerprint mismatch! Expected {expected_fingerprint[:8]}, got {fp[:8]}"
    
    # AST diagnostics
    ast_keys = ["has_top_level_assert", "top_level_assert_count", "assert_node_lines"]
    for k in ast_keys:
        assert k in ev["ast_diagnostics"], f"Missing AST key: {k}"
    assert isinstance(ev["ast_diagnostics"]["has_top_level_assert"], bool)
    assert isinstance(ev["ast_diagnostics"]["top_level_assert_count"], int)
    assert isinstance(ev["ast_diagnostics"]["assert_node_lines"], list)
    
    # Execution diagnostics (CRITICAL verification of zero-execution during preflight)
    exec_keys = ["executed", "exit_code", "stdout", "stderr", "error_message"]
    for k in exec_keys:
        assert k in ev["execution_diagnostics"], f"Missing Execution key: {k}"
    assert ev["execution_diagnostics"]["executed"] is False, "Execution occurred during preflight!"
    assert ev["execution_diagnostics"]["exit_code"] is None
    assert isinstance(ev["execution_diagnostics"]["stdout"], str)
    assert isinstance(ev["execution_diagnostics"]["stderr"], str)
    
    # Decision (Must always be INSUFFICIENT_EXISTING_EVIDENCE and ABSTAIN)
    assert ev["decision"]["status"] == "INSUFFICIENT_EXISTING_EVIDENCE", "Decision status must be INSUFFICIENT_EXISTING_EVIDENCE"
    assert ev["decision"]["action"] == "ABSTAIN", "Decision action must be ABSTAIN"

def run_preflight():
    proj_root = Path(__file__).resolve().parents[3]
    
    print("Starting Conditional23 Static-Only Diagnostics Preflight...")
    
    # Load roster from frozen preregistration
    prereg_dir = proj_root / "artifacts" / "public_benchmark_governance" / "candidate_b_r003_taxonomy_v31_conditional23_preregistration_v1"
    roster_path = prereg_dir / "conditional23_candidate_roster.csv"
    
    with open(roster_path, "r", encoding="utf-8") as f:
        roster_rows = list(csv.DictReader(f))
        
    assert len(roster_rows) == 23, f"Expected 23 cells in roster, got {len(roster_rows)}"
    
    # Validate each existing evidence file
    diagnostics_dir = proj_root / "artifacts" / "public_benchmark_governance" / "candidate_b_r003_taxonomy_v31_conditional23_diagnostics_v1"
    
    for row in roster_rows:
        cell_id = row["cell_id"]
        task_id = row["task_id"]
        seed = int(row["seed"])
        source_hash = row["source_hash"]
        
        run_dir = diagnostics_dir / "runs" / cell_id
        evidence_path = run_dir / "diagnostic_evidence.json"
        
        assert evidence_path.exists(), f"Evidence file missing for cell {cell_id}"
        
        # Calculate expected fingerprint
        expected_fp = compute_sha256(json.dumps({
            "cell_id": cell_id,
            "task_id": task_id,
            "seed": seed,
            "source_hash": source_hash,
            "run_dir": str(run_dir)
        }, sort_keys=True))
        
        with open(evidence_path, "r", encoding="utf-8") as f:
            ev = json.load(f)
            
        validate_evidence_format(ev, expected_fp)
        
    print("Diagnostics Preflight Completed successfully! All 23 existing cell JSON outputs verified.")
    print("Preflight verification shows zero candidate-program execution and valid resume fingerprints.")

if __name__ == "__main__":
    run_preflight()
