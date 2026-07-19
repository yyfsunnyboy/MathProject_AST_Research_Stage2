#!/usr/bin/env python3
"""Evaluate frozen Candidate B r003 H0 + changed-H1 cells with EvalPlus.

There is intentionally no generation, retry, resume, selective acceptance, or
overwrite path.  Pass/fail conclusions and paired analysis are out of scope.
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
from typing import Any, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import prepare_mbpp_candidate_b_r003_h0_h1_evalplus as prepared  # noqa: E402


FROZEN_MANIFEST_RELATIVE = prepared.OUTPUT_RELATIVE / "manifest.json"
FROZEN_OUTPUT_RELATIVE = prepared.OUTPUT_RELATIVE / "manual_evalplus_run_001"
FROZEN_MANIFEST_SHA256 = "6a84a328307f3ce98a49933008aa18da481aae52920238b9204dcf47b1280606"
EXPECTED_EVALPLUS_CELLS = prepared.EXPECTED_EVALPLUS_CELLS
EXPECTED_CHANGED_H1 = prepared.EXPECTED_CHANGED_H1
EXPECTED_UNCHANGED_H1 = prepared.EXPECTED_UNCHANGED_H1
EXPECTED_HEALER_SHA256 = prepared.EXPECTED_HEALER_SHA256
EXPECTED_PIPELINE_SHA256 = prepared.EXPECTED_PIPELINE_SHA256
EXPECTED_CANDIDATE_ID = prepared.EXPECTED_CANDIDATE_ID
EXPECTED_HEALER_RULE = prepared.EXPECTED_HEALER_RULE
EXPECTED_DATASET_VERSION = prepared.EXPECTED_DATASET_VERSION
EXPECTED_DATASET_HASH = prepared.EXPECTED_DATASET_HASH
EXPECTED_EVALPLUS_VERSION = prepared.EXPECTED_EVALUATOR_VERSION
EXPECTED_EVALUATOR_ENGINE = prepared.EXPECTED_EVALUATOR_ENGINE

RESULT_FIELDS = (
    "program_id", "evaluation_account_id", "healer_account", "run_id",
    "task_id", "seed", "generation_id", "pipeline_normalized_source_sha256",
    "evaluation_source_sha256", "base_status", "plus_status", "evalplus_pass",
    "evaluator_version", "evaluator_engine", "evaluation_disposition",
)


class EvaluationDriverError(RuntimeError):
    """Raised on any frozen input or execution contract violation."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise EvaluationDriverError(message)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def validate_frozen_inputs(
    *, manifest_path: Path, manifest_sha256: str, parallel: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    expected_path = (REPO_ROOT / FROZEN_MANIFEST_RELATIVE).resolve()
    _require(manifest_path.resolve() == expected_path, "only the frozen Candidate B EvalPlus manifest path is accepted")
    _require(manifest_sha256 == FROZEN_MANIFEST_SHA256, "manifest SHA-256 argument is not the frozen hash")
    _require(parallel == 1, "--parallel must equal 1")
    manifest_bytes = manifest_path.read_bytes()
    _require(_sha256_bytes(manifest_bytes) == FROZEN_MANIFEST_SHA256, "frozen manifest bytes drift")
    manifest = json.loads(manifest_bytes)
    _require(manifest["status"] == "prepared_not_executed", "manifest status drift")
    _require(manifest["manifest_version"] == "candidate_b_r003_h0_h1_evalplus_v1", "manifest version drift")
    _require(manifest["run_id"] == prepared.RUN_ID, "run ID drift")
    _require(manifest["candidate_id"] == EXPECTED_CANDIDATE_ID, "other Healer candidate rejected")
    _require(manifest["rule_order"] == [EXPECTED_HEALER_RULE], "other Healer rule rejected")
    _require(manifest["healer_sha256"] == EXPECTED_HEALER_SHA256, "Healer hash drift")
    _require(manifest["pipeline_sha256"] == EXPECTED_PIPELINE_SHA256, "Pipeline hash drift")
    _require(manifest["dataset_version"] == EXPECTED_DATASET_VERSION, "dataset version drift")
    _require(manifest["dataset_hash"] == EXPECTED_DATASET_HASH, "dataset hash drift")
    _require(manifest["evaluator_version"] == EXPECTED_EVALPLUS_VERSION, "evaluator version drift")
    expected_counts = {
        "tasks": 60,
        "task_seed_identities": 300,
        "candidate_b_programs": 300,
        "candidate_b_accounts": 600,
        "candidate_b_h0": 300,
        "candidate_b_h1": 300,
        "h1_changed": EXPECTED_CHANGED_H1,
        "h1_unchanged": EXPECTED_UNCHANGED_H1,
        "evalplus_cells": EXPECTED_EVALPLUS_CELLS,
        "factorial_programs": 600,
        "factorial_accounts": 1200,
    }
    _require(manifest["counts"] == expected_counts, "manifest count drift")
    _require(manifest["model_calls"] == manifest["evalplus_executions"] == manifest["new_generation_runs"] == 0, "preparation execution count drift")
    _require(manifest["evalplus_output_directory_created"] is False, "EvalPlus output directory must start absent")
    _require(manifest["r001_r002_used_as_result_source"] is False, "incident contamination flag drift")

    for relative, digest in manifest["source_sha256"].items():
        _require("mbpp_b28" not in relative, "interrupted b28 artifact outside scope")
        source = REPO_ROOT / relative
        _require(source.is_file(), f"frozen source missing: {relative}")
        _require(_sha256_bytes(source.read_bytes()) == digest, f"frozen source hash drift: {relative}")

    rebuilt = prepared.build_outputs(REPO_ROOT)
    _require(rebuilt["manifest.json"] == manifest_bytes, "deterministic manifest rebuild drift")
    lock = manifest["output_sha256_excluding_manifest_and_operator_guide"]
    expected_lock = set(rebuilt) - {"manifest.json", "operator_guide_zh.md"}
    _require(set(lock) == expected_lock, "frozen output lock set drift")
    root = manifest_path.parent
    for name, digest in lock.items():
        path = root / name
        _require(path.is_file(), f"frozen asset missing: {name}")
        _require(_sha256_bytes(path.read_bytes()) == digest, f"frozen asset hash drift: {name}")
        _require(path.read_bytes() == rebuilt[name], f"frozen asset deterministic bytes drift: {name}")

    accounts = _read_csv(root / "candidate_b_h0_h1_accounts.csv")
    raw = _read_csv(root / "candidate_b_raw_generation_ledger.csv")
    eval_rows = _read_jsonl(root / "evalplus_input.jsonl")
    reuse = _read_csv(root / "candidate_b_h1_unchanged_h0_reuse_ledger.csv")
    _require(len(accounts) == 600, "account row count must be 600")
    _require(len(raw) == 300, "raw ledger must contain 300 rows")
    _require(len(eval_rows) == EXPECTED_EVALPLUS_CELLS, "EvalPlus input count drift")
    _require(len(reuse) == EXPECTED_UNCHANGED_H1, "reuse ledger count drift")
    _require(len({row["evaluation_account_id"] for row in accounts}) == 600, "duplicate evaluation account identity")
    _require(len({row["program_id"] for row in accounts}) == 300, "program identity count drift")
    _require(len({row["generation_id"] for row in raw}) == 300, "duplicate raw generation identity")
    _require(all(row["status"] == "complete_single_attempt" for row in raw), "raw status drift")
    _require(all(row["retry_count"] == "0" and row["resume"] == "False" for row in raw), "retry/resume drift")
    _require(sum(row["healer_account"] == "H0" for row in eval_rows) == 300, "H0 eval count drift")
    _require(sum(row["healer_account"] == "H1" for row in eval_rows) == EXPECTED_CHANGED_H1, "changed H1 eval count drift")
    _require(len({row["evaluation_account_id"] for row in eval_rows}) == EXPECTED_EVALPLUS_CELLS, "duplicate eval account identity")
    account_by_id = {row["evaluation_account_id"]: row for row in accounts}
    for row in eval_rows:
        account = account_by_id[row["evaluation_account_id"]]
        _require(row["program_id"] == account["program_id"], "eval/account program mismatch")
        _require(row["generation_id"] == account["generation_id"], "eval/account generation mismatch")
        _require(row["healer_candidate_id"] == EXPECTED_CANDIDATE_ID, "unexpected Healer candidate on eval row")
        completion = row.get("completion")
        _require(isinstance(completion, str), "eval completion missing")
        if completion:
            _require(_sha256_bytes(completion.encode("utf-8")) == row["evaluation_source_sha256"], "eval completion hash drift")
            _require(row["evaluation_source_sha256"] == account["evaluation_source_sha256"], "eval/account source mismatch")
        else:
            _require(account["evaluation_source_sha256"] == "", "empty completion with non-empty account source")
    _require(all(row["reuse_eligible_after_h0_evalplus"] == "true" and row["source_sha256_exact_match"] == "true" for row in reuse), "reuse eligibility drift")
    _require(not (REPO_ROOT / prepared.OUTPUT_RELATIVE / "manual_evalplus_run_001").exists(), "EvalPlus output directory must remain absent before execution")
    return manifest, eval_rows


def _official_check(args: tuple[Any, ...]) -> dict[str, Any]:
    from evalplus.evaluate import check_correctness

    return check_correctness(*args)


def evaluate(
    *, manifest_path: Path, manifest_sha256: str, parallel: int, output_dir: Path,
) -> None:
    if os.name == "nt" or sys.platform.startswith("win"):
        raise EvaluationDriverError("formal evaluation must run inside WSL/Linux")
    manifest, eval_rows = validate_frozen_inputs(
        manifest_path=manifest_path, manifest_sha256=manifest_sha256, parallel=parallel,
    )
    _require(output_dir.resolve() == (REPO_ROOT / FROZEN_OUTPUT_RELATIVE).resolve(), "only the frozen output path is accepted")
    _require(not output_dir.exists(), "output directory exists; retry/resume/overwrite forbidden")
    _require(importlib.metadata.version("evalplus") == EXPECTED_EVALPLUS_VERSION, "EvalPlus version drift")

    from evalplus.data import get_mbpp_plus, get_mbpp_plus_hash
    from evalplus.eval import PASS
    from evalplus.eval._special_oracle import MBPP_OUTPUT_NOT_NONE_TASKS
    from evalplus.evaluate import get_groundtruth

    all_problems = get_mbpp_plus(version=EXPECTED_DATASET_VERSION)
    dataset_hash = get_mbpp_plus_hash(version=EXPECTED_DATASET_VERSION)
    _require(dataset_hash == EXPECTED_DATASET_HASH, "official MBPP+ dataset hash drift")
    task_ids = sorted({row["task_id"] for row in eval_rows})
    _require(all(task_id in all_problems for task_id in task_ids), "eval task missing from official dataset")
    problems = {task_id: all_problems[task_id] for task_id in task_ids}
    subset_hash = dataset_hash + "-" + _sha256_bytes("\n".join(task_ids).encode("utf-8"))[:16]
    expected_output = get_groundtruth(problems, subset_hash, MBPP_OUTPUT_NOT_NONE_TASKS)

    result_rows: list[dict[str, Any]] = []
    for row in eval_rows:
        task_id = row["task_id"]
        solution = problems[task_id]["prompt"] + row["completion"]
        result = _official_check((
            "mbpp", int(row["sample_index"]), problems[task_id], solution,
            expected_output[task_id], False, True, row["evaluation_account_id"],
        ))
        base_status = result["base"][0]
        plus_status = result["plus"][0]
        passed = base_status == plus_status == PASS
        result_rows.append({
            "program_id": row["program_id"],
            "evaluation_account_id": row["evaluation_account_id"],
            "healer_account": row["healer_account"],
            "run_id": row["run_id"],
            "task_id": task_id,
            "seed": row["seed"],
            "generation_id": row["generation_id"],
            "pipeline_normalized_source_sha256": row["pipeline_normalized_source_sha256"],
            "evaluation_source_sha256": row["evaluation_source_sha256"],
            "base_status": base_status,
            "plus_status": plus_status,
            "evalplus_pass": str(passed).lower(),
            "evaluator_version": EXPECTED_EVALPLUS_VERSION,
            "evaluator_engine": EXPECTED_EVALUATOR_ENGINE,
            "evaluation_disposition": row["evaluation_disposition"],
        })
    _require(len(result_rows) == EXPECTED_EVALPLUS_CELLS, "evaluation result count drift")

    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=RESULT_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(result_rows)
    results_bytes = buffer.getvalue().encode("utf-8")
    execution = {
        "status": "candidate_b_evalplus_complete_pending_paired_analysis",
        "frozen_manifest_sha256": FROZEN_MANIFEST_SHA256,
        "evalplus_cells_evaluated": EXPECTED_EVALPLUS_CELLS,
        "candidate_b_h0_cells_evaluated": 300,
        "candidate_b_h1_changed_cells_evaluated": EXPECTED_CHANGED_H1,
        "candidate_b_h1_unchanged_not_re_evaluated": EXPECTED_UNCHANGED_H1,
        "parallel": 1,
        "evalplus_version": EXPECTED_EVALPLUS_VERSION,
        "dataset_version": EXPECTED_DATASET_VERSION,
        "dataset_hash": EXPECTED_DATASET_HASH,
        "results_sha256": _sha256_bytes(results_bytes),
        "gate_or_paired_conclusion_produced": False,
        "retry_resume_selective_acceptance_overwrite": False,
        "model_calls": 0,
        "source_manifest_status": manifest["status"],
    }
    execution_bytes = (json.dumps(execution, indent=2, sort_keys=True) + "\n").encode("utf-8")
    output_dir.mkdir(parents=True)
    with (output_dir / "evalplus_results.csv").open("xb") as handle:
        handle.write(results_bytes)
    with (output_dir / "execution_manifest.json").open("xb") as handle:
        handle.write(execution_bytes)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--parallel", type=int, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        evaluate(
            manifest_path=args.manifest,
            manifest_sha256=args.manifest_sha256,
            parallel=args.parallel,
            output_dir=args.output_dir,
        )
    except (EvaluationDriverError, ImportError, KeyError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
