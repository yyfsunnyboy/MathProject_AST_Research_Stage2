#!/usr/bin/env python3
"""Evaluate exactly the 41 frozen changed H1 MBPP cells with EvalPlus.

There is intentionally no generation, retry, resume, selective acceptance, or
overwrite path in this driver.  It writes no rescue/regression conclusion.
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
FROZEN_MANIFEST_RELATIVE = Path(
    "artifacts/public_benchmark_governance/"
    "healer_h0_h1_functional_evaluation_v1/manifest.json"
)
FROZEN_OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_governance/"
    "healer_h0_h1_functional_evaluation_v1/manual_evalplus_run_001"
)
FROZEN_MANIFEST_SHA256 = "420eb05267f11f4f9f157f63167398e86fbc68322f33b33b9bf5656fb6f24913"
EXPECTED_HEALER_SHA256 = "cf4d086ca6e3af968f31b0d087ed2479e5ad38be4b7abe5d2ce5516b68000d44"
EXPECTED_PIPELINE_SHA256 = "a59da1c0a76fe24e868a51481306a5ea09d8d8977c92aab38a6c0c4dc38feccf"
EXPECTED_CANDIDATE_ID = "mbpp_evaluator_blind_healer_candidate_v0"
EXPECTED_RULE_ID = "entrypoint_alias_unique_arity_compatible_v0"
EXPECTED_DATASET_VERSION = "v0.2.0"
EXPECTED_DATASET_HASH = "ee43ecabebf20deef4bb776a405ac5b1"
EXPECTED_EVALPLUS_VERSION = "0.3.1"
EXPECTED_EVALUATOR_ENGINE = "evalplus_0.3.1_check_correctness_subset"

RESULT_FIELDS = (
    "program_id", "evaluation_account_id", "development_layer",
    "prompt_condition", "run_id", "task_id", "seed", "generation_id",
    "normalized_source_sha256", "h1_source_sha256", "base_status",
    "plus_status", "h1_evalplus_pass", "evaluator_version", "evaluator_engine",
)


class EvaluationDriverError(RuntimeError):
    """Raised on any frozen input or execution contract violation."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise EvaluationDriverError(message)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def validate_frozen_inputs(
    *, manifest_path: Path, manifest_sha256: str, parallel: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    expected_path = (REPO_ROOT / FROZEN_MANIFEST_RELATIVE).resolve()
    _require(manifest_path.resolve() == expected_path, "only the frozen manifest path is accepted")
    _require(manifest_sha256 == FROZEN_MANIFEST_SHA256, "manifest SHA-256 argument is not the frozen hash")
    _require(parallel == 1, "--parallel must equal 1")
    manifest_bytes = manifest_path.read_bytes()
    _require(_sha256_bytes(manifest_bytes) == FROZEN_MANIFEST_SHA256, "frozen manifest bytes drift")
    manifest = json.loads(manifest_bytes)
    _require(manifest["status"] == "prepared_not_executed", "manifest status drift")
    _require(manifest["candidate_id"] == EXPECTED_CANDIDATE_ID, "other Healer candidate rejected")
    _require(manifest["rule_order"] == [EXPECTED_RULE_ID], "other Healer rule/version rejected")
    _require(manifest["healer_sha256"] == EXPECTED_HEALER_SHA256, "Healer hash drift")
    _require(manifest["pipeline_sha256"] == EXPECTED_PIPELINE_SHA256, "Pipeline hash/version drift")
    _require(manifest["dataset_version"] == EXPECTED_DATASET_VERSION, "dataset version drift")
    _require(manifest["dataset_hash"] == EXPECTED_DATASET_HASH, "dataset hash drift")
    expected_counts = {"tasks": 60, "task_seed_identities": 300, "programs": 600, "accounts": 1200, "h0": 600, "h1": 600, "changed": 41, "unchanged": 559}
    _require(manifest["counts"] == expected_counts, "manifest count drift")
    _require(manifest["changed_by_prompt_condition"] == {"p0": 39, "scaffold_like": 2}, "changed stratum drift")
    _require(manifest["model_calls"] == manifest["evalplus_executions"] == manifest["new_generation_runs"] == 0, "preparation execution count drift")

    source_hashes = manifest["source_sha256"]
    _require(source_hashes["agent_tools/finals_rebuild/mbpp_evaluator_blind_healer.py"] == EXPECTED_HEALER_SHA256, "manifest Healer source binding drift")
    _require(source_hashes["agent_tools/finals_rebuild/extraction.py"] == EXPECTED_PIPELINE_SHA256, "manifest Pipeline source binding drift")
    for relative, digest in source_hashes.items():
        _require("mbpp_b28" not in relative, "new-28 artifact is outside this evaluation scope")
        source_path = REPO_ROOT / relative
        _require(source_path.is_file(), f"frozen source artifact missing: {relative}")
        _require(_sha256_bytes(source_path.read_bytes()) == digest, f"frozen source artifact hash drift: {relative}")

    root = manifest_path.parent
    locked = manifest["output_sha256_excluding_manifest_and_operator_guide"]
    required_locks = {
        "h0_h1_accounts.csv", "changed_h1_eval_input.jsonl",
        "unchanged_h0_reuse_ledger.csv", "evaluation_plan.json",
        "paired_analysis_plan.json",
    }
    _require(set(locked) == required_locks, "manifest output lock set drift")
    for name, digest in locked.items():
        path = root / name
        _require(path.is_file(), f"frozen asset missing: {name}")
        _require(_sha256_bytes(path.read_bytes()) == digest, f"frozen asset hash drift: {name}")

    accounts = _read_csv(root / "h0_h1_accounts.csv")
    changed = _read_jsonl(root / "changed_h1_eval_input.jsonl")
    reuse = _read_csv(root / "unchanged_h0_reuse_ledger.csv")
    _require(len(accounts) == 1200, "account row count must be 1200")
    _require(sum(row["healer_account"] == "H0" for row in accounts) == 600, "H0 count must be 600")
    _require(sum(row["healer_account"] == "H1" for row in accounts) == 600, "H1 count must be 600")
    _require(len({row["evaluation_account_id"] for row in accounts}) == 1200, "duplicate evaluation account identity")
    _require(len({row["program_id"] for row in accounts}) == 600, "program identity count drift")
    _require(len(changed) == 41, "changed H1 input must contain exactly 41 cells")
    _require(len(reuse) == 559, "reuse ledger must contain exactly 559 cells")
    _require(len({row["program_id"] for row in changed}) == 41, "duplicate changed program identity")
    _require(len({row["evaluation_account_id"] for row in changed}) == 41, "duplicate changed H1 account identity")
    _require(sum(row["prompt_condition"] == "p0" for row in changed) == 39, "changed P0 count must be 39")
    _require(sum(row["prompt_condition"] == "scaffold_like" for row in changed) == 2, "changed Scaffold-like count must be 2")
    changed_accounts = {
        row["evaluation_account_id"]: row for row in accounts
        if row["healer_account"] == "H1" and row["source_changed"] == "true"
    }
    _require(set(changed_accounts) == {row["evaluation_account_id"] for row in changed}, "unexpected changed identity")
    for row in changed:
        account = changed_accounts[row["evaluation_account_id"]]
        _require(row["program_id"] == account["program_id"], "changed program/account mismatch")
        _require(row["healer_candidate_id"] == EXPECTED_CANDIDATE_ID, "changed row other Healer rejected")
        _require(row["healer_rule_id"] == EXPECTED_RULE_ID, "changed row other Healer rule rejected")
        _require(_sha256_bytes(row["completion"].encode("utf-8")) == row["h1_source_sha256"], "changed source hash drift")
        _require(row["h1_source_sha256"] == account["evaluation_source_sha256"], "changed/account source mismatch")
    _require(all(row["reuse_eligible"] == "true" and row["source_state_sha256_exact_match"] == "true" for row in reuse), "reuse eligibility drift")
    return manifest, changed


def _official_check(args: tuple[Any, ...]) -> dict[str, Any]:
    from evalplus.evaluate import check_correctness

    return check_correctness(*args)


def evaluate(
    *, manifest_path: Path, manifest_sha256: str, parallel: int, output_dir: Path,
) -> None:
    if os.name == "nt" or sys.platform.startswith("win"):
        raise EvaluationDriverError("formal evaluation must run inside WSL/Linux")
    manifest, changed = validate_frozen_inputs(
        manifest_path=manifest_path, manifest_sha256=manifest_sha256, parallel=parallel
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
    task_ids = sorted({row["task_id"] for row in changed})
    _require(all(task_id in all_problems for task_id in task_ids), "changed task missing from official dataset")
    problems = {task_id: all_problems[task_id] for task_id in task_ids}
    subset_hash = dataset_hash + "-" + _sha256_bytes("\n".join(task_ids).encode("utf-8"))[:16]
    expected_output = get_groundtruth(problems, subset_hash, MBPP_OUTPUT_NOT_NONE_TASKS)

    result_rows: list[dict[str, Any]] = []
    for row in changed:
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
            "development_layer": row["development_layer"],
            "prompt_condition": row["prompt_condition"],
            "run_id": row["run_id"],
            "task_id": task_id,
            "seed": row["seed"],
            "generation_id": row["generation_id"],
            "normalized_source_sha256": row["normalized_source_sha256"],
            "h1_source_sha256": row["h1_source_sha256"],
            "base_status": base_status,
            "plus_status": plus_status,
            "h1_evalplus_pass": str(passed).lower(),
            "evaluator_version": EXPECTED_EVALPLUS_VERSION,
            "evaluator_engine": EXPECTED_EVALUATOR_ENGINE,
        })
    _require(len(result_rows) == 41, "evaluation result count drift")

    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=RESULT_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(result_rows)
    results_bytes = buffer.getvalue().encode("utf-8")
    execution = {
        "status": "changed_h1_evaluation_complete_pending_paired_analysis",
        "frozen_manifest_sha256": FROZEN_MANIFEST_SHA256,
        "changed_h1_cells_evaluated": 41,
        "unchanged_cells_not_re_evaluated": 559,
        "parallel": 1,
        "evalplus_version": EXPECTED_EVALPLUS_VERSION,
        "dataset_version": EXPECTED_DATASET_VERSION,
        "dataset_hash": EXPECTED_DATASET_HASH,
        "results_sha256": _sha256_bytes(results_bytes),
        "rescue_regression_conclusion_produced": False,
        "retry_resume_selective_acceptance_overwrite": False,
        "model_calls": 0,
        "source_manifest_status": manifest["status"],
    }
    execution_bytes = (json.dumps(execution, indent=2, sort_keys=True) + "\n").encode("utf-8")
    output_dir.mkdir(parents=True)
    with (output_dir / "changed_h1_evalplus_results.csv").open("xb") as handle:
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
