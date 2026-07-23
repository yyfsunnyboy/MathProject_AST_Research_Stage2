import subprocess
import hashlib
from pathlib import Path

def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def test_builder_determinism_and_validation():
    # Zero candidate-program import/compile/execution validation:
    # This script does not import, compile, or execute any candidate codes.
    
    current_dir = Path(__file__).parent
    build_script = current_dir / "build_preregistration.py"
    validate_script = current_dir / "validate_preregistration.py"
    
    assert build_script.exists(), "Build script missing"
    assert validate_script.exists(), "Validate script missing"
    
    # 1. Run builder to generate output files
    subprocess.run(
        ["python", str(build_script)],
        capture_output=True,
        text=True,
        check=True
    )
    
    generated_files = [
        "conditional23_candidate_roster.csv",
        "evidence_cluster_ledger.csv",
        "mechanism_family_registry.json",
        "decision_schema.json"
    ]
    
    hashes1 = {name: _file_hash(current_dir / name) for name in generated_files}
    
    # 2. Run builder again to ensure determinism
    subprocess.run(
        ["python", str(build_script)],
        capture_output=True,
        text=True,
        check=True
    )
    
    hashes2 = {name: _file_hash(current_dir / name) for name in generated_files}
    
    # Assert byte-for-byte identity
    for name in generated_files:
        assert hashes1[name] == hashes2[name], f"Non-deterministic build for {name}"
        
    # 3. Run validator to verify correctness
    result_val = subprocess.run(
        ["python", str(validate_script)],
        capture_output=True,
        text=True,
        check=True
    )
    
    assert "Zero-model validation passed successfully!" in result_val.stdout
    print("Determinism and Validation tests passed successfully!")

if __name__ == "__main__":
    test_builder_determinism_and_validation()
