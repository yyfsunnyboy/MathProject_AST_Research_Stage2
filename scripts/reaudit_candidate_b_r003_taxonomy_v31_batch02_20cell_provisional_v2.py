#!/usr/bin/env python3
"""Mechanical independent re-audit of Batch02 provisional v2.

This revision verifies that v2 implements exactly the two material findings
approved by the v1 independent audit.  It does not re-adjudicate the eighteen
affirmed cells and performs no candidate/runtime/model work.
"""

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
    "candidate_b_r003_taxonomy_v31_batch02_20cell_provisional_v2_independent_reaudit_v1"
)
START_HEAD = "79a6543ae888a0cedf3694a9985d88c4f97e0713"
STATUS = "INDEPENDENT_MECHANICAL_REAUDIT_COMPLETE_NO_MATERIAL_FINDINGS"
VERDICT = "READY_TO_FREEZE_BATCH02_PROVISIONAL_V2"

ROSTER = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_remaining81_batch02_20cell_roster_v1/batch02_roster.csv")
V1 = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_batch02_20cell_provisional_v1/adjudication_records.csv")
AUDIT = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_batch02_20cell_provisional_v1_independent_audit_v1/material_findings.csv")
V2_DIR = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_batch02_20cell_provisional_v2")
V2 = V2_DIR / "adjudication_records.csv"
V2_MANIFEST = V2_DIR / "manifest.json"
V2_ROSTER = V2_DIR / "adjudication_roster.csv"
V2_CHANGES = V2_DIR / "audit_approved_changes.csv"
V2_SUMMARY = V2_DIR / "adjudication_summary.json"
V2_GAPS = V2_DIR / "unresolved_evidence_gaps.csv"
V2_EXECUTION = V2_DIR / "execution_counts.json"
V2_PROVENANCE = V2_DIR / "provenance.json"
V2_REPORT = V2_DIR / "report_zh.md"

SOURCE_HASHES = {
    ROSTER: "8742e496ce63a834d6b72237319c8b2419fd749b2e2af971700aaef4055c435d",
    V1: "cb4101111e610faeadc292f8d26dbbb5088848011bf9d4527dbbe029b07252e9",
    AUDIT: "47160a3054e2bd634a1530f4f25e663209164d5d45c7f618fb02af1cb3182e9c",
    V2: "dc6d4a4fa0f0027eb87e3af48b3567c72443255fcda2e2779acf7fe0fbf70f04",
    V2_MANIFEST: "0f3bb9c0c106f4bed5942b4883132c92cc460f87fec1e4c146d4333f68346c0d",
    V2_ROSTER: "ca1544ad12d0336638425ac770e7bf40c19e94ca59522e7cf0a90f3d122d6e4c",
    V2_CHANGES: "6544d6225c364eb8e716856934c6e44ab20bf1e840075717e55ea41db4c56897",
    V2_SUMMARY: "a61e382dd3a52c6ea7ce0bc4f46f759cb862249d1e993ba9cf0c7fae9be1a442",
    V2_GAPS: "90c14c69ff97a850a7f699e3da1a2ad6d819da42f7220bb23dc0aec5b277f44a",
    V2_EXECUTION: "a2689e5b6dca7db3a16ca8460cda80476eea60a6907dda92bee875e294f3d4a7",
    V2_PROVENANCE: "57bc54d2f81bd09b4267525028b989753313b6211c855c561afbe1c2b89bcab6",
    V2_REPORT: "9d88e4065b7013f49a91bdeffe11501099cdf33f9d10a96befc7bbcfa302f9d8",
}

TARGET_IDS = {
    "12179f714d4beea5b64235cf46138bb8095c7170101cacbc268dbb8e53ed2f1d",
    "30f2df90febe8769b5db029b8b00959550855960e64ef7a41e570149744cad4a",
}
EXPECTED_CHANGED_FIELDS = {
    "primary_layer", "mechanism_tags_json", "failure_chain", "confidence",
    "eligibility_reason", "unresolved_reason_code", "evidence_present",
    "evidence_missing", "minimal_future_diagnostic", "public_evidence",
    "evidence_citations",
}
EXPECTED_MECHANISMS = {
    "negative_number_boundary": "SUSPECTED",
    "public_examples_non_discriminating": "CONFIRMED",
    "plus_failure_not_localized": "CONFIRMED",
    "diagnostic_execution_required": "SUPPORTED",
    "return_shape_mismatch": "REJECTED",
}
REASON = "input_domain_not_publicly_closed_plus_failure_not_localized"

FINDING_FIELDS = (
    "batch_rank", "program_id", "cell_identity_sha256", "source_sha256",
    "finding_status", "change_scope", "changed_fields_json",
    "identity_status", "source_sha_status", "audit_implementation_status",
    "evidence_gap_status", "citation_status", "material_reason",
)
MATERIAL_FIELDS = FINDING_FIELDS + ("impact", "required_revision")


class ReauditError(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ReauditError(message)


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


def _read_csv(repo: Path, path: Path) -> list[dict[str, str]]:
    with (repo / path).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def verify_sources(repo: Path = REPO_ROOT) -> None:
    for path, digest in SOURCE_HASHES.items():
        _require((repo / path).is_file(), f"missing upstream: {path.as_posix()}")
        _require(_sha((repo / path).read_bytes()) == digest, f"upstream byte drift: {path.as_posix()}")


def build_analysis(repo: Path = REPO_ROOT) -> dict[str, Any]:
    verify_sources(repo)
    roster = _read_csv(repo, ROSTER)
    v1_rows = _read_csv(repo, V1)
    v2_rows = _read_csv(repo, V2)
    material = _read_csv(repo, AUDIT)
    _require(len(roster) == len(v1_rows) == len(v2_rows) == 20, "20-cell closure drift")
    _require({row["program_id"] for row in material} == TARGET_IDS, "audit target closure drift")
    _require([r["program_id"] for r in roster] == [r["program_id"] for r in v1_rows] == [r["program_id"] for r in v2_rows], "row order drift")

    findings: list[dict[str, str]] = []
    changed_ids: set[str] = set()
    unauthorized: list[str] = []
    for roster_row, old, new in zip(roster, v1_rows, v2_rows):
        pid = new["program_id"]
        _require(new["cell_identity_sha256"] == roster_row["cell_identity_sha256"], f"identity drift: {pid}")
        _require(new["source_sha256"] == roster_row["source_sha256"], f"source SHA drift: {pid}")
        changed = [field for field in old if old[field] != new[field]]
        if changed:
            changed_ids.add(pid)
        if pid in TARGET_IDS:
            _require(set(changed) == EXPECTED_CHANGED_FIELDS, f"approved field delta drift: {pid}: {changed}")
            _require(new["primary_layer"] == "UNRESOLVED", f"primary drift: {pid}")
            _require(new["secondary_layer"] == "", f"secondary drift: {pid}")
            _require(new["confidence"] == "LOW", f"confidence drift: {pid}")
            _require(new["outcome_validity"] == "VALID_MODEL_OUTCOME", f"outcome drift: {pid}")
            _require(new["healer_eligibility"] == "abstain", f"healer drift: {pid}")
            mechanisms = {item["tag"]: item["strength"] for item in json.loads(new["mechanism_tags_json"])}
            _require(mechanisms == EXPECTED_MECHANISMS, f"mechanism closure drift: {pid}")
            _require(new["unresolved_reason_code"] == REASON, f"reason drift: {pid}")
            _require(bool(new["evidence_present"] and new["evidence_missing"] and new["minimal_future_diagnostic"]), f"evidence gap incomplete: {pid}")
            citation = f"{AUDIT.as_posix()}#program_id={pid}"
            _require(citation in new["evidence_citations"], f"audit citation missing: {pid}")
            status, scope = "AUDIT_CHANGE_AFFIRMED", "approved_audit_revision"
        else:
            if changed:
                unauthorized.append(pid)
            _require(not changed, f"non-approved row changed: {pid}")
            status, scope = "UNCHANGED_AFFIRMED", "field_for_field_equal_to_v1"
        findings.append({
            "batch_rank": new["batch_rank"], "program_id": pid,
            "cell_identity_sha256": new["cell_identity_sha256"], "source_sha256": new["source_sha256"],
            "finding_status": status, "change_scope": scope,
            "changed_fields_json": json.dumps(changed, ensure_ascii=False, separators=(",", ":")),
            "identity_status": "MATCH", "source_sha_status": "MATCH",
            "audit_implementation_status": "COMPLETE" if pid in TARGET_IDS else "NOT_APPLICABLE",
            "evidence_gap_status": "COMPLETE" if pid in TARGET_IDS else "NOT_REAUDITED",
            "citation_status": "COMPLETE" if pid in TARGET_IDS else "NOT_REAUDITED",
            "material_reason": "",
        })

    _require(changed_ids == TARGET_IDS, f"changed cell closure drift: {sorted(changed_ids)}")
    _require(not unauthorized, f"unauthorized differences: {unauthorized}")
    _require(sum(row["finding_status"] == "UNCHANGED_AFFIRMED" for row in findings) == 18, "18-cell equality drift")
    primary = Counter(row["primary_layer"] for row in v2_rows)
    secondary = Counter(row["secondary_layer"] or "empty" for row in v2_rows)
    confidence = Counter(row["confidence"] for row in v2_rows)
    outcome = Counter(row["outcome_validity"] for row in v2_rows)
    healer = Counter(row["healer_eligibility"] for row in v2_rows)
    _require(primary == Counter({"UNRESOLVED": 11, "L5": 5, "L2": 3, "L4": 1}), f"primary drift: {primary}")
    _require(secondary == Counter({"empty": 16, "L5": 4}), f"secondary drift: {secondary}")
    _require(confidence == Counter({"LOW": 11, "HIGH": 7, "MEDIUM": 2}), f"confidence drift: {confidence}")
    _require(outcome == Counter({"VALID_MODEL_OUTCOME": 20}), f"outcome drift: {outcome}")
    _require(healer == Counter({"abstain": 20}), f"healer drift: {healer}")
    _require(len({r["program_id"] for r in v2_rows}) == 20, "program uniqueness drift")
    _require(len({r["cell_identity_sha256"] for r in v2_rows}) == 20, "cell uniqueness drift")
    _require(len({r["source_sha256"] for r in v2_rows}) == 19, "source uniqueness drift")

    summary = {
        "revision": OUTPUT_RELATIVE.name, "status": STATUS, "verdict": VERDICT,
        "cells": 20, "audit_change_affirmed": 2, "unchanged_affirmed": 18,
        "unauthorized_differences": 0, "material_findings": 0,
        "unique_program_id": 20, "unique_cell_identity": 20, "unique_source_sha256": 19,
        "primary_layer_distribution": dict(sorted(primary.items())),
        "secondary_layer_distribution": dict(sorted(secondary.items())),
        "confidence_distribution": dict(sorted(confidence.items())),
        "outcome_validity_distribution": dict(sorted(outcome.items())),
        "healer_eligibility_distribution": {"eligible": 0, "conditional": 0, "abstain": 20},
        "upstream_modified": False, "new_runtime_observations": 0,
    }
    return {"findings": findings, "material": [], "summary": summary}


def _report(summary: dict[str, Any]) -> str:
    return "\n".join([
        "# Candidate B r003 taxonomy v3.1：Batch02 provisional v2 獨立 re-audit", "",
        f"**狀態：`{STATUS}`**", "", f"**Verdict：`{VERDICT}`**", "",
        "兩格 audit 核准修訂已完整落實；其餘18格與v1逐欄一致。", "",
        "- audit核准差異：2格", "- 非核准差異：0格", "- MATERIAL finding：0格",
        f"- primary：{summary['primary_layer_distribution']}",
        f"- secondary：{summary['secondary_layer_distribution']}",
        f"- confidence：{summary['confidence_distribution']}",
        f"- outcome：{summary['outcome_validity_distribution']}",
        f"- Healer：{summary['healer_eligibility_distribution']}", "",
        "本 re-audit 未重新裁決18格，亦未執行 candidate、imports、tests、EvalPlus、diagnostics、validation、Healer或模型。", "",
    ])


def build_outputs(repo: Path = REPO_ROOT) -> dict[str, bytes]:
    analysis = build_analysis(repo)
    execution = {
        "model_calls": 0, "candidate_executions": 0, "candidate_imports": 0,
        "public_test_executions": 0, "hidden_test_executions": 0,
        "evalplus_correctness_executions": 0, "diagnostics_executions": 0,
        "validation_executions": 0, "healer_executions": 0, "programs_executed": 0,
    }
    outputs = {
        "per_cell_change_findings.csv": _csv_bytes(FINDING_FIELDS, analysis["findings"]),
        "material_findings.csv": _csv_bytes(MATERIAL_FIELDS, analysis["material"]),
        "reaudit_summary.json": _json_bytes(analysis["summary"]),
        "execution_counts.json": _json_bytes(execution),
        "report_zh.md": _report(analysis["summary"]).encode("utf-8"),
    }
    provenance = {
        **analysis["summary"], **execution, "start_head": START_HEAD,
        "scope": "mechanical verification of exactly two approved audit revisions; eighteen rows not re-adjudicated",
        "source_hashes": {path.as_posix(): digest for path, digest in SOURCE_HASHES.items()},
    }
    outputs["provenance.json"] = _json_bytes(provenance)
    manifest = {
        "revision": OUTPUT_RELATIVE.as_posix(), "status": STATUS, "verdict": VERDICT,
        "start_head": START_HEAD, "cells": 20, "audit_approved_differences": 2,
        "unauthorized_differences": 0, "material_findings": 0,
        "fixed_roster_sha256": SOURCE_HASHES[ROSTER], "v1_records_sha256": SOURCE_HASHES[V1],
        "audit_material_findings_sha256": SOURCE_HASHES[AUDIT], "v2_records_sha256": SOURCE_HASHES[V2],
        "v2_manifest_sha256": SOURCE_HASHES[V2_MANIFEST],
        "outputs_sha256_excluding_manifest": {name: _sha(data) for name, data in outputs.items()},
        **execution,
    }
    outputs["manifest.json"] = _json_bytes(manifest)
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
    print(f"manifest_sha256={_sha((output / 'manifest.json').read_bytes())}")
    print(f"verdict={manifest['verdict']}")


if __name__ == "__main__":
    main()
