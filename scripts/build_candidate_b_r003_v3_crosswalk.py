#!/usr/bin/env python3
"""Build the immutable v3 crosswalk and freeze the unresolved-198 protocol."""

from __future__ import annotations

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
    "candidate_b_r003_v3_crosswalk_diagnostics_protocol_v1"
)
START_HEAD = "a104ceacfe6d4c371ce4d50ad938ae39fd4578ea"
REVISION = "candidate_b_r003_v3_crosswalk_001"
SPLIT_ID = "mbpp_candidate_b_development60_r003"
V3_ATTACHMENT = Path(r"C:\Users\yehya\Downloads\AI 生成程式共同失敗分類標準（實際使用版 v3）.md")
V3_ATTACHMENT_SHA256 = "7df8f4472ce048569967436cbc73ede8fd4bd117ad67d0028ddd95af2055a304"

CENSUS = Path("artifacts/public_benchmark_governance/candidate_b_r003_failure_census_v1/candidate_b_r003_failure_census.csv")
CENSUS_MANIFEST = CENSUS.parent / "manifest.json"
ADJUDICATION = Path("artifacts/public_benchmark_governance/candidate_b_r003_failure_census_human_review_adjudication_v1/adjudication_results.csv")
ADJUDICATION_MANIFEST = ADJUDICATION.parent / "manifest.json"
ACCOUNTS = Path("artifacts/public_benchmark_governance/candidate_b_r003_h0_h1_evalplus_v1/candidate_b_h0_h1_accounts.csv")
PAIRED = Path("artifacts/public_benchmark_governance/candidate_b_r003_formal_paired_analysis_v1/paired_cell_results.csv")
PAIRED_MANIFEST = PAIRED.parent / "manifest.json"
JOURNAL = Path("artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/mbpp_q35_9b_candidate_b_development60_replay_r003/h0_h1_accounts.jsonl")

SOURCE_HASHES = {
    CENSUS: "289b2d1e562453bb944032254cc02b47d738a504720aca6dc85da6c252c10740",
    CENSUS_MANIFEST: "6e2dfa1ea9fbc3f7362f8f69ff5b02bae9edb57a4134ca3a6ec58cabfa594593",
    ADJUDICATION: "b244f6c7ca6d291906dadd36992371cf9b5a57bd56a1e59c227b0efbd5468256",
    ADJUDICATION_MANIFEST: "391857eaaff6cf838b37d02a07582d55d141ccca9387781db46139606b1abd28",
    ACCOUNTS: "54e05091ef35af7f99a32a5409c74f688d00c2564d31b8a52301af8d65ce360e",
    PAIRED: "425efbf8351cc2d1fbe2a0f22e5c6ae5e2bc29b57ee8da6a7a9adfe88752ae43",
    PAIRED_MANIFEST: "88576cfd91968df9fdb92de76af031724156c0fafb37c384c8930f726fc33d86",
    JOURNAL: "b1313615bf41840bc1c45c36d2b8ac9b544f37fb5bb801c104aad1657ca2c2ec",
    Path("agent_tools/finals_rebuild/extraction.py"): "a59da1c0a76fe24e868a51481306a5ea09d8d8977c92aab38a6c0c4dc38feccf",
    Path("agent_tools/finals_rebuild/mbpp_evaluator_blind_healer.py"): "cf4d086ca6e3af968f31b0d087ed2479e5ad38be4b7abe5d2ce5516b68000d44",
}

V3_FIELDS = (
    "v3_classification_revision", "v3_classification_status",
    "v3_primary_failure_layer", "v3_g3e_entry_point",
    "v3_g3s_output_schema", "v3_mechanism_tags",
    "v3_outcome_validity", "v3_healer_eligibility",
    "v3_healer_decision", "v3_healer_outcome", "v3_evidence_role",
    "v3_split_id", "v3_evidence_basis", "v3_responsibility_notes",
    "v3_diagnostics_allowed_as_healer_runtime_input",
)


class CrosswalkError(RuntimeError):
    """Fail-closed identity, hash, schema, or policy error."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CrosswalkError(message)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _csv_bytes(fields: tuple[str, ...], rows: list[dict[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows({field: row.get(field, "") for field in fields} for row in rows)
    return stream.getvalue().encode("utf-8")


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def _index_unique(rows: list[dict[str, str]], field: str, label: str) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        key = row[field]
        _require(key not in result, f"duplicate identity in {label}: {key}")
        result[key] = row
    return result


def _verify_inputs(repo: Path, attachment: Path) -> None:
    _require(attachment.is_file(), "v3 attachment missing")
    _require(_sha(attachment.read_bytes()) == V3_ATTACHMENT_SHA256, "v3 attachment hash drift")
    for relative, expected in SOURCE_HASHES.items():
        path = repo / relative
        _require(path.is_file(), f"frozen source missing: {relative.as_posix()}")
        _require(_sha(path.read_bytes()) == expected, f"frozen source hash drift: {relative.as_posix()}")


def _v3_tags(census: dict[str, str], adjudication: dict[str, str] | None) -> list[str]:
    layer = census["primary_failure_layer"]
    subtype = census["failure_subtype"]
    tags: set[str] = set()
    if layer == "UNRESOLVED":
        return ["needs_human_review"]
    if layer == "PASSED":
        return []
    if layer == "L1":
        tags.add("model_assembly_failure")
        if subtype == "GENERATION_TRUNCATED":
            tags.add("truncation")
        if adjudication:
            reviewed = adjudication["adjudicated_subtype"]
            if "TEXT_POLLUTION" in reviewed or "DOCSTRING" in reviewed:
                tags.add("format_contamination")
            if "TRUNCATED" in reviewed:
                tags.add("truncation")
            if "REPEATED" in reviewed or "DUPLICATE" in reviewed:
                tags.add("code_bloat")
    elif subtype == "REQUIRED_FUNCTION_MISSING_AMBIGUOUS":
        tags.update(("ambiguous_entry_point", "entry_point_mismatch"))
    elif subtype == "REQUIRED_FUNCTION_MISSING_UNIQUE_ALIAS":
        tags.add("entry_point_mismatch")
    elif subtype == "REQUIRED_SIGNATURE_INCOMPATIBLE":
        tags.add("signature_mismatch")
    return sorted(tags)


def _diagnostic_protocol() -> dict[str, Any]:
    return {
        "protocol_version": "candidate_b_r003_unresolved198_coarse_diagnostics_v1",
        "status": "prepared_not_executed",
        "population": {"cells": 198, "legacy_layer": "UNRESOLVED", "outcome_validity": "PENDING_REVIEW"},
        "classification_order": ["infrastructure", "G1", "G3e", "G2", "G3s", "G3a", "G4"],
        "execution_environment": {
            "os": "WSL/Linux only",
            "python": "/home/yehya/.venvs/ast_evalplus/bin/python",
            "evalplus_package_version_for_frozen_dataset_loader_only": "0.3.1",
            "dataset_version": "v0.2.0",
            "dataset_hash": "ee43ecabebf20deef4bb776a405ac5b1",
            "parallel": 1,
            "per_cell_timeout_seconds": 10,
        },
        "allowed_result_fields": [
            "cell_identity_sha256", "program_id", "task_identity_sha256",
            "evaluation_source_sha256", "evaluator_hash", "protocol_sha256",
            "phase", "exception_class", "model_source_line",
            "model_source_ast_node", "entry_point_bound",
            "entry_point_callable", "signature_binding", "termination",
            "return_type_bucket", "return_shape_bucket",
        ],
        "forbidden_result_fields_or_content": [
            "hidden_input", "test_input", "expected_value", "actual_value",
            "exception_message", "assertion_message", "traceback", "stdout",
            "stderr", "source", "completion", "reference_solution",
        ],
        "g3s_policy": "NOT_APPLICABLE unless a separately frozen public MBPP+ output-schema contract exists; type/shape buckets are diagnostic observations only",
        "g3a_policy": "NOT_APPLICABLE for this ordinary MBPP+ split; no required Domain API was frozen",
        "g4_policy": "not re-executed or re-scored by this diagnostic runner",
        "healer_runtime_input": False,
        "diagnostic_results_may_define_or_trigger_healer_rules": False,
        "output_directory": str(OUTPUT_RELATIVE / "manual_diagnostics_run_001").replace("\\", "/"),
        "retry_resume_overwrite": False,
    }


def build_analysis(repo: Path = REPO_ROOT, attachment: Path = V3_ATTACHMENT) -> dict[str, Any]:
    _verify_inputs(repo, attachment)
    legacy_fields, census_rows = _read_csv(repo / CENSUS)
    adjud_fields, adjud_rows = _read_csv(repo / ADJUDICATION)
    _, account_rows = _read_csv(repo / ACCOUNTS)
    _, paired_rows = _read_csv(repo / PAIRED)
    _require(len(census_rows) == 300, "legacy census must contain 300 rows")
    census_by_id = _index_unique(census_rows, "program_id", "legacy census")
    adjud_by_id = _index_unique(adjud_rows, "program_id", "21-case adjudication")
    _require(len(adjud_by_id) == 21 and set(adjud_by_id) <= set(census_by_id), "adjudication identity drift")
    h1_by_id = _index_unique([row for row in account_rows if row["healer_account"] == "H1"], "program_id", "Candidate B H1")
    paired_by_id = _index_unique([row for row in paired_rows if row["prompt_condition"] == "Candidate_B"], "program_id", "paired Candidate B")
    _require(set(census_by_id) == set(h1_by_id) == set(paired_by_id), "cross-source program identity mismatch")

    prefixed_adjud_fields = [f"legacy_adjudication_{field}" for field in adjud_fields]
    output_rows: list[dict[str, Any]] = []
    diagnostic_rows: list[dict[str, str]] = []
    for legacy in census_rows:
        pid = legacy["program_id"]
        layer = legacy["primary_failure_layer"]
        adjud = adjud_by_id.get(pid)
        h1 = h1_by_id[pid]
        paired = paired_by_id[pid]
        _require(h1["healer_status"] in {"transformed", "abstained", "no_trigger"}, "unexpected H1 decision")
        transition = paired["healer_transition"]
        _require(transition in {"fail_to_fail", "pass_to_pass"}, "unexpected Candidate B H0/H1 transition")
        if layer == "UNRESOLVED":
            status, v3_layer, validity, eligibility = "PENDING_REVIEW", "", "PENDING_REVIEW", "undetermined"
            basis = "legacy_aggregate_evaluator_status_only;21_case_adjudication_preserved_but_not_promoted_without_frozen_diagnostics" if adjud else "legacy_aggregate_evaluator_status_only"
        elif layer == "PASSED":
            status, v3_layer, validity, eligibility = "ADJUDICATED", "", "VALID_MODEL_OUTCOME", "noneligible"
            basis = "legacy_frozen_negative_control_pass"
        else:
            status, v3_layer, validity = "ADJUDICATED", layer, legacy["outcome_validity"]
            eligibility = "eligible" if legacy["failure_subtype"] == "REQUIRED_FUNCTION_MISSING_UNIQUE_ALIAS" else "noneligible"
            basis = "legacy_census+21_case_adjudication" if adjud else "legacy_census_machine_parse_or_contract_evidence"
        g3e = "NOT_ASSESSED" if layer == "L1" else ("FAIL" if layer == "L2" else "PASS")
        g3s = "NOT_APPLICABLE"
        outcome = "preserved_pass" if transition == "pass_to_pass" else "unchanged_fail"
        result: dict[str, Any] = dict(legacy)
        for field, prefixed in zip(adjud_fields, prefixed_adjud_fields):
            result[prefixed] = adjud[field] if adjud else ""
        result.update({
            "v3_classification_revision": REVISION,
            "v3_classification_status": status,
            "v3_primary_failure_layer": v3_layer,
            "v3_g3e_entry_point": g3e,
            "v3_g3s_output_schema": g3s,
            "v3_mechanism_tags": json.dumps(_v3_tags(legacy, adjud), ensure_ascii=False, separators=(",", ":")),
            "v3_outcome_validity": validity,
            "v3_healer_eligibility": eligibility,
            "v3_healer_decision": h1["healer_status"],
            "v3_healer_outcome": outcome,
            "v3_evidence_role": "development",
            "v3_split_id": SPLIT_ID,
            "v3_evidence_basis": basis,
            "v3_responsibility_notes": "evidence insufficient; retain pending review" if status == "PENDING_REVIEW" else "derived annotation; legacy result unchanged",
            "v3_diagnostics_allowed_as_healer_runtime_input": "false",
        })
        output_rows.append(result)
        if layer == "UNRESOLVED":
            cell_identity = _sha(json.dumps({
                "program_id": pid,
                "source": legacy["evaluation_source_sha256"],
                "evaluator": legacy["evaluator_hash"],
            }, sort_keys=True, separators=(",", ":")).encode("utf-8"))
            diagnostic_rows.append({
                "cell_identity_sha256": cell_identity,
                "program_id": pid,
                "task_identity_sha256": _sha(legacy["task_id"].encode("utf-8")),
                "generation_id": legacy["generation_id"],
                "evaluation_source_sha256": legacy["evaluation_source_sha256"],
                "prompt_hash": legacy["prompt_hash"].removeprefix("sha256:"),
                "evaluator_hash": legacy["evaluator_hash"].removeprefix("sha256:"),
                "classification_status": "PENDING_REVIEW",
                "primary_failure_layer": "",
            })

    counts = Counter(row["v3_primary_failure_layer"] or ("PENDING_REVIEW" if row["v3_classification_status"] == "PENDING_REVIEW" else "PASSED") for row in output_rows)
    _require(counts == Counter({"PENDING_REVIEW": 198, "PASSED": 76, "L1": 20, "L2": 6}), "v3 crosswalk count drift")
    _require(len(diagnostic_rows) == len({row["cell_identity_sha256"] for row in diagnostic_rows}) == 198, "diagnostic identity drift")
    return {
        "legacy_fields": legacy_fields,
        "adjudication_fields": adjud_fields,
        "crosswalk_rows": output_rows,
        "diagnostic_rows": sorted(diagnostic_rows, key=lambda row: row["program_id"]),
        "counts": dict(sorted(counts.items())),
    }


def _privacy_policy() -> str:
    return """# Candidate B r003 unresolved198 diagnostics privacy policy

本政策適用於 `candidate_b_r003_unresolved198_coarse_diagnostics_v1`。本輪僅凍結，沒有執行 diagnostics。

## 允許保存

每格只可保存：phase、exception class、最後一個 model-source frame 的行號與 AST node kind、entry-point／callable／signature binding 結果、termination、return type bucket、return shape bucket，以及 program/source/task/evaluator/protocol identity hashes。

## 絕對禁止保存

不得保存 hidden 或 public test input、expected/actual value、return value、exception/assertion message、traceback、stdout/stderr 內容、candidate source、reference solution 或 evaluator frame。CSV header 與每個值都必須通過 allowlist；出現未知欄位、換行文字或未允許內容即 fail-closed，且不得建立 output directory。

## 使用隔離

diagnostic 結果只供後續人工分類 revision 使用，不得成為 Healer runtime input、rule trigger、transformation parameter、答案推導資料或 validation 選擇訊號。任何新 mechanism／rule family 必須另行版本化，具至少跨兩個不同 task 的證據，並同時滿足 Local、Deterministic、Answer-free、Task-agnostic、Unique、Invariant-supported、Tested、Frozen、Evaluator-blind；否則 abstain。

## 執行紀律

僅能在 WSL/Linux、固定 Python/EvalPlus dataset loader 版本、parallel=1、無 retry/resume/overwrite 下，以 manifest 中唯一 output path 人工執行一次。runner 不執行 EvalPlus correctness、不寫 G4 結論，也不修改 census、adjudication、Prompt、Healer、Pipeline 或 validation。
"""


def _report(counts: dict[str, int]) -> str:
    return f"""# Candidate B r003 v3 derived crosswalk 與 unresolved198 diagnostics freeze

## Derived crosswalk

此目錄是 development evidence 的衍生 view，不覆寫既有 census、21 案 adjudication、統計、manifest 或 hash。輸出逐欄保存原 census，並以 `legacy_adjudication_*` 保存 21 案裁決；所有 v3 欄位另加前綴。

- L1：{counts['L1']}。依既有 G1／parse evidence crosswalk；truncation 僅作 mechanism tag。
- L2：{counts['L2']}。皆由 G3e entry-point／signature evidence crosswalk。
- PASSED controls：{counts['PASSED']}，不配置 failure layer。
- PENDING_REVIEW：{counts['PENDING_REVIEW']}，`v3_primary_failure_layer` 保持 CSV null（空值），沒有猜成 L4 或 L5。

21 案 adjudication 仍完整保留為 legacy evidence。即使其中曾提出更細的人工診斷，本 revision 也不以少數代表案回填 198 格；必須等待 frozen coarse diagnostics 後另建 revision。

## Healer 三欄

`healer_eligibility`、`healer_decision`、`healer_outcome` 已拆開。兩個既有 unique alias 為 eligible／transformed／unchanged_fail；其他已裁決 L1/L2 不符合完整 v3 安全條件。198 unresolved 的 eligibility 為 undetermined，實際 v0 decision 與 paired outcome仍依 frozen artifact記錄。

## Diagnostics freeze

protocol 的判定順序固定為 infrastructure → G1 → G3e → G2 → G3s → G3a → G4。runner 只輸出 allowlisted 粗粒度欄位，不保存輸入、expected/actual、訊息或 traceback；不執行 EvalPlus correctness，且結果永遠不得成為 Healer runtime input。本輪 diagnostics executions 為 0。
"""


def build_outputs(repo: Path = REPO_ROOT, attachment: Path = V3_ATTACHMENT) -> dict[Path, bytes]:
    result = build_analysis(repo, attachment)
    legacy_fields = result["legacy_fields"]
    adjud_fields = [f"legacy_adjudication_{field}" for field in result["adjudication_fields"]]
    crosswalk_fields = tuple(legacy_fields + adjud_fields + list(V3_FIELDS))
    protocol = _diagnostic_protocol()
    protocol_bytes = _json_bytes(protocol)
    protocol_sha = _sha(protocol_bytes)
    diagnostic_rows = result["diagnostic_rows"]
    for row in diagnostic_rows:
        row["protocol_sha256"] = protocol_sha
    diag_fields = (
        "cell_identity_sha256", "program_id", "task_identity_sha256",
        "generation_id", "evaluation_source_sha256", "prompt_hash",
        "evaluator_hash", "protocol_sha256", "classification_status",
        "primary_failure_layer",
    )
    summary_rows = [
        {"v3_bucket": bucket, "cells": count, "evidence_role": "development", "split_id": SPLIT_ID, "revision": REVISION}
        for bucket, count in (("L1", 20), ("L2", 6), ("PASSED", 76), ("PENDING_REVIEW_LAYER_NULL", 198))
    ]
    outputs: dict[Path, bytes] = {
        Path("candidate_b_r003_v3_derived_crosswalk.csv"): _csv_bytes(crosswalk_fields, result["crosswalk_rows"]),
        Path("v3_crosswalk_summary.csv"): _csv_bytes(tuple(summary_rows[0]), summary_rows),
        Path("unresolved198_diagnostics_input_ledger.csv"): _csv_bytes(diag_fields, diagnostic_rows),
        Path("diagnostics_protocol.json"): protocol_bytes,
        Path("diagnostics_output_schema.json"): _json_bytes({
            "schema_version": "candidate_b_r003_unresolved198_diagnostics_output_v1",
            "fields": protocol["allowed_result_fields"],
            "additional_fields": False,
            "null_representation": "empty CSV field",
            "row_count": 198,
        }),
        Path("diagnostics_privacy_policy_zh.md"): _privacy_policy().encode("utf-8"),
        Path("v3_crosswalk_report_zh.md"): _report(result["counts"]).encode("utf-8"),
        Path("provenance.json"): _json_bytes({
            "analysis_version": "candidate_b_r003_v3_crosswalk_diagnostics_protocol_v1",
            "start_head": START_HEAD,
            "v3_attachment_sha256": V3_ATTACHMENT_SHA256,
            "legacy_artifacts_overwritten": False,
            "legacy_fields_preserved": True,
            "evidence_role": "development",
            "diagnostics_executed": False,
            "diagnostic_results_allowed_as_healer_runtime_input": False,
        }),
        Path("execution_manifest.json"): _json_bytes({
            "status": "crosswalk_complete_diagnostics_prepared_not_executed",
            "model_calls": 0,
            "evalplus_executions": 0,
            "diagnostic_executions": 0,
            "healer_rules_modified": False,
            "prompt_pipeline_validation_modified": False,
            "validation_not_executed": True,
        }),
    }
    source_ledger = [
        {"path": path.as_posix(), "role": "frozen_repo_input", "sha256": digest}
        for path, digest in sorted(SOURCE_HASHES.items(), key=lambda item: item[0].as_posix())
    ]
    source_ledger.append({"path": str(attachment), "role": "external_v3_codebook", "sha256": V3_ATTACHMENT_SHA256})
    outputs[Path("source_hash_ledger.csv")] = _csv_bytes(("path", "role", "sha256"), source_ledger)

    analyzer = Path("scripts/build_candidate_b_r003_v3_crosswalk.py")
    runner = Path("scripts/run_candidate_b_r003_unresolved_diagnostics.py")
    tests = Path("tests/finals_rebuild/test_candidate_b_r003_v3_crosswalk_diagnostics.py")
    for path in (analyzer, runner, tests):
        _require((repo / path).is_file(), f"required reproducibility source missing: {path.as_posix()}")
    output_hashes = {path.as_posix(): _sha(content) for path, content in sorted(outputs.items(), key=lambda item: item[0].as_posix())}
    manifest = {
        "manifest_version": "candidate_b_r003_v3_crosswalk_diagnostics_protocol_v1",
        "status": "complete_crosswalk_diagnostics_prepared_not_executed",
        "counts": {"programs": 300, "L1": 20, "L2": 6, "passed": 76, "pending_review_layer_null": 198, "diagnostic_input_cells": 198},
        "v3_classification_revision": REVISION,
        "diagnostics_protocol_sha256": protocol_sha,
        "diagnostics_output_directory_created": False,
        "new_rule_families_frozen": 0,
        "model_calls": 0,
        "evalplus_executions": 0,
        "diagnostic_executions": 0,
        "healer_rules_modified": False,
        "validation_not_executed": True,
        "source_sha256": {
            analyzer.as_posix(): _sha((repo / analyzer).read_bytes()),
            runner.as_posix(): _sha((repo / runner).read_bytes()),
            tests.as_posix(): _sha((repo / tests).read_bytes()),
        },
        "outputs_sha256_excluding_manifest_and_operator_guide": output_hashes,
    }
    manifest_bytes = _json_bytes(manifest)
    outputs[Path("manifest.json")] = manifest_bytes
    manifest_sha = _sha(manifest_bytes)
    command = (
        "cd /mnt/c/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2 && "
        "/home/yehya/.venvs/ast_evalplus/bin/python "
        "scripts/run_candidate_b_r003_unresolved_diagnostics.py "
        "--manifest artifacts/public_benchmark_governance/"
        "candidate_b_r003_v3_crosswalk_diagnostics_protocol_v1/manifest.json "
        f"--manifest-sha256 {manifest_sha} --parallel 1 "
        "--output-dir artifacts/public_benchmark_governance/"
        "candidate_b_r003_v3_crosswalk_diagnostics_protocol_v1/manual_diagnostics_run_001 "
        "--execute-frozen-diagnostics"
    )
    outputs[Path("operator_guide_zh.md")] = (
        "# unresolved198 coarse diagnostics operator guide\n\n"
        "本輪未執行 diagnostics。下列是唯一允許的人工 WSL 指令；禁止 retry、resume、overwrite、"
        "parallel>1 或其他 output path。\n\n```bash\n" + command + "\n```\n"
    ).encode("utf-8")
    return outputs


def write_outputs(repo: Path = REPO_ROOT, attachment: Path = V3_ATTACHMENT) -> Path:
    output_dir = repo / OUTPUT_RELATIVE
    output_dir.mkdir(parents=True, exist_ok=True)
    for relative, content in build_outputs(repo, attachment).items():
        (output_dir / relative).write_bytes(content)
    return output_dir


def main() -> int:
    print(write_outputs())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
