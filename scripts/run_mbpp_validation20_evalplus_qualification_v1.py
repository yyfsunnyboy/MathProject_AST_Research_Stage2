#!/usr/bin/env python3
"""Validation20 3600-cell EvalPlus qualification runner architecture.

Single --model per invocation. Formal evaluation is WSL/Linux only and uses
the existing EvalPlus check_correctness subset engine. This round supports
preflight only; --execute requires acknowledgement and refuses native Windows.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import os
import sys
from pathlib import Path
from typing import Any, Mapping

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import freeze_mbpp_validation20_scaffold_healer_v3 as freeze  # noqa: E402
from scripts import preflight_mbpp_validation20_generation_v1 as gen_preflight  # noqa: E402

EXECUTE_ACK = "I_ACKNOWLEDGE_VALIDATION20_EVALPLUS_FORMAL_EXECUTION"
RUNNER_IDENTITY = "mbpp_validation20_evalplus_qualification_runner_v1"


class QualificationError(RuntimeError):
    """Fail-closed qualification runner violation."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise QualificationError(message)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def derive_mutex_summary(
    *,
    raw_pass: bool | None,
    final_pass: bool | None,
    decision: str,
    repair_depth: list[str],
    invalid: bool,
    infra_failure: bool,
) -> str:
    """Mechanically derive the mutex summary using fixed priority."""
    if invalid:
        return "invalid_or_missing_candidate"
    if infra_failure:
        return "evaluator_infrastructure_failure"
    if raw_pass is False and final_pass is True:
        return "verified_rescue"
    if raw_pass is True and final_pass is False:
        return "execution_regression"
    if raw_pass is True and final_pass is True and decision == "transformed":
        return "transformed_known_pass_preserved"
    if (
        raw_pass is False
        and final_pass is False
        and any(
            tag in repair_depth
            for tag in ("partial_repair", "blocker_removed", "parse_rescue", "executable_or_diagnosable")
        )
    ):
        return "partial_repair"
    if raw_pass is True and final_pass is True:
        return "unchanged_pass"
    return "unchanged_failure"


def assert_not_existing_formal_run(output_dir: Path, repo_root: Path) -> None:
    resolved = output_dir.resolve()
    for relative in freeze.FORBIDDEN_OUTPUT_COLLISION_RELATIVES:
        _require(
            resolved != (repo_root / relative).resolve(),
            f"output directory points at existing formal run: {relative}",
        )
    # Also forbid sibling historical manual_evalplus directories.
    banned_names = {
        "manual_evalplus_run_001",
        "manual_h0_evalplus_run_001",
        "manual_post_h2_evalplus_run_001",
    }
    if output_dir.name in banned_names and "validation20" not in output_dir.as_posix():
        raise QualificationError("refusing non-validation20 historical EvalPlus directory")


def build_eval_cells_plan(model_tag: str, repo_root: Path = REPO_ROOT) -> list[dict[str, Any]]:
    cells = _read_csv(repo_root / freeze.model_dir(model_tag) / "generation_cells.csv")
    planned: list[dict[str, Any]] = []
    for cell in cells:
        for stage in freeze.STAGES:
            planned.append(
                {
                    "evaluation_account_id": _sha256_text(
                        json.dumps(
                            {
                                "generation_id": cell["generation_id"],
                                "stage": stage,
                            },
                            sort_keys=True,
                            separators=(",", ":"),
                        )
                    ),
                    "generation_id": cell["generation_id"],
                    "cell_identity": cell["cell_identity"],
                    "task_id": cell["task_id"],
                    "seed": int(cell["seed"]),
                    "prompt_condition": cell["prompt_condition"],
                    "model_tag": model_tag,
                    "stage": stage,
                }
            )
    _require(len(planned) == 1200, f"{model_tag}: expected 1200 eval cells")
    return planned


def zero_candidate_execution_preflight(
    *,
    model: str,
    repo_root: Path = REPO_ROOT,
    require_output_absent: bool = True,
) -> dict[str, Any]:
    model_tag = gen_preflight.resolve_model_tag(model)
    gen_receipt = gen_preflight.zero_model_preflight(
        model=model_tag,
        repo_root=repo_root,
        require_verified_identity=False,
        require_output_absent=False,
    )
    planned = build_eval_cells_plan(model_tag, repo_root)
    output_dir = repo_root / freeze.MODEL_SPECS[model_tag]["evalplus_output_relative"]
    assert_not_existing_formal_run(output_dir, repo_root)
    if require_output_absent:
        _require(not output_dir.exists(), f"EvalPlus output must be absent before run: {output_dir}")

    # Schema / pairing checks without loading candidate source bodies for execution.
    generation_ids = {row["generation_id"] for row in planned}
    _require(len(generation_ids) == 400, "generation_id count drift")
    for generation_id in generation_ids:
        stages = {row["stage"] for row in planned if row["generation_id"] == generation_id}
        _require(stages == set(freeze.STAGES), f"stage pairing incomplete: {generation_id}")

    evalplus_importable = False
    evalplus_version = None
    try:
        evalplus_version = importlib.metadata.version("evalplus")
        evalplus_importable = True
    except importlib.metadata.PackageNotFoundError:
        evalplus_importable = False

    return {
        "status": "zero_candidate_execution_evalplus_preflight_passed",
        "plan_id": freeze.PLAN_ID,
        "model_tag": model_tag,
        "planned_eval_cells": len(planned),
        "planned_candidates": 400,
        "stages": list(freeze.STAGES),
        "output_directory": freeze.MODEL_SPECS[model_tag]["evalplus_output_relative"].as_posix(),
        "dataset_version": freeze.DATASET_VERSION,
        "dataset_hash": freeze.DATASET_HASH,
        "evalplus_version_expected": freeze.EVALPLUS_VERSION,
        "evalplus_package_importable": evalplus_importable,
        "evalplus_package_version_observed": evalplus_version,
        "native_windows": os.name == "nt" or sys.platform.startswith("win"),
        "formal_execute_allowed_here": not (os.name == "nt" or sys.platform.startswith("win")),
        "generation_preflight_status": gen_receipt["status"],
        "require_output_absent": require_output_absent,
        "model_calls": 0,
        "candidate_program_executed": False,
        "candidate_program_imported": False,
        "candidate_program_compiled": False,
        "evalplus_executed": False,
    }


def _official_check(args: tuple[Any, ...]) -> dict[str, Any]:
    from evalplus.evaluate import check_correctness

    return check_correctness(*args)


def execute_model(
    *,
    model: str,
    acknowledgement: str,
    parallel: int,
    resume: bool,
    repo_root: Path = REPO_ROOT,
    per_cell_timeout: float = 10.0,
) -> dict[str, Any]:
    _require(acknowledgement == EXECUTE_ACK, "execute acknowledgement mismatch")
    _require(parallel == 1, "--parallel must equal 1")
    if os.name == "nt" or sys.platform.startswith("win"):
        raise QualificationError("formal EvalPlus must run inside WSL/Linux")

    model_tag = gen_preflight.resolve_model_tag(model)
    preflight = zero_candidate_execution_preflight(
        model=model_tag,
        repo_root=repo_root,
        require_output_absent=not resume,
    )
    _require(preflight["evalplus_package_importable"] is True, "evalplus package missing")
    _require(
        preflight["evalplus_package_version_observed"] == freeze.EVALPLUS_VERSION,
        "EvalPlus version drift",
    )

    from evalplus.data import get_mbpp_plus, get_mbpp_plus_hash
    from evalplus.eval import PASS
    from evalplus.eval._special_oracle import MBPP_OUTPUT_NOT_NONE_TASKS
    from evalplus.evaluate import get_groundtruth

    run_dir = repo_root / freeze.MODEL_SPECS[model_tag]["run_output_relative"]
    deriv_dir = run_dir / "derivatives"
    _require(deriv_dir.is_dir(), "derivatives directory missing; run derivatives first")
    output_dir = repo_root / freeze.MODEL_SPECS[model_tag]["evalplus_output_relative"]
    if resume:
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        _require(not output_dir.exists(), "output exists; use --resume for safe continuation")
        output_dir.mkdir(parents=True, exist_ok=False)

    all_problems = get_mbpp_plus(version=freeze.DATASET_VERSION)
    dataset_hash = get_mbpp_plus_hash(version=freeze.DATASET_VERSION)
    _require(dataset_hash == freeze.DATASET_HASH, "official MBPP+ dataset hash drift")

    planned = build_eval_cells_plan(model_tag, repo_root)
    task_ids = sorted({row["task_id"] for row in planned})
    problems = {task_id: all_problems[task_id] for task_id in task_ids}
    subset_hash = dataset_hash + "-" + _sha256_bytes("\n".join(task_ids).encode("utf-8"))[:16]
    expected_output = get_groundtruth(problems, subset_hash, MBPP_OUTPUT_NOT_NONE_TASKS)

    results_path = output_dir / "cell_level_ledger.csv"
    cache_path = output_dir / "eval_result_cache_provenance.jsonl"
    completed: dict[str, dict[str, str]] = {}
    if resume and results_path.is_file():
        for row in _read_csv(results_path):
            if row.get("ledger_complete") == "true":
                completed[row["evaluation_account_id"]] = row

    result_rows: list[dict[str, Any]] = []
    cache_rows: list[dict[str, Any]] = []
    sha_to_result: dict[str, dict[str, Any]] = {}

    for index, plan_row in enumerate(planned):
        account_id = plan_row["evaluation_account_id"]
        if account_id in completed:
            prev = completed[account_id]
            result_rows.append(prev)
            prev_sha = prev.get("evaluation_source_sha256") or ""
            if prev_sha and prev.get("evaluation_disposition") in {
                "evaluated",
                "evaluated_via_byte_identical_cache",
            }:
                sha_to_result.setdefault(
                    prev_sha,
                    {
                        "evaluation_account_id": account_id,
                        "base_status": prev.get("base_status", ""),
                        "plus_status": prev.get("plus_status", ""),
                        "evalplus_pass": prev.get("evalplus_pass") == "true",
                    },
                )
            continue
        derived = _read_json(deriv_dir / f"{plan_row['generation_id']}.json")
        stage_payload = derived["stages"][plan_row["stage"]]
        source = stage_payload.get("source")
        source_sha = stage_payload.get("source_sha256")
        invalid = not isinstance(source, str) or source_sha is None
        infra_failure = False
        base_status = ""
        plus_status = ""
        passed = False
        cache_hit = False
        cache_source_account = ""

        if invalid:
            disposition = "invalid_or_missing_candidate"
        elif source_sha in sha_to_result:
            cached = sha_to_result[source_sha]
            base_status = cached["base_status"]
            plus_status = cached["plus_status"]
            passed = cached["evalplus_pass"]
            cache_hit = True
            cache_source_account = cached["evaluation_account_id"]
            disposition = "evaluated_via_byte_identical_cache"
        else:
            try:
                solution = problems[plan_row["task_id"]]["prompt"] + source
                result = _official_check(
                    (
                        "mbpp",
                        index,
                        problems[plan_row["task_id"]],
                        solution,
                        expected_output[plan_row["task_id"]],
                        False,
                        True,
                        account_id,
                    )
                )
                base_status = str(result["base"][0])
                plus_status = str(result["plus"][0])
                passed = base_status == plus_status == str(PASS) or (
                    base_status == PASS and plus_status == PASS
                )
                disposition = "evaluated"
                sha_to_result[source_sha] = {
                    "evaluation_account_id": account_id,
                    "base_status": base_status,
                    "plus_status": plus_status,
                    "evalplus_pass": passed,
                }
            except Exception as exc:  # noqa: BLE001 - classified as infrastructure
                infra_failure = True
                disposition = "evaluator_infrastructure_failure"
                base_status = f"infra:{type(exc).__name__}"
                plus_status = base_status
                passed = False

        row = {
            "evaluation_account_id": account_id,
            "generation_id": plan_row["generation_id"],
            "cell_identity": plan_row["cell_identity"],
            "task_id": plan_row["task_id"],
            "seed": plan_row["seed"],
            "prompt_condition": plan_row["prompt_condition"],
            "model_tag": model_tag,
            "stage": plan_row["stage"],
            "evaluation_source_sha256": source_sha or "",
            "base_status": base_status,
            "plus_status": plus_status,
            "evalplus_pass": str(passed).lower(),
            "evaluation_disposition": disposition,
            "cache_hit": str(cache_hit).lower(),
            "cache_source_account": cache_source_account,
            "ledger_complete": "true",
            "evaluator_version": freeze.EVALPLUS_VERSION,
            "evaluator_engine": freeze.EVALUATOR_ENGINE,
            "runner_identity": RUNNER_IDENTITY,
            "invalid_or_missing_candidate": str(invalid).lower(),
            "evaluator_infrastructure_failure": str(infra_failure).lower(),
        }
        result_rows.append(row)
        cache_rows.append(
            {
                "evaluation_account_id": account_id,
                "stage": plan_row["stage"],
                "evaluation_source_sha256": source_sha or "",
                "cache_hit": cache_hit,
                "cache_source_account": cache_source_account,
                "disposition": disposition,
            }
        )

    # Persist ledgers (resume-safe rewrite of complete set).
    fields = list(result_rows[0].keys()) if result_rows else []
    with results_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(result_rows)
    with cache_path.open("w", encoding="utf-8") as handle:
        for row in cache_rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    execution_manifest = {
        "status": "evalplus_complete_pending_cross_machine_merge",
        "plan_id": freeze.PLAN_ID,
        "model_tag": model_tag,
        "eval_cells": len(result_rows),
        "dataset_hash": freeze.DATASET_HASH,
        "dataset_version": freeze.DATASET_VERSION,
        "evalplus_version": freeze.EVALPLUS_VERSION,
        "evaluator_engine": freeze.EVALUATOR_ENGINE,
        "parallel": parallel,
        "resume": resume,
        "model_calls": 0,
        "candidate_program_executed": True,
        "evalplus_executed": True,
        "results_sha256": _sha256_bytes(results_path.read_bytes()),
    }
    (output_dir / "execution_manifest.json").write_text(
        json.dumps(execution_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return execution_manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, choices=freeze.ALLOWED_MODEL_TAGS)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--plan", action="store_true")
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--resume", action="store_true")
    parser.add_argument("--parallel", type=int, default=1)
    parser.add_argument("--acknowledgement", default="")
    parser.add_argument("--per-cell-timeout", type=float, default=10.0)
    args = parser.parse_args(argv)

    if args.preflight:
        print(
            json.dumps(
                zero_candidate_execution_preflight(model=args.model),
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if args.plan:
        planned = build_eval_cells_plan(args.model)
        print(
            json.dumps(
                {
                    "status": "eval_plan_only",
                    "model_tag": args.model,
                    "eval_cells": len(planned),
                    "model_calls": 0,
                    "candidate_program_executed": False,
                    "evalplus_executed": False,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    result = execute_model(
        model=args.model,
        acknowledgement=args.acknowledgement,
        parallel=args.parallel,
        resume=bool(args.resume),
        per_cell_timeout=args.per_cell_timeout,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
