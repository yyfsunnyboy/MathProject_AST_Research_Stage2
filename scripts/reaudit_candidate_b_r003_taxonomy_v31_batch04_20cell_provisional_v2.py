#!/usr/bin/env python3
"""Independent mechanical re-audit of Batch04 provisional v2.

This verifies the complete v1→v2 delta, independently checks the single approved
source-level correction, and reconciles every v2 derivative.  No unaffected
cell is re-adjudicated and no candidate/runtime/model work is performed.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_batch04_20cell_provisional_v2_independent_reaudit_v1"
)
START_HEAD = "4ef378b6303ff58291acc2c7a60b874ee8c2cc68"
STATUS = "INDEPENDENT_V2_REAUDIT_COMPLETE_NO_MATERIAL_FINDINGS"
VERDICT = "READY_TO_FREEZE_BATCH04_PROVISIONAL_V2"

ROSTER = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_remaining41_batch04_20cell_roster_v1/batch04_roster.csv"
)
V1_DIR = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_batch04_20cell_provisional_v1"
)
V1_RECORDS = V1_DIR / "adjudication_records.csv"
V1_EVIDENCE = V1_DIR / "per_cell_evidence_ledger.csv"
V1_GAPS = V1_DIR / "unresolved_evidence_gaps.csv"
V1_CONDITIONAL = V1_DIR / "conditional_diagnostic_queue.csv"
AUDIT_DIR = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_batch04_20cell_provisional_v1_independent_audit_v1"
)
AUDIT_FINDINGS = AUDIT_DIR / "per_cell_audit_findings.csv"
AUDIT_MATERIAL = AUDIT_DIR / "material_findings.csv"
AUDIT_MANIFEST = AUDIT_DIR / "manifest.json"
V2_DIR = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_batch04_20cell_provisional_v2"
)
V2_RECORDS = V2_DIR / "adjudication_records.csv"
V2_MANIFEST = V2_DIR / "manifest.json"
V2_LEDGER = V2_DIR / "approved_difference_ledger.csv"
V2_EVIDENCE = V2_DIR / "per_cell_evidence_ledger.csv"
V2_MECHANISMS = V2_DIR / "mechanism_ledger.csv"
V2_CONDITIONAL = V2_DIR / "conditional_diagnostic_queue.csv"
V2_GAPS = V2_DIR / "unresolved_evidence_gaps.csv"
V2_SUMMARY = V2_DIR / "adjudication_summary.json"
V2_EXECUTION = V2_DIR / "execution_counts.json"
V2_PROVENANCE = V2_DIR / "provenance.json"
V2_REPORT = V2_DIR / "report_zh.md"
V2_BUILDER = Path("scripts/adjudicate_candidate_b_r003_taxonomy_v31_batch04_20cell_provisional_v2.py")
V2_TEST = Path("tests/finals_rebuild/test_candidate_b_r003_taxonomy_v31_batch04_20cell_provisional_v2.py")
ACCOUNTS = Path(
    "artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/"
    "mbpp_q35_9b_candidate_b_development60_replay_r003/h0_h1_accounts.jsonl"
)
TASKS = Path("data/mbpp_plus/tasks.jsonl")
EVALPLUS = Path(
    "artifacts/public_benchmark_governance/candidate_b_r003_h0_h1_evalplus_v1/"
    "manual_evalplus_run_001/evalplus_results.csv"
)
TAXONOMY = Path("C:/Users/yehya/Downloads/AI_生成程式共同失敗分類標準_實際使用版_v3.1.md")

SOURCE_HASHES = {
    ROSTER: "0c77a58de44149c17c2dd33ed310c2ef4e6b81b357874eb9ab21157e59b2ecae",
    V1_RECORDS: "5f61c4fc90f9200376e85c622f3fd54d4fa2fd6f0829e1606fb52a17a6033624",
    V1_EVIDENCE: "85a8ee679816ca931126cec3199139b3523504f7b69b915dad8765ddf2cf362e",
    V1_GAPS: "76ad7647b3348705e0069da451af73a601014f8e403b73f85b920ceb46feda48",
    V1_CONDITIONAL: "fb82e22dad104d428fbb8e8c66024e742ccdc7c326fffa0e9b6969b6133c1808",
    AUDIT_FINDINGS: "95a7d6927666b8f153db68a39a4f4e3db219aad95ce15f3f340b55a4ce197f53",
    AUDIT_MATERIAL: "17560e5c50ec7147be536c9f8c7d26ce230ae4d912e3f600c0ef7b0169a391b2",
    AUDIT_MANIFEST: "a264dd9b32a33911c2d6ba9fec0bbbb75d7459c3ae5599734b05178ddff46e83",
    V2_RECORDS: "03cf83d8f295815f5f5f66dbdc3eb347556606245e542d052d88d0a50d945028",
    V2_MANIFEST: "b0b41591716133d183b56ae9c4f9254ef726524d06831be0c2b7361f05953681",
    V2_LEDGER: "125f6f367867fea06fc123a81765aabdd7f572a0af8709d966ce86197d6b3bc1",
    V2_EVIDENCE: "85a8ee679816ca931126cec3199139b3523504f7b69b915dad8765ddf2cf362e",
    V2_MECHANISMS: "10c2897809de9b0d86c8cbd9a23955eab199a76711b19e1702548fae553d3a9b",
    V2_CONDITIONAL: "fb82e22dad104d428fbb8e8c66024e742ccdc7c326fffa0e9b6969b6133c1808",
    V2_GAPS: "76ad7647b3348705e0069da451af73a601014f8e403b73f85b920ceb46feda48",
    V2_SUMMARY: "290ce21fbe4a8aa7ba3b4bfc0f63369b499a15595303e86f386cfce7a202869d",
    V2_EXECUTION: "a2689e5b6dca7db3a16ca8460cda80476eea60a6907dda92bee875e294f3d4a7",
    V2_PROVENANCE: "e9beeb9eef0c3c5660f52ca322c7277ea2521338eec693b8616bbb13158b64e0",
    V2_REPORT: "0bad2629e6be924c8a99f6d372fb8738b0fef3e7a2b6ed1309edb8d5a62598fe",
    V2_BUILDER: "decf9ef001306e75973f5675d3fbea23a4dadb01b6cce5a0de19650430f6305a",
    V2_TEST: "1c2fb8c022018f2883f565ab49d239533c19fcdc328bb3c00da2c2cee12c565e",
    ACCOUNTS: "b1313615bf41840bc1c45c36d2b8ac9b544f37fb5bb801c104aad1657ca2c2ec",
    TASKS: "b816022b8b587047cb1d275417a96acb009de328684e5914e7ac010c9d8c6f3c",
    EVALPLUS: "338e66ecd09f48bcf2b8c8d1c8cf75911755dad92743c99257698d994a01938e",
    TAXONOMY: "93908ec8e4721f0039acc779fb948988b6c25e712c29890bd98aa7c21a8422a0",
}

TARGET_IDS = {
    "9dbe9166f6ac22cedfafb269276c88ee25a37cf84044e736f7be00d8089464ba",
}
OLD_TAG = "dedupe_instead_of_unique_occurrence"
NEW_TAG = "frequency_one_instead_of_distinct_value"

FINDING_FIELDS = (
    "batch_rank", "program_id", "cell_identity_sha256", "source_sha256",
    "reaudit_status", "change_status", "changed_fields_json", "identity_status",
    "derived_products_status", "independent_evidence", "material_reason",
)
DIFF_FIELDS = (
    "batch_rank", "program_id", "cell_identity_sha256", "field_name",
    "expected_change", "observed_change", "verification_status", "evidence",
)
APPROVED_FIELDS = (
    "batch_rank", "program_id", "cell_identity_sha256", "source_sha256",
    "verification_status", "v1_mechanisms_json", "v2_mechanisms_json",
    "preserved_fields_status", "independent_source_evidence", "public_contract_evidence",
)
ISSUE_FIELDS = ("scope", "finding_id", "field_name", "observed", "expected", "evidence", "impact")


class ReauditError(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ReauditError(message)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_csv(repo: Path, path: Path) -> list[dict[str, str]]:
    actual = path if path.is_absolute() else repo / path
    with actual.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_jsonl(repo: Path, path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in (repo / path).read_text(encoding="utf-8").splitlines() if line]


def _csv_bytes(fields: tuple[str, ...], rows: list[dict[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows({field: row.get(field, "") for field in fields} for row in rows)
    return stream.getvalue().encode("utf-8")


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def verify_sources(repo: Path = REPO_ROOT) -> None:
    for path, digest in SOURCE_HASHES.items():
        actual = path if path.is_absolute() else repo / path
        _require(actual.is_file(), f"missing upstream: {path.as_posix()}")
        _require(_sha(actual.read_bytes()) == digest, f"upstream byte drift: {path.as_posix()}")
    v2_manifest = json.loads((repo / V2_MANIFEST).read_text(encoding="utf-8"))
    _require(
        v2_manifest["verdict"] == "READY_FOR_BATCH04_PROVISIONAL_V2_INDEPENDENT_REAUDIT",
        "v2 verdict drift",
    )
    audit_manifest = json.loads((repo / AUDIT_MANIFEST).read_text(encoding="utf-8"))
    _require(audit_manifest["verdict"] == "BATCH04_PROVISIONAL_V2_REVISION_REQUIRED", "audit verdict drift")
    _require(audit_manifest["material"] == 1, "audit material count drift")


def build_analysis(repo: Path = REPO_ROOT) -> dict[str, Any]:
    verify_sources(repo)
    roster = _read_csv(repo, ROSTER)
    v1 = _read_csv(repo, V1_RECORDS)
    v2 = _read_csv(repo, V2_RECORDS)
    ledger = _read_csv(repo, V2_LEDGER)
    audit_material = _read_csv(repo, AUDIT_MATERIAL)
    mechanism_rows = _read_csv(repo, V2_MECHANISMS)
    evidence_rows = _read_csv(repo, V2_EVIDENCE)
    gaps = _read_csv(repo, V2_GAPS)
    conditional = _read_csv(repo, V2_CONDITIONAL)
    summary = json.loads((repo / V2_SUMMARY).read_text(encoding="utf-8"))
    provenance = json.loads((repo / V2_PROVENANCE).read_text(encoding="utf-8"))
    report = (repo / V2_REPORT).read_text(encoding="utf-8")
    accounts = {r["program_id"]: r for r in _read_jsonl(repo, ACCOUNTS) if r["healer_account"] == "H0"}
    tasks = {r["task_id"]: r for r in _read_jsonl(repo, TASKS)}
    evals = {r["program_id"]: r for r in _read_csv(repo, EVALPLUS) if r["healer_account"] == "H0"}
    _require(len(roster) == len(v1) == len(v2) == 20, "20-cell closure drift")
    _require(
        [r["program_id"] for r in roster]
        == [r["program_id"] for r in v1]
        == [r["program_id"] for r in v2],
        "order closure drift",
    )
    _require(
        {r["program_id"] for r in ledger}
        == {r["program_id"] for r in audit_material}
        == TARGET_IDS,
        "approved target closure drift",
    )

    findings: list[dict[str, str]] = []
    differences: list[dict[str, str]] = []
    approved: list[dict[str, str]] = []
    changed_ids: set[str] = set()
    for rr, old, new in zip(roster, v1, v2):
        pid = new["program_id"]
        _require(new["cell_identity_sha256"] == rr["cell_identity_sha256"], f"identity drift: {pid}")
        _require(
            new["source_sha256"] == rr["source_sha256"] == accounts[pid]["evaluation_source_sha256"],
            f"source drift: {pid}",
        )
        changed = [field for field in old if old[field] != new[field]]
        if changed:
            changed_ids.add(pid)
        if pid in TARGET_IDS:
            _require(changed == ["mechanism_tags_json"], f"approved record delta drift: {pid}:{changed}")
            old_tags = {x["tag"]: x["strength"] for x in json.loads(old["mechanism_tags_json"])}
            new_tags = {x["tag"]: x["strength"] for x in json.loads(new["mechanism_tags_json"])}
            _require(
                old_tags == {OLD_TAG: "CONFIRMED", "semantic_goal_drift": "CONFIRMED"},
                f"v1 target mechanisms drift: {pid}",
            )
            _require(
                new_tags == {NEW_TAG: "CONFIRMED", "semantic_goal_drift": "CONFIRMED"},
                f"v2 target mechanisms drift: {pid}",
            )
            for field in old:
                if field != "mechanism_tags_json":
                    _require(old[field] == new[field], f"target preserved field drift: {pid}:{field}")
            _require(new["primary_layer"] == "L5" and new["confidence"] == "HIGH", "rank10 disposition drift")
            _require(
                new["outcome_validity"] == "VALID_MODEL_OUTCOME"
                and new["healer_eligibility"] == "abstain",
                "rank10 outcome/healer drift",
            )
            source = accounts[pid]["evaluation_source"]
            prompt = tasks[new["task_id"]]["prompt"]
            _require("Counter" in source and "counts[num] == 1" in source, "independent source evidence drift")
            _require("find_sum([1,2,3,1,1,4,5,6]) == 21" in prompt, "public contract evidence drift")
            _require(
                evals[pid]["base_status"] == "fail" and evals[pid]["plus_status"] == "fail",
                "preserved evaluator evidence drift",
            )
            approved.append(
                {
                    "batch_rank": new["batch_rank"],
                    "program_id": pid,
                    "cell_identity_sha256": new["cell_identity_sha256"],
                    "source_sha256": new["source_sha256"],
                    "verification_status": "AFFIRMED",
                    "v1_mechanisms_json": json.dumps(old_tags, sort_keys=True, separators=(",", ":")),
                    "v2_mechanisms_json": json.dumps(new_tags, sort_keys=True, separators=(",", ":")),
                    "preserved_fields_status": "ALL_NON_MECHANISM_FIELDS_EQUAL",
                    "independent_source_evidence": (
                        "Counter frequency map; sum includes only counts[num] == 1, "
                        "excluding repeated value 1 entirely"
                    ),
                    "public_contract_evidence": (
                        "public assert expects 21, requiring each distinct value 1..6 once"
                    ),
                }
            )
            differences.append(
                {
                    "batch_rank": new["batch_rank"],
                    "program_id": pid,
                    "cell_identity_sha256": new["cell_identity_sha256"],
                    "field_name": "mechanism_tags_json",
                    "expected_change": f"{OLD_TAG} -> {NEW_TAG}",
                    "observed_change": f"{OLD_TAG} -> {NEW_TAG}",
                    "verification_status": "AFFIRMED",
                    "evidence": "v1 audit material finding plus independent source/public contract",
                }
            )
            change_status = "APPROVED_CHANGE_AFFIRMED"
            evidence = (
                "frequency-one filter and public distinct-value result independently confirm corrected direction"
            )
        else:
            _require(not changed, f"unapproved record delta: {pid}:{changed}")
            change_status = "UNCHANGED_AFFIRMED"
            evidence = "record field-for-field equal to v1; not re-adjudicated"
        findings.append(
            {
                "batch_rank": new["batch_rank"],
                "program_id": pid,
                "cell_identity_sha256": new["cell_identity_sha256"],
                "source_sha256": new["source_sha256"],
                "reaudit_status": "AFFIRMED",
                "change_status": change_status,
                "changed_fields_json": json.dumps(changed, separators=(",", ":")),
                "identity_status": "MATCH",
                "derived_products_status": "MATCH",
                "independent_evidence": evidence,
                "material_reason": "",
            }
        )
    _require(changed_ids == TARGET_IDS and len(approved) == len(differences) == 1, "complete delta closure drift")
    _require(sum(a == b for a, b in zip(v1, v2)) == 19, "19-cell equality drift")

    ledger_by_pid = {r["program_id"]: r for r in ledger}
    _require(
        all(json.loads(ledger_by_pid[p]["changed_fields_json"]) == ["mechanism_tags_json"] for p in TARGET_IDS),
        "approved ledger field drift",
    )
    mechanisms_by_pid: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    for row in mechanism_rows:
        mechanisms_by_pid[row["program_id"]].append(
            (row["mechanism_tag"], row["strength"], row["note"])
        )
    for row in v2:
        record_tags = sorted((x["tag"], x["strength"], x["note"]) for x in json.loads(row["mechanism_tags_json"]))
        _require(
            record_tags == sorted(mechanisms_by_pid[row["program_id"]]),
            f"mechanism ledger mismatch: {row['program_id']}",
        )
    _require((repo / V2_EVIDENCE).read_bytes() == (repo / V1_EVIDENCE).read_bytes(), "evidence ledger should remain byte-identical")
    _require((repo / V2_GAPS).read_bytes() == (repo / V1_GAPS).read_bytes() and len(gaps) == 9, "gap derivative drift")
    _require(
        (repo / V2_CONDITIONAL).read_bytes() == (repo / V1_CONDITIONAL).read_bytes() and len(conditional) == 0,
        "conditional derivative drift",
    )
    primary = Counter(r["primary_layer"] for r in v2)
    secondary = Counter(r["secondary_layer"] or "empty" for r in v2)
    confidence = Counter(r["confidence"] for r in v2)
    outcome = Counter(r["outcome_validity"] for r in v2)
    healer = Counter(r["healer_eligibility"] for r in v2)
    mechanism_counts = Counter(r["mechanism_tag"] for r in mechanism_rows)
    _require(summary["primary_layer_distribution"] == dict(sorted(primary.items())), "summary primary drift")
    _require(summary["secondary_layer_distribution"] == dict(sorted(secondary.items())), "summary secondary drift")
    _require(summary["confidence_distribution"] == dict(sorted(confidence.items())), "summary confidence drift")
    _require(summary["outcome_validity_distribution"] == dict(sorted(outcome.items())), "summary outcome drift")
    _require(summary["mechanism_tag_distribution"] == dict(sorted(mechanism_counts.items())), "summary mechanism drift")
    _require(
        summary["healer_eligibility_distribution"] == {"eligible": 0, "conditional": 0, "abstain": 20},
        "summary healer drift",
    )
    _require(mechanism_counts[NEW_TAG] == 1 and mechanism_counts[OLD_TAG] == 0, "corrected mechanism derivative drift")
    _require(mechanism_counts["semantic_goal_drift"] == 3, "semantic_goal_drift count drift")
    _require(NEW_TAG in report and OLD_TAG in report and "：0" in report, "report correction statement drift")
    _require(
        [x["stage"] for x in provenance["chain"]]
        == ["roster", "roster_audit", "provisional_v1", "independent_audit", "provisional_v2"],
        "provenance chain drift",
    )
    _require(len(evidence_rows) == 20, "evidence ledger row drift")

    shared = [r for r in v2 if r["batch_rank"] in {"5", "12"}]
    _require(
        len({r["source_sha256"] for r in shared}) == 1 and len({r["cell_identity_sha256"] for r in shared}) == 2,
        "legal shared source closure drift",
    )
    _require(primary == Counter({"L5": 10, "UNRESOLVED": 9, "L4": 1}), "expected primary stats drift")
    _require(secondary == Counter({"empty": 19, "L5": 1}), "expected secondary stats drift")
    _require(confidence == Counter({"HIGH": 11, "LOW": 9}), "expected confidence stats drift")
    _require(outcome == Counter({"VALID_MODEL_OUTCOME": 20}), "expected outcome stats drift")
    _require(healer == Counter({"abstain": 20}), "expected healer stats drift")
    rebuilt = {
        "primary": dict(sorted(primary.items())),
        "secondary": dict(sorted(secondary.items())),
        "confidence": dict(sorted(confidence.items())),
        "outcome": dict(sorted(outcome.items())),
        "healer": {"eligible": 0, "conditional": 0, "abstain": 20},
        "mechanisms": dict(sorted(mechanism_counts.items())),
    }
    summary_out = {
        "revision": OUTPUT_RELATIVE.name,
        "status": STATUS,
        "verdict": VERDICT,
        "cells": 20,
        "affirmed": 20,
        "non_material": 0,
        "material": 0,
        "approved_changes_affirmed": 1,
        "unchanged_records_affirmed": 19,
        "unauthorized_differences": 0,
        "identity_source_closure": 20,
        "unique_program_id": 20,
        "unique_cell_identity": 20,
        "unique_source_sha256": 19,
        "legal_shared_source_ranks": ["5", "12"],
        "rebuilt_statistics": rebuilt,
        "derived_products_affirmed": 6,
        "first_audit_material_fully_corrected": True,
        "upstream_modified": False,
        "new_runtime_observations": 0,
        "batch05_started": False,
    }
    return {
        "findings": findings,
        "differences": differences,
        "approved": approved,
        "material": [],
        "non_material": [],
        "summary": summary_out,
    }


def _report(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Candidate B r003 taxonomy v3.1：Batch04 provisional v2 獨立re-audit",
            "",
            f"**狀態：`{STATUS}`**",
            "",
            "- AFFIRMED：20",
            "- NON_MATERIAL：0",
            "- MATERIAL：0",
            "- Rank 10核准mechanism修訂完整落實：`dedupe_instead_of_unique_occurrence` → "
            "`frequency_one_instead_of_distinct_value`；`semantic_goal_drift`保留",
            "- 其餘19格records逐欄等同v1",
            "- 未核准差異：0",
            "- mechanism/evidence/summary/report/gaps/conditional derivatives全部閉合",
            "",
            f"- Primary：{summary['rebuilt_statistics']['primary']}",
            f"- Secondary：{summary['rebuilt_statistics']['secondary']}",
            f"- Confidence：{summary['rebuilt_statistics']['confidence']}",
            f"- Outcome：{summary['rebuilt_statistics']['outcome']}",
            f"- Healer：{summary['rebuilt_statistics']['healer']}",
            f"- `{NEW_TAG}`：1；`{OLD_TAG}`：0；`semantic_goal_drift`：3",
            "",
            "Rank 10 source使用Counter frequency map並只納入counts[num] == 1；公開assert 21要求"
            "distinct值各計一次。首次audit唯一MATERIAL已完全修正且未引入新差異。",
            "",
            "未重新裁決其他個案，未執行candidate、tests、diagnostics、Healer或模型；未freeze、未開始Batch05。",
            "",
        ]
    )


def build_outputs(repo: Path = REPO_ROOT) -> dict[str, bytes]:
    analysis = build_analysis(repo)
    execution = {
        "model_calls": 0,
        "candidate_executions": 0,
        "candidate_imports": 0,
        "public_test_executions": 0,
        "hidden_test_executions": 0,
        "evalplus_correctness_executions": 0,
        "diagnostics_executions": 0,
        "validation_executions": 0,
        "healer_executions": 0,
        "programs_executed": 0,
    }
    outputs = {
        "per_cell_v2_reaudit_findings.csv": _csv_bytes(FINDING_FIELDS, analysis["findings"]),
        "field_level_difference_verification.csv": _csv_bytes(DIFF_FIELDS, analysis["differences"]),
        "approved_change_verification.csv": _csv_bytes(APPROVED_FIELDS, analysis["approved"]),
        "material_findings.csv": _csv_bytes(ISSUE_FIELDS, analysis["material"]),
        "non_material_findings.csv": _csv_bytes(ISSUE_FIELDS, analysis["non_material"]),
        "reaudit_summary.json": _json_bytes(analysis["summary"]),
        "execution_counts.json": _json_bytes(execution),
        "report_zh.md": _report(analysis["summary"]).encode("utf-8"),
    }
    provenance = {
        **analysis["summary"],
        **execution,
        "start_head": START_HEAD,
        "v1_records_sha256": SOURCE_HASHES[V1_RECORDS],
        "v1_audit_findings_sha256": SOURCE_HASHES[AUDIT_FINDINGS],
        "v1_audit_material_sha256": SOURCE_HASHES[AUDIT_MATERIAL],
        "v2_records_sha256": SOURCE_HASHES[V2_RECORDS],
        "v2_manifest_sha256": SOURCE_HASHES[V2_MANIFEST],
        "approved_difference_ledger_sha256": SOURCE_HASHES[V2_LEDGER],
        "taxonomy_sha256": SOURCE_HASHES[TAXONOMY],
        "source_hashes": {path.as_posix(): digest for path, digest in SOURCE_HASHES.items()},
        "v1_modified": False,
        "audit_modified": False,
        "v2_modified": False,
        "batch04_frozen": False,
        "batch05_started": False,
    }
    outputs["provenance.json"] = _json_bytes(provenance)
    manifest = {
        "revision": OUTPUT_RELATIVE.as_posix(),
        "status": STATUS,
        "verdict": VERDICT,
        "start_head": START_HEAD,
        "cells": 20,
        "affirmed": 20,
        "non_material": 0,
        "material": 0,
        "v2_records_sha256": SOURCE_HASHES[V2_RECORDS],
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
    print(f"findings_sha256={manifest['outputs_sha256_excluding_manifest']['per_cell_v2_reaudit_findings.csv']}")
    print(f"manifest_sha256={_sha((output / 'manifest.json').read_bytes())}")
    print(f"verdict={manifest['verdict']}")


if __name__ == "__main__":
    main()
