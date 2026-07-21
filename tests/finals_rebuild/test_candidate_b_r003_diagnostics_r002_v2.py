from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

from scripts import build_candidate_b_r003_diagnostics_r002_v2 as builder
from scripts import run_candidate_b_r003_diagnostics_r002_v2 as runner


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / builder.OUTPUT_RELATIVE


def test_v1_manifest_is_preserved_and_incident_was_zero_execution():
    v1 = REPO_ROOT / builder.V1_RELATIVE / "manifest.json"
    assert hashlib.sha256(v1.read_bytes()).hexdigest() == builder.V1_MANIFEST_SHA256
    incident = json.loads((OUTPUT_DIR / "incident_ledger.json").read_bytes())
    assert incident["incident_type"] == "ZERO_EXECUTION_PREFLIGHT_SCHEMA_INCIDENT"
    assert incident["actual_calibration_run_incident"] is False
    assert incident["worker_processes_started"] == 0
    assert incident["calibration_cells_executed"] == 0
    assert incident["diagnostic_executions"] == 0
    assert incident["model_calls"] == 0
    assert incident["evalplus_correctness_executions"] == 0


def test_materializer_emits_required_exact_integer_zero():
    manifest = json.loads(builder.build_outputs(REPO_ROOT)[Path("manifest.json")])
    assert "diagnostic_executions" in manifest
    assert type(manifest["diagnostic_executions"]) is int
    assert manifest["diagnostic_executions"] == 0


@pytest.mark.parametrize("value", [True, False, "0", 0.0, None, [], {}, 1, -1])
def test_preflight_rejects_bool_other_noninteger_and_nonzero(value):
    with pytest.raises(runner.R002V2RunnerError):
        runner._validate_diagnostic_executions_field({"diagnostic_executions": value})


def test_preflight_rejects_missing_field():
    with pytest.raises(runner.R002V2RunnerError, match="missing required field") as caught:
        runner._validate_diagnostic_executions_field({})
    assert caught.value.stage == "manifest_schema"


def test_formal_frozen_manifest_integrates_directly_with_runner_validation():
    manifest_path = OUTPUT_DIR / "manifest.json"
    digest = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    manifest = runner._validate_manifest(manifest_path, digest)
    assert manifest["manifest_version"] == "candidate_b_r003_diagnostics_r002_v2"
    assert manifest["diagnostic_executions"] == 0


def test_manifest_hash_drift_fails_closed_before_any_execution():
    with pytest.raises(runner.R002V2RunnerError, match="SHA-256 mismatch") as caught:
        runner._validate_manifest(OUTPUT_DIR / "manifest.json", "0" * 64)
    assert caught.value.stage == "manifest_hash"


def test_cli_error_is_safe_specific_and_has_no_traceback(capsys):
    code = runner.main([
        "--mode", "calibration",
        "--manifest", str(OUTPUT_DIR / "manifest.json"),
        "--manifest-sha256", "0" * 64,
        "--output-dir", str(REPO_ROOT / runner.CALIBRATION_OUTPUT),
    ])
    captured = capsys.readouterr()
    assert code == 1
    assert captured.out == ""
    assert "stage=execution_authorization" in captured.err
    assert "exception_type=R002V2RunnerError" in captured.err
    assert "message=explicit execution flag is required" in captured.err
    assert "Traceback" not in captured.err
    for forbidden in ("hidden", "expected", "actual", "candidate source"):
        assert forbidden not in captured.err


def test_calibration_hash_means_execution_manifest_file_sha(tmp_path: Path):
    directory = tmp_path / "calibration"
    directory.mkdir()
    result = {field: "" for field in runner.RESULT_FIELDS}
    result.update({
        "worker_ready": "True",
        "phase": "completed",
        "termination": "returned",
        "ipc_status": "result_received",
        "child_exit_bucket": "exit_0",
    })
    (directory / "calibration_results.csv").write_bytes(
        runner.execution_core._csv_bytes([dict(result) for _ in range(runner.CALIBRATION_CELLS)])
    )
    source_manifest_sha = "1" * 64
    receipt_bytes = (json.dumps({
        "formal_198_authorized": True,
        "source_manifest_sha256": source_manifest_sha,
    }, sort_keys=True) + "\n").encode("utf-8")
    (directory / "execution_manifest.json").write_bytes(receipt_bytes)
    execution_manifest_file_sha = hashlib.sha256(receipt_bytes).hexdigest()
    assert runner._calibration_all_passed(
        directory, execution_manifest_file_sha, source_manifest_sha
    ) is True
    with pytest.raises(runner.R002V2RunnerError, match="execution_manifest.json"):
        runner._calibration_all_passed(directory, source_manifest_sha, source_manifest_sha)
    with pytest.raises(runner.R002V2RunnerError, match="source manifest"):
        runner._calibration_all_passed(directory, execution_manifest_file_sha, "2" * 64)


def test_cli_operator_and_formal_protocol_use_consistent_sha_name():
    parser_actions = {action.dest for action in runner.build_parser()._actions}
    assert "calibration_execution_manifest_sha256" in parser_actions
    assert "calibration_manifest_sha256" not in parser_actions
    formal = json.loads((OUTPUT_DIR / "formal_diagnostics_protocol.json").read_bytes())
    assert formal["formal_cli_flag"] == "--calibration-execution-manifest-sha256"
    assert "execution_manifest.json file bytes" in formal["calibration_execution_manifest_sha256_semantics"]
    guide = (OUTPUT_DIR / "operator_guide_zh.md").read_text(encoding="utf-8")
    assert "--calibration-execution-manifest-sha256" in guide


def test_outputs_are_deterministic_hash_locked_and_have_one_manual_command():
    first = builder.build_outputs(REPO_ROOT)
    second = builder.build_outputs(REPO_ROOT)
    assert first == second
    for relative, content in first.items():
        assert (OUTPUT_DIR / relative).read_bytes() == content
    manifest = json.loads(first[Path("manifest.json")])
    assert manifest["status"] == "r002_v2_calibration_prepared_formal_locked"
    assert manifest["diagnostic_executions"] == 0
    for name, digest in manifest["outputs_sha256_excluding_manifest_and_operator_guide"].items():
        assert hashlib.sha256(first[Path(name)]).hexdigest() == digest
    guide = first[Path("operator_guide_zh.md")].decode("utf-8")
    assert guide.count("scripts/run_candidate_b_r003_diagnostics_r002_v2.py") == 1
    assert re.search(r"--manifest-sha256 ([0-9a-f]{64})", guide).group(1) == hashlib.sha256(
        first[Path("manifest.json")]
    ).hexdigest()


def test_no_calibration_or_formal_output_was_created():
    assert not (REPO_ROOT / builder.V1_RELATIVE / "manual_calibration_run_001").exists()
    assert not (REPO_ROOT / runner.CALIBRATION_OUTPUT).exists()
    assert not (REPO_ROOT / runner.FORMAL_OUTPUT).exists()
