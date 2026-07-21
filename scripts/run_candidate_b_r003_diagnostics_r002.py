#!/usr/bin/env python3
"""Run Candidate B r003 diagnostics r002 calibration or gated formal mode in WSL.

The parent receives a worker-ready handshake before starting the candidate
timer.  IPC uses one-way Pipes and receives the payload before joining.
"""

from __future__ import annotations

import argparse
import ast
import contextlib
import copy
import csv
import hashlib
import importlib.metadata
import inspect
import io
import json
import multiprocessing
import os
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
FROZEN_RELATIVE = Path("artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v1")
FROZEN_MANIFEST = FROZEN_RELATIVE / "manifest.json"
CALIBRATION_OUTPUT = FROZEN_RELATIVE / "manual_calibration_run_001"
FORMAL_OUTPUT = FROZEN_RELATIVE / "manual_formal_diagnostics_run_001"
JOURNAL = Path("artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/mbpp_q35_9b_candidate_b_development60_replay_r003/h0_h1_accounts.jsonl")
EXPECTED_EVALPLUS_VERSION = "0.3.1"
EXPECTED_DATASET_VERSION = "v0.2.0"
EXPECTED_DATASET_HASH = "ee43ecabebf20deef4bb776a405ac5b1"
STARTUP_TIMEOUT_SECONDS = 30
EXECUTION_TIMEOUT_SECONDS = 30
CALIBRATION_CELLS = 8
FORMAL_CELLS = 198

RESULT_FIELDS = (
    "cell_identity_sha256", "program_id", "task_identity_sha256",
    "evaluation_source_sha256", "evaluator_hash", "protocol_sha256",
    "phase", "exception_class", "model_source_line", "model_source_ast_node",
    "entry_point_bound", "entry_point_callable", "signature_binding",
    "termination", "return_type_bucket", "return_shape_bucket",
    "worker_ready", "startup_duration_bucket", "execution_duration_bucket",
    "ipc_status", "child_exit_bucket",
)


class R002RunnerError(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise R002RunnerError(message)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _csv_bytes(rows: list[dict[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=RESULT_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows({field: row.get(field, "") for field in RESULT_FIELDS} for row in rows)
    return stream.getvalue().encode("utf-8")


def _duration_bucket(seconds: float) -> str:
    for limit, label in ((0.1, "lt_0_1s"), (0.5, "0_1_to_0_5s"), (1, "0_5_to_1s"), (2, "1_to_2s"), (5, "2_to_5s"), (10, "5_to_10s"), (30, "10_to_30s")):
        if seconds < limit:
            return label
    return "gte_30s"


def _task_identity(task_id: str) -> str:
    return _sha(task_id.encode("utf-8"))


def _load_selected_sources(wanted: set[str]) -> dict[str, str]:
    selected: dict[str, str] = {}
    needles = {pid: f'"program_id": "{pid}"' for pid in wanted}
    with (REPO_ROOT / JOURNAL).open(encoding="utf-8") as handle:
        for line in handle:
            pid = next((key for key, needle in needles.items() if needle in line), None)
            if pid is None:
                continue
            row = json.loads(line)
            if row["healer_account"] != "H0":
                continue
            _require(pid not in selected, f"duplicate H0 source: {pid}")
            selected[pid] = row["evaluation_source"]
    _require(set(selected) == wanted, "source identity mismatch")
    return selected


def _function_accepts(function: ast.FunctionDef | ast.AsyncFunctionDef, arities: set[int]) -> bool:
    positional = len(function.args.posonlyargs) + len(function.args.args)
    minimum = positional - len(function.args.defaults)
    maximum: int | None = None if function.args.vararg else positional
    return all(arity >= minimum and (maximum is None or arity <= maximum) for arity in arities)


def _static_g3e(tree: ast.Module, entry_point: str, arities: set[int]) -> tuple[bool, bool]:
    definitions = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == entry_point]
    return bool(definitions), bool(definitions) and _function_accepts(definitions[-1], arities)


def _bucket(value: Any) -> tuple[str, str]:
    if value is None: return "none", "none"
    if isinstance(value, bool): return "bool", "scalar"
    if isinstance(value, int): return "int", "scalar"
    if isinstance(value, float): return "float", "scalar"
    if isinstance(value, complex): return "complex", "scalar"
    if isinstance(value, (str, bytes, list, tuple)):
        return type(value).__name__, "empty_sequence" if not value else "nonempty_sequence"
    if isinstance(value, dict): return "dict", "empty_mapping" if not value else "nonempty_mapping"
    if isinstance(value, (set, frozenset)): return "set", "empty_set" if not value else "nonempty_set"
    return "other", "other"


def _model_line(exc: BaseException, filename: str) -> int | None:
    line = None
    tb = exc.__traceback__
    while tb is not None:
        if tb.tb_frame.f_code.co_filename == filename:
            line = tb.tb_lineno
        tb = tb.tb_next
    return line


def _ast_node(source: str, line: int | None) -> str:
    if line is None: return ""
    nodes = [node for node in ast.walk(ast.parse(source)) if getattr(node, "lineno", None) == line]
    return type(nodes[-1]).__name__ if nodes else ""


def _send_result(connection: Any, result: dict[str, Any]) -> None:
    connection.send(("result", result))
    connection.close()


def _worker(ready_send: Any, control_recv: Any, result_send: Any, source: str, prompt: str, entry_point: str, base_inputs: list[Any], plus_inputs: list[Any], program_id: str) -> None:
    filename = f"<candidate:{program_id}>"
    ready_sent = False
    try:
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (1024 * 1024 * 1024, 1024 * 1024 * 1024))
        resource.setrlimit(resource.RLIMIT_FSIZE, (1024 * 1024, 1024 * 1024))
        os.environ.clear()
        temporary = tempfile.TemporaryDirectory()
        os.chdir(temporary.name)
        ready_send.send(("ready",))
        ready_sent = True
        ready_send.close()
        if control_recv.recv() != "go":
            raise RuntimeError("control_protocol")
        control_recv.close()
        resource.setrlimit(resource.RLIMIT_CPU, (EXECUTION_TIMEOUT_SECONDS, EXECUTION_TIMEOUT_SECONDS + 1))
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            namespace: dict[str, Any] = {}
            try:
                exec(compile(prompt + source, filename, "exec"), namespace, namespace)
            except BaseException as exc:
                _send_result(result_send, {"phase": "G2_module", "exception_class": type(exc).__name__, "model_source_line": _model_line(exc, filename), "entry_point_bound": False, "entry_point_callable": False, "signature_binding": "not_assessed", "termination": "raised", "return_type_bucket": "", "return_shape_bucket": ""})
                return
            bound = entry_point in namespace
            callable_value = callable(namespace.get(entry_point))
            if not bound or not callable_value:
                _send_result(result_send, {"phase": "G3e", "exception_class": "", "model_source_line": None, "entry_point_bound": bound, "entry_point_callable": callable_value, "signature_binding": "failed", "termination": "not_run", "return_type_bucket": "", "return_shape_bucket": ""})
                return
            function = namespace[entry_point]
            try:
                for inputs in base_inputs + plus_inputs:
                    inspect.signature(function).bind(*inputs)
            except (TypeError, ValueError):
                _send_result(result_send, {"phase": "G3e", "exception_class": "", "model_source_line": None, "entry_point_bound": True, "entry_point_callable": True, "signature_binding": "failed", "termination": "not_run", "return_type_bucket": "", "return_shape_bucket": ""})
                return
            types: set[str] = set()
            shapes: set[str] = set()
            for phase, inputs_list in (("G2_base", base_inputs), ("G2_plus", plus_inputs)):
                for inputs in inputs_list:
                    try:
                        type_bucket, shape_bucket = _bucket(function(*copy.deepcopy(inputs)))
                        types.add(type_bucket); shapes.add(shape_bucket)
                    except BaseException as exc:
                        _send_result(result_send, {"phase": phase, "exception_class": type(exc).__name__, "model_source_line": _model_line(exc, filename), "entry_point_bound": True, "entry_point_callable": True, "signature_binding": "passed", "termination": "raised", "return_type_bucket": "", "return_shape_bucket": ""})
                        return
            _send_result(result_send, {"phase": "completed", "exception_class": "", "model_source_line": None, "entry_point_bound": True, "entry_point_callable": True, "signature_binding": "passed", "termination": "returned", "return_type_bucket": next(iter(types)) if len(types) == 1 else "mixed", "return_shape_bucket": next(iter(shapes)) if len(shapes) == 1 else "mixed"})
    except BaseException as exc:
        try:
            connection = result_send if ready_sent else ready_send
            connection.send(("startup_or_ipc_error", type(exc).__name__))
            connection.close()
        except BaseException:
            pass


def _exit_bucket(exitcode: int | None) -> str:
    if exitcode is None: return "not_exited"
    if exitcode == 0: return "exit_0"
    if exitcode < 0: return "signal_exit"
    return "nonzero_exit"


def _base_result(**updates: Any) -> dict[str, Any]:
    result = {"phase": "infrastructure", "exception_class": "", "model_source_line": "", "model_source_ast_node": "", "entry_point_bound": False, "entry_point_callable": False, "signature_binding": "not_assessed", "termination": "not_run", "return_type_bucket": "", "return_shape_bucket": "", "worker_ready": False, "startup_duration_bucket": "", "execution_duration_bucket": "", "ipc_status": "", "child_exit_bucket": ""}
    result.update(updates)
    return result


def _run_cell(source: str, problem: dict[str, Any], program_id: str) -> dict[str, Any]:
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return _base_result(phase="G1", exception_class=type(exc).__name__, model_source_line=exc.lineno, termination="not_run", ipc_status="not_started")
    all_inputs = list(problem["base_input"]) + list(problem["plus_input"])
    name_bound, signature_ok = _static_g3e(tree, problem["entry_point"], {len(item) for item in all_inputs})
    if not name_bound or not signature_ok:
        return _base_result(phase="G3e", entry_point_bound=name_bound, entry_point_callable=name_bound, signature_binding="passed" if signature_ok else "failed", ipc_status="not_started")
    context = multiprocessing.get_context("fork")
    ready_recv, ready_send = context.Pipe(duplex=False)
    control_recv, control_send = context.Pipe(duplex=False)
    result_recv, result_send = context.Pipe(duplex=False)
    process = context.Process(target=_worker, args=(ready_send, control_recv, result_send, source, problem["prompt"], problem["entry_point"], list(problem["base_input"]), list(problem["plus_input"]), program_id))
    startup_start = time.monotonic()
    process.start()
    ready_send.close(); control_recv.close(); result_send.close()
    if not ready_recv.poll(STARTUP_TIMEOUT_SECONDS):
        process.join(0.2)
        if process.is_alive(): process.terminate(); process.join()
        return _base_result(exception_class="StartupTimeout", startup_duration_bucket="gte_30s", ipc_status="ready_timeout", child_exit_bucket=_exit_bucket(process.exitcode))
    try:
        event = ready_recv.recv()
    except EOFError:
        process.join(0.2)
        return _base_result(exception_class="WorkerProcessExit", startup_duration_bucket=_duration_bucket(time.monotonic() - startup_start), ipc_status="ready_eof", child_exit_bucket=_exit_bucket(process.exitcode))
    startup_bucket = _duration_bucket(time.monotonic() - startup_start)
    if event != ("ready",):
        if process.is_alive(): process.terminate(); process.join()
        exception_class = str(event[1]) if isinstance(event, tuple) and len(event) > 1 else "WorkerStartupError"
        return _base_result(exception_class=exception_class, startup_duration_bucket=startup_bucket, ipc_status="startup_error", child_exit_bucket=_exit_bucket(process.exitcode))
    execution_start = time.monotonic()
    control_send.send("go"); control_send.close()
    if not result_recv.poll(EXECUTION_TIMEOUT_SECONDS):
        if process.is_alive(): process.terminate(); process.join()
        return _base_result(phase="G2", exception_class="TimeoutError", entry_point_bound=True, entry_point_callable=True, signature_binding="passed", termination="timeout", worker_ready=True, startup_duration_bucket=startup_bucket, execution_duration_bucket="gte_30s", ipc_status="result_timeout", child_exit_bucket=_exit_bucket(process.exitcode))
    try:
        event = result_recv.recv()
    except EOFError:
        process.join(0.2)
        return _base_result(exception_class="WorkerProcessExit", worker_ready=True, startup_duration_bucket=startup_bucket, execution_duration_bucket=_duration_bucket(time.monotonic() - execution_start), ipc_status="result_eof", child_exit_bucket=_exit_bucket(process.exitcode))
    execution_bucket = _duration_bucket(time.monotonic() - execution_start)
    if not isinstance(event, tuple) or not event:
        if process.is_alive(): process.terminate(); process.join()
        return _base_result(exception_class="IPCProtocolError", worker_ready=True, startup_duration_bucket=startup_bucket, execution_duration_bucket=execution_bucket, ipc_status="invalid_result", child_exit_bucket=_exit_bucket(process.exitcode))
    if event[0] != "result":
        process.join(0.2)
        return _base_result(exception_class=str(event[1]) if len(event) > 1 else "WorkerError", worker_ready=True, startup_duration_bucket=startup_bucket, execution_duration_bucket=execution_bucket, ipc_status="worker_error", child_exit_bucket=_exit_bucket(process.exitcode))
    payload = event[1]
    line = payload.get("model_source_line")
    payload["model_source_line"] = "" if line is None else line
    payload["model_source_ast_node"] = _ast_node(source, line)
    process.join(2)
    if process.is_alive(): process.terminate(); process.join()
    payload.update({"worker_ready": True, "startup_duration_bucket": startup_bucket, "execution_duration_bucket": execution_bucket, "ipc_status": "result_received", "child_exit_bucket": _exit_bucket(process.exitcode)})
    return payload


def _validate_manifest(manifest_path: Path, manifest_sha: str) -> dict[str, Any]:
    _require(manifest_path.resolve() == (REPO_ROOT / FROZEN_MANIFEST).resolve(), "only frozen r002 manifest accepted")
    data = manifest_path.read_bytes(); _require(_sha(data) == manifest_sha, "manifest hash mismatch")
    manifest = json.loads(data)
    _require(manifest["status"] == "r002_calibration_prepared_formal_locked", "manifest status drift")
    _require(manifest["diagnostic_executions"] == 0, "manifest is not pre-execution")
    for name, digest in manifest["outputs_sha256_excluding_manifest_and_operator_guide"].items():
        path = manifest_path.parent / name
        _require(path.is_file() and _sha(path.read_bytes()) == digest, f"artifact hash drift: {name}")
    for name, digest in manifest["source_sha256"].items():
        path = REPO_ROOT / name
        _require(path.is_file() and _sha(path.read_bytes()) == digest, f"source hash drift: {name}")
    return manifest


def _calibration_all_passed(directory: Path, manifest_sha: str) -> bool:
    receipt_path = directory / "execution_manifest.json"; result_path = directory / "calibration_results.csv"
    _require(receipt_path.is_file() and result_path.is_file(), "calibration artifacts missing")
    _require(_sha(receipt_path.read_bytes()) == manifest_sha, "calibration manifest hash mismatch")
    receipt = json.loads(receipt_path.read_bytes())
    rows = _read_csv(result_path)
    return bool(receipt.get("formal_198_authorized") and len(rows) == CALIBRATION_CELLS and all(row["worker_ready"] == "True" and row["phase"] == "completed" and row["termination"] == "returned" and row["ipc_status"] == "result_received" and row["child_exit_bucket"] == "exit_0" for row in rows))


def _validate_result_rows(rows: list[dict[str, Any]], expected_count: int) -> None:
    _require(len(rows) == expected_count, "result row count drift")
    _require(all(set(row) == set(RESULT_FIELDS) for row in rows), "unknown or missing result field")
    _require(len({row["cell_identity_sha256"] for row in rows}) == expected_count, "duplicate result identity")
    allowed_phases = {"infrastructure", "G1", "G3e", "G2", "G2_module", "G2_base", "G2_plus", "completed"}
    duration_buckets = {"", "lt_0_1s", "0_1_to_0_5s", "0_5_to_1s", "1_to_2s", "2_to_5s", "5_to_10s", "10_to_30s", "gte_30s"}
    for row in rows:
        _require(row["phase"] in allowed_phases, "unknown result phase")
        _require(row["startup_duration_bucket"] in duration_buckets and row["execution_duration_bucket"] in duration_buckets, "duration bucket drift")
        for value in row.values():
            _require("\n" not in str(value) and "\r" not in str(value), "multiline result value rejected")


def run(mode: str, manifest_path: Path, manifest_sha: str, output_dir: Path, execute: bool, calibration_manifest_sha: str | None = None) -> None:
    _require(execute, "explicit execution flag required")
    _require(os.name != "nt" and not sys.platform.startswith("win"), "WSL/Linux required")
    _require(sys.version_info[:2] == (3, 14), "Python 3.14 required")
    _require(threading.active_count() == 1, "parent must be single-threaded before explicit fork")
    manifest = _validate_manifest(manifest_path, manifest_sha)
    expected_output = REPO_ROOT / (CALIBRATION_OUTPUT if mode == "calibration" else FORMAL_OUTPUT)
    _require(output_dir.resolve() == expected_output.resolve() and not output_dir.exists(), "output path/state rejected")
    if mode == "formal":
        _require(bool(calibration_manifest_sha), "formal mode requires calibration manifest SHA")
        _require(_calibration_all_passed(REPO_ROOT / CALIBRATION_OUTPUT, str(calibration_manifest_sha)), "calibration gate failed; formal 198 prohibited")
    _require(importlib.metadata.version("evalplus") == EXPECTED_EVALPLUS_VERSION, "dataset loader version drift")
    from evalplus.data import get_mbpp_plus, get_mbpp_plus_hash
    _require(get_mbpp_plus_hash(version=EXPECTED_DATASET_VERSION) == EXPECTED_DATASET_HASH, "dataset hash drift")
    problems = get_mbpp_plus(version=EXPECTED_DATASET_VERSION)
    task_by_hash = {_task_identity(task_id): problem for task_id, problem in problems.items()}
    ledger_name = "calibration_cohort.csv" if mode == "calibration" else "formal198_input_ledger.csv"
    ledger = _read_csv(manifest_path.parent / ledger_name)
    expected_count = CALIBRATION_CELLS if mode == "calibration" else FORMAL_CELLS
    _require(len(ledger) == expected_count, "ledger count drift")
    sources = _load_selected_sources({row["program_id"] for row in ledger})
    rows: list[dict[str, Any]] = []
    protocol_sha = manifest["calibration_protocol_sha256"] if mode == "calibration" else manifest["formal_protocol_sha256"]
    for ledger_row in ledger:
        source = sources[ledger_row["program_id"]]
        _require(_sha(source.encode()) == ledger_row["evaluation_source_sha256"], "source hash drift")
        problem = task_by_hash.get(ledger_row["task_identity_sha256"]); _require(problem is not None, "task hash missing")
        observed = _run_cell(source, problem, ledger_row["program_id"])
        rows.append({"cell_identity_sha256": ledger_row["cell_identity_sha256"], "program_id": ledger_row["program_id"], "task_identity_sha256": ledger_row["task_identity_sha256"], "evaluation_source_sha256": ledger_row["evaluation_source_sha256"], "evaluator_hash": ledger_row["evaluator_hash"], "protocol_sha256": protocol_sha, **observed})
    _validate_result_rows(rows, expected_count)
    result_bytes = _csv_bytes(rows)
    calibration_ok = mode == "calibration" and all(row["worker_ready"] is True and row["phase"] == "completed" and row["termination"] == "returned" and row["ipc_status"] == "result_received" and row["child_exit_bucket"] == "exit_0" for row in rows)
    receipt = {"status": f"r002_{mode}_complete", "mode": mode, "cells": expected_count, "results_sha256": _sha(result_bytes), "source_manifest_sha256": manifest_sha, "dataset_initialized_once_in_parent": True, "worker_ready_handshake": True, "startup_and_execution_timeouts_separate": True, "formal_198_authorized": calibration_ok if mode == "calibration" else True, "hidden_input_expected_actual_message_traceback_saved": False, "healer_runtime_input": False, "evalplus_correctness_executions": 0, "model_calls": 0, "retry_resume_overwrite": False}
    output_dir.mkdir(parents=True)
    result_name = "calibration_results.csv" if mode == "calibration" else "coarse_diagnostics.csv"
    (output_dir / result_name).write_bytes(result_bytes)
    (output_dir / "execution_manifest.json").write_bytes((json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("calibration", "formal"), required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--calibration-manifest-sha256")
    parser.add_argument("--execute-r002-diagnostics", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        run(args.mode, args.manifest, args.manifest_sha256, args.output_dir, args.execute_r002_diagnostics, args.calibration_manifest_sha256)
    except (R002RunnerError, ImportError, KeyError, OSError, ValueError):
        print("R002RunnerError", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
