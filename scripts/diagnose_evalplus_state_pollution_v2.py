"""Re-evaluate the five suspected v1 regressions with isolated evaluator v2."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import pathlib
import sys
from datetime import datetime, timezone
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.evalplus_isolated_evaluator_v2 import IsolatedEvalPlusEvaluatorV2

DEFAULT_OUTPUT = pathlib.Path(
    "artifacts/public_benchmark_governance/evalplus_state_pollution_diagnosis_v2"
)
TARGETS = (
    ("qwen3.5:4b", "251ddd15a1217e7e940e0365e29c5fca3d6effb32433516f6ca45203f0189a26"),
    ("qwen3.5:4b", "c7e7b62bf09a3ea8f930f28540195b40d64fe79b62418b7733054f10281cc590"),
    ("qwen3.5:9b", "80f3248946afc14a809633467ed074220cb5dc1ff21606ca68cd41531bb1e3dd"),
    ("qwen3.5:9b", "d543e43c0eae75e2fe7bc6b608ffac3f88ede04dec6743f284e313819c7b20b1"),
    ("qwen3.5:9b", "ed3eff9be1754a7aa4348d6aebc182acaf9cbdb046829ac03c57809a2409c724"),
)


def _tag(model: str) -> str:
    return "qwen35_4b" if model.endswith("4b") else "qwen35_9b"


def _result_dict(result) -> dict[str, Any]:
    return {
        "base_pass": result.base_pass,
        "plus_pass": result.plus_pass,
        "final_pass": result.final_pass,
        "base_status": result.base_status,
        "plus_status": result.plus_status,
    }


def _v1_result(item: dict[str, Any], prefix: str) -> dict[str, bool]:
    return {
        "base_pass": bool(item[f"{prefix}_base_pass"]),
        "plus_pass": bool(item[f"{prefix}_plus_pass"]),
        "final_pass": bool(item[f"{prefix}_final_pass"]),
    }


def diagnose(repo_root: pathlib.Path = REPO_ROOT) -> dict[str, Any]:
    evaluator = IsolatedEvalPlusEvaluatorV2()
    rows = []
    for model, cell_id in TARGETS:
        tag = _tag(model)
        replay_path = (
            repo_root
            / "artifacts/public_benchmark_governance"
            / f"{tag}_h1_h2_h3_h4_full_replay_v1/j/{cell_id}.json"
        )
        v1_path = (
            repo_root
            / "artifacts/public_benchmark_governance"
            / f"{tag}_h1_h2_h3_h4_full_evalplus_v1/j/{cell_id}.json"
        )
        replay = json.loads(replay_path.read_text(encoding="utf-8"))
        v1 = json.loads(v1_path.read_text(encoding="utf-8"))
        raw_source = replay["raw_source"]
        final_source = replay["final_source"]
        raw_sha = hashlib.sha256(raw_source.encode("utf-8")).hexdigest()
        final_sha = hashlib.sha256(final_source.encode("utf-8")).hexdigest()
        if raw_sha != replay["raw_sha256"] or final_sha != replay["final_sha256"]:
            raise RuntimeError(f"source hash drift: {cell_id}")
        task_id = replay["task_id"]
        entry_point = replay["entry_point"]

        raw_first = evaluator.evaluate("mbpp", task_id, entry_point, raw_source)
        final_second = evaluator.evaluate("mbpp", task_id, entry_point, final_source)
        final_first = evaluator.evaluate("mbpp", task_id, entry_point, final_source)
        raw_second = evaluator.evaluate("mbpp", task_id, entry_point, raw_source)
        raw_stable = raw_first == raw_second
        final_stable = final_first == final_second
        order_invariant = raw_stable and final_stable
        if not order_invariant:
            conclusion = "v2_isolation_failure"
        elif raw_first.final_pass and not final_first.final_pass:
            conclusion = "true_regression"
        elif v1["transition_category"] == "regression":
            conclusion = "evaluator_artifact"
        else:
            conclusion = "v1_v2_agree_non_regression"

        rows.append(
            {
                "model": model,
                "cell_identity": cell_id,
                "task_id": task_id,
                "treatment": replay["treatment"],
                "raw_sha256": raw_sha,
                "final_sha256": final_sha,
                "sources_identical": raw_source == final_source,
                "layers_changed": replay.get("layers_changed") or [],
                "v1": {
                    "raw": _v1_result(v1, "raw"),
                    "final": _v1_result(v1, "cumulative"),
                    "transition": v1["transition_category"],
                },
                "v2_raw_then_final": {
                    "raw": _result_dict(raw_first),
                    "final": _result_dict(final_second),
                },
                "v2_final_then_raw": {
                    "final": _result_dict(final_first),
                    "raw": _result_dict(raw_second),
                },
                "order_invariant": order_invariant,
                "conclusion": conclusion,
            }
        )
    return {
        "diagnosis_id": "evalplus_state_pollution_diagnosis_v2",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "evalplus_version": "0.3.1",
        "isolation": "evalplus.check_correctness->untrusted_check->fresh_process",
        "model_calls": 0,
        "replay_executed": False,
        "cells": rows,
        "counts": {
            name: sum(row["conclusion"] == name for row in rows)
            for name in (
                "true_regression",
                "evaluator_artifact",
                "v2_isolation_failure",
                "v1_v2_agree_non_regression",
            )
        },
    }


def write_outputs(result: dict[str, Any], output_dir: pathlib.Path) -> None:
    if not output_dir.name.endswith("_v2"):
        raise RuntimeError("diagnostic output directory name must end in _v2")
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output_dir}")
    output_dir.mkdir(parents=True)
    (output_dir / "diagnosis_v2.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with (output_dir / "diagnosis_v2.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "model",
                "task_id",
                "treatment",
                "raw_sha256",
                "final_sha256",
                "layers_changed",
                "v1_raw_final_pass",
                "v1_final_final_pass",
                "v2_raw_final_pass",
                "v2_final_final_pass",
                "order_invariant",
                "conclusion",
            ]
        )
        for row in result["cells"]:
            writer.writerow(
                [
                    row["model"],
                    row["task_id"],
                    row["treatment"],
                    row["raw_sha256"],
                    row["final_sha256"],
                    "|".join(row["layers_changed"]),
                    row["v1"]["raw"]["final_pass"],
                    row["v1"]["final"]["final_pass"],
                    row["v2_raw_then_final"]["raw"]["final_pass"],
                    row["v2_raw_then_final"]["final"]["final_pass"],
                    row["order_invariant"],
                    row["conclusion"],
                ]
            )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args(argv)
    if not args.execute:
        parser.error("--execute is required for the focused five-cell diagnosis")
    output_dir = pathlib.Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = REPO_ROOT / output_dir
    result = diagnose()
    write_outputs(result, output_dir)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
