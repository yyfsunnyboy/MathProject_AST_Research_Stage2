from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

import pytest

from scripts import build_candidate_b_r003_diagnostics_r002_incident as builder
from scripts import run_candidate_b_r003_diagnostics_r002 as runner


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / builder.OUTPUT_RELATIVE


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_run001_bytes_and_observed_incident_are_preserved_exactly():
    analysis = builder.build_analysis(REPO_ROOT)
    incident = analysis["incident"]
    assert hashlib.sha256((REPO_ROOT / builder.R001_RESULTS).read_bytes()).hexdigest() == "da09a67b7fc461bac355cfae3b3eebed5c4183a12b4ecd7ea82eae6a18d8767b"
    assert hashlib.sha256((REPO_ROOT / builder.R001_RECEIPT).read_bytes()).hexdigest() == "3245a980581ee0ff29c225a7b1b38dc20c782e6ffabffcb4c259a44c5368bc4c"
    assert incident["diagnostics_executed"] == 198
    assert incident["usable_classifications"] == 0
    assert incident["suspected_protocol_failure"] is True
    assert incident["crosswalk_modified"] is False
    assert incident["l4_l5_conclusions_produced"] is False
    assert incident["healer_rule_evidence"] is False


def test_run001_distribution_binding_and_empty_payload_evidence():
    rows = builder.build_analysis(REPO_ROOT)["run_rows"]
    assert sum(row["phase"] == "G2" and row["exception_class"] == "TimeoutError" for row in rows) == 196
    assert sum(row["phase"] == "infrastructure" and row["exception_class"] == "WorkerProcessExit" for row in rows) == 2
    assert all(row["entry_point_bound"] == row["entry_point_callable"] == "True" and row["signature_binding"] == "passed" for row in rows)
    assert all(not row["model_source_line"] and not row["model_source_ast_node"] and not row["return_type_bucket"] and not row["return_shape_bucket"] for row in rows)


def test_calibration_cohort_is_eight_distinct_development_known_pass_controls():
    cohort = builder.build_analysis(REPO_ROOT)["cohort"]
    assert len(cohort) == 8
    assert len({row["program_id"] for row in cohort}) == 8
    assert len({row["task_identity_sha256"] for row in cohort}) == 8
    assert all(row["known_pass_evidence"] == "frozen_candidate_b_h0_evalplus_pass" for row in cohort)
    assert all(row["evidence_role"] == "development_calibration" for row in cohort)


def test_r002_protocol_separates_ready_startup_execution_and_output_directories():
    calibration = builder._protocol("calibration", 8)
    formal = builder._protocol("formal", 198)
    assert calibration["worker_ready_handshake"] is True
    assert calibration["startup_timeout_seconds"] == 30
    assert calibration["candidate_execution_timeout_seconds"] == 30
    assert calibration["candidate_timer_starts"].startswith("after_ready_received")
    assert calibration["dataset_initialization"] == "once_in_parent_before_cell_workers"
    assert calibration["expected_outputs_loaded"] is False
    assert calibration["ipc"].startswith("two_one_way_Pipes")
    assert calibration["output_path"] != formal["output_path"]
    assert formal["formal_gate"].startswith("all 8 known-pass")
    assert calibration["privacy"]["healer_runtime_input"] is False


def test_runner_uses_pipe_receives_before_join_and_never_uses_queue():
    source = (REPO_ROOT / "scripts/run_candidate_b_r003_diagnostics_r002.py").read_text(encoding="utf-8")
    run_cell = source[source.index("def _run_cell"):source.index("def _validate_manifest")]
    assert "context.Pipe(duplex=False)" in run_cell
    assert "Queue(" not in run_cell
    assert run_cell.index("ready_recv.poll") < run_cell.index('control_send.send("go")')
    assert run_cell.index("ready_recv.poll") < run_cell.index("execution_start = time.monotonic()") < run_cell.index('control_send.send("go")')
    assert run_cell.index("result_recv.recv()") < run_cell.index("process.join(2)")
    assert "time.monotonic()" in run_cell
    assert "get_context(\"fork\")" in run_cell
    worker = source[source.index("def _worker"):source.index("def _exit_bucket")]
    assert worker.index('control_recv.recv()') < worker.index("RLIMIT_CPU")


def test_coarse_duration_buckets_and_privacy_schema():
    assert runner._duration_bucket(0.01) == "lt_0_1s"
    assert runner._duration_bucket(0.2) == "0_1_to_0_5s"
    assert runner._duration_bucket(12) == "10_to_30s"
    assert runner._duration_bucket(30) == "gte_30s"
    forbidden = {"input", "expected", "actual", "exception_message", "assertion_message", "traceback", "source"}
    assert not (set(runner.RESULT_FIELDS) & forbidden)
    assert {"worker_ready", "startup_duration_bucket", "execution_duration_bucket", "ipc_status", "child_exit_bucket"} <= set(runner.RESULT_FIELDS)
    with pytest.raises(runner.R002RunnerError, match="unknown or missing"):
        runner._validate_result_rows([{"unexpected": "field"}], 1)


def test_formal_gate_rejects_missing_or_nonpassing_calibration(tmp_path: Path):
    with pytest.raises(runner.R002RunnerError, match="missing"):
        runner._calibration_all_passed(tmp_path, "0" * 64)
    directory = tmp_path / "cal"; directory.mkdir()
    result = {field: "" for field in runner.RESULT_FIELDS}
    result.update({"worker_ready": "True", "phase": "G2", "termination": "timeout", "ipc_status": "result_timeout", "child_exit_bucket": "signal_exit"})
    (directory / "calibration_results.csv").write_bytes(runner._csv_bytes([result] * 8))
    receipt = {"formal_198_authorized": False}
    receipt_bytes = (json.dumps(receipt) + "\n").encode()
    (directory / "execution_manifest.json").write_bytes(receipt_bytes)
    assert runner._calibration_all_passed(directory, hashlib.sha256(receipt_bytes).hexdigest()) is False


def test_no_calibration_or_formal_output_created_during_freeze():
    assert not (REPO_ROOT / runner.CALIBRATION_OUTPUT).exists()
    assert not (REPO_ROOT / runner.FORMAL_OUTPUT).exists()


def test_outputs_deterministic_hash_locked_and_unique_command():
    first = builder.build_outputs(REPO_ROOT); second = builder.build_outputs(REPO_ROOT)
    assert first == second
    for relative, content in first.items(): assert (OUTPUT_DIR / relative).read_bytes() == content
    manifest = json.loads(first[Path("manifest.json")])
    assert manifest["status"] == "r002_calibration_prepared_formal_locked"
    assert manifest["incident"]["usable_classifications"] == 0
    assert manifest["diagnostic_executions_this_freeze"] == 0
    assert manifest["calibration_output_directory_created"] is False
    assert manifest["formal_output_directory_created"] is False
    for name, digest in manifest["outputs_sha256_excluding_manifest_and_operator_guide"].items():
        assert hashlib.sha256(first[Path(name)]).hexdigest() == digest
    guide = first[Path("operator_guide_zh.md")].decode()
    assert guide.count("scripts/run_candidate_b_r003_diagnostics_r002.py") == 1
    assert re.search(r"--manifest-sha256 ([0-9a-f]{64})", guide).group(1) == hashlib.sha256(first[Path("manifest.json")]).hexdigest()
