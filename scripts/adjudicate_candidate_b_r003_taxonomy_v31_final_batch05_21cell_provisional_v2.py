#!/usr/bin/env python3
"""Deterministically apply the sole approved Batch05 v1-to-v2 audit change."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_RELATIVE = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_final_batch05_21cell_provisional_v2")
START_HEAD = "1aa7b692c4d499ada2e0b6e0799b3475f2f68b18"
STATUS = "AUDIT_APPROVED_SINGLE_FIELD_PROVISIONAL_V2_NOT_REAUDITED"
VERDICT = "READY_FOR_FINAL_BATCH05_PROVISIONAL_V2_INDEPENDENT_REAUDIT"
TARGET_RANK = "17"
TARGET_PROGRAM = "fa5a49bae5aacc269bbba5a927d4839d1c04e0afa4d2d508cfc95d34df05c877"
REMOVED_TAG = "algorithm_reconstruction_required"

V1_DIR = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_final_batch05_21cell_provisional_v1")
V1_RECORDS = V1_DIR / "adjudication_records.csv"
V1_MANIFEST = V1_DIR / "manifest.json"
V1_MECHANISMS = V1_DIR / "mechanism_ledger.csv"
V1_CHAINS = V1_DIR / "failure_chain_ledger.csv"
V1_SUMMARY = V1_DIR / "adjudication_summary.json"
V1_GAPS = V1_DIR / "unresolved_evidence_gaps.csv"
V1_EXECUTION = V1_DIR / "execution_counts.json"
V1_PROVENANCE = V1_DIR / "provenance.json"
V1_REPORT = V1_DIR / "report_zh.md"
AUDIT_DIR = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_final_batch05_21cell_provisional_v1_independent_audit_v1")
AUDIT_FINDINGS = AUDIT_DIR / "per_cell_audit_findings.csv"
AUDIT_DIFFERENCES = AUDIT_DIR / "field_level_difference_ledger.csv"
AUDIT_MATERIAL = AUDIT_DIR / "material_findings.csv"
AUDIT_MANIFEST = AUDIT_DIR / "manifest.json"
ROSTER = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_final_batch05_21cell_roster_v1/batch05_roster.csv")
ROSTER_AUDIT = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_final_batch05_21cell_roster_v1_independent_audit_v1/per_cell_roster_findings.csv")
REMAINING21 = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_remaining41_batch04_20cell_roster_v1/remaining21_roster.csv")
CUMULATIVE177 = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_frozen_progress_census_v4/cumulative_frozen_identity_ledger.csv")
TAXONOMY = Path("C:/Users/yehya/Downloads/AI_生成程式共同失敗分類標準_實際使用版_v3.1.md")

SOURCE_HASHES = {
    V1_RECORDS: "ab6b389c1c9d04d72e6bed6a415b422eb222f9b4a8a1cec238ba2af6c34c291c",
    V1_MANIFEST: "b28a96c894f838ace38a673d1a4c6f9d63a12336661804981ca55ff73cc8c68c",
    V1_MECHANISMS: "4db008589a4701be8bc06f267ebe10d64b89e1cf1dc978575a37a4a00cdd7f91",
    V1_CHAINS: "d397088f5c067a4cefad360dc5ea4cb34a66c0fee227cc90961ba635007dd025",
    V1_SUMMARY: "d0d6c9f539014387c9c63e9bc06a909c97f2a2cfcdfe7db73e70aa376eed751f",
    V1_GAPS: "72866c3b068c76576c3744b06bdf61d7d8b87d28af1ac0285ebfbd9e6df44ee7",
    V1_EXECUTION: "a2689e5b6dca7db3a16ca8460cda80476eea60a6907dda92bee875e294f3d4a7",
    V1_PROVENANCE: "c5c32c7f594795857d577834f1f34dfa5426aa51a56b78b12372711c8192a67f",
    V1_REPORT: "a433acebb5c37ae068ec6c163835774016894277e8daa2183d8ba62bb8927535",
    AUDIT_FINDINGS: "ba74b40e03eae81494e2fa84d26a6bbdb98cf0c9cb88543093f428b15d1a2afc",
    AUDIT_DIFFERENCES: "342c36d39063f4878bcd7b02f749a31d592e888d006a7286f02c67e200fc99e7",
    AUDIT_MATERIAL: "86fb73fd1bc61f4b7b8ae2590280510561c6bb9b5d338fea510ab91780b3d314",
    AUDIT_MANIFEST: "5cef1a885e710ede709d97c02d7bb261c8ad2a979b233790a1f81a4d86f6705c",
    ROSTER: "4ec24e450a66c50db46230a5b950137af6e6a4cb3d9a067f182a545818851764",
    ROSTER_AUDIT: "d834c492a4c61bc22048356de6d17c1da2c766f57d948f3df713570251761f34",
    REMAINING21: "48647e94065311f5f8376fb9e3e3299b96b8a95176d97a890be90919ff2ed07b",
    CUMULATIVE177: "d91c7d7f215f9e4a086aaa806958d1f8782686f0e0f71f2fa0df6a6c025f9422",
    TAXONOMY: "93908ec8e4721f0039acc779fb948988b6c25e712c29890bd98aa7c21a8422a0",
}

DIFFERENCE_FIELDS = (
    "batch_rank", "program_id", "cell_identity_sha256", "field_name",
    "approval_source", "v1_value", "v2_value", "change_operation",
    "change_reason", "nonmechanism_fields_unchanged", "approved_difference",
)
MECHANISM_FIELDS = (
    "batch_rank", "program_id", "cell_identity_sha256", "primary_layer",
    "mechanism_tag", "strength", "note",
)
CHAIN_FIELDS = (
    "batch_rank", "program_id", "cell_identity_sha256", "stage_count",
    "primary_layer", "outcome_validity", "failure_chain_json", "citations",
)
GAP_FIELDS = (
    "batch_rank", "program_id", "cell_identity_sha256", "unresolved_reason_code",
    "evidence_present", "evidence_missing", "competing_explanations", "minimal_future_diagnostic",
)


class V2Error(RuntimeError):
    pass


def _require(value: bool, message: str) -> None:
    if not value:
        raise V2Error(message)


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


def _csv_bytes(fields: list[str] | tuple[str, ...], rows: list[dict[str, Any]]) -> bytes:
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
    fields, v1 = _read_csv_with_fields(repo, V1_RECORDS)
    roster = _read_csv(repo, ROSTER)
    audit_findings = _read_csv(repo, AUDIT_FINDINGS)
    audit_differences = _read_csv(repo, AUDIT_DIFFERENCES)
    audit_material = _read_csv(repo, AUDIT_MATERIAL)
    frozen = {(row["program_id"], row["cell_identity_sha256"]) for row in _read_csv(repo, CUMULATIVE177)}
    _require(len(v1) == len(roster) == len(audit_findings) == 21, "21-cell input closure drift")
    _require(len(audit_differences) == len(audit_material) == 1, "audit approval count drift")
    approval = audit_differences[0]
    _require(approval["batch_rank"] == TARGET_RANK and approval["program_id"] == TARGET_PROGRAM, "approved rank/program drift")
    _require(approval["field_name"] == "mechanism_tags_json" and approval["difference_status"] == "MATERIAL", "approved field drift")
    _require(sum(row["audit_status"] == "AFFIRMED" for row in audit_findings) == 20, "audit AFFIRMED count drift")
    _require(sum(row["audit_status"] == "MATERIAL" for row in audit_findings) == 1, "audit MATERIAL count drift")

    v2 = [dict(row) for row in v1]
    target = v2[16]
    _require(target["batch_rank"] == TARGET_RANK and target["program_id"] == TARGET_PROGRAM, "rank 17 identity drift")
    old_tags = json.loads(target["mechanism_tags_json"])
    _require([tag["tag"] for tag in old_tags].count(REMOVED_TAG) == 1, "rank 17 removed tag occurrence drift")
    new_tags = [tag for tag in old_tags if tag["tag"] != REMOVED_TAG]
    _require({tag["tag"] for tag in new_tags} == {"end_index_off_by_one", "wrong_boundary_condition"}, "rank 17 retained tag drift")
    target["mechanism_tags_json"] = json.dumps(new_tags, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    differences: list[tuple[int, str, str, str]] = []
    for rank, (before, after) in enumerate(zip(v1, v2), 1):
        for field in fields:
            if before[field] != after[field]:
                differences.append((rank, field, before[field], after[field]))
    _require(len(differences) == 1, f"unauthorized difference count: {len(differences)}")
    _require(differences[0][0:2] == (17, "mechanism_tags_json"), "unauthorized v1-v2 difference")
    for before, after in zip(v1, v2):
        if before["batch_rank"] != TARGET_RANK:
            _require(before == after, f"non-target row changed: {before['batch_rank']}")
        else:
            for field in fields:
                if field != "mechanism_tags_json":
                    _require(before[field] == after[field], f"rank17 nonmechanism field changed: {field}")
    _require(target["primary_layer"] == "L5" and target["confidence"] == "HIGH", "rank17 primary/confidence drift")
    _require(target["outcome_validity"] == "VALID_MODEL_OUTCOME" and target["healer_eligibility"] == "abstain", "rank17 outcome/healer drift")
    _require(target["failure_chain"] == v1[16]["failure_chain"], "rank17 failure chain drift")

    mechanisms: list[dict[str, str]] = []
    chains: list[dict[str, str]] = []
    gaps: list[dict[str, str]] = []
    for row in v2:
        tags = json.loads(row["mechanism_tags_json"])
        for tag in tags:
            mechanisms.append({
                "batch_rank": row["batch_rank"], "program_id": row["program_id"],
                "cell_identity_sha256": row["cell_identity_sha256"], "primary_layer": row["primary_layer"],
                "mechanism_tag": tag["tag"], "strength": tag["strength"], "note": tag["note"],
            })
        chain = json.loads(row["failure_chain"])
        chains.append({
            "batch_rank": row["batch_rank"], "program_id": row["program_id"],
            "cell_identity_sha256": row["cell_identity_sha256"], "stage_count": str(len(chain)),
            "primary_layer": row["primary_layer"], "outcome_validity": row["outcome_validity"],
            "failure_chain_json": row["failure_chain"], "citations": row["evidence_citations"],
        })
        if row["primary_layer"] == "UNRESOLVED":
            gaps.append({field: row[field] for field in GAP_FIELDS})

    primary = Counter(row["primary_layer"] for row in v2)
    secondary = Counter(row["secondary_layer"] or "empty" for row in v2)
    confidence = Counter(row["confidence"] for row in v2)
    outcome = Counter(row["outcome_validity"] for row in v2)
    healer = Counter(row["healer_eligibility"] for row in v2)
    mechanism_counts = Counter(row["mechanism_tag"] for row in mechanisms)
    _require(primary == {"L5": 10, "UNRESOLVED": 11}, "primary distribution drift")
    _require(secondary == {"empty": 21} and confidence == {"HIGH": 10, "LOW": 11}, "secondary/confidence drift")
    _require(outcome == {"VALID_MODEL_OUTCOME": 21} and healer == {"abstain": 21}, "outcome/healer drift")
    _require(mechanism_counts[REMOVED_TAG] == 9, "algorithm reconstruction mechanism count drift")
    program_ids = {row["program_id"] for row in v2}
    cell_ids = {row["cell_identity_sha256"] for row in v2}
    source_ids = {row["source_sha256"] for row in v2}
    _require(len(program_ids) == len(cell_ids) == 21 and len(source_ids) == 20, "identity/source closure drift")
    _require(all((row["program_id"], row["cell_identity_sha256"]) not in frozen for row in v2), "frozen177 overlap")

    difference_ledger = [{
        "batch_rank": TARGET_RANK, "program_id": TARGET_PROGRAM,
        "cell_identity_sha256": target["cell_identity_sha256"], "field_name": "mechanism_tags_json",
        "approval_source": f"{AUDIT_DIFFERENCES.as_posix()}#batch_rank=17;field_name=mechanism_tags_json",
        "v1_value": v1[16]["mechanism_tags_json"], "v2_value": target["mechanism_tags_json"],
        "change_operation": "REMOVE_TAG:algorithm_reconstruction_required",
        "change_reason": "match.end()-1 is a localized off-by-one and does not require algorithm reconstruction",
        "nonmechanism_fields_unchanged": "true", "approved_difference": "true",
    }]
    summary = {
        "revision": OUTPUT_RELATIVE.name, "status": STATUS, "verdict": VERDICT,
        "cells": 21, "v1_to_v2_changed_records": 1, "v1_to_v2_changed_fields": 1,
        "changed_ranks": [17], "approved_differences_adopted": 1, "unauthorized_differences": 0,
        "unchanged_records": 20, "rank17_nonmechanism_fields_unchanged": True,
        "primary_distribution": dict(sorted(primary.items())),
        "secondary_distribution": dict(sorted(secondary.items())),
        "confidence_distribution": dict(sorted(confidence.items())),
        "outcome_validity_distribution": dict(sorted(outcome.items())),
        "healer_distribution": {"eligible": 0, "conditional": 0, "abstain": 21},
        "mechanism_distribution": dict(sorted(mechanism_counts.items())),
        "algorithm_reconstruction_required_v1": 10,
        "algorithm_reconstruction_required_v2": mechanism_counts[REMOVED_TAG],
        "unique_program_id": 21, "unique_cell_identity": 21, "unique_source_sha256": 20,
        "legal_shared_source_ranks": [5, 21], "overlap_with_frozen177": 0,
        "set_closure": "198=177+21", "unadjudicated_remaining": 0,
        "independent_reaudit_performed": False, "v2_frozen": False,
    }
    return {
        "fields": fields, "records": v2, "difference_ledger": difference_ledger,
        "mechanisms": mechanisms, "chains": chains, "gaps": gaps, "summary": summary,
    }


def _report(summary: dict[str, Any], records_sha: str) -> str:
    return (
        "# Final Batch05 provisional adjudication v2\n\n"
        f"**狀態：`{STATUS}`**\n\n**Records SHA-256：`{records_sha}`**\n\n"
        "- v1→v2唯一差異：rank 17 mechanism_tags_json移除algorithm_reconstruction_required。\n"
        "- rank 17的primary=L5、confidence=HIGH、outcome、failure chain、Healer=abstain及其他非mechanism欄位均不變。\n"
        "- 其餘20格逐欄等值；未核准差異=0。\n"
        "- Primary：L5=10、UNRESOLVED=11；Secondary empty=21；HIGH=10、LOW=11。\n"
        "- Outcome VALID_MODEL_OUTCOME=21；Healer eligible=0、conditional=0、abstain=21。\n"
        "- algorithm_reconstruction_required：10→9；其他mechanism由v2 records重建。\n"
        "- 198=177+21；未裁決剩餘=0；所有執行計數為0。\n"
        "- 本revision尚未獨立re-audit、未freeze。\n"
    )


def build_outputs(repo: Path = REPO_ROOT) -> dict[str, bytes]:
    analysis = build_analysis(repo)
    records_bytes = _csv_bytes(analysis["fields"], analysis["records"])
    execution = {
        "model_calls": 0, "candidate_executions": 0, "candidate_imports": 0,
        "candidate_test_executions": 0, "public_test_executions": 0,
        "hidden_test_executions": 0, "evalplus_correctness_executions": 0,
        "diagnostics_executions": 0, "validation_executions": 0,
        "healer_executions": 0, "programs_executed": 0,
    }
    outputs = {
        "adjudication_records.csv": records_bytes,
        "approved_difference_ledger.csv": _csv_bytes(DIFFERENCE_FIELDS, analysis["difference_ledger"]),
        "mechanism_ledger.csv": _csv_bytes(MECHANISM_FIELDS, analysis["mechanisms"]),
        "failure_chain_ledger.csv": _csv_bytes(CHAIN_FIELDS, analysis["chains"]),
        "unresolved_evidence_gaps.csv": _csv_bytes(GAP_FIELDS, analysis["gaps"]),
        "adjudication_summary.json": _json_bytes(analysis["summary"]),
        "execution_counts.json": _json_bytes(execution),
        "report_zh.md": _report(analysis["summary"], _sha(records_bytes)).encode("utf-8"),
    }
    outputs["provenance.json"] = _json_bytes({
        **analysis["summary"], **execution, "start_head": START_HEAD,
        "provenance_chain": "roster -> roster audit -> provisional v1 -> independent audit -> provisional v2",
        "source_hashes": {path.as_posix(): digest for path, digest in SOURCE_HASHES.items()},
        "change_policy": "apply only audit-approved rank17 mechanism_tags_json tag removal",
        "candidate_code_imported_or_executed": False, "independent_reaudit_performed": False,
    })
    outputs["manifest.json"] = _json_bytes({
        "revision": OUTPUT_RELATIVE.as_posix(), "status": STATUS, "verdict": VERDICT,
        "start_head": START_HEAD, "records_sha256": _sha(records_bytes),
        "v1_records_sha256": SOURCE_HASHES[V1_RECORDS], "v1_manifest_sha256": SOURCE_HASHES[V1_MANIFEST],
        "audit_findings_sha256": SOURCE_HASHES[AUDIT_FINDINGS], "audit_manifest_sha256": SOURCE_HASHES[AUDIT_MANIFEST],
        "audit_difference_ledger_sha256": SOURCE_HASHES[AUDIT_DIFFERENCES],
        "taxonomy_sha256": SOURCE_HASHES[TAXONOMY], "changed_records": 1,
        "changed_fields": 1, "unauthorized_differences": 0,
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
    print(f"records_sha256={manifest['records_sha256']}")
    print(f"manifest_sha256={_sha((output / 'manifest.json').read_bytes())}")
    print(f"verdict={manifest['verdict']}")


if __name__ == "__main__":
    main()
