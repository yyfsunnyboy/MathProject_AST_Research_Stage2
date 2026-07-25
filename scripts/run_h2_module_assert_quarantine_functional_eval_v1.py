#!/usr/bin/env python3
"""Run the preregistered 71-cell H2 Post-H2 EvalPlus evaluation once."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import io
import json
import os
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_governance/"
    "h2_module_assert_quarantine_functional_evaluation_v1"
)
PREREG_PATH = REPO_ROOT / OUTPUT_RELATIVE / "preregistration.json"
INPUT_PATH = REPO_ROOT / OUTPUT_RELATIVE / "post_h2_eval_input.jsonl"
RUN_OUTPUT = REPO_ROOT / OUTPUT_RELATIVE / "manual_post_h2_evalplus_run_001"
EXPECTED_EVALPLUS_VERSION = "0.3.1"
EXPECTED_DATASET_VERSION = "v0.2.0"
EXPECTED_DATASET_HASH = "ee43ecabebf20deef4bb776a405ac5b1"
ENGINE = "evalplus_0.3.1_check_correctness_subset"
RESULT_FIELDS = (
    "evaluation_order",
    "source_record_id",
    "cohort",
    "program_id",
    "task_id",
    "seed",
    "entry_point",
    "post_h2_source_sha256",
    "base_status",
    "plus_status",
    "strict_status",
    "base_detail_count",
    "base_detail_pass_count",
    "plus_detail_count",
    "plus_detail_pass_count",
    "blocker_removed_execution_evidence",
    "evaluator_version",
    "evaluator_engine",
    "parallel",
)


class FunctionalEvaluationError(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise FunctionalEvaluationError(message)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _validate_preregistration(
    prereg_path: Path, prereg_sha256: str, parallel: int
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    _require(prereg_path.resolve() == PREREG_PATH.resolve(), "unexpected prereg path")
    _require(parallel == 1, "parallel must equal 1")
    prereg_bytes = prereg_path.read_bytes()
    _require(_sha(prereg_bytes) == prereg_sha256, "preregistration SHA mismatch")
    prereg = json.loads(prereg_bytes)
    _require(prereg["status"] == "preregistered_not_executed", "prereg status drift")
    _require(prereg["scope"] == "Stage2_MBPP+_only", "scope drift")
    _require(prereg["rule"]["rule_id"] == "module_assert_entrypoint_selftest_quarantine_v0", "rule ID drift")
    _require(prereg["rule"]["sha256"] == "dbd96fc3c1228f74c784e2444350102de121d4e202dcb0075aad214090bbfa18", "rule SHA drift")
    _require(prereg["counts"] == {"roster": 91, "transformed_to_execute": 71, "abstained_identity_only": 20}, "preregistered counts drift")
    _require(prereg["execution"]["parallel"] == 1, "preregistered parallel drift")
    _require(prereg["execution"]["retry_resume_overwrite"] is False, "retry policy drift")
    input_bytes = INPUT_PATH.read_bytes()
    _require(_sha(input_bytes) == prereg["frozen_files"]["post_h2_eval_input.jsonl"], "input SHA drift")
    rows = _read_jsonl(INPUT_PATH)
    _require(len(rows) == 71, "evaluation input is not 71 cells")
    _require(len({row["source_record_id"] for row in rows}) == 71, "duplicate evaluation identity")
    for row in rows:
        source = row.get("completion")
        _require(isinstance(source, str) and bool(source), "empty Post-H2 source")
        _require(_sha(source.encode("utf-8")) == row["post_h2_source_sha256"], "Post-H2 source SHA drift")
        _require(row["transformed"] is True, "non-transformed cell in execution input")
    return prereg, rows


def evaluate(
    prereg_path: Path,
    prereg_sha256: str,
    parallel: int,
    output_dir: Path,
) -> None:
    _require(os.name != "nt" and not sys.platform.startswith("win"), "formal evaluation requires WSL/Linux")
    _require(output_dir.resolve() == RUN_OUTPUT.resolve(), "unexpected output directory")
    _require(not output_dir.exists(), "output exists; retry/resume/overwrite forbidden")
    prereg, rows = _validate_preregistration(prereg_path, prereg_sha256, parallel)
    _require(importlib.metadata.version("evalplus") == EXPECTED_EVALPLUS_VERSION, "EvalPlus version drift")

    from evalplus.data import get_mbpp_plus, get_mbpp_plus_hash
    from evalplus.eval import PASS
    from evalplus.eval._special_oracle import MBPP_OUTPUT_NOT_NONE_TASKS
    from evalplus.evaluate import check_correctness, get_groundtruth

    problems_all = get_mbpp_plus(version=EXPECTED_DATASET_VERSION)
    dataset_hash = get_mbpp_plus_hash(version=EXPECTED_DATASET_VERSION)
    _require(dataset_hash == EXPECTED_DATASET_HASH, "MBPP+ dataset hash drift")
    task_ids = sorted({row["task_id"] for row in rows})
    _require(all(task_id in problems_all for task_id in task_ids), "task absent from MBPP+")
    problems = {task_id: problems_all[task_id] for task_id in task_ids}
    subset_hash = dataset_hash + "-" + _sha("\n".join(task_ids).encode("utf-8"))[:16]
    groundtruth = get_groundtruth(problems, subset_hash, MBPP_OUTPUT_NOT_NONE_TASKS)

    results: list[dict[str, Any]] = []
    for row in rows:
        problem = problems[row["task_id"]]
        _require(problem["entry_point"] == row["entry_point"], "entry point drift")
        result = check_correctness(
            "mbpp",
            int(row["evaluation_order"]),
            problem,
            problem["prompt"] + row["completion"],
            groundtruth[row["task_id"]],
            False,
            True,
            row["source_record_id"],
        )
        base_status, base_details = result["base"]
        plus_status, plus_details = result["plus"]
        strict_status = "pass" if base_status == plus_status == PASS else "fail"
        blocker_evidence = (
            base_status == PASS
            or plus_status == PASS
            or len(base_details) > 0
            or len(plus_details) > 0
        )
        results.append(
            {
                "evaluation_order": row["evaluation_order"],
                "source_record_id": row["source_record_id"],
                "cohort": row["cohort"],
                "program_id": row["program_id"],
                "task_id": row["task_id"],
                "seed": row["seed"],
                "entry_point": row["entry_point"],
                "post_h2_source_sha256": row["post_h2_source_sha256"],
                "base_status": base_status,
                "plus_status": plus_status,
                "strict_status": strict_status,
                "base_detail_count": len(base_details),
                "base_detail_pass_count": sum(value is True for value in base_details),
                "plus_detail_count": len(plus_details),
                "plus_detail_pass_count": sum(value is True for value in plus_details),
                "blocker_removed_execution_evidence": str(blocker_evidence).lower(),
                "evaluator_version": EXPECTED_EVALPLUS_VERSION,
                "evaluator_engine": ENGINE,
                "parallel": 1,
            }
        )
    _require(len(results) == 71, "result count drift")
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=RESULT_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(results)
    result_bytes = stream.getvalue().encode("utf-8")
    execution = {
        "status": "post_h2_evalplus_complete_pending_finalization",
        "scope": "Stage2_MBPP+_only",
        "preregistration_sha256": prereg_sha256,
        "post_h2_eval_input_sha256": prereg["frozen_files"]["post_h2_eval_input.jsonl"],
        "evaluated_cells": 71,
        "abstained_cells_executed": 0,
        "parallel": 1,
        "evalplus_version": EXPECTED_EVALPLUS_VERSION,
        "dataset_version": EXPECTED_DATASET_VERSION,
        "dataset_hash": EXPECTED_DATASET_HASH,
        "evaluator_engine": ENGINE,
        "results_sha256": _sha(result_bytes),
        "model_calls": 0,
        "candidate_generations": 0,
        "candidate_executions": 71,
        "retry_resume_selective_acceptance_overwrite": False,
        "guard_or_rule_modified": False,
    }
    output_dir.mkdir(parents=True)
    (output_dir / "post_h2_evalplus_results.csv").write_bytes(result_bytes)
    (output_dir / "execution_record.json").write_text(
        json.dumps(execution, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preregistration", type=Path, required=True)
    parser.add_argument("--preregistration-sha256", required=True)
    parser.add_argument("--parallel", type=int, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    evaluate(
        args.preregistration,
        args.preregistration_sha256,
        args.parallel,
        args.output_dir,
    )
    print('{"evaluated_cells":71,"status":"post_h2_evalplus_complete"}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
