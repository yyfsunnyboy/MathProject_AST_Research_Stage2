#!/usr/bin/env python3
"""Freeze the next development-only MBPP+ factorial qualification protocol."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
from pathlib import Path
from typing import Any, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_tools.finals_rebuild import mbpp_evaluator_blind_healer as healer  # noqa: E402


OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_governance/factorial_development_qualification_v1"
)
EXPANSION_MANIFEST = Path(
    "artifacts/public_benchmark_governance/development_expansion_v1/"
    "development_expansion_manifest.json"
)
HEALER_LEDGER = Path(
    "artifacts/public_benchmark_governance/healer_candidate_v0_development_audit/"
    "healer_candidate_v0_cell_ledger.csv"
)
HEALER_SPEC = Path(
    "artifacts/public_benchmark_governance/healer_candidate_v0_development_audit/"
    "healer_candidate_v0_spec.json"
)
M2G_SCAFFOLD = Path(
    "artifacts/public_benchmark_governance/milestone_2g_integrated_development_evidence/"
    "scaffold_candidate_evidence.csv"
)
PIPELINE_SOURCE = Path("agent_tools/finals_rebuild/extraction.py")
HEALER_SOURCE = Path("agent_tools/finals_rebuild/mbpp_evaluator_blind_healer.py")

SEEDS = (11, 22, 33, 44, 55)
NEW_TASK_COUNT = 28
FIRST_RANK = 41
LAST_RANK = 68
CANDIDATE_B_TEXT = (
    "Return exactly one concise, complete, executable Python source file.\n"
    "Use the exact required function name and parameters, include required imports, and finish the implementation within the output limit.\n"
    "Do not use Markdown fences or explanatory text; output only Python code.\n"
)
SEPARATOR = "\n\n--- GENERIC CODE SCAFFOLD V0 ---\n\n"
P0_RUN_ID = "mbpp_q35_9b_p0_b28_r001"
P1_RUN_ID = "mbpp_q35_9b_cb_b28_r001"
P0_PATH = "artifacts/pbd/mbpp_b28/p0/r001"
P1_PATH = "artifacts/pbd/mbpp_b28/cb/r001"

SELECTION_FIELDS = (
    "dataset", "dataset_version", "task_id", "source_frozen_governance_role",
    "prior_selection_rank", "prior_selection_hash", "qualification_layer",
    "selection_method", "prompt_answer_tests_read", "frozen_status",
)
EXISTING_ACCOUNT_FIELDS = (
    "development_layer", "prompt_condition", "treatment", "run_id", "task_id",
    "seed", "generation_id", "healer_account", "evaluation_account_id",
    "shared_pipeline_input_sha256", "evaluation_source_sha256", "healer_status",
    "same_generation_h0_h1", "evaluator_not_yet_executed", "development_only",
)
NEW_ACCOUNT_FIELDS = (
    "task_id", "seed", "paired_identity", "prompt_condition", "generation_run_id",
    "generation_planned_cell_id", "healer_account", "evaluation_account_id",
    "pipeline_sha256", "healer_sha256", "same_generation_h0_h1",
    "model_regeneration_for_healer", "development_only",
)


class QualificationFreezeError(RuntimeError):
    """Raised before writes when a protocol invariant drifts."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise QualificationFreezeError(message)


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256(value.encode("utf-8"))


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _csv_bytes(rows: list[dict[str, str]], fields: tuple[str, ...]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def _id(*parts: object) -> str:
    return _sha256_text("|".join(str(part) for part in parts))


def _source_hashes(repo_root: Path) -> dict[str, str]:
    paths = (EXPANSION_MANIFEST, HEALER_LEDGER, HEALER_SPEC, M2G_SCAFFOLD, PIPELINE_SOURCE, HEALER_SOURCE)
    return {path.as_posix(): _sha256((repo_root / path).read_bytes()) for path in paths}


def _select_new_tasks(expansion: dict[str, Any]) -> list[dict[str, str]]:
    _require(expansion["counts"]["historical_development_pool"] == 116, "historical pool drift")
    _require(expansion["counts"]["total_development"] == 60, "active development drift")
    records = expansion["selection"]["records"]
    _require(len(records) == 96, "selection record count drift")
    chosen = [
        record for record in records
        if FIRST_RANK <= int(record["selection_rank_within_remaining_pool"]) <= LAST_RANK
    ]
    _require(len(chosen) == NEW_TASK_COUNT, "new task count drift")
    _require(all(record["selected"] is False for record in chosen), "previously active task selected")
    _require([int(record["selection_rank_within_remaining_pool"]) for record in chosen] == list(range(FIRST_RANK, LAST_RANK + 1)), "rank continuity drift")
    active = {row["task_id"] for row in expansion["development_tasks"]}
    _require(not (active & {record["task_id"] for record in chosen}), "active/new overlap")
    _require(len(active) == 60 and len({record["task_id"] for record in chosen}) == 28, "task uniqueness drift")
    for record in chosen:
        preimage = "\n".join((
            expansion["selection"]["salt"],
            expansion["selection"]["seed"],
            expansion["dataset"],
            expansion["dataset_version"],
            "historical_development_pool",
            record["task_id"],
        )) + "\n"
        _require(_sha256_text(preimage) == record["selection_hash"], f"selection hash drift: {record['task_id']}")
    return [{
        "dataset": expansion["dataset"],
        "dataset_version": expansion["dataset_version"],
        "task_id": record["task_id"],
        "source_frozen_governance_role": "historical_development_pool",
        "prior_selection_rank": str(record["selection_rank_within_remaining_pool"]),
        "prior_selection_hash": record["selection_hash"],
        "qualification_layer": "factorial_qualification_development",
        "selection_method": "next_contiguous_unused_ranks_41_through_68_from_frozen_public_hash_order",
        "prompt_answer_tests_read": "false",
        "frozen_status": "frozen_not_executed",
    } for record in chosen]


def _existing_accounts(ledger: list[dict[str, str]]) -> list[dict[str, str]]:
    _require(len(ledger) == 600, "existing program ledger drift")
    rows: list[dict[str, str]] = []
    for source in ledger:
        for account in ("H0", "H1"):
            evaluation_hash = source["input_sha256"] if account == "H0" else source["output_sha256"]
            status = "not_applied_control" if account == "H0" else source["healer_status"]
            rows.append({
                "development_layer": source["development_layer"],
                "prompt_condition": source["prompt_condition"],
                "treatment": source["treatment"],
                "run_id": source["run_id"],
                "task_id": source["task_id"],
                "seed": source["seed"],
                "generation_id": source["generation_id"],
                "healer_account": account,
                "evaluation_account_id": _id("existing600", source["generation_id"], account, evaluation_hash),
                "shared_pipeline_input_sha256": source["input_sha256"],
                "evaluation_source_sha256": evaluation_hash,
                "healer_status": status,
                "same_generation_h0_h1": "true",
                "evaluator_not_yet_executed": "true",
                "development_only": "true",
            })
    _require(len(rows) == 1200, "existing H0/H1 account count drift")
    _require(len({row["evaluation_account_id"] for row in rows}) == 1200, "existing account ID uniqueness drift")
    return rows


def _new_cells(tasks: list[dict[str, str]], pipeline_hash: str, healer_hash: str) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    generation_cells: list[dict[str, Any]] = []
    accounts: list[dict[str, str]] = []
    for task_index, task in enumerate(tasks):
        for sample_index, seed in enumerate(SEEDS):
            identity = f"{task['task_id']}|seed={seed}"
            for prompt_condition, run_id in (("P0", P0_RUN_ID), ("P1_candidate_b", P1_RUN_ID)):
                planned_id = _id("factorial_b28_v1", run_id, task["task_id"], seed)
                generation_cells.append({
                    "prompt_condition": prompt_condition,
                    "run_id": run_id,
                    "task_id": task["task_id"],
                    "seed": seed,
                    "task_index": task_index,
                    "sample_index": sample_index,
                    "paired_identity": identity,
                    "planned_cell_id": planned_id,
                    "attempt_count": 1,
                })
                for healer_account in ("H0", "H1"):
                    accounts.append({
                        "task_id": task["task_id"],
                        "seed": str(seed),
                        "paired_identity": identity,
                        "prompt_condition": prompt_condition,
                        "generation_run_id": run_id,
                        "generation_planned_cell_id": planned_id,
                        "healer_account": healer_account,
                        "evaluation_account_id": _id("factorial_b28_eval_v1", planned_id, healer_account),
                        "pipeline_sha256": pipeline_hash,
                        "healer_sha256": healer_hash,
                        "same_generation_h0_h1": "true",
                        "model_regeneration_for_healer": "false",
                        "development_only": "true",
                    })
    _require(len(generation_cells) == 280, "new generation cell count drift")
    _require(len(accounts) == 560, "new evaluation account count drift")
    _require(len({row["evaluation_account_id"] for row in accounts}) == 560, "new account ID uniqueness drift")
    _require(len({(cell["task_id"], cell["seed"]) for cell in generation_cells}) == 140, "new paired identity drift")
    return generation_cells, accounts


def _completion_gap() -> dict[str, Any]:
    return {
        "audit_version": "mbpp_final_factorial_completion_gap_v1",
        "overall_status": "incomplete_formal_validation_not_authorized",
        "requirements": [
            {"requirement": "four formal accounts P0_H0 P0_H1 P1_H0 P1_H1", "status": "specified_not_executed", "evidence": "factorial_evaluation_readiness_v1/factorial_accounting_spec.json"},
            {"requirement": "same Pipeline before H0/H1 fork", "status": "specified_source_hash_pinned_for_development_only", "evidence": PIPELINE_SOURCE.as_posix()},
            {"requirement": "same Healer version order guards for P0/P1", "status": "implemented_development_candidate_not_final_frozen", "evidence": HEALER_SOURCE.as_posix()},
            {"requirement": "rule trigger cells and unique tasks by condition", "status": "achieved_development_only", "evidence": "healer_candidate_v0_development_audit/healer_candidate_v0_rule_summary.csv"},
            {"requirement": "final P1", "status": "missing_independent_qualification", "evidence": "Candidate A failed preregistered format gate; Candidate B not yet executed"},
            {"requirement": "prospective validation identities", "status": "missing_and_unread", "evidence": "validation_task_ids remains empty"},
            {"requirement": "formal analysis and interaction claim rule", "status": "missing_final_freeze", "evidence": "draft plan explicitly leaves method pending"},
            {"requirement": "raw packaging ablation separate", "status": "specified", "evidence": "factorial_accounting_spec.json"},
        ],
        "next_authorized_stage": "execute_only_the_frozen_development_qualification_after_separate_operator_authorization",
        "formal_validation_allowed": False,
    }


def _existing_protocol(source_hashes: dict[str, str]) -> dict[str, Any]:
    return {
        "protocol_id": "mbpp_existing600_healer_h0_h1_development_eval_v1",
        "status": "frozen_not_executed_development_only",
        "programs": 600,
        "h0_accounts": 600,
        "h1_accounts": 600,
        "total_evaluation_accounts": 1200,
        "candidate_source_sha256": source_hashes[HEALER_SOURCE.as_posix()],
        "pipeline_source_sha256": source_hashes[PIPELINE_SOURCE.as_posix()],
        "accounting": "same persisted generation and Pipeline-normalized source forks to H0 unchanged and H1 candidate output",
        "all_accounts_itt": True,
        "pipeline_extraction_failure_retained": True,
        "healer_abstention_retained": True,
        "per_cell_accept_revert_or_selective_rule_use": False,
        "evaluator_used_to_accept_transformation": False,
        "model_regeneration": False,
        "analysis": {
            "report_by_prompt_condition": ["P0", "Scaffold-like"],
            "report": ["triggers cells/tasks", "transforms cells/tasks", "abstentions", "H0/H1 pass counts", "rescues", "regressions", "common pass", "common fail", "exact McNemar"],
            "claim_status": "retrospective_development_rule_construction_audit_only_no_confirmatory_claim",
            "all_regressions_disclosed": True,
        },
        "evalplus_executions_this_freeze": 0,
    }


def _qualification_plan(tasks: list[dict[str, str]], generation_cells: list[dict[str, Any]], source_hashes: dict[str, str]) -> dict[str, Any]:
    candidate_hash = _sha256_text(CANDIDATE_B_TEXT)
    pipeline_hash = source_hashes[PIPELINE_SOURCE.as_posix()]
    healer_hash = source_hashes[HEALER_SOURCE.as_posix()]
    path_budget = max(len(f"{path}/journals/{'f' * 64}.json") for path in (P0_PATH, P1_PATH))
    _require(path_budget < 240, "Windows path budget failed")
    return {
        "protocol_id": "mbpp_candidate_b28_factorial_development_qualification_v1",
        "status": "frozen_not_executed_development_only",
        "candidate_b": {
            "candidate_id": "candidate_b_concise_complete",
            "status": "frozen_experimental_candidate_not_official_p1",
            "exact_text_utf8": CANDIDATE_B_TEXT,
            "exact_text_sha256": candidate_hash,
            "same_candidate_a_40_retest_allowed": False,
        },
        "selection": {
            "tasks": len(tasks),
            "prior_frozen_hash_order_ranks": [FIRST_RANK, LAST_RANK],
            "selection_manual_override": False,
            "task_content_read": False,
            "remaining_unused_historical_development_tasks": 28,
            "rationale": "use exactly half of the 56 unused tasks and preserve the other half for one independent protocol if qualification fails",
        },
        "generation": {
            "p0": {"run_id": P0_RUN_ID, "physical_path": P0_PATH, "cells": 140, "prompt": "official prompt only"},
            "p1": {"run_id": P1_RUN_ID, "physical_path": P1_PATH, "cells": 140, "prompt": "official prompt + fixed separator + Candidate B exact text"},
            "total_cells": 280,
            "paired_task_seed_identities": 140,
            "cells": generation_cells,
            "exactly_one_attempt": True,
            "retry_resume_selective_retry_overwrite": False,
            "run_directories_created_by_this_freeze": False,
        },
        "evaluation": {
            "factorial_accounts": ["P0_H0", "P0_H1", "P1_H0", "P1_H1"],
            "accounts": 560,
            "order": "generation -> identical frozen Pipeline -> H0/H1 fork -> evaluation",
            "pipeline_sha256": pipeline_hash,
            "healer_sha256": healer_hash,
            "same_healer_version_order_guards": True,
            "healer_model_regeneration": False,
            "pipeline_packaging_is_healer": False,
        },
        "model_protocol": {
            "model": "qwen3.5:9b",
            "digest": "6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7",
            "quantization": "Q4_K_M",
            "think": False,
            "timeout_seconds": 600,
            "sampling": {"temperature": 0.2, "top_p": 0.95, "top_k": 20, "num_ctx": 8192, "num_predict": 2048},
            "seeds": list(SEEDS),
        },
        "prompt_composition": {"separator_exact_text_utf8": SEPARATOR, "separator_sha256": _sha256_text(SEPARATOR)},
        "promotion_gates": {
            "p1_format": {"strict_python_only_min": 0.90, "fence_rate_max": 0.05, "extra_text_rate_max": 0.05, "pipeline_extraction_success_min": 0.95},
            "p1_correctness_safety": {"pipeline_pass_not_below_p0": True, "rescues_at_least_regressions": True, "all_regressions_disclosed": True},
            "p1_claim": "correctness improvement only if rescues > regressions and exact McNemar p < 0.05",
            "healer_static": {"changes_outside_trigger": 0, "ast_prefix_preservation_rate": 1.0, "same_source_order_guards_both_conditions": True},
            "healer_evidence": {"pooled_trigger_cells_min": 5, "pooled_trigger_unique_tasks_min": 3, "trigger_cells_each_prompt_condition_min": 1, "pooled_rescues_min": 1, "transformed_pass_to_fail_regressions_max": 0},
            "joint_activation": "formal validation remains forbidden unless both final P1 and final Healer are separately frozen after all applicable gates",
        },
        "failure_policy": {
            "modify_and_rerun_same_28": False,
            "mix_other_candidate_into_results": False,
            "future_protocol_may_use_only_remaining_unused_28": True,
        },
        "windows_path_budget": {"maximum_planned_journal_path_characters": path_budget, "limit": 240, "passed": True},
        "model_calls_this_freeze": 0,
        "evalplus_executions_this_freeze": 0,
    }


def _report(plan: dict[str, Any]) -> bytes:
    lines = [
        "# MBPP+ 2×2 development qualification v1",
        "",
        "目前正式2×2尚未完成：Candidate A有correctness改善但format gate失敗；Healer只有靜態安全證據，尚無完整H0/H1功能帳；validation名單仍未讀取也未凍結。",
        "",
        "## 既有600程式的Healer稽核",
        "",
        "已凍結1200個development-only評估帳：每份既有Pipeline-normalized程式各有H0原樣帳與H1候選帳。兩帳共享generation與Pipeline輸入；不得重新生成、選擇性接受或在看到evaluator結果後撤回個別轉換。本輪尚未執行評估。",
        "",
        "## Candidate B的新資料資格測試",
        "",
        f"從既有公開hash排序的未使用56題中，固定取排名{FIRST_RANK}至{LAST_RANK}的28題；不讀prompt、答案或tests，並保留另外28題。每題5 seeds，P0與Candidate B各140 generations，共280；之後同一generation分H0/H1，形成560個development-only評估帳。",
        "",
        "Candidate B只是`frozen_experimental_candidate_not_official_p1`。它不能回到Candidate A的40題重測；若失敗，不得修改後重跑這28題。Healer也必須在P0與P1使用完全相同source、rule order與guards。",
        "",
        "## 為何仍不能進validation",
        "",
        "本次只凍結下一階段protocol與名單，未建立run directory、未呼叫模型、未執行EvalPlus。只有完成新development qualification、依預註冊gates分別凍結final P1與final Healer，再凍結validation identities、sampling與analysis claim rules，才能啟用正式validation。",
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def build_outputs(repo_root: Path = REPO_ROOT) -> dict[str, bytes]:
    repo_root = repo_root.resolve()
    expansion = _read_json(repo_root / EXPANSION_MANIFEST)
    healer_spec = _read_json(repo_root / HEALER_SPEC)
    _require(healer_spec["status"] == healer.CANDIDATE_STATUS, "Healer candidate status drift")
    scaffold_rows = _read_csv(repo_root / M2G_SCAFFOLD)
    _require(
        {row["exact_text_draft_utf8"] for row in scaffold_rows if row["candidate_id"] == "candidate_b_concise_complete_draft"}
        == {CANDIDATE_B_TEXT},
        "Candidate B exact-text draft drift",
    )
    source_hashes = _source_hashes(repo_root)
    tasks = _select_new_tasks(expansion)
    existing_accounts = _existing_accounts(_read_csv(repo_root / HEALER_LEDGER))
    generation_cells, new_accounts = _new_cells(
        tasks, source_hashes[PIPELINE_SOURCE.as_posix()], source_hashes[HEALER_SOURCE.as_posix()]
    )
    plan = _qualification_plan(tasks, generation_cells, source_hashes)
    for path in (repo_root / P0_PATH, repo_root / P1_PATH):
        _require(not path.exists(), f"run directory must not exist: {path}")
    outputs = {
        "completion_gap_audit.json": _json_bytes(_completion_gap()),
        "existing_600_healer_evaluation_protocol.json": _json_bytes(_existing_protocol(source_hashes)),
        "existing_600_h0_h1_account_plan.csv": _csv_bytes(existing_accounts, EXISTING_ACCOUNT_FIELDS),
        "candidate_b_exact_text.txt": CANDIDATE_B_TEXT.encode("utf-8"),
        "candidate_b_new28_selection.csv": _csv_bytes(tasks, SELECTION_FIELDS),
        "candidate_b_2x2_development_plan.json": _json_bytes(plan),
        "candidate_b_2x2_account_plan.csv": _csv_bytes(new_accounts, NEW_ACCOUNT_FIELDS),
        "factorial_development_qualification_summary_zh.md": _report(plan),
    }
    manifest = {
        "manifest_version": "mbpp_factorial_development_qualification_v1",
        "status": "frozen_not_executed_development_only",
        "counts": {"new_tasks": 28, "new_task_seed_identities": 140, "planned_generations": 280, "planned_new_factorial_accounts": 560, "existing_programs": 600, "planned_existing_h0_h1_accounts": 1200, "remaining_unused_development_tasks": 28},
        "candidate_b_sha256": _sha256_text(CANDIDATE_B_TEXT),
        "pipeline_sha256": source_hashes[PIPELINE_SOURCE.as_posix()],
        "healer_sha256": source_hashes[HEALER_SOURCE.as_posix()],
        "source_sha256": source_hashes,
        "validation_tasks_read": False,
        "confirmatory_or_sealed_tasks_read": False,
        "run_directories_created": False,
        "model_calls": 0,
        "evalplus_executions": 0,
        "output_sha256_excluding_manifest": {name: _sha256(content) for name, content in sorted(outputs.items())},
    }
    outputs["factorial_development_qualification_manifest.json"] = _json_bytes(manifest)
    return outputs


def write_outputs(repo_root: Path = REPO_ROOT, check: bool = False) -> None:
    output_dir = repo_root.resolve() / OUTPUT_RELATIVE
    outputs = build_outputs(repo_root)
    if check:
        _require(output_dir.is_dir(), "output directory missing")
        _require({path.name for path in output_dir.iterdir() if path.is_file()} == set(outputs), "output file set drift")
        for name, content in outputs.items():
            _require((output_dir / name).read_bytes() == content, f"deterministic bytes drift: {name}")
        return
    _require(not output_dir.exists(), "output directory exists; overwrite forbidden")
    output_dir.mkdir(parents=True)
    for name, content in outputs.items():
        (output_dir / name).write_bytes(content)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        write_outputs(check=args.check)
    except QualificationFreezeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
