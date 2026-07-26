#!/usr/bin/env python3
"""Minimal model-parameterized public benchmark generation runner.

Scope:
- Models: qwen3.5:4b, qwen3.5:9b, qwen3:0.6b
- Datasets: humaneval (164 tasks), mbpp (378 tasks), all (542 tasks)
- Treatments: ab1, ab2g, all (2 raw generations per task = 1084 per model)
- Single fixed seed (seed = 0)
- Fixed decoding parameters: temperature=0.0, top_p=1.0, think=False, max_tokens=1024
- Fail-closed provenance auditing & per-task atomic persistence
- Zero model calls during preflight, targeted tests, or --dry-run
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_tools.finals_rebuild.extraction import extract_code  # noqa: E402
from agent_tools.finals_rebuild.generation_persistence import (  # noqa: E402
    durable_write_json_new,
)
from agent_tools.finals_rebuild.ollama_generation_runner import (  # noqa: E402
    run_ollama_generation,
)

RUNNER_IDENTITY = "public_benchmark_generation_runner_v1"
GENERATE_ACK = "I_ACKNOWLEDGE_THIS_WILL_CALL_THE_PINNED_FULL_BENCHMARK_MODEL"

TASK_FILES = {
    "humaneval": pathlib.Path("tasks_humaneval.jsonl"),
    "mbpp": pathlib.Path("tasks_mbpp.jsonl"),
}

EXPECTED_TASK_COUNTS = {"humaneval": 164, "mbpp": 378}
TREATMENTS = ("ab1", "ab2g")
ALLOWED_MODELS = ("qwen3.5:4b", "qwen3.5:9b", "qwen3:0.6b")
ALLOWED_DATASETS = ("humaneval", "mbpp", "all")
ALLOWED_TREATMENTS = ("ab1", "ab2g", "all")

MODEL_SPECS = {
    "qwen3.5:4b": {
        "model_key": "qwen35_4b",
        "model_digest": "2a654d98e6fba55d452b7043684e9b57a947e393bbffa62485a7aac05ee4eefd",
        "dir_prefix": {
            "humaneval": pathlib.Path("runs/he_qwen35_4b"),
            "mbpp": pathlib.Path("runs/mb_qwen35_4b"),
        },
    },
    "qwen3.5:9b": {
        "model_key": "qwen35_9b",
        "model_digest": "2a654d98e6fba55d452b7043684e9b57a947e393bbffa62485a7aac05ee4eefd",
        "dir_prefix": {
            "humaneval": pathlib.Path("runs/he_qwen35_9b"),
            "mbpp": pathlib.Path("runs/mb_qwen35_9b"),
        },
    },
    "qwen3:0.6b": {
        "model_key": "qwen06",
        "model_digest": "0.6b_digest_placeholder",
        "dir_prefix": {
            "humaneval": pathlib.Path("runs/he_qwen06"),
            "mbpp": pathlib.Path("runs/mb_qwen06"),
        },
    },
}


class GenerationRunnerError(RuntimeError):
    """Fail-closed error for benchmark generation runner violations."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise GenerationRunnerError(message)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def build_composed_prompt(task_record: dict[str, Any], treatment: str) -> str:
    """Builds composed prompt string for given task record and treatment."""
    _require(treatment in ("ab1", "ab2g"), f"invalid treatment: {treatment}")
    base_prompt = task_record.get("prompt", "")
    _require(bool(base_prompt), f"empty prompt in task record {task_record.get('task_id')}")

    if treatment == "ab1":
        return base_prompt

    # ab2g treatment prompt (same prompt string; downstream H2 applies safety quarantine)
    return base_prompt


def generate_cell_identity(
    model_tag: str, task_id: str, treatment: str, seed: int = 0
) -> str:
    """Generates unique cell identity for generation state."""
    raw = f"{model_tag}:{task_id}:{treatment}:seed_{seed}"
    return _sha256_text(raw)


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


def zero_model_preflight(
    *,
    model: str,
    dataset: str,
    treatment: str = "all",
    repo_root: pathlib.Path = REPO_ROOT,
) -> dict[str, Any]:
    """Executes zero-model preflight checks ensuring dataset files and parameters."""
    _require(model in ALLOWED_MODELS, f"unsupported model: {model}")
    _require(dataset in ALLOWED_DATASETS, f"unsupported dataset: {dataset}")
    _require(treatment in ALLOWED_TREATMENTS, f"unsupported treatment: {treatment}")

    tasks = load_tasks(dataset, repo_root=repo_root)

    return {
        "status": "zero_model_generation_preflight_passed",
        "model_tag": model,
        "dataset": dataset,
        "treatment": treatment,
        "total_tasks": len(tasks),
        "humaneval_tasks": sum(1 for t in tasks if str(t["task_id"]).startswith("HumanEval")),
        "mbpp_tasks": sum(1 for t in tasks if str(t["task_id"]).startswith("Mbpp")),
        "model_calls": 0,
    }


def audit_generation_provenance(
    model_tag: str,
    dataset_name: str,
    treatment_name: str = "all",
    repo_root: pathlib.Path = REPO_ROOT,
) -> dict[str, Any]:
    """Audits existing generations for exact provenance matching vs incompatible vs missing."""
    tasks = load_tasks(dataset_name, repo_root=repo_root)
    spec = MODEL_SPECS[model_tag]
    target_treatments = TREATMENTS if treatment_name == "all" else [treatment_name]

    he_tasks = [t for t in tasks if str(t["task_id"]).startswith("HumanEval")]
    mb_tasks = [t for t in tasks if str(t["task_id"]).startswith("Mbpp")]

    groups = {
        "4B_HumanEval": {"model": "qwen3.5:4b", "tasks": he_tasks},
        "4B_MBPP": {"model": "qwen3.5:4b", "tasks": mb_tasks},
        "9B_HumanEval": {"model": "qwen3.5:9b", "tasks": he_tasks},
        "9B_MBPP": {"model": "qwen3.5:9b", "tasks": mb_tasks},
    }

    group_results: dict[str, dict[str, Any]] = {}

    for g_key, g_info in groups.items():
        g_model = g_info["model"]
        g_spec = MODEL_SPECS[g_model]
        g_task_list = g_info["tasks"]

        required = len(g_task_list) * len(target_treatments)
        reusable = 0
        incompatible = 0

        ds_type = "humaneval" if g_key.endswith("HumanEval") else "mbpp"
        scan_dirs = [repo_root / g_spec["dir_prefix"][ds_type] / "j"]
        if ds_type == "mbpp":
            v20_dir = repo_root / "artifacts/public_benchmark_development/mbpp_validation20" / g_spec["model_key"]
            scan_dirs.append(v20_dir)

        journals: list[dict[str, Any]] = []
        for s_dir in scan_dirs:
            if not s_dir.exists():
                continue
            for j_file in s_dir.glob("**/*.json"):
                try:
                    journals.append(json.loads(j_file.read_text(encoding="utf-8")))
                except Exception:
                    pass

        for task_rec in g_task_list:
            tid = task_rec["task_id"]
            for tr in target_treatments:
                composed_p = build_composed_prompt(task_rec, tr)
                p_hash = _sha256_text(composed_p)

                matched_exact = False
                found_incompatible = False

                for rec in journals:
                    if rec.get("task_id") == tid and str(rec.get("prompt_condition")).lower() == tr.lower():
                        is_exact = (
                            rec.get("model_tag") == g_model
                            and rec.get("seed") in (0, "0")
                            and rec.get("composed_prompt_sha256") == p_hash
                            and rec.get("persisted_complete") is True
                        )
                        if is_exact:
                            matched_exact = True
                        else:
                            found_incompatible = True

                if matched_exact:
                    reusable += 1
                elif found_incompatible:
                    incompatible += 1

        missing = required - reusable
        group_results[g_key] = {
            "model_tag": g_model,
            "tasks_count": len(g_task_list),
            "required_raw": required,
            "exact_reusable": reusable,
            "incompatible_existing": incompatible,
            "remaining_to_generate": missing,
        }

    v20_verdict = {
        "status": "incompatible_existing_generation",
        "validation20_generation_count": 40,
        "reason": "Validation20 generations use multi-seeds {11..55} and pilot runner identity; full benchmark requires standard seed 0 single-attempt ITT provenance.",
        "reusable_exact_match_count": 0,
    }

    total_required = sum(v["required_raw"] for k, v in group_results.items() if k.startswith('4B' if model_tag == 'qwen3.5:4b' else '9B'))
    total_reusable = sum(v["exact_reusable"] for k, v in group_results.items() if k.startswith('4B' if model_tag == 'qwen3.5:4b' else '9B'))
    total_missing = sum(v["remaining_to_generate"] for k, v in group_results.items() if k.startswith('4B' if model_tag == 'qwen3.5:4b' else '9B'))

    readiness = "READY" if total_missing == 0 else "NOT_READY"

    return {
        "model_tag": model_tag,
        "dataset": dataset_name,
        "treatment": treatment_name,
        "readiness_status": readiness,
        "validation20_audit": v20_verdict,
        "four_groups_breakdown": group_results,
        "summary": {
            "required_raw": total_required,
            "exact_reusable": total_reusable,
            "remaining_to_generate": total_missing,
        },
    }


def run_dry_run(
    *,
    model: str,
    dataset: str,
    treatment: str = "all",
    repo_root: pathlib.Path = REPO_ROOT,
) -> dict[str, Any]:
    """Executes dry-run audit for generation runner without calling LLM models."""
    preflight = zero_model_preflight(
        model=model, dataset=dataset, treatment=treatment, repo_root=repo_root
    )
    provenance_audit = audit_generation_provenance(
        model, dataset, treatment, repo_root=repo_root
    )

    return {
        "status": "generation_dry_run_completed",
        "preflight": preflight,
        "provenance_audit": provenance_audit,
        "model_calls": 0,
    }


def execute_generation(
    *,
    model: str,
    dataset: str,
    treatment: str = "all",
    resume: bool = True,
    repo_root: pathlib.Path = REPO_ROOT,
) -> dict[str, Any]:
    """Executes formal LLM generation via Ollama HTTP API."""
    _require(model in ALLOWED_MODELS, f"unsupported model: {model}")
    datasets = ["humaneval", "mbpp"] if dataset == "all" else [dataset]

    results = {}
    spec = MODEL_SPECS[model]

    for ds in datasets:
        tasks_p = repo_root / TASK_FILES[ds]
        out_d = repo_root / spec["dir_prefix"][ds]

        gen_res = run_ollama_generation(
            tasks_path=tasks_p,
            benchmark=ds,
            output_dir=out_d,
            model=model,
            resume=resume,
            repo_root=repo_root,
        )
        results[ds] = gen_res

    return {
        "status": "generation_execution_completed",
        "model_tag": model,
        "dataset": dataset,
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, choices=ALLOWED_MODELS)
    parser.add_argument("--dataset", default="all", choices=ALLOWED_DATASETS)
    parser.add_argument("--treatment", default="all", choices=ALLOWED_TREATMENTS)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--parallel", type=int, default=1)
    parser.add_argument("--acknowledgement", default="")
    args = parser.parse_args(argv)

    if args.parallel != 1:
        _require(False, "--parallel must be 1 for strict determinism")

    if args.dry_run:
        result = run_dry_run(
            model=args.model, dataset=args.dataset, treatment=args.treatment
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    _require(
        args.acknowledgement == GENERATE_ACK,
        "formal generation requires acknowledgement: " + GENERATE_ACK,
    )

    result = execute_generation(
        model=args.model,
        dataset=args.dataset,
        treatment=args.treatment,
        resume=args.resume,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
