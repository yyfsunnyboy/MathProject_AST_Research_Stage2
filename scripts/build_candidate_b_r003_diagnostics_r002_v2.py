#!/usr/bin/env python3
"""Materialize the deterministic r002 v2 preflight-schema repair freeze."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_RELATIVE = Path("artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v2")
V1_RELATIVE = Path("artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v1")
START_HEAD = "1f62eeaa8de013c713f5652495be22ca3e3db31a"
V1_MANIFEST_SHA256 = "701b8117b45389cad827011eee26ce34b2b861aa509b1e6754a9985234027e5e"
BUILDER = Path("scripts/build_candidate_b_r003_diagnostics_r002_v2.py")
RUNNER = Path("scripts/run_candidate_b_r003_diagnostics_r002_v2.py")
EXECUTION_CORE = Path("scripts/run_candidate_b_r003_diagnostics_r002.py")
TESTS = Path("tests/finals_rebuild/test_candidate_b_r003_diagnostics_r002_v2.py")


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


def _v1_file(repo: Path, name: str) -> bytes:
    path = repo / V1_RELATIVE / name
    _require(path.is_file(), f"missing frozen v1 artifact: {name}")
    return path.read_bytes()


def _protocol(repo: Path, kind: str) -> bytes:
    name = "calibration_protocol.json" if kind == "calibration" else "formal_diagnostics_protocol.json"
    value = json.loads(_v1_file(repo, name))
    value["protocol_version"] = f"candidate_b_r003_diagnostics_r002_{kind}_v2"
    value["preflight_source_manifest_required_field"] = {"diagnostic_executions": 0}
    value["preflight_type_contract"] = "exact integer zero; bool rejected"
    if kind == "formal":
        value["calibration_execution_manifest_sha256_semantics"] = (
            "SHA-256 of manual_calibration_run_001/execution_manifest.json file bytes"
        )
        value["calibration_source_manifest_sha256_semantics"] = (
            "separate receipt field; must equal frozen r002 v2 manifest SHA-256"
        )
        value["formal_cli_flag"] = "--calibration-execution-manifest-sha256"
    return _json_bytes(value)


def build_outputs(repo: Path = REPO_ROOT) -> dict[Path, bytes]:
    v1_manifest = _v1_file(repo, "manifest.json")
    _require(_sha(v1_manifest) == V1_MANIFEST_SHA256, "frozen v1 manifest hash drift")
    for path in (BUILDER, RUNNER, EXECUTION_CORE, TESTS):
        _require((repo / path).is_file(), f"missing reproducibility source: {path.as_posix()}")
    _require(not (repo / V1_RELATIVE / "manual_calibration_run_001").exists(), "v1 calibration output unexpectedly exists")
    _require(not (repo / OUTPUT_RELATIVE / "manual_calibration_run_001").exists(), "v2 calibration output unexpectedly exists")
    _require(not (repo / OUTPUT_RELATIVE / "manual_formal_diagnostics_run_001").exists(), "v2 formal output unexpectedly exists")

    calibration_protocol = _protocol(repo, "calibration")
    formal_protocol = _protocol(repo, "formal")
    incident = {
        "incident_type": "ZERO_EXECUTION_PREFLIGHT_SCHEMA_INCIDENT",
        "status": "preserved_as_preflight_schema_incident_not_calibration_run_incident",
        "affected_revision": V1_RELATIVE.name,
        "affected_manifest_sha256": V1_MANIFEST_SHA256,
        "root_cause": (
            "v1 runner required manifest['diagnostic_executions'] while the frozen v1 materializer emitted only "
            "diagnostic_executions_this_freeze"
        ),
        "exception_type": "KeyError",
        "exception_field": "diagnostic_executions",
        "calibration_output_directory_created": False,
        "worker_processes_started": 0,
        "calibration_cells_executed": 0,
        "diagnostic_executions": 0,
        "model_calls": 0,
        "evalplus_correctness_executions": 0,
        "actual_calibration_run_incident": False,
        "v1_assets_modified": False,
    }
    contract = {
        "revision": "candidate_b_r003_diagnostics_r002_v2",
        "required_manifest_field": "diagnostic_executions",
        "accepted_value": 0,
        "accepted_python_type": "int excluding bool",
        "missing_rejected": True,
        "bool_rejected": True,
        "other_non_integer_rejected": True,
        "nonzero_rejected": True,
        "validation_occurs_before_dataset_initialization_or_worker_start": True,
        "hash_drift_rejected": True,
    }
    sha_semantics = {
        "formal_cli_flag": "--calibration-execution-manifest-sha256",
        "flag_value": "SHA-256 of calibration output execution_manifest.json file bytes",
        "receipt_source_manifest_sha256": "SHA-256 of frozen r002 v2 source manifest bytes",
        "relationship": "distinct values with independent checks",
        "formal198_executed_this_freeze": False,
    }
    execution_manifest = {
        "status": "r002_v2_prepared_not_executed",
        "incident_type": incident["incident_type"],
        "diagnostic_executions": 0,
        "calibration_cells_executed": 0,
        "formal198_cells_executed": 0,
        "worker_processes_started": 0,
        "model_calls": 0,
        "evalplus_correctness_executions": 0,
        "healer_prompt_pipeline_modified": False,
        "validation_not_executed": True,
    }
    provenance = {
        "start_head": START_HEAD,
        "v1_manifest_sha256": V1_MANIFEST_SHA256,
        "v1_preserved_in_place": True,
        "materialized_revision": OUTPUT_RELATIVE.name,
        "zero_execution_preflight_only": True,
        "calibration_executed": False,
        "formal198_executed": False,
        "validation_touched": False,
    }
    report = """# Candidate B r003 diagnostics r002 v2 preflight schema incident

## 結論

本事件是 `ZERO_EXECUTION_PREFLIGHT_SCHEMA_INCIDENT`，不是 calibration run incident。v1 frozen manifest 缺少 runner 所要求的 `diagnostic_executions`，因此在 dataset initialization 與 worker start 之前即以 `KeyError` 結束；worker processes started = 0、calibration cells executed = 0、diagnostic executions = 0。

v1 目錄與 manifest bytes 原樣保留。v2 由 materializer 明確產生整數 `diagnostic_executions: 0`；runner 對欄位缺失、bool、其他非整數、非零與任何 frozen hash drift 均 fail-closed。

## calibration manifest SHA 語意

舊 `_calibration_all_passed()` 實際計算的是 calibration output `execution_manifest.json` **檔案 bytes 的 SHA-256**，並非 receipt 內的 `source_manifest_sha256`。v2 將參數與 formal CLI 統一命名為 `calibration_execution_manifest_sha256` / `--calibration-execution-manifest-sha256`。receipt 的 `source_manifest_sha256` 另行要求等於 frozen r002 v2 manifest SHA-256；兩種 hash 不得互換。

## 執行狀態

本輪只做靜態 materialization、zero-execution manifest preflight 與 tests，未執行 calibration 或 formal198，也未呼叫模型或 EvalPlus correctness。
"""
    privacy = """# r002 v2 diagnostics privacy policy

延續 v1：不得保存 hidden input、expected、actual、exception/assertion message、traceback、stdout/stderr 或 candidate source。CLI 只顯示安全的 stage、exception type 與預定義 message。diagnostics 結果不得成為 Healer runtime input。
"""

    outputs: dict[Path, bytes] = {
        Path("incident_ledger.json"): _json_bytes(incident),
        Path("preflight_schema_contract.json"): _json_bytes(contract),
        Path("calibration_manifest_sha256_semantics.json"): _json_bytes(sha_semantics),
        Path("calibration_cohort.csv"): _v1_file(repo, "calibration_cohort.csv"),
        Path("formal198_input_ledger.csv"): _v1_file(repo, "formal198_input_ledger.csv"),
        Path("calibration_protocol.json"): calibration_protocol,
        Path("formal_diagnostics_protocol.json"): formal_protocol,
        Path("diagnostics_output_schema.json"): _v1_file(repo, "diagnostics_output_schema.json"),
        Path("privacy_policy_zh.md"): privacy.encode("utf-8"),
        Path("incident_report_zh.md"): report.encode("utf-8"),
        Path("provenance.json"): _json_bytes(provenance),
        Path("execution_manifest.json"): _json_bytes(execution_manifest),
    }
    source_rows = []
    for path in (BUILDER, RUNNER, EXECUTION_CORE, TESTS, V1_RELATIVE / "manifest.json"):
        source_rows.append({
            "path": path.as_posix(),
            "role": "reproducibility_source" if path != V1_RELATIVE / "manifest.json" else "preserved_v1_manifest",
            "sha256": _sha((repo / path).read_bytes()),
        })
    outputs[Path("source_hash_ledger.csv")] = _csv_bytes(("path", "role", "sha256"), source_rows)

    output_hashes = {
        path.as_posix(): _sha(data)
        for path, data in sorted(outputs.items(), key=lambda item: item[0].as_posix())
    }
    source_hashes = {
        path.as_posix(): _sha((repo / path).read_bytes())
        for path in (BUILDER, RUNNER, EXECUTION_CORE, TESTS)
    }
    manifest = {
        "manifest_version": "candidate_b_r003_diagnostics_r002_v2",
        "status": "r002_v2_calibration_prepared_formal_locked",
        "incident_type": incident["incident_type"],
        "preserved_v1_manifest_sha256": V1_MANIFEST_SHA256,
        "diagnostic_executions": 0,
        "calibration_cells": 8,
        "formal_cells_locked": 198,
        "calibration_output_directory_created": False,
        "formal_output_directory_created": False,
        "calibration_protocol_sha256": _sha(calibration_protocol),
        "formal_protocol_sha256": _sha(formal_protocol),
        "evalplus_correctness_executions": 0,
        "model_calls": 0,
        "healer_rules_modified": False,
        "validation_not_executed": True,
        "source_sha256": source_hashes,
        "outputs_sha256_excluding_manifest_and_operator_guide": output_hashes,
    }
    manifest_bytes = _json_bytes(manifest)
    outputs[Path("manifest.json")] = manifest_bytes
    manifest_sha = _sha(manifest_bytes)
    command = (
        "cd /mnt/c/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2 && "
        "/home/yehya/.venvs/ast_evalplus/bin/python scripts/run_candidate_b_r003_diagnostics_r002_v2.py "
        "--mode calibration "
        "--manifest artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v2/manifest.json "
        f"--manifest-sha256 {manifest_sha} "
        "--output-dir artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v2/manual_calibration_run_001 "
        "--execute-r002-diagnostics"
    )
    guide = f"""# r002 v2 calibration operator guide

本輪未執行。唯一人工 WSL calibration 指令：

```bash
{command}
```

formal CLI 的 calibration hash 參數固定為 `--calibration-execution-manifest-sha256`，其值是 calibration output `execution_manifest.json` 檔案 bytes 的 SHA-256；receipt 內 `source_manifest_sha256` 是另一個獨立驗證欄位。正式198格維持鎖定。
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
