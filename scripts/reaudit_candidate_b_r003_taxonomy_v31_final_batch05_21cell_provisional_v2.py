#!/usr/bin/env python3
"""Independent mechanical/static re-audit of Final Batch05 provisional v2."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_RELATIVE = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_final_batch05_21cell_provisional_v2_independent_reaudit_v1")
START_HEAD = "1aa7b692c4d499ada2e0b6e0799b3475f2f68b18"
STATUS = "INDEPENDENT_V2_REAUDIT_COMPLETE_NO_MATERIAL_FINDINGS"
VERDICT = "READY_TO_FREEZE_FINAL_BATCH05_PROVISIONAL_V2"
TARGET_RANK = "17"
TARGET_PROGRAM = "fa5a49bae5aacc269bbba5a927d4839d1c04e0afa4d2d508cfc95d34df05c877"

V1 = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_final_batch05_21cell_provisional_v1/adjudication_records.csv")
AUDIT_DIR = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_final_batch05_21cell_provisional_v1_independent_audit_v1")
AUDIT_FINDINGS = AUDIT_DIR / "per_cell_audit_findings.csv"
AUDIT_DIFFERENCES = AUDIT_DIR / "field_level_difference_ledger.csv"
AUDIT_MATERIAL = AUDIT_DIR / "material_findings.csv"
AUDIT_MANIFEST = AUDIT_DIR / "manifest.json"
V2_DIR = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_final_batch05_21cell_provisional_v2")
V2 = V2_DIR / "adjudication_records.csv"
V2_MANIFEST = V2_DIR / "manifest.json"
V2_DIFFERENCES = V2_DIR / "approved_difference_ledger.csv"
V2_MECHANISMS = V2_DIR / "mechanism_ledger.csv"
V2_CHAINS = V2_DIR / "failure_chain_ledger.csv"
V2_SUMMARY = V2_DIR / "adjudication_summary.json"
V2_GAPS = V2_DIR / "unresolved_evidence_gaps.csv"
V2_EXECUTION = V2_DIR / "execution_counts.json"
V2_PROVENANCE = V2_DIR / "provenance.json"
V2_REPORT = V2_DIR / "report_zh.md"
V2_BUILDER = Path("scripts/adjudicate_candidate_b_r003_taxonomy_v31_final_batch05_21cell_provisional_v2.py")
V2_TEST = Path("tests/finals_rebuild/test_candidate_b_r003_taxonomy_v31_final_batch05_21cell_provisional_v2.py")
ROSTER = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_final_batch05_21cell_roster_v1/batch05_roster.csv")
ACCOUNTS = Path("artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/mbpp_q35_9b_candidate_b_development60_replay_r003/h0_h1_accounts.jsonl")
TASKS = Path("data/mbpp_plus/tasks.jsonl")
EVALPLUS = Path("artifacts/public_benchmark_governance/candidate_b_r003_h0_h1_evalplus_v1/manual_evalplus_run_001/evalplus_results.csv")
PREPARATION = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v3_formal_classification_preparation_v1/classification_preparation.csv")
CUMULATIVE177 = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_frozen_progress_census_v4/cumulative_frozen_identity_ledger.csv")
TAXONOMY = Path("C:/Users/yehya/Downloads/AI_生成程式共同失敗分類標準_實際使用版_v3.1.md")

SOURCE_HASHES = {
    V1: "ab6b389c1c9d04d72e6bed6a415b422eb222f9b4a8a1cec238ba2af6c34c291c",
    AUDIT_FINDINGS: "ba74b40e03eae81494e2fa84d26a6bbdb98cf0c9cb88543093f428b15d1a2afc",
    AUDIT_DIFFERENCES: "342c36d39063f4878bcd7b02f749a31d592e888d006a7286f02c67e200fc99e7",
    AUDIT_MATERIAL: "86fb73fd1bc61f4b7b8ae2590280510561c6bb9b5d338fea510ab91780b3d314",
    AUDIT_MANIFEST: "5cef1a885e710ede709d97c02d7bb261c8ad2a979b233790a1f81a4d86f6705c",
    V2: "22faba56d483e172064338f2649533e4758bfd1110e64467d8ce6eff2a47cf34",
    V2_MANIFEST: "326604be78641011c7121c157dfc5c0ba2c1082dfcd1228c078bf1c67685a595",
    V2_DIFFERENCES: "0d575930ee91d521e3ae2d11a3b989e578d922da9185744cf5b9915915acef01",
    V2_MECHANISMS: "5598e35524a33371e4aca38697e5cf51c9e4264cd2e4e38490419e4e13cf4fa2",
    V2_CHAINS: "d397088f5c067a4cefad360dc5ea4cb34a66c0fee227cc90961ba635007dd025",
    V2_SUMMARY: "d4e0e3abbab18e492af1d11b8b122cecf63449d6f598f8d87d012a6e72e92596",
    V2_GAPS: "72866c3b068c76576c3744b06bdf61d7d8b87d28af1ac0285ebfbd9e6df44ee7",
    V2_EXECUTION: "046f0571a0f3c6039edda24ba333324ae5d7063e606a91d353a7cc2ddb1da217",
    V2_PROVENANCE: "41954e55a692a2dd7f58a7b5c04aa750153deb050867fcd6b6c54b0536b68ed1",
    V2_REPORT: "37a3403a2bd641f0d61db67cc9ac0af3741e30e4c37ba90e29a9e36927365759",
    V2_BUILDER: "b8b5eff5bc5242a88731d5e374a7dce438b333acdcedc7798c82e4a6f571b797",
    V2_TEST: "4b0cd78d40e995ebef71d3a01ae95d34e5a486d04a26d9ea53c28807cc980a63",
    ROSTER: "4ec24e450a66c50db46230a5b950137af6e6a4cb3d9a067f182a545818851764",
    ACCOUNTS: "b1313615bf41840bc1c45c36d2b8ac9b544f37fb5bb801c104aad1657ca2c2ec",
    TASKS: "b816022b8b587047cb1d275417a96acb009de328684e5914e7ac010c9d8c6f3c",
    EVALPLUS: "338e66ecd09f48bcf2b8c8d1c8cf75911755dad92743c99257698d994a01938e",
    PREPARATION: "5b0106b93f2d192d89c740659f83021956c15113397f1a54b70e65b7cc7a128c",
    CUMULATIVE177: "d91c7d7f215f9e4a086aaa806958d1f8782686f0e0f71f2fa0df6a6c025f9422",
    TAXONOMY: "93908ec8e4721f0039acc779fb948988b6c25e712c29890bd98aa7c21a8422a0",
}

FINDING_FIELDS = (
    "batch_rank", "program_id", "cell_identity_sha256", "reaudit_status",
    "v1_v2_change_status", "primary_status", "secondary_status", "confidence_status",
    "outcome_status", "healer_status", "mechanism_status", "failure_chain_status",
    "unresolved_evidence_status", "citation_status", "field_differences_json", "reaudit_reason",
)
DIFF_FIELDS = (
    "batch_rank", "program_id", "cell_identity_sha256", "field_name",
    "v1_value", "v2_value", "audit_approved", "reaudit_status", "evidence",
)
APPROVAL_FIELDS = (
    "check_id", "expected", "observed", "reaudit_status", "evidence",
)
MECHANISM_FIELDS = (
    "mechanism_tag", "rebuilt_count", "v2_ledger_count", "summary_count",
    "reaudit_status", "ranks_json",
)
CHAIN_FIELDS = (
    "batch_rank", "program_id", "stage_count", "sequence_status", "evidence_status",
    "rank11_infrastructure_status", "reaudit_status",
)
UNRESOLVED_FIELDS = (
    "batch_rank", "program_id", "reason_status", "gap_status", "diagnostic_status",
    "plus_inference_status", "citation_status", "reaudit_status",
)
MATERIAL_FIELDS = (
    "finding_id", "batch_rank", "program_id", "field_name", "observed", "expected", "evidence", "impact",
)


class ReauditError(RuntimeError):
    pass


def _require(value: bool, message: str) -> None:
    if not value:
        raise ReauditError(message)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _path(repo: Path, value: Path) -> Path:
    return value if value.is_absolute() else repo / value


def _read_csv_with_fields(repo: Path, value: Path) -> tuple[list[str], list[dict[str, str]]]:
    with _path(repo, value).open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def _read_csv(repo: Path, value: Path) -> list[dict[str, str]]:
    return _read_csv_with_fields(repo, value)[1]


def _read_jsonl(repo: Path, value: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in _path(repo, value).read_text(encoding="utf-8").splitlines() if line]


def _csv_bytes(fields: tuple[str, ...], rows: list[dict[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows({field: row.get(field, "") for field in fields} for row in rows)
    return stream.getvalue().encode("utf-8")


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def verify_sources(repo: Path = REPO_ROOT) -> None:
    for relative, digest in SOURCE_HASHES.items():
        path = _path(repo, relative)
        _require(path.is_file(), f"missing upstream: {relative.as_posix()}")
        _require(_sha(path.read_bytes()) == digest, f"upstream byte drift: {relative.as_posix()}")


def build_analysis(repo: Path = REPO_ROOT) -> dict[str, Any]:
    verify_sources(repo)
    fields1, v1 = _read_csv_with_fields(repo, V1)
    fields2, v2 = _read_csv_with_fields(repo, V2)
    roster = _read_csv(repo, ROSTER)
    audit_diffs = _read_csv(repo, AUDIT_DIFFERENCES)
    v2_approval = _read_csv(repo, V2_DIFFERENCES)
    v2_mechanism_rows = _read_csv(repo, V2_MECHANISMS)
    v2_summary = json.loads(_path(repo, V2_SUMMARY).read_text(encoding="utf-8"))
    accounts = {row["program_id"]: row for row in _read_jsonl(repo, ACCOUNTS) if row.get("healer_account") == "H0"}
    task_ids = {row["task_id"] for row in _read_jsonl(repo, TASKS)}
    eval_ids = {row["program_id"] for row in _read_csv(repo, EVALPLUS) if row["healer_account"] == "H0"}
    prep_ids = {row["program_id"] for row in _read_csv(repo, PREPARATION)}
    frozen = {(row["program_id"], row["cell_identity_sha256"]) for row in _read_csv(repo, CUMULATIVE177)}
    _require(fields1 == fields2 and len(v1) == len(v2) == len(roster) == 21, "v1/v2 schema or count drift")
    _require([row["program_id"] for row in v1] == [row["program_id"] for row in v2] == [row["program_id"] for row in roster], "identity/order drift")
    _require(len(audit_diffs) == len(v2_approval) == 1, "approval ledger count drift")

    raw_differences: list[tuple[int, str, str, str]] = []
    for rank, (before, after) in enumerate(zip(v1, v2), 1):
        for field in fields1:
            if before[field] != after[field]:
                raw_differences.append((rank, field, before[field], after[field]))
    _require(len(raw_differences) == 1, f"v1-v2 difference count drift: {len(raw_differences)}")
    rank, field, old_value, new_value = raw_differences[0]
    _require((rank, field) == (17, "mechanism_tags_json"), "unauthorized v1-v2 difference")
    old_tags = {tag["tag"] for tag in json.loads(old_value)}
    new_tags = {tag["tag"] for tag in json.loads(new_value)}
    _require(old_tags - new_tags == {"algorithm_reconstruction_required"}, "removed tag drift")
    _require(new_tags == {"end_index_off_by_one", "wrong_boundary_condition"}, "retained rank17 tags drift")
    audit_row = audit_diffs[0]
    approval_row = v2_approval[0]
    _require(audit_row["batch_rank"] == approval_row["batch_rank"] == TARGET_RANK, "approval rank drift")
    _require(audit_row["program_id"] == approval_row["program_id"] == TARGET_PROGRAM, "approval program drift")
    _require(audit_row["field_name"] == approval_row["field_name"] == "mechanism_tags_json", "approval field drift")

    findings: list[dict[str, str]] = []
    chain_findings: list[dict[str, str]] = []
    unresolved_findings: list[dict[str, str]] = []
    rebuilt_mechanisms: list[dict[str, Any]] = []
    for rank, (before, after) in enumerate(zip(v1, v2), 1):
        program_id = after["program_id"]
        source = accounts[program_id]["evaluation_source"]
        _require(isinstance(source, str) and source and _sha(source.encode("utf-8")) == after["source_sha256"], f"source closure rank {rank}")
        _require(after["task_id"] in task_ids and program_id in eval_ids and program_id in prep_ids, f"evidence source missing rank {rank}")
        citations = after["evidence_citations"].split(";")
        citation_ok = len(citations) >= 6 and all(item for item in citations)
        chain = json.loads(after["failure_chain"])
        chain_evidence_ok = all(node.get("evidence") for node in chain)
        if after["primary_layer"] == "UNRESOLVED":
            chain_sequence_ok = len(chain) == 3 and chain[-1]["layer"] == "UNRESOLVED" and chain[-1]["mechanism"] == "insufficient_static_evidence"
        else:
            chain_sequence_ok = chain[-1]["layer"] == "L5" and chain[-1]["gate"] == "G4"
        rank11_status = "NOT_APPLICABLE"
        if rank == 11:
            infra = [node for node in chain if node.get("mechanism") == "diagnostic_infrastructure_failure"]
            rank11_status = "PRESENT_SCOPED_L5_PRESERVED" if len(infra) == 1 and after["primary_layer"] == "L5" and after["outcome_validity"] == "VALID_MODEL_OUTCOME" else "MISMATCH"
            chain_sequence_ok = chain_sequence_ok and rank11_status.startswith("PRESENT")
        chain_ok = chain_sequence_ok and chain_evidence_ok
        chain_findings.append({
            "batch_rank": str(rank), "program_id": program_id, "stage_count": str(len(chain)),
            "sequence_status": "MATCH" if chain_sequence_ok else "MISMATCH",
            "evidence_status": "COMPLETE" if chain_evidence_ok else "INCOMPLETE",
            "rank11_infrastructure_status": rank11_status,
            "reaudit_status": "AFFIRMED" if chain_ok else "MATERIAL",
        })
        if after["primary_layer"] == "UNRESOLVED":
            tags = {tag["tag"] for tag in json.loads(after["mechanism_tags_json"])}
            reason_ok = bool(after["reason"] and after["unresolved_reason_code"])
            gap_ok = bool(after["evidence_missing"] and after["competing_explanations"])
            diagnostic_ok = bool(after["minimal_future_diagnostic"])
            no_inference = {"public_examples_non_discriminating", "plus_failure_not_localized", "diagnostic_execution_required"} <= tags
            unresolved_findings.append({
                "batch_rank": str(rank), "program_id": program_id,
                "reason_status": "COMPLETE" if reason_ok else "MISSING",
                "gap_status": "COMPLETE" if gap_ok else "MISSING",
                "diagnostic_status": "SPECIFIC_NOT_EXECUTED" if diagnostic_ok else "MISSING",
                "plus_inference_status": "NO_UNSUPPORTED_INFERENCE" if no_inference else "MISMATCH",
                "citation_status": "COMPLETE" if citation_ok else "MISSING",
                "reaudit_status": "AFFIRMED" if reason_ok and gap_ok and diagnostic_ok and no_inference and citation_ok else "MATERIAL",
            })
        tags = json.loads(after["mechanism_tags_json"])
        for tag in tags:
            rebuilt_mechanisms.append({"rank": rank, **tag})

        if rank == 17:
            nonmechanism_ok = all(before[name] == after[name] for name in fields1 if name != "mechanism_tags_json")
            change_status = "APPROVED_SINGLE_MECHANISM_CHANGE" if nonmechanism_ok else "MISMATCH"
            field_diffs = ["mechanism_tags_json"]
        else:
            nonmechanism_ok = before == after
            change_status = "UNCHANGED_ALL_FIELDS" if nonmechanism_ok else "MISMATCH"
            field_diffs = []
        core_ok = (
            after["primary_layer"] in {"L5", "UNRESOLVED"}
            and after["secondary_layer"] == ""
            and after["confidence"] == ("HIGH" if after["primary_layer"] == "L5" else "LOW")
            and after["outcome_validity"] == "VALID_MODEL_OUTCOME"
            and after["healer_eligibility"] == "abstain"
            and chain_ok and citation_ok and nonmechanism_ok
        )
        findings.append({
            "batch_rank": str(rank), "program_id": program_id,
            "cell_identity_sha256": after["cell_identity_sha256"],
            "reaudit_status": "AFFIRMED" if core_ok else "MATERIAL",
            "v1_v2_change_status": change_status,
            "primary_status": "AFFIRMED", "secondary_status": "AFFIRMED",
            "confidence_status": "AFFIRMED", "outcome_status": "AFFIRMED",
            "healer_status": "AFFIRMED", "mechanism_status": "AFFIRMED",
            "failure_chain_status": "AFFIRMED" if chain_ok else "MATERIAL",
            "unresolved_evidence_status": "AFFIRMED" if after["primary_layer"] == "UNRESOLVED" else "NOT_APPLICABLE",
            "citation_status": "AFFIRMED" if citation_ok else "MATERIAL",
            "field_differences_json": json.dumps(field_diffs, separators=(",", ":")),
            "reaudit_reason": "approved rank17 mechanism correction fully applied" if rank == 17 else "all fields byte-equivalent to v1",
        })

    _require(all(row["reaudit_status"] == "AFFIRMED" for row in findings), "per-cell reaudit finding drift")
    _require(all(row["reaudit_status"] == "AFFIRMED" for row in chain_findings), "failure-chain finding drift")
    _require(len(unresolved_findings) == 11 and all(row["reaudit_status"] == "AFFIRMED" for row in unresolved_findings), "UNRESOLVED finding drift")
    rebuilt_counts = Counter(row["tag"] for row in rebuilt_mechanisms)
    ledger_counts = Counter(row["mechanism_tag"] for row in v2_mechanism_rows)
    summary_counts = Counter(v2_summary["mechanism_distribution"])
    _require(rebuilt_counts == ledger_counts == summary_counts, "mechanism derived artifact drift")
    _require(rebuilt_counts["algorithm_reconstruction_required"] == 9, "algorithm reconstruction count drift")
    mechanism_findings = []
    for tag in sorted(rebuilt_counts):
        ranks = [row["rank"] for row in rebuilt_mechanisms if row["tag"] == tag]
        mechanism_findings.append({
            "mechanism_tag": tag, "rebuilt_count": str(rebuilt_counts[tag]),
            "v2_ledger_count": str(ledger_counts[tag]), "summary_count": str(summary_counts[tag]),
            "reaudit_status": "AFFIRMED", "ranks_json": json.dumps(ranks, separators=(",", ":")),
        })

    primary = Counter(row["primary_layer"] for row in v2)
    secondary = Counter(row["secondary_layer"] or "empty" for row in v2)
    confidence = Counter(row["confidence"] for row in v2)
    outcome = Counter(row["outcome_validity"] for row in v2)
    healer = Counter(row["healer_eligibility"] for row in v2)
    _require(primary == {"L5": 10, "UNRESOLVED": 11}, "primary stats drift")
    _require(secondary == {"empty": 21} and confidence == {"HIGH": 10, "LOW": 11}, "secondary/confidence stats drift")
    _require(outcome == {"VALID_MODEL_OUTCOME": 21} and healer == {"abstain": 21}, "outcome/healer stats drift")
    program_ids = {row["program_id"] for row in v2}
    cell_ids = {row["cell_identity_sha256"] for row in v2}
    source_ids = {row["source_sha256"] for row in v2}
    _require(len(program_ids) == len(cell_ids) == 21 and len(source_ids) == 20, "identity/source uniqueness drift")
    _require(all((row["program_id"], row["cell_identity_sha256"]) not in frozen for row in v2), "frozen177 overlap")

    difference_verification = [{
        "batch_rank": "17", "program_id": TARGET_PROGRAM,
        "cell_identity_sha256": v2[16]["cell_identity_sha256"], "field_name": "mechanism_tags_json",
        "v1_value": old_value, "v2_value": new_value, "audit_approved": "true",
        "reaudit_status": "AFFIRMED",
        "evidence": "exactly algorithm_reconstruction_required removed; end_index_off_by_one and wrong_boundary_condition retained",
    }]
    approval_checks = [
        {"check_id": "changed_record_count", "expected": "1", "observed": "1", "reaudit_status": "AFFIRMED", "evidence": "full v1-v2 field diff"},
        {"check_id": "changed_field_count", "expected": "1", "observed": "1", "reaudit_status": "AFFIRMED", "evidence": "mechanism_tags_json only"},
        {"check_id": "changed_rank", "expected": "17", "observed": "17", "reaudit_status": "AFFIRMED", "evidence": AUDIT_DIFFERENCES.as_posix()},
        {"check_id": "unauthorized_differences", "expected": "0", "observed": "0", "reaudit_status": "AFFIRMED", "evidence": "20 rows all-field equal; rank17 all nonmechanism fields equal"},
        {"check_id": "removed_tag", "expected": "algorithm_reconstruction_required", "observed": "algorithm_reconstruction_required", "reaudit_status": "AFFIRMED", "evidence": "set difference of parsed mechanism tags"},
    ]
    summary = {
        "revision": OUTPUT_RELATIVE.name, "status": STATUS, "verdict": VERDICT,
        "cells": 21, "affirmed": 21, "non_material": 0, "material": 0,
        "v1_to_v2_changed_records": 1, "v1_to_v2_changed_fields": 1,
        "approved_changes_affirmed": 1, "unauthorized_differences": 0,
        "rank17_nonmechanism_fields_unchanged": True, "unchanged_records": 20,
        "primary_distribution": dict(sorted(primary.items())),
        "secondary_distribution": dict(sorted(secondary.items())),
        "confidence_distribution": dict(sorted(confidence.items())),
        "outcome_validity_distribution": dict(sorted(outcome.items())),
        "healer_distribution": {"eligible": 0, "conditional": 0, "abstain": 21},
        "mechanism_distribution": dict(sorted(rebuilt_counts.items())),
        "algorithm_reconstruction_required": 9,
        "failure_chains_affirmed": 21, "unresolved_evidence_affirmed": 11,
        "unique_program_id": 21, "unique_cell_identity": 21, "unique_source_sha256": 20,
        "legal_shared_source_ranks": [5, 21], "overlap_with_frozen177": 0,
        "set_closure": "198=177+21", "unadjudicated_remaining": 0,
        "v1_modified": False, "first_audit_modified": False, "v2_modified": False,
        "v3_created": False, "frozen": False,
    }
    return {
        "findings": findings, "difference_verification": difference_verification,
        "approval_checks": approval_checks, "mechanism_findings": mechanism_findings,
        "chain_findings": chain_findings, "unresolved_findings": unresolved_findings,
        "material": [], "non_material": [], "summary": summary,
    }


def _report(findings_sha: str) -> str:
    return (
        "# Final Batch05 provisional v2：獨立 re-audit\n\n"
        f"**狀態：`{STATUS}`**\n\n**Findings SHA-256：`{findings_sha}`**\n\n"
        "- 21格：AFFIRMED=21、NON_MATERIAL=0、MATERIAL=0。\n"
        "- v1→v2恰有rank 17 mechanism_tags_json一項核准差異；未核准差異=0。\n"
        "- rank 17僅移除algorithm_reconstruction_required；保留兩個off-by-one/boundary tags及全部非mechanism欄位。\n"
        "- 其餘20格逐欄與v1等值。\n"
        "- L5=10、UNRESOLVED=11；HIGH=10、LOW=11；VALID_MODEL_OUTCOME=21；abstain=21。\n"
        "- algorithm_reconstruction_required=9；完整mechanism分布由records重建並與ledger/summary一致。\n"
        "- failure chain 21/21、UNRESOLVED evidence 11/11、citations 21/21均AFFIRMED。\n"
        "- 所有執行計數為0；未建立v3、未freeze。\n"
    )


def build_outputs(repo: Path = REPO_ROOT) -> dict[str, bytes]:
    analysis = build_analysis(repo)
    findings_bytes = _csv_bytes(FINDING_FIELDS, analysis["findings"])
    execution = {
        "model_calls": 0, "candidate_executions": 0, "candidate_imports": 0,
        "candidate_test_executions": 0, "public_test_executions": 0,
        "hidden_test_executions": 0, "evalplus_correctness_executions": 0,
        "diagnostics_executions": 0, "validation_executions": 0,
        "healer_executions": 0, "programs_executed": 0,
    }
    outputs = {
        "per_cell_v2_reaudit_findings.csv": findings_bytes,
        "field_level_difference_verification.csv": _csv_bytes(DIFF_FIELDS, analysis["difference_verification"]),
        "approved_change_verification.csv": _csv_bytes(APPROVAL_FIELDS, analysis["approval_checks"]),
        "mechanism_rebuild.csv": _csv_bytes(MECHANISM_FIELDS, analysis["mechanism_findings"]),
        "failure_chain_reaudit.csv": _csv_bytes(CHAIN_FIELDS, analysis["chain_findings"]),
        "unresolved_reaudit.csv": _csv_bytes(UNRESOLVED_FIELDS, analysis["unresolved_findings"]),
        "material_findings.csv": _csv_bytes(MATERIAL_FIELDS, analysis["material"]),
        "non_material_findings.csv": _csv_bytes(MATERIAL_FIELDS, analysis["non_material"]),
        "reaudit_summary.json": _json_bytes(analysis["summary"]),
        "execution_counts.json": _json_bytes(execution),
        "report_zh.md": _report(_sha(findings_bytes)).encode("utf-8"),
    }
    outputs["provenance.json"] = _json_bytes({
        **analysis["summary"], **execution, "start_head": START_HEAD,
        "source_hashes": {path.as_posix(): digest for path, digest in SOURCE_HASHES.items()},
        "independent_method": "full v1-v2 field diff plus records-derived mechanism/statistics and preserved evidence-chain checks; no import of v2 builder",
        "candidate_code_imported_or_executed": False, "v2_modified": False,
    })
    outputs["manifest.json"] = _json_bytes({
        "revision": OUTPUT_RELATIVE.as_posix(), "status": STATUS, "verdict": VERDICT,
        "start_head": START_HEAD, "findings_sha256": _sha(findings_bytes),
        "v1_records_sha256": SOURCE_HASHES[V1], "first_audit_findings_sha256": SOURCE_HASHES[AUDIT_FINDINGS],
        "first_audit_manifest_sha256": SOURCE_HASHES[AUDIT_MANIFEST],
        "v2_records_sha256": SOURCE_HASHES[V2], "v2_manifest_sha256": SOURCE_HASHES[V2_MANIFEST],
        "taxonomy_sha256": SOURCE_HASHES[TAXONOMY], "affirmed": 21,
        "non_material": 0, "material": 0, "unauthorized_differences": 0,
        "outputs_sha256_excluding_manifest": {name: _sha(data) for name, data in outputs.items()},
        **execution,
    })
    return outputs


def write_outputs(repo: Path = REPO_ROOT) -> Path:
    output = repo / OUTPUT_RELATIVE
    output.mkdir(parents=True, exist_ok=True)
    for name, data in build_outputs(repo).items():
        (output / name).write_bytes(data)
    return output


def main() -> None:
    output = write_outputs()
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    print(f"wrote {output}")
    print(f"findings_sha256={manifest['findings_sha256']}")
    print(f"manifest_sha256={_sha((output / 'manifest.json').read_bytes())}")
    print(f"verdict={manifest['verdict']}")


if __name__ == "__main__":
    main()
