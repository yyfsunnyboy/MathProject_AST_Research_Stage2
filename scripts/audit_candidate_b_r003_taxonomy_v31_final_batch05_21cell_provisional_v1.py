#!/usr/bin/env python3
"""Independent static audit of Final Batch05 provisional adjudication v1."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_RELATIVE = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_final_batch05_21cell_provisional_v1_independent_audit_v1")
START_HEAD = "1aa7b692c4d499ada2e0b6e0799b3475f2f68b18"
STATUS = "INDEPENDENT_STATIC_AUDIT_COMPLETE_ONE_MATERIAL_MECHANISM_FINDING"
VERDICT = "FINAL_BATCH05_PROVISIONAL_V2_REVISION_REQUIRED"

ROSTER = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_final_batch05_21cell_roster_v1/batch05_roster.csv")
ROSTER_AUDIT = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_final_batch05_21cell_roster_v1_independent_audit_v1/per_cell_roster_findings.csv")
PROVISIONAL = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_final_batch05_21cell_provisional_v1/adjudication_records.csv")
PROVISIONAL_DIR = PROVISIONAL.parent
PROVISIONAL_MANIFEST = PROVISIONAL_DIR / "manifest.json"
PROVISIONAL_MECHANISMS = PROVISIONAL_DIR / "mechanism_ledger.csv"
PROVISIONAL_CHAINS = PROVISIONAL_DIR / "failure_chain_ledger.csv"
PROVISIONAL_SUMMARY = PROVISIONAL_DIR / "adjudication_summary.json"
PROVISIONAL_GAPS = PROVISIONAL_DIR / "unresolved_evidence_gaps.csv"
PROVISIONAL_EXECUTION = PROVISIONAL_DIR / "execution_counts.json"
PROVISIONAL_PROVENANCE = PROVISIONAL_DIR / "provenance.json"
PROVISIONAL_REPORT = PROVISIONAL_DIR / "report_zh.md"
PROVISIONAL_BUILDER = Path("scripts/adjudicate_candidate_b_r003_taxonomy_v31_final_batch05_21cell_provisional_v1.py")
PROVISIONAL_TEST = Path("tests/finals_rebuild/test_candidate_b_r003_taxonomy_v31_final_batch05_21cell_provisional_v1.py")
ACCOUNTS = Path("artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/mbpp_q35_9b_candidate_b_development60_replay_r003/h0_h1_accounts.jsonl")
TASKS = Path("data/mbpp_plus/tasks.jsonl")
EVALPLUS = Path("artifacts/public_benchmark_governance/candidate_b_r003_h0_h1_evalplus_v1/manual_evalplus_run_001/evalplus_results.csv")
PREPARATION = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v3_formal_classification_preparation_v1/classification_preparation.csv")
CUMULATIVE177 = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_frozen_progress_census_v4/cumulative_frozen_identity_ledger.csv")
TAXONOMY = Path("C:/Users/yehya/Downloads/AI_生成程式共同失敗分類標準_實際使用版_v3.1.md")

SOURCE_HASHES = {
    ROSTER: "4ec24e450a66c50db46230a5b950137af6e6a4cb3d9a067f182a545818851764",
    ROSTER_AUDIT: "d834c492a4c61bc22048356de6d17c1da2c766f57d948f3df713570251761f34",
    PROVISIONAL: "ab6b389c1c9d04d72e6bed6a415b422eb222f9b4a8a1cec238ba2af6c34c291c",
    PROVISIONAL_MANIFEST: "b28a96c894f838ace38a673d1a4c6f9d63a12336661804981ca55ff73cc8c68c",
    PROVISIONAL_MECHANISMS: "4db008589a4701be8bc06f267ebe10d64b89e1cf1dc978575a37a4a00cdd7f91",
    PROVISIONAL_CHAINS: "d397088f5c067a4cefad360dc5ea4cb34a66c0fee227cc90961ba635007dd025",
    PROVISIONAL_SUMMARY: "d0d6c9f539014387c9c63e9bc06a909c97f2a2cfcdfe7db73e70aa376eed751f",
    PROVISIONAL_GAPS: "72866c3b068c76576c3744b06bdf61d7d8b87d28af1ac0285ebfbd9e6df44ee7",
    PROVISIONAL_EXECUTION: "a2689e5b6dca7db3a16ca8460cda80476eea60a6907dda92bee875e294f3d4a7",
    PROVISIONAL_PROVENANCE: "c5c32c7f594795857d577834f1f34dfa5426aa51a56b78b12372711c8192a67f",
    PROVISIONAL_REPORT: "a433acebb5c37ae068ec6c163835774016894277e8daa2183d8ba62bb8927535",
    PROVISIONAL_BUILDER: "a6833de75be3cc220f59494de42936c6ce4c90a6a4e993d1929b8322b405dd35",
    PROVISIONAL_TEST: "e99ae67a9ffeea44d1340c5baf2e953614a6f874bab89fb7106c0e054449bbd7",
    ACCOUNTS: "b1313615bf41840bc1c45c36d2b8ac9b544f37fb5bb801c104aad1657ca2c2ec",
    TASKS: "b816022b8b587047cb1d275417a96acb009de328684e5914e7ac010c9d8c6f3c",
    EVALPLUS: "338e66ecd09f48bcf2b8c8d1c8cf75911755dad92743c99257698d994a01938e",
    PREPARATION: "5b0106b93f2d192d89c740659f83021956c15113397f1a54b70e65b7cc7a128c",
    CUMULATIVE177: "d91c7d7f215f9e4a086aaa806958d1f8782686f0e0f71f2fa0df6a6c025f9422",
    TAXONOMY: "93908ec8e4721f0039acc779fb948988b6c25e712c29890bd98aa7c21a8422a0",
}

FINDING_FIELDS = (
    "batch_rank", "program_id", "cell_identity_sha256", "audit_status",
    "independent_primary", "provisional_primary", "primary_status",
    "secondary_status", "confidence_status", "outcome_status", "healer_status",
    "mechanism_status", "failure_chain_status", "citation_status",
    "field_differences_json", "independent_evidence", "audit_reason",
)
DIFFERENCE_FIELDS = (
    "batch_rank", "program_id", "cell_identity_sha256", "field_name",
    "difference_status", "provisional_value", "recommended_value",
    "evidence", "impact",
)
MATERIAL_FIELDS = (
    "finding_id", "batch_rank", "program_id", "field_name", "provisional_value",
    "recommended_value", "evidence", "taxonomy_basis", "impact",
)
MECHANISM_AUDIT_FIELDS = (
    "mechanism_tag", "provisional_count", "independent_supported_count",
    "audit_status", "affected_ranks_json", "evidence",
)
HEALER_FIELDS = (
    "batch_rank", "program_id", "provisional_disposition", "independent_disposition",
    "audit_status", "safety_reason",
)
CHAIN_AUDIT_FIELDS = (
    "batch_rank", "program_id", "stage_count", "sequence_status",
    "evidence_status", "rank11_diagnostic_node_status", "audit_status", "note",
)
UNRESOLVED_FIELDS = (
    "batch_rank", "program_id", "audit_status", "public_example_status",
    "plus_localization_status", "gap_status", "minimal_diagnostic_status", "audit_reason",
)


class AuditError(RuntimeError):
    pass


def _require(value: bool, message: str) -> None:
    if not value:
        raise AuditError(message)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _path(repo: Path, value: Path) -> Path:
    return value if value.is_absolute() else repo / value


def _read_csv(repo: Path, value: Path) -> list[dict[str, str]]:
    with _path(repo, value).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


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


PRIMARY = {
    1: "UNRESOLVED", 2: "UNRESOLVED", 3: "UNRESOLVED", 4: "UNRESOLVED", 5: "UNRESOLVED",
    6: "L5", 7: "UNRESOLVED", 8: "L5", 9: "UNRESOLVED", 10: "L5", 11: "L5",
    12: "L5", 13: "L5", 14: "UNRESOLVED", 15: "UNRESOLVED", 16: "L5", 17: "L5",
    18: "L5", 19: "L5", 20: "UNRESOLVED", 21: "UNRESOLVED",
}

EVIDENCE = {
    1: "positive repeated-division conversion satisfies 8; signed representation is not publicly closed",
    2: "outer len satisfies the all-sublists example; heterogeneous-member semantics are not closed",
    3: "public 123.11 does not distinguish exact/two-or-fewer decimal grammar",
    4: "sorted divisibility DP satisfies public chain; zero/duplicate/signed failing boundary is absent",
    5: "component reversal satisfies the well-formed public date; validation/normalization boundary is absent",
    6: "stable dedupe retains repeated 2 and 3, directly contradicting public [1,4,5]",
    7: "modulo satisfies positive 123; signed last-digit convention is absent",
    8: "static trace for public n=5 reaches False, directly contradicting True",
    9: "outer len satisfies the all-sublists example; heterogeneous-member semantics are not closed",
    10: "raw Counter does not merge reversed tuples required by the public output",
    11: "public array advances left past the final unique value and returns None; diagnostic WorkerProcessExit is separate",
    12: "source returns [10,15,20,30], directly contradicting public [10,20,30,15]",
    13: "str.islower accepts lowercase-plus-digit components contrary to lowercase-letters-only grammar",
    14: "balanced-bracket stack satisfies public example; non-bracket expression grammar is absent",
    15: "balanced-bracket stack satisfies public example; non-bracket expression grammar is absent",
    16: "required callable returns boolean True for 7, directly contradicting required nth value 11",
    17: "match.end()-1 returns 6 for clearly, directly contradicting public end position 7",
    18: "DP counts [2,6,3] as 3 although 2 and 3 are incomparable",
    19: "float .abs raises inside public path and broad except returns False instead of True",
    20: "k=len(nums) satisfies public 47; meaning of k when smaller is absent",
    21: "component reversal satisfies the well-formed public date; validation/normalization boundary is absent",
}

REQUIRED_TAGS = {
    6: {"dedupe_instead_of_unique_occurrence", "semantic_goal_drift"},
    8: {"difference_of_squares_condition_error", "algorithmic_error"},
    10: {"tuple_pair_normalization_omitted", "semantic_goal_drift"},
    11: {"binary_search_pair_alignment_error", "algorithmic_error", "diagnostic_infrastructure_failure"},
    12: {"incorrect_ordering_semantics", "embedded_assert_contract_drift"},
    13: {"lowercase_letter_class_underconstrained", "edge_case_omission"},
    16: {"predicate_instead_of_nth_value", "semantic_goal_drift"},
    17: {"end_index_off_by_one", "wrong_boundary_condition"},
    18: {"pairwise_divisibility_nontransitive_dp", "algorithmic_error"},
    19: {"exception_swallowed_to_wrong_answer", "decimal_validation_expression_error", "algorithmic_error"},
}


def build_analysis(repo: Path = REPO_ROOT) -> dict[str, Any]:
    verify_sources(repo)
    roster = _read_csv(repo, ROSTER)
    records = _read_csv(repo, PROVISIONAL)
    roster_audit = _read_csv(repo, ROSTER_AUDIT)
    accounts = {row["program_id"]: row for row in _read_jsonl(repo, ACCOUNTS) if row.get("healer_account") == "H0"}
    tasks = {row["task_id"]: row for row in _read_jsonl(repo, TASKS)}
    eval_rows = {row["program_id"]: row for row in _read_csv(repo, EVALPLUS) if row["healer_account"] == "H0"}
    prep = {row["program_id"]: row for row in _read_csv(repo, PREPARATION)}
    frozen = {(row["program_id"], row["cell_identity_sha256"]) for row in _read_csv(repo, CUMULATIVE177)}
    _require(len(roster) == len(records) == len(roster_audit) == 21, "21-cell input closure drift")
    _require(all(row["audit_status"] == "AFFIRMED" for row in roster_audit), "roster audit drift")
    _require([row["program_id"] for row in roster] == [row["program_id"] for row in records], "record order drift")

    findings: list[dict[str, str]] = []
    differences: list[dict[str, str]] = []
    material: list[dict[str, str]] = []
    healer_audit: list[dict[str, str]] = []
    chain_audit: list[dict[str, str]] = []
    unresolved_audit: list[dict[str, str]] = []
    supported_tag_counts: Counter[str] = Counter()
    source_ids: set[str] = set()

    for rank, (roster_row, record) in enumerate(zip(roster, records), 1):
        program_id = record["program_id"]
        source = accounts[program_id]["evaluation_source"]
        _require(isinstance(source, str) and source, f"empty source rank {rank}")
        _require(_sha(source.encode("utf-8")) == record["source_sha256"], f"source SHA drift rank {rank}")
        _require(tasks[record["task_id"]]["prompt"].strip(), f"empty public spec rank {rank}")
        _require(eval_rows[program_id]["plus_status"] == "fail", f"saved result drift rank {rank}")
        _require((program_id, record["cell_identity_sha256"]) not in frozen, f"frozen overlap rank {rank}")
        source_ids.add(record["source_sha256"])

        expected_primary = PRIMARY[rank]
        primary_ok = record["primary_layer"] == expected_primary
        secondary_ok = record["secondary_layer"] == ""
        confidence_ok = record["confidence"] == ("HIGH" if expected_primary == "L5" else "LOW")
        outcome_ok = record["outcome_validity"] == "VALID_MODEL_OUTCOME"
        healer_ok = record["healer_eligibility"] == "abstain"
        tags = json.loads(record["mechanism_tags_json"])
        tag_names = {tag["tag"] for tag in tags}
        mechanism_ok = True
        field_diffs: list[str] = []

        if expected_primary == "UNRESOLVED":
            expected_unresolved = {"public_examples_non_discriminating", "plus_failure_not_localized", "diagnostic_execution_required"}
            mechanism_ok = expected_unresolved <= tag_names
            _require(record["evidence_missing"] and record["minimal_future_diagnostic"], f"unresolved gap incomplete rank {rank}")
            unresolved_audit.append({
                "batch_rank": str(rank), "program_id": program_id, "audit_status": "AFFIRMED",
                "public_example_status": "STATICALLY_SATISFIED_NON_DISCRIMINATING",
                "plus_localization_status": "NOT_LOCALIZED_NO_ROOT_CAUSE_INFERENCE",
                "gap_status": "COMPLETE", "minimal_diagnostic_status": "SPECIFIC_NOT_EXECUTED",
                "audit_reason": EVIDENCE[rank],
            })
        else:
            mechanism_ok = REQUIRED_TAGS[rank] <= tag_names

        if rank == 17 and "algorithm_reconstruction_required" in tag_names:
            mechanism_ok = False
            field_diffs.append("mechanism_tags_json")
            recommended_tags = [tag for tag in tags if tag["tag"] != "algorithm_reconstruction_required"]
            diff = {
                "batch_rank": "17", "program_id": program_id,
                "cell_identity_sha256": record["cell_identity_sha256"],
                "field_name": "mechanism_tags_json", "difference_status": "MATERIAL",
                "provisional_value": record["mechanism_tags_json"],
                "recommended_value": json.dumps(recommended_tags, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
                "evidence": "source returns match.end()-1; removing -1 is a local off-by-one correction and does not reconstruct the regex/search algorithm",
                "impact": "remove unsupported algorithm_reconstruction_required tag at rank 17; batch mechanism count changes 10->9; primary/confidence/outcome/Healer unchanged",
            }
            differences.append(diff)
            material.append({
                "finding_id": "MATERIAL-R17-MECHANISM-001", "batch_rank": "17", "program_id": program_id,
                "field_name": "mechanism_tags_json",
                "provisional_value": "algorithm_reconstruction_required=SUPPORTED",
                "recommended_value": "remove algorithm_reconstruction_required; retain end_index_off_by_one and wrong_boundary_condition",
                "evidence": diff["evidence"],
                "taxonomy_basis": "v3.1 sections 8 and 11 require mechanism claims to be evidence-supported and separate Healer safety from failure mechanism",
                "impact": diff["impact"],
            })

        for tag in tags:
            if not (rank == 17 and tag["tag"] == "algorithm_reconstruction_required"):
                supported_tag_counts[tag["tag"]] += 1

        chain = json.loads(record["failure_chain"])
        chain_evidence_ok = all(node.get("evidence") for node in chain)
        if expected_primary == "UNRESOLVED":
            sequence_ok = len(chain) == 3 and chain[-1]["layer"] == "UNRESOLVED" and chain[-1]["mechanism"] == "insufficient_static_evidence"
        else:
            sequence_ok = chain[-1]["layer"] == "L5" and chain[-1]["gate"] == "G4"
        rank11_status = "NOT_APPLICABLE"
        if rank == 11:
            infra = [node for node in chain if node.get("mechanism") == "diagnostic_infrastructure_failure"]
            rank11_status = "PRESENT_SCOPED_DOES_NOT_DISPLACE_L5" if len(infra) == 1 and record["primary_layer"] == "L5" and record["outcome_validity"] == "VALID_MODEL_OUTCOME" else "MISMATCH"
            sequence_ok = sequence_ok and rank11_status.startswith("PRESENT") and prep[program_id]["diagnostic_phase"] == "infrastructure"
        chain_status = "AFFIRMED" if sequence_ok and chain_evidence_ok else "MATERIAL"
        chain_audit.append({
            "batch_rank": str(rank), "program_id": program_id, "stage_count": str(len(chain)),
            "sequence_status": "CORRECT" if sequence_ok else "MISMATCH",
            "evidence_status": "COMPLETE" if chain_evidence_ok else "INCOMPLETE",
            "rank11_diagnostic_node_status": rank11_status, "audit_status": chain_status,
            "note": "logical Gate/evidence sequence retained; no post-hoc Plus root-cause inference",
        })
        _require(chain_status == "AFFIRMED", f"failure-chain audit failed rank {rank}")

        healer_audit.append({
            "batch_rank": str(rank), "program_id": program_id,
            "provisional_disposition": record["healer_eligibility"], "independent_disposition": "abstain",
            "audit_status": "AFFIRMED" if healer_ok else "MATERIAL",
            "safety_reason": (
                "root layer and unique safe repair are not closed"
                if expected_primary == "UNRESOLVED"
                else "semantic/algorithm repair lacks a frozen tested task-agnostic evaluator-blind rule"
            ),
        })

        core_ok = primary_ok and secondary_ok and confidence_ok and outcome_ok and healer_ok and chain_status == "AFFIRMED"
        audit_status = "MATERIAL" if field_diffs else ("AFFIRMED" if core_ok and mechanism_ok else "MATERIAL")
        if not primary_ok: field_diffs.append("primary_layer")
        if not secondary_ok: field_diffs.append("secondary_layer")
        if not confidence_ok: field_diffs.append("confidence")
        if not outcome_ok: field_diffs.append("outcome_validity")
        if not healer_ok: field_diffs.append("healer_eligibility")
        if not mechanism_ok and rank != 17: field_diffs.append("mechanism_tags_json")
        findings.append({
            "batch_rank": str(rank), "program_id": program_id,
            "cell_identity_sha256": record["cell_identity_sha256"], "audit_status": audit_status,
            "independent_primary": expected_primary, "provisional_primary": record["primary_layer"],
            "primary_status": "MATCH" if primary_ok else "MISMATCH",
            "secondary_status": "MATCH" if secondary_ok else "MISMATCH",
            "confidence_status": "MATCH" if confidence_ok else "MISMATCH",
            "outcome_status": "MATCH" if outcome_ok else "MISMATCH",
            "healer_status": "MATCH" if healer_ok else "MISMATCH",
            "mechanism_status": "MATCH" if mechanism_ok else "MATERIAL_DIFFERENCE",
            "failure_chain_status": chain_status, "citation_status": "COMPLETE" if record["evidence_citations"] else "MISSING",
            "field_differences_json": json.dumps(field_diffs, separators=(",", ":")),
            "independent_evidence": EVIDENCE[rank],
            "audit_reason": "independent static conclusion matches v1" if not field_diffs else "unsupported mechanism tag requires v2 revision",
        })

    _require(len({row["program_id"] for row in records}) == 21, "program uniqueness drift")
    _require(len({row["cell_identity_sha256"] for row in records}) == 21, "cell uniqueness drift")
    _require(len(source_ids) == 20, "source uniqueness drift")
    _require(len(material) == len(differences) == 1, "material finding count drift")
    status_counts = Counter(row["audit_status"] for row in findings)
    _require(status_counts == {"AFFIRMED": 20, "MATERIAL": 1}, "audit status count drift")

    provisional_mechanism_counts = Counter(row["mechanism_tag"] for row in _read_csv(repo, PROVISIONAL_MECHANISMS))
    mechanism_audit: list[dict[str, str]] = []
    focus = (
        "public_examples_non_discriminating", "plus_failure_not_localized", "diagnostic_execution_required",
        "algorithm_reconstruction_required", "algorithmic_error", "semantic_goal_drift",
    )
    expected_counts = {
        "public_examples_non_discriminating": 11, "plus_failure_not_localized": 11,
        "diagnostic_execution_required": 11, "algorithm_reconstruction_required": 9,
        "algorithmic_error": 4, "semantic_goal_drift": 3,
    }
    for tag in focus:
        affected = [int(row["batch_rank"]) for row in _read_csv(repo, PROVISIONAL_MECHANISMS) if row["mechanism_tag"] == tag]
        observed = provisional_mechanism_counts[tag]
        expected = expected_counts[tag]
        mechanism_audit.append({
            "mechanism_tag": tag, "provisional_count": str(observed),
            "independent_supported_count": str(expected),
            "audit_status": "AFFIRMED" if observed == expected else "MATERIAL",
            "affected_ranks_json": json.dumps(affected, separators=(",", ":")),
            "evidence": "rank 17 local off-by-one does not require algorithm reconstruction" if tag == "algorithm_reconstruction_required" else "independent per-cell static review supports all recorded instances",
        })

    summary = {
        "revision": OUTPUT_RELATIVE.name, "status": STATUS, "verdict": VERDICT,
        "cells": 21, "affirmed": 20, "non_material": 0, "material": 1,
        "material_ranks": [17], "field_level_differences": 1,
        "independent_primary_distribution": {"L5": 10, "UNRESOLVED": 11},
        "independent_secondary_distribution": {"empty": 21},
        "independent_confidence_distribution": {"HIGH": 10, "LOW": 11},
        "independent_outcome_distribution": {"VALID_MODEL_OUTCOME": 21},
        "independent_healer_distribution": {"abstain": 21},
        "unresolved_ranks": [1, 2, 3, 4, 5, 7, 9, 14, 15, 20, 21],
        "rank11_primary": "L5", "rank11_outcome": "VALID_MODEL_OUTCOME",
        "rank11_diagnostic_only_infrastructure_node": "AFFIRMED",
        "algorithm_reconstruction_required_provisional": 10,
        "algorithm_reconstruction_required_independently_supported": 9,
        "unique_program_id": 21, "unique_cell_identity": 21, "unique_source_sha256": 20,
        "legal_shared_source_ranks": [5, 21], "overlap_with_frozen177": 0,
        "set_closure": "198=177+21", "unadjudicated_remaining": 0,
        "v1_modified": False, "v2_created": False,
    }
    return {
        "findings": findings, "differences": differences, "material": material,
        "non_material": [], "mechanism_audit": mechanism_audit,
        "healer_audit": healer_audit, "chain_audit": chain_audit,
        "unresolved_audit": unresolved_audit, "summary": summary,
    }


def _report(summary: dict[str, Any], findings_sha: str) -> str:
    return (
        "# Final Batch05 provisional v1：獨立靜態 audit\n\n"
        f"**狀態：`{STATUS}`**\n\n**Findings SHA-256：`{findings_sha}`**\n\n"
        "- 21格：AFFIRMED=20、NON_MATERIAL=0、MATERIAL=1。\n"
        "- L5=10與UNRESOLVED=11的primary、confidence、outcome及Healer均獨立支持。\n"
        "- Rank 11 diagnostic-only infrastructure節點完整保留，不取代primary L5；outcome仍為VALID_MODEL_OUTCOME。\n"
        "- MATERIAL：rank 17的off-by-one是局部錯誤，`algorithm_reconstruction_required`缺乏證據；v2應移除此tag。\n"
        "- 修訂後該mechanism計數應由10改為9；其餘主要mechanism統計不變。\n"
        "- abstain=21仍正確：移除該tag不會建立已凍結、tested、task-agnostic且evaluator-blind的Healer規則。\n"
        "- v1未修改、v2未建立；所有執行計數為0。\n"
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
        "per_cell_audit_findings.csv": findings_bytes,
        "field_level_difference_ledger.csv": _csv_bytes(DIFFERENCE_FIELDS, analysis["differences"]),
        "material_findings.csv": _csv_bytes(MATERIAL_FIELDS, analysis["material"]),
        "non_material_findings.csv": _csv_bytes(MATERIAL_FIELDS, analysis["non_material"]),
        "mechanism_audit.csv": _csv_bytes(MECHANISM_AUDIT_FIELDS, analysis["mechanism_audit"]),
        "healer_disposition_audit.csv": _csv_bytes(HEALER_FIELDS, analysis["healer_audit"]),
        "failure_chain_audit.csv": _csv_bytes(CHAIN_AUDIT_FIELDS, analysis["chain_audit"]),
        "unresolved_audit.csv": _csv_bytes(UNRESOLVED_FIELDS, analysis["unresolved_audit"]),
        "audit_summary.json": _json_bytes(analysis["summary"]),
        "execution_counts.json": _json_bytes(execution),
        "report_zh.md": _report(analysis["summary"], _sha(findings_bytes)).encode("utf-8"),
    }
    outputs["provenance.json"] = _json_bytes({
        **analysis["summary"], **execution, "start_head": START_HEAD,
        "source_hashes": {path.as_posix(): digest for path, digest in SOURCE_HASHES.items()},
        "independent_method": "read public specification, generated source, saved result/status, and existing static metadata before comparing v1 fields",
        "candidate_code_imported_or_executed": False, "v1_modified": False, "v2_created": False,
    })
    outputs["manifest.json"] = _json_bytes({
        "revision": OUTPUT_RELATIVE.as_posix(), "status": STATUS, "verdict": VERDICT,
        "start_head": START_HEAD, "findings_sha256": _sha(findings_bytes),
        "provisional_records_sha256": SOURCE_HASHES[PROVISIONAL],
        "provisional_manifest_sha256": SOURCE_HASHES[PROVISIONAL_MANIFEST],
        "roster_sha256": SOURCE_HASHES[ROSTER], "roster_audit_findings_sha256": SOURCE_HASHES[ROSTER_AUDIT],
        "taxonomy_sha256": SOURCE_HASHES[TAXONOMY], "affirmed": 20, "non_material": 0, "material": 1,
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
