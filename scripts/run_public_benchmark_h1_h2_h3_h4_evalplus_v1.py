#!/usr/bin/env python3
"""Public benchmark cumulative H1->H2->H3->H4 EvalPlus runner (development-candidate evidence).

Experiment name for this artifact family: "cumulative H1-H4 candidate replay"
/ "development-candidate cumulative evaluation". This is exploratory/candidate
evidence, not a frozen/production Healer claim.

Reads the paired Raw/cumulative-final journals written by
run_public_benchmark_h1_h2_h3_h4_replay_v1.py and evaluates BOTH sources
(Raw and cumulative-H4-final) per (task_id, treatment) pair, using the exact
same sandboxed EvalPlus worker as the existing H2-only public benchmark
EvalPlus runner (imported, not reimplemented).

Per model: 1084 Raw/cumulative pairs -> 2168 individual EvalPlus executions
(1084 Raw + 1084 cumulative), stored as 1084 paired per-cell journals.

Zero LLM model calls. Never re-runs replay. Never touches the existing
H2-only ablation artifacts (qwen35_<tag>_h2_full_replay_v1 /
qwen35_<tag>_h2_full_evalplus_v1) or Raw generation artifacts.
"""

from __future__ import annotations

import argparse
import ast
import csv
import json
import pathlib
import sys
from datetime import datetime, timezone
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_tools.finals_rebuild.generation_persistence import (  # noqa: E402
    durable_write_json_new,
)
from scripts.run_public_benchmark_h2_evalplus_v1 import (  # noqa: E402
    EXPECTED_EVALPLUS_VERSION,
    PersistentEvalWorker,
)
import evalplus  # noqa: E402

ALLOWED_MODELS = ("qwen3.5:4b", "qwen3.5:9b")
ALLOWED_DATASETS = ("humaneval", "mbpp", "all")

MODEL_SPECS = {
    "qwen3.5:4b": {
        "model_key": "qwen35_4b",
        "replay_dir": pathlib.Path(
            "artifacts/public_benchmark_governance/qwen35_4b_h1_h2_h3_h4_full_replay_v1"
        ),
        "default_output": pathlib.Path(
            "artifacts/public_benchmark_governance/qwen35_4b_h1_h2_h3_h4_full_evalplus_v1"
        ),
    },
    "qwen3.5:9b": {
        "model_key": "qwen35_9b",
        "replay_dir": pathlib.Path(
            "artifacts/public_benchmark_governance/qwen35_9b_h1_h2_h3_h4_full_replay_v1"
        ),
        "default_output": pathlib.Path(
            "artifacts/public_benchmark_governance/qwen35_9b_h1_h2_h3_h4_full_evalplus_v1"
        ),
    },
}

FORBIDDEN_OUTPUT_DIRS = {
    "qwen35_4b_h2_full_replay_v1",
    "qwen35_9b_h2_full_replay_v1",
    "qwen35_4b_h2_full_evalplus_v1",
    "qwen35_9b_h2_full_evalplus_v1",
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


class CumulativeEvalPlusError(RuntimeError):
    """Fail-closed error for cumulative EvalPlus runner violations."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CumulativeEvalPlusError(message)


def zero_eval_preflight(
    *,
    model: str,
    dataset: str,
    output_dir_arg: str = "",
    repo_root: pathlib.Path = REPO_ROOT,
) -> dict[str, Any]:
    _require(model in ALLOWED_MODELS, f"unsupported model: {model}")
    _require(dataset in ALLOWED_DATASETS, f"unsupported dataset: {dataset}")

    actual_version = getattr(evalplus, "__version__", "unknown")
    _require(
        actual_version == EXPECTED_EVALPLUS_VERSION,
        f"EvalPlus version mismatch: expected {EXPECTED_EVALPLUS_VERSION}, got {actual_version}",
    )

    spec = MODEL_SPECS[model]
    replay_j_dir = repo_root / spec["replay_dir"] / "j"

    out_dir = repo_root / output_dir_arg if output_dir_arg else repo_root / spec["default_output"]
    _require(
        out_dir.name not in FORBIDDEN_OUTPUT_DIRS,
        f"output directory collides with existing H2-only ablation artifact: {out_dir.name}",
    )

    planned_he = 328 if dataset in ("humaneval", "all") else 0
    planned_mb = 756 if dataset in ("mbpp", "all") else 0
    total_planned_pairs = planned_he + planned_mb

    return {
        "status": "zero_eval_preflight_passed",
        "model_tag": model,
        "dataset": dataset,
        "evalplus_version": actual_version,
        "planned_pairs": total_planned_pairs,
        "planned_executions": total_planned_pairs * 2,
        "replay_journal_dir": replay_j_dir.as_posix(),
        "replay_journals_exist": replay_j_dir.is_dir(),
        "output_directory": out_dir.as_posix(),
        "model_calls": 0,
        "evalplus_executed": False,
    }


def run_dry_run(
    *,
    model: str,
    dataset: str,
    output_dir_arg: str = "",
    repo_root: pathlib.Path = REPO_ROOT,
) -> dict[str, Any]:
    preflight = zero_eval_preflight(
        model=model, dataset=dataset, output_dir_arg=output_dir_arg, repo_root=repo_root
    )

    spec = MODEL_SPECS[model]
    replay_j_dir = repo_root / spec["replay_dir"] / "j"

    present = 0
    he_present = 0
    mb_present = 0
    if replay_j_dir.is_dir():
        for p in replay_j_dir.glob("*.json"):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                tid = str(data.get("task_id", ""))
                if dataset == "humaneval" and not tid.startswith("HumanEval"):
                    continue
                if dataset == "mbpp" and not tid.startswith("Mbpp"):
                    continue
                present += 1
                if tid.startswith("HumanEval"):
                    he_present += 1
                elif tid.startswith("Mbpp"):
                    mb_present += 1
            except Exception:
                pass

    readiness = "READY" if present == preflight["planned_pairs"] else "NOT_READY"

    return {
        "status": "dry_run_completed",
        "model_tag": model,
        "dataset": dataset,
        "readiness_status": readiness,
        "planned_pairs": preflight["planned_pairs"],
        "planned_executions": preflight["planned_executions"],
        "present_replay_pairs": present,
        "humaneval_present": he_present,
        "mbpp_present": mb_present,
        "missing_replay_pairs": preflight["planned_pairs"] - present,
        "model_calls": 0,
        "evalplus_executed": False,
    }


def classify_transition(
    *,
    modified: bool,
    raw_base_pass: bool,
    raw_plus_pass: bool,
    raw_final_pass: bool,
    cumulative_base_pass: bool,
    cumulative_plus_pass: bool,
    cumulative_final_pass: bool,
    any_layer_abstained: bool,
) -> str:
    if not raw_final_pass and cumulative_final_pass:
        return "verified_rescue"
    if raw_final_pass and not cumulative_final_pass:
        return "regression"
    if raw_final_pass and cumulative_final_pass:
        return "preserved_pass"
    # both raw and cumulative fail final from here on
    if modified:
        if (not raw_base_pass) and cumulative_base_pass and not cumulative_final_pass:
            return "blocker_removed_but_incorrect"
        return "modified_but_still_failed"
    if any_layer_abstained:
        return "abstained_unchanged"
    return "unchanged_failure"


def run_evalplus_execution(
    *,
    model: str,
    dataset: str,
    resume: bool = True,
    output_dir_arg: str = "",
    repo_root: pathlib.Path = REPO_ROOT,
) -> dict[str, Any]:
    dry_audit = run_dry_run(model=model, dataset=dataset, output_dir_arg=output_dir_arg, repo_root=repo_root)
    _require(
        dry_audit["readiness_status"] == "READY",
        f"cumulative replay pairs incomplete for {model} on {dataset}: "
        f"missing {dry_audit['missing_replay_pairs']}",
    )

    spec = MODEL_SPECS[model]
    replay_j_dir = repo_root / spec["replay_dir"] / "j"
    out_dir = repo_root / output_dir_arg if output_dir_arg else repo_root / spec["default_output"]
    eval_j_dir = out_dir / "j"
    eval_j_dir.mkdir(parents=True, exist_ok=True)

    j_files = sorted(list(replay_j_dir.glob("*.json")))

    eval_journals: list[dict[str, Any]] = []
    executed_pairs = 0
    executed_executions = 0
    skipped_pairs = 0
    seen_cell_ids: set[str] = set()
    duplicate_count = 0

    worker = PersistentEvalWorker(per_cell_timeout=3.0)

    try:
        for j_file in j_files:
            rj = json.loads(j_file.read_text(encoding="utf-8"))
            tid = str(rj.get("task_id", ""))

            if dataset == "humaneval" and not tid.startswith("HumanEval"):
                continue
            if dataset == "mbpp" and not tid.startswith("Mbpp"):
                continue

            cid = str(rj.get("cell_identity", ""))
            if cid in seen_cell_ids:
                duplicate_count += 1
            seen_cell_ids.add(cid)

            ej_file = eval_j_dir / f"{cid}.json"

            if resume and ej_file.is_file():
                try:
                    existing = json.loads(ej_file.read_text(encoding="utf-8"))
                    if existing.get("persisted_complete") is True:
                        skipped_pairs += 1
                        eval_journals.append(existing)
                        continue
                except Exception:
                    pass

            ep = str(rj.get("entry_point", ""))
            ds_type = "humaneval" if tid.startswith("HumanEval") else "mbpp"
            raw_src = rj.get("raw_source", "") or ""
            final_src = rj.get("final_source", "") or ""

            raw_base, raw_plus, raw_final = worker.evaluate(ds_type, tid, ep, raw_src)
            cum_base, cum_plus, cum_final = worker.evaluate(ds_type, tid, ep, final_src)
            executed_executions += 2

            layers_changed = rj.get("layers_changed") or []
            modified = bool(layers_changed)
            abstention_reasons = rj.get("abstention_reason_by_layer") or {}
            # any_layer_abstained is schema-limited: the replay journal
            # stores each layer's reason string, not a dedicated abstained
            # boolean. We can only distinguish "some rule engaged and
            # declined" (any non-empty reason, when nothing was modified)
            # from "no engagement at all"; a per-layer abstained/no-trigger
            # split is unavailable without re-deriving each rule's internal
            # status, which this runner does not do.
            if not abstention_reason_by_layer_available(rj):
                any_layer_abstained = None
            else:
                any_layer_abstained = any(
                    v not in (None, "") for v in abstention_reasons.values()
                ) and not modified

            transition = classify_transition(
                modified=modified,
                raw_base_pass=raw_base,
                raw_plus_pass=raw_plus,
                raw_final_pass=raw_final,
                cumulative_base_pass=cum_base,
                cumulative_plus_pass=cum_plus,
                cumulative_final_pass=cum_final,
                any_layer_abstained=bool(any_layer_abstained),
            )

            ej = {
                "cell_identity": cid,
                "model_tag": model,
                "dataset": ds_type,
                "task_id": tid,
                "treatment": rj.get("treatment"),
                "generation_id": rj.get("generation_id"),
                "raw_sha256": rj.get("raw_sha256"),
                "post_h1_sha256": rj.get("post_h1_sha256"),
                "post_h2_sha256": rj.get("post_h2_sha256"),
                "post_h3_sha256": rj.get("post_h3_sha256"),
                "post_h4_sha256": rj.get("post_h4_sha256"),
                "final_sha256": rj.get("final_sha256"),
                "layers_invoked": rj.get("layers_invoked"),
                "layers_changed": layers_changed,
                "rules_triggered": rj.get("rules_triggered"),
                "rules_applied": rj.get("rules_applied"),
                "abstention_reason_by_layer": abstention_reasons,
                "first_effective_rule": rj.get("first_effective_rule"),
                "raw_parse_status": rj.get("raw_parse_status"),
                "cumulative_parse_status": rj.get("cumulative_parse_status"),
                "raw_execution_status": "unavailable",
                "cumulative_execution_status": "unavailable",
                "raw_base_pass": raw_base,
                "raw_plus_pass": raw_plus,
                "raw_final_pass": raw_final,
                "cumulative_base_pass": cum_base,
                "cumulative_plus_pass": cum_plus,
                "cumulative_final_pass": cum_final,
                "transition_category": transition,
                "persisted_complete": True,
                "runner_identity": "public_benchmark_h1_h2_h3_h4_evalplus_runner_v1",
                "experiment_label": "cumulative_H1_H4_candidate_replay",
            }
            durable_write_json_new(ej_file, ej)
            executed_pairs += 1
            eval_journals.append(ej)
    finally:
        worker.close()

    _require(duplicate_count == 0, f"duplicate cell_identity detected: {duplicate_count}")

    total_pairs = len(eval_journals)
    transition_counts = {c: 0 for c in TRANSITION_CATEGORIES}
    for ej in eval_journals:
        cat = ej.get("transition_category")
        if cat in transition_counts:
            transition_counts[cat] += 1

    summary = {
        "status": "cumulative_evalplus_execution_completed",
        "experiment_label": "cumulative_H1_H4_candidate_replay",
        "model_tag": model,
        "dataset": dataset,
        "evalplus_version": EXPECTED_EVALPLUS_VERSION,
        "output_directory": out_dir.as_posix(),
        "total_pairs": total_pairs,
        "total_executions": executed_executions + (skipped_pairs * 2 if skipped_pairs else 0),
        "expected_pairs": dry_audit["planned_pairs"],
        "expected_executions": dry_audit["planned_executions"],
        "missing": 0,
        "duplicate": duplicate_count,
        "executed_pairs": executed_pairs,
        "skipped_resume_pairs": skipped_pairs,
        "model_calls": 0,
        "evalplus_executed": True,
        "transition_counts": transition_counts,
    }

    summary_path = out_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    ledger_path = out_dir / "cell_level_ledger.csv"
    with ledger_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "cell_identity", "task_id", "treatment",
                "raw_final_pass", "cumulative_final_pass", "transition_category",
            ]
        )
        for ej in eval_journals:
            writer.writerow(
                [
                    ej["cell_identity"], ej["task_id"], ej["treatment"],
                    ej["raw_final_pass"], ej["cumulative_final_pass"], ej["transition_category"],
                ]
            )

    manifest_path = out_dir / "execution_manifest.json"
    manifest_data = {
        "plan_id": f"{spec['model_key']}_h1_h2_h3_h4_full_evalplus_v1",
        "experiment_label": "cumulative_H1_H4_candidate_replay",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "model_tag": model,
        "dataset": dataset,
        "evalplus_version": EXPECTED_EVALPLUS_VERSION,
        "total_pairs": total_pairs,
        "model_calls": 0,
        "evalplus_executed": True,
    }
    manifest_path.write_text(json.dumps(manifest_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return summary


def abstention_reason_by_layer_available(rj: dict[str, Any]) -> bool:
    return isinstance(rj.get("abstention_reason_by_layer"), dict) and bool(rj.get("abstention_reason_by_layer"))


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
        result = run_dry_run(model=args.model, dataset=args.dataset, output_dir_arg=args.output_dir)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

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
