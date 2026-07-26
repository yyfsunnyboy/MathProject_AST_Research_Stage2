#!/usr/bin/env python3
"""Minimal model-parameterized public benchmark H2 replay & readiness runner.

Supports:
- Models: qwen3.5:4b, qwen3.5:9b, qwen3:0.6b
- Datasets: humaneval (164), mbpp (378), all (542)
- 4 ITT conditions: Ab1-Raw, Ab1-H2, Ab2g-Raw, Ab2g-H2
- Fixed extractor (non-modifying code block extractor)
- Frozen H2 quarantine rule with fail-closed SHA256 check
- Zero model calls during replay/audit
- CLI flags: --model, --dataset, --dry-run, --resume, --parallel 1
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
from typing import Any, Mapping, Sequence

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_tools.finals_rebuild.extraction import extract_code  # noqa: E402
from agent_tools.finals_rebuild.mbpp_h2_module_assert_quarantine import (  # noqa: E402
    RULE_ID,
    quarantine_module_assert_entrypoint_selftest,
)

RULE_RELATIVE = pathlib.Path("agent_tools/finals_rebuild/mbpp_h2_module_assert_quarantine.py")
EXPECTED_RULE_SHA256 = (
    "dbd96fc3c1228f74c784e2444350102de121d4e202dcb0075aad214090bbfa18"
)

TASK_FILES = {
    "humaneval": pathlib.Path("tasks_humaneval.jsonl"),
    "mbpp": pathlib.Path("tasks_mbpp.jsonl"),
}

EXPECTED_TASK_COUNTS = {"humaneval": 164, "mbpp": 378}
CONDITIONS = ("Ab1-Raw", "Ab1-H2", "Ab2g-Raw", "Ab2g-H2")
ALLOWED_MODELS = ("qwen3.5:4b", "qwen3.5:9b", "qwen3:0.6b")
ALLOWED_DATASETS = ("humaneval", "mbpp", "all")

MODEL_SPECS = {
    "qwen3.5:4b": {
        "model_key": "qwen35_4b",
        "search_dirs": [
            pathlib.Path("runs/he_qwen35_4b"),
            pathlib.Path("runs/mb_qwen35_4b"),
            pathlib.Path("artifacts/public_benchmark_development/mbpp_validation20/qwen35_4b"),
        ],
        "default_output": pathlib.Path("artifacts/public_benchmark_governance/qwen35_4b_h2_full_replay_v1"),
    },
    "qwen3.5:9b": {
        "model_key": "qwen35_9b",
        "search_dirs": [
            pathlib.Path("runs/he_qwen35_9b"),
            pathlib.Path("runs/mb_qwen35_9b"),
            pathlib.Path("artifacts/public_benchmark_development/mbpp_validation20/qwen35_9b"),
            pathlib.Path("artifacts/public_benchmark_development/mbpp_qwen35_9b_ab1"),
        ],
        "default_output": pathlib.Path("artifacts/public_benchmark_governance/qwen35_9b_h2_full_replay_v1"),
    },
    "qwen3:0.6b": {
        "model_key": "qwen06",
        "search_dirs": [
            pathlib.Path("runs/he_qwen06"),
            pathlib.Path("runs/mb_qwen06"),
        ],
        "default_output": pathlib.Path("artifacts/public_benchmark_governance/qwen06_h2_full_replay_evaluation_v1"),
    },
}


class BenchmarkRunnerError(RuntimeError):
    """Fail-closed error for benchmark runner violations."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise BenchmarkRunnerError(message)


def _sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_tasks(dataset_name: str, repo_root: pathlib.Path = REPO_ROOT) -> list[dict[str, Any]]:
    """Loads and validates benchmark task records from dataset jsonl file."""
    _require(dataset_name in ALLOWED_DATASETS, f"unsupported dataset: {dataset_name}")
    datasets_to_load = ["humaneval", "mbpp"] if dataset_name == "all" else [dataset_name]

    tasks: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for ds in datasets_to_load:
        task_file = repo_root / TASK_FILES[ds]
        _require(task_file.is_file(), f"task file missing: {task_file}")
        lines = task_file.read_text(encoding="utf-8").splitlines()
        ds_tasks = []
        for line in lines:
            if not line.strip():
                continue
            rec = json.loads(line)
            tid = rec.get("task_id")
            ep = rec.get("entry_point")
            _require(bool(tid), f"missing task_id in {ds}")
            _require(tid not in seen_ids, f"duplicate task_id: {tid}")
            _require(bool(ep) and str(ep).isidentifier(), f"invalid entry_point '{ep}' for task {tid}")
            seen_ids.add(tid)
            ds_tasks.append(rec)
        _require(
            len(ds_tasks) == EXPECTED_TASK_COUNTS[ds],
            f"{ds} task count mismatch: expected {EXPECTED_TASK_COUNTS[ds]}, found {len(ds_tasks)}",
        )
        tasks.extend(ds_tasks)

    return tasks


def validate_roster(dataset_name: str, repo_root: pathlib.Path = REPO_ROOT) -> dict[str, Any]:
    """Validates roster integrity for HumanEval and MBPP datasets."""
    tasks = load_tasks(dataset_name, repo_root=repo_root)
    he_count = sum(1 for t in tasks if str(t["task_id"]).startswith("HumanEval"))
    mb_count = sum(1 for t in tasks if str(t["task_id"]).startswith("Mbpp"))

    return {
        "status": "roster_validation_passed",
        "dataset": dataset_name,
        "total_tasks": len(tasks),
        "humaneval_tasks": he_count,
        "mbpp_tasks": mb_count,
        "unique_task_ids": len(tasks),
    }


def zero_model_preflight(
    *,
    model: str,
    dataset: str,
    repo_root: pathlib.Path = REPO_ROOT,
) -> dict[str, Any]:
    """Executes zero-model preflight checks ensuring code immutability and rule hashes."""
    _require(model in ALLOWED_MODELS, f"unsupported model: {model}")
    _require(dataset in ALLOWED_DATASETS, f"unsupported dataset: {dataset}")

    rule_path = repo_root / RULE_RELATIVE
    _require(rule_path.is_file(), f"H2 rule file missing: {rule_path}")
    actual_hash = _sha256_file(rule_path)
    _require(
        actual_hash == EXPECTED_RULE_SHA256,
        f"H2 rule hash mismatch: expected {EXPECTED_RULE_SHA256}, got {actual_hash}",
    )

    roster_info = validate_roster(dataset, repo_root=repo_root)

    return {
        "status": "zero_model_preflight_passed",
        "model_tag": model,
        "dataset": dataset,
        "rule_id": RULE_ID,
        "rule_hash": actual_hash,
        "model_calls": 0,
        "roster_info": roster_info,
    }


def audit_inventory(
    model_tag: str,
    dataset_name: str,
    repo_root: pathlib.Path = REPO_ROOT,
) -> dict[str, Any]:
    """Audits existing raw generation attempts and extracted completions for model & dataset."""
    tasks = load_tasks(dataset_name, repo_root=repo_root)
    spec = MODEL_SPECS[model_tag]

    # Map of (task_id, condition) -> boolean present
    present_raw: dict[tuple[str, str], bool] = {}

    for search_dir in spec["search_dirs"]:
        abs_dir = repo_root / search_dir
        if not abs_dir.exists():
            continue

        # Check jsonl files
        for jsonl_file in abs_dir.glob("**/*.jsonl"):
            try:
                for line in jsonl_file.read_text(encoding="utf-8").splitlines():
                    if not line.strip():
                        continue
                    rec = json.loads(line)
                    tid = rec.get("task_id")
                    cond = rec.get("prompt_condition")
                    if tid and cond and rec.get("model_tag") == model_tag:
                        present_raw[(tid, cond)] = True
            except Exception:
                pass

        # Check individual json journals
        for json_file in abs_dir.glob("**/*.json"):
            try:
                rec = json.loads(json_file.read_text(encoding="utf-8"))
                tid = rec.get("task_id")
                cond = rec.get("prompt_condition")
                if tid and cond and rec.get("model_tag") == model_tag:
                    present_raw[(tid, cond)] = True
            except Exception:
                pass

    # Tally missing items
    treatments = ["Ab1", "Ab2g"]
    total_planned_raw = len(tasks) * len(treatments)
    total_planned_itt = len(tasks) * len(CONDITIONS)

    he_tasks = [t for t in tasks if str(t["task_id"]).startswith("HumanEval")]
    mb_tasks = [t for t in tasks if str(t["task_id"]).startswith("Mbpp")]

    he_present_raw = sum(1 for t in he_tasks for cond in treatments if (t["task_id"], cond) in present_raw)
    mb_present_raw = sum(1 for t in mb_tasks for cond in treatments if (t["task_id"], cond) in present_raw)

    he_missing_raw = len(he_tasks) * len(treatments) - he_present_raw
    mb_missing_raw = len(mb_tasks) * len(treatments) - mb_present_raw
    total_missing_raw = total_planned_raw - (he_present_raw + mb_present_raw)

    he_missing_itt = len(he_tasks) * len(CONDITIONS) - (he_present_raw * 2)
    mb_missing_itt = len(mb_tasks) * len(CONDITIONS) - (mb_present_raw * 2)
    total_missing_itt = total_planned_itt - ((he_present_raw + mb_present_raw) * 2)

    readiness = "READY" if total_missing_raw == 0 else "NOT_READY"

    return {
        "model_tag": model_tag,
        "dataset": dataset_name,
        "readiness_status": readiness,
        "humaneval_tasks": len(he_tasks),
        "mbpp_tasks": len(mb_tasks),
        "total_tasks": len(tasks),
        "conditions_count": len(CONDITIONS),
        "total_planned_itt_states": total_planned_itt,
        "present_raw_generations": he_present_raw + mb_present_raw,
        "missing_raw_generations": total_missing_raw,
        "missing_itt_states": total_missing_itt,
        "breakdown": {
            "humaneval": {
                "tasks": len(he_tasks),
                "planned_itt_states": len(he_tasks) * len(CONDITIONS),
                "present_raw": he_present_raw,
                "missing_raw": he_missing_raw,
                "missing_itt": he_missing_itt,
            },
            "mbpp": {
                "tasks": len(mb_tasks),
                "planned_itt_states": len(mb_tasks) * len(CONDITIONS),
                "present_raw": mb_present_raw,
                "missing_raw": mb_missing_raw,
                "missing_itt": mb_missing_itt,
            },
        },
    }


def run_dry_run(
    *,
    model: str,
    dataset: str,
    repo_root: pathlib.Path = REPO_ROOT,
) -> dict[str, Any]:
    """Performs dry-run readiness audit for specified model and dataset."""
    preflight = zero_model_preflight(model=model, dataset=dataset, repo_root=repo_root)
    inventory = audit_inventory(model, dataset, repo_root=repo_root)

    return {
        "status": "dry_run_completed",
        "preflight": preflight,
        "inventory": inventory,
        "model_calls": 0,
        "evalplus_executed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, choices=ALLOWED_MODELS)
    parser.add_argument("--dataset", default="all", choices=ALLOWED_DATASETS)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--parallel", type=int, default=1)
    parser.add_argument("--output-dir", default="")
    args = parser.parse_args(argv)

    if args.parallel != 1:
        _require(False, "--parallel must be 1 for strict determinism")

    if args.dry_run:
        result = run_dry_run(model=args.model, dataset=args.dataset)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    print("Model-parameterized public benchmark runner initialized.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
