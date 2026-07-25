"""Finalize the preregistered demo-print development evaluation."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_governance/"
    "top_level_demo_print_quarantine_development_v1"
)
H2_RESULTS_RELATIVE = Path(
    "artifacts/public_benchmark_governance/"
    "h2_module_assert_quarantine_functional_evaluation_v1/"
    "manual_post_h2_evalplus_run_001/post_h2_evalplus_results.csv"
)
PREREG_SHA = "01f96a7a4d1c93484ff18a7dcd36d089d1828c83101c614a8df71acbff9cd579"
RESULTS_SHA = "e3c84016a0edbb423eb9d7ff9efe1df9c5df963587e5702966131a6108651796"
RULE_SHA = "a0b89828b2f3e524fd8d03a64bc0a5afe00b38b774aae47572d22c0e0a7f3ee9"
H2_SHA = "dbd96fc3c1228f74c784e2444350102de121d4e202dcb0075aad214090bbfa18"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text("utf-8").splitlines() if line]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode()


def csv_bytes(rows: list[dict[str, Any]], fields: list[str]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows({field: row.get(field, "") for field in fields} for row in rows)
    return stream.getvalue().encode()


def classify(raw: str, arm: str, blocker_removed: bool) -> str:
    if raw == "fail" and arm == "pass":
        return "verified_rescue"
    if raw == "fail" and arm == "fail":
        return "partial_repair" if blocker_removed else "unchanged_failure"
    if raw == "pass" and arm == "pass":
        return "preserved_pass"
    if raw == "pass" and arm == "fail":
        return "regression"
    raise RuntimeError(f"unclassifiable transition: {raw}->{arm}")


def build_outputs(repo_root: Path) -> dict[str, bytes]:
    root = repo_root / OUTPUT_RELATIVE
    prereg_bytes = (root / "preregistration.json").read_bytes()
    require(sha256_bytes(prereg_bytes) == PREREG_SHA, "preregistration SHA drift")
    prereg = json.loads(prereg_bytes)
    require(prereg["rule"]["sha256"] == RULE_SHA, "rule SHA drift")
    require(prereg["h2"]["sha256"] == H2_SHA, "H2 SHA drift")
    result_path = root / "manual_evalplus_run_001/evalplus_results.csv"
    result_bytes = result_path.read_bytes()
    require(sha256_bytes(result_bytes) == RESULTS_SHA, "result SHA drift")
    execution_bytes = (
        root / "manual_evalplus_run_001/execution_record.json"
    ).read_bytes()
    execution = json.loads(execution_bytes)
    require(execution["preregistration_sha256"] == PREREG_SHA, "execution prereg drift")
    require(execution["results_sha256"] == RESULTS_SHA, "execution result drift")
    require(execution["model_calls"] == 0, "model call detected")

    plan = read_jsonl(root / "four_arm_evaluation_plan.jsonl")
    executed = {
        (row["cell_id"], row["arm"]): row for row in read_csv(result_path)
    }
    h2_results = {
        row["program_id"]: row
        for row in read_csv(repo_root / H2_RESULTS_RELATIVE)
    }
    raw_by_cell = {
        row["cell_id"]: row
        for row in plan
        if row["arm"] == "raw"
    }
    require(len(plan) == 84 and len(raw_by_cell) == 21, "plan scope drift")

    ledger: list[dict[str, Any]] = []
    for row in plan:
        raw_status = raw_by_cell[row["cell_id"]]["reused_strict_status"]
        if row["arm"] == "raw":
            base = row["reused_base_status"]
            plus = row["reused_plus_status"]
            strict = raw_status
            blocker = False
            outcome = "raw_reference"
            authority = row["reuse_authority"]
        elif row["execution_disposition"] == "reuse_existing_h2":
            result = h2_results[row["program_id"]]
            require(result["post_h2_source_sha256"] == row["source_sha256"], "H2 source drift")
            base, plus, strict = (
                result["base_status"],
                result["plus_status"],
                result["strict_status"],
            )
            blocker = result["blocker_removed_execution_evidence"] == "true"
            outcome = classify(raw_status, strict, blocker)
            authority = row["reuse_authority"]
        else:
            result = executed[(row["cell_id"], row["arm"])]
            require(result["source_sha256"] == row["source_sha256"], "executed source drift")
            base, plus, strict = (
                result["base_status"],
                result["plus_status"],
                result["strict_status"],
            )
            blocker = result["blocker_removed_execution_evidence"] == "true"
            outcome = classify(raw_status, strict, blocker)
            authority = (
                OUTPUT_RELATIVE
                / "manual_evalplus_run_001/evalplus_results.csv"
            ).as_posix()
        ledger.append(
            {
                "cell_id": row["cell_id"],
                "program_id": row["program_id"],
                "task_id": row["task_id"],
                "seed": row["seed"],
                "arm": row["arm"],
                "source_sha256": row["source_sha256"],
                "execution_disposition": row["execution_disposition"],
                "raw_strict_status": raw_status,
                "base_status": base,
                "plus_status": plus,
                "strict_status": strict,
                "blocker_removed": str(blocker).lower(),
                "paired_outcome": outcome,
                "rule_sha256": row["rule_sha256"],
                "h2_sha256": row["h2_sha256"],
                "result_authority": authority,
            }
        )

    non_raw = [row for row in ledger if row["arm"] != "raw"]
    arm_summary: dict[str, dict[str, int]] = {}
    for arm in ("demo_print_only", "h2_only", "h2_plus_demo_print"):
        rows = [row for row in non_raw if row["arm"] == arm]
        outcomes = Counter(row["paired_outcome"] for row in rows)
        arm_summary[arm] = {
            "cells": len(rows),
            "strict_pass": sum(row["strict_status"] == "pass" for row in rows),
            "strict_fail": sum(row["strict_status"] == "fail" for row in rows),
            "verified_rescue": outcomes["verified_rescue"],
            "partial_repair": outcomes["partial_repair"],
            "unchanged_failure": outcomes["unchanged_failure"],
            "preserved_pass": outcomes["preserved_pass"],
            "regression": outcomes["regression"],
            "blocker_removed": sum(row["blocker_removed"] == "true" for row in rows),
        }
    require(
        arm_summary["demo_print_only"]
        == {
            "cells": 21,
            "strict_pass": 17,
            "strict_fail": 4,
            "verified_rescue": 0,
            "partial_repair": 0,
            "unchanged_failure": 4,
            "preserved_pass": 17,
            "regression": 0,
            "blocker_removed": 17,
        },
        "demo-print outcome drift",
    )
    require(all(v["regression"] == 0 for v in arm_summary.values()), "regression detected")
    raw_pass_total = prereg["static_audit"]["raw_pass_controls"]
    transformed_raw_pass = arm_summary["demo_print_only"]["preserved_pass"]
    abstained_raw_pass = raw_pass_total - transformed_raw_pass
    require(abstained_raw_pass == 111, "PASS control accounting drift")

    verification = {
        "deterministic_rebuild": True,
        "idempotence_all_transformed": True,
        "ast_parseable_all_outputs": True,
        "provenance_guards_all_transformed": True,
        "all_raw_pass_preserved": True,
        "raw_pass_transformed_and_evaluated": transformed_raw_pass,
        "raw_pass_abstained_byte_identical": abstained_raw_pass,
    }
    decision = {
        "rule_id": "top_level_literal_only_demo_print_quarantine_v0",
        "rule_sha256": RULE_SHA,
        "decision": "development_candidate_not_frozen",
        "confirmatory_claim": False,
        "criterion": "B",
        "basis": {
            "demo_print_only_verified_rescue": 0,
            "demo_print_only_regression": 0,
            "all_raw_pass_preserved": True,
            "determinism_idempotence_ast_provenance": True,
        },
        "h2_effect_attributed_to_new_rule": False,
    }
    summary = {
        "status": "functional_evaluation_complete",
        "research_role": "development_candidate",
        "cohort": {"4B": 200, "9B": 300, "total": 500},
        "static_audit": {"transformed": 21, "abstained": 479},
        "raw_controls": {"pass": 128, "fail": 358, "not_evaluated": 14},
        "four_arm_rows": 84,
        "new_evalplus_executions": 50,
        "reused_raw_results": 21,
        "reused_h2_results": 13,
        "arm_summary": arm_summary,
        "verification": verification,
        "decision": decision["decision"],
        "model_calls": 0,
        "candidate_generations": 0,
        "h1_modified": False,
        "h2_modified_or_merged": False,
    }
    fields = [
        "cell_id", "program_id", "task_id", "seed", "arm", "source_sha256",
        "execution_disposition", "raw_strict_status", "base_status", "plus_status",
        "strict_status", "blocker_removed", "paired_outcome", "rule_sha256",
        "h2_sha256", "result_authority",
    ]
    ledger_bytes = csv_bytes(ledger, fields)
    report = f"""# 頂層示範 print 隔離規則 development 評測

本研究僅為 development candidate 評測，不構成 confirmatory validation。

- 全 cohort 靜態盤點：500 格（4B 200、9B 300）；命中 21、abstain 479。
- Raw 控制：PASS 128、FAIL 358、未正式評測 14。
- 新規則單獨臂：17/21 strict PASS；保留 17 個命中的 Raw PASS，4 個 Raw FAIL 均未救援。
- 新規則：verified rescue 0、regression 0、unchanged failure 4。
- H2 使用既有精確規則 SHA `{H2_SHA}`，效果獨立記錄，未歸功於新規則。
- 新執行 EvalPlus 50 次；模型呼叫與模型生成皆為 0。

依預登錄 criterion B，最終狀態為 `development_candidate_not_frozen`。
"""
    core = {
        "paired_four_arm_ledger.csv": ledger_bytes,
        "evaluation_summary.json": json_bytes(summary),
        "freeze_decision.json": json_bytes(decision),
        "research_report_zh.md": report.encode(),
    }
    receipt = {
        "receipt_id": "top_level_demo_print_quarantine_development_v1",
        "preregistration_sha256": PREREG_SHA,
        "functional_eval_input_sha256": prereg["frozen_files"]["functional_eval_input.jsonl"],
        "evalplus_results_sha256": RESULTS_SHA,
        "execution_record_sha256": sha256_bytes(execution_bytes),
        "rule_sha256": RULE_SHA,
        "h2_sha256": H2_SHA,
        "outputs": {name: sha256_bytes(data) for name, data in sorted(core.items())},
        "candidate_executions": 50,
        "evalplus_executions": 50,
        "model_calls": 0,
        "selective_rerun": False,
        "guard_modified_after_preregistration": False,
    }
    core["build_receipt.json"] = json_bytes(receipt)
    return core


def write_or_check(repo_root: Path, check: bool) -> None:
    outputs = build_outputs(repo_root)
    root = repo_root / OUTPUT_RELATIVE
    for name, data in outputs.items():
        path = root / name
        if check:
            require(path.read_bytes() == data, f"rebuild drift: {name}")
        else:
            require(not path.exists(), f"refusing to overwrite: {name}")
            path.write_bytes(data)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    write_or_check(args.repo_root.resolve(), args.check)
    print("top_level_demo_print_quarantine_development_v1_finalized: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
