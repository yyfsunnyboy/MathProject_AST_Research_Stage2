#!/usr/bin/env python3
"""Build the evidence-limited Milestone 1C census for MBPP+ run_003."""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_RELATIVE = Path(
    "artifacts/public_benchmark_development/mbpp_qwen35_9b_ab1/runs/"
    "mbpp_qwen35_9b_ab1_dev_run_003"
)
OUTPUT_RELATIVE = RUN_RELATIVE / "milestone_1c_failure_census"
PROTOCOL_RELATIVE = Path("configs/public_benchmark_generation_protocol_v1.json")
FROZEN_SPLIT_RELATIVE = Path("artifacts/public_benchmark_governance/frozen_split.csv")
TASKS_RELATIVE = Path("data/mbpp_plus/tasks.jsonl")

EXPECTED_MODEL = "qwen3.5:9b"
EXPECTED_DIGEST = "6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7"
EXPECTED_SEEDS = [11, 22, 33, 44, 55]
EXPECTED_TASKS = 20
EXPECTED_CELLS = 100
EXPECTED_PIPELINE_FAILS = 70
EXPECTED_FAILED_TASKS = 19
EXPECTED_SOURCE_HASHES = {
    "generation_plan.json": "3c4e61db0588bd237e415f7cb0b8fde05d3db67c19a012968a4d676e37a56be5",
    "raw_generations.jsonl": "24cc22a57f252f46a633dba34d53652398f0b2cf213363af774b82f90bcc9964",
    "pipeline_corrected.jsonl": "4a8015fec50b4dd1e0d432f66bb01d6972dc2ed73ec748a36773bed2b10531fa",
    "evaluation_results.csv": "86525489640c2076dfd4d35e7224a975ca0b5770fe8ad99019476b4d0c1ed54d",
    "failure_census_summary.md": "d1731b037802610fbc9a43095c79b4f5d503916b74ef426400af33cacb7ed111",
}

CATEGORIES = (
    "extraction_or_format_failure",
    "syntax_failure",
    "missing_or_wrong_entry_point",
    "import_or_name_failure",
    "runtime_exception",
    "timeout_or_resource_failure",
    "functional_test_failure",
    "unknown",
)

CSV_FIELDS = (
    "task_id",
    "seed",
    "cell_id",
    "raw_generation_sha256",
    "extracted_program_sha256",
    "pipeline_extracted",
    "observed_status",
    "pipeline_status",
    "failure_stage",
    "exception_type_or_evaluator_outcome",
    "failure_category",
    "classification_basis",
    "scaffold_candidate",
    "healer_candidate",
    "semantic_risk",
    "review_status",
)


class CensusIntegrityError(RuntimeError):
    """Raised before any output is written when frozen inputs do not reconcile."""


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CensusIntegrityError(message)


def _index_unique(rows: Iterable[dict[str, Any]], label: str) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        generation_id = row.get("generation_id")
        _require(isinstance(generation_id, str) and generation_id, f"{label}: missing generation_id")
        _require(generation_id not in indexed, f"{label}: duplicate generation_id {generation_id}")
        indexed[generation_id] = row
    return indexed


def _load_entry_points(repo_root: Path, selected_ids: list[str]) -> dict[str, str]:
    """Retain only the model-visible fields for the permitted 20-task subset."""
    selected = set(selected_ids)
    found: dict[str, str] = {}
    with (repo_root / TASKS_RELATIVE).open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            task_id = record.get("task_id")
            if task_id not in selected:
                continue
            _require(
                set(record) == {"task_id", "prompt", "entry_point"},
                f"{task_id}: model-visible task schema drift",
            )
            found[task_id] = record["entry_point"]
    _require(set(found) == selected, "active development entry-point set mismatch")
    return found


def _defined_names(source: str) -> set[str]:
    tree = ast.parse(source)
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }


def _classify(
    pipeline: dict[str, Any], evaluation: dict[str, str], entry_point: str
) -> dict[str, str]:
    extracted = pipeline["extraction_status"] == "extracted"
    source = pipeline["pipeline_corrected_output"]
    if not extracted or source is None:
        return {
            "failure_stage": "pipeline_extraction",
            "outcome": "not_run_extraction_failed",
            "category": "extraction_or_format_failure",
            "basis": "saved extraction_status is not extracted and evaluator status is not_run_extraction_failed",
            "scaffold": "true",
            "healer": "false",
            "risk": "low",
            "review": "classified_from_saved_diagnostics",
        }
    if evaluation["pipeline_corrected_syntax_compile_status"] == "fail":
        return {
            "failure_stage": "syntax_compile",
            "outcome": "syntax_compile_fail",
            "category": "syntax_failure",
            "basis": "saved pipeline_corrected_syntax_compile_status is fail",
            "scaffold": "false",
            "healer": "true",
            "risk": "high",
            "review": "classified_from_saved_diagnostics",
        }
    try:
        names = _defined_names(source)
    except (SyntaxError, ValueError, OverflowError) as exc:
        raise CensusIntegrityError(
            f"{pipeline['generation_id']}: saved compile status conflicts with AST parse: {type(exc).__name__}"
        ) from exc
    if entry_point not in names:
        return {
            "failure_stage": "entry_point_static_check",
            "outcome": "expected_entry_point_not_defined",
            "category": "missing_or_wrong_entry_point",
            "basis": f"AST top-level definitions do not include frozen entry point {entry_point}",
            "scaffold": "false",
            "healer": "true",
            "risk": "high",
            "review": "classified_from_saved_diagnostics",
        }
    if evaluation["pipeline_corrected_runtime_timeout_status"] == "timeout":
        return {
            "failure_stage": "evalplus_execution",
            "outcome": "timeout",
            "category": "timeout_or_resource_failure",
            "basis": "saved pipeline_corrected_runtime_timeout_status is timeout",
            "scaffold": "false",
            "healer": "false",
            "risk": "high",
            "review": "classified_from_saved_diagnostics",
        }
    return {
        "failure_stage": "evalplus_execution_or_assertion",
        "outcome": "evalplus_failure_unspecified",
        "category": "unknown",
        "basis": (
            "saved artifacts show compile pass, expected entry point present, and generic EvalPlus failure; "
            "they do not distinguish import/name error, runtime exception, or functional assertion failure"
        ),
        "scaffold": "false",
        "healer": "false",
        "risk": "unknown",
        "review": "manual_review_required",
    }


def build_census(repo_root: Path = REPO_ROOT) -> tuple[list[dict[str, str]], dict[str, Any]]:
    repo_root = repo_root.resolve()
    run_dir = repo_root / RUN_RELATIVE
    source_hashes = {
        name: _sha256_bytes((run_dir / name).read_bytes()) for name in EXPECTED_SOURCE_HASHES
    }
    _require(source_hashes == EXPECTED_SOURCE_HASHES, "run_003 source artifact hash mismatch")

    plan = json.loads((run_dir / "generation_plan.json").read_text(encoding="utf-8"))
    protocol_path = repo_root / PROTOCOL_RELATIVE
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    _require(plan["run_id"] == "mbpp_qwen35_9b_ab1_dev_run_003", "run_id mismatch")
    _require(plan["dataset"] == "MBPP+", "unexpected benchmark")
    _require(len(plan["task_ids"]) == EXPECTED_TASKS, "task count mismatch")
    _require(len(set(plan["task_ids"])) == EXPECTED_TASKS, "duplicate task in plan")
    _require(plan["seeds"] == EXPECTED_SEEDS, "seed protocol mismatch")
    _require(plan["expected_cells"] == EXPECTED_CELLS, "expected cell count mismatch")
    _require(
        not any(plan[key] for key in ("retry", "resume", "overwrite", "scaffold", "healer")),
        "run plan contains forbidden retry/resume/overwrite/scaffold/healer setting",
    )
    _require(plan["post_healer_account"] is False, "run contains a post-Healer account")
    primary = protocol["models"]["primary_development_model"]
    _require(plan["model"] == primary["tag"] == EXPECTED_MODEL, "model tag mismatch")
    _require(plan["model_digest"] == primary["digest"] == EXPECTED_DIGEST, "model digest mismatch")
    _require(plan["protocol_sha256"] == _sha256_bytes(protocol_path.read_bytes()), "protocol hash mismatch")
    _require(
        plan["frozen_split_sha256"] == _sha256_bytes((repo_root / FROZEN_SPLIT_RELATIVE).read_bytes()),
        "frozen split hash mismatch",
    )

    raw_rows = _read_jsonl(run_dir / "raw_generations.jsonl")
    pipeline_rows = _read_jsonl(run_dir / "pipeline_corrected.jsonl")
    with (run_dir / "evaluation_results.csv").open(encoding="utf-8", newline="") as handle:
        evaluation_rows = list(csv.DictReader(handle))
    journal_paths = sorted((run_dir / "generation_journal").glob("*.json"))
    _require(
        len(raw_rows) == len(pipeline_rows) == len(evaluation_rows) == len(journal_paths) == EXPECTED_CELLS,
        "run_003 must contain exactly 100 records in every artifact account",
    )
    raw_by_id = _index_unique(raw_rows, "raw")
    pipeline_by_id = _index_unique(pipeline_rows, "pipeline")
    evaluation_by_id = _index_unique(evaluation_rows, "evaluation")
    journals = {path.stem: json.loads(path.read_text(encoding="utf-8")) for path in journal_paths}
    _require(len(journals) == EXPECTED_CELLS, "duplicate or malformed journal filename")
    _require(
        set(raw_by_id) == set(pipeline_by_id) == set(evaluation_by_id) == set(journals),
        "generation identifiers do not reconcile across artifacts",
    )
    expected_cells = {(task_id, seed) for task_id in plan["task_ids"] for seed in EXPECTED_SEEDS}
    _require(
        {(row["task_id"], row["seed"]) for row in raw_rows} == expected_cells,
        "missing, duplicate, or out-of-scope task/seed cell",
    )
    entry_points = _load_entry_points(repo_root, plan["task_ids"])
    settings = protocol["generation"]

    for raw in raw_rows:
        generation_id = raw["generation_id"]
        pipeline = pipeline_by_id[generation_id]
        evaluation = evaluation_by_id[generation_id]
        request = raw["request"]
        options = request["options"]
        expected_options = {
            "num_ctx": settings["num_ctx"],
            "num_predict": settings["num_predict"],
            "seed": raw["seed"],
            "temperature": settings["temperature"],
            "top_k": settings["top_k"],
            "top_p": settings["top_p"],
        }
        _require(raw == journals[generation_id], f"{generation_id}: journal/raw record mismatch")
        _require(raw["model"] == EXPECTED_MODEL and raw["model_digest"] == EXPECTED_DIGEST, f"{generation_id}: model mismatch")
        _require(request["model"] == EXPECTED_MODEL, f"{generation_id}: request model mismatch")
        _require(request["think"] is False and request["stream"] is False, f"{generation_id}: thinking/stream mismatch")
        _require(options == expected_options, f"{generation_id}: sampling parameter mismatch")
        _require(raw["retry_count"] == 0, f"{generation_id}: retry detected")
        _require(_sha256_text(raw["raw_response"]) == raw["raw_response_sha256"], f"{generation_id}: raw response hash mismatch")
        _require(json.loads(raw["raw_http_response_body"])["message"]["content"] == raw["raw_response"], f"{generation_id}: raw HTTP response mismatch")
        _require(pipeline["task_id"] == raw["task_id"] and pipeline["seed"] == raw["seed"], f"{generation_id}: pipeline identity mismatch")
        _require(pipeline["source_raw_response_sha256"] == raw["raw_response_sha256"], f"{generation_id}: pipeline source hash mismatch")
        corrected = pipeline["pipeline_corrected_output"]
        corrected_hash = pipeline["pipeline_corrected_output_sha256"]
        _require((corrected is None and corrected_hash is None) or (corrected is not None and _sha256_text(corrected) == corrected_hash), f"{generation_id}: extracted program hash mismatch")
        _require(evaluation["task_id"] == raw["task_id"] and int(evaluation["seed"]) == raw["seed"], f"{generation_id}: evaluation identity mismatch")
        _require(evaluation["observed_output_sha256"] == raw["raw_response_sha256"], f"{generation_id}: observed evaluation hash mismatch")
        _require(evaluation["pipeline_corrected_output_sha256"] == (corrected_hash or ""), f"{generation_id}: pipeline evaluation hash mismatch")

    observed_counts = Counter(row["observed_status"] for row in evaluation_rows)
    pipeline_counts = Counter(row["pipeline_corrected_status"] for row in evaluation_rows)
    failed_tasks = {row["task_id"] for row in evaluation_rows if row["pipeline_corrected_status"] == "fail"}
    _require(observed_counts == {"fail": 100}, "observed evaluation summary mismatch")
    _require(pipeline_counts == {"pass": 30, "fail": 70}, "pipeline evaluation summary mismatch")
    _require(len(failed_tasks) == EXPECTED_FAILED_TASKS, "unique failed task count mismatch")
    _require(not (pipeline_counts["fail"] < 20 or len(failed_tasks) < 5), "expansion trigger mismatch")

    census_rows: list[dict[str, str]] = []
    for raw in raw_rows:
        generation_id = raw["generation_id"]
        evaluation = evaluation_by_id[generation_id]
        if evaluation["pipeline_corrected_status"] != "fail":
            continue
        pipeline = pipeline_by_id[generation_id]
        classification = _classify(pipeline, evaluation, entry_points[raw["task_id"]])
        census_rows.append(
            {
                "task_id": raw["task_id"],
                "seed": str(raw["seed"]),
                "cell_id": generation_id,
                "raw_generation_sha256": raw["raw_response_sha256"],
                "extracted_program_sha256": pipeline["pipeline_corrected_output_sha256"] or "",
                "pipeline_extracted": str(pipeline["extraction_status"] == "extracted").lower(),
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
    _require(len(census_rows) == EXPECTED_PIPELINE_FAILS, "census row count mismatch")
    _require(len({row["task_id"] for row in census_rows}) == EXPECTED_FAILED_TASKS, "census task count mismatch")

    category_counts = Counter(row["failure_category"] for row in census_rows)
    journal_tree_material = "".join(
        f"{path.name}  {_sha256_bytes(path.read_bytes())}\n" for path in journal_paths
    ).encode("utf-8")
    manifest = {
        "census_version": "milestone_1c_v1",
        "run_id": plan["run_id"],
        "scope": "MBPP+ frozen active development subset only",
        "generation_cells": EXPECTED_CELLS,
        "evaluation_accounts": ["observed", "pipeline_corrected"],
        "evaluated_account_rows": 200,
        "evaluated_account_rows_explanation": "100 identical generation cells evaluated in two accounts; not 200 generations",
        "observed_pass": 0,
        "observed_fail": 100,
        "pipeline_pass": 30,
        "pipeline_fail": 70,
        "failed_unique_tasks": 19,
        "expansion_triggered": False,
        "pipeline_rescues_excluded_from_healer_effect": 30,
        "source_artifacts": {
            name: {"path": (RUN_RELATIVE / name).as_posix(), "sha256": digest}
            for name, digest in source_hashes.items()
        },
        "generation_journal": {
            "path": (RUN_RELATIVE / "generation_journal").as_posix(),
            "file_count": len(journal_paths),
            "tree_manifest_sha256": _sha256_bytes(journal_tree_material),
        },
        "protocol": {"path": PROTOCOL_RELATIVE.as_posix(), "sha256": plan["protocol_sha256"]},
        "frozen_split": {"path": FROZEN_SPLIT_RELATIVE.as_posix(), "sha256": plan["frozen_split_sha256"]},
        "category_counts": {category: category_counts[category] for category in CATEGORIES},
        "scaffold_candidates": sum(row["scaffold_candidate"] == "true" for row in census_rows),
        "healer_candidates": sum(row["healer_candidate"] == "true" for row in census_rows),
        "unknown_or_manual_review": sum(
            row["failure_category"] == "unknown" or row["review_status"] == "manual_review_required"
            for row in census_rows
        ),
    }
    return census_rows, manifest


def render_csv(rows: list[dict[str, str]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def render_manifest(manifest: dict[str, Any]) -> bytes:
    return (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")


def render_summary(manifest: dict[str, Any]) -> bytes:
    lines = [
        "# Milestone 1C: MBPP+ development failure census",
        "",
        "## Integrity result",
        "",
        "- Generation cells: 100 (20 task IDs × seeds 11, 22, 33, 44, 55)",
        "- Observed: 0 pass / 100 fail",
        "- Pipeline-corrected: 30 pass / 70 fail",
        "- Pipeline-corrected failed tasks: 19",
        "- Expansion triggered: false",
        "- Retry, duplicate, missing, and out-of-scope cells: none",
        "- Model/protocol: qwen3.5:9b, frozen digest and sampling settings verified, `think=false`",
        "",
        "`evaluated 200/200` means that the same 100 generation cells were evaluated under the Observed and Pipeline-corrected accounts. It does not mean 200 generations occurred.",
        "",
        "## Failure categories",
        "",
        "| Category | Cells |",
        "|---|---:|",
    ]
    for category in CATEGORIES:
        lines.append(f"| `{category}` | {manifest['category_counts'][category]} |")
    lines.extend(
        [
            "",
            "## Candidate counts",
            "",
            f"- Scaffold candidates: {manifest['scaffold_candidates']}",
            f"- Healer candidates: {manifest['healer_candidates']}",
            f"- Unknown/manual review: {manifest['unknown_or_manual_review']}",
            "",
            "Candidate labels are triage hypotheses only; they do not establish safe repair rules. Functional test failures are never automatically labeled Healer candidates. The 30 Pipeline rescues are Pipeline correction outcomes and are excluded from Healer effectiveness.",
            "",
            "Rows classified as `unknown` remain manual-review-required because the saved evaluator artifact collapses assertion failures and runtime exceptions into a generic failure outcome. No hidden tests, expected outputs, canonical solutions, or sealed model outputs were read or stored.",
            "",
            "Pipeline correction and Healer accounting remain completely separate. No Scaffold or Healer was modified or built, and no generation or EvalPlus execution was performed.",
            "",
        ]
    )
    return "\n".join(lines).encode("utf-8")


def write_outputs(repo_root: Path, output_dir: Path) -> dict[str, Any]:
    rows, manifest = build_census(repo_root)
    rendered = {
        "failure_census.csv": render_csv(rows),
        "failure_census_manifest.json": render_manifest(manifest),
        "failure_census_summary.md": render_summary(manifest),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, content in rendered.items():
        (output_dir / name).write_bytes(content)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()
    output_dir = args.output_dir or repo_root / OUTPUT_RELATIVE
    manifest = write_outputs(repo_root, output_dir)
    print(json.dumps({"output_dir": str(output_dir), **manifest}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
