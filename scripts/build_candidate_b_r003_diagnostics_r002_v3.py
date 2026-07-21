#!/usr/bin/env python3
"""Materialize the deterministic r002 v3 formal-preflight repair freeze."""

from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_RELATIVE = Path("artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v3")
V2_RELATIVE = Path("artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v2")
CALIBRATION_RELATIVE = V2_RELATIVE / "manual_calibration_run_001"
START_HEAD = "fddf8bf85cfa34b11d46df5375dd9c436c1f89fc"
V2_MANIFEST_SHA256 = "1e69e02b0a434cbcaa88f899896805d803bd8dfa3b21c0d7134e1033dc89acf2"
V2_RUNNER_SHA256 = "47966c12d00d4041aa4d9f9749755bc816704c94ca6e66e1029a69efe3298d30"
CALIBRATION_RESULTS_SHA256 = "01242c67b26509a76d852d9dc934cf15239ef9ea73a83678c639c85b486cb038"
CALIBRATION_EXECUTION_MANIFEST_SHA256 = "5be126a2c0465691db3a2be690dbb8c6054f86b7154b34e6ca06de32e01dcf37"
CALIBRATION_COHORT_SHA256 = "6a688058d6f39b27baff8f045249ce62975ea213f951b7517e084da18794ef6b"
CALIBRATION_PROTOCOL_SHA256 = "d9c20ffba5ace67b00dda625ad67ca3da1a6f8db7ce882dd0c549ab11575f8ce"
FORMAL_PROTOCOL_SHA256 = "d4d0bdb8ae470d10e0746241f24efa806c66e4d089e235b25893a315765e30d9"
FORMAL_LEDGER_SHA256 = "d2d62a33b4f51118d0a51b41aadc9445bd64d680c3b1ef5c54117ae180272640"
OUTPUT_SCHEMA_SHA256 = "535faf4ac77b90af2f5d2a5b2c6567c84858844640e5e1dc8b2ce20a581e66a2"
BUILDER = Path("scripts/build_candidate_b_r003_diagnostics_r002_v3.py")
RUNNER = Path("scripts/run_candidate_b_r003_diagnostics_r002_v3.py")
V2_RUNNER = Path("scripts/run_candidate_b_r003_diagnostics_r002_v2.py")
WORKER_CORE = Path("scripts/run_candidate_b_r003_diagnostics_r002.py")
TESTS = Path("tests/finals_rebuild/test_candidate_b_r003_diagnostics_r002_v3.py")


class FreezeError(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise FreezeError(message)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _csv_bytes(fields: tuple[str, ...], rows: list[dict[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _read(repo: Path, relative: Path, expected_sha: str) -> bytes:
    path = repo / relative
    _require(path.is_file(), f"missing frozen input: {relative.as_posix()}")
    data = path.read_bytes()
    _require(_sha(data) == expected_sha, f"frozen input hash drift: {relative.as_posix()}")
    return data


def _source_section_hashes(repo: Path) -> dict[str, str]:
    source = (repo / WORKER_CORE).read_text(encoding="utf-8")
    tree = ast.parse(source)
    wanted = {
        "RESULT_FIELDS",
        "STARTUP_TIMEOUT_SECONDS",
        "EXECUTION_TIMEOUT_SECONDS",
        "_worker",
        "_run_cell",
        "_validate_result_rows",
    }
    sections: dict[str, str] = {}
    for node in tree.body:
        name = getattr(node, "name", None)
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            names = [target.id for target in targets if isinstance(target, ast.Name)]
            name = names[0] if len(names) == 1 else None
        if name in wanted:
            segment = ast.get_source_segment(source, node)
            _require(segment is not None, f"cannot extract worker-core section: {name}")
            sections[str(name)] = _sha((segment + "\n").encode("utf-8"))
    _require(set(sections) == wanted, "worker-core source section set drift")
    return dict(sorted(sections.items()))


def build_outputs(repo: Path = REPO_ROOT) -> dict[Path, bytes]:
    v2_manifest = _read(repo, V2_RELATIVE / "manifest.json", V2_MANIFEST_SHA256)
    _read(repo, V2_RUNNER, V2_RUNNER_SHA256)
    results = _read(repo, CALIBRATION_RELATIVE / "calibration_results.csv", CALIBRATION_RESULTS_SHA256)
    receipt_bytes = _read(repo, CALIBRATION_RELATIVE / "execution_manifest.json", CALIBRATION_EXECUTION_MANIFEST_SHA256)
    cohort = _read(repo, V2_RELATIVE / "calibration_cohort.csv", CALIBRATION_COHORT_SHA256)
    calibration_protocol = _read(repo, V2_RELATIVE / "calibration_protocol.json", CALIBRATION_PROTOCOL_SHA256)
    formal_protocol = _read(repo, V2_RELATIVE / "formal_diagnostics_protocol.json", FORMAL_PROTOCOL_SHA256)
    formal_ledger = _read(repo, V2_RELATIVE / "formal198_input_ledger.csv", FORMAL_LEDGER_SHA256)
    output_schema = _read(repo, V2_RELATIVE / "diagnostics_output_schema.json", OUTPUT_SCHEMA_SHA256)
    for path in (BUILDER, RUNNER, TESTS, WORKER_CORE):
        _require((repo / path).is_file(), f"missing reproducibility source: {path.as_posix()}")
    _require(not (repo / OUTPUT_RELATIVE / "manual_formal_diagnostics_run_001").exists(), "formal output unexpectedly exists")

    receipt = json.loads(receipt_bytes)
    _require(receipt["results_sha256"] == CALIBRATION_RESULTS_SHA256, "calibration receipt results hash drift")
    _require(receipt["source_manifest_sha256"] == V2_MANIFEST_SHA256, "calibration receipt source manifest drift")
    _require(receipt["formal_198_authorized"] is True and receipt["cells"] == 8, "calibration authorization drift")

    calibration_evidence = {
        "directory": CALIBRATION_RELATIVE.as_posix(),
        "results_sha256": CALIBRATION_RESULTS_SHA256,
        "execution_manifest_sha256": CALIBRATION_EXECUTION_MANIFEST_SHA256,
        "source_manifest_sha256": V2_MANIFEST_SHA256,
        "cohort_sha256": CALIBRATION_COHORT_SHA256,
        "protocol_sha256": CALIBRATION_PROTOCOL_SHA256,
        "cells": 8,
        "worker_ready": 8,
        "completed": 8,
        "returned": 8,
        "result_received": 8,
        "exit_0": 8,
        "formal_198_authorized": True,
        "recalibration_required": False,
    }
    incident = {
        "incident_type": "ZERO_EXECUTION_FORMAL_PREFLIGHT_LOGIC_INCIDENT",
        "status": "preserved_as_zero_execution_formal_preflight_incident",
        "affected_revision": V2_RELATIVE.name,
        "root_cause": (
            "v2 manifest validation unconditionally required both calibration and formal output directories to be absent, "
            "while formal mode subsequently required the calibration directory to exist"
        ),
        "observed_safe_error": {
            "stage": "output_preflight",
            "exception_type": "R002V2RunnerError",
            "message": "calibration output path already exists",
        },
        "formal_cells_executed": 0,
        "worker_processes_started": 0,
        "formal_output_created": False,
        "model_calls": 0,
        "evalplus_correctness_executions": 0,
        "v2_manifest_runner_calibration_modified": False,
        "actual_formal_run_incident": False,
    }
    state_machine = {
        "calibration": {
            "calibration_output": "must_not_exist",
            "formal_output": "must_not_exist",
        },
        "formal": {
            "calibration_output": "must_exist_and_pass_frozen_evidence_gate",
            "formal_output": "must_not_exist",
        },
        "formal_never_requires_calibration_absence": True,
        "transition_fixed": "validated_calibration -> formal_worker_loop_boundary",
    }
    worker_equivalence = {
        "worker_cell_diagnostic_modifications": 0,
        "v3_defines_worker_or_run_cell": False,
        "v3_binding": "v2_runner.execution_core._run_cell",
        "v2_runner_sha256": V2_RUNNER_SHA256,
        "worker_core_file": WORKER_CORE.as_posix(),
        "worker_core_file_sha256": _sha((repo / WORKER_CORE).read_bytes()),
        "source_section_sha256": _source_section_hashes(repo),
        "timeouts_unchanged": {"startup_seconds": 30, "candidate_execution_seconds": 30},
        "result_schema_unchanged": True,
        "data_identity_ledgers_unchanged": True,
    }
    provenance = {
        "start_head": START_HEAD,
        "v2_manifest_sha256": V2_MANIFEST_SHA256,
        "v2_runner_sha256": V2_RUNNER_SHA256,
        "v2_calibration_preserved_in_place": True,
        "v2_calibration_observed_mtime_utc": {
            "calibration_results.csv": "2026-07-21T02:28:56.8522360Z",
            "execution_manifest.json": "2026-07-21T02:28:56.8578777Z",
        },
        "calibration_reexecuted": False,
        "formal198_executed": False,
        "validation_touched": False,
    }
    execution_manifest = {
        "status": "r002_v3_formal_prepared_not_executed",
        "incident_type": incident["incident_type"],
        "diagnostic_executions": 0,
        "formal_cells_executed": 0,
        "worker_processes_started": 0,
        "formal_output_created": False,
        "model_calls": 0,
        "evalplus_correctness_executions": 0,
        "healer_executed": False,
        "validation_not_executed": True,
    }
    report = """# Candidate B r003 diagnostics v2 formal preflight incident 與 v3 freeze

## 結論

v2 calibration 為有效的 8/8 development controls，原目錄、bytes、SHA-256、mtime 與內容均保留。本事件是 `ZERO_EXECUTION_FORMAL_PREFLIGHT_LOGIC_INCIDENT`：formal 嘗試在任何 worker 啟動前，被「calibration 必須不存在」與後續「calibration 必須存在」的矛盾 preflight 阻擋；formal cells executed = 0。

v3 只修正 mode-specific state transition。formal mode 要求 v2 calibration directory 存在，並逐項驗證固定 execution-manifest hash、results hash、receipt、8-row results、cohort identities、protocol hash與v2 source-manifest hash；只要求新的 v3 formal output 不存在。worker、per-cell procedure、timeouts、result schema與198-cell identity ledger均未修改，因此不重跑 calibration。

本輪未執行 calibration、formal198、模型、EvalPlus correctness、Healer或validation。
"""
    privacy = """# r002 v3 diagnostics privacy policy

延續 v2：CLI 僅輸出安全 stage、exception type與預定義 message；不得輸出 candidate source、hidden inputs、expected/actual、exception/assertion messages或traceback。diagnostics 不得成為 Healer runtime input。
"""

    outputs: dict[Path, bytes] = {
        Path("incident_ledger.json"): _json_bytes(incident),
        Path("mode_state_machine.json"): _json_bytes(state_machine),
        Path("calibration_evidence_ledger.json"): _json_bytes(calibration_evidence),
        Path("worker_core_equivalence.json"): _json_bytes(worker_equivalence),
        Path("formal198_input_ledger.csv"): formal_ledger,
        Path("formal_diagnostics_protocol.json"): formal_protocol,
        Path("diagnostics_output_schema.json"): output_schema,
        Path("privacy_policy_zh.md"): privacy.encode("utf-8"),
        Path("incident_report_zh.md"): report.encode("utf-8"),
        Path("provenance.json"): _json_bytes(provenance),
        Path("execution_manifest.json"): _json_bytes(execution_manifest),
    }
    source_paths = (
        BUILDER,
        RUNNER,
        TESTS,
        V2_RUNNER,
        WORKER_CORE,
        V2_RELATIVE / "manifest.json",
        CALIBRATION_RELATIVE / "calibration_results.csv",
        CALIBRATION_RELATIVE / "execution_manifest.json",
        V2_RELATIVE / "calibration_cohort.csv",
        V2_RELATIVE / "calibration_protocol.json",
    )
    source_rows = [{
        "path": path.as_posix(),
        "role": "reproducibility_source" if path in (BUILDER, RUNNER, TESTS, V2_RUNNER, WORKER_CORE) else "frozen_calibration_evidence",
        "sha256": _sha((repo / path).read_bytes()),
    } for path in source_paths]
    outputs[Path("source_hash_ledger.csv")] = _csv_bytes(("path", "role", "sha256"), source_rows)
    output_hashes = {path.as_posix(): _sha(data) for path, data in sorted(outputs.items(), key=lambda item: item[0].as_posix())}
    source_hashes = {path.as_posix(): _sha((repo / path).read_bytes()) for path in (BUILDER, RUNNER, TESTS, V2_RUNNER, WORKER_CORE)}
    manifest = {
        "manifest_version": "candidate_b_r003_diagnostics_r002_v3",
        "status": "r002_v3_formal_prepared_not_executed",
        "incident_type": incident["incident_type"],
        "diagnostic_executions": 0,
        "formal_cells_locked": 198,
        "formal_output_created": False,
        "calibration_reused_not_rerun": True,
        "calibration_evidence": calibration_evidence,
        "formal_protocol_sha256": FORMAL_PROTOCOL_SHA256,
        "formal_input_ledger_sha256": FORMAL_LEDGER_SHA256,
        "worker_cell_diagnostic_modifications": 0,
        "model_calls": 0,
        "evalplus_correctness_executions": 0,
        "healer_executed": False,
        "validation_not_executed": True,
        "source_sha256": source_hashes,
        "outputs_sha256_excluding_manifest_and_operator_guide": output_hashes,
    }
    manifest_bytes = _json_bytes(manifest)
    outputs[Path("manifest.json")] = manifest_bytes
    manifest_sha = _sha(manifest_bytes)
    command = (
        "cd /mnt/c/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2 && "
        "/home/yehya/.venvs/ast_evalplus/bin/python scripts/run_candidate_b_r003_diagnostics_r002_v3.py "
        "--mode formal "
        "--manifest artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v3/manifest.json "
        f"--manifest-sha256 {manifest_sha} "
        "--output-dir artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v3/manual_formal_diagnostics_run_001 "
        f"--calibration-execution-manifest-sha256 {CALIBRATION_EXECUTION_MANIFEST_SHA256} "
        "--execute-r002-diagnostics"
    )
    guide = f"""# r002 v3 formal operator guide

本輪未執行。唯一人工 WSL formal 指令：

```bash
{command}
```

`--calibration-execution-manifest-sha256` 的值是既有 v2 calibration output `execution_manifest.json` 檔案 bytes 的固定 SHA-256。v3 會另外驗證 receipt、results、cohort、protocol及source-manifest identity；不得以其他 hash 取代。
"""
    outputs[Path("operator_guide_zh.md")] = guide.encode("utf-8")
    return outputs


def write_outputs(repo: Path = REPO_ROOT) -> Path:
    directory = repo / OUTPUT_RELATIVE
    directory.mkdir(parents=True, exist_ok=True)
    for relative, data in build_outputs(repo).items():
        (directory / relative).write_bytes(data)
    return directory


if __name__ == "__main__":
    print(write_outputs())
