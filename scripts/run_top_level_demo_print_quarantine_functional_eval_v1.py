#!/usr/bin/env python3
"""Run the preregistered transformed-cohort EvalPlus evaluation once."""

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
    "top_level_demo_print_quarantine_development_v1"
)
PREREG_PATH = REPO_ROOT / OUTPUT_RELATIVE / "preregistration.json"
INPUT_PATH = REPO_ROOT / OUTPUT_RELATIVE / "functional_eval_input.jsonl"
RUN_OUTPUT = REPO_ROOT / OUTPUT_RELATIVE / "manual_evalplus_run_001"
EXPECTED_RULE_SHA = "a0b89828b2f3e524fd8d03a64bc0a5afe00b38b774aae47572d22c0e0a7f3ee9"
EXPECTED_H2_SHA = "dbd96fc3c1228f74c784e2444350102de121d4e202dcb0075aad214090bbfa18"
EXPECTED_EVALPLUS_VERSION = "0.3.1"
EXPECTED_DATASET_VERSION = "v0.2.0"
EXPECTED_DATASET_HASH = "ee43ecabebf20deef4bb776a405ac5b1"
ENGINE = "evalplus_0.3.1_check_correctness_subset"
RESULT_FIELDS = [
    "evaluation_order",
    "cell_id",
    "program_id",
    "task_id",
    "seed",
    "arm",
    "source_sha256",
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
]


class FunctionalEvaluationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise FunctionalEvaluationError(message)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def evaluate(
    preregistration: Path,
    preregistration_sha256: str,
    parallel: int,
    output_dir: Path,
) -> None:
    require(os.name != "nt" and not sys.platform.startswith("win"), "WSL/Linux required")
    require(preregistration.resolve() == PREREG_PATH.resolve(), "unexpected preregistration")
    require(output_dir.resolve() == RUN_OUTPUT.resolve(), "unexpected output directory")
    require(not output_dir.exists(), "output exists; retry/resume/overwrite forbidden")
    require(parallel == 1, "parallel must equal 1")
    prereg_bytes = preregistration.read_bytes()
    require(
        sha256_bytes(prereg_bytes) == preregistration_sha256,
        "preregistration SHA drift",
    )
    prereg = json.loads(prereg_bytes)
    require(prereg["status"] == "preregistered_not_executed", "status drift")
    require(prereg["rule"]["sha256"] == EXPECTED_RULE_SHA, "rule SHA drift")
    require(prereg["h2"]["sha256"] == EXPECTED_H2_SHA, "H2 SHA drift")
    require(prereg["execution"]["new_evalplus_cells"] == 50, "execution scope drift")
    require(prereg["execution"]["parallel"] == 1, "parallel prereg drift")
    require(prereg["execution"]["retry_resume_overwrite"] is False, "retry policy drift")
    input_bytes = INPUT_PATH.read_bytes()
    require(
        sha256_bytes(input_bytes) == prereg["frozen_files"]["functional_eval_input.jsonl"],
        "input SHA drift",
    )
    rows = read_jsonl(INPUT_PATH)
    require(len(rows) == 50, "input is not 50 evaluation arms")
    require(
        len({(row["cell_id"], row["arm"]) for row in rows}) == 50,
        "duplicate evaluation arm",
    )
    require(
        {row["arm"] for row in rows} == {"demo_print_only", "h2_only", "h2_plus_demo_print"},
        "unexpected arm set",
    )
    require(
        sum(row["arm"] == "demo_print_only" for row in rows) == 21
        and sum(row["arm"] == "h2_plus_demo_print" for row in rows) == 21
        and sum(row["arm"] == "h2_only" for row in rows) == 8,
        "arm counts drift",
    )
    for row in rows:
        source = row["completion"]
        require(
            sha256_bytes(source.encode("utf-8")) == row["source_sha256"],
            "source SHA drift",
        )

    require(
        importlib.metadata.version("evalplus") == EXPECTED_EVALPLUS_VERSION,
        "EvalPlus version drift",
    )
    from evalplus.data import get_mbpp_plus, get_mbpp_plus_hash
    from evalplus.eval import PASS
    from evalplus.eval._special_oracle import MBPP_OUTPUT_NOT_NONE_TASKS
    from evalplus.evaluate import check_correctness, get_groundtruth

    problems_all = get_mbpp_plus(version=EXPECTED_DATASET_VERSION)
    dataset_hash = get_mbpp_plus_hash(version=EXPECTED_DATASET_VERSION)
    require(dataset_hash == EXPECTED_DATASET_HASH, "dataset hash drift")
    task_ids = sorted({row["task_id"] for row in rows})
    require(all(task_id in problems_all for task_id in task_ids), "task missing")
    problems = {task_id: problems_all[task_id] for task_id in task_ids}
    subset_hash = dataset_hash + "-" + sha256_bytes(
        "\n".join(task_ids).encode("utf-8")
    )[:16]
    groundtruth = get_groundtruth(problems, subset_hash, MBPP_OUTPUT_NOT_NONE_TASKS)

    results: list[dict[str, Any]] = []
    for row in rows:
        problem = problems[row["task_id"]]
        require(problem["entry_point"] == row["entry_point"], "entry point drift")
        result = check_correctness(
            "mbpp",
            int(row["evaluation_order"]),
            problem,
            problem["prompt"] + row["completion"],
            groundtruth[row["task_id"]],
            False,
            True,
            f"{row['cell_id']}:{row['arm']}",
        )
        base_status, base_details = result["base"]
        plus_status, plus_details = result["plus"]
        strict = "pass" if base_status == plus_status == PASS else "fail"
        blocker_removed = (
            base_status == PASS
            or plus_status == PASS
            or bool(base_details)
            or bool(plus_details)
        )
        results.append(
            {
                "evaluation_order": row["evaluation_order"],
                "cell_id": row["cell_id"],
                "program_id": row["program_id"],
                "task_id": row["task_id"],
                "seed": row["seed"],
                "arm": row["arm"],
                "source_sha256": row["source_sha256"],
                "base_status": base_status,
                "plus_status": plus_status,
                "strict_status": strict,
                "base_detail_count": len(base_details),
                "base_detail_pass_count": sum(value is True for value in base_details),
                "plus_detail_count": len(plus_details),
                "plus_detail_pass_count": sum(value is True for value in plus_details),
                "blocker_removed_execution_evidence": str(blocker_removed).lower(),
                "evaluator_version": EXPECTED_EVALPLUS_VERSION,
                "evaluator_engine": ENGINE,
                "parallel": 1,
            }
        )
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=RESULT_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(results)
    result_bytes = stream.getvalue().encode("utf-8")
    execution = {
        "status": "minimal_evalplus_complete_pending_finalization",
        "preregistration_sha256": preregistration_sha256,
        "functional_eval_input_sha256": sha256_bytes(input_bytes),
        "evaluated_cells": 50,
        "candidate_executions": 50,
        "evalplus_executions": 50,
        "model_calls": 0,
        "candidate_generations": 0,
        "parallel": 1,
        "evalplus_version": EXPECTED_EVALPLUS_VERSION,
        "dataset_version": EXPECTED_DATASET_VERSION,
        "dataset_hash": EXPECTED_DATASET_HASH,
        "evaluator_engine": ENGINE,
        "results_sha256": sha256_bytes(result_bytes),
        "retry_resume_selective_acceptance_overwrite": False,
        "guard_or_rule_modified": False,
        "hidden_test_contents_emitted": False,
        "canonical_solution_contents_emitted": False,
    }
    output_dir.mkdir(parents=True)
    (output_dir / "evalplus_results.csv").write_bytes(result_bytes)
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
    print('{"evaluated_cells":50,"model_calls":0,"status":"complete"}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
