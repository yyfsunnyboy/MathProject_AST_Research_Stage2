import os
import sys
import csv
import json
import ast
import hashlib
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parents[3]))

def compute_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def load_roster(roster_path: Path):
    with open(roster_path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def extract_candidate_code(accounts_path: Path, task_id: str, seed: int) -> str:
    """Extract h0 code from the accounts jsonl file without importing it."""
    if not accounts_path.exists():
        raise FileNotFoundError(f"Accounts file not found: {accounts_path}")
    with open(accounts_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            data = json.loads(line)
            if data.get("task_id") == task_id and data.get("seed") == seed and data.get("factorial_arm") == "Candidate_B_H0":
                return data.get("evaluation_source", "")
    raise ValueError(f"Task {task_id} with seed {seed} and H0 arm not found in {accounts_path}")

def analyze_ast(code: str):
    """Statically parse the AST of the candidate program.
    NO compilation or import/execution is performed.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return {
            "has_top_level_assert": False,
            "top_level_assert_count": 0,
            "assert_node_lines": [],
            "syntax_error": str(e)
        }
        
    assert_lines = []
    # Traverse only the top-level statements
    for node in tree.body:
        if isinstance(node, ast.Assert):
            assert_lines.append(node.lineno)
            
    return {
        "has_top_level_assert": len(assert_lines) > 0,
        "top_level_assert_count": len(assert_lines),
        "assert_node_lines": assert_lines
    }

def run_cell_diagnostics(cell_id: str, proj_root: Path, force: bool = False) -> dict:
    prereg_dir = proj_root / "artifacts" / "public_benchmark_governance" / "candidate_b_r003_taxonomy_v31_conditional23_preregistration_v1"
    roster_path = prereg_dir / "conditional23_candidate_roster.csv"
    
    roster = load_roster(roster_path)
    matched_row = next((row for row in roster if row["cell_id"] == cell_id), None)
    if not matched_row:
        raise ValueError(f"Cell ID {cell_id} not found in the frozen roster")
        
    # Identity and security validation
    task_id = matched_row["task_id"]
    source_hash = matched_row["source_hash"]
    seed = int(matched_row["seed"])
    dataset = matched_row["dataset"]
    condition = matched_row["condition"]
    
    if dataset != "MBPP+" or condition != "H0":
        raise ValueError(f"Invalid dataset/condition: {dataset}/{condition} for cell {cell_id}")
        
    # Extract candidate code
    accounts_rel_path = matched_row["pipeline_corrected_artifact_path"]
    accounts_path = proj_root / accounts_rel_path
    
    code = extract_candidate_code(accounts_path, task_id, seed)
    
    # Verify hash identity
    actual_hash = compute_sha256(code)
    if actual_hash != source_hash:
        raise ValueError(f"SHA-256 hash mismatch for cell {cell_id}. Roster: {source_hash[:8]}, Actual: {actual_hash[:8]}")
        
    # Isolation directory setup
    run_dir = proj_root / "artifacts" / "public_benchmark_governance" / "candidate_b_r003_taxonomy_v31_conditional23_diagnostics_v1" / "runs" / cell_id
    evidence_path = run_dir / "diagnostic_evidence.json"
    
    # Resume checking: skipped only if fingerprint and files match
    fingerprint = compute_sha256(json.dumps({
        "cell_id": cell_id,
        "task_id": task_id,
        "seed": seed,
        "source_hash": source_hash,
        "run_dir": str(run_dir)
    }, sort_keys=True))
    
    if not force and evidence_path.exists():
        try:
            with open(evidence_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
            if existing.get("fingerprint") == fingerprint and existing.get("preflight_passed") == True:
                print(f"Skipping cell {cell_id} (resume fingerprint match)")
                return existing
        except Exception:
            pass # Re-run if file reading failed
            
    run_dir.mkdir(parents=True, exist_ok=True)
    
    # Execute static AST diagnostics
    ast_res = analyze_ast(code)
    
    # Execution Diagnostics (Zero-execution preflight: we do not run candidate code)
    exec_res = {
        "executed": False,
        "exit_code": None,
        "stdout": "",
        "stderr": "",
        "error_message": "Candidate execution prohibited during preflight phase"
    }
    
    # Decision matching decision_schema.json
    decision = {
        "status": "INSUFFICIENT_EXISTING_EVIDENCE",
        "action": "ABSTAIN"
    }
    
    evidence = {
        "cell_id": cell_id,
        "task_id": task_id,
        "source_hash": source_hash,
        "preflight_passed": True,
        "fingerprint": fingerprint,
        "ast_diagnostics": ast_res,
        "execution_diagnostics": exec_res,
        "decision": decision
    }
    
    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2, ensure_ascii=False)
        
    print(f"Completed diagnostics for cell {cell_id}")
    return evidence

def run_all(proj_root: Path, force: bool = False):
    prereg_dir = proj_root / "artifacts" / "public_benchmark_governance" / "candidate_b_r003_taxonomy_v31_conditional23_preregistration_v1"
    roster_path = prereg_dir / "conditional23_candidate_roster.csv"
    
    roster = load_roster(roster_path)
    results = {}
    for row in roster:
        cell_id = row["cell_id"]
        results[cell_id] = run_cell_diagnostics(cell_id, proj_root, force=force)
    return results

if __name__ == "__main__":
    proj_root = Path(__file__).resolve().parents[3]
    run_all(proj_root)
