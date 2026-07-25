"""Freeze the full-cohort static audit and minimal functional preregistration."""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import io
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_tools.finals_rebuild.mbpp_h2_module_assert_quarantine import (  # noqa: E402
    quarantine_module_assert_entrypoint_selftest,
)
from agent_tools.finals_rebuild.mbpp_top_level_demo_print_quarantine import (  # noqa: E402
    RULE_ID,
    RULE_STATUS,
    assert_fingerprint,
    quarantine_top_level_literal_only_demo_print,
)


OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_governance/"
    "top_level_demo_print_quarantine_development_v1"
)
RULE_RELATIVE = Path(
    "agent_tools/finals_rebuild/mbpp_top_level_demo_print_quarantine.py"
)
H2_RULE_RELATIVE = Path(
    "agent_tools/finals_rebuild/mbpp_h2_module_assert_quarantine.py"
)
RUNNER_RELATIVE = Path(
    "scripts/run_top_level_demo_print_quarantine_functional_eval_v1.py"
)
INVENTORY_RELATIVE = Path(
    "artifacts/public_benchmark_governance/"
    "deterministic_healer_candidate_inventory_4b9b_v1"
)
FOUR_B_RELATIVE = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_4b_failure_supply_pilot_analysis_v1"
)
NINE_B_RUN_RELATIVE = Path(
    "artifacts/public_benchmark_development/mbpp_candidate_b_development60/"
    "runs/mbpp_q35_9b_candidate_b_development60_replay_r003"
)
NINE_B_RESULT_RELATIVE = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_h0_h1_evalplus_v1/manual_evalplus_run_001"
)
H2_EVAL_RELATIVE = Path(
    "artifacts/public_benchmark_governance/"
    "h2_module_assert_quarantine_functional_evaluation_v1"
)
TASKS_RELATIVE = Path("data/mbpp_plus/tasks.jsonl")
DATASET_MANIFEST_RELATIVE = Path("data/mbpp_plus/dataset_manifest.json")
EXPECTED_RULE_SHA = "a0b89828b2f3e524fd8d03a64bc0a5afe00b38b774aae47572d22c0e0a7f3ee9"
EXPECTED_H1_SHA = "cf4d086ca6e3af968f31b0d087ed2479e5ad38be4b7abe5d2ce5516b68000d44"
EXPECTED_H2_SHA = "dbd96fc3c1228f74c784e2444350102de121d4e202dcb0075aad214090bbfa18"
EXPECTED_DATASET_VERSION = "v0.2.0"
EXPECTED_DATASET_HASH = "ee43ecabebf20deef4bb776a405ac5b1"
EXPECTED_EVALPLUS_VERSION = "0.3.1"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def jsonl_bytes(rows: list[dict[str, Any]]) -> bytes:
    return "".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows
    ).encode("utf-8")


def csv_bytes(rows: list[dict[str, Any]], fields: list[str]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field, "") for field in fields})
    return stream.getvalue().encode("utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def public_assert_fingerprints(prompt: str) -> tuple[str, ...]:
    fingerprints: list[str] = []
    for line in prompt.splitlines():
        if not line.lstrip().startswith("assert "):
            continue
        try:
            statement = ast.parse(line.strip()).body[0]
        except (SyntaxError, IndexError):
            continue
        if isinstance(statement, ast.Assert):
            fingerprints.append(assert_fingerprint(statement))
    return tuple(fingerprints)


def tasks(repo_root: Path) -> tuple[dict[str, dict[str, str]], dict[str, Any]]:
    manifest = json.loads(
        (repo_root / DATASET_MANIFEST_RELATIVE).read_text(encoding="utf-8")
    )
    require(manifest["dataset_name"] == "MBPP+", "dataset drift")
    require(
        manifest["official_tests_and_canonical_solutions_included"] is False,
        "forbidden evaluation material present",
    )
    require(
        manifest["stored_fields"] == ["task_id", "prompt", "entry_point"],
        "unexpected task fields",
    )
    task_bytes = (repo_root / TASKS_RELATIVE).read_bytes()
    require(sha256_bytes(task_bytes) == manifest["tasks_sha256"], "task SHA drift")
    rows = read_jsonl(repo_root / TASKS_RELATIVE)
    require(
        all(set(row) == {"task_id", "prompt", "entry_point"} for row in rows),
        "unexpected task record",
    )
    return {row["task_id"]: row for row in rows}, manifest


def raw_strict(base_status: str, plus_status: str) -> str:
    return "pass" if base_status == plus_status == "pass" else "fail"


def four_b_records(
    repo_root: Path, task_map: dict[str, dict[str, str]]
) -> list[dict[str, Any]]:
    root = repo_root / FOUR_B_RELATIVE
    frozen = json.loads((root / "frozen_input_manifest.json").read_text("utf-8"))
    require(frozen["counts"]["cells"] == 200, "4B population drift")
    inventory = {
        row["generation_id"]: row
        for row in read_csv(root / "generation_evidence_inventory.csv")
    }
    extraction = {
        row["generation_id"]: row
        for row in read_csv(root / "extraction_itt_ledger.csv")
    }
    cells = read_csv(root / "cell_itt_ledger.csv")
    eval_sources = {
        row["generation_id"]: row
        for row in read_jsonl(root / "h0_evalplus_input.jsonl")
    }
    results = {
        row["cell_identity"]: row
        for row in read_csv(root / "manual_h0_evalplus_run_001/h0_evalplus_results.csv")
    }
    require(len(cells) == len(inventory) == len(extraction) == 200, "4B roster drift")
    records: list[dict[str, Any]] = []
    for cell in cells:
        generation_id = cell["generation_id"]
        inv = inventory[generation_id]
        ext = extraction[generation_id]
        journal_path = repo_root / inv["journal_path"]
        journal_bytes = journal_path.read_bytes()
        require(sha256_bytes(journal_bytes) == inv["journal_sha256"], "4B journal SHA")
        journal = json.loads(journal_bytes)
        raw_body = json.loads(journal["response_metadata"]["raw_body"])
        extracted = ext["extraction_status"] == "extracted" and ext["candidate_count"] == "1"
        if extracted:
            selected = eval_sources[generation_id]
            source = selected["completion"]
            require(
                sha256_bytes(source.encode()) == ext["extracted_code_sha256"],
                "4B extracted SHA",
            )
        else:
            source = journal["raw_response"]
        task = task_map[cell["task_id"]]
        decision = quarantine_top_level_literal_only_demo_print(
            source,
            task["entry_point"],
            extraction_unambiguous=extracted,
            source_complete=raw_body.get("done_reason") == "stop",
            public_assert_fingerprints=public_assert_fingerprints(task["prompt"]),
        )
        raw_result = results.get(cell["cell_identity"])
        records.append(
            {
                "cohort": "4B_complete_development200",
                "cell_id": cell["cell_identity"],
                "cell_index": int(cell["cell_index"]),
                "program_id": cell["program_id"],
                "generation_id": generation_id,
                "task_id": cell["task_id"],
                "seed": int(cell["seed"]),
                "condition": cell["condition_id"],
                "model": inv["model_tag"],
                "entry_point": task["entry_point"],
                "source": source,
                "source_sha256": sha256_bytes(source.encode()),
                "raw_response_sha256": inv["raw_response_sha256"],
                "extraction_unambiguous": extracted,
                "source_complete": raw_body.get("done_reason") == "stop",
                "raw_result": raw_result,
                "raw_result_authority": (
                    FOUR_B_RELATIVE / "manual_h0_evalplus_run_001/h0_evalplus_results.csv"
                ).as_posix(),
                "decision": decision,
            }
        )
    return records


def nine_b_records(
    repo_root: Path, task_map: dict[str, dict[str, str]]
) -> list[dict[str, Any]]:
    root = repo_root / NINE_B_RUN_RELATIVE
    raw = {row["program_id"]: row for row in read_jsonl(root / "raw_generations.jsonl")}
    accounts = {
        row["program_id"]: row
        for row in read_jsonl(root / "h0_h1_accounts.jsonl")
        if row["healer_account"] == "H0"
    }
    results = {
        row["program_id"]: row
        for row in read_csv(
            repo_root / NINE_B_RESULT_RELATIVE / "evalplus_results.csv"
        )
        if row["healer_account"] == "H0"
    }
    require(len(raw) == len(accounts) == len(results) == 300, "9B population drift")
    records: list[dict[str, Any]] = []
    for program_id, account in sorted(
        accounts.items(), key=lambda item: int(raw[item[0]]["cell_index"])
    ):
        generation = raw[program_id]
        source = account["evaluation_source"]
        require(
            sha256_bytes(source.encode()) == account["evaluation_source_sha256"],
            "9B source SHA",
        )
        task = task_map[account["task_id"]]
        decision = quarantine_top_level_literal_only_demo_print(
            source,
            task["entry_point"],
            extraction_unambiguous=True,
            source_complete=generation["generation_metadata"].get("done_reason") == "stop",
            public_assert_fingerprints=public_assert_fingerprints(task["prompt"]),
        )
        records.append(
            {
                "cohort": "9B_complete_development300",
                "cell_id": program_id,
                "cell_index": int(generation["cell_index"]),
                "program_id": program_id,
                "generation_id": account["generation_id"],
                "task_id": account["task_id"],
                "seed": int(account["seed"]),
                "condition": "Candidate_B_H0",
                "model": "qwen3.5:9b",
                "entry_point": task["entry_point"],
                "source": source,
                "source_sha256": account["evaluation_source_sha256"],
                "raw_response_sha256": generation["raw_response_sha256"],
                "extraction_unambiguous": True,
                "source_complete": generation["generation_metadata"].get("done_reason") == "stop",
                "raw_result": results[program_id],
                "raw_result_authority": (
                    NINE_B_RESULT_RELATIVE / "evalplus_results.csv"
                ).as_posix(),
                "decision": decision,
            }
        )
    return records


def build_outputs(repo_root: Path) -> dict[str, bytes]:
    rule_bytes = (repo_root / RULE_RELATIVE).read_bytes()
    h2_rule_bytes = (repo_root / H2_RULE_RELATIVE).read_bytes()
    require(sha256_bytes(rule_bytes) == EXPECTED_RULE_SHA, "new rule SHA drift")
    require(sha256_bytes(h2_rule_bytes) == EXPECTED_H2_SHA, "H2 SHA drift")
    task_map, dataset_manifest = tasks(repo_root)
    # Static decisions are completed for all 500 cells before outcome fields are used.
    records = four_b_records(repo_root, task_map) + nine_b_records(repo_root, task_map)
    require(len(records) == 500, "full development cohort is not 500")
    require(len({(row["model"], row["cell_id"]) for row in records}) == 500, "duplicate")
    transformed = [row for row in records if row["decision"].transformed]
    require(len(transformed) == 21, f"expected 21 transforms, got {len(transformed)}")
    require(
        {
            "5ac277bdc6b75e21aa18043943c5f72d3c2ebdb67c21a4b75b6f5a1d405433fc",
            "93e763a6916038e0e019b7d602e32aa1daccaa75365b3a053b1dc89ad7425b1b",
        }
        <= {row["source_sha256"] for row in transformed},
        "formal development evidence missing from full-cohort transforms",
    )

    h2_existing_roster = {
        row["program_id"]: row
        for row in read_jsonl(repo_root / H2_EVAL_RELATIVE / "cell_roster.jsonl")
    }
    h2_existing_sources = {
        row["program_id"]: row
        for row in read_jsonl(repo_root / H2_EVAL_RELATIVE / "post_h2_eval_input.jsonl")
    }
    h2_existing_results = {
        row["program_id"]: row
        for row in read_csv(
            repo_root
            / H2_EVAL_RELATIVE
            / "manual_post_h2_evalplus_run_001/post_h2_evalplus_results.csv"
        )
    }

    audit_rows: list[dict[str, Any]] = []
    source_rows: list[dict[str, Any]] = []
    plan_rows: list[dict[str, Any]] = []
    functional_rows: list[dict[str, Any]] = []
    for row in records:
        decision = row["decision"]
        raw_result = row["raw_result"]
        raw_base = raw_result["base_status"] if raw_result else ""
        raw_plus = raw_result["plus_status"] if raw_result else ""
        strict = raw_strict(raw_base, raw_plus) if raw_result else "not_evaluated"
        audit_rows.append(
            {
                "cohort": row["cohort"],
                "cell_id": row["cell_id"],
                "cell_index": row["cell_index"],
                "program_id": row["program_id"],
                "task_id": row["task_id"],
                "seed": row["seed"],
                "condition": row["condition"],
                "model": row["model"],
                "entry_point": row["entry_point"],
                "source_sha256": row["source_sha256"],
                "output_sha256": decision.output_sha256,
                "triggered": str(decision.triggered).lower(),
                "transformed": str(decision.transformed).lower(),
                "abstained": str(decision.abstained).lower(),
                "reason": decision.reason,
                "guard_results_json": json.dumps(
                    decision.guard_results, sort_keys=True, separators=(",", ":")
                ),
                "raw_control_status": strict,
                "outcome_blind_rule_decision": "true",
            }
        )
        if not decision.transformed:
            continue
        idempotence = quarantine_top_level_literal_only_demo_print(
            decision.output_source,
            row["entry_point"],
            extraction_unambiguous=True,
            source_complete=True,
            public_assert_fingerprints=public_assert_fingerprints(
                task_map[row["task_id"]]["prompt"]
            ),
        )
        require(
            not idempotence.transformed
            and idempotence.output_source == decision.output_source,
            "idempotence failure",
        )
        h2_raw = quarantine_module_assert_entrypoint_selftest(
            row["source"],
            row["entry_point"],
            extraction_unambiguous=True,
            source_complete=True,
        )
        h2_combined = quarantine_module_assert_entrypoint_selftest(
            decision.output_source,
            row["entry_point"],
            extraction_unambiguous=True,
            source_complete=True,
        )
        require(h2_raw.transformed and h2_combined.transformed, "H2 composition failure")
        source_rows.append(
            {
                "cell_id": row["cell_id"],
                "program_id": row["program_id"],
                "task_id": row["task_id"],
                "seed": row["seed"],
                "entry_point": row["entry_point"],
                "raw_source_sha256": row["source_sha256"],
                "raw_source": row["source"],
                "demo_print_source_sha256": decision.output_sha256,
                "demo_print_source": decision.output_source,
                "h2_source_sha256": h2_raw.output_sha256,
                "h2_source": h2_raw.output_source,
                "combined_source_sha256": h2_combined.output_sha256,
                "combined_source": h2_combined.output_source,
                "composition_order": ["demo_print", "H2"],
            }
        )
        existing = h2_existing_roster.get(row["program_id"])
        reuse_h2 = bool(existing and existing["transformed"])
        if reuse_h2:
            require(
                existing["pipeline_source_sha256"] == row["source_sha256"]
                and existing["post_h2_source_sha256"] == h2_raw.output_sha256,
                "existing H2 source identity mismatch",
            )
            require(
                h2_existing_sources[row["program_id"]]["completion"]
                == h2_raw.output_source,
                "existing H2 output bytes mismatch",
            )
        raw_result = row["raw_result"]
        require(raw_result is not None, "transformed target lacks Raw result")
        for arm, source, source_sha, disposition in [
            ("raw", row["source"], row["source_sha256"], "reuse_formal_raw"),
            (
                "demo_print_only",
                decision.output_source,
                decision.output_sha256,
                "execute_new",
            ),
            (
                "h2_only",
                h2_raw.output_source,
                h2_raw.output_sha256,
                "reuse_existing_h2" if reuse_h2 else "execute_new",
            ),
            (
                "h2_plus_demo_print",
                h2_combined.output_source,
                h2_combined.output_sha256,
                "execute_new",
            ),
        ]:
            plan = {
                "cell_id": row["cell_id"],
                "program_id": row["program_id"],
                "task_id": row["task_id"],
                "seed": row["seed"],
                "entry_point": row["entry_point"],
                "arm": arm,
                "source_sha256": source_sha,
                "execution_disposition": disposition,
                "rule_sha256": EXPECTED_RULE_SHA if "demo_print" in arm else "",
                "h2_sha256": EXPECTED_H2_SHA if arm in {"h2_only", "h2_plus_demo_print"} else "",
            }
            if disposition == "reuse_formal_raw":
                plan.update(
                    {
                        "reused_base_status": raw_result["base_status"],
                        "reused_plus_status": raw_result["plus_status"],
                        "reused_strict_status": raw_strict(
                            raw_result["base_status"], raw_result["plus_status"]
                        ),
                        "reuse_authority": row["raw_result_authority"],
                    }
                )
            elif disposition == "reuse_existing_h2":
                result = h2_existing_results[row["program_id"]]
                plan.update(
                    {
                        "reused_base_status": result["base_status"],
                        "reused_plus_status": result["plus_status"],
                        "reused_strict_status": result["strict_status"],
                        "reuse_authority": (
                            H2_EVAL_RELATIVE
                            / "manual_post_h2_evalplus_run_001/post_h2_evalplus_results.csv"
                        ).as_posix(),
                    }
                )
            else:
                plan.update(
                    {
                        "reused_base_status": "",
                        "reused_plus_status": "",
                        "reused_strict_status": "",
                        "reuse_authority": "",
                    }
                )
                functional_rows.append(
                    {
                        "evaluation_order": len(functional_rows) + 1,
                        "cell_id": row["cell_id"],
                        "program_id": row["program_id"],
                        "task_id": row["task_id"],
                        "seed": row["seed"],
                        "entry_point": row["entry_point"],
                        "arm": arm,
                        "source_sha256": source_sha,
                        "completion": source,
                    }
                )
            plan_rows.append(plan)

    require(len(source_rows) == 21 and len(plan_rows) == 84, "plan count drift")
    require(len(functional_rows) == 50, "minimal execution is not 50 arms")
    require(
        Counter(row["raw_control_status"] for row in audit_rows)
        == Counter({"fail": 358, "pass": 128, "not_evaluated": 14}),
        "Raw control distribution drift",
    )
    # Fourteen ambiguous 4B extraction cells lack a formal Raw evaluation.
    require(
        all(
            row["source_sha256"] == row["output_sha256"]
            for row in audit_rows
            if row["raw_control_status"] == "pass" and row["transformed"] == "false"
        ),
        "abstained Raw PASS control changed",
    )

    audit_fields = [
        "cohort",
        "cell_id",
        "cell_index",
        "program_id",
        "task_id",
        "seed",
        "condition",
        "model",
        "entry_point",
        "source_sha256",
        "output_sha256",
        "triggered",
        "transformed",
        "abstained",
        "reason",
        "guard_results_json",
        "raw_control_status",
        "outcome_blind_rule_decision",
    ]
    audit_bytes = csv_bytes(audit_rows, audit_fields)
    sources_bytes = jsonl_bytes(source_rows)
    plan_bytes = jsonl_bytes(plan_rows)
    functional_bytes = jsonl_bytes(functional_rows)
    schema = {
        "schema_id": "top_level_demo_print_quarantine_development_v1",
        "static_audit_rows": 500,
        "transformed_rows": 21,
        "evaluation_plan_arms": 84,
        "new_evalplus_cells": 50,
        "audit_required_fields": audit_fields,
        "metrics": [
            "verified_rescue",
            "partial_repair",
            "unchanged_failure",
            "preserved_pass",
            "regression",
            "blocker_removed",
        ],
    }
    summary = {
        "cohort": {"4B": 200, "9B": 300, "total": 500},
        "static_decisions": {
            "transformed": 21,
            "abstained": 479,
            "reason_counts": dict(
                sorted(Counter(row["reason"] for row in audit_rows).items())
            ),
        },
        "raw_controls": dict(
            sorted(Counter(row["raw_control_status"] for row in audit_rows).items())
        ),
        "outcome_blind": True,
        "model_calls": 0,
        "candidate_executions": 0,
        "evalplus_executions": 0,
    }
    core = {
        "frozen_rule.py": rule_bytes,
        "static_audit_ledger.csv": audit_bytes,
        "transformed_sources.jsonl": sources_bytes,
        "four_arm_evaluation_plan.jsonl": plan_bytes,
        "functional_eval_input.jsonl": functional_bytes,
        "schema.json": json_bytes(schema),
        "static_audit_summary.json": json_bytes(summary),
    }
    frozen_files = {name: sha256_bytes(data) for name, data in sorted(core.items())}
    source_paths = [
        INVENTORY_RELATIVE / "candidate_ledger.csv",
        INVENTORY_RELATIVE / "summary.json",
        FOUR_B_RELATIVE / "frozen_input_manifest.json",
        FOUR_B_RELATIVE / "generation_evidence_inventory.csv",
        FOUR_B_RELATIVE / "extraction_itt_ledger.csv",
        FOUR_B_RELATIVE / "h0_evalplus_input.jsonl",
        FOUR_B_RELATIVE / "manual_h0_evalplus_run_001/h0_evalplus_results.csv",
        NINE_B_RUN_RELATIVE / "raw_generations.jsonl",
        NINE_B_RUN_RELATIVE / "h0_h1_accounts.jsonl",
        NINE_B_RESULT_RELATIVE / "evalplus_results.csv",
        H2_EVAL_RELATIVE / "cell_roster.jsonl",
        H2_EVAL_RELATIVE / "post_h2_eval_input.jsonl",
        H2_EVAL_RELATIVE / "manual_post_h2_evalplus_run_001/post_h2_evalplus_results.csv",
        TASKS_RELATIVE,
        DATASET_MANIFEST_RELATIVE,
    ]
    source_sha = {
        path.as_posix(): sha256_bytes((repo_root / path).read_bytes())
        for path in source_paths
    }
    preregistration = {
        "preregistration_id": "top_level_demo_print_quarantine_development_v1",
        "status": "preregistered_not_executed",
        "research_role": "development_candidate",
        "confirmatory_claim": False,
        "rule": {
            "rule_id": RULE_ID,
            "status": RULE_STATUS,
            "path": RULE_RELATIVE.as_posix(),
            "sha256": EXPECTED_RULE_SHA,
            "guard_changes_after_preregistration": "forbidden",
        },
        "h1": {
            "rule_id": "entrypoint_alias_unique_arity_compatible_v0",
            "sha256": EXPECTED_H1_SHA,
            "modified": False,
        },
        "h2": {
            "rule_id": "module_assert_entrypoint_selftest_quarantine_v0",
            "sha256": EXPECTED_H2_SHA,
            "modified_or_merged": False,
            "composition_order": "demo_print_then_H2",
            "attribution": "separate",
        },
        "static_audit": {
            "full_development_cohort": 500,
            "four_b": 200,
            "nine_b": 300,
            "raw_pass_controls": 128,
            "transformed": 21,
            "abstained": 479,
            "outcome_blind_rule_decision": True,
        },
        "arms": ["raw", "demo_print_only", "h2_only", "h2_plus_demo_print"],
        "execution": {
            "new_evalplus_cells": 50,
            "raw_reused": 21,
            "h2_reused": 13,
            "parallel": 1,
            "retry_resume_overwrite": False,
            "model_calls": 0,
            "candidate_generations": 0,
        },
        "evaluator": {
            "engine": "evalplus_0.3.1_check_correctness_subset",
            "evalplus_version": EXPECTED_EVALPLUS_VERSION,
            "dataset": "MBPP+",
            "dataset_version": EXPECTED_DATASET_VERSION,
            "dataset_hash": EXPECTED_DATASET_HASH,
            "os": "WSL2 Ubuntu/Linux",
            "python": "/home/yehya/.venvs/ast_evalplus/bin/python",
            "python_version": "3.14.4",
            "parallel": 1,
            "runner": RUNNER_RELATIVE.as_posix(),
            "runner_sha256": sha256_bytes((repo_root / RUNNER_RELATIVE).read_bytes()),
        },
        "definitions": {
            "verified_rescue": "Raw strict FAIL -> arm strict PASS",
            "partial_repair": "Raw strict FAIL -> arm strict FAIL AND blocker_removed",
            "unchanged_failure": "Raw strict FAIL -> arm strict FAIL AND NOT blocker_removed",
            "preserved_pass": "Raw strict PASS -> arm strict PASS",
            "regression": "Raw strict PASS -> arm strict FAIL",
            "blocker_removed": (
                "arm returns PASS on either suite or at least one per-test detail"
            ),
        },
        "freeze_criteria": {
            "A": (
                "regression=0 AND every Raw PASS preserved AND verified_rescue>=1 "
                "AND determinism/idempotence/AST/provenance all pass => "
                "development_rule_frozen_no_confirmatory_claim"
            ),
            "B": (
                "regression=0 AND verified_rescue=0 => "
                "development_candidate_not_frozen"
            ),
            "C": "regression>0 => development_rejected_pending_review",
            "priority": "C, then A, then B",
            "post_outcome_guard_change_or_rerun": "forbidden",
        },
        "frozen_files": frozen_files,
        "source_sha256": source_sha,
        "dataset_manifest": dataset_manifest,
        "forbidden": [
            "model generation",
            "hidden test inspection",
            "canonical solution inspection",
            "post-outcome guard modification",
            "selective rerun",
            "H1 modification",
            "H2 modification or merge",
        ],
    }
    core["preregistration.json"] = json_bytes(preregistration)
    return core


def write_or_check(repo_root: Path, check: bool) -> None:
    expected = build_outputs(repo_root)
    output_dir = repo_root / OUTPUT_RELATIVE
    if check:
        require(output_dir.is_dir(), "output directory missing")
        for name, data in expected.items():
            require((output_dir / name).read_bytes() == data, f"rebuild drift: {name}")
        return
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, data in expected.items():
        (output_dir / name).write_bytes(data)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    args = parser.parse_args()
    write_or_check(args.repo_root.resolve(), args.check)
    print("top_level_demo_print_quarantine_development_v1_preregistered: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
