#!/usr/bin/env python3
"""Run the frozen 186 evaluable H0 cells with official EvalPlus in WSL.

All 14 extraction-ambiguous cells remain in the 200-cell ITT denominator and
are intentionally not assigned code candidates. Cell 5 is explicitly among
them. There is no generation, Healer, H1, retry, resume, selective acceptance,
or overwrite path.
"""

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
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import prepare_candidate_b_4b_failure_supply_analysis_v1 as prepared  # noqa: E402

EXPECTED_EVALPLUS_VERSION = "0.3.1"
EXPECTED_DATASET_VERSION = "v0.2.0"
EXPECTED_DATASET_HASH = "ee43ecabebf20deef4bb776a405ac5b1"
ENGINE = "evalplus_0.3.1_check_correctness_subset"
RESULT_FIELDS = (
    "cell_index", "program_id", "cell_identity", "run_id", "task_id", "seed",
    "condition_id", "generation_id", "entry_point", "evaluation_source_sha256",
    "base_status", "plus_status", "aggregate_status", "evaluator_version",
    "evaluator_engine", "parallel",
)


class EvaluationError(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise EvaluationError(message)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_and_validate(manifest_path: Path, manifest_sha256: str, parallel: int) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    expected = (REPO_ROOT / prepared.OUTPUT_RELATIVE / "frozen_input_manifest.json").resolve()
    _require(manifest_path.resolve() == expected, "only the frozen 4B analysis manifest is accepted")
    _require(parallel == 1, "--parallel must equal 1")
    manifest_bytes = manifest_path.read_bytes()
    _require(_sha(manifest_bytes) == manifest_sha256, "frozen input manifest SHA argument mismatch")
    manifest = json.loads(manifest_bytes)
    _require(manifest["status"] == "frozen_inputs_ready_for_h0_evalplus", "input manifest status drift")
    _require(manifest["scope"] == "Stage2_MBPP+_only", "scope contamination")
    _require(manifest["counts"]["cells"] == 200 and manifest["counts"]["h0_evalplus"] == 186, "input counts drift")
    _require(manifest["cell5_policy"] == "extraction_ambiguous_no_candidate_selected_itt_retained", "Cell 5 policy drift")
    for relative, digest in manifest["source_sha256"].items():
        path = REPO_ROOT / relative
        _require(path.is_file() and _sha(path.read_bytes()) == digest, f"source hash drift: {relative}")
    for name, digest in manifest["prepared_output_sha256"].items():
        path = manifest_path.parent / name
        _require(path.is_file() and _sha(path.read_bytes()) == digest, f"prepared output hash drift: {name}")
    input_path = manifest_path.parent / "h0_evalplus_input.jsonl"
    rows = [json.loads(line) for line in input_path.read_text(encoding="utf-8").splitlines() if line]
    _require(len(rows) == 186, "H0 EvalPlus input count is not 186")
    _require(len({row["cell_index"] for row in rows}) == 186, "duplicate EvalPlus cell index")
    expected_eval_cells = set(range(1, 201)) - set(manifest["fail_closed_ambiguous_cells"])
    _require({row["cell_index"] for row in rows} == expected_eval_cells, "EvalPlus roster differs from fail-closed extraction roster")
    _require(5 in manifest["fail_closed_ambiguous_cells"], "Cell 5 is not fail-closed")
    for row in rows:
        completion = row.get("completion")
        _require(isinstance(completion, str) and bool(completion), "empty EvalPlus completion")
        _require(_sha(completion.encode("utf-8")) == row["evaluation_source_sha256"], "completion SHA drift")
        _require(row["evaluation_disposition"] == "requires_h0_evalplus", "evaluation disposition drift")
    return manifest, rows


def evaluate(manifest_path: Path, manifest_sha256: str, parallel: int, output_dir: Path) -> None:
    _require(os.name != "nt" and not sys.platform.startswith("win"), "formal evaluation must run in WSL/Linux")
    expected_output = (REPO_ROOT / prepared.OUTPUT_RELATIVE / "manual_h0_evalplus_run_001").resolve()
    _require(output_dir.resolve() == expected_output, "only the frozen output directory is accepted")
    _require(not output_dir.exists(), "output exists; retry/resume/overwrite forbidden")
    manifest, rows = _load_and_validate(manifest_path, manifest_sha256, parallel)
    _require(importlib.metadata.version("evalplus") == EXPECTED_EVALPLUS_VERSION, "EvalPlus version drift")

    from evalplus.data import get_mbpp_plus, get_mbpp_plus_hash
    from evalplus.eval import PASS
    from evalplus.eval._special_oracle import MBPP_OUTPUT_NOT_NONE_TASKS
    from evalplus.evaluate import check_correctness, get_groundtruth

    all_problems = get_mbpp_plus(version=EXPECTED_DATASET_VERSION)
    dataset_hash = get_mbpp_plus_hash(version=EXPECTED_DATASET_VERSION)
    _require(dataset_hash == EXPECTED_DATASET_HASH, "official MBPP+ dataset hash drift")
    task_ids = sorted({row["task_id"] for row in rows})
    _require(all(task_id in all_problems for task_id in task_ids), "task absent from official MBPP+")
    problems = {task_id: all_problems[task_id] for task_id in task_ids}
    subset_hash = dataset_hash + "-" + _sha("\n".join(task_ids).encode("utf-8"))[:16]
    groundtruth = get_groundtruth(problems, subset_hash, MBPP_OUTPUT_NOT_NONE_TASKS)

    results: list[dict[str, Any]] = []
    for row in rows:
        task_id = row["task_id"]
        problem = problems[task_id]
        solution = problem["prompt"] + row["completion"]
        result = check_correctness(*(
            "mbpp", int(row["sample_index"]), problem, solution,
            groundtruth[task_id], False, True, row["program_id"],
        ))
        base_status = result["base"][0]
        plus_status = result["plus"][0]
        aggregate = "pass" if base_status == plus_status == PASS else "fail"
        results.append({
            "cell_index": row["cell_index"],
            "program_id": row["program_id"],
            "cell_identity": row["cell_identity"],
            "run_id": row["run_id"],
            "task_id": task_id,
            "seed": row["seed"],
            "condition_id": row["condition_id"],
            "generation_id": row["generation_id"],
            "entry_point": problem["entry_point"],
            "evaluation_source_sha256": row["evaluation_source_sha256"],
            "base_status": base_status,
            "plus_status": plus_status,
            "aggregate_status": aggregate,
            "evaluator_version": EXPECTED_EVALPLUS_VERSION,
            "evaluator_engine": ENGINE,
            "parallel": 1,
        })
    _require(len(results) == 186, "result count drift")

    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=RESULT_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(results)
    result_bytes = buffer.getvalue().encode("utf-8")
    receipt = {
        "status": "h0_evalplus_complete",
        "scope": "Stage2_MBPP+_only",
        "frozen_input_manifest_sha256": manifest_sha256,
        "itt_denominator": 200,
        "evaluated_cells": 186,
        "unevaluated_extraction_ambiguous_cells": manifest["fail_closed_ambiguous_cells"],
        "parallel": 1,
        "evalplus_version": EXPECTED_EVALPLUS_VERSION,
        "dataset_version": EXPECTED_DATASET_VERSION,
        "dataset_hash": EXPECTED_DATASET_HASH,
        "results_sha256": _sha(result_bytes),
        "model_calls": 0,
        "healer_applied": False,
        "h1_created": False,
        "retry_resume_selective_acceptance_overwrite": False,
        "source_manifest_status": manifest["status"],
    }
    output_dir.mkdir(parents=True)
    (output_dir / "h0_evalplus_results.csv").write_bytes(result_bytes)
    (output_dir / "execution_manifest.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--parallel", type=int, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    evaluate(args.manifest, args.manifest_sha256, args.parallel, args.output_dir)
    print(json.dumps({"status": "h0_evalplus_complete", "evaluated_cells": 186}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
