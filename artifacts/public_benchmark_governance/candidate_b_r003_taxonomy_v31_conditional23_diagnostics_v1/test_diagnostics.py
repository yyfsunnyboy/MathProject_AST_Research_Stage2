import pytest
import shutil
import json
import csv
from pathlib import Path
import run_diagnostics
import preflight_check

PROJ_ROOT = Path(__file__).resolve().parents[3]

def test_roster_exclusion_rejected():
    # cell_id not in roster must raise ValueError
    with pytest.raises(ValueError) as exc:
        run_diagnostics.run_cell_diagnostics("invalid_cell_id_not_in_roster", PROJ_ROOT)
    assert "not found in the frozen roster" in str(exc.value)

def test_identity_mismatch_rejected(monkeypatch):
    # Retrieve a valid cell_id from roster
    prereg_dir = PROJ_ROOT / "artifacts" / "public_benchmark_governance" / "candidate_b_r003_taxonomy_v31_conditional23_preregistration_v1"
    roster_path = prereg_dir / "conditional23_candidate_roster.csv"
    with open(roster_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        row = next(reader)
    cell_id = row["cell_id"]
    
    # Mock extract_candidate_code to return wrong code, causing hash mismatch
    monkeypatch.setattr(run_diagnostics, "extract_candidate_code", lambda *args, **kwargs: "print('wrong code')")
    
    with pytest.raises(ValueError) as exc:
        run_diagnostics.run_cell_diagnostics(cell_id, PROJ_ROOT, force=True)
    assert "SHA-256 hash mismatch" in str(exc.value)

def test_output_path_isolation_and_resume():
    # Retrieve a valid cell_id from roster
    prereg_dir = PROJ_ROOT / "artifacts" / "public_benchmark_governance" / "candidate_b_r003_taxonomy_v31_conditional23_preregistration_v1"
    roster_path = prereg_dir / "conditional23_candidate_roster.csv"
    with open(roster_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        row = next(reader)
    cell_id = row["cell_id"]
    
    # Read first time to check validation and skip resume check
    run_dir = PROJ_ROOT / "artifacts" / "public_benchmark_governance" / "candidate_b_r003_taxonomy_v31_conditional23_diagnostics_v1" / "runs" / cell_id
    evidence_path = run_dir / "diagnostic_evidence.json"
    
    assert evidence_path.exists(), "Evidence file was not found"
    with open(evidence_path, "r", encoding="utf-8") as f:
        res1 = json.load(f)
        
    assert res1["preflight_passed"] is True
    assert res1["execution_diagnostics"]["executed"] is False
    
    # Run second time without force (should resume/skip and return same dict)
    res2 = run_diagnostics.run_cell_diagnostics(cell_id, PROJ_ROOT, force=False)
    assert res1["fingerprint"] == res2["fingerprint"]

def test_schema_validation_failures():
    # Verify that missing keys cause validation assertions in preflight_check
    invalid_ev = {
        "cell_id": "test",
        "task_id": "test",
        # missing source_hash, preflight_passed, etc.
    }
    with pytest.raises(AssertionError):
        preflight_check.validate_evidence_format(invalid_ev, "expected_fp")
        
    invalid_ev2 = {
        "cell_id": "test",
        "task_id": "test",
        "source_hash": "test",
        "preflight_passed": True,
        "ast_diagnostics": {}, # missing keys
        "execution_diagnostics": {
            "executed": False,
            "exit_code": None,
            "stdout": "",
            "stderr": "",
            "error_message": None
        },
        "decision": {
            "status": "INSUFFICIENT_EXISTING_EVIDENCE",
            "action": "ABSTAIN"
        }
    }
    with pytest.raises(AssertionError):
        preflight_check.validate_evidence_format(invalid_ev2, "expected_fp")

def test_fingerprint_missing_fails():
    invalid_ev = {
        "cell_id": "test",
        "task_id": "test",
        "source_hash": "test",
        "preflight_passed": True,
        "ast_diagnostics": {
            "has_top_level_assert": True,
            "top_level_assert_count": 1,
            "assert_node_lines": [26]
        },
        "execution_diagnostics": {
            "executed": False,
            "exit_code": None,
            "stdout": "",
            "stderr": "",
            "error_message": "test"
        },
        "decision": {
            "status": "INSUFFICIENT_EXISTING_EVIDENCE",
            "action": "ABSTAIN"
        }
        # missing fingerprint
    }
    with pytest.raises(AssertionError):
        preflight_check.validate_evidence_format(invalid_ev, "expected_fp")

def test_fingerprint_wrong_fails():
    invalid_ev = {
        "cell_id": "test",
        "task_id": "test",
        "source_hash": "test",
        "fingerprint": "b" * 64,
        "preflight_passed": True,
        "ast_diagnostics": {
            "has_top_level_assert": True,
            "top_level_assert_count": 1,
            "assert_node_lines": [26]
        },
        "execution_diagnostics": {
            "executed": False,
            "exit_code": None,
            "stdout": "",
            "stderr": "",
            "error_message": "test"
        },
        "decision": {
            "status": "INSUFFICIENT_EXISTING_EVIDENCE",
            "action": "ABSTAIN"
        }
    }
    with pytest.raises(AssertionError) as exc:
        preflight_check.validate_evidence_format(invalid_ev, "a" * 64)
    assert "Fingerprint mismatch" in str(exc.value)

def test_correct_fingerprint_passes():
    valid_fp = "a" * 64
    valid_ev = {
        "cell_id": "test",
        "task_id": "test",
        "source_hash": "test",
        "fingerprint": valid_fp,
        "preflight_passed": True,
        "ast_diagnostics": {
            "has_top_level_assert": True,
            "top_level_assert_count": 1,
            "assert_node_lines": [26]
        },
        "execution_diagnostics": {
            "executed": False,
            "exit_code": None,
            "stdout": "",
            "stderr": "",
            "error_message": "test"
        },
        "decision": {
            "status": "INSUFFICIENT_EXISTING_EVIDENCE",
            "action": "ABSTAIN"
        }
    }
    # Should run without error
    preflight_check.validate_evidence_format(valid_ev, valid_fp)

def test_decision_invariants():
    valid_fp = "a" * 64
    
    # 1. Invalid status
    invalid_ev1 = {
        "cell_id": "test",
        "task_id": "test",
        "source_hash": "test",
        "fingerprint": valid_fp,
        "preflight_passed": True,
        "ast_diagnostics": {
            "has_top_level_assert": True,
            "top_level_assert_count": 1,
            "assert_node_lines": [26]
        },
        "execution_diagnostics": {
            "executed": False,
            "exit_code": None,
            "stdout": "",
            "stderr": "",
            "error_message": "test"
        },
        "decision": {
            "status": "ELIGIBLE_FOR_IMPLEMENTATION", # wrong
            "action": "ABSTAIN"
        }
    }
    with pytest.raises(AssertionError):
        preflight_check.validate_evidence_format(invalid_ev1, valid_fp)
        
    # 2. Invalid action
    invalid_ev2 = {
        "cell_id": "test",
        "task_id": "test",
        "source_hash": "test",
        "fingerprint": valid_fp,
        "preflight_passed": True,
        "ast_diagnostics": {
            "has_top_level_assert": True,
            "top_level_assert_count": 1,
            "assert_node_lines": [26]
        },
        "execution_diagnostics": {
            "executed": False,
            "exit_code": None,
            "stdout": "",
            "stderr": "",
            "error_message": "test"
        },
        "decision": {
            "status": "INSUFFICIENT_EXISTING_EVIDENCE",
            "action": "REPAIR" # wrong
        }
    }
    with pytest.raises(AssertionError):
        preflight_check.validate_evidence_format(invalid_ev2, valid_fp)

if __name__ == "__main__":
    pytest.main([__file__])
