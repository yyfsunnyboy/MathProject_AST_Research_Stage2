#!/usr/bin/env python3
"""Read-only census planning for remaining121 taxonomy-v3 cells.

CENSUS_PLANNING_NOT_TAXONOMY_ADJUDICATION

Population:
  remaining171 machine census
  − module_exception provisional 37
  − multiple_signal_chain provisional 13
  = remaining121

Does not adjudicate taxonomy, does not decide Healer eligibility, does not
execute candidates, diagnostics, validation, or models.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

try:
    from scripts import prepare_candidate_b_r003_taxonomy_v3_formal_classification as preparation
    from scripts import prepare_candidate_b_r003_taxonomy_v3_remaining171_machine_census_v1 as census_prep
except ModuleNotFoundError as exc:
    if exc.name != "scripts":
        raise
    import prepare_candidate_b_r003_taxonomy_v3_formal_classification as preparation
    import prepare_candidate_b_r003_taxonomy_v3_remaining171_machine_census_v1 as census_prep


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_remaining121_census_planning_v1"
)
START_HEAD = "a18cf32f27c781daa3e9c3f493a4527f31a6f481"
STATUS = "CENSUS_PLANNING_NOT_TAXONOMY_ADJUDICATION"
ANALYZER = Path("scripts/prepare_candidate_b_r003_taxonomy_v3_remaining121_census_planning_v1.py")
TESTS = Path(
    "tests/finals_rebuild/test_candidate_b_r003_taxonomy_v3_remaining121_census_planning_v1.py"
)

MACHINE_CENSUS_DIR = census_prep.OUTPUT_RELATIVE
MACHINE_CENSUS_MANIFEST = MACHINE_CENSUS_DIR / "manifest.json"
MACHINE_CENSUS_CSV = MACHINE_CENSUS_DIR / "machine_census.csv"
MACHINE_CENSUS_ROSTER = MACHINE_CENSUS_DIR / "fixed_roster.csv"
MACHINE_CENSUS_MANIFEST_SHA256 = "3def8a5806b20200ade0b5d4a652d3fb6998ecc889bf7277485cd6045831ef07"
MACHINE_CENSUS_CSV_SHA256 = "284802c8f1aeff92ad70f65b42c4aa7dabc252da592f8ad62011be71537f8a32"
MACHINE_CENSUS_ROSTER_SHA256 = "6e2c6e243fc6ff01c0b0fc2c6939e99cf7f87ef5f17bdf97206adc62ab9af1a5"

G2_PROVISIONAL_CSV = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_g2_module_ai_assisted_provisional_adjudication_v1/"
    "ai_assisted_provisional_adjudication.csv"
)
G2_PROVISIONAL_CSV_SHA256 = (
    "90d17695c25d4c1f054fa23949cbd5237fcfeb4ade80eb38175b3c022687b119"
)

MODULE_EXCEPTION_DIR = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_remaining171_module_exception_provisional_v1"
)
MODULE_EXCEPTION_CSV = MODULE_EXCEPTION_DIR / "ai_provisional_adjudication.csv"
MODULE_EXCEPTION_MANIFEST = MODULE_EXCEPTION_DIR / "manifest.json"
MODULE_EXCEPTION_CSV_SHA256 = (
    "8b32d0561c0d42efe07c1bf89bd3bcaf4b7a42657f54bee25922f0be2aca6ab7"
)
MODULE_EXCEPTION_MANIFEST_SHA256 = (
    "72b02ab7da59e65db2d5e09cee9344c3d52940a717ea3dfea05310e0529d76c1"
)

MULTIPLE_SIGNAL_DIR = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_remaining134_multiple_signal_chain13_provisional_v1"
)
MULTIPLE_SIGNAL_CSV = MULTIPLE_SIGNAL_DIR / "ai_provisional_adjudication.csv"
MULTIPLE_SIGNAL_MANIFEST = MULTIPLE_SIGNAL_DIR / "manifest.json"
MULTIPLE_SIGNAL_CSV_SHA256 = (
    "dc2e7202c048400d32e019fed6940051f65ca1a67b865727152d94dccf302d70"
)
MULTIPLE_SIGNAL_MANIFEST_SHA256 = (
    "fd26fdbd103ad216e2a38c8e16b839c9e2b72a242e360713edee8d7762f59336"
)

SOURCE_HASHES: dict[Path, str] = {
    preparation.JOURNAL: preparation.SOURCE_HASHES[preparation.JOURNAL],
    preparation.TASKS: preparation.SOURCE_HASHES[preparation.TASKS],
    MACHINE_CENSUS_MANIFEST: MACHINE_CENSUS_MANIFEST_SHA256,
    MACHINE_CENSUS_CSV: MACHINE_CENSUS_CSV_SHA256,
    MACHINE_CENSUS_ROSTER: MACHINE_CENSUS_ROSTER_SHA256,
    G2_PROVISIONAL_CSV: G2_PROVISIONAL_CSV_SHA256,
    MODULE_EXCEPTION_CSV: MODULE_EXCEPTION_CSV_SHA256,
    MODULE_EXCEPTION_MANIFEST: MODULE_EXCEPTION_MANIFEST_SHA256,
    MULTIPLE_SIGNAL_CSV: MULTIPLE_SIGNAL_CSV_SHA256,
    MULTIPLE_SIGNAL_MANIFEST: MULTIPLE_SIGNAL_MANIFEST_SHA256,
}

# Fixed before any population statistics are inspected.
WORK_CLUSTER_PRIORITY: tuple[str, ...] = (
    "parse_or_compile_signal",
    "truncation_mechanism_signal",
    "missing_or_ambiguous_entry_point_signal",
    "import_or_name_resolution_signal",
    "module_execution_exception_signal",
    "timeout_or_nontermination_signal",
    "duplicate_definition_signal",
    "output_or_contract_shape_signal",
    "test_execution_failure_signal",
    "static_unbound_name_signal",
    "packaging_or_scaffold_residue_signal",
    "no_decisive_machine_signal",
)

# Fixed before any population statistics are inspected.
NEXT_BATCH_TARGET_CLUSTER = "output_or_contract_shape_signal"
NEXT_BATCH_TARGET_SIZE = 20
NEXT_BATCH_DEDUPLICATE_BY_SOURCE = True
NEXT_BATCH_ROUND_ROBIN_BY_RETURN_TYPE = True

PROCESSED_SETS: tuple[tuple[str, Path, str], ...] = (
    ("G2_module", G2_PROVISIONAL_CSV, G2_PROVISIONAL_CSV_SHA256),
    ("module_exception", MODULE_EXCEPTION_CSV, MODULE_EXCEPTION_CSV_SHA256),
    ("multiple_signal_chain", MULTIPLE_SIGNAL_CSV, MULTIPLE_SIGNAL_CSV_SHA256),
)

ROSTER_FIELDS = (
    "roster_rank",
    "program_id",
    "cell_identity_sha256",
    "task_identity_sha256",
    "task_id",
    "seed",
    "generation_id",
    "condition",
    "required_entry_point",
    "evaluation_source_sha256",
    "original_diagnostic_phase",
    "original_diagnostic_exception_class",
    "original_termination",
    "original_outcome_validity",
    "machine_census_roster_rank",
    "inclusion_reason",
)

EXCLUSION_AUDIT_FIELDS = (
    "program_id",
    "processed_set",
    "source_roster_path",
    "source_roster_sha256",
    "in_remaining171",
    "excluded_from_remaining121",
)

SIGNAL_INVENTORY_FIELDS = (
    "roster_rank",
    "program_id",
    "cell_identity_sha256",
    "task_id",
    "seed",
    "condition",
    "evaluation_source_sha256",
    "diagnostic_phase",
    "diagnostic_exception_class",
    "termination",
    "return_type_bucket",
    "return_shape_bucket",
    "all_signal_tags",
    "work_cluster",
    "work_cluster_priority_rule",
    "duplicate_source_group_id",
    "duplicate_source_group_size",
    "is_source_representative",
)

CLUSTER_SUMMARY_FIELDS = ("work_cluster", "cells", "unique_program_id", "unique_task_id", "unique_source_sha256")

DUPLICATE_SUMMARY_FIELDS = (
    "duplicate_source_group_id",
    "evaluation_source_sha256",
    "group_size",
    "program_ids",
    "task_ids",
    "seeds",
    "cross_seed_replay",
    "same_task",
)

NEXT_BATCH_ROSTER_FIELDS = (
    "batch_rank",
    "program_id",
    "cell_identity_sha256",
    "task_id",
    "seed",
    "condition",
    "evaluation_source_sha256",
    "work_cluster",
    "return_type_bucket",
    "return_shape_bucket",
    "duplicate_source_group_size",
    "selection_reason",
)


class PlanningError(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PlanningError(message)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _csv_bytes(fields: tuple[str, ...], rows: list[dict[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows({field: row.get(field, "") for field in fields} for row in rows)
    return stream.getvalue().encode("utf-8")


def _path(repo: Path, relative: Path) -> Path:
    return relative if relative.is_absolute() else repo / relative


def verify_sources(repo: Path = REPO_ROOT, expected: dict[Path, str] | None = None) -> None:
    for relative, digest in (expected or SOURCE_HASHES).items():
        path = _path(repo, relative)
        _require(path.is_file(), f"missing frozen source: {path}")
        _require(_sha(path.read_bytes()) == digest, f"frozen source hash drift: {path}")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _static_signal_tags(source: str, entry_point: str) -> tuple[list[str], dict[str, str]]:
    tags: list[str] = []
    details: dict[str, str] = {
        "truncation_mechanism_signal": "false",
        "duplicate_definition_signal": "false",
        "static_unbound_name_signal": "false",
    }
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        tags.append("parse_or_compile_signal")
        if "truncated" in (exc.msg or "").lower() or source.rstrip().endswith((":", "\\", "(")):
            tags.append("truncation_mechanism_signal")
            details["truncation_mechanism_signal"] = "true"
        return tags, details

    names_at_module: Counter[str] = Counter()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names_at_module[node.name] += 1
    if any(count > 1 for count in names_at_module.values()):
        tags.append("duplicate_definition_signal")
        details["duplicate_definition_signal"] = "true"

    defined = set(names_at_module)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                defined.add(alias.asname or alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                defined.add(alias.asname or alias.name)
    for node in tree.body:
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            if node.id not in defined and node.id not in dir(__builtins__):
                tags.append("static_unbound_name_signal")
                details["static_unbound_name_signal"] = "true"
                break

    defs = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == entry_point
    ]
    if not defs:
        tags.append("missing_or_ambiguous_entry_point_signal")
    elif len(defs) > 1:
        tags.append("missing_or_ambiguous_entry_point_signal")

    scaffold_tokens = ("if __name__", "print(", "# Example", "# Test", "All tests passed")
    module_nodes = [
        node
        for node in tree.body
        if not isinstance(
            node,
            (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
        )
    ]
    if any(token in source for token in scaffold_tokens) or module_nodes:
        tags.append("packaging_or_scaffold_residue_signal")

    return sorted(set(tags)), details


def _frozen_signal_tags(census_row: dict[str, str]) -> list[str]:
    tags = json.loads(census_row["all_observed_machine_signals"])
    if census_row["parse_success"] == "false" and "parse_or_compile_signal" not in tags:
        tags.append("parse_or_compile_signal")
    if census_row["truncation_mechanism_candidate"] == "true":
        tags.append("truncation_mechanism_signal")
    if census_row["module_execution_exception_signal"] == "true":
        tags.append("module_execution_exception_signal")
    if census_row["import_or_name_resolution_signal"] == "true":
        tags.append("import_or_name_resolution_signal")
    if census_row["timeout_or_nontermination_signal"] == "true":
        tags.append("timeout_or_nontermination_signal")
    if census_row["completed_return_signal"] == "true":
        tags.append("test_execution_failure_signal")
    if census_row["output_or_contract_shape_signal"] == "true":
        tags.append("output_or_contract_shape_signal")
    if census_row["packaging_or_scaffold_residue_signal"] == "true":
        tags.append("packaging_or_scaffold_residue_signal")
    if census_row["diagnostic_evidence_validity"] == "INVALID_INFRASTRUCTURE":
        return ["no_decisive_machine_signal"]
    return sorted(set(tags))


def _assign_work_cluster(all_signal_tags: list[str]) -> tuple[str, str]:
    decisive = [tag for tag in all_signal_tags if tag != "packaging_or_scaffold_residue_signal"]
    if not decisive and "packaging_or_scaffold_residue_signal" in all_signal_tags:
        return "packaging_or_scaffold_residue_signal", "priority:packaging_only"
    for cluster in WORK_CLUSTER_PRIORITY:
        if cluster in decisive:
            return cluster, f"priority:{cluster}"
    if "packaging_or_scaffold_residue_signal" in all_signal_tags:
        return "packaging_or_scaffold_residue_signal", "priority:packaging_only"
    return "no_decisive_machine_signal", "priority:fallback_no_decisive"


def _load_processed_sets(repo: Path) -> tuple[dict[str, set[str]], list[dict[str, str]]]:
    processed_by_set: dict[str, set[str]] = {}
    audit_rows: list[dict[str, str]] = []
    for set_name, roster_path, roster_sha in PROCESSED_SETS:
        ids = {row["program_id"] for row in _read_csv(repo / roster_path)}
        processed_by_set[set_name] = ids
        for program_id in sorted(ids):
            audit_rows.append(
                {
                    "program_id": program_id,
                    "processed_set": set_name,
                    "source_roster_path": roster_path.as_posix(),
                    "source_roster_sha256": roster_sha,
                    "in_remaining171": "",
                    "excluded_from_remaining121": "",
                }
            )
    g2 = processed_by_set["G2_module"]
    module_exc = processed_by_set["module_exception"]
    multi = processed_by_set["multiple_signal_chain"]
    _require(len(g2) == 27, f"G2_module count drift: {len(g2)}")
    _require(len(module_exc) == 37, f"module_exception count drift: {len(module_exc)}")
    _require(len(multi) == 13, f"multiple_signal_chain count drift: {len(multi)}")
    _require(not (g2 & module_exc), "G2 ∩ module_exception must be empty")
    _require(not (g2 & multi), "G2 ∩ multiple_signal_chain must be empty")
    _require(not (module_exc & multi), "module_exception ∩ multiple_signal_chain must be empty")
    _require(len(g2 | module_exc | multi) == 77, "processed union must be 77 unique program_id")
    return processed_by_set, audit_rows


def _select_next_batch(
    inventory: list[dict[str, str]],
) -> list[dict[str, str]]:
    candidates = [
        row
        for row in inventory
        if row["work_cluster"] == NEXT_BATCH_TARGET_CLUSTER
        and row["is_source_representative"] == "true"
    ]
    _require(candidates, "no candidates for next batch")
    if NEXT_BATCH_ROUND_ROBIN_BY_RETURN_TYPE:
        by_bucket: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in sorted(candidates, key=lambda item: (item["task_id"], item["program_id"])):
            by_bucket[row["return_type_bucket"] or "UNKNOWN"].append(row)
        buckets = sorted(by_bucket)
        selected: list[dict[str, str]] = []
        index = 0
        while len(selected) < NEXT_BATCH_TARGET_SIZE:
            added = False
            for bucket in buckets:
                if index < len(by_bucket[bucket]):
                    selected.append(by_bucket[bucket][index])
                    added = True
                    if len(selected) >= NEXT_BATCH_TARGET_SIZE:
                        break
            if not added:
                break
            index += 1
        selected = sorted(selected, key=lambda item: item["program_id"])
    else:
        selected = sorted(
            candidates,
            key=lambda item: (item["return_type_bucket"], item["task_id"], item["program_id"]),
        )[:NEXT_BATCH_TARGET_SIZE]
    _require(selected, "next batch selection empty")
    return selected


def build_analysis(repo: Path = REPO_ROOT) -> dict[str, Any]:
    verify_sources(repo)
    processed_by_set, audit_template = _load_processed_sets(repo)
    g2_ids = processed_by_set["G2_module"]
    module_exc_ids = processed_by_set["module_exception"]
    multi_ids = processed_by_set["multiple_signal_chain"]
    processed_in_remaining171 = module_exc_ids | multi_ids

    roster171 = _read_csv(repo / MACHINE_CENSUS_ROSTER)
    census171 = _read_csv(repo / MACHINE_CENSUS_CSV)
    _require(len(roster171) == 171, "remaining171 roster count drift")
    _require(len(census171) == 171, "remaining171 census count drift")

    roster_by_program = {row["program_id"]: row for row in roster171}
    census_by_program = {row["program_id"]: row for row in census171}
    remaining171_ids = set(roster_by_program)
    _require(not (remaining171_ids & g2_ids), "G2 must not appear in remaining171")
    _require(len(processed_in_remaining171 & remaining171_ids) == 50, "processed-in-remaining171 count drift")

    for row in audit_template:
        pid = row["program_id"]
        row["in_remaining171"] = str(pid in remaining171_ids).lower()
        row["excluded_from_remaining121"] = str(pid in processed_in_remaining171).lower()

    remaining121_ids = remaining171_ids - processed_in_remaining171
    _require(len(remaining121_ids) == 121, f"remaining121 count drift: {len(remaining121_ids)}")

    journals = {
        row["program_id"]: row
        for row in _read_jsonl(repo / preparation.JOURNAL)
        if row["healer_account"] == "H0"
    }
    tasks = {row["task_id"]: row for row in _read_jsonl(repo / preparation.TASKS)}

    remaining_sorted = sorted(remaining121_ids)
    roster_rows: list[dict[str, str]] = []
    inventory_rows: list[dict[str, str]] = []

    for rank, program_id in enumerate(remaining_sorted, 1):
        roster_row = roster_by_program[program_id]
        census_row = census_by_program[program_id]
        journal = journals[program_id]
        task = tasks[roster_row["task_id"]]
        source = journal["evaluation_source"]
        _require(
            _sha(source.encode("utf-8")) == roster_row["evaluation_source_sha256"],
            f"source sha drift: {program_id}",
        )
        static_tags, _static_details = _static_signal_tags(source, str(task["entry_point"]))
        frozen_tags = _frozen_signal_tags(census_row)
        all_tags = sorted(set(static_tags) | set(frozen_tags))
        work_cluster, priority_rule = _assign_work_cluster(all_tags)

        roster_rows.append(
            {
                "roster_rank": str(rank),
                "program_id": program_id,
                "cell_identity_sha256": roster_row["cell_identity_sha256"],
                "task_identity_sha256": roster_row["task_identity_sha256"],
                "task_id": roster_row["task_id"],
                "seed": roster_row["seed"],
                "generation_id": roster_row["generation_id"],
                "condition": roster_row["condition_account"],
                "required_entry_point": roster_row["required_entry_point"],
                "evaluation_source_sha256": roster_row["evaluation_source_sha256"],
                "original_diagnostic_phase": roster_row["original_diagnostic_phase"],
                "original_diagnostic_exception_class": roster_row["original_diagnostic_exception_class"],
                "original_termination": roster_row["original_termination"],
                "original_outcome_validity": roster_row["original_outcome_validity"],
                "machine_census_roster_rank": roster_row["roster_rank"],
                "inclusion_reason": "remaining171_minus_module_exception37_minus_multiple_signal13",
            }
        )
        inventory_rows.append(
            {
                "roster_rank": str(rank),
                "program_id": program_id,
                "cell_identity_sha256": roster_row["cell_identity_sha256"],
                "task_id": roster_row["task_id"],
                "seed": roster_row["seed"],
                "condition": roster_row["condition_account"],
                "evaluation_source_sha256": roster_row["evaluation_source_sha256"],
                "diagnostic_phase": census_row["diagnostic_phase"],
                "diagnostic_exception_class": census_row["diagnostic_exception_class"],
                "termination": census_row["termination"],
                "return_type_bucket": census_row["return_type_bucket"],
                "return_shape_bucket": census_row["return_shape_bucket"],
                "all_signal_tags": _json(all_tags),
                "work_cluster": work_cluster,
                "work_cluster_priority_rule": priority_rule,
                "duplicate_source_group_id": "",
                "duplicate_source_group_size": "1",
                "is_source_representative": "true",
            }
        )

    source_groups: dict[str, list[str]] = defaultdict(list)
    for row in inventory_rows:
        source_groups[row["evaluation_source_sha256"]].append(row["program_id"])
    duplicate_summaries: list[dict[str, str]] = []
    for group_index, (source_sha, program_ids) in enumerate(
        sorted(source_groups.items(), key=lambda item: (-len(item[1]), item[0])),
        1,
    ):
        group_id = f"dup_src_{group_index:03d}"
        group_size = len(program_ids)
        representative = min(program_ids)
        inv_by_program = {row["program_id"]: row for row in inventory_rows}
        task_ids = sorted({inv_by_program[pid]["task_id"] for pid in program_ids})
        seeds = sorted(inv_by_program[pid]["seed"] for pid in program_ids)
        for row in inventory_rows:
            if row["evaluation_source_sha256"] == source_sha:
                row["duplicate_source_group_id"] = group_id
                row["duplicate_source_group_size"] = str(group_size)
                row["is_source_representative"] = str(row["program_id"] == representative).lower()
        if group_size > 1:
            duplicate_summaries.append(
                {
                    "duplicate_source_group_id": group_id,
                    "evaluation_source_sha256": source_sha,
                    "group_size": str(group_size),
                    "program_ids": _json(program_ids),
                    "task_ids": _json(task_ids),
                    "seeds": _json(seeds),
                    "cross_seed_replay": str(len(set(seeds)) > 1).lower(),
                    "same_task": str(len(set(task_ids)) == 1).lower(),
                }
            )

    cluster_counter = Counter(row["work_cluster"] for row in inventory_rows)
    _require(sum(cluster_counter.values()) == 121, "cluster sum must be 121")
    cluster_summary = []
    for cluster in WORK_CLUSTER_PRIORITY:
        rows = [row for row in inventory_rows if row["work_cluster"] == cluster]
        cluster_summary.append(
            {
                "work_cluster": cluster,
                "cells": str(len(rows)),
                "unique_program_id": str(len({row["program_id"] for row in rows})),
                "unique_task_id": str(len({row["task_id"] for row in rows})),
                "unique_source_sha256": str(len({row["evaluation_source_sha256"] for row in rows})),
            }
        )

    next_batch_candidates = _select_next_batch(inventory_rows)
    next_batch_rows = []
    for batch_rank, row in enumerate(next_batch_candidates, 1):
        next_batch_rows.append(
            {
                "batch_rank": str(batch_rank),
                "program_id": row["program_id"],
                "cell_identity_sha256": row["cell_identity_sha256"],
                "task_id": row["task_id"],
                "seed": row["seed"],
                "condition": row["condition"],
                "evaluation_source_sha256": row["evaluation_source_sha256"],
                "work_cluster": row["work_cluster"],
                "return_type_bucket": row["return_type_bucket"],
                "return_shape_bucket": row["return_shape_bucket"],
                "duplicate_source_group_size": row["duplicate_source_group_size"],
                "selection_reason": (
                    f"cluster={NEXT_BATCH_TARGET_CLUSTER};"
                    f"source_representative={row['is_source_representative']};"
                    f"round_robin_return_type={NEXT_BATCH_ROUND_ROBIN_BY_RETURN_TYPE}"
                ),
            }
        )

    execution_counts = {
        "model_calls": 0,
        "candidate_executions": 0,
        "evalplus_correctness_executions": 0,
        "diagnostics_executions": 0,
        "validation_executions": 0,
        "healer_executions": 0,
        "programs_executed": 0,
    }

    return {
        "roster_rows": roster_rows,
        "audit_rows": audit_template,
        "inventory_rows": inventory_rows,
        "cluster_summary": cluster_summary,
        "cluster_counter": cluster_counter,
        "duplicate_summaries": duplicate_summaries,
        "next_batch_rows": next_batch_rows,
        "execution_counts": execution_counts,
        "processed_by_set": processed_by_set,
        "remaining121_ids": remaining121_ids,
    }


def _next_batch_report(analysis: dict[str, Any], roster_hash: str) -> str:
    batch = analysis["next_batch_rows"]
    inventory = {row["program_id"]: row for row in analysis["inventory_rows"]}
    return_type_counts = Counter(row["return_type_bucket"] for row in batch)
    task_ids = {row["task_id"] for row in batch}
    source_shas = {row["evaluation_source_sha256"] for row in batch}
    lines = [
        "# Candidate B r003 taxonomy v3：remaining121 下一批次選定報告",
        "",
        f"**狀態：`{STATUS}`**",
        "",
        "## 選定原則（統計前固定）",
        "",
        f"- 目標 work cluster：`{NEXT_BATCH_TARGET_CLUSTER}`",
        f"- 目標規模：{NEXT_BATCH_TARGET_SIZE} 格",
        f"- 來源去重：{NEXT_BATCH_DEDUPLICATE_BY_SOURCE}",
        f"- return_type 輪詢：{NEXT_BATCH_ROUND_ROBIN_BY_RETURN_TYPE}",
        "- 與 processed77 交集必須為 0",
        "- 不使用 hidden oracle；不因 Healer 可修性選樣",
        "",
        "## 本批摘要",
        "",
        f"- 格數：{len(batch)}",
        f"- 唯一 task_id：{len(task_ids)}",
        f"- 唯一 source_sha256：{len(source_shas)}",
        f"- roster SHA256：{roster_hash}",
        "",
        "## return_type_bucket 分布",
        "",
        "| Bucket | Cells |",
        "|---|---:|",
    ]
    for key, value in sorted(return_type_counts.items()):
        lines.append(f"| `{key or 'EMPTY'}` | {value} |")
    lines.extend(
        [
            "",
            "## 選定理由",
            "",
            "- remaining121 在排除 module_exception（37）與 multiple_signal_chain（13）後，"
            "絕大多數格具 `output_or_contract_shape_signal`：completed 且具 return shape 公開訊號。",
            "- 此 family 與已處理的 runtime exception／multi-signal chain 邊界分明，"
            "適合釐清 L3/L4（語意／契約）與 outcome validity 邊界。",
            "- 本批以 source_sha256 代表格去重，避免跨 seed 重播被當成獨立錯誤模式。",
            "- return_type 輪詢確保批次內含 bool/int/str/list 等多種公開 return shape 線索。",
            "",
            "## 邊界",
            "",
            "- 本報告僅規劃下一批 roster；尚未開始 provisional adjudication。",
            "- `no_decisive_machine_signal`（2 格 INVALID_INFRASTRUCTURE）不納入本批。",
            "",
        ]
    )
    return "\n".join(lines)


def build_outputs(repo: Path = REPO_ROOT) -> dict[str, bytes]:
    analysis = build_analysis(repo)
    provenance = {
        "revision": OUTPUT_RELATIVE.name,
        "status": STATUS,
        "start_head": START_HEAD,
        "remaining121_roster": 121,
        "processed77_total": 77,
        "processed_in_remaining171": 50,
        "g2_outside_remaining171": 27,
        "machine_census_manifest_sha256": MACHINE_CENSUS_MANIFEST_SHA256,
        "multiple_signal_manifest_sha256": MULTIPLE_SIGNAL_MANIFEST_SHA256,
        "taxonomy_adjudication_completed": False,
        "healer_eligibility_decided": False,
        "hidden_expected_actual_used": False,
        "h1_used_for_sampling": False,
        "model_calls": 0,
        "candidate_executions": 0,
        "evalplus_correctness_executions": 0,
        "diagnostics_executions": 0,
        "validation_executions": 0,
        "healer_executions": 0,
        "programs_executed": 0,
        "work_cluster_priority": list(WORK_CLUSTER_PRIORITY),
        "next_batch_target_cluster": NEXT_BATCH_TARGET_CLUSTER,
        "next_batch_target_size": NEXT_BATCH_TARGET_SIZE,
        "source_hashes_verified": len(SOURCE_HASHES),
    }
    outputs = {
        Path("remaining121_roster.csv"): _csv_bytes(ROSTER_FIELDS, analysis["roster_rows"]),
        Path("processed77_exclusion_audit.csv"): _csv_bytes(EXCLUSION_AUDIT_FIELDS, analysis["audit_rows"]),
        Path("signal_inventory.csv"): _csv_bytes(SIGNAL_INVENTORY_FIELDS, analysis["inventory_rows"]),
        Path("mutually_exclusive_cluster_summary.csv"): _csv_bytes(
            CLUSTER_SUMMARY_FIELDS, analysis["cluster_summary"]
        ),
        Path("duplicate_source_summary.csv"): _csv_bytes(
            DUPLICATE_SUMMARY_FIELDS, analysis["duplicate_summaries"]
        ),
        Path("next_batch_roster.csv"): _csv_bytes(NEXT_BATCH_ROSTER_FIELDS, analysis["next_batch_rows"]),
        Path("execution_counts.json"): _json_bytes(analysis["execution_counts"]),
        Path("provenance.json"): _json_bytes(provenance),
    }
    roster_hash = _sha(outputs[Path("next_batch_roster.csv")])
    outputs[Path("next_batch_selection_report_zh.md")] = _next_batch_report(
        analysis, roster_hash
    ).encode("utf-8")
    return outputs


def write_outputs(repo: Path = REPO_ROOT) -> Path:
    destination = repo / OUTPUT_RELATIVE
    _require(not destination.exists(), f"output already exists: {destination}")
    destination.mkdir(parents=True)
    outputs = build_outputs(repo)
    hashes = {path.as_posix(): _sha(data) for path, data in outputs.items()}
    for path, data in outputs.items():
        (destination / path).write_bytes(data)
    manifest = {
        "revision": OUTPUT_RELATIVE.name,
        "status": STATUS,
        "remaining121_roster": 121,
        "processed77_total": 77,
        "processed_in_remaining171": 50,
        "next_batch_size": len(_read_csv(destination / "next_batch_roster.csv")),
        "next_batch_roster_sha256": hashes["next_batch_roster.csv"],
        "model_calls": 0,
        "candidate_executions": 0,
        "evalplus_correctness_executions": 0,
        "diagnostics_executions": 0,
        "validation_executions": 0,
        "healer_executions": 0,
        "programs_executed": 0,
        "source_hashes_verified": len(SOURCE_HASHES),
        "outputs_sha256_excluding_manifest": hashes,
    }
    (destination / "manifest.json").write_bytes(_json_bytes(manifest))
    return destination


def main() -> None:
    path = write_outputs()
    print(path)


if __name__ == "__main__":
    main()
