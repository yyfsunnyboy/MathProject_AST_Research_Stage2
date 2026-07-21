#!/usr/bin/env python3
"""Run frozen Candidate B r003 diagnostics r002 v2 in WSL.

The v2 revision repairs only the zero-execution preflight schema contract.
Candidate execution remains explicitly gated and is never performed by import
or manifest validation.
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
    from scripts import run_candidate_b_r003_diagnostics_r002 as execution_core
except ModuleNotFoundError as exc:
    if exc.name != "scripts":
        raise
    import run_candidate_b_r003_diagnostics_r002 as execution_core


REPO_ROOT = Path(__file__).resolve().parents[1]
FROZEN_RELATIVE = Path("artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v2")
FROZEN_MANIFEST = FROZEN_RELATIVE / "manifest.json"
CALIBRATION_OUTPUT = FROZEN_RELATIVE / "manual_calibration_run_001"
FORMAL_OUTPUT = FROZEN_RELATIVE / "manual_formal_diagnostics_run_001"
CALIBRATION_CELLS = execution_core.CALIBRATION_CELLS
FORMAL_CELLS = execution_core.FORMAL_CELLS
RESULT_FIELDS = execution_core.RESULT_FIELDS


class R002V2RunnerError(RuntimeError):
    """Fail-closed error whose stage and message are safe for CLI display."""

    def __init__(self, stage: str, message: str) -> None:
        super().__init__(message)
        self.stage = stage
        self.safe_message = message


def _require(condition: bool, stage: str, message: str) -> None:
    if not condition:
        raise R002V2RunnerError(stage, message)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _validate_diagnostic_executions_field(manifest: dict[str, Any]) -> None:
    field = "diagnostic_executions"
    _require(field in manifest, "manifest_schema", "missing required field: diagnostic_executions")
    value = manifest[field]
    _require(
        not isinstance(value, bool) and isinstance(value, int),
        "manifest_schema",
        "diagnostic_executions must be an integer; bool is rejected",
    )
    _require(value == 0, "manifest_schema", "diagnostic_executions must equal zero")


def _validate_manifest(manifest_path: Path, manifest_sha256: str) -> dict[str, Any]:
    expected = (REPO_ROOT / FROZEN_MANIFEST).resolve()
    _require(manifest_path.resolve() == expected, "manifest_identity", "only the frozen r002 v2 manifest is accepted")
    data = manifest_path.read_bytes()
    _require(_sha(data) == manifest_sha256, "manifest_hash", "frozen manifest SHA-256 mismatch")
    manifest = json.loads(data)
    _require(isinstance(manifest, dict), "manifest_schema", "manifest root must be an object")
    _require(
        manifest.get("status") == "r002_v2_calibration_prepared_formal_locked",
        "manifest_schema",
        "manifest status mismatch",
    )
    _validate_diagnostic_executions_field(manifest)
    _require(not (REPO_ROOT / CALIBRATION_OUTPUT).exists(), "output_preflight", "calibration output path already exists")
    _require(not (REPO_ROOT / FORMAL_OUTPUT).exists(), "output_preflight", "formal output path already exists")
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


def _calibration_all_passed(
    directory: Path,
    calibration_execution_manifest_sha256: str,
    expected_source_manifest_sha256: str,
) -> bool:
    """Validate calibration using its execution_manifest.json *file* SHA.

    The receipt's source_manifest_sha256 is a separate provenance assertion
    and must identify the frozen r002 v2 source manifest.
    """
    receipt_path = directory / "execution_manifest.json"
    result_path = directory / "calibration_results.csv"
    _require(receipt_path.is_file() and result_path.is_file(), "formal_gate", "calibration artifacts are missing")
    receipt_bytes = receipt_path.read_bytes()
    _require(
        _sha(receipt_bytes) == calibration_execution_manifest_sha256,
        "formal_gate",
        "calibration execution_manifest.json SHA-256 mismatch",
    )
    receipt = json.loads(receipt_bytes)
    _require(
        receipt.get("source_manifest_sha256") == expected_source_manifest_sha256,
        "formal_gate",
        "calibration source manifest SHA-256 mismatch",
    )
    rows = execution_core._read_csv(result_path)
    return bool(
        receipt.get("formal_198_authorized")
        and len(rows) == CALIBRATION_CELLS
        and all(
            row["worker_ready"] == "True"
            and row["phase"] == "completed"
            and row["termination"] == "returned"
            and row["ipc_status"] == "result_received"
            and row["child_exit_bucket"] == "exit_0"
            for row in rows
        )
    )


def run(
    mode: str,
    manifest_path: Path,
    manifest_sha256: str,
    output_dir: Path,
    execute: bool,
    calibration_execution_manifest_sha256: str | None = None,
) -> None:
    _require(execute, "execution_authorization", "explicit execution flag is required")
    _require(os.name != "nt" and not sys.platform.startswith("win"), "environment", "WSL/Linux is required")
    _require(sys.version_info[:2] == (3, 14), "environment", "Python 3.14 is required")
    _require(threading.active_count() == 1, "environment", "parent process must be single-threaded")
    manifest = _validate_manifest(manifest_path, manifest_sha256)
    expected_output = REPO_ROOT / (CALIBRATION_OUTPUT if mode == "calibration" else FORMAL_OUTPUT)
    _require(output_dir.resolve() == expected_output.resolve(), "output_preflight", "output path mismatch")
    _require(not output_dir.exists(), "output_preflight", "output path already exists")
    if mode == "formal":
        _require(
            bool(calibration_execution_manifest_sha256),
            "formal_gate",
            "formal mode requires calibration execution_manifest.json SHA-256",
        )
        _require(
            _calibration_all_passed(
                REPO_ROOT / CALIBRATION_OUTPUT,
                str(calibration_execution_manifest_sha256),
                manifest_sha256,
            ),
            "formal_gate",
            "calibration controls did not all pass; formal 198 is prohibited",
        )

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
    ledger_name = "calibration_cohort.csv" if mode == "calibration" else "formal198_input_ledger.csv"
    ledger = execution_core._read_csv(manifest_path.parent / ledger_name)
    expected_count = CALIBRATION_CELLS if mode == "calibration" else FORMAL_CELLS
    _require(len(ledger) == expected_count, "input_ledger", "input ledger row count mismatch")
    sources = execution_core._load_selected_sources({row["program_id"] for row in ledger})
    rows: list[dict[str, Any]] = []
    protocol_sha = manifest["calibration_protocol_sha256"] if mode == "calibration" else manifest["formal_protocol_sha256"]
    for ledger_row in ledger:
        source = sources[ledger_row["program_id"]]
        _require(
            _sha(source.encode("utf-8")) == ledger_row["evaluation_source_sha256"],
            "input_ledger",
            "evaluation source SHA-256 mismatch",
        )
        problem = task_by_hash.get(ledger_row["task_identity_sha256"])
        _require(problem is not None, "input_ledger", "task identity is absent from frozen dataset")
        observed = execution_core._run_cell(source, problem, ledger_row["program_id"])
        rows.append({
            "cell_identity_sha256": ledger_row["cell_identity_sha256"],
            "program_id": ledger_row["program_id"],
            "task_identity_sha256": ledger_row["task_identity_sha256"],
            "evaluation_source_sha256": ledger_row["evaluation_source_sha256"],
            "evaluator_hash": ledger_row["evaluator_hash"],
            "protocol_sha256": protocol_sha,
            **observed,
        })
    execution_core._validate_result_rows(rows, expected_count)
    result_bytes = execution_core._csv_bytes(rows)
    calibration_ok = mode == "calibration" and all(
        row["worker_ready"] is True
        and row["phase"] == "completed"
        and row["termination"] == "returned"
        and row["ipc_status"] == "result_received"
        and row["child_exit_bucket"] == "exit_0"
        for row in rows
    )
    receipt = {
        "status": f"r002_v2_{mode}_complete",
        "mode": mode,
        "cells": expected_count,
        "results_sha256": _sha(result_bytes),
        "source_manifest_sha256": manifest_sha256,
        "dataset_initialized_once_in_parent": True,
        "worker_ready_handshake": True,
        "startup_and_execution_timeouts_separate": True,
        "formal_198_authorized": calibration_ok if mode == "calibration" else True,
        "hidden_input_expected_actual_message_traceback_saved": False,
        "healer_runtime_input": False,
        "evalplus_correctness_executions": 0,
        "model_calls": 0,
        "retry_resume_overwrite": False,
    }
    output_dir.mkdir(parents=True)
    result_name = "calibration_results.csv" if mode == "calibration" else "coarse_diagnostics.csv"
    (output_dir / result_name).write_bytes(result_bytes)
    (output_dir / "execution_manifest.json").write_bytes((json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode("utf-8"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("calibration", "formal"), required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--calibration-execution-manifest-sha256")
    parser.add_argument("--execute-r002-diagnostics", action="store_true")
    return parser


def _safe_cli_error(exc: BaseException) -> tuple[str, str, str]:
    if isinstance(exc, R002V2RunnerError):
        return exc.stage, type(exc).__name__, exc.safe_message
    if isinstance(exc, ImportError):
        return "dataset_initialization", type(exc).__name__, "required dependency import failed"
    if isinstance(exc, KeyError):
        return "runtime_schema", type(exc).__name__, "required runtime field is missing"
    if isinstance(exc, execution_core.R002RunnerError):
        return "diagnostic_validation", type(exc).__name__, "diagnostic validation failed"
    if isinstance(exc, json.JSONDecodeError):
        return "manifest_schema", type(exc).__name__, "JSON decoding failed"
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
        R002V2RunnerError,
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
