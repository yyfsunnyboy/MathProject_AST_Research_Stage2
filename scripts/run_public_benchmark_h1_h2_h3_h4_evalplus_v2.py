"""Run cumulative H1-H4 public-benchmark evaluation with evaluator v2.

This reads the already-materialized v1 replay journals.  It performs no model
calls and no replay.  Raw and final candidates are evaluated independently via
EvalPlus 0.3.1's process-isolated public interface.  All outputs use new v2
directories; v1 artifacts are never overwritten.
"""

from __future__ import annotations

import argparse
import csv
import json
import pathlib
import sys
from datetime import datetime, timezone
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_tools.finals_rebuild.generation_persistence import durable_write_json_new
from scripts.evalplus_isolated_evaluator_v2 import (
    EXPECTED_EVALPLUS_VERSION,
    IsolatedEvalPlusEvaluatorV2,
    require_evalplus_031,
)

ALLOWED_MODELS = ("qwen3.5:4b", "qwen3.5:9b")
ALLOWED_DATASETS = ("humaneval", "mbpp", "all")
MODEL_SPECS = {
    "qwen3.5:4b": {
        "model_key": "qwen35_4b",
        "replay_dir": pathlib.Path(
            "artifacts/public_benchmark_governance/"
            "qwen35_4b_h1_h2_h3_h4_full_replay_v1"
        ),
        "default_output": pathlib.Path(
            "artifacts/public_benchmark_governance/"
            "qwen35_4b_h1_h2_h3_h4_full_evalplus_v2"
        ),
    },
    "qwen3.5:9b": {
        "model_key": "qwen35_9b",
        "replay_dir": pathlib.Path(
            "artifacts/public_benchmark_governance/"
            "qwen35_9b_h1_h2_h3_h4_full_replay_v1"
        ),
        "default_output": pathlib.Path(
            "artifacts/public_benchmark_governance/"
            "qwen35_9b_h1_h2_h3_h4_full_evalplus_v2"
        ),
    },
}
TRANSITION_CATEGORIES = (
    "verified_rescue",
    "regression",
    "preserved_pass",
    "unchanged_failure",
    "modified_but_still_failed",
    "blocker_removed_but_incorrect",
    "abstained_unchanged",
)


class IsolatedEvalPlusV2Error(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise IsolatedEvalPlusV2Error(message)


def _output_dir(
    model: str, output_dir_arg: str, repo_root: pathlib.Path
) -> pathlib.Path:
    spec = MODEL_SPECS[model]
    out_dir = (
        repo_root / output_dir_arg
        if output_dir_arg
        else repo_root / spec["default_output"]
    )
    _require(out_dir.name.endswith("_v2"), "v2 output directory name must end in _v2")
    return out_dir


def _selected(task_id: str, dataset: str) -> bool:
    return (
        dataset == "all"
        or (dataset == "humaneval" and task_id.startswith("HumanEval"))
        or (dataset == "mbpp" and task_id.startswith("Mbpp"))
    )


def classify_transition(
    *,
    modified: bool,
    raw_base_pass: bool,
    raw_final_pass: bool,
    final_base_pass: bool,
    final_final_pass: bool,
    any_layer_abstained: bool,
) -> str:
    if not raw_final_pass and final_final_pass:
        return "verified_rescue"
    if raw_final_pass and not final_final_pass:
        return "regression"
    if raw_final_pass and final_final_pass:
        return "preserved_pass"
    if modified:
        if not raw_base_pass and final_base_pass:
            return "blocker_removed_but_incorrect"
        return "modified_but_still_failed"
    if any_layer_abstained:
        return "abstained_unchanged"
    return "unchanged_failure"


def run_dry_run(
    *,
    model: str,
    dataset: str,
    output_dir_arg: str = "",
    repo_root: pathlib.Path = REPO_ROOT,
) -> dict[str, Any]:
    _require(model in ALLOWED_MODELS, f"unsupported model: {model}")
    _require(dataset in ALLOWED_DATASETS, f"unsupported dataset: {dataset}")
    require_evalplus_031()
    replay_j_dir = repo_root / MODEL_SPECS[model]["replay_dir"] / "j"
    pairs = 0
    if replay_j_dir.is_dir():
        for path in replay_j_dir.glob("*.json"):
            item = json.loads(path.read_text(encoding="utf-8"))
            if _selected(str(item.get("task_id", "")), dataset):
                pairs += 1
    expected = (
        1084 if dataset == "all" else 328 if dataset == "humaneval" else 756
    )
    return {
        "status": "isolated_evalplus_v2_dry_run_completed",
        "model_tag": model,
        "dataset": dataset,
        "evalplus_version": EXPECTED_EVALPLUS_VERSION,
        "isolation": "evalplus.check_correctness->untrusted_check->fresh_process",
        "present_replay_pairs": pairs,
        "expected_pairs": expected,
        "planned_executions": expected * 2,
        "readiness_status": "READY" if pairs == expected else "NOT_READY",
        "output_directory": _output_dir(
            model, output_dir_arg, repo_root
        ).as_posix(),
        "model_calls": 0,
        "replay_executed": False,
        "evalplus_executed": False,
    }


def run_evalplus_execution(
    *,
    model: str,
    dataset: str,
    resume: bool = False,
    output_dir_arg: str = "",
    repo_root: pathlib.Path = REPO_ROOT,
) -> dict[str, Any]:
    dry = run_dry_run(
        model=model,
        dataset=dataset,
        output_dir_arg=output_dir_arg,
        repo_root=repo_root,
    )
    _require(dry["readiness_status"] == "READY", "replay journals are incomplete")
    spec = MODEL_SPECS[model]
    replay_j_dir = repo_root / spec["replay_dir"] / "j"
    out_dir = _output_dir(model, output_dir_arg, repo_root)
    eval_j_dir = out_dir / "j"
    eval_j_dir.mkdir(parents=True, exist_ok=True)
    evaluator = IsolatedEvalPlusEvaluatorV2()
    journals: list[dict[str, Any]] = []
    executed_pairs = skipped_pairs = 0
    seen: set[str] = set()

    for replay_path in sorted(replay_j_dir.glob("*.json")):
        replay = json.loads(replay_path.read_text(encoding="utf-8"))
        task_id = str(replay.get("task_id", ""))
        if not _selected(task_id, dataset):
            continue
        cell_id = str(replay["cell_identity"])
        _require(cell_id not in seen, f"duplicate cell_identity: {cell_id}")
        seen.add(cell_id)
        output_path = eval_j_dir / f"{cell_id}.json"
        if resume and output_path.is_file():
            existing = json.loads(output_path.read_text(encoding="utf-8"))
            if (
                existing.get("persisted_complete") is True
                and existing.get("runner_identity")
                == "public_benchmark_h1_h2_h3_h4_evalplus_runner_v2"
            ):
                journals.append(existing)
                skipped_pairs += 1
                continue

        ds = "humaneval" if task_id.startswith("HumanEval") else "mbpp"
        entry_point = str(replay["entry_point"])
        raw = evaluator.evaluate(ds, task_id, entry_point, replay["raw_source"])
        final = evaluator.evaluate(ds, task_id, entry_point, replay["final_source"])
        layers_changed = replay.get("layers_changed") or []
        abstentions = replay.get("abstention_reason_by_layer") or {}
        transition = classify_transition(
            modified=bool(layers_changed),
            raw_base_pass=raw.base_pass,
            raw_final_pass=raw.final_pass,
            final_base_pass=final.base_pass,
            final_final_pass=final.final_pass,
            any_layer_abstained=(
                not layers_changed
                and any(value not in (None, "") for value in abstentions.values())
            ),
        )
        journal = {
            "cell_identity": cell_id,
            "model_tag": model,
            "dataset": ds,
            "task_id": task_id,
            "treatment": replay.get("treatment"),
            "generation_id": replay.get("generation_id"),
            "raw_sha256": replay.get("raw_sha256"),
            "final_sha256": replay.get("final_sha256"),
            "layers_changed": layers_changed,
            "raw_base_pass": raw.base_pass,
            "raw_plus_pass": raw.plus_pass,
            "raw_final_pass": raw.final_pass,
            "raw_base_status": raw.base_status,
            "raw_plus_status": raw.plus_status,
            "cumulative_base_pass": final.base_pass,
            "cumulative_plus_pass": final.plus_pass,
            "cumulative_final_pass": final.final_pass,
            "cumulative_base_status": final.base_status,
            "cumulative_plus_status": final.plus_status,
            "transition_category": transition,
            "isolation": "evalplus.check_correctness->untrusted_check->fresh_process",
            "persisted_complete": True,
            "runner_identity": "public_benchmark_h1_h2_h3_h4_evalplus_runner_v2",
            "experiment_label": "cumulative_H1_H4_candidate_replay_isolated_v2",
        }
        durable_write_json_new(output_path, journal)
        journals.append(journal)
        executed_pairs += 1

    counts = {name: 0 for name in TRANSITION_CATEGORIES}
    for journal in journals:
        counts[journal["transition_category"]] += 1
    summary = {
        "status": "isolated_evalplus_v2_execution_completed",
        "model_tag": model,
        "dataset": dataset,
        "evalplus_version": EXPECTED_EVALPLUS_VERSION,
        "total_pairs": len(journals),
        "total_executions": len(journals) * 2,
        "executed_pairs": executed_pairs,
        "skipped_resume_pairs": skipped_pairs,
        "transition_counts": counts,
        "model_calls": 0,
        "replay_executed": False,
        "evalplus_executed": True,
    }
    (out_dir / "summary_v2.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with (out_dir / "cell_level_ledger_v2.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "cell_identity",
                "task_id",
                "treatment",
                "raw_final_pass",
                "cumulative_final_pass",
                "transition_category",
            ]
        )
        for journal in journals:
            writer.writerow(
                [
                    journal["cell_identity"],
                    journal["task_id"],
                    journal["treatment"],
                    journal["raw_final_pass"],
                    journal["cumulative_final_pass"],
                    journal["transition_category"],
                ]
            )
    manifest = {
        "plan_id": f"{spec['model_key']}_h1_h2_h3_h4_full_evalplus_v2",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "evalplus_version": EXPECTED_EVALPLUS_VERSION,
        "isolation": "evalplus.check_correctness->untrusted_check->fresh_process",
        "model_calls": 0,
        "replay_executed": False,
    }
    (out_dir / "execution_manifest_v2.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, choices=ALLOWED_MODELS)
    parser.add_argument("--dataset", default="all", choices=ALLOWED_DATASETS)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--parallel", type=int, default=1)
    parser.add_argument("--output-dir", default="")
    args = parser.parse_args(argv)
    _require(args.parallel == 1, "--parallel must be 1 for strict determinism")
    _require(
        args.dry_run != args.execute,
        "choose exactly one of --dry-run or --execute",
    )
    if args.dry_run:
        result = run_dry_run(
            model=args.model,
            dataset=args.dataset,
            output_dir_arg=args.output_dir,
        )
    else:
        result = run_evalplus_execution(
            model=args.model,
            dataset=args.dataset,
            resume=args.resume,
            output_dir_arg=args.output_dir,
        )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
