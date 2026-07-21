#!/usr/bin/env python3
"""Preserve diagnostics run_001 incident and freeze r002 calibration protocol."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_RELATIVE = Path("artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v1")
START_HEAD = "36c6992626ac7201da3ad6f2c4eb10fa6f679d30"
R001_DIR = Path("artifacts/public_benchmark_governance/candidate_b_r003_v3_crosswalk_diagnostics_protocol_v1/manual_diagnostics_run_001")
R001_RESULTS = R001_DIR / "coarse_diagnostics.csv"
R001_RECEIPT = R001_DIR / "execution_manifest.json"
CROSSWALK = Path("artifacts/public_benchmark_governance/candidate_b_r003_v3_crosswalk_diagnostics_protocol_v1/candidate_b_r003_v3_derived_crosswalk.csv")
FORMAL_INPUT = Path("artifacts/public_benchmark_governance/candidate_b_r003_v3_crosswalk_diagnostics_protocol_v1/unresolved198_diagnostics_input_ledger.csv")
R001_MANIFEST = Path("artifacts/public_benchmark_governance/candidate_b_r003_v3_crosswalk_diagnostics_protocol_v1/manifest.json")
PAIRED = Path("artifacts/public_benchmark_governance/candidate_b_r003_formal_paired_analysis_v1/paired_cell_results.csv")
JOURNAL = Path("artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/mbpp_q35_9b_candidate_b_development60_replay_r003/h0_h1_accounts.jsonl")

SOURCE_HASHES = {
    R001_RESULTS: "da09a67b7fc461bac355cfae3b3eebed5c4183a12b4ecd7ea82eae6a18d8767b",
    R001_RECEIPT: "3245a980581ee0ff29c225a7b1b38dc20c782e6ffabffcb4c259a44c5368bc4c",
    CROSSWALK: "6a083a06b2cbbb5f937b6f1ae343466ae3bc97e35f93323c8902adec4f5658f7",
    FORMAL_INPUT: "d2d62a33b4f51118d0a51b41aadc9445bd64d680c3b1ef5c54117ae180272640",
    R001_MANIFEST: "3e605bec8f126900f89af757f237063db4800329dd3d99cda1218a581985b9a8",
    PAIRED: "425efbf8351cc2d1fbe2a0f22e5c6ae5e2bc29b57ee8da6a7a9adfe88752ae43",
    JOURNAL: "b1313615bf41840bc1c45c36d2b8ac9b544f37fb5bb801c104aad1657ca2c2ec",
    Path("scripts/run_candidate_b_r003_unresolved_diagnostics.py"): "259fa51919d5db7655128ba2c8fd0611d73afbf0eb111f3162541133a3643653",
    Path("agent_tools/finals_rebuild/extraction.py"): "a59da1c0a76fe24e868a51481306a5ea09d8d8977c92aab38a6c0c4dc38feccf",
    Path("agent_tools/finals_rebuild/mbpp_evaluator_blind_healer.py"): "cf4d086ca6e3af968f31b0d087ed2479e5ad38be4b7abe5d2ce5516b68000d44",
}
RESULT_FIELDS = (
    "cell_identity_sha256", "program_id", "task_identity_sha256",
    "evaluation_source_sha256", "evaluator_hash", "protocol_sha256",
    "phase", "exception_class", "model_source_line", "model_source_ast_node",
    "entry_point_bound", "entry_point_callable", "signature_binding",
    "termination", "return_type_bucket", "return_shape_bucket",
    "worker_ready", "startup_duration_bucket", "execution_duration_bucket",
    "ipc_status", "child_exit_bucket",
)


class IncidentError(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition: raise IncidentError(message)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def _csv_bytes(fields: tuple[str, ...], rows: list[dict[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader(); writer.writerows({field: row.get(field, "") for field in fields} for row in rows)
    return stream.getvalue().encode("utf-8")


def _verify_sources(repo: Path) -> None:
    for relative, digest in SOURCE_HASHES.items():
        path = repo / relative
        _require(path.is_file() and _sha(path.read_bytes()) == digest, f"source hash drift: {relative.as_posix()}")


def _incident(repo: Path) -> tuple[dict[str, Any], list[dict[str, str]]]:
    _, rows = _read_csv(repo / R001_RESULTS)
    _require(len(rows) == len({row["cell_identity_sha256"] for row in rows}) == 198, "run_001 identity drift")
    distribution = Counter((row["phase"], row["exception_class"], row["termination"]) for row in rows)
    _require(distribution == Counter({("G2", "TimeoutError", "timeout"): 196, ("infrastructure", "WorkerProcessExit", "worker_error"): 2}), "run_001 distribution drift")
    _require(all(row["entry_point_bound"] == "True" and row["entry_point_callable"] == "True" and row["signature_binding"] == "passed" for row in rows), "run_001 binding field drift")
    _require(all(not row["return_type_bucket"] and not row["return_shape_bucket"] and not row["model_source_line"] and not row["model_source_ast_node"] for row in rows), "run_001 empty evidence drift")
    worker_exit = [row for row in rows if row["exception_class"] == "WorkerProcessExit"]
    _require(len({row["task_identity_sha256"] for row in worker_exit}) == 1, "WorkerProcessExit task grouping drift")
    incident = {
        "incident_id": "candidate_b_r003_diagnostics_run001_systematic_timeout",
        "status": "preserved_protocol_failure_no_cell_classification",
        "diagnostics_executed": 198,
        "usable_classifications": 0,
        "suspected_protocol_failure": True,
        "protocol_failure_confirmed": True,
        "run001_results_sha256": SOURCE_HASHES[R001_RESULTS],
        "run001_execution_manifest_sha256": SOURCE_HASHES[R001_RECEIPT],
        "observed": {"G2_TimeoutError": 196, "infrastructure_WorkerProcessExit": 2, "binding_fields_hardcoded_on_parent_timeout_path": 196, "return_or_source_frame_present": 0},
        "root_cause": {
            "primary": "parent joins child before consuming multiprocessing.Queue payload; Python documents this ordering as deadlock-prone because child termination waits for feeder-thread pipe flush",
            "timer_conflation": "single wall timeout starts after process.start and includes worker startup, module execution, all base+plus calls, result serialization, queue flush, and process finalization",
            "dataset_loading": "EvalPlus dataset loaded once in parent; expected outputs never loaded; per-child dataset reload was not the cause",
            "start_method": "runner explicitly requested fork, so Python 3.14 POSIX forkserver default was bypassed; runtime version was not recorded and explicit fork safety was not calibrated",
            "worker_process_exit": "two no-payload child exits were collapsed without exitcode/signal; both share Mbpp/119 task identity and include non-progress loop risk, but no L4 conclusion is allowed",
            "test_gap": "prior tests never exercised production dataset initialization, ready timing, full base+plus workload, queue-before-join ordering, signal exit, or known-pass calibration",
        },
        "crosswalk_modified": False,
        "l4_l5_conclusions_produced": False,
        "healer_rule_evidence": False,
        "validation_touched": False,
    }
    return incident, rows


def _protocol(kind: str, cells: int) -> dict[str, Any]:
    return {
        "protocol_version": f"candidate_b_r003_diagnostics_r002_{kind}_v1",
        "status": "prepared_not_executed",
        "cells": cells,
        "python": "3.14.x",
        "wsl_linux_only": True,
        "multiprocessing_start_method": "explicit_fork",
        "single_threaded_parent_precondition": True,
        "dataset_initialization": "once_in_parent_before_cell_workers",
        "expected_outputs_loaded": False,
        "worker_ready_handshake": True,
        "startup_timeout_seconds": 30,
        "candidate_execution_timeout_seconds": 30,
        "candidate_timer_starts": "after_ready_received_immediately_before_go_signal",
        "ipc": "two_one_way_Pipes; receive_result_before_join; EOF/invalid-event/signal fail_closed",
        "duration_storage": "coarse_buckets_only",
        "privacy": {"save_input_expected_actual": False, "save_exception_or_assertion_message": False, "save_traceback": False, "save_stdout_stderr": False, "healer_runtime_input": False},
        "evalplus_correctness_executions": 0,
        "output_path": (OUTPUT_RELATIVE / ("manual_calibration_run_001" if kind == "calibration" else "manual_formal_diagnostics_run_001")).as_posix(),
        "retry_resume_overwrite": False,
        "formal_gate": "all 8 known-pass calibration cells must worker-ready, completed, returned, result_received, exit_0" if kind == "formal" else "calibration only; no formal 198 execution",
    }


def build_analysis(repo: Path = REPO_ROOT) -> dict[str, Any]:
    _verify_sources(repo)
    incident, run_rows = _incident(repo)
    cross_fields, cross_rows = _read_csv(repo / CROSSWALK)
    _, paired_rows = _read_csv(repo / PAIRED)
    paired = {row["program_id"]: row for row in paired_rows if row["prompt_condition"] == "Candidate_B"}
    passed = sorted((row for row in cross_rows if row["final_status"] == "PASSED" and paired[row["program_id"]]["h0_pass"] == "true"), key=lambda row: row["program_id"])
    selected: list[dict[str, str]] = []
    tasks: set[str] = set()
    for row in passed:
        if row["task_id"] in tasks: continue
        tasks.add(row["task_id"]); selected.append(row)
        if len(selected) == 8: break
    _require(len(selected) == len(tasks) == 8, "calibration cohort selection drift")
    cohort = []
    for row in selected:
        cohort.append({
            "cell_identity_sha256": _sha(json.dumps({"program_id": row["program_id"], "source": row["evaluation_source_sha256"], "role": "r002_known_pass_calibration"}, sort_keys=True, separators=(",", ":")).encode()),
            "program_id": row["program_id"],
            "task_identity_sha256": _sha(row["task_id"].encode()),
            "evaluation_source_sha256": row["evaluation_source_sha256"],
            "prompt_hash": row["prompt_hash"].removeprefix("sha256:"),
            "evaluator_hash": row["evaluator_hash"].removeprefix("sha256:"),
            "known_pass_evidence": "frozen_candidate_b_h0_evalplus_pass",
            "evidence_role": "development_calibration",
        })
    formal_fields, formal_rows = _read_csv(repo / FORMAL_INPUT)
    _require(len(formal_rows) == 198, "formal ledger drift")
    return {"incident": incident, "run_rows": run_rows, "cohort": cohort, "formal_fields": formal_fields, "formal_rows": formal_rows, "cross_fields": cross_fields}


def _root_cause_report() -> str:
    return """# Candidate B r003 diagnostics run_001 incident root-cause report

## 結論

run_001 的 196 TimeoutError 與 2 WorkerProcessExit 不可用於 L4/L5 分類；usable classifications = 0。確認的是 protocol/IPC failure，而不是 196 個 model programs 的共同 runtime failure。

## 九項調查

1. 舊 timeout 在 `process.start()` 後立刻開始，沒有 ready handshake；12 秒同時涵蓋 fork/startup、candidate module exec、全部 base+plus inputs、序列化、Queue flush 與 child finalization。
2. EvalPlus dataset 只在 parent 載入一次；child 沒有重載 dataset，也沒有建立 expected outputs。重複 dataset initialization 不是根因。
3. 舊 runner 明確使用 `get_context("fork")`，因此 Python 3.14 的 POSIX 預設 forkserver 變更沒有直接生效；但 receipt 未記錄 Python/WSL版本，且 explicit fork 未做 single-threaded/known-pass calibration。
4. parent 先 `process.join(12)`，之後才 `queue.get()`。Python 官方文件明示 child put Queue 後會等待 feeder flush，先 join、後 get 可能 deadlock。
5. 196 rows 沒有任何 worker payload；父程序在 join timeout 後 terminate，故無法區分 candidate timeout、Queue feeder/finalization block 或 startup cost。
6. worker 的 module/call/outer exception 都以同一 Queue 回傳；catch 本身存在，但 parent 的讀取順序不能保證 payload 被消費。
7. 舊 10 CPU/12 wall 秒沒有正常 worker startup 或 known-pass full-workload calibration，不能證明 timeout 大於正常成本。
8. 兩個 WorkerProcessExit 是 child 在沒有 Queue payload時先退出；舊 runner未保存 exitcode/signal。兩者同屬 Mbpp/119，source可見 non-progress風險，但事故資料不足以作 L4 結論。
9. 舊 synthetic tests只覆蓋 parser、privacy、deterministic bytes與預設不執行；未覆蓋 production dataset load、worker-ready、full inputs、Queue drain-before-join、signal exit或 known-pass calibration。

官方依據：

- https://docs.python.org/3/library/multiprocessing.html#joining-processes-that-use-queues
- https://docs.python.org/3/library/multiprocessing.html#contexts-and-start-methods

## r002 修正

r002 使用 one-way Pipe、ready/go handshake、startup與candidate timeout分離、收到result後才join、粗粒度duration buckets、exit/EOF fail-closed。先凍結8格不同task的development known-pass cohort；任一格不能正常 returned，即禁止正式198格。diagnostic結果不得成為Healer runtime input或rule evidence。
"""


def build_outputs(repo: Path = REPO_ROOT) -> dict[Path, bytes]:
    analysis = build_analysis(repo)
    cohort_fields = tuple(analysis["cohort"][0])
    calibration_protocol = _protocol("calibration", 8)
    formal_protocol = _protocol("formal", 198)
    calibration_bytes = _json_bytes(calibration_protocol); formal_bytes = _json_bytes(formal_protocol)
    outputs: dict[Path, bytes] = {
        Path("incident_ledger.json"): _json_bytes(analysis["incident"]),
        Path("run001_observed_distribution.csv"): _csv_bytes(("phase", "exception_class", "termination", "cells", "usable_for_classification"), [
            {"phase": "G2", "exception_class": "TimeoutError", "termination": "timeout", "cells": 196, "usable_for_classification": "false"},
            {"phase": "infrastructure", "exception_class": "WorkerProcessExit", "termination": "worker_error", "cells": 2, "usable_for_classification": "false"},
        ]),
        Path("root_cause_report_zh.md"): _root_cause_report().encode(),
        Path("calibration_cohort.csv"): _csv_bytes(cohort_fields, analysis["cohort"]),
        Path("formal198_input_ledger.csv"): _csv_bytes(tuple(analysis["formal_fields"]), analysis["formal_rows"]),
        Path("calibration_protocol.json"): calibration_bytes,
        Path("formal_diagnostics_protocol.json"): formal_bytes,
        Path("diagnostics_output_schema.json"): _json_bytes({"fields": list(RESULT_FIELDS), "additional_fields": False, "duration_values": ["lt_0_1s", "0_1_to_0_5s", "0_5_to_1s", "1_to_2s", "2_to_5s", "5_to_10s", "10_to_30s", "gte_30s"], "forbidden": ["input", "expected", "actual", "exception_message", "assertion_message", "traceback", "stdout", "stderr", "source"]}),
        Path("privacy_policy_zh.md"): ("# r002 diagnostics privacy policy\n\n只保存 phase、exception class、model-source line/AST node、binding、termination、return type/shape bucket、worker-ready、coarse duration、IPC/exit bucket及identity hashes。不得保存input、expected、actual、message、traceback、stdout/stderr或source。diagnostics不得成為Healer runtime input、rule trigger或rule evidence。\n").encode(),
        Path("provenance.json"): _json_bytes({"start_head": START_HEAD, "run001_preserved_in_place": True, "crosswalk_modified": False, "diagnostics_executed_this_freeze": 0, "calibration_executed": False, "formal198_executed": False, "validation_touched": False}),
        Path("execution_manifest.json"): _json_bytes({"status": "incident_preserved_r002_calibration_prepared", "diagnostics_executed": 198, "usable_classifications": 0, "suspected_protocol_failure": True, "new_diagnostic_executions": 0, "evalplus_correctness_executions": 0, "model_calls": 0, "healer_prompt_pipeline_modified": False, "validation_not_executed": True}),
    }
    ledger = [{"path": path.as_posix(), "role": "frozen_input", "sha256": digest} for path, digest in sorted(SOURCE_HASHES.items(), key=lambda item: item[0].as_posix())]
    outputs[Path("source_hash_ledger.csv")] = _csv_bytes(("path", "role", "sha256"), ledger)
    builder = Path("scripts/build_candidate_b_r003_diagnostics_r002_incident.py")
    runner = Path("scripts/run_candidate_b_r003_diagnostics_r002.py")
    tests = Path("tests/finals_rebuild/test_candidate_b_r003_diagnostics_r002_incident.py")
    for path in (builder, runner, tests): _require((repo / path).is_file(), f"missing reproducibility source: {path}")
    output_hashes = {path.as_posix(): _sha(data) for path, data in sorted(outputs.items(), key=lambda item: item[0].as_posix())}
    manifest = {
        "manifest_version": "candidate_b_r003_diagnostics_r002_v1",
        "status": "r002_calibration_prepared_formal_locked",
        "incident": {"diagnostics_executed": 198, "usable_classifications": 0, "suspected_protocol_failure": True, "crosswalk_modified": False, "l4_l5_conclusions": 0, "healer_rule_evidence": False},
        "calibration_cells": 8,
        "formal_cells_locked": 198,
        "calibration_output_directory_created": False,
        "formal_output_directory_created": False,
        "calibration_protocol_sha256": _sha(calibration_bytes),
        "formal_protocol_sha256": _sha(formal_bytes),
        "diagnostic_executions_this_freeze": 0,
        "evalplus_correctness_executions": 0,
        "model_calls": 0,
        "healer_rules_modified": False,
        "validation_not_executed": True,
        "source_sha256": {path.as_posix(): _sha((repo / path).read_bytes()) for path in (builder, runner, tests)},
        "outputs_sha256_excluding_manifest_and_operator_guide": output_hashes,
    }
    manifest_bytes = _json_bytes(manifest); outputs[Path("manifest.json")] = manifest_bytes
    manifest_sha = _sha(manifest_bytes)
    command = ("cd /mnt/c/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2 && /home/yehya/.venvs/ast_evalplus/bin/python scripts/run_candidate_b_r003_diagnostics_r002.py --mode calibration --manifest artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v1/manifest.json " + f"--manifest-sha256 {manifest_sha} " + "--output-dir artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v1/manual_calibration_run_001 --execute-r002-diagnostics")
    outputs[Path("operator_guide_zh.md")] = ("# r002 calibration operator guide\n\n本輪未執行。唯一人工 calibration 指令：\n\n```bash\n" + command + "\n```\n\n正式198格維持鎖定；不得在 calibration 8/8 正常 returned 前執行。\n").encode()
    return outputs


def write_outputs(repo: Path = REPO_ROOT) -> Path:
    directory = repo / OUTPUT_RELATIVE; directory.mkdir(parents=True, exist_ok=True)
    for relative, data in build_outputs(repo).items(): (directory / relative).write_bytes(data)
    return directory


if __name__ == "__main__":
    print(write_outputs())
