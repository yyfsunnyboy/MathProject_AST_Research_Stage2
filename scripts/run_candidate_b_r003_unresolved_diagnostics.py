#!/usr/bin/env python3
"""Run the frozen unresolved-198 coarse diagnostics once, manually, in WSL.

Importing this module and invoking its parser never executes diagnostics.  The
future execution path requires the explicit --execute-frozen-diagnostics flag.
It does not run EvalPlus correctness and never serializes test values.
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
from pathlib import Path
from typing import Any, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
FROZEN_RELATIVE = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_v3_crosswalk_diagnostics_protocol_v1"
)
FROZEN_MANIFEST = FROZEN_RELATIVE / "manifest.json"
FROZEN_OUTPUT = FROZEN_RELATIVE / "manual_diagnostics_run_001"
JOURNAL = Path(
    "artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/"
    "mbpp_q35_9b_candidate_b_development60_replay_r003/h0_h1_accounts.jsonl"
)
EXPECTED_EVALPLUS_VERSION = "0.3.1"
EXPECTED_DATASET_VERSION = "v0.2.0"
EXPECTED_DATASET_HASH = "ee43ecabebf20deef4bb776a405ac5b1"
EXPECTED_CELLS = 198
TIMEOUT_SECONDS = 10

RESULT_FIELDS = (
    "cell_identity_sha256", "program_id", "task_identity_sha256",
    "evaluation_source_sha256", "evaluator_hash", "protocol_sha256",
    "phase", "exception_class", "model_source_line",
    "model_source_ast_node", "entry_point_bound", "entry_point_callable",
    "signature_binding", "termination", "return_type_bucket",
    "return_shape_bucket",
)


class DiagnosticRunnerError(RuntimeError):
    """Fail-closed frozen protocol or execution error."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise DiagnosticRunnerError(message)


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


def _task_identity(task_id: str) -> str:
    return _sha(task_id.encode("utf-8"))


def _load_selected_sources(repo: Path, wanted: set[str]) -> dict[str, str]:
    selected: dict[str, str] = {}
    needles = {pid: f'"program_id": "{pid}"' for pid in wanted}
    with (repo / JOURNAL).open(encoding="utf-8") as handle:
        for line in handle:
            pid = next((key for key, needle in needles.items() if needle in line), None)
            if pid is None:
                continue
            row = json.loads(line)
            if row["healer_account"] != "H0":
                continue
            _require(pid not in selected, f"duplicate H0 source: {pid}")
            source = row["evaluation_source"]
            _require(isinstance(source, str), f"missing H0 source: {pid}")
            selected[pid] = source
    _require(set(selected) == wanted, "missing or unexpected unresolved source identity")
    return selected


def _validate_frozen_inputs(
    manifest_path: Path, manifest_sha256: str, output_dir: Path, parallel: int,
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, str]]]:
    _require(manifest_path.resolve() == (REPO_ROOT / FROZEN_MANIFEST).resolve(), "only frozen manifest path accepted")
    _require(output_dir.resolve() == (REPO_ROOT / FROZEN_OUTPUT).resolve(), "only frozen output path accepted")
    _require(parallel == 1, "parallel must equal 1")
    _require(not output_dir.exists(), "diagnostic output already exists; retry/resume/overwrite forbidden")
    manifest_bytes = manifest_path.read_bytes()
    _require(_sha(manifest_bytes) == manifest_sha256, "manifest SHA-256 argument/bytes mismatch")
    manifest = json.loads(manifest_bytes)
    _require(manifest["status"] == "complete_crosswalk_diagnostics_prepared_not_executed", "manifest status drift")
    _require(manifest["counts"]["diagnostic_input_cells"] == EXPECTED_CELLS, "diagnostic count drift")
    _require(manifest["diagnostic_executions"] == 0, "manifest is not pre-execution")
    _require(manifest["diagnostics_output_directory_created"] is False, "output directory state drift")
    _require(manifest["healer_rules_modified"] is False, "Healer modification flag drift")
    for name, digest in manifest["outputs_sha256_excluding_manifest_and_operator_guide"].items():
        path = manifest_path.parent / name
        _require(path.is_file() and _sha(path.read_bytes()) == digest, f"frozen output hash drift: {name}")
    for name, digest in manifest["source_sha256"].items():
        path = REPO_ROOT / name
        _require(path.is_file() and _sha(path.read_bytes()) == digest, f"reproducibility source hash drift: {name}")
    source_ledger = _read_csv(manifest_path.parent / "source_hash_ledger.csv")
    for row in source_ledger:
        if row["role"] != "frozen_repo_input":
            continue
        path = REPO_ROOT / row["path"]
        _require(path.is_file() and _sha(path.read_bytes()) == row["sha256"], f"frozen repo source drift: {row['path']}")
    protocol_path = manifest_path.parent / "diagnostics_protocol.json"
    _require(_sha(protocol_path.read_bytes()) == manifest["diagnostics_protocol_sha256"], "protocol hash drift")
    protocol = json.loads(protocol_path.read_bytes())
    _require(protocol["status"] == "prepared_not_executed", "protocol status drift")
    _require(protocol["allowed_result_fields"] == list(RESULT_FIELDS), "result allowlist drift")
    _require(protocol["healer_runtime_input"] is False, "diagnostics-to-Healer isolation drift")
    ledger = _read_csv(manifest_path.parent / "unresolved198_diagnostics_input_ledger.csv")
    _require(len(ledger) == EXPECTED_CELLS, "diagnostic ledger row-count drift")
    _require(len({row["cell_identity_sha256"] for row in ledger}) == EXPECTED_CELLS, "duplicate diagnostic identity")
    _require(all(row["primary_failure_layer"] == "" and row["classification_status"] == "PENDING_REVIEW" for row in ledger), "unresolved layer/status drift")
    _require(all(row["protocol_sha256"] == manifest["diagnostics_protocol_sha256"] for row in ledger), "ledger protocol hash drift")
    return manifest, protocol, ledger


def _function_accepts(function: ast.FunctionDef | ast.AsyncFunctionDef, arities: set[int]) -> bool:
    positional = len(function.args.posonlyargs) + len(function.args.args)
    minimum = positional - len(function.args.defaults)
    maximum: int | None = None if function.args.vararg else positional
    return all(arity >= minimum and (maximum is None or arity <= maximum) for arity in arities)


def _static_g3e(tree: ast.Module, entry_point: str, arities: set[int]) -> tuple[bool, bool]:
    definitions = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == entry_point]
    assignments = [node for node in tree.body if isinstance(node, (ast.Assign, ast.AnnAssign))]
    name_bound = bool(definitions) or any(
        any(isinstance(target, ast.Name) and target.id == entry_point for target in (node.targets if isinstance(node, ast.Assign) else [node.target]))
        for node in assignments
    )
    signature_compatible = bool(definitions) and _function_accepts(definitions[-1], arities)
    return name_bound, signature_compatible


def _ast_node_at_line(source: str, line: int | None) -> str:
    if line is None:
        return ""
    try:
        nodes = [node for node in ast.walk(ast.parse(source)) if getattr(node, "lineno", None) == line]
    except SyntaxError:
        return ""
    return type(nodes[-1]).__name__ if nodes else ""


def _return_buckets(values: list[Any]) -> tuple[str, str]:
    type_buckets: set[str] = set()
    shape_buckets: set[str] = set()
    for value in values:
        if value is None:
            type_bucket, shape = "none", "none"
        elif isinstance(value, bool):
            type_bucket, shape = "bool", "scalar"
        elif isinstance(value, int):
            type_bucket, shape = "int", "scalar"
        elif isinstance(value, float):
            type_bucket, shape = "float", "scalar"
        elif isinstance(value, complex):
            type_bucket, shape = "complex", "scalar"
        elif isinstance(value, str):
            type_bucket, shape = "str", "empty_sequence" if not value else "nonempty_sequence"
        elif isinstance(value, bytes):
            type_bucket, shape = "bytes", "empty_sequence" if not value else "nonempty_sequence"
        elif isinstance(value, list):
            type_bucket, shape = "list", "empty_sequence" if not value else "nonempty_sequence"
        elif isinstance(value, tuple):
            type_bucket, shape = "tuple", "empty_sequence" if not value else "nonempty_sequence"
        elif isinstance(value, dict):
            type_bucket, shape = "dict", "empty_mapping" if not value else "nonempty_mapping"
        elif isinstance(value, (set, frozenset)):
            type_bucket, shape = "set", "empty_set" if not value else "nonempty_set"
        else:
            type_bucket, shape = "other", "other"
        type_buckets.add(type_bucket)
        shape_buckets.add(shape)
    return (
        next(iter(type_buckets)) if len(type_buckets) == 1 else "mixed",
        next(iter(shape_buckets)) if len(shape_buckets) == 1 else "mixed",
    )


def _model_frame_line(exc: BaseException, filename: str) -> int | None:
    line: int | None = None
    tb = exc.__traceback__
    while tb is not None:
        if tb.tb_frame.f_code.co_filename == filename:
            line = tb.tb_lineno
        tb = tb.tb_next
    return line


def _worker(queue: Any, source: str, prompt: str, entry_point: str, base_inputs: list[Any], plus_inputs: list[Any], program_id: str) -> None:
    filename = f"<candidate:{program_id}>"
    try:
        import resource
        resource.setrlimit(resource.RLIMIT_CPU, (TIMEOUT_SECONDS, TIMEOUT_SECONDS + 1))
        resource.setrlimit(resource.RLIMIT_AS, (1024 * 1024 * 1024, 1024 * 1024 * 1024))
        resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
        os.environ.clear()
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            os.chdir(directory)
            namespace: dict[str, Any] = {}
            try:
                exec(compile(prompt + source, filename, "exec"), namespace, namespace)
            except BaseException as exc:
                queue.put({"phase": "G2_module", "exception_class": type(exc).__name__, "model_source_line": _model_frame_line(exc, filename), "entry_point_bound": False, "entry_point_callable": False, "signature_binding": "not_assessed", "termination": "raised", "return_type_bucket": "", "return_shape_bucket": ""})
                return
            bound = entry_point in namespace
            callable_value = callable(namespace.get(entry_point))
            if not bound or not callable_value:
                queue.put({"phase": "G3e", "exception_class": "", "model_source_line": None, "entry_point_bound": bound, "entry_point_callable": callable_value, "signature_binding": "failed", "termination": "not_run", "return_type_bucket": "", "return_shape_bucket": ""})
                return
            function = namespace[entry_point]
            try:
                for inputs in base_inputs + plus_inputs:
                    inspect.signature(function).bind(*inputs)
            except (TypeError, ValueError):
                queue.put({"phase": "G3e", "exception_class": "", "model_source_line": None, "entry_point_bound": True, "entry_point_callable": True, "signature_binding": "failed", "termination": "not_run", "return_type_bucket": "", "return_shape_bucket": ""})
                return
            values: list[Any] = []
            for phase, inputs_list in (("G2_base", base_inputs), ("G2_plus", plus_inputs)):
                for inputs in inputs_list:
                    try:
                        values.append(function(*copy.deepcopy(inputs)))
                    except BaseException as exc:
                        queue.put({"phase": phase, "exception_class": type(exc).__name__, "model_source_line": _model_frame_line(exc, filename), "entry_point_bound": True, "entry_point_callable": True, "signature_binding": "passed", "termination": "raised", "return_type_bucket": "", "return_shape_bucket": ""})
                        return
            type_bucket, shape_bucket = _return_buckets(values)
            queue.put({"phase": "completed", "exception_class": "", "model_source_line": None, "entry_point_bound": True, "entry_point_callable": True, "signature_binding": "passed", "termination": "returned", "return_type_bucket": type_bucket, "return_shape_bucket": shape_bucket})
    except BaseException as exc:
        queue.put({"phase": "infrastructure", "exception_class": type(exc).__name__, "model_source_line": None, "entry_point_bound": False, "entry_point_callable": False, "signature_binding": "not_assessed", "termination": "worker_error", "return_type_bucket": "", "return_shape_bucket": ""})


def _run_cell(source: str, problem: dict[str, Any], program_id: str) -> dict[str, Any]:
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return {"phase": "G1", "exception_class": type(exc).__name__, "model_source_line": exc.lineno, "model_source_ast_node": "", "entry_point_bound": False, "entry_point_callable": False, "signature_binding": "not_assessed", "termination": "not_run", "return_type_bucket": "", "return_shape_bucket": ""}
    inputs = list(problem["base_input"]) + list(problem["plus_input"])
    arities = {len(item) for item in inputs}
    name_bound, signature_compatible = _static_g3e(tree, problem["entry_point"], arities)
    if not name_bound or not signature_compatible:
        return {"phase": "G3e", "exception_class": "", "model_source_line": "", "model_source_ast_node": "", "entry_point_bound": name_bound, "entry_point_callable": name_bound, "signature_binding": "passed" if signature_compatible else "failed", "termination": "not_run", "return_type_bucket": "", "return_shape_bucket": ""}
    context = multiprocessing.get_context("fork")
    queue = context.Queue(maxsize=1)
    process = context.Process(target=_worker, args=(queue, source, problem["prompt"], problem["entry_point"], list(problem["base_input"]), list(problem["plus_input"]), program_id))
    process.start()
    process.join(TIMEOUT_SECONDS + 2)
    if process.is_alive():
        process.terminate()
        process.join()
        return {"phase": "G2", "exception_class": "TimeoutError", "model_source_line": "", "model_source_ast_node": "", "entry_point_bound": True, "entry_point_callable": True, "signature_binding": "passed", "termination": "timeout", "return_type_bucket": "", "return_shape_bucket": ""}
    if queue.empty():
        return {"phase": "infrastructure", "exception_class": "WorkerProcessExit", "model_source_line": "", "model_source_ast_node": "", "entry_point_bound": True, "entry_point_callable": True, "signature_binding": "passed", "termination": "worker_error", "return_type_bucket": "", "return_shape_bucket": ""}
    result = queue.get()
    line = result.get("model_source_line")
    result["model_source_line"] = "" if line is None else line
    result["model_source_ast_node"] = _ast_node_at_line(source, line)
    return result


def _validate_result_rows(rows: list[dict[str, Any]], protocol: dict[str, Any]) -> None:
    _require(len(rows) == EXPECTED_CELLS, "result row-count drift")
    _require(len({row["cell_identity_sha256"] for row in rows}) == EXPECTED_CELLS, "duplicate result identity")
    _require(set(RESULT_FIELDS) == set(protocol["allowed_result_fields"]), "allowlist/schema drift")
    allowed_phases = {"infrastructure", "G1", "G3e", "G2", "G2_module", "G2_base", "G2_plus", "completed"}
    for row in rows:
        _require(set(row) == set(RESULT_FIELDS), "unknown diagnostic result field")
        _require(row["phase"] in allowed_phases, "unknown phase")
        for value in row.values():
            _require("\n" not in str(value) and "\r" not in str(value), "multiline diagnostic value rejected")


def run(manifest_path: Path, manifest_sha256: str, output_dir: Path, parallel: int, execute: bool) -> None:
    _require(execute, "explicit --execute-frozen-diagnostics flag required")
    _require(os.name != "nt" and not sys.platform.startswith("win"), "diagnostics must run inside WSL/Linux")
    manifest, protocol, ledger = _validate_frozen_inputs(manifest_path, manifest_sha256, output_dir, parallel)
    _require(importlib.metadata.version("evalplus") == EXPECTED_EVALPLUS_VERSION, "EvalPlus dataset-loader package version drift")
    from evalplus.data import get_mbpp_plus, get_mbpp_plus_hash
    _require(get_mbpp_plus_hash(version=EXPECTED_DATASET_VERSION) == EXPECTED_DATASET_HASH, "MBPP+ dataset hash drift")
    problems = get_mbpp_plus(version=EXPECTED_DATASET_VERSION)
    task_by_hash = {_task_identity(task_id): problem for task_id, problem in problems.items()}
    _require(len(task_by_hash) == len(problems), "task identity hash collision")
    sources = _load_selected_sources(REPO_ROOT, {row["program_id"] for row in ledger})
    results: list[dict[str, Any]] = []
    for row in ledger:
        source = sources[row["program_id"]]
        _require(_sha(source.encode("utf-8")) == row["evaluation_source_sha256"], "source hash drift")
        problem = task_by_hash.get(row["task_identity_sha256"])
        _require(problem is not None, "frozen task identity missing from official dataset")
        observed = _run_cell(source, problem, row["program_id"])
        results.append({
            "cell_identity_sha256": row["cell_identity_sha256"],
            "program_id": row["program_id"],
            "task_identity_sha256": row["task_identity_sha256"],
            "evaluation_source_sha256": row["evaluation_source_sha256"],
            "evaluator_hash": row["evaluator_hash"],
            "protocol_sha256": row["protocol_sha256"],
            **observed,
        })
    _validate_result_rows(results, protocol)
    results_bytes = _csv_bytes(results)
    receipt = {
        "status": "coarse_diagnostics_complete_pending_new_classification_revision",
        "cells": EXPECTED_CELLS,
        "results_sha256": _sha(results_bytes),
        "source_manifest_sha256": manifest_sha256,
        "diagnostics_protocol_sha256": manifest["diagnostics_protocol_sha256"],
        "evalplus_correctness_executions": 0,
        "model_calls": 0,
        "healer_runtime_input": False,
        "hidden_input_expected_actual_message_traceback_saved": False,
        "retry_resume_overwrite": False,
    }
    receipt_bytes = (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode("utf-8")
    output_dir.mkdir(parents=True)
    (output_dir / "coarse_diagnostics.csv").write_bytes(results_bytes)
    (output_dir / "execution_manifest.json").write_bytes(receipt_bytes)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--parallel", type=int, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--execute-frozen-diagnostics", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        run(args.manifest, args.manifest_sha256, args.output_dir, args.parallel, args.execute_frozen_diagnostics)
    except (DiagnosticRunnerError, ImportError, KeyError, OSError, ValueError) as exc:
        print(type(exc).__name__, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
