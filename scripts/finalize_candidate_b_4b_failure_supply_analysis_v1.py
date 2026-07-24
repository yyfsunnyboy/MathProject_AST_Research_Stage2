#!/usr/bin/env python3
"""Build deterministic ITT, taxonomy v3.1, eligibility, and report artifacts."""

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

from scripts import prepare_candidate_b_4b_failure_supply_analysis_v1 as prepared  # noqa: E402

OUTPUT_DIR = REPO_ROOT / prepared.OUTPUT_RELATIVE
RESULT_RELATIVE = Path("manual_h0_evalplus_run_001/h0_evalplus_results.csv")
EXECUTION_RELATIVE = Path("manual_h0_evalplus_run_001/execution_manifest.json")
TAXONOMY_VERSION = "v3.1"

TAXONOMY_FIELDS = (
    "cell_index", "program_id", "cell_identity", "task_id", "seed",
    "condition_id", "generation_id", "taxonomy_version",
    "classification_status", "primary_failure_layer",
    "secondary_failure_layers_json", "mechanism_tags_json", "failure_chain",
    "confidence", "outcome_validity", "evidence_basis",
)
ELIGIBILITY_FIELDS = (
    "cell_index", "program_id", "task_id", "seed", "condition_id",
    "generation_id", "healer_eligibility", "eligibility_reason",
    "eligibility_rule", "rejection_condition", "healer_applied",
    "h1_created", "rescue_result_created", "regression_result_created",
)
CELL_FIELDS = (
    "cell_index", "program_id", "cell_identity", "task_id", "seed",
    "condition_id", "generation_id", "itt_included", "generation_status",
    "raw_response_sha256", "extraction_status", "extracted_code_sha256",
    "h0_evaluation_disposition", "h0_base_status", "h0_plus_status",
    "h0_aggregate_status", "taxonomy_version", "primary_failure_layer",
    "mechanism_tags_json", "failure_chain", "confidence",
    "healer_eligibility",
)


class FinalizationError(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise FinalizationError(message)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _csv_bytes(fields: tuple[str, ...], rows: list[dict[str, Any]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _static_entry_point(code: str, entry_point: str) -> tuple[str, int]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return "syntax_error", 0
    count = sum(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == entry_point
        for node in tree.body
    )
    return "parsed", count


def _classification(
    extraction: dict[str, str],
    eval_row: dict[str, str] | None,
    code: str | None,
) -> dict[str, str]:
    if extraction["extraction_status"] != "extracted":
        return {
            "classification_status": "ADJUDICATED",
            "primary_failure_layer": "L0",
            "secondary_failure_layers_json": "[]",
            "mechanism_tags_json": json.dumps(["extraction_ambiguous", "fail_closed_no_candidate_selection"]),
            "failure_chain": "raw response persisted → multiple winning extraction candidates → no code selected → H0 not evaluated",
            "confidence": "HIGH",
            "outcome_validity": "VALID_GENERATION_PIPELINE_EXCLUSION",
            "evidence_basis": "canonical extraction replay and raw-response SHA only",
        }
    _require(eval_row is not None and code is not None, "extracted row missing EvalPlus/static evidence")
    parse_status, entry_count = _static_entry_point(code, eval_row["entry_point"])
    if parse_status == "syntax_error":
        return {
            "classification_status": "ADJUDICATED",
            "primary_failure_layer": "L1",
            "secondary_failure_layers_json": "[]",
            "mechanism_tags_json": json.dumps(["syntax_or_format_failure"]),
            "failure_chain": "canonical extraction succeeded → Python AST parse failed → required program structure unavailable",
            "confidence": "HIGH",
            "outcome_validity": "VALID_MODEL_OUTCOME",
            "evidence_basis": "offline AST parse; no hidden tests or expected outputs",
        }
    if entry_count != 1:
        tag = "missing_entry_point" if entry_count == 0 else "duplicate_required_entry_point"
        return {
            "classification_status": "ADJUDICATED",
            "primary_failure_layer": "L2",
            "secondary_failure_layers_json": "[]",
            "mechanism_tags_json": json.dumps([tag, "output_contract_failure"]),
            "failure_chain": f"canonical extraction succeeded → AST parsed → required entry point count={entry_count} → contract not satisfied",
            "confidence": "HIGH",
            "outcome_validity": "VALID_MODEL_OUTCOME",
            "evidence_basis": "offline AST and official public entry-point name",
        }
    base, plus = eval_row["base_status"], eval_row["plus_status"]
    if base == plus == "pass":
        return {
            "classification_status": "NOT_APPLICABLE_PASS",
            "primary_failure_layer": "",
            "secondary_failure_layers_json": "[]",
            "mechanism_tags_json": json.dumps(["h0_base_plus_pass"]),
            "failure_chain": "canonical extraction succeeded → H0 base pass → H0 plus pass → no failure layer assigned",
            "confidence": "HIGH",
            "outcome_validity": "VALID_MODEL_OUTCOME",
            "evidence_basis": "official EvalPlus aggregate statuses",
        }
    if base == "pass" and plus != "pass":
        tags = ["plus_only_failure_unlocalized", "diagnostic_execution_not_run"]
        chain = "canonical extraction succeeded → H0 base pass → H0 plus fail → root layer not localized"
    else:
        tags = ["base_and_plus_failure_unlocalized", "diagnostic_execution_not_run"]
        chain = "canonical extraction succeeded → H0 base fail → H0 plus fail → runtime versus semantic root not localized"
    return {
        "classification_status": "ADJUDICATED",
        "primary_failure_layer": "UNRESOLVED",
        "secondary_failure_layers_json": "[]",
        "mechanism_tags_json": json.dumps(tags),
        "failure_chain": chain,
        "confidence": "LOW",
        "outcome_validity": "VALID_MODEL_OUTCOME",
        "evidence_basis": "official EvalPlus statuses without result-driven code selection or diagnostic execution",
    }


def build_outputs() -> dict[str, bytes]:
    frozen_manifest_path = OUTPUT_DIR / "frozen_input_manifest.json"
    frozen_manifest_bytes = frozen_manifest_path.read_bytes()
    frozen_manifest = json.loads(frozen_manifest_bytes)
    extraction = _read_csv(OUTPUT_DIR / "extraction_itt_ledger.csv")
    inventory = _read_csv(OUTPUT_DIR / "generation_evidence_inventory.csv")
    eval_input = _read_jsonl(OUTPUT_DIR / "h0_evalplus_input.jsonl")
    results = _read_csv(OUTPUT_DIR / RESULT_RELATIVE)
    execution_bytes = (OUTPUT_DIR / EXECUTION_RELATIVE).read_bytes()
    execution = json.loads(execution_bytes)

    _require(len(extraction) == len(inventory) == 200, "ITT source row count drift")
    _require(len(eval_input) == len(results) == 186, "H0 evaluated row count drift")
    result_bytes = (OUTPUT_DIR / RESULT_RELATIVE).read_bytes()
    _require(_sha(result_bytes) == execution["results_sha256"], "EvalPlus result receipt mismatch")
    _require(execution["model_calls"] == 0 and execution["healer_applied"] is False and execution["h1_created"] is False, "evaluation account contamination")
    _require(execution["parallel"] == 1, "parallel drift")

    inventory_by_cell = {int(row["cell_index"]): row for row in inventory}
    extraction_by_cell = {int(row["cell_index"]): row for row in extraction}
    input_by_cell = {int(row["cell_index"]): row for row in eval_input}
    result_by_cell = {int(row["cell_index"]): row for row in results}
    _require(set(inventory_by_cell) == set(extraction_by_cell) == set(range(1, 201)), "ITT cell roster drift")
    _require(set(input_by_cell) == set(result_by_cell), "EvalPlus input/result roster drift")
    _require(set(result_by_cell) == set(range(1, 201)) - set(frozen_manifest["fail_closed_ambiguous_cells"]), "evaluation exclusion roster drift")

    taxonomy_rows: list[dict[str, Any]] = []
    eligibility_rows: list[dict[str, Any]] = []
    cell_rows: list[dict[str, Any]] = []
    for cell_index in range(1, 201):
        inv = inventory_by_cell[cell_index]
        ext = extraction_by_cell[cell_index]
        result = result_by_cell.get(cell_index)
        code = input_by_cell.get(cell_index, {}).get("completion")
        finding = _classification(ext, result, code)
        taxonomy = {
            "cell_index": cell_index,
            "program_id": inv["program_id"],
            "cell_identity": inv["cell_identity"],
            "task_id": inv["task_id"],
            "seed": inv["seed"],
            "condition_id": inv["condition_id"],
            "generation_id": inv["generation_id"],
            "taxonomy_version": TAXONOMY_VERSION,
            **finding,
        }
        taxonomy_rows.append(taxonomy)

        layer = finding["primary_failure_layer"]
        if finding["classification_status"] == "NOT_APPLICABLE_PASS":
            eligibility_reason = "H0 already passes base and plus; no failure-targeted Healer eligibility is needed."
        elif layer == "L0":
            eligibility_reason = "Extraction ambiguity has no unique answer-independent candidate; selecting a block is forbidden."
        elif layer == "UNRESOLVED":
            eligibility_reason = "Current evidence does not localize a unique L0-L5 root or a deterministic invariant-preserving repair."
        else:
            eligibility_reason = "A failure layer is identified, but no unique local repair rule is established across distinct tasks."
        eligibility = {
            "cell_index": cell_index,
            "program_id": inv["program_id"],
            "task_id": inv["task_id"],
            "seed": inv["seed"],
            "condition_id": inv["condition_id"],
            "generation_id": inv["generation_id"],
            "healer_eligibility": "abstain",
            "eligibility_reason": eligibility_reason,
            "eligibility_rule": "",
            "rejection_condition": "no unique answer-independent deterministic repair established",
            "healer_applied": "false",
            "h1_created": "false",
            "rescue_result_created": "false",
            "regression_result_created": "false",
        }
        eligibility_rows.append(eligibility)
        cell_rows.append({
            "cell_index": cell_index,
            "program_id": inv["program_id"],
            "cell_identity": inv["cell_identity"],
            "task_id": inv["task_id"],
            "seed": inv["seed"],
            "condition_id": inv["condition_id"],
            "generation_id": inv["generation_id"],
            "itt_included": "true",
            "generation_status": "success",
            "raw_response_sha256": inv["raw_response_sha256"],
            "extraction_status": ext["extraction_status"],
            "extracted_code_sha256": ext["extracted_code_sha256"],
            "h0_evaluation_disposition": ext["evaluation_disposition"],
            "h0_base_status": result["base_status"] if result else "not_evaluated_extraction_ambiguous",
            "h0_plus_status": result["plus_status"] if result else "not_evaluated_extraction_ambiguous",
            "h0_aggregate_status": result["aggregate_status"] if result else "not_evaluated_extraction_ambiguous",
            "taxonomy_version": TAXONOMY_VERSION,
            "primary_failure_layer": layer,
            "mechanism_tags_json": finding["mechanism_tags_json"],
            "failure_chain": finding["failure_chain"],
            "confidence": finding["confidence"],
            "healer_eligibility": "abstain",
        })

    extraction_dist = Counter(row["extraction_status"] for row in extraction)
    base_dist = Counter(row["base_status"] for row in results)
    plus_dist = Counter(row["plus_status"] for row in results)
    aggregate_dist = Counter(row["aggregate_status"] for row in results)
    taxonomy_dist = Counter(
        row["primary_failure_layer"] or "NOT_APPLICABLE_PASS" for row in taxonomy_rows
    )
    classification_dist = Counter(row["classification_status"] for row in taxonomy_rows)
    confidence_dist = Counter(row["confidence"] for row in taxonomy_rows)
    mechanism_dist: Counter[str] = Counter()
    for row in taxonomy_rows:
        mechanism_dist.update(json.loads(row["mechanism_tags_json"]))
    eligibility_dist = Counter(row["healer_eligibility"] for row in eligibility_rows)

    base_passes = base_dist["pass"]
    plus_passes = plus_dist["pass"]
    both_passes = aggregate_dist["pass"]
    summary = {
        "status": "analysis_complete",
        "scope": "Stage2_MBPP+_only",
        "run_id": prepared.frozen.RUN_ID,
        "itt_denominator": 200,
        "generation": {"completed": 200, "failed": 0, "model_calls_this_phase": 0},
        "extraction": dict(sorted(extraction_dist.items())),
        "h0_evalplus": {
            "evaluated": 186,
            "not_evaluated_extraction_ambiguous": 14,
            "base_status_evaluable": dict(sorted(base_dist.items())),
            "plus_status_evaluable": dict(sorted(plus_dist.items())),
            "aggregate_status_evaluable": dict(sorted(aggregate_dist.items())),
            "itt_base_pass": base_passes,
            "itt_plus_pass": plus_passes,
            "itt_base_plus_pass": both_passes,
            "itt_base_pass_rate": base_passes / 200,
            "itt_plus_pass_rate": plus_passes / 200,
            "itt_base_plus_pass_rate": both_passes / 200,
        },
        "taxonomy_v3_1": {
            "primary_distribution": dict(sorted(taxonomy_dist.items())),
            "classification_status_distribution": dict(sorted(classification_dist.items())),
            "confidence_distribution": dict(sorted(confidence_dist.items())),
            "mechanism_tag_distribution": dict(sorted(mechanism_dist.items())),
        },
        "healer_eligibility": {
            "eligible": eligibility_dist["eligible"],
            "conditional": eligibility_dist["conditional"],
            "abstain": eligibility_dist["abstain"],
        },
        "cell5": {
            "task_id": "Mbpp/633", "condition_id": "Ab1_H0", "seed": 33,
            "extraction_status": "ambiguous", "candidate_selected": False,
            "itt_included": True, "h0_evaluated": False,
            "primary_failure_layer": "L0", "healer_eligibility": "abstain",
        },
        "healer_applied": False,
        "h1_created": False,
        "rescue_results_created": False,
        "regression_results_created": False,
    }

    outputs = {
        "taxonomy_v31_ledger.csv": _csv_bytes(TAXONOMY_FIELDS, taxonomy_rows),
        "healer_eligibility_ledger.csv": _csv_bytes(ELIGIBILITY_FIELDS, eligibility_rows),
        "cell_itt_ledger.csv": _csv_bytes(CELL_FIELDS, cell_rows),
        "aggregate_summary.json": _json_bytes(summary),
    }
    receipt = {
        "receipt_version": "candidate_b_4b_failure_supply_pilot_reproducibility_v1",
        "status": "complete_pending_independent_audit",
        "start_head": prepared.START_HEAD,
        "run_id": prepared.frozen.RUN_ID,
        "generation_manifest_sha256": prepared.EXPECTED_MANIFEST_SHA256,
        "frozen_input_manifest_sha256": _sha(frozen_manifest_bytes),
        "evalplus_execution_manifest_sha256": _sha(execution_bytes),
        "evalplus_results_sha256": _sha(result_bytes),
        "deterministic_output_sha256": {name: _sha(data) for name, data in sorted(outputs.items())},
        "model_calls": 0,
        "parallel": 1,
        "canonical_extraction_sha256": prepared.EXPECTED_PIPELINE_SHA256,
        "formal_evaluation_environment": {
            "os": "WSL/Linux", "python": "/home/yehya/.venvs/ast_evalplus/bin/python",
            "evalplus": "0.3.1", "dataset_version": "v0.2.0",
            "dataset_hash": "ee43ecabebf20deef4bb776a405ac5b1",
        },
        "preexecution_driver_incident": {
            "occurred": True,
            "candidate_cells_evaluated_before_failure": 0,
            "output_directory_created": False,
            "reason": "initial driver called check_correctness with one tuple instead of positional arguments",
            "disposition": "runner signature corrected before any candidate evaluation; formal output created once",
        },
    }
    outputs["reproducibility_receipt.json"] = _json_bytes(receipt)
    report = f"""# Stage2 qwen3.5:4b failure-supply pilot 研究報告

## 範圍與資料完整性

本輪僅處理 Stage2／MBPP+ run `{prepared.frozen.RUN_ID}`。凍結 manifest SHA-256 為
`{prepared.EXPECTED_MANIFEST_SHA256}`。200 格 generation journal、raw response 與 identity
均驗收通過；本輪 model calls=0，未修改既有 raw、journal、prompt、manifest 或 frozen artifact。
generation `failed=0` 只表示 200 格回應已持久化，不代表 200 格程式正確。

## 離線抽取與 ITT

使用 repo canonical `agent_tools/finals_rebuild/extraction.py`（SHA-256
`{prepared.EXPECTED_PIPELINE_SHA256}`）重放：186 格 extracted、14 格 ambiguous。所有 200
格均保留於 ITT 分母；14 格沒有依評測或任一候選內容選程式，因此不送 EvalPlus。
Cell 5（Mbpp/633／Ab1_H0／seed=33）維持 ambiguous、未選 code block、ITT 保留。

## H0 EvalPlus

正式環境為 WSL/Linux、EvalPlus 0.3.1、MBPP+ v0.2.0、parallel=1。可評測 186 格中，
base pass={base_passes}、plus pass={plus_passes}、base+plus aggregate pass={both_passes}。
以 200 格 ITT 分母計，base={base_passes}/200（{base_passes/200:.1%}）、
plus={plus_passes}/200（{plus_passes/200:.1%}）、aggregate={both_passes}/200（{both_passes/200:.1%}）。

## Taxonomy v3.1 與 Healer eligibility

Primary 分布：{json.dumps(dict(sorted(taxonomy_dist.items())), ensure_ascii=False)}。
本輪只使用 extraction、AST、公開 entry point 與 EvalPlus aggregate status。base/plus FAIL
本身不足以區分 runtime 與 semantic root，因此未硬歸 L5，而保留 UNRESOLVED/LOW。
eligibility：eligible=0、conditional=0、abstain=200。未套用或修改 Healer，未建立 H1、
rescue 或 regression 結果。

## 限制

這是 20 個 development tasks 的 failure-supply pilot，不是 validation、confirmatory 或
sealed-reserve 結論。14 格 extraction ambiguity 以 fail-closed 計入 ITT 非通過；186 格評測
只保存 base/plus aggregate status，沒有使用 hidden inputs、canonical solution、expected/actual
或 PASS/FAIL 回饋挑選程式。由於未執行額外定位 diagnostics，多數測試失敗只能安全標為
UNRESOLVED；這是證據邊界，不代表已證明不存在 L3、L4 或 L5 問題。

## 結論

本輪資料可作為 Stage2 MBPP+ 4B failure supply 與後續安全規則研究的 audited input；
目前沒有任何格具備足以授權 Healer 的唯一、答案獨立、確定性修復證據。
"""
    outputs["research_report_zh.md"] = report.encode("utf-8")
    return outputs


def write_or_check(outputs: dict[str, bytes], check: bool) -> None:
    for name, data in outputs.items():
        path = OUTPUT_DIR / name
        if check:
            _require(path.is_file() and path.read_bytes() == data, f"deterministic rebuild drift: {name}")
        else:
            _require(not path.exists(), f"refusing to overwrite finalized artifact: {name}")
            path.write_bytes(data)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = build_outputs()
    write_or_check(outputs, args.check)
    print(json.dumps({"status": "deterministic_final_rebuild_passed" if args.check else "analysis_finalized", "file_count": len(outputs)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
