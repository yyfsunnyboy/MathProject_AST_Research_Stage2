from __future__ import annotations

import ast
import hashlib
import json
import re
from pathlib import Path

import pytest

from scripts import build_candidate_b_r003_diagnostics_r002_v3 as builder
from scripts import run_candidate_b_r003_diagnostics_r002_v2 as v2_runner
from scripts import run_candidate_b_r003_diagnostics_r002_v3 as runner


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / builder.OUTPUT_RELATIVE
CALIBRATION_DIR = REPO_ROOT / builder.CALIBRATION_RELATIVE


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _evidence() -> dict:
    return json.loads((OUTPUT_DIR / "manifest.json").read_bytes())["calibration_evidence"]


def _copy_evidence(tmp_path: Path) -> tuple[Path, Path, Path, dict]:
    directory = tmp_path / "calibration"
    directory.mkdir()
    for name in ("calibration_results.csv", "execution_manifest.json"):
        (directory / name).write_bytes((CALIBRATION_DIR / name).read_bytes())
    cohort = tmp_path / "calibration_cohort.csv"
    protocol = tmp_path / "calibration_protocol.json"
    cohort.write_bytes((REPO_ROOT / runner.CALIBRATION_COHORT).read_bytes())
    protocol.write_bytes((REPO_ROOT / runner.CALIBRATION_PROTOCOL).read_bytes())
    return directory, cohort, protocol, dict(_evidence())


def _rehash_receipt(directory: Path, evidence: dict) -> str:
    digest = _digest(directory / "execution_manifest.json")
    evidence["execution_manifest_sha256"] = digest
    return digest


def test_v2_frozen_manifest_runner_and_calibration_bytes_are_preserved():
    assert _digest(REPO_ROOT / builder.V2_RELATIVE / "manifest.json") == builder.V2_MANIFEST_SHA256
    assert _digest(REPO_ROOT / builder.V2_RUNNER) == builder.V2_RUNNER_SHA256
    assert _digest(CALIBRATION_DIR / "calibration_results.csv") == builder.CALIBRATION_RESULTS_SHA256
    assert _digest(CALIBRATION_DIR / "execution_manifest.json") == builder.CALIBRATION_EXECUTION_MANIFEST_SHA256


def test_incident_is_zero_execution_formal_preflight_logic_only():
    incident = json.loads((OUTPUT_DIR / "incident_ledger.json").read_bytes())
    assert incident["incident_type"] == "ZERO_EXECUTION_FORMAL_PREFLIGHT_LOGIC_INCIDENT"
    assert incident["formal_cells_executed"] == 0
    assert incident["worker_processes_started"] == 0
    assert incident["formal_output_created"] is False
    assert incident["model_calls"] == 0
    assert incident["evalplus_correctness_executions"] == 0
    assert incident["v2_manifest_runner_calibration_modified"] is False


def test_state_calibration_absent_and_formal_absent_can_enter(tmp_path: Path):
    runner._validate_mode_state("calibration", tmp_path / "calibration", tmp_path / "formal")


def test_state_existing_calibration_blocks_calibration_mode(tmp_path: Path):
    calibration = tmp_path / "calibration"
    calibration.mkdir()
    with pytest.raises(runner.R002V3RunnerError, match="calibration output path already exists"):
        runner._validate_mode_state("calibration", calibration, tmp_path / "formal")


def test_state_formal_missing_calibration_fails_closed(tmp_path: Path):
    with pytest.raises(runner.R002V3RunnerError, match="calibration evidence directory is missing"):
        runner._validate_mode_state("formal", tmp_path / "missing", tmp_path / "formal")


def test_state_formal_valid_calibration_and_absent_formal_can_enter(tmp_path: Path):
    runner._validate_mode_state("formal", CALIBRATION_DIR, tmp_path / "formal")


def test_state_existing_formal_output_blocks_formal_mode(tmp_path: Path):
    formal = tmp_path / "formal"
    formal.mkdir()
    with pytest.raises(runner.R002V3RunnerError, match="formal output path already exists"):
        runner._validate_mode_state("formal", CALIBRATION_DIR, formal)


def test_actual_v2_calibration_passes_full_frozen_evidence_gate():
    rows = runner._validate_calibration_evidence(
        CALIBRATION_DIR,
        builder.CALIBRATION_EXECUTION_MANIFEST_SHA256,
        _evidence(),
        REPO_ROOT / runner.CALIBRATION_COHORT,
        REPO_ROOT / runner.CALIBRATION_PROTOCOL,
    )
    assert len(rows) == 8
    assert all(
        row["worker_ready"] == "True"
        and row["phase"] == "completed"
        and row["termination"] == "returned"
        and row["ipc_status"] == "result_received"
        and row["child_exit_bucket"] == "exit_0"
        for row in rows
    )


def test_calibration_execution_manifest_hash_drift_fails_closed():
    with pytest.raises(runner.R002V3RunnerError, match="CLI calibration"):
        runner._validate_calibration_evidence(
            CALIBRATION_DIR,
            "0" * 64,
            _evidence(),
            REPO_ROOT / runner.CALIBRATION_COHORT,
            REPO_ROOT / runner.CALIBRATION_PROTOCOL,
        )


def test_calibration_receipt_false_fails_closed(tmp_path: Path):
    directory, cohort, protocol, evidence = _copy_evidence(tmp_path)
    receipt = json.loads((directory / "execution_manifest.json").read_bytes())
    receipt["formal_198_authorized"] = False
    (directory / "execution_manifest.json").write_bytes((json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode())
    receipt_sha = _rehash_receipt(directory, evidence)
    with pytest.raises(runner.R002V3RunnerError, match="does not authorize"):
        runner._validate_calibration_evidence(directory, receipt_sha, evidence, cohort, protocol)


def test_calibration_result_row_count_drift_fails_closed(tmp_path: Path):
    directory, cohort, protocol, evidence = _copy_evidence(tmp_path)
    lines = (directory / "calibration_results.csv").read_bytes().splitlines(keepends=True)
    (directory / "calibration_results.csv").write_bytes(b"".join(lines[:-1]))
    results_sha = _digest(directory / "calibration_results.csv")
    evidence["results_sha256"] = results_sha
    receipt = json.loads((directory / "execution_manifest.json").read_bytes())
    receipt["results_sha256"] = results_sha
    (directory / "execution_manifest.json").write_bytes((json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode())
    receipt_sha = _rehash_receipt(directory, evidence)
    with pytest.raises(runner.R002V3RunnerError, match="row count"):
        runner._validate_calibration_evidence(directory, receipt_sha, evidence, cohort, protocol)


def test_calibration_results_hash_drift_fails_closed(tmp_path: Path):
    directory, cohort, protocol, evidence = _copy_evidence(tmp_path)
    path = directory / "calibration_results.csv"
    path.write_bytes(path.read_bytes() + b"drift")
    with pytest.raises(runner.R002V3RunnerError, match="results SHA-256"):
        runner._validate_calibration_evidence(
            directory,
            evidence["execution_manifest_sha256"],
            evidence,
            cohort,
            protocol,
        )


@pytest.mark.parametrize("target", ["cohort", "protocol"])
def test_calibration_cohort_and_protocol_hash_drift_fail_closed(tmp_path: Path, target: str):
    directory, cohort, protocol, evidence = _copy_evidence(tmp_path)
    path = cohort if target == "cohort" else protocol
    path.write_bytes(path.read_bytes() + b"drift")
    with pytest.raises(runner.R002V3RunnerError, match=target):
        runner._validate_calibration_evidence(
            directory,
            evidence["execution_manifest_sha256"],
            evidence,
            cohort,
            protocol,
        )


def test_calibration_source_manifest_identity_drift_fails_closed(tmp_path: Path):
    directory, cohort, protocol, evidence = _copy_evidence(tmp_path)
    evidence["source_manifest_sha256"] = "0" * 64
    with pytest.raises(runner.R002V3RunnerError, match="source manifest"):
        runner._validate_calibration_evidence(
            directory,
            evidence["execution_manifest_sha256"],
            evidence,
            cohort,
            protocol,
        )


def test_formal_integration_reaches_worker_loop_boundary_without_running_cells(monkeypatch):
    class WorkerLoopBoundaryReached(Exception):
        pass

    sentinel = {"synthetic": "prepared_without_dataset_or_workers"}
    reached = []
    monkeypatch.setattr(runner, "_validate_environment", lambda execute: None)
    monkeypatch.setattr(runner, "_prepare_worker_loop", lambda manifest: sentinel)

    def stop_at_boundary(prepared, output_dir, source_manifest_sha256):
        reached.append((prepared, output_dir, source_manifest_sha256))
        raise WorkerLoopBoundaryReached

    monkeypatch.setattr(runner, "_run_worker_loop", stop_at_boundary)
    manifest_path = OUTPUT_DIR / "manifest.json"
    manifest_sha = _digest(manifest_path)
    with pytest.raises(WorkerLoopBoundaryReached):
        runner.run(
            "formal",
            manifest_path,
            manifest_sha,
            REPO_ROOT / runner.FORMAL_OUTPUT,
            True,
            builder.CALIBRATION_EXECUTION_MANIFEST_SHA256,
        )
    assert reached == [(sentinel, REPO_ROOT / runner.FORMAL_OUTPUT, manifest_sha)]
    assert not (REPO_ROOT / runner.FORMAL_OUTPUT).exists()


def test_worker_and_cell_diagnostics_are_exact_v2_bindings_with_no_v3_definitions():
    assert runner.execution_core._worker is v2_runner.execution_core._worker
    assert runner.execution_core._run_cell is v2_runner.execution_core._run_cell
    source = (REPO_ROOT / builder.RUNNER).read_text(encoding="utf-8")
    names = {node.name for node in ast.parse(source).body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    assert "_worker" not in names
    assert "_run_cell" not in names
    proof = json.loads((OUTPUT_DIR / "worker_core_equivalence.json").read_bytes())
    assert proof["worker_cell_diagnostic_modifications"] == 0
    assert proof["timeouts_unchanged"] == {"startup_seconds": 30, "candidate_execution_seconds": 30}


def test_cli_error_output_remains_safe_and_specific(capsys):
    code = runner.main([
        "--mode", "formal",
        "--manifest", str(OUTPUT_DIR / "manifest.json"),
        "--manifest-sha256", _digest(OUTPUT_DIR / "manifest.json"),
        "--output-dir", str(REPO_ROOT / runner.FORMAL_OUTPUT),
        "--calibration-execution-manifest-sha256", builder.CALIBRATION_EXECUTION_MANIFEST_SHA256,
    ])
    captured = capsys.readouterr()
    assert code == 1
    assert "stage=execution_authorization" in captured.err
    assert "exception_type=R002V3RunnerError" in captured.err
    assert "message=explicit execution flag is required" in captured.err
    assert "Traceback" not in captured.err
    for forbidden in ("candidate source", "hidden input", "expected", "actual"):
        assert forbidden not in captured.err


def test_outputs_are_deterministic_hash_locked_and_unique_formal_command():
    first = builder.build_outputs(REPO_ROOT)
    second = builder.build_outputs(REPO_ROOT)
    assert first == second
    for relative, content in first.items():
        assert (OUTPUT_DIR / relative).read_bytes() == content
    manifest = json.loads(first[Path("manifest.json")])
    assert manifest["status"] == "r002_v3_formal_prepared_not_executed"
    assert manifest["worker_cell_diagnostic_modifications"] == 0
    assert manifest["calibration_reused_not_rerun"] is True
    for name, digest in manifest["outputs_sha256_excluding_manifest_and_operator_guide"].items():
        assert hashlib.sha256(first[Path(name)]).hexdigest() == digest
    guide = first[Path("operator_guide_zh.md")].decode()
    assert guide.count("scripts/run_candidate_b_r003_diagnostics_r002_v3.py") == 1
    assert guide.count("--calibration-execution-manifest-sha256") == 2
    assert builder.CALIBRATION_EXECUTION_MANIFEST_SHA256 in guide
    assert re.search(r"--manifest-sha256 ([0-9a-f]{64})", guide).group(1) == _digest(OUTPUT_DIR / "manifest.json")


def test_formal_output_is_absent_and_no_execution_was_materialized():
    assert not (REPO_ROOT / runner.FORMAL_OUTPUT).exists()
    execution = json.loads((OUTPUT_DIR / "execution_manifest.json").read_bytes())
    assert execution["diagnostic_executions"] == 0
    assert execution["formal_cells_executed"] == 0
    assert execution["worker_processes_started"] == 0
