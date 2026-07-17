#!/usr/bin/env python3
"""Build deterministic Milestone 2B P0/P1 paired development analysis."""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import io
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_tools.finals_rebuild.ollama_generation_runner import (  # noqa: E402
    detect_reasoning_leakage,
)
from scripts import build_mbpp_development_failure_census as census_v1  # noqa: E402
from scripts import build_mbpp_scaffold_healer_evidence_packets as evidence_v1  # noqa: E402


P0_RUN_ID = "mbpp_qwen35_9b_ab1_dev_run_003"
P1_RUN_ID = "mbpp_qwen35_9b_scaffold_v0_dev_run_002"
P0_RELATIVE = Path(
    "artifacts/public_benchmark_development/mbpp_qwen35_9b_ab1/runs/"
    "mbpp_qwen35_9b_ab1_dev_run_003"
)
P1_RELATIVE = Path("artifacts/pbd/mbpp_sv0/r002")
OUTPUT_RELATIVE = P1_RELATIVE / "milestone_2b_paired_analysis"

EXPECTED_SOURCE_HASHES = {
    "p0/generation_plan.json": "3c4e61db0588bd237e415f7cb0b8fde05d3db67c19a012968a4d676e37a56be5",
    "p0/raw_generations.jsonl": "24cc22a57f252f46a633dba34d53652398f0b2cf213363af774b82f90bcc9964",
    "p0/pipeline_corrected.jsonl": "4a8015fec50b4dd1e0d432f66bb01d6972dc2ed73ec748a36773bed2b10531fa",
    "p0/evaluation_results.csv": "86525489640c2076dfd4d35e7224a975ca0b5770fe8ad99019476b4d0c1ed54d",
    "p0/failure_census.csv": "d6df0132893927b36aa1bdb58fbee00fe660be7cd0745ba3c6fd5c4960b59c94",
    "p0/scaffold_evidence_ledger.csv": "ea71e31175e72fc9146299dc2172ec85b8a6cb5c75bbbff55d5533305023f6ad",
    "p1/generation_plan.json": "da9875857782711b46b3116bc5d21421bdfdd3dd71f5b2dc9bb5a37805ccec13",
    "p1/raw_generations.jsonl": "42625c93bc68ed736cb865aa35dc02bda8dce1172c6f5ade1bde1c0525c455c7",
    "p1/pipeline_corrected.jsonl": "4bdf90e08e8060c81756d63334d0df4b976205159349ea81472c66c6cc15204d",
    "p1/evaluation_results.csv": "6c1a73cfba4b03db9b970b3411d1536b21dfd1333579cb75408176c34e69742a",
    "p1/evaluation_summary.md": "66583a8d43f486a17df4e6a2f2621d7b58aba2aae5b0002a94bdef185375fb95",
    "p1/first_attempt_recovery_manifest.json": "138290888eb714a8f9d9e524f71ab80d0e59d83df52d5f073636d5adac52809f",
}

SOURCE_PATHS = {
    "p0/generation_plan.json": P0_RELATIVE / "generation_plan.json",
    "p0/raw_generations.jsonl": P0_RELATIVE / "raw_generations.jsonl",
    "p0/pipeline_corrected.jsonl": P0_RELATIVE / "pipeline_corrected.jsonl",
    "p0/evaluation_results.csv": P0_RELATIVE / "evaluation_results.csv",
    "p0/failure_census.csv": P0_RELATIVE / "milestone_1c_failure_census/failure_census.csv",
    "p0/scaffold_evidence_ledger.csv": P0_RELATIVE
    / "milestone_1d_evidence_review/scaffold_evidence_ledger.csv",
    "p1/generation_plan.json": P1_RELATIVE / "generation_plan.json",
    "p1/raw_generations.jsonl": P1_RELATIVE / "raw_generations.jsonl",
    "p1/pipeline_corrected.jsonl": P1_RELATIVE / "pipeline_corrected.jsonl",
    "p1/evaluation_results.csv": P1_RELATIVE / "evaluation_results.csv",
    "p1/evaluation_summary.md": P1_RELATIVE / "evaluation_summary.md",
    "p1/first_attempt_recovery_manifest.json": P1_RELATIVE
    / "first_attempt_recovery_manifest.json",
}

CATEGORY_ORDER = census_v1.CATEGORIES
CENSUS_FIELDS = census_v1.CSV_FIELDS
TRANSITIONS = ("fail_to_fail", "fail_to_pass", "pass_to_fail", "pass_to_pass")

PAIRED_FIELDS = (
    "task_id",
    "seed",
    "p0_generation_id",
    "p1_generation_id",
    "p0_observed_status",
    "p1_observed_status",
    "observed_transition",
    "observed_scaffold_rescue",
    "observed_scaffold_regression",
    "p0_pipeline_status",
    "p1_pipeline_status",
    "pipeline_transition",
    "pipeline_scaffold_rescue",
    "pipeline_scaffold_regression",
    "p0_raw_response_sha256",
    "p1_raw_response_sha256",
    "p0_strict_python_only_compliant",
    "p1_strict_python_only_compliant",
    "p0_code_fence_marker_count",
    "p1_code_fence_marker_count",
    "p0_extra_text_outside_fences",
    "p1_extra_text_outside_fences",
    "p0_multiple_program_segments",
    "p1_multiple_program_segments",
    "p0_generation_truncated",
    "p1_generation_truncated",
    "p0_extraction_action",
    "p1_extraction_action",
    "p0_raw_compile_status",
    "p1_raw_compile_status",
    "p0_pipeline_compile_status",
    "p1_pipeline_compile_status",
    "p0_raw_entry_point_status",
    "p1_raw_entry_point_status",
    "p0_pipeline_entry_point_status",
    "p1_pipeline_entry_point_status",
    "p0_reasoning_leakage",
    "p1_reasoning_leakage",
)


class PairedAnalysisError(RuntimeError):
    """Raised before output when paired inputs or deterministic evidence drift."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PairedAnalysisError(message)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _index_pair(rows: Iterable[dict[str, Any]], label: str) -> dict[tuple[str, int], dict[str, Any]]:
    indexed: dict[tuple[str, int], dict[str, Any]] = {}
    for row in rows:
        key = (str(row["task_id"]), int(row["seed"]))
        _require(key not in indexed, f"{label}: duplicate task/seed pair {key}")
        indexed[key] = row
    return indexed


def _entry_point_status(source: str | None, entry_point: str) -> str:
    if source is None:
        return "extraction_failed"
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError, OverflowError):
        return "not_assessed_compile_fail"
    names = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }
    return "present" if entry_point in names else "missing"


def _bool(value: bool) -> str:
    return str(value).lower()


def _transition(before: str, after: str) -> str:
    _require(before in {"pass", "fail"} and after in {"pass", "fail"}, "invalid status")
    return f"{before}_to_{after}"


def exact_mcnemar_p(fail_to_pass: int, pass_to_fail: int) -> float:
    """Two-sided exact conditional binomial McNemar p-value."""
    discordant = fail_to_pass + pass_to_fail
    if discordant == 0:
        return 1.0
    tail = sum(
        math.comb(discordant, index) for index in range(min(fail_to_pass, pass_to_fail) + 1)
    ) / (2**discordant)
    return min(1.0, 2.0 * tail)


def _integer_beta_cdf(value: float, alpha: int, beta: int) -> float:
    """Regularized incomplete beta for positive integer shape parameters."""
    if value <= 0.0:
        return 0.0
    if value >= 1.0:
        return 1.0
    total = alpha + beta - 1
    return math.fsum(
        math.comb(total, index)
        * value**index
        * (1.0 - value) ** (total - index)
        for index in range(alpha, total + 1)
    )


def _beta_quantile(probability: float, alpha: int, beta: int) -> float:
    low, high = 0.0, 1.0
    for _ in range(100):
        midpoint = (low + high) / 2.0
        if _integer_beta_cdf(midpoint, alpha, beta) < probability:
            low = midpoint
        else:
            high = midpoint
    return (low + high) / 2.0


def clopper_pearson(successes: int, trials: int, alpha: float = 0.05) -> tuple[float, float]:
    _require(0 <= successes <= trials and trials > 0, "invalid binomial count")
    lower = 0.0 if successes == 0 else _beta_quantile(alpha / 2, successes, trials - successes + 1)
    upper = (
        1.0
        if successes == trials
        else _beta_quantile(1 - alpha / 2, successes + 1, trials - successes)
    )
    return lower, upper


def paired_statistics(counts: Counter[str], total: int = 100) -> dict[str, Any]:
    gains = counts["fail_to_pass"]
    losses = counts["pass_to_fail"]
    discordant = gains + losses
    result: dict[str, Any] = {
        "discordant_pairs": discordant,
        "fail_to_pass": gains,
        "pass_to_fail": losses,
        "net_change_cells": gains - losses,
        "paired_risk_difference": (gains - losses) / total,
        "exact_mcnemar_two_sided_p": exact_mcnemar_p(gains, losses),
    }
    if discordant:
        lower, upper = clopper_pearson(gains, discordant)
        result.update(
            {
                "discordant_superiority_probability": gains / discordant,
                "discordant_superiority_exact_95ci": [lower, upper],
                "matched_pairs_odds_ratio": "infinity" if losses == 0 else gains / losses,
                "matched_pairs_odds_ratio_exact_95ci": [
                    lower / (1.0 - lower) if lower < 1.0 else "infinity",
                    upper / (1.0 - upper) if upper < 1.0 else "infinity",
                ],
            }
        )
    else:
        result.update(
            {
                "discordant_superiority_probability": None,
                "discordant_superiority_exact_95ci": None,
                "matched_pairs_odds_ratio": None,
                "matched_pairs_odds_ratio_exact_95ci": None,
            }
        )
    return result


def _feature_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "cells": len(rows),
        "strict_python_only_compliant": sum(row["strict"] for row in rows),
        "code_fence": sum(row["features"]["marker_count"] > 0 for row in rows),
        "extra_text_outside_fences": sum(row["features"]["extra_text"] for row in rows),
        "multiple_program_segments": sum(row["features"]["multiple"] for row in rows),
        "generation_truncated": sum(row["features"]["truncated"] for row in rows),
        "raw_compile_pass": sum(row["features"]["compile_status"] == "pass" for row in rows),
        "raw_compile_fail": sum(row["features"]["compile_status"] == "fail" for row in rows),
        "pipeline_compile_status": dict(
            sorted(Counter(row["pipeline_compile"] for row in rows).items())
        ),
        "reasoning_leakage": sum(row["reasoning"] for row in rows),
        "extraction_actions": dict(sorted(Counter(row["action"] for row in rows).items())),
        "raw_entry_point_status": dict(
            sorted(Counter(row["raw_entry"] for row in rows).items())
        ),
        "pipeline_entry_point_status": dict(
            sorted(Counter(row["pipeline_entry"] for row in rows).items())
        ),
    }


def _fmt_number(value: Any) -> str:
    if value == "infinity":
        return "∞"
    if value is None:
        return "NA"
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def _render_csv(rows: list[dict[str, str]], fields: tuple[str, ...]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def _render_json(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def build_analysis(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    source_hashes = {
        label: _sha256_bytes((repo_root / SOURCE_PATHS[label]).read_bytes())
        for label in SOURCE_PATHS
    }
    _require(source_hashes == EXPECTED_SOURCE_HASHES, "source artifact hash mismatch")
    p0_dir, p1_dir = repo_root / P0_RELATIVE, repo_root / P1_RELATIVE
    p0_plan = json.loads((p0_dir / "generation_plan.json").read_text(encoding="utf-8"))
    p1_plan = json.loads((p1_dir / "generation_plan.json").read_text(encoding="utf-8"))
    _require(p0_plan["run_id"] == P0_RUN_ID and p1_plan["run_id"] == P1_RUN_ID, "run ID mismatch")
    _require(p0_plan["task_ids"] == p1_plan["task_ids"], "P0/P1 task order mismatch")
    _require(p0_plan["seeds"] == p1_plan["seeds"] == [11, 22, 33, 44, 55], "seed mismatch")
    _require(p0_plan["expected_cells"] == p1_plan["expected_cells"] == 100, "cell plan mismatch")

    p0_raw = _read_jsonl(p0_dir / "raw_generations.jsonl")
    p1_raw = _read_jsonl(p1_dir / "raw_generations.jsonl")
    p0_pipeline = _read_jsonl(p0_dir / "pipeline_corrected.jsonl")
    p1_pipeline = _read_jsonl(p1_dir / "pipeline_corrected.jsonl")
    p0_eval = _read_csv(p0_dir / "evaluation_results.csv")
    p1_eval = _read_csv(p1_dir / "evaluation_results.csv")
    for label, rows in (
        ("P0 raw", p0_raw),
        ("P1 raw", p1_raw),
        ("P0 pipeline", p0_pipeline),
        ("P1 pipeline", p1_pipeline),
        ("P0 evaluation", p0_eval),
        ("P1 evaluation", p1_eval),
    ):
        _require(len(rows) == 100, f"{label} row count mismatch")

    indexes = {
        "p0_raw": _index_pair(p0_raw, "P0 raw"),
        "p1_raw": _index_pair(p1_raw, "P1 raw"),
        "p0_pipeline": _index_pair(p0_pipeline, "P0 pipeline"),
        "p1_pipeline": _index_pair(p1_pipeline, "P1 pipeline"),
        "p0_eval": _index_pair(p0_eval, "P0 evaluation"),
        "p1_eval": _index_pair(p1_eval, "P1 evaluation"),
    }
    expected_pairs = {
        (task_id, seed) for task_id in p0_plan["task_ids"] for seed in p0_plan["seeds"]
    }
    _require(all(set(index) == expected_pairs for index in indexes.values()), "paired identity mismatch")
    entry_points = census_v1._load_entry_points(repo_root, p0_plan["task_ids"])

    paired_rows: list[dict[str, str]] = []
    feature_rows: dict[str, list[dict[str, Any]]] = {"p0": [], "p1": []}
    transition_counts = {"observed": Counter(), "pipeline": Counter()}
    task_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for task_id in p0_plan["task_ids"]:
        for seed in p0_plan["seeds"]:
            key = (task_id, seed)
            raw0, raw1 = indexes["p0_raw"][key], indexes["p1_raw"][key]
            pipe0, pipe1 = indexes["p0_pipeline"][key], indexes["p1_pipeline"][key]
            eval0, eval1 = indexes["p0_eval"][key], indexes["p1_eval"][key]
            for raw, evaluation, label in ((raw0, eval0, "P0"), (raw1, eval1, "P1")):
                _require(
                    _sha256_text(raw["raw_response"]) == raw["raw_response_sha256"],
                    f"{label} raw response SHA mismatch",
                )
                _require(
                    evaluation["observed_output_sha256"] == raw["raw_response_sha256"],
                    f"{label} observed evaluation hash mismatch",
                )
            for raw, pipe, evaluation, label in (
                (raw0, pipe0, eval0, "P0"),
                (raw1, pipe1, eval1, "P1"),
            ):
                _require(
                    pipe["source_raw_response_sha256"] == raw["raw_response_sha256"],
                    f"{label} pipeline source hash mismatch",
                )
                _require(
                    evaluation["pipeline_corrected_output_sha256"]
                    == (pipe["pipeline_corrected_output_sha256"] or ""),
                    f"{label} pipeline evaluation hash mismatch",
                )

            features0, features1 = evidence_v1._raw_features(raw0), evidence_v1._raw_features(raw1)
            reasoning0 = detect_reasoning_leakage(
                json.loads(raw0["raw_http_response_body"]), raw0["raw_response"]
            )
            reasoning1 = detect_reasoning_leakage(
                json.loads(raw1["raw_http_response_body"]), raw1["raw_response"]
            )
            strict0, strict1 = features0["compliant"] and not reasoning0, features1["compliant"] and not reasoning1
            raw_entry0 = _entry_point_status(raw0["raw_response"], entry_points[task_id])
            raw_entry1 = _entry_point_status(raw1["raw_response"], entry_points[task_id])
            pipeline_entry0 = _entry_point_status(
                pipe0["pipeline_corrected_output"], entry_points[task_id]
            )
            pipeline_entry1 = _entry_point_status(
                pipe1["pipeline_corrected_output"], entry_points[task_id]
            )
            action0, action1 = evidence_v1._pipeline_action(pipe0), evidence_v1._pipeline_action(pipe1)
            for label, features, reasoning, strict, action, raw_entry, pipeline_entry, pipeline_compile in (
                (
                    "p0",
                    features0,
                    reasoning0,
                    strict0,
                    action0,
                    raw_entry0,
                    pipeline_entry0,
                    eval0["pipeline_corrected_syntax_compile_status"],
                ),
                (
                    "p1",
                    features1,
                    reasoning1,
                    strict1,
                    action1,
                    raw_entry1,
                    pipeline_entry1,
                    eval1["pipeline_corrected_syntax_compile_status"],
                ),
            ):
                feature_rows[label].append(
                    {
                        "features": features,
                        "reasoning": reasoning,
                        "strict": strict,
                        "action": action,
                        "raw_entry": raw_entry,
                        "pipeline_entry": pipeline_entry,
                        "pipeline_compile": pipeline_compile,
                    }
                )
            observed_transition = _transition(eval0["observed_status"], eval1["observed_status"])
            pipeline_transition = _transition(
                eval0["pipeline_corrected_status"], eval1["pipeline_corrected_status"]
            )
            transition_counts["observed"][observed_transition] += 1
            transition_counts["pipeline"][pipeline_transition] += 1
            for prefix, evaluation in (("p0", eval0), ("p1", eval1)):
                task_counts[task_id][f"{prefix}_observed"] += evaluation["observed_status"] == "pass"
                task_counts[task_id][f"{prefix}_pipeline"] += (
                    evaluation["pipeline_corrected_status"] == "pass"
                )
            paired_rows.append(
                {
                    "task_id": task_id,
                    "seed": str(seed),
                    "p0_generation_id": raw0["generation_id"],
                    "p1_generation_id": raw1["generation_id"],
                    "p0_observed_status": eval0["observed_status"],
                    "p1_observed_status": eval1["observed_status"],
                    "observed_transition": observed_transition,
                    "observed_scaffold_rescue": _bool(observed_transition == "fail_to_pass"),
                    "observed_scaffold_regression": _bool(observed_transition == "pass_to_fail"),
                    "p0_pipeline_status": eval0["pipeline_corrected_status"],
                    "p1_pipeline_status": eval1["pipeline_corrected_status"],
                    "pipeline_transition": pipeline_transition,
                    "pipeline_scaffold_rescue": _bool(pipeline_transition == "fail_to_pass"),
                    "pipeline_scaffold_regression": _bool(pipeline_transition == "pass_to_fail"),
                    "p0_raw_response_sha256": raw0["raw_response_sha256"],
                    "p1_raw_response_sha256": raw1["raw_response_sha256"],
                    "p0_strict_python_only_compliant": _bool(strict0),
                    "p1_strict_python_only_compliant": _bool(strict1),
                    "p0_code_fence_marker_count": str(features0["marker_count"]),
                    "p1_code_fence_marker_count": str(features1["marker_count"]),
                    "p0_extra_text_outside_fences": _bool(features0["extra_text"]),
                    "p1_extra_text_outside_fences": _bool(features1["extra_text"]),
                    "p0_multiple_program_segments": _bool(features0["multiple"]),
                    "p1_multiple_program_segments": _bool(features1["multiple"]),
                    "p0_generation_truncated": _bool(features0["truncated"]),
                    "p1_generation_truncated": _bool(features1["truncated"]),
                    "p0_extraction_action": action0,
                    "p1_extraction_action": action1,
                    "p0_raw_compile_status": features0["compile_status"],
                    "p1_raw_compile_status": features1["compile_status"],
                    "p0_pipeline_compile_status": eval0["pipeline_corrected_syntax_compile_status"],
                    "p1_pipeline_compile_status": eval1["pipeline_corrected_syntax_compile_status"],
                    "p0_raw_entry_point_status": raw_entry0,
                    "p1_raw_entry_point_status": raw_entry1,
                    "p0_pipeline_entry_point_status": pipeline_entry0,
                    "p1_pipeline_entry_point_status": pipeline_entry1,
                    "p0_reasoning_leakage": _bool(reasoning0),
                    "p1_reasoning_leakage": _bool(reasoning1),
                }
            )

    _require(len(paired_rows) == 100, "paired row count mismatch")
    _require(transition_counts["observed"] == {"fail_to_fail": 70, "fail_to_pass": 30}, "Observed transition mismatch")
    _require(
        transition_counts["pipeline"]
        == {"fail_to_fail": 53, "fail_to_pass": 17, "pass_to_fail": 17, "pass_to_pass": 13},
        "Pipeline transition mismatch",
    )
    format_summary = {
        "p0": _feature_summary(feature_rows["p0"]),
        "p1": _feature_summary(feature_rows["p1"]),
    }
    _require(format_summary["p1"]["reasoning_leakage"] == 1, "P1 leakage count mismatch")

    p1_census_rows: list[dict[str, str]] = []
    for row in paired_rows:
        if row["p1_pipeline_status"] != "fail":
            continue
        key = (row["task_id"], int(row["seed"]))
        raw = indexes["p1_raw"][key]
        pipeline = indexes["p1_pipeline"][key]
        evaluation = indexes["p1_eval"][key]
        classification = census_v1._classify(pipeline, evaluation, entry_points[row["task_id"]])
        p1_census_rows.append(
            {
                "task_id": row["task_id"],
                "seed": row["seed"],
                "cell_id": raw["generation_id"],
                "raw_generation_sha256": raw["raw_response_sha256"],
                "extracted_program_sha256": pipeline["pipeline_corrected_output_sha256"] or "",
                "pipeline_extracted": _bool(pipeline["extraction_status"] == "extracted"),
                "observed_status": evaluation["observed_status"],
                "pipeline_status": evaluation["pipeline_corrected_status"],
                "failure_stage": classification["failure_stage"],
                "exception_type_or_evaluator_outcome": classification["outcome"],
                "failure_category": classification["category"],
                "classification_basis": classification["basis"],
                "scaffold_candidate": classification["scaffold"],
                "healer_candidate": classification["healer"],
                "semantic_risk": classification["risk"],
                "review_status": classification["review"],
            }
        )
    _require(len(p1_census_rows) == 70, "P1 failure census must contain 70 rows")
    p1_category_counts = Counter(row["failure_category"] for row in p1_census_rows)
    p0_census_rows = _read_csv(repo_root / SOURCE_PATHS["p0/failure_census.csv"])
    p0_category_counts = Counter(row["failure_category"] for row in p0_census_rows)
    category_pair_counts = Counter()
    p0_category_by_pair = {
        (row["task_id"], int(row["seed"])): row["failure_category"] for row in p0_census_rows
    }
    p1_category_by_pair = {
        (row["task_id"], int(row["seed"])): row["failure_category"] for row in p1_census_rows
    }
    for key in expected_pairs:
        category_pair_counts[
            f"{p0_category_by_pair.get(key, 'pipeline_pass')} -> "
            f"{p1_category_by_pair.get(key, 'pipeline_pass')}"
        ] += 1

    task_summary = []
    for task_id in p0_plan["task_ids"]:
        counts = task_counts[task_id]
        task_summary.append(
            {
                "task_id": task_id,
                "p0_observed_pass_seeds": counts["p0_observed"],
                "p1_observed_pass_seeds": counts["p1_observed"],
                "observed_delta": counts["p1_observed"] - counts["p0_observed"],
                "p0_pipeline_pass_seeds": counts["p0_pipeline"],
                "p1_pipeline_pass_seeds": counts["p1_pipeline"],
                "pipeline_delta": counts["p1_pipeline"] - counts["p0_pipeline"],
            }
        )

    result = {
        "source_hashes": source_hashes,
        "paired_rows": paired_rows,
        "p1_census_rows": p1_census_rows,
        "transition_counts": {
            account: {name: transition_counts[account][name] for name in TRANSITIONS}
            for account in ("observed", "pipeline")
        },
        "statistics": {
            account: paired_statistics(transition_counts[account])
            for account in ("observed", "pipeline")
        },
        "task_summary": task_summary,
        "format_summary": format_summary,
        "p0_category_counts": {name: p0_category_counts[name] for name in CATEGORY_ORDER},
        "p1_category_counts": {name: p1_category_counts[name] for name in CATEGORY_ORDER},
        "category_pair_counts": dict(sorted(category_pair_counts.items())),
    }
    return result


def _task_table(task_summary: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| task_id | Observed P0→P1 (Δ) | Pipeline P0→P1 (Δ) |",
        "|---|---:|---:|",
    ]
    for row in task_summary:
        lines.append(
            f"| {row['task_id']} | {row['p0_observed_pass_seeds']}→{row['p1_observed_pass_seeds']} "
            f"({row['observed_delta']:+d}) | {row['p0_pipeline_pass_seeds']}→"
            f"{row['p1_pipeline_pass_seeds']} ({row['pipeline_delta']:+d}) |"
        )
    return lines


def render_transition_summary(result: dict[str, Any]) -> bytes:
    lines = [
        "# Milestone 2B paired transition summary",
        "",
        "> MBPP+ active development exploratory analysis only; no external-generalization claim.",
        "",
    ]
    for account, title in (("observed", "Observed"), ("pipeline", "Pipeline-corrected")):
        counts, stats = result["transition_counts"][account], result["statistics"][account]
        ci = stats["discordant_superiority_exact_95ci"]
        lines.extend(
            [
                f"## {title}",
                "",
                "| P0 \\ P1 | fail | pass |",
                "|---|---:|---:|",
                f"| fail | {counts['fail_to_fail']} | {counts['fail_to_pass']} |",
                f"| pass | {counts['pass_to_fail']} | {counts['pass_to_pass']} |",
                "",
                f"- Paired rescues: {counts['fail_to_pass']}",
                f"- Paired regressions: {counts['pass_to_fail']}",
                f"- Net change: {stats['net_change_cells']:+d}/100 "
                f"({stats['paired_risk_difference'] * 100:+.1f} percentage points)",
                f"- Exact McNemar two-sided p: `{_fmt_number(stats['exact_mcnemar_two_sided_p'])}`",
                f"- Discordant superiority: `{_fmt_number(stats['discordant_superiority_probability'])}`; "
                f"exact 95% CI `{_fmt_number(ci[0]) if ci else 'NA'}`–"
                f"`{_fmt_number(ci[1]) if ci else 'NA'}`",
                f"- Matched-pairs odds ratio: `{_fmt_number(stats['matched_pairs_odds_ratio'])}`; "
                f"exact 95% CI `{_fmt_number(stats['matched_pairs_odds_ratio_exact_95ci'][0])}`–"
                f"`{_fmt_number(stats['matched_pairs_odds_ratio_exact_95ci'][1])}`",
                "",
            ]
        )
    lines.extend(["## Per-task five-seed pass counts", "", *_task_table(result["task_summary"]), ""])
    return "\n".join(lines).encode("utf-8")


def render_analysis_zh(result: dict[str, Any]) -> bytes:
    p0, p1 = result["format_summary"]["p0"], result["format_summary"]["p1"]
    observed, pipeline = result["transition_counts"]["observed"], result["transition_counts"]["pipeline"]
    lines = [
        "# MBPP+ Scaffold v0 development paired analysis（Milestone 2B）",
        "",
        "## 研究界線",
        "",
        "本報告只分析凍結的20題active development subset與既有P0/P1 artifacts。這是development exploratory analysis，不代表validation、confirmatory或外部泛化結果。Pipeline correction不是Healer；本輪沒有建置Healer或Scaffold v1，也沒有重新生成或重新評估。",
        "",
        "## 配對結論",
        "",
        f"- 以 `task_id + seed` 得到100組完整配對，無重複或缺漏。",
        f"- Observed：70 fail→fail、30 fail→pass、0 pass→fail、0 pass→pass；Scaffold paired rescues={observed['fail_to_pass']}、regressions={observed['pass_to_fail']}、net=+30。",
        f"- Pipeline-corrected：53 fail→fail、17 fail→pass、17 pass→fail、13 pass→pass；paired rescues={pipeline['fail_to_pass']}、regressions={pipeline['pass_to_fail']}、net=0。",
        "- P1的30個Pipeline成功不等於P0的30個成功：只有13個pass→pass，另有17個新成功與17個paired regressions。",
        "",
        "## Observed、Pipeline與Scaffold效果分離",
        "",
        "- **Observed effect**：直接通過由0/100升至30/100，且因P0無Observed pass，所以沒有Observed paired regression。",
        "- **Pipeline effect**：兩組皆為30/100，但逐格配對顯示17 rescue與17 regression；淨效果為0，不能以相同總數推論cells相同。",
        "- **Scaffold effect**：strict Python-only與直接可編譯性大幅提升，這支持『提升直接可評估性』；但沒有提升Pipeline-corrected correctness。",
        "- **Reasoning leakage**：P1有1格，是獨立protocol violation；該格仍按ITT保留，沒有算成合規、Healer或Pipeline rescue。",
        "",
        "## 格式與結構診斷（100 cells）",
        "",
        "| 指標 | P0 | P1 |",
        "|---|---:|---:|",
        f"| Strict Python-only compliant | {p0['strict_python_only_compliant']} | {p1['strict_python_only_compliant']} |",
        f"| Code fence | {p0['code_fence']} | {p1['code_fence']} |",
        f"| 額外文字（fence外） | {p0['extra_text_outside_fences']} | {p1['extra_text_outside_fences']} |",
        f"| 多段程式（多個完整fenced blocks） | {p0['multiple_program_segments']} | {p1['multiple_program_segments']} |",
        f"| Length termination／truncation | {p0['generation_truncated']} | {p1['generation_truncated']} |",
        f"| Raw compile pass | {p0['raw_compile_pass']} | {p1['raw_compile_pass']} |",
        f"| Pipeline compile status | `{json.dumps(p0['pipeline_compile_status'], sort_keys=True)}` | `{json.dumps(p1['pipeline_compile_status'], sort_keys=True)}` |",
        f"| Reasoning leakage | {p0['reasoning_leakage']} | {p1['reasoning_leakage']} |",
        "",
        f"P0 extraction actions：`{json.dumps(p0['extraction_actions'], sort_keys=True)}`。",
        f"P1 extraction actions：`{json.dumps(p1['extraction_actions'], sort_keys=True)}`；100格皆為既有plain-text pass-through。",
        "",
        f"P0 Pipeline entry-point status：`{json.dumps(p0['pipeline_entry_point_status'], sort_keys=True)}`。",
        f"P1 Pipeline entry-point status：`{json.dumps(p1['pipeline_entry_point_status'], sort_keys=True)}`。",
        "",
        "操作定義沿用Milestone 1D：strict compliance要求非空、無Markdown fence、無多段fenced program、無fence外文字、非length termination、raw可編譯，並在本分析額外要求無reasoning leakage。它衡量可直接交付Python parser的格式，不等於功能正確。",
        "",
        "## Failure census與signature比較",
        "",
        "| Taxonomy category | P0 Pipeline failures | P1 Pipeline failures |",
        "|---|---:|---:|",
    ]
    for category in CATEGORY_ORDER:
        lines.append(
            f"| {category} | {result['p0_category_counts'][category]} | "
            f"{result['p1_category_counts'][category]} |"
        )
    lines.extend(
        [
            "",
            "- Scaffold消除：code fence 96→0、fence外文字79→0、多段fenced programs 25→0、Pipeline extraction failures 21→0。",
            "- 仍存在：syntax failures 6→6；entry-point failures由17降至3；length termination由13降至8。",
            "- 新增／新暴露：reasoning leakage 0→1；此外Pipeline有17個paired correctness regressions。後者是結果轉移，不應推測成特定程式錯誤原因。",
            "- P1有61個`unknown`：saved evaluator diagnostics只表示generic failure，不能可靠區分functional assertion、runtime、import/name等原因，因此全部維持manual review。",
            "",
            "## 統計解讀",
            "",
            f"Observed exact McNemar p=`{_fmt_number(result['statistics']['observed']['exact_mcnemar_two_sided_p'])}`，paired risk difference=+30 percentage points。Pipeline exact McNemar p=`{_fmt_number(result['statistics']['pipeline']['exact_mcnemar_two_sided_p'])}`，paired risk difference=0。完整matched-pairs effect size與exact 95% CI見transition summary。",
            "",
            "這些cell共享task群組且來自development selection，p值與CI僅作探索性量化，不應解讀為獨立同分布母體抽樣或外部泛化證據。",
            "",
            "## v0治理判定",
            "",
            "Scaffold v0可以維持為**已凍結、已評估的development baseline artifact**，但目前不能提升為『已證明改善Pipeline correctness』的最終規則：Pipeline淨增益為0且存在17個paired regressions。若要變更提示，只能另提Scaffold v1候選並重新預註冊；本輪不修改v0，也不開始v1。",
            "",
            "## Per-task five-seed pass counts",
            "",
            *_task_table(result["task_summary"]),
            "",
        ]
    )
    return "\n".join(lines).encode("utf-8")


def build_outputs(repo_root: Path = REPO_ROOT) -> dict[Path, bytes]:
    result = build_analysis(repo_root)
    outputs: dict[Path, bytes] = {
        Path("paired_cell_comparison.csv"): _render_csv(result["paired_rows"], PAIRED_FIELDS),
        Path("paired_transition_summary.md"): render_transition_summary(result),
        Path("p1_failure_census.csv"): _render_csv(result["p1_census_rows"], CENSUS_FIELDS),
        Path("scaffold_v0_development_analysis_zh.md"): render_analysis_zh(result),
    }
    manifest = {
        "analysis_version": "milestone_2b_p0_p1_paired_development_v1",
        "scope": "MBPP+ frozen active development subset only",
        "analysis_design": "paired by task_id + seed",
        "exploratory_development_analysis": True,
        "external_generalization_claimed": False,
        "p0_run_id": P0_RUN_ID,
        "p1_run_id": P1_RUN_ID,
        "paired_cells": 100,
        "duplicate_pairs": 0,
        "missing_pairs": 0,
        "transition_counts": result["transition_counts"],
        "statistics": result["statistics"],
        "format_summary": result["format_summary"],
        "p0_failure_category_counts": result["p0_category_counts"],
        "p1_failure_category_counts": result["p1_category_counts"],
        "failure_category_pair_counts": result["category_pair_counts"],
        "p1_failure_census_rows": len(result["p1_census_rows"]),
        "reasoning_leakage_protocol_violations": 1,
        "pipeline_correction_is_healer": False,
        "model_calls": 0,
        "evalplus_executions": 0,
        "source_artifacts": {
            label: {
                "path": SOURCE_PATHS[label].as_posix(),
                "sha256": result["source_hashes"][label],
            }
            for label in sorted(SOURCE_PATHS)
        },
        "outputs": {
            path.as_posix(): {"sha256": _sha256_bytes(content), "size_bytes": len(content)}
            for path, content in sorted(outputs.items(), key=lambda item: item[0].as_posix())
        },
    }
    outputs[Path("paired_analysis_manifest.json")] = _render_json(manifest)
    return outputs


def write_outputs(repo_root: Path = REPO_ROOT) -> None:
    output_dir = repo_root.resolve() / OUTPUT_RELATIVE
    for relative, content in build_outputs(repo_root).items():
        path = output_dir / relative
        if path.exists():
            _require(path.read_bytes() == content, f"refusing output drift/overwrite: {relative}")
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    args = parser.parse_args()
    write_outputs(args.repo_root)
    print(json.dumps({"status": "built", "paired_cells": 100}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
