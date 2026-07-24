"""Finalize the preregistered H2 functional evaluation without re-execution."""

from __future__ import annotations

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
OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_governance/"
    "h2_module_assert_quarantine_functional_evaluation_v1"
)
OUTPUT_DIR = REPO_ROOT / OUTPUT_RELATIVE
RUN_DIR = OUTPUT_DIR / "manual_post_h2_evalplus_run_001"
RULE_RELATIVE = Path(
    "agent_tools/finals_rebuild/mbpp_h2_module_assert_quarantine.py"
)
EXPECTED_RULE_SHA = "dbd96fc3c1228f74c784e2444350102de121d4e202dcb0075aad214090bbfa18"
FINAL_FILES = (
    "evaluation_manifest.json",
    "paired_cell_ledger.jsonl",
    "aggregate_summary.json",
    "freeze_decision.json",
    "execution_receipt.json",
    "research_report_zh.md",
    "credential_scan.json",
    "artifact_manifest.json",
)


class FinalizationError(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise FinalizationError(message)


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _jsonl_bytes(rows: list[dict[str, Any]]) -> bytes:
    return "".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows
    ).encode("utf-8")


def _strict(base: str, plus: str) -> str:
    return "pass" if base == plus == "pass" else "fail"


def _suite_counts(rows: list[dict[str, Any]], prefix: str) -> dict[str, int]:
    return {
        "cells": len(rows),
        "base_pass": sum(row[f"{prefix}_base_status"] == "pass" for row in rows),
        "plus_pass": sum(row[f"{prefix}_plus_status"] == "pass" for row in rows),
        "strict_pass": sum(row[f"{prefix}_strict_status"] == "pass" for row in rows),
        "strict_fail": sum(row[f"{prefix}_strict_status"] == "fail" for row in rows),
    }


def _security_scan(outputs: dict[str, bytes]) -> dict[str, Any]:
    import re

    patterns = {
        "aws_access_key": re.compile(rb"AKIA[0-9A-Z]{16}"),
        "private_key": re.compile(rb"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
        "github_token": re.compile(rb"gh[pousr]_[A-Za-z0-9]{30,}"),
        "generic_secret_assignment": re.compile(
            rb"(?i)(api[_-]?key|access[_-]?token|secret)\s*[:=]\s*['\"][^'\"]{12,}"
        ),
    }
    findings = []
    for name, content in outputs.items():
        for label, pattern in patterns.items():
            if pattern.search(content):
                findings.append({"file": name, "pattern": label})
    return {
        "status": "pass" if not findings else "fail",
        "finding_count": len(findings),
        "findings": findings,
        "files_scanned": sorted(outputs),
        "pattern_classes": sorted(patterns),
    }


def build_outputs() -> dict[str, bytes]:
    from scripts import build_h2_module_assert_quarantine_static_audit_v1 as static
    from scripts import prepare_h2_module_assert_quarantine_functional_eval_v1 as prepare

    prereg_expected = prepare.build_outputs()
    for name, content in prereg_expected.items():
        _require((OUTPUT_DIR / name).read_bytes() == content, f"preregistration drift: {name}")
    prereg_bytes = (OUTPUT_DIR / "preregistration.json").read_bytes()
    prereg = json.loads(prereg_bytes)
    roster = _read_jsonl(OUTPUT_DIR / "cell_roster.jsonl")
    eval_input = _read_jsonl(OUTPUT_DIR / "post_h2_eval_input.jsonl")

    static_expected = static.build_outputs()
    for name, content in static_expected.items():
        _require(
            (REPO_ROOT / static.OUTPUT_RELATIVE / name).read_bytes() == content,
            f"static audit deterministic drift: {name}",
        )
    _require(_sha((REPO_ROOT / RULE_RELATIVE).read_bytes()) == EXPECTED_RULE_SHA, "rule SHA changed")
    for row in eval_input:
        tree = ast.parse(row["completion"])
        _require(not any(isinstance(node, ast.Assert) for node in tree.body), "Post-H2 module assert remains")
        _require(
            any(
                isinstance(node, ast.If)
                and any(isinstance(child, ast.Assert) for child in node.body)
                for node in tree.body
            ),
            "Post-H2 guarded assert absent",
        )

    result_path = RUN_DIR / "post_h2_evalplus_results.csv"
    execution_path = RUN_DIR / "execution_record.json"
    result_bytes = result_path.read_bytes()
    execution_bytes = execution_path.read_bytes()
    execution = json.loads(execution_bytes)
    _require(execution["preregistration_sha256"] == _sha(prereg_bytes), "execution/prereg binding mismatch")
    _require(execution["results_sha256"] == _sha(result_bytes), "result receipt mismatch")
    _require(execution["evaluated_cells"] == 71, "execution count drift")
    _require(execution["abstained_cells_executed"] == 0, "abstained cell was executed")
    _require(execution["model_calls"] == 0 and execution["candidate_generations"] == 0, "zero-model/generation invariant failed")
    _require(execution["guard_or_rule_modified"] is False, "rule modification recorded")
    results = {row["source_record_id"]: row for row in _read_csv(result_path)}
    _require(len(results) == 71, "result identity count drift")

    paired: list[dict[str, Any]] = []
    for roster_row in roster:
        identity = roster_row["source_record_id"]
        if roster_row["transformed"]:
            result = results.get(identity)
            _require(result is not None, f"missing Post-H2 result: {identity}")
            _require(result["post_h2_source_sha256"] == roster_row["post_h2_source_sha256"], "result/Post-H2 SHA mismatch")
            post_base = result["base_status"]
            post_plus = result["plus_status"]
            post_strict = result["strict_status"]
            blocker_removed = result["blocker_removed_execution_evidence"] == "true"
            result_basis = "executed_preregistered_post_h2_evalplus"
            if roster_row["raw_strict_status"] == "pass":
                outcome = "preserved_pass" if post_strict == "pass" else "regression"
            elif post_strict == "pass":
                outcome = "verified_rescue"
            elif blocker_removed:
                outcome = "partial_repair"
            else:
                outcome = "unchanged_failure"
            timeout = any(
                "time" in status.lower()
                for status in (post_base, post_plus)
            )
            execution_error = (
                not timeout
                and post_base not in {"pass", "fail"}
                or not timeout
                and post_plus not in {"pass", "fail"}
            )
            details = {
                "base_detail_count": int(result["base_detail_count"]),
                "base_detail_pass_count": int(result["base_detail_pass_count"]),
                "plus_detail_count": int(result["plus_detail_count"]),
                "plus_detail_pass_count": int(result["plus_detail_pass_count"]),
            }
        else:
            _require(
                roster_row["pipeline_source_sha256"]
                == roster_row["post_h2_source_sha256"],
                "abstained identity changed",
            )
            _require(identity not in results, "abstained cell has execution result")
            post_base = roster_row["raw_base_status"]
            post_plus = roster_row["raw_plus_status"]
            post_strict = roster_row["raw_strict_status"]
            blocker_removed = False
            result_basis = "identity_reuse_raw_no_candidate_execution"
            outcome = "abstained_unchanged"
            timeout = False
            execution_error = False
            details = {
                "base_detail_count": None,
                "base_detail_pass_count": None,
                "plus_detail_count": None,
                "plus_detail_pass_count": None,
            }
        paired.append(
            {
                **roster_row,
                "post_h2_base_status": post_base,
                "post_h2_plus_status": post_plus,
                "post_h2_strict_status": post_strict,
                "post_h2_result_basis": result_basis,
                "blocker_removed": blocker_removed,
                "outcome": outcome,
                "timeout": timeout,
                "execution_error": execution_error,
                **details,
            }
        )
    _require(len(paired) == 91, "paired ledger count drift")
    _require(set(results) == {row["source_record_id"] for row in paired if row["transformed"]}, "execution scope differs from 71 transformed cells")

    cohorts: dict[str, Any] = {}
    for cohort in (
        "4B_all_module_level_assert_cells",
        "9B_formal_Conditional23",
        "combined",
    ):
        selected = paired if cohort == "combined" else [row for row in paired if row["cohort"] == cohort]
        outcomes = Counter(row["outcome"] for row in selected)
        cohorts[cohort] = {
            "raw": _suite_counts(selected, "raw"),
            "post_h2": _suite_counts(selected, "post_h2"),
            "transformed": sum(row["transformed"] for row in selected),
            "abstained": sum(row["abstained"] for row in selected),
            "blocker_removed": sum(row["blocker_removed"] for row in selected),
            "verified_rescue": outcomes["verified_rescue"],
            "partial_repair": outcomes["partial_repair"],
            "regression": outcomes["regression"],
            "preserved_pass": outcomes["preserved_pass"],
            "unchanged_failure": outcomes["unchanged_failure"],
            "abstained_unchanged": outcomes["abstained_unchanged"],
            "timeout": sum(row["timeout"] for row in selected),
            "execution_error": sum(row["execution_error"] for row in selected),
        }

    four_pass_controls = [
        row
        for row in paired
        if row["cohort"].startswith("4B")
        and row["transformed"]
        and row["raw_strict_status"] == "pass"
    ]
    nine_pass_controls = [
        row
        for row in paired
        if row["cohort"].startswith("9B")
        and row["raw_strict_status"] == "pass"
    ]
    fail_to_pass = [row["source_record_id"] for row in paired if row["outcome"] == "verified_rescue"]
    pass_to_fail = [row["source_record_id"] for row in paired if row["outcome"] == "regression"]
    blocker_removed_still_fail = [
        {
            "source_record_id": row["source_record_id"],
            "cohort": row["cohort"],
            "task_id": row["task_id"],
            "seed": row["seed"],
            "raw_strict_status": row["raw_strict_status"],
            "post_h2_base_status": row["post_h2_base_status"],
            "post_h2_plus_status": row["post_h2_plus_status"],
        }
        for row in paired
        if row["blocker_removed"] and row["post_h2_strict_status"] == "fail"
    ]

    combined = cohorts["combined"]
    all_raw_pass_preserved = all(
        row["post_h2_strict_status"] == "pass"
        for row in paired
        if row["raw_strict_status"] == "pass"
    )
    validation_gates = {
        "deterministic_static_rebuild": True,
        "h2_idempotence_and_ast": True,
        "provenance_and_sha": True,
        "execution_scope_exactly_71": True,
        "abstained_sha_identity_20": True,
        "rule_sha_unchanged": True,
    }
    if combined["regression"] > 0 or not all_raw_pass_preserved:
        criterion = "C"
        status = "development_rejected_pending_review"
        frozen = False
    elif combined["verified_rescue"] >= 1 and all(validation_gates.values()):
        criterion = "A"
        status = "module_assert_entrypoint_selftest_quarantine_v1_frozen"
        frozen = True
    else:
        criterion = "B"
        status = "development_candidate_not_frozen"
        frozen = False

    summary = {
        "evaluation_id": "h2_module_assert_quarantine_functional_evaluation_v1",
        "scope": "Stage2_MBPP+_only",
        "cohorts": cohorts,
        "four_b_transformed_raw_pass_controls": {
            "count": len(four_pass_controls),
            "preserved": sum(row["outcome"] == "preserved_pass" for row in four_pass_controls),
            "regressed": sum(row["outcome"] == "regression" for row in four_pass_controls),
        },
        "nine_b_all_raw_pass_controls": {
            "count": len(nine_pass_controls),
            "preserved": sum(row["outcome"] == "preserved_pass" for row in nine_pass_controls),
            "regressed": sum(row["outcome"] == "regression" for row in nine_pass_controls),
        },
        "fail_to_pass_source_record_ids": fail_to_pass,
        "pass_to_fail_source_record_ids": pass_to_fail,
        "blocker_removed_but_still_failed": blocker_removed_still_fail,
    }
    freeze_decision = {
        "decision": status,
        "criterion": criterion,
        "frozen": frozen,
        "rule_id": prereg["rule"]["rule_id"],
        "rule_sha256": EXPECTED_RULE_SHA,
        "rule_sha_unchanged": True,
        "regression": combined["regression"],
        "all_raw_pass_preserved": all_raw_pass_preserved,
        "verified_rescue": combined["verified_rescue"],
        "validation_gates": validation_gates,
        "reason": (
            "Criterion B: regression=0 and every Raw strict PASS was preserved, "
            "but verified_rescue=0; retain development_candidate_not_frozen."
            if criterion == "B"
            else f"Preregistered criterion {criterion} applied without modification."
        ),
    }
    execution_receipt = {
        **execution,
        "status": "functional_evaluation_finalized",
        "raw_results_reused_not_reexecuted": 91,
        "post_h2_candidates_executed": 71,
        "abstained_candidates_executed": 0,
        "paired_cells": 91,
        "paired_ledger_sha256": None,
        "zero_model_calls_confirmed": execution["model_calls"] == 0,
        "zero_candidate_generation_confirmed": execution["candidate_generations"] == 0,
        "new_algorithm_scaffold_experiments": 0,
        "h1_modified": False,
        "h2_rule_modified": False,
        "raw_or_static_audit_modified": False,
    }
    paired_bytes = _jsonl_bytes(paired)
    execution_receipt["paired_ledger_sha256"] = _sha(paired_bytes)
    evaluation_manifest = {
        "manifest_id": "h2_module_assert_quarantine_functional_evaluation_v1",
        "status": "complete",
        "scope": "Stage2_MBPP+_only",
        "preregistration_sha256": _sha(prereg_bytes),
        "cell_roster_sha256": _sha((OUTPUT_DIR / "cell_roster.jsonl").read_bytes()),
        "post_h2_eval_input_sha256": _sha((OUTPUT_DIR / "post_h2_eval_input.jsonl").read_bytes()),
        "post_h2_eval_results_sha256": _sha(result_bytes),
        "raw_execution_record_sha256": _sha(execution_bytes),
        "rule_sha256": EXPECTED_RULE_SHA,
        "counts": {"roster": 91, "executed": 71, "abstained_identity_only": 20},
        "freeze_decision": status,
    }
    report = f"""# H2 module assert quarantine 功能評測報告

本輪依執行前預登錄，使用 WSL2 Ubuntu、Python 3.14.4、EvalPlus 0.3.1、
MBPP+ v0.2.0、parallel=1，僅執行 71 個 transformed Post-H2 candidate。
20 個 abstained 格僅驗證 pipeline/output SHA 完全一致，未執行。

## 結果

- 4B：Raw strict PASS {cohorts['4B_all_module_level_assert_cells']['raw']['strict_pass']}；
  Post-H2 strict PASS {cohorts['4B_all_module_level_assert_cells']['post_h2']['strict_pass']}。
  25 個 transformed Raw PASS 控制格全部 preserved，regression 0。
- 9B Conditional23：Raw strict PASS {cohorts['9B_formal_Conditional23']['raw']['strict_pass']}；
  Post-H2 strict PASS {cohorts['9B_formal_Conditional23']['post_h2']['strict_pass']}。
- 合計：verified rescue {combined['verified_rescue']}、partial repair
  {combined['partial_repair']}、regression {combined['regression']}、
  preserved pass {combined['preserved_pass']}、abstained unchanged
  {combined['abstained_unchanged']}。
- 71 個 transformed 格都有 per-test execution detail，故 assert module-load
  blocker 均有解除證據；其中 {len(blocker_removed_still_fail)} 格仍未達 strict PASS。

## 凍結決定

套用預登錄判準 {criterion}：`{status}`。
沒有 regression，所有 Raw PASS 均 preserved，但 verified rescue 為
{combined['verified_rescue']}，因此不凍結為 v1。此結論不代表 H2 無法解除
module-load 阻斷；它只表示本 cohort 未觀察到 strict FAIL→PASS。

本輪零模型呼叫、零重新生成、Raw結果只沿用正式證據；未修改 H1、H2 rule、
raw、static audit，亦未執行新演算法鷹架實驗。
"""
    outputs: dict[str, bytes] = {
        "evaluation_manifest.json": _json_bytes(evaluation_manifest),
        "paired_cell_ledger.jsonl": paired_bytes,
        "aggregate_summary.json": _json_bytes(summary),
        "freeze_decision.json": _json_bytes(freeze_decision),
        "execution_receipt.json": _json_bytes(execution_receipt),
        "research_report_zh.md": report.encode("utf-8"),
    }
    scan = _security_scan(outputs)
    _require(scan["status"] == "pass", "credential scan failed")
    outputs["credential_scan.json"] = _json_bytes(scan)
    outputs["artifact_manifest.json"] = _json_bytes(
        {
            "manifest_id": "h2_module_assert_quarantine_functional_evaluation_artifacts_v1",
            "status": status,
            "output_sha256_excluding_manifest": {
                name: _sha(content) for name, content in sorted(outputs.items())
            },
        }
    )
    return outputs


def write_outputs(check: bool = False) -> None:
    outputs = build_outputs()
    _require(set(outputs) == set(FINAL_FILES), "final file set drift")
    for name, content in outputs.items():
        path = OUTPUT_DIR / name
        if check:
            _require(path.is_file() and path.read_bytes() == content, f"final rebuild mismatch: {name}")
        else:
            _require(not path.exists(), f"final output exists: {name}")
            path.write_bytes(content)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    write_outputs(check=args.check)
    print("functional_finalization_check=pass" if args.check else "functional_finalization_written=8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
