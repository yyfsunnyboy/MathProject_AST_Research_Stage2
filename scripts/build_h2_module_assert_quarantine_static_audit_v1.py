"""Build the zero-execution H2 module-assert quarantine static audit.

This builder reads only frozen Stage2/MBPP+ evidence.  It does not execute
candidate source, call a model, invoke EvalPlus, or use outcomes in rule
decisions.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import io
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_tools.finals_rebuild.mbpp_h2_module_assert_quarantine import (  # noqa: E402
    RULE_ID,
    RULE_STATUS,
    quarantine_module_assert_entrypoint_selftest,
)

OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_governance/"
    "h2_module_assert_quarantine_development_static_audit_v1"
)
OUTPUT_DIR = REPO_ROOT / OUTPUT_RELATIVE
FOUR_B_RELATIVE = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_4b_failure_supply_pilot_analysis_v1"
)
NINE_B_ROSTER_RELATIVE = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_conditional23_preregistration_v1"
)
NINE_B_ARCHIVE_RELATIVE = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_9b_source_evidence_archive_v1/ARCHIVE_MANIFEST.md"
)
TASKS_RELATIVE = Path("data/mbpp_plus/tasks.jsonl")
DATASET_MANIFEST_RELATIVE = Path("data/mbpp_plus/dataset_manifest.json")
RULE_RELATIVE = Path(
    "agent_tools/finals_rebuild/mbpp_h2_module_assert_quarantine.py"
)
BUILDER_RELATIVE = Path(__file__).resolve().relative_to(REPO_ROOT)


def _bytes(path: Path) -> bytes:
    return path.read_bytes()


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_file(relative: Path) -> str:
    return _sha_bytes(_bytes(REPO_ROOT / relative))


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _jsonl_bytes(rows: Iterable[dict[str, Any]]) -> bytes:
    return "".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows
    ).encode("utf-8")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _csv_bytes(rows: list[dict[str, Any]], fields: list[str]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field, "") for field in fields})
    return stream.getvalue().encode("utf-8")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _verify_hash(relative: Path, expected: str, label: str) -> None:
    actual = _sha_file(relative)
    _require(actual == expected, f"{label} SHA mismatch: {actual} != {expected}")


def _tasks() -> tuple[dict[str, dict[str, str]], dict[str, Any]]:
    manifest = json.loads(
        (REPO_ROOT / DATASET_MANIFEST_RELATIVE).read_text(encoding="utf-8")
    )
    _require(manifest["dataset_name"] == "MBPP+", "dataset is not MBPP+")
    _require(
        manifest["official_tests_and_canonical_solutions_included"] is False,
        "dataset unexpectedly includes hidden evaluation material",
    )
    _require(
        manifest["stored_fields"] == ["task_id", "prompt", "entry_point"],
        "unexpected task fields",
    )
    _verify_hash(
        TASKS_RELATIVE, manifest["tasks_sha256"], "official MBPP+ tasks"
    )
    rows = _read_jsonl(REPO_ROOT / TASKS_RELATIVE)
    _require(
        all(set(row) == {"task_id", "prompt", "entry_point"} for row in rows),
        "task record contains forbidden or unexpected fields",
    )
    return {row["task_id"]: row for row in rows}, manifest


def _module_assert_count(source: str) -> int:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return 0
    return sum(isinstance(node, ast.Assert) for node in tree.body)


def _four_b_rows(tasks: dict[str, dict[str, str]]) -> tuple[list[dict], dict]:
    root = REPO_ROOT / FOUR_B_RELATIVE
    frozen_bytes = (root / "frozen_input_manifest.json").read_bytes()
    frozen = json.loads(frozen_bytes)
    _require(frozen["scope"] == "Stage2_MBPP+_only", "4B scope mismatch")
    _require(
        frozen["run_id"] == "mbpp_q35_4b_dev20_failure_supply_pilot_r001",
        "4B run mismatch",
    )
    _require(frozen["counts"]["cells"] == 200, "4B frozen ITT is not 200")
    _require(frozen["counts"]["h0_evalplus"] == 186, "4B extracted count mismatch")
    _require(frozen["model_calls"] == 0, "4B frozen analysis recorded model calls")
    for name, expected in frozen["prepared_output_sha256"].items():
        _verify_hash(FOUR_B_RELATIVE / name, expected, f"4B prepared {name}")

    inputs = _read_jsonl(root / "h0_evalplus_input.jsonl")
    inventory = {
        row["generation_id"]: row
        for row in _read_csv(root / "generation_evidence_inventory.csv")
    }
    extraction = {
        row["generation_id"]: row
        for row in _read_csv(root / "extraction_itt_ledger.csv")
    }
    _require(len(inventory) == 200, "4B inventory is not 200 cells")
    _require(len(extraction) == 200, "4B extraction ITT is not 200 cells")

    records: list[dict] = []
    for candidate in inputs:
        source = candidate["completion"]
        if _module_assert_count(source) == 0:
            continue
        generation_id = candidate["generation_id"]
        inv = inventory[generation_id]
        ext = extraction[generation_id]
        _require(ext["extraction_status"] == "extracted", "4B source not extracted")
        _require(
            ext["candidate_count"] == "1",
            "4B selected source was not uniquely extracted",
        )
        _require(
            ext["extracted_code_sha256"]
            == candidate["evaluation_source_sha256"],
            "4B extraction/source SHA mismatch",
        )
        journal_relative = Path(inv["journal_path"])
        _verify_hash(journal_relative, inv["journal_sha256"], "4B journal")
        journal = json.loads(
            (REPO_ROOT / journal_relative).read_text(encoding="utf-8")
        )
        _require(
            journal["generation_id"] == generation_id,
            "4B journal generation identity mismatch",
        )
        raw = journal["raw_response"].encode("utf-8")
        _require(
            _sha_bytes(raw) == inv["raw_response_sha256"],
            "4B raw response SHA mismatch",
        )
        raw_body = json.loads(journal["response_metadata"]["raw_body"])
        done_reason = raw_body.get("done_reason")
        decision = quarantine_module_assert_entrypoint_selftest(
            source,
            tasks[candidate["task_id"]]["entry_point"],
            extraction_unambiguous=True,
            source_complete=done_reason == "stop",
        )
        complete_source_probe = quarantine_module_assert_entrypoint_selftest(
            source,
            tasks[candidate["task_id"]]["entry_point"],
            extraction_unambiguous=True,
            source_complete=True,
        )
        records.append(
            {
                "cohort": "4B_all_module_level_assert_cells",
                "source_authority": str(
                    FOUR_B_RELATIVE / "frozen_input_manifest.json"
                ).replace("\\", "/"),
                "source_record_id": candidate["cell_identity"],
                "cell_index": candidate["cell_index"],
                "program_id": candidate["program_id"],
                "generation_id": generation_id,
                "task_id": candidate["task_id"],
                "seed": candidate["seed"],
                "condition": candidate["condition_id"],
                "model": inv["model_tag"],
                "entry_point": tasks[candidate["task_id"]]["entry_point"],
                "extraction_unambiguous": True,
                "source_complete": done_reason == "stop",
                "completion_reason": done_reason or "missing",
                "diagnostic_source_incomplete": done_reason != "stop",
                "diagnostic_predicate_unsafe": (
                    complete_source_probe.reason
                    in {
                        "assert_not_direct_entrypoint_selftest",
                        "assert_depends_on_external_state",
                        "assert_has_external_or_side_effectful_call",
                        "assert_call_arguments_not_literal",
                        "assert_expression_shape_ambiguous",
                    }
                ),
                "diagnostic_message_unsafe": (
                    complete_source_probe.reason
                    == "assert_message_depends_on_external_state"
                ),
                "decision": decision,
            }
        )
    return records, {
        "frozen_input_manifest_sha256": _sha_bytes(frozen_bytes),
        "generation_manifest_sha256": frozen["generation_manifest_sha256"],
        "run_id": frozen["run_id"],
        "frozen_counts": frozen["counts"],
    }


def _nine_b_rows(tasks: dict[str, dict[str, str]]) -> tuple[list[dict], dict]:
    prereg = REPO_ROOT / NINE_B_ROSTER_RELATIVE
    roster_relative = NINE_B_ROSTER_RELATIVE / "conditional23_candidate_roster.csv"
    provenance_relative = NINE_B_ROSTER_RELATIVE / "provenance_summary.json"
    provenance = json.loads(
        (REPO_ROOT / provenance_relative).read_text(encoding="utf-8")
    )
    expected_roster_sha = provenance["generated_draft_files"][
        "conditional23_candidate_roster.csv"
    ]["sha256"]
    _verify_hash(roster_relative, expected_roster_sha, "Conditional23 roster")
    roster = _read_csv(REPO_ROOT / roster_relative)
    _require(roster, "Conditional23 roster is empty")
    _require(
        all(
            row["dataset"] == "MBPP+"
            and row["condition"] == "H0"
            and row["taxonomy_version"] == "v3.1"
            and row["exception_class"] == "module_level_executable_assertion"
            for row in roster
        ),
        "Conditional23 roster scope mismatch",
    )
    account_paths = {row["pipeline_corrected_artifact_path"] for row in roster}
    _require(len(account_paths) == 1, "Conditional23 has multiple account sources")
    accounts_relative = Path(account_paths.pop())
    account_authority = provenance["authoritative_sources"].get(
        str(accounts_relative).replace("\\", "/")
    )
    _require(account_authority is not None, "accounts file lacks provenance authority")
    _verify_hash(
        accounts_relative, account_authority["sha256"], "9B H0 accounts"
    )

    run_root = (REPO_ROOT / accounts_relative).parent
    frozen_relative = run_root.relative_to(REPO_ROOT) / "frozen_manifest.json"
    raw_relative = run_root.relative_to(REPO_ROOT) / "raw_generations.jsonl"
    frozen = json.loads((REPO_ROOT / frozen_relative).read_text(encoding="utf-8"))
    _require(
        (REPO_ROOT / frozen["run_output_relative"]).resolve()
        == run_root.resolve(),
        "9B frozen run path mismatch",
    )
    _require(frozen["model_calls_during_freeze"] == 0, "9B freeze model call mismatch")
    _require(
        frozen["evalplus_executions_during_freeze"] == 0,
        "9B freeze EvalPlus execution mismatch",
    )
    archive_text = (REPO_ROOT / NINE_B_ARCHIVE_RELATIVE).read_text(
        encoding="utf-8"
    )
    raw_sha_match = re.search(
        r"raw_generations\.jsonl.*?`([0-9a-f]{64})`", archive_text
    )
    _require(raw_sha_match is not None, "9B archive lacks raw SHA")
    _verify_hash(raw_relative, raw_sha_match.group(1), "9B raw generations")

    accounts = _read_jsonl(REPO_ROOT / accounts_relative)
    raw_by_id = {
        row["generation_id"]: row for row in _read_jsonl(REPO_ROOT / raw_relative)
    }
    records: list[dict] = []
    for roster_row in roster:
        matches = [
            row
            for row in accounts
            if row["healer_account"] == "H0"
            and row["task_id"] == roster_row["task_id"]
            and str(row["seed"]) == roster_row["seed"]
            and row["evaluation_source_sha256"] == roster_row["source_hash"]
        ]
        _require(len(matches) == 1, "Conditional23 H0 account join is not unique")
        account = matches[0]
        raw = raw_by_id[account["generation_id"]]
        _require(raw["raw_response_sha256"] == account["raw_response_sha256"], "9B raw/account SHA mismatch")
        _require(
            _sha_bytes(account["evaluation_source"].encode("utf-8"))
            == account["evaluation_source_sha256"],
            "9B evaluation source SHA mismatch",
        )
        done_reason = raw.get("generation_metadata", {}).get("done_reason")
        decision = quarantine_module_assert_entrypoint_selftest(
            account["evaluation_source"],
            tasks[account["task_id"]]["entry_point"],
            extraction_unambiguous=(
                account["pipeline_normalized_source_sha256"]
                == account["evaluation_source_sha256"]
            ),
            source_complete=done_reason == "stop",
        )
        records.append(
            {
                "cohort": "9B_formal_Conditional23",
                "source_authority": str(roster_relative).replace("\\", "/"),
                "source_record_id": roster_row["cell_id"],
                "cell_index": account["cell_index"],
                "program_id": account["program_id"],
                "generation_id": account["generation_id"],
                "task_id": account["task_id"],
                "seed": account["seed"],
                "condition": "H0",
                "model": raw["model"],
                "entry_point": tasks[account["task_id"]]["entry_point"],
                "extraction_unambiguous": True,
                "source_complete": done_reason == "stop",
                "completion_reason": done_reason or "missing",
                "diagnostic_source_incomplete": done_reason != "stop",
                "diagnostic_predicate_unsafe": False,
                "diagnostic_message_unsafe": False,
                "decision": decision,
            }
        )
    return records, {
        "conditional_roster_sha256": expected_roster_sha,
        "conditional_roster_rows": len(roster),
        "accounts_sha256": _sha_file(accounts_relative),
        "raw_generations_sha256": _sha_file(raw_relative),
        "frozen_manifest_sha256": _sha_file(frozen_relative),
        "run_id": frozen["run_id"],
    }


def _reason_group(record: dict) -> str:
    decision = record["decision"]
    if decision.transformed:
        return "transformed"
    if decision.reason.startswith("entry_point_"):
        return "entrypoint_missing_or_nonunique"
    if decision.reason == "module_assert_count_not_one":
        return "multiple_module_asserts"
    return "complex_external_or_incomplete"


def _posthoc_four_b_pass_controls(records: list[dict]) -> int:
    """Count prior PASS controls only after H2 decisions are complete."""
    path = (
        REPO_ROOT
        / FOUR_B_RELATIVE
        / "manual_h0_evalplus_run_001/h0_evalplus_results.csv"
    )
    outcomes = {int(row["cell_index"]): row for row in _read_csv(path)}
    return sum(
        record["decision"].transformed
        and outcomes[int(record["cell_index"])]["aggregate_status"] == "pass"
        for record in records
        if record["cohort"] == "4B_all_module_level_assert_cells"
    )


def build_outputs() -> dict[str, bytes]:
    tasks, dataset_manifest = _tasks()
    four_b, four_provenance = _four_b_rows(tasks)
    nine_b, nine_provenance = _nine_b_rows(tasks)
    records = sorted(
        four_b + nine_b,
        key=lambda row: (
            row["cohort"],
            int(row["cell_index"]),
            str(row["source_record_id"]),
        ),
    )

    ledger: list[dict[str, Any]] = []
    transformed_sources: list[dict[str, Any]] = []
    for row in records:
        decision = row["decision"]
        ledger.append(
            {
                **{key: value for key, value in row.items() if key != "decision"},
                "rule_id": decision.rule_id,
                "rule_status": decision.rule_status,
                "triggered": str(decision.triggered).lower(),
                "transformed": str(decision.transformed).lower(),
                "abstained": str(decision.abstained).lower(),
                "reason": decision.reason,
                "reason_group": _reason_group(row),
                "module_assert_count": decision.module_assert_count,
                "entrypoint_status": decision.entrypoint_status,
                "guard_results_json": json.dumps(
                    decision.guard_results, sort_keys=True, separators=(",", ":")
                ),
                "source_sha256": decision.source_sha256,
                "output_sha256": decision.output_sha256,
                "claim": decision.claim,
            }
        )
        if decision.transformed:
            transformed_sources.append(
                {
                    "cohort": row["cohort"],
                    "source_record_id": row["source_record_id"],
                    "rule_id": decision.rule_id,
                    "source_sha256": decision.source_sha256,
                    "output_sha256": decision.output_sha256,
                    "output_source": decision.output_source,
                    "claim": decision.claim,
                }
            )

    cohort_summary: dict[str, Any] = {}
    for cohort in sorted({row["cohort"] for row in records}):
        selected = [row for row in records if row["cohort"] == cohort]
        cohort_summary[cohort] = {
            "cells": len(selected),
            "triggered": sum(row["decision"].triggered for row in selected),
            "transformed": sum(row["decision"].transformed for row in selected),
            "abstained": sum(row["decision"].abstained for row in selected),
            "reason_groups": dict(
                sorted(Counter(_reason_group(row) for row in selected).items())
            ),
            "reasons": dict(
                sorted(Counter(row["decision"].reason for row in selected).items())
            ),
        }
    posthoc_pass_controls = _posthoc_four_b_pass_controls(records)
    four_b_records = [
        row
        for row in records
        if row["cohort"] == "4B_all_module_level_assert_cells"
    ]
    incomplete_ids = {
        row["source_record_id"]
        for row in four_b_records
        if row["diagnostic_source_incomplete"]
    }
    predicate_unsafe_ids = {
        row["source_record_id"]
        for row in four_b_records
        if row["diagnostic_predicate_unsafe"]
    }
    message_unsafe_ids = {
        row["source_record_id"]
        for row in four_b_records
        if row["diagnostic_message_unsafe"]
    }
    actual_reference = {
        "four_b_cells": cohort_summary["4B_all_module_level_assert_cells"]["cells"],
        "four_b_transformed": cohort_summary["4B_all_module_level_assert_cells"][
            "transformed"
        ],
        "four_b_abstained": cohort_summary["4B_all_module_level_assert_cells"][
            "abstained"
        ],
        "four_b_entrypoint_abstain": cohort_summary[
            "4B_all_module_level_assert_cells"
        ]["reason_groups"].get("entrypoint_missing_or_nonunique", 0),
        "four_b_complex_external_or_incomplete": cohort_summary[
            "4B_all_module_level_assert_cells"
        ]["reason_groups"].get("complex_external_or_incomplete", 0),
        "four_b_multiple_assert_abstain": cohort_summary[
            "4B_all_module_level_assert_cells"
        ]["reason_groups"].get("multiple_module_asserts", 0),
        "four_b_transformed_prior_pass_control": posthoc_pass_controls,
        "nine_b_conditional_cells": cohort_summary["9B_formal_Conditional23"]["cells"],
        "nine_b_conditional_transformed": cohort_summary[
            "9B_formal_Conditional23"
        ]["transformed"],
    }
    reference_only = {
        "four_b_cells": 68,
        "four_b_transformed": 45,
        "four_b_abstained": 23,
        "four_b_entrypoint_abstain": 9,
        "four_b_complex_external_or_incomplete": 11,
        "four_b_multiple_assert_abstain": 3,
        "four_b_transformed_prior_pass_control": 21,
        "nine_b_conditional_cells": 23,
        "nine_b_conditional_transformed": 23,
    }
    summary = {
        "audit_id": "h2_module_assert_quarantine_development_static_audit_v1",
        "rule_id": RULE_ID,
        "rule_status": RULE_STATUS,
        "scope": "Stage2_MBPP+_only",
        "cohorts": cohort_summary,
        "reference_comparison_is_non_gating": True,
        "reference_expected": reference_only,
        "reference_actual": actual_reference,
        "reference_match": actual_reference == reference_only,
        "reference_reconciliation": {
            "nonexclusive_source_incomplete": len(incomplete_ids),
            "nonexclusive_predicate_external_or_complex": len(
                predicate_unsafe_ids
            ),
            "nonexclusive_message_external_or_complex": len(message_unsafe_ids),
            "source_incomplete_and_predicate_complex_overlap": len(
                incomplete_ids & predicate_unsafe_ids
            ),
            "naive_incomplete_plus_predicate_count": (
                len(incomplete_ids) + len(predicate_unsafe_ids)
            ),
            "explanation": (
                "The supplied complex/external reference 11 equals 6 incomplete "
                "+ 5 predicate-risk flags, but 3 cells have both flags. Treating "
                "primary abstain reasons as mutually exclusive prevents those "
                "cells from being subtracted twice. The same cohort-agnostic "
                "rule must allow the pure builtin abs tolerance shape because "
                "two formal 9B Conditional23 cells use that identical shape."
            ),
        },
        "outcomes_available_to_rule": False,
        "posthoc_control_outcome_used_for_rule": False,
        "candidate_execution_count": 0,
        "evalplus_execution_count": 0,
        "model_call_count": 0,
        "claim": "module_load_assert_quarantined_only_no_pass_claim",
    }

    fields = [
        "cohort", "source_authority", "source_record_id", "cell_index",
        "program_id", "generation_id", "task_id", "seed", "condition", "model",
        "entry_point", "extraction_unambiguous", "source_complete",
        "completion_reason", "rule_id", "rule_status", "triggered",
        "transformed", "abstained", "reason", "reason_group",
        "module_assert_count", "entrypoint_status", "guard_results_json",
        "source_sha256", "output_sha256", "claim",
    ]
    outputs: dict[str, bytes] = {
        "decision_ledger.csv": _csv_bytes(ledger, fields),
        "transformed_sources.jsonl": _jsonl_bytes(transformed_sources),
        "aggregate_summary.json": _json_bytes(summary),
    }
    report = f"""# H2 module assert quarantine 靜態研究報告

規則 `{RULE_ID}` 狀態為 `{RULE_STATUS}`。本 audit 僅涵蓋 Stage2／MBPP+：
4B 凍結證據中全部 {actual_reference['four_b_cells']} 個 module-level assert 格，以及
9B 正式 Conditional23 的 {actual_reference['nine_b_conditional_cells']} 格。

4B：{actual_reference['four_b_transformed']} 格轉換、{actual_reference['four_b_abstained']} 格 abstain；
abstain 分組為 entry-point 缺失／非唯一 {actual_reference['four_b_entrypoint_abstain']}、
複雜／外部狀態／來源不完整 {actual_reference['four_b_complex_external_or_incomplete']}、
多 assert {actual_reference['four_b_multiple_assert_abstain']}。
9B Conditional23：{actual_reference['nine_b_conditional_transformed']} 格轉換。
4B 轉換格中的既有原 PASS 控制格為 {posthoc_pass_controls}；此值只在決策完成後統計，
未提供給規則，也未用於挑選轉換。

既有核對值是否完全一致：{str(summary['reference_match']).lower()}。
差異已定位：參考的複雜／外部狀態 11 是「來源不完整 6」與「predicate
複雜／外部狀態 5」的非互斥相加，其中 3 格同時具備兩種旗標。逐格決策採唯一
primary reason 時不得重複扣除，因此 4B 唯一 abstain 為 20、轉換為 48。
若為得到 45 而排除純 builtin `abs(entrypoint(...)-literal)`，結構相同的兩個
9B Conditional23 格也會被排除，與單一 cohort-agnostic 規則及 9B 23/23 衝突。
規則只把唯一且明確的 entry-point 自我測試 assert 移至
`if __name__ == "__main__":`，不刪除 assert、不修改函式內容。
研究主張僅限解除 import 時的該 assert 阻斷，不主張程式因此 PASS。

本輪零模型呼叫、零 candidate execution、零 EvalPlus、零重新評分；
未套用或修改既有 H1。
"""
    outputs["research_report_zh.md"] = report.encode("utf-8")

    scan_patterns = {
        "aws_access_key": re.compile(rb"AKIA[0-9A-Z]{16}"),
        "private_key": re.compile(rb"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
        "github_token": re.compile(rb"gh[pousr]_[A-Za-z0-9]{30,}"),
        "generic_secret_assignment": re.compile(
            rb"(?i)(api[_-]?key|access[_-]?token|secret)\s*[:=]\s*['\"][^'\"]{12,}"
        ),
    }
    findings = []
    for name, content in outputs.items():
        for pattern_name, pattern in scan_patterns.items():
            if pattern.search(content):
                findings.append({"file": name, "pattern": pattern_name})
    outputs["credential_scan.json"] = _json_bytes(
        {
            "files_scanned": sorted(outputs),
            "pattern_classes": sorted(scan_patterns),
            "finding_count": len(findings),
            "findings": findings,
            "status": "pass" if not findings else "fail",
        }
    )
    _require(not findings, "credential scan found a possible secret")

    receipt = {
        "receipt_id": "h2_module_assert_quarantine_reproducibility_v1",
        "rule_id": RULE_ID,
        "rule_status": RULE_STATUS,
        "scope": "Stage2_MBPP+_only",
        "four_b_provenance": four_provenance,
        "nine_b_provenance": nine_provenance,
        "dataset_manifest_sha256": _sha_file(DATASET_MANIFEST_RELATIVE),
        "tasks_sha256": dataset_manifest["tasks_sha256"],
        "rule_sha256": _sha_file(RULE_RELATIVE),
        "builder_sha256": _sha_file(BUILDER_RELATIVE),
        "controls": {
            "candidate_source_executed": False,
            "evalplus_invoked": False,
            "model_invoked": False,
            "outcomes_supplied_to_rule": False,
            "task_id_supplied_to_rule": False,
            "canonical_solution_or_hidden_tests_read": False,
            "existing_h1_modified_or_applied": False,
        },
        "output_sha256_excluding_manifest_and_receipt": {
            name: _sha_bytes(content) for name, content in sorted(outputs.items())
        },
    }
    outputs["reproducibility_receipt.json"] = _json_bytes(receipt)
    manifest = {
        "manifest_id": "h2_module_assert_quarantine_development_static_audit_v1",
        "rule_id": RULE_ID,
        "status": RULE_STATUS,
        "scope": "Stage2_MBPP+_only",
        "output_sha256_excluding_manifest": {
            name: _sha_bytes(content) for name, content in sorted(outputs.items())
        },
    }
    outputs["manifest.json"] = _json_bytes(manifest)
    return outputs


def write_outputs(outputs: dict[str, bytes]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    unexpected = {
        path.name for path in OUTPUT_DIR.iterdir() if path.is_file()
    } - set(outputs)
    _require(not unexpected, f"unexpected existing audit files: {sorted(unexpected)}")
    for name, content in outputs.items():
        (OUTPUT_DIR / name).write_bytes(content)


def check_outputs(outputs: dict[str, bytes]) -> None:
    actual_names = {
        path.name for path in OUTPUT_DIR.iterdir() if path.is_file()
    }
    _require(actual_names == set(outputs), "audit artifact file set mismatch")
    for name, expected in outputs.items():
        actual = (OUTPUT_DIR / name).read_bytes()
        _require(actual == expected, f"deterministic rebuild mismatch: {name}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = build_outputs()
    if args.check:
        check_outputs(outputs)
        print("deterministic_rebuild=pass")
    else:
        write_outputs(outputs)
        print(f"wrote={len(outputs)} directory={OUTPUT_RELATIVE.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
