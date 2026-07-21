#!/usr/bin/env python3
"""Run frozen Candidate B r003 diagnostics r002 v3 formal mode in WSL.

v3 changes only the mode-specific output preflight and calibration-evidence
gate.  Worker and per-cell diagnostics are imported unchanged from v2.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import sys
import threading
from pathlib import Path
from typing import Any, Sequence

try:
    from scripts import run_candidate_b_r003_diagnostics_r002_v2 as v2_runner
except ModuleNotFoundError as exc:
    if exc.name != "scripts":
        raise
    import run_candidate_b_r003_diagnostics_r002_v2 as v2_runner


REPO_ROOT = Path(__file__).resolve().parents[1]
FROZEN_RELATIVE = Path("artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v3")
FROZEN_MANIFEST = FROZEN_RELATIVE / "manifest.json"
CALIBRATION_EVIDENCE = Path(
    "artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v2/manual_calibration_run_001"
)
FORMAL_OUTPUT = FROZEN_RELATIVE / "manual_formal_diagnostics_run_001"
CALIBRATION_COHORT = Path(
    "artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v2/calibration_cohort.csv"
)
CALIBRATION_PROTOCOL = Path(
    "artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v2/calibration_protocol.json"
)
CALIBRATION_CELLS = v2_runner.CALIBRATION_CELLS
FORMAL_CELLS = v2_runner.FORMAL_CELLS
RESULT_FIELDS = v2_runner.RESULT_FIELDS
execution_core = v2_runner.execution_core


class R002V3RunnerError(RuntimeError):
    def __init__(self, stage: str, message: str) -> None:
        super().__init__(message)
        self.stage = stage
        self.safe_message = message


def _require(condition: bool, stage: str, message: str) -> None:
    if not condition:
        raise R002V3RunnerError(stage, message)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _validate_manifest(manifest_path: Path, manifest_sha256: str) -> dict[str, Any]:
    expected = (REPO_ROOT / FROZEN_MANIFEST).resolve()
    _require(manifest_path.resolve() == expected, "manifest_identity", "only the frozen r002 v3 manifest is accepted")
    data = manifest_path.read_bytes()
    _require(_sha(data) == manifest_sha256, "manifest_hash", "frozen manifest SHA-256 mismatch")
    manifest = json.loads(data)
    _require(isinstance(manifest, dict), "manifest_schema", "manifest root must be an object")
    _require(
        manifest.get("status") == "r002_v3_formal_prepared_not_executed",
        "manifest_schema",
        "manifest status mismatch",
    )
    value = manifest.get("diagnostic_executions")
    _require(
        not isinstance(value, bool) and isinstance(value, int) and value == 0,
        "manifest_schema",
        "diagnostic_executions must be the integer zero",
    )
    outputs = manifest.get("outputs_sha256_excluding_manifest_and_operator_guide")
    _require(isinstance(outputs, dict), "manifest_schema", "output hash ledger must be an object")
    for name, digest in outputs.items():
        path = manifest_path.parent / name
        _require(path.is_file() and _sha(path.read_bytes()) == digest, "artifact_hash", f"frozen artifact SHA-256 mismatch: {name}")
    sources = manifest.get("source_sha256")
    _require(isinstance(sources, dict), "manifest_schema", "source hash ledger must be an object")
    for name, digest in sources.items():
        path = REPO_ROOT / name
        _require(path.is_file() and _sha(path.read_bytes()) == digest, "source_hash", f"reproducibility source SHA-256 mismatch: {name}")
    return manifest


def _validate_mode_state(mode: str, calibration_directory: Path, formal_directory: Path) -> None:
    if mode == "calibration":
        _require(not calibration_directory.exists(), "output_preflight", "calibration output path already exists")
        _require(not formal_directory.exists(), "output_preflight", "formal output path already exists")
        return
    _require(calibration_directory.is_dir(), "output_preflight", "calibration evidence directory is missing")
    _require(not formal_directory.exists(), "output_preflight", "formal output path already exists")


def _validate_calibration_evidence(
    directory: Path,
    calibration_execution_manifest_sha256: str,
    evidence: dict[str, Any],
    cohort_path: Path,
    protocol_path: Path,
) -> list[dict[str, str]]:
    receipt_path = directory / "execution_manifest.json"
    results_path = directory / "calibration_results.csv"
    _require(receipt_path.is_file() and results_path.is_file(), "calibration_gate", "calibration evidence files are missing")
    receipt_bytes = receipt_path.read_bytes()
    results_bytes = results_path.read_bytes()
    expected_receipt_sha = evidence.get("execution_manifest_sha256")
    _require(
        calibration_execution_manifest_sha256 == expected_receipt_sha,
        "calibration_gate",
        "CLI calibration execution_manifest.json SHA-256 is not the frozen value",
    )
    _require(
        _sha(receipt_bytes) == expected_receipt_sha,
        "calibration_gate",
        "calibration execution_manifest.json SHA-256 mismatch",
    )
    _require(
        _sha(results_bytes) == evidence.get("results_sha256"),
        "calibration_gate",
        "calibration results SHA-256 mismatch",
    )
    _require(
        cohort_path.is_file() and _sha(cohort_path.read_bytes()) == evidence.get("cohort_sha256"),
        "calibration_gate",
        "calibration cohort SHA-256 mismatch",
    )
    _require(
        protocol_path.is_file() and _sha(protocol_path.read_bytes()) == evidence.get("protocol_sha256"),
        "calibration_gate",
        "calibration protocol SHA-256 mismatch",
    )
    receipt = json.loads(receipt_bytes)
    _require(receipt.get("source_manifest_sha256") == evidence.get("source_manifest_sha256"), "calibration_gate", "calibration source manifest SHA-256 mismatch")
    _require(receipt.get("results_sha256") == evidence.get("results_sha256"), "calibration_gate", "receipt results SHA-256 mismatch")
    _require(receipt.get("cells") == CALIBRATION_CELLS, "calibration_gate", "calibration receipt cell count mismatch")
    _require(receipt.get("formal_198_authorized") is True, "calibration_gate", "calibration receipt does not authorize formal diagnostics")
    _require(receipt.get("mode") == "calibration", "calibration_gate", "calibration receipt mode mismatch")
    _require(receipt.get("model_calls") == 0, "calibration_gate", "calibration receipt model_calls mismatch")
    _require(receipt.get("evalplus_correctness_executions") == 0, "calibration_gate", "calibration receipt correctness-execution count mismatch")
    rows = execution_core._read_csv(results_path)
    cohort = execution_core._read_csv(cohort_path)
    _require(len(rows) == CALIBRATION_CELLS, "calibration_gate", "calibration results row count mismatch")
    _require(len(cohort) == CALIBRATION_CELLS, "calibration_gate", "calibration cohort row count mismatch")
    _require(len({row["cell_identity_sha256"] for row in rows}) == CALIBRATION_CELLS, "calibration_gate", "duplicate calibration result identity")
    _require(len({row["cell_identity_sha256"] for row in cohort}) == CALIBRATION_CELLS, "calibration_gate", "duplicate calibration cohort identity")
    cohort_by_identity = {row["cell_identity_sha256"]: row for row in cohort}
    identity_fields = (
        "program_id",
        "task_identity_sha256",
        "evaluation_source_sha256",
        "evaluator_hash",
    )
    for row in rows:
        _require(set(row) == set(RESULT_FIELDS), "calibration_gate", "calibration result schema mismatch")
        expected = cohort_by_identity.get(row["cell_identity_sha256"])
        _require(expected is not None, "calibration_gate", "calibration result is absent from frozen cohort")
        _require(all(row[field] == expected[field] for field in identity_fields), "calibration_gate", "calibration result identity-field mismatch")
        _require(row["protocol_sha256"] == evidence.get("protocol_sha256"), "calibration_gate", "calibration result protocol SHA-256 mismatch")
        _require(
            row["worker_ready"] == "True"
            and row["phase"] == "completed"
            and row["termination"] == "returned"
            and row["ipc_status"] == "result_received"
            and row["child_exit_bucket"] == "exit_0",
            "calibration_gate",
            "calibration control did not complete successfully",
        )
    return rows


def _validate_environment(execute: bool) -> None:
    _require(execute, "execution_authorization", "explicit execution flag is required")
    _require(os.name != "nt" and not sys.platform.startswith("win"), "environment", "WSL/Linux is required")
    _require(sys.version_info[:2] == (3, 14), "environment", "Python 3.14 is required")
    _require(threading.active_count() == 1, "environment", "parent process must be single-threaded")


def _prepare_worker_loop(manifest: dict[str, Any]) -> dict[str, Any]:
    _require(
        importlib.metadata.version("evalplus") == execution_core.EXPECTED_EVALPLUS_VERSION,
        "dataset_initialization",
        "dataset loader version mismatch",
    )
    from evalplus.data import get_mbpp_plus, get_mbpp_plus_hash

    _require(
        get_mbpp_plus_hash(version=execution_core.EXPECTED_DATASET_VERSION) == execution_core.EXPECTED_DATASET_HASH,
        "dataset_initialization",
        "dataset hash mismatch",
    )
    problems = get_mbpp_plus(version=execution_core.EXPECTED_DATASET_VERSION)
    task_by_hash = {execution_core._task_identity(task_id): problem for task_id, problem in problems.items()}
    ledger = execution_core._read_csv(REPO_ROOT / FROZEN_RELATIVE / "formal198_input_ledger.csv")
    _require(len(ledger) == FORMAL_CELLS, "input_ledger", "formal input ledger row count mismatch")
    sources = execution_core._load_selected_sources({row["program_id"] for row in ledger})
    return {
        "ledger": ledger,
        "sources": sources,
        "task_by_hash": task_by_hash,
        "protocol_sha256": manifest["formal_protocol_sha256"],
    }


def _run_worker_loop(prepared: dict[str, Any], output_dir: Path, source_manifest_sha256: str) -> None:
    rows: list[dict[str, Any]] = []
    for ledger_row in prepared["ledger"]:
        source = prepared["sources"][ledger_row["program_id"]]
        _require(_sha(source.encode("utf-8")) == ledger_row["evaluation_source_sha256"], "input_ledger", "evaluation source SHA-256 mismatch")
        problem = prepared["task_by_hash"].get(ledger_row["task_identity_sha256"])
        _require(problem is not None, "input_ledger", "task identity is absent from frozen dataset")
        observed = execution_core._run_cell(source, problem, ledger_row["program_id"])
        rows.append({
            "cell_identity_sha256": ledger_row["cell_identity_sha256"],
            "program_id": ledger_row["program_id"],
            "task_identity_sha256": ledger_row["task_identity_sha256"],
            "evaluation_source_sha256": ledger_row["evaluation_source_sha256"],
            "evaluator_hash": ledger_row["evaluator_hash"],
            "protocol_sha256": prepared["protocol_sha256"],
            **observed,
        })
    execution_core._validate_result_rows(rows, FORMAL_CELLS)
    result_bytes = execution_core._csv_bytes(rows)
    receipt = {
        "status": "r002_v3_formal_complete",
        "mode": "formal",
        "cells": FORMAL_CELLS,
        "results_sha256": _sha(result_bytes),
        "source_manifest_sha256": source_manifest_sha256,
        "calibration_reused": True,
        "dataset_initialized_once_in_parent": True,
        "worker_ready_handshake": True,
        "startup_and_execution_timeouts_separate": True,
        "hidden_input_expected_actual_message_traceback_saved": False,
        "healer_runtime_input": False,
        "evalplus_correctness_executions": 0,
        "model_calls": 0,
        "retry_resume_overwrite": False,
    }
    output_dir.mkdir(parents=True)
    (output_dir / "coarse_diagnostics.csv").write_bytes(result_bytes)
    (output_dir / "execution_manifest.json").write_bytes((json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode("utf-8"))


def run(
    mode: str,
    manifest_path: Path,
    manifest_sha256: str,
    output_dir: Path,
    execute: bool,
    calibration_execution_manifest_sha256: str | None,
) -> None:
    _validate_environment(execute)
    manifest = _validate_manifest(manifest_path, manifest_sha256)
    expected_formal = REPO_ROOT / FORMAL_OUTPUT
    expected_calibration = REPO_ROOT / CALIBRATION_EVIDENCE
    _require(mode == "formal", "mode", "v3 is formal-only because valid v2 calibration is frozen")
    _require(output_dir.resolve() == expected_formal.resolve(), "output_preflight", "formal output path mismatch")
    _validate_mode_state(mode, expected_calibration, expected_formal)
    _require(bool(calibration_execution_manifest_sha256), "calibration_gate", "formal mode requires calibration execution_manifest.json SHA-256")
    _validate_calibration_evidence(
        expected_calibration,
        str(calibration_execution_manifest_sha256),
        manifest["calibration_evidence"],
        REPO_ROOT / CALIBRATION_COHORT,
        REPO_ROOT / CALIBRATION_PROTOCOL,
    )
    prepared = _prepare_worker_loop(manifest)
    _run_worker_loop(prepared, output_dir, manifest_sha256)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("formal",), required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--calibration-execution-manifest-sha256", required=True)
    parser.add_argument("--execute-r002-diagnostics", action="store_true")
    return parser


def _safe_cli_error(exc: BaseException) -> tuple[str, str, str]:
    if isinstance(exc, R002V3RunnerError):
        return exc.stage, type(exc).__name__, exc.safe_message
    if isinstance(exc, ImportError):
        return "dataset_initialization", type(exc).__name__, "required dependency import failed"
    if isinstance(exc, KeyError):
        return "runtime_schema", type(exc).__name__, "required runtime field is missing"
    if isinstance(exc, execution_core.R002RunnerError):
        return "diagnostic_validation", type(exc).__name__, "diagnostic validation failed"
    if isinstance(exc, json.JSONDecodeError):
        return "evidence_schema", type(exc).__name__, "JSON decoding failed"
    if isinstance(exc, OSError):
        return "filesystem", type(exc).__name__, "filesystem operation failed"
    return "runtime_validation", type(exc).__name__, "runtime value validation failed"


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        run(
            args.mode,
            args.manifest,
            args.manifest_sha256,
            args.output_dir,
            args.execute_r002_diagnostics,
            args.calibration_execution_manifest_sha256,
        )
    except (
        R002V3RunnerError,
        execution_core.R002RunnerError,
        ImportError,
        KeyError,
        OSError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        stage, exception_type, message = _safe_cli_error(exc)
        print(f"stage={stage} exception_type={exception_type} message={message}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
