#!/usr/bin/env python3
"""Formal immutable freeze of Batch04 provisional adjudication v2.

The v2 records and ledgers are copied byte-for-byte.  This builder also emits a
new frozen-progress census revision reconciling 157+20=177 and 198=177+21.
No reclassification, review, candidate execution, or model work is performed.
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
    "candidate_b_r003_taxonomy_v31_batch04_20cell_frozen_v1"
)
PROGRESS_OUTPUT = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_frozen_progress_census_v4"
)
START_HEAD = "4ef378b6303ff58291acc2c7a60b874ee8c2cc68"
STATUS = "FORMALLY_FROZEN_AI_ASSISTED_PROVISIONAL_ADJUDICATION"
PROGRESS_STATUS = "TAXONOMY_V31_FROZEN_PROGRESS_CENSUS"
VERDICT = "BATCH04_PROVISIONAL_V2_FROZEN_READY_TO_COMMIT"
FREEZE_BASIS = "READY_TO_FREEZE_BATCH04_PROVISIONAL_V2"

PREVIOUSLY_FROZEN = 157
NEWLY_FROZEN = 20
TOTAL_FROZEN = 177
REMAINING = 21
FORMAL_POPULATION = 198

ROSTER = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_remaining41_batch04_20cell_roster_v1/batch04_roster.csv"
)
ROSTER_MANIFEST = ROSTER.with_name("manifest.json")
REMAINING21 = ROSTER.with_name("remaining21_roster.csv")
ROSTER_AUDIT = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_remaining41_batch04_20cell_roster_v1_independent_audit_v1/manifest.json"
)
V1_DIR = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_batch04_20cell_provisional_v1"
)
V1_RECORDS = V1_DIR / "adjudication_records.csv"
V1_MANIFEST = V1_DIR / "manifest.json"
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
V2_GAPS = V2_DIR / "unresolved_evidence_gaps.csv"
V2_CONDITIONAL = V2_DIR / "conditional_diagnostic_queue.csv"
V2_SUMMARY = V2_DIR / "adjudication_summary.json"
REAUDIT_DIR = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_batch04_20cell_provisional_v2_independent_reaudit_v1"
)
REAUDIT_FINDINGS = REAUDIT_DIR / "per_cell_v2_reaudit_findings.csv"
REAUDIT_APPROVED = REAUDIT_DIR / "approved_change_verification.csv"
REAUDIT_SUMMARY = REAUDIT_DIR / "reaudit_summary.json"
REAUDIT_MANIFEST = REAUDIT_DIR / "manifest.json"
BATCH01_FROZEN = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_frozen_v1/frozen_adjudication.csv"
)
BATCH02_FROZEN = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_batch02_20cell_frozen_v1/frozen_adjudication.csv"
)
BATCH03_FROZEN = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_batch03_20cell_frozen_v1/frozen_adjudication_records.csv"
)
BATCH03_MANIFEST = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_batch03_20cell_frozen_v1/manifest.json"
)
PROGRESS_V3_MANIFEST = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_frozen_progress_census_v3/manifest.json"
)
PREPARATION = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_formal_classification_preparation_v1/"
    "classification_preparation.csv"
)
TAXONOMY = Path("C:/Users/yehya/Downloads/AI_生成程式共同失敗分類標準_實際使用版_v3.1.md")

SOURCE_HASHES = {
    ROSTER: "0c77a58de44149c17c2dd33ed310c2ef4e6b81b357874eb9ab21157e59b2ecae",
    ROSTER_MANIFEST: "9de720aba72fa5acb134b93785201aacde0482ef817b71ac6ba3739afbe10719",
    REMAINING21: "48647e94065311f5f8376fb9e3e3299b96b8a95176d97a890be90919ff2ed07b",
    ROSTER_AUDIT: "cd11f7da198044968773198cb9e66f057b11fb5285e4a12e1f70c7fb8475f3b7",
    V1_RECORDS: "5f61c4fc90f9200376e85c622f3fd54d4fa2fd6f0829e1606fb52a17a6033624",
    V1_MANIFEST: "6d170aa0e8f1c54cccf10159c42b5c61fad00b133c843749d15efab1a15250e4",
    AUDIT_FINDINGS: "95a7d6927666b8f153db68a39a4f4e3db219aad95ce15f3f340b55a4ce197f53",
    AUDIT_MATERIAL: "17560e5c50ec7147be536c9f8c7d26ce230ae4d912e3f600c0ef7b0169a391b2",
    AUDIT_MANIFEST: "a264dd9b32a33911c2d6ba9fec0bbbb75d7459c3ae5599734b05178ddff46e83",
    V2_RECORDS: "03cf83d8f295815f5f5f66dbdc3eb347556606245e542d052d88d0a50d945028",
    V2_MANIFEST: "b0b41591716133d183b56ae9c4f9254ef726524d06831be0c2b7361f05953681",
    V2_LEDGER: "125f6f367867fea06fc123a81765aabdd7f572a0af8709d966ce86197d6b3bc1",
    V2_EVIDENCE: "85a8ee679816ca931126cec3199139b3523504f7b69b915dad8765ddf2cf362e",
    V2_MECHANISMS: "10c2897809de9b0d86c8cbd9a23955eab199a76711b19e1702548fae553d3a9b",
    V2_GAPS: "76ad7647b3348705e0069da451af73a601014f8e403b73f85b920ceb46feda48",
    V2_CONDITIONAL: "fb82e22dad104d428fbb8e8c66024e742ccdc7c326fffa0e9b6969b6133c1808",
    V2_SUMMARY: "290ce21fbe4a8aa7ba3b4bfc0f63369b499a15595303e86f386cfce7a202869d",
    REAUDIT_FINDINGS: "3ac3a21afa235a147b3e2a6bb3031235111c5a9a9b99c8a9282055605a01a409",
    REAUDIT_APPROVED: "f624064c3b47e7072705f788ddec14751e73a600eb5e64aff43662a028e85239",
    REAUDIT_SUMMARY: "28acc9a6fb118ea4dc2f0b23758a0c8300b2692fd7311f5bceb8b911306a0845",
    REAUDIT_MANIFEST: "4ae6168126c6365200f253dd3e30c2ebe05a2413660612fa9a5955d1faf0251f",
    BATCH01_FROZEN: "8f2410122205610f41d4e7dfbbc4b958d05c1e3da40176b9dc9269880512c0cb",
    BATCH02_FROZEN: "dc6d4a4fa0f0027eb87e3af48b3567c72443255fcda2e2779acf7fe0fbf70f04",
    BATCH03_FROZEN: "d0f59af50c2e433c7d02546da04a3d3802641077b75c649144f953f3c2b4d80f",
    BATCH03_MANIFEST: "af9becc880d45e6969074cf5e2e53e47a3b87b4cbf6a6ecab0cb4b69963f51d9",
    PROGRESS_V3_MANIFEST: "92f076996db37ea4188f83168889c70ea5b7814d6374b2b1f24cdd170760bf1e",
    PREPARATION: "5b0106b93f2d192d89c740659f83021956c15113397f1a54b70e65b7cc7a128c",
    TAXONOMY: "93908ec8e4721f0039acc779fb948988b6c25e712c29890bd98aa7c21a8422a0",
}

AUTH_FIELDS = ("check_id", "expected", "observed", "status", "evidence")
CUMULATIVE_FIELDS = (
    "freeze_order",
    "cell_identity_sha256",
    "program_id",
    "source_sha256",
    "task_id",
    "membership",
)
REGISTRY_FIELDS = (
    "batch_id",
    "cells",
    "unique_program_id",
    "unique_source_sha256",
    "source_revision",
    "source_manifest_sha256",
    "freeze_revision",
    "notes",
)


class FreezeError(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise FreezeError(message)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_csv(repo: Path, path: Path) -> list[dict[str, str]]:
    actual = path if path.is_absolute() else repo / path
    with actual.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


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


def _cell_id(row: dict[str, str]) -> str:
    return row.get("cell_identity_sha256") or row["cell_id"]


def build_payload(repo: Path = REPO_ROOT) -> dict[str, Any]:
    verify_sources(repo)
    v2_manifest = json.loads((repo / V2_MANIFEST).read_text(encoding="utf-8"))
    re_manifest = json.loads((repo / REAUDIT_MANIFEST).read_text(encoding="utf-8"))
    re_summary = json.loads((repo / REAUDIT_SUMMARY).read_text(encoding="utf-8"))
    batch03_manifest = json.loads((repo / BATCH03_MANIFEST).read_text(encoding="utf-8"))
    _require(v2_manifest["verdict"] == "READY_FOR_BATCH04_PROVISIONAL_V2_INDEPENDENT_REAUDIT", "v2 verdict drift")
    _require(re_manifest["verdict"] == FREEZE_BASIS, "reaudit verdict drift")
    _require(re_summary["affirmed"] == 20 and re_summary["material"] == 0 and re_summary["non_material"] == 0, "freeze authorization drift")
    _require(batch03_manifest["total_frozen"] == PREVIOUSLY_FROZEN, "prior frozen count drift")

    records_bytes = (repo / V2_RECORDS).read_bytes()
    evidence_bytes = (repo / V2_EVIDENCE).read_bytes()
    mechanism_bytes = (repo / V2_MECHANISMS).read_bytes()
    gaps_bytes = (repo / V2_GAPS).read_bytes()
    conditional_bytes = (repo / V2_CONDITIONAL).read_bytes()
    remaining21_bytes = (repo / REMAINING21).read_bytes()

    records = _read_csv(repo, V2_RECORDS)
    roster = _read_csv(repo, ROSTER)
    remaining21 = _read_csv(repo, REMAINING21)
    mechanisms = _read_csv(repo, V2_MECHANISMS)
    gaps = _read_csv(repo, V2_GAPS)
    conditional = _read_csv(repo, V2_CONDITIONAL)
    prep = _read_csv(repo, PREPARATION)
    batch01 = _read_csv(repo, BATCH01_FROZEN)
    batch02 = _read_csv(repo, BATCH02_FROZEN)
    batch03 = _read_csv(repo, BATCH03_FROZEN)

    _require(len(records) == len(roster) == 20, "20-cell count drift")
    _require([r["program_id"] for r in records] == [r["program_id"] for r in roster], "program order drift")
    _require(
        [r["cell_identity_sha256"] for r in records] == [r["cell_identity_sha256"] for r in roster],
        "cell identity drift",
    )
    _require([r["source_sha256"] for r in records] == [r["source_sha256"] for r in roster], "source drift")
    _require(len(remaining21) == REMAINING, "remaining21 count drift")
    _require(_sha(remaining21_bytes) == SOURCE_HASHES[REMAINING21], "remaining21 byte drift")

    batch04_cells = {r["cell_identity_sha256"] for r in records}
    batch04_programs = {r["program_id"] for r in records}
    remaining21_cells = {r["cell_identity_sha256"] for r in remaining21}
    recent_frozen_cells = {_cell_id(r) for r in batch01} | {_cell_id(r) for r in batch02} | {_cell_id(r) for r in batch03}
    recent_frozen_programs = (
        {r["program_id"] for r in batch01} | {r["program_id"] for r in batch02} | {r["program_id"] for r in batch03}
    )
    _require(not (batch04_cells & remaining21_cells), "batch04/remaining21 cell intersection")
    _require(not (batch04_cells & recent_frozen_cells), "batch04/prior-batch frozen cell intersection")
    _require(not (batch04_programs & recent_frozen_programs), "batch04/prior-batch program intersection")
    _require(len(batch04_cells) == 20 and len(batch04_programs) == 20, "duplicate cell/program drift")

    prep_cells = {r["cell_identity_sha256"] for r in prep}
    _require(len(prep) == len(prep_cells) == FORMAL_POPULATION, "formal population drift")
    remaining41_cells = batch04_cells | remaining21_cells
    _require(len(remaining41_cells) == 41, "remaining41 closure drift")
    prior_frozen_cells = prep_cells - remaining41_cells
    _require(len(prior_frozen_cells) == PREVIOUSLY_FROZEN, f"prior frozen set drift: {len(prior_frozen_cells)}")
    _require(not (batch04_cells & prior_frozen_cells), "batch04/prior157 intersection drift")
    cumulative_cells = prior_frozen_cells | batch04_cells
    _require(len(cumulative_cells) == TOTAL_FROZEN, "cumulative frozen set drift")
    _require(cumulative_cells | remaining21_cells == prep_cells, "198=177+21 set closure drift")
    _require(len(cumulative_cells & remaining21_cells) == 0, "frozen/remaining overlap drift")

    primary = Counter(r["primary_layer"] for r in records)
    secondary = Counter(r["secondary_layer"] or "empty" for r in records)
    confidence = Counter(r["confidence"] for r in records)
    outcome = Counter(r["outcome_validity"] for r in records)
    healer = Counter(r["healer_eligibility"] for r in records)
    mechanism_counts = Counter(r["mechanism_tag"] for r in mechanisms)
    _require(primary == Counter({"L5": 10, "UNRESOLVED": 9, "L4": 1}), "primary statistics drift")
    _require(secondary == Counter({"empty": 19, "L5": 1}), "secondary statistics drift")
    _require(confidence == Counter({"HIGH": 11, "LOW": 9}), "confidence statistics drift")
    _require(outcome == Counter({"VALID_MODEL_OUTCOME": 20}), "outcome statistics drift")
    _require(healer == Counter({"abstain": 20}), "healer statistics drift")
    _require(
        mechanism_counts["frequency_one_instead_of_distinct_value"] == 1
        and mechanism_counts["dedupe_instead_of_unique_occurrence"] == 0
        and mechanism_counts["semantic_goal_drift"] == 3,
        "mechanism statistics drift",
    )
    _require(len(gaps) == 9 and len(conditional) == 0, "gap/conditional drift")
    _require(len({r["source_sha256"] for r in records}) == 19, "unique source drift")
    shared = [r for r in records if r["batch_rank"] in {"5", "12"}]
    _require(
        len({r["source_sha256"] for r in shared}) == 1 and len({r["cell_identity_sha256"] for r in shared}) == 2,
        "legal shared source drift",
    )

    prep_by_cell = {r["cell_identity_sha256"]: r for r in prep}
    cumulative_rows = []
    for index, cell in enumerate(sorted(cumulative_cells), start=1):
        row = prep_by_cell[cell]
        membership = "batch04_newly_frozen" if cell in batch04_cells else "previously_frozen"
        cumulative_rows.append(
            {
                "freeze_order": str(index),
                "cell_identity_sha256": cell,
                "program_id": row["program_id"],
                "source_sha256": row["evaluation_source_sha256"],
                "task_id": row["task_id"],
                "membership": membership,
            }
        )
    _require(len(cumulative_rows) == TOTAL_FROZEN, "cumulative ledger count drift")
    _require(sum(r["membership"] == "batch04_newly_frozen" for r in cumulative_rows) == 20, "new membership drift")

    stats = {
        "primary": dict(sorted(primary.items())),
        "secondary": dict(sorted(secondary.items())),
        "confidence": dict(sorted(confidence.items())),
        "outcome": dict(sorted(outcome.items())),
        "healer": {"eligible": 0, "conditional": 0, "abstain": 20},
        "mechanisms": dict(sorted(mechanism_counts.items())),
    }
    authorization = [
        {
            "check_id": "reaudit_verdict",
            "expected": FREEZE_BASIS,
            "observed": re_manifest["verdict"],
            "status": "PASS",
            "evidence": REAUDIT_MANIFEST.as_posix(),
        },
        {
            "check_id": "reaudit_affirmed",
            "expected": "20",
            "observed": str(re_summary["affirmed"]),
            "status": "PASS",
            "evidence": REAUDIT_SUMMARY.as_posix(),
        },
        {
            "check_id": "reaudit_material",
            "expected": "0",
            "observed": str(re_summary["material"]),
            "status": "PASS",
            "evidence": REAUDIT_SUMMARY.as_posix(),
        },
        {
            "check_id": "records_byte_identity",
            "expected": SOURCE_HASHES[V2_RECORDS],
            "observed": _sha(records_bytes),
            "status": "PASS",
            "evidence": V2_RECORDS.as_posix(),
        },
        {
            "check_id": "prior157_intersection_empty",
            "expected": "0",
            "observed": "0",
            "status": "PASS",
            "evidence": PREPARATION.as_posix(),
        },
        {
            "check_id": "remaining21_unchanged",
            "expected": SOURCE_HASHES[REMAINING21],
            "observed": _sha(remaining21_bytes),
            "status": "PASS",
            "evidence": REMAINING21.as_posix(),
        },
        {
            "check_id": "set_closure_198",
            "expected": "198=177+21",
            "observed": f"{FORMAL_POPULATION}={TOTAL_FROZEN}+{REMAINING}",
            "status": "PASS",
            "evidence": PREPARATION.as_posix(),
        },
    ]
    summary = {
        "revision": OUTPUT_RELATIVE.name,
        "status": STATUS,
        "verdict": VERDICT,
        "cells": 20,
        "freeze_basis": FREEZE_BASIS,
        "freeze_authorized": True,
        "reaudit_affirmed": 20,
        "reaudit_material": 0,
        "previously_frozen": PREVIOUSLY_FROZEN,
        "newly_frozen": NEWLY_FROZEN,
        "total_frozen": TOTAL_FROZEN,
        "remaining": REMAINING,
        "formal_population": FORMAL_POPULATION,
        "reconciliation": f"{FORMAL_POPULATION}={TOTAL_FROZEN}+{REMAINING}",
        "unique_program_id": 20,
        "unique_cell_identity": 20,
        "unique_source_sha256": 19,
        "rank5_rank12_legal_shared_source": True,
        "intersection_with_prior157": 0,
        "duplicate_cells": 0,
        "statistics": stats,
        "frozen_records_byte_identical_to_v2": True,
        "eligible_zero_is_formal_safety_result": True,
        "verified_healer_rescues_claimed": 0,
        "remaining21_unchanged": True,
        "batch05_started": False,
        "upstream_modified": False,
    }
    return {
        "records_bytes": records_bytes,
        "evidence_bytes": evidence_bytes,
        "mechanism_bytes": mechanism_bytes,
        "gaps_bytes": gaps_bytes,
        "conditional_bytes": conditional_bytes,
        "remaining21_bytes": remaining21_bytes,
        "authorization": authorization,
        "summary": summary,
        "cumulative_rows": cumulative_rows,
        "stats": stats,
    }


def _freeze_report(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Frozen Batch04：Candidate B r003 taxonomy v3.1",
            "",
            f"**狀態：`{STATUS}`**",
            "",
            "Batch04共有20格，frozen records與provisional v2逐byte一致。",
            "",
            "- 1格primary L4且secondary L5，因此Healer abstain",
            "- 10格primary L5",
            "- 9格因現有靜態證據不足而UNRESOLVED",
            "- eligible=0不是搜尋失敗，而是安全標準下的正式結果",
            "- 本批不得用來宣稱Healer有成功修復案例",
            "",
            f"- Primary：{summary['statistics']['primary']}",
            f"- Secondary：{summary['statistics']['secondary']}",
            f"- Confidence：{summary['statistics']['confidence']}",
            f"- Outcome：{summary['statistics']['outcome']}",
            f"- Healer：{summary['statistics']['healer']}",
            f"- 累計凍結：{summary['previously_frozen']}+{summary['newly_frozen']}={summary['total_frozen']}",
            f"- 集合閉合：{summary['reconciliation']}",
            "",
            "本freeze未重新分類、重新審查或執行candidate、tests、diagnostics、Healer或模型；",
            "remaining21逐byte不變；未開始Batch05。",
            "",
        ]
    )


def _progress_report(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Taxonomy v3.1 frozen progress census v4",
            "",
            f"**狀態：`{PROGRESS_STATUS}`**",
            "",
            "## 總進度",
            "",
            f"- formal population={FORMAL_POPULATION}",
            f"- previously frozen={PREVIOUSLY_FROZEN}",
            f"- newly frozen this revision={NEWLY_FROZEN}（Batch04）",
            f"- total frozen={TOTAL_FROZEN}",
            f"- remaining={REMAINING}",
            f"- reconciliation：{FORMAL_POPULATION}={TOTAL_FROZEN}+{REMAINING}",
            "",
            "## 邊界",
            "",
            "- 本 census 為新的 immutable progress revision，不覆寫 progress v3",
            "- remaining21 已保存且逐byte不變",
            "- 未開始 Batch05／Final roster",
            "",
            f"- Batch04 statistics：{summary['statistics']}",
            "",
        ]
    )


def build_outputs(repo: Path = REPO_ROOT) -> dict[str, dict[str, bytes]]:
    payload = build_payload(repo)
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
    freeze_outputs = {
        "frozen_adjudication_records.csv": payload["records_bytes"],
        "frozen_per_cell_evidence_ledger.csv": payload["evidence_bytes"],
        "frozen_mechanism_ledger.csv": payload["mechanism_bytes"],
        "frozen_unresolved_evidence_gaps.csv": payload["gaps_bytes"],
        "frozen_conditional_queue.csv": payload["conditional_bytes"],
        "frozen_summary.json": _json_bytes(payload["summary"]),
        "freeze_authorization_closure_ledger.csv": _csv_bytes(AUTH_FIELDS, payload["authorization"]),
        "report_zh.md": _freeze_report(payload["summary"]).encode("utf-8"),
        "execution_counts.json": _json_bytes(execution),
    }
    freeze_provenance = {
        **payload["summary"],
        **execution,
        "start_head": START_HEAD,
        "provenance_chain": [
            {"stage": "roster", "sha256": SOURCE_HASHES[ROSTER]},
            {"stage": "roster_audit", "sha256": SOURCE_HASHES[ROSTER_AUDIT]},
            {"stage": "provisional_v1", "sha256": SOURCE_HASHES[V1_RECORDS]},
            {"stage": "v1_independent_audit", "sha256": SOURCE_HASHES[AUDIT_MANIFEST]},
            {"stage": "provisional_v2", "sha256": SOURCE_HASHES[V2_RECORDS]},
            {"stage": "v2_independent_reaudit", "sha256": SOURCE_HASHES[REAUDIT_MANIFEST]},
            {"stage": "frozen_batch04"},
        ],
        "source_hashes": {path.as_posix(): digest for path, digest in SOURCE_HASHES.items()},
        "no_new_adjudication": True,
        "batch05_started": False,
    }
    freeze_outputs["provenance.json"] = _json_bytes(freeze_provenance)
    sha_ledger = {
        "taxonomy_sha256": SOURCE_HASHES[TAXONOMY],
        "roster_sha256": SOURCE_HASHES[ROSTER],
        "remaining21_sha256": SOURCE_HASHES[REMAINING21],
        "provisional_v2_records_sha256": SOURCE_HASHES[V2_RECORDS],
        "provisional_v2_manifest_sha256": SOURCE_HASHES[V2_MANIFEST],
        "reaudit_findings_sha256": SOURCE_HASHES[REAUDIT_FINDINGS],
        "reaudit_approved_change_sha256": SOURCE_HASHES[REAUDIT_APPROVED],
        "reaudit_manifest_sha256": SOURCE_HASHES[REAUDIT_MANIFEST],
        "frozen_records_sha256": _sha(payload["records_bytes"]),
    }
    freeze_outputs["sha_ledger.json"] = _json_bytes(sha_ledger)
    freeze_manifest = {
        "revision": OUTPUT_RELATIVE.as_posix(),
        "status": STATUS,
        "verdict": VERDICT,
        "start_head": START_HEAD,
        "cells": 20,
        "freeze_basis_verdict": FREEZE_BASIS,
        "freeze_authorized": True,
        "reaudit_affirmed": 20,
        "reaudit_material": 0,
        "frozen_records_byte_identical_to_v2": True,
        "frozen_records_sha256": _sha(payload["records_bytes"]),
        "provisional_v2_records_sha256": SOURCE_HASHES[V2_RECORDS],
        "provisional_v2_manifest_sha256": SOURCE_HASHES[V2_MANIFEST],
        "reaudit_manifest_sha256": SOURCE_HASHES[REAUDIT_MANIFEST],
        "previously_frozen": PREVIOUSLY_FROZEN,
        "newly_frozen": NEWLY_FROZEN,
        "total_frozen": TOTAL_FROZEN,
        "remaining": REMAINING,
        "formal_population": FORMAL_POPULATION,
        "outputs_sha256_excluding_manifest": {name: _sha(data) for name, data in freeze_outputs.items()},
        **execution,
    }
    freeze_outputs["manifest.json"] = _json_bytes(freeze_manifest)

    cumulative_bytes = _csv_bytes(CUMULATIVE_FIELDS, payload["cumulative_rows"])
    registry_rows = [
        {
            "batch_id": "batch01_through_batch03_prior157",
            "cells": str(PREVIOUSLY_FROZEN),
            "unique_program_id": str(PREVIOUSLY_FROZEN),
            "unique_source_sha256": "",
            "source_revision": "prior_frozen_set_via_preparation_minus_remaining41",
            "source_manifest_sha256": SOURCE_HASHES[BATCH03_MANIFEST],
            "freeze_revision": BATCH03_FROZEN.parent.name,
            "notes": "Prior 157 identities = preparation 198 minus remaining41",
        },
        {
            "batch_id": "remaining41_batch04_20",
            "cells": "20",
            "unique_program_id": "20",
            "unique_source_sha256": "19",
            "source_revision": V2_DIR.name,
            "source_manifest_sha256": SOURCE_HASHES[V2_MANIFEST],
            "freeze_revision": OUTPUT_RELATIVE.name,
            "notes": "Batch04 freeze; remaining21 unchanged; Batch05 not started",
        },
    ]
    progress_summary = {
        "revision": PROGRESS_OUTPUT.name,
        "status": PROGRESS_STATUS,
        "formal_population": FORMAL_POPULATION,
        "previously_frozen": PREVIOUSLY_FROZEN,
        "newly_frozen": NEWLY_FROZEN,
        "total_frozen": TOTAL_FROZEN,
        "remaining": REMAINING,
        "reconciliation": f"{FORMAL_POPULATION}={TOTAL_FROZEN}+{REMAINING}",
        "batch04_frozen_cells": NEWLY_FROZEN,
        "batch04_roster_sha256": SOURCE_HASHES[ROSTER],
        "batch04_freeze_revision": OUTPUT_RELATIVE.name,
        "batch04_freeze_basis_verdict": FREEZE_BASIS,
        "batch04_primary_layer_distribution": payload["stats"]["primary"],
        "batch04_secondary_layer_distribution": payload["stats"]["secondary"],
        "batch04_healer_eligibility_distribution": payload["stats"]["healer"],
        "remaining21_sha256": SOURCE_HASHES[REMAINING21],
        "remaining21_unchanged": True,
        "batch05_started": False,
        "overwrites_prior_census": False,
        "cumulative_frozen_identity_rows": TOTAL_FROZEN,
    }
    progress_outputs = {
        "cumulative_frozen_identity_ledger.csv": cumulative_bytes,
        "batch_registry.csv": _csv_bytes(REGISTRY_FIELDS, registry_rows),
        "frozen_progress_summary.json": _json_bytes(progress_summary),
        "frozen_progress_report_zh.md": _progress_report(payload["summary"]).encode("utf-8"),
        "execution_counts.json": _json_bytes(execution),
    }
    progress_provenance = {
        **progress_summary,
        **execution,
        "start_head": START_HEAD,
        "source_hashes": {
            ROSTER.as_posix(): SOURCE_HASHES[ROSTER],
            REMAINING21.as_posix(): SOURCE_HASHES[REMAINING21],
            V2_RECORDS.as_posix(): SOURCE_HASHES[V2_RECORDS],
            REAUDIT_MANIFEST.as_posix(): SOURCE_HASHES[REAUDIT_MANIFEST],
            PREPARATION.as_posix(): SOURCE_HASHES[PREPARATION],
            PROGRESS_V3_MANIFEST.as_posix(): SOURCE_HASHES[PROGRESS_V3_MANIFEST],
            BATCH03_MANIFEST.as_posix(): SOURCE_HASHES[BATCH03_MANIFEST],
        },
        "does_not_modify_progress_v3": True,
    }
    progress_outputs["provenance.json"] = _json_bytes(progress_provenance)
    progress_manifest = {
        "revision": PROGRESS_OUTPUT.as_posix(),
        "status": PROGRESS_STATUS,
        "formal_population": FORMAL_POPULATION,
        "previously_frozen": PREVIOUSLY_FROZEN,
        "newly_frozen": NEWLY_FROZEN,
        "total_frozen": TOTAL_FROZEN,
        "remaining": REMAINING,
        "freeze_basis_verdict": FREEZE_BASIS,
        "freeze_revision": OUTPUT_RELATIVE.name,
        "remaining21_sha256": SOURCE_HASHES[REMAINING21],
        "cumulative_frozen_identity_ledger_sha256": _sha(cumulative_bytes),
        "batch05_started": False,
        "overwrites_prior_census": False,
        "outputs_sha256_excluding_manifest": {name: _sha(data) for name, data in progress_outputs.items()},
        **execution,
    }
    progress_outputs["manifest.json"] = _json_bytes(progress_manifest)
    return {"freeze": freeze_outputs, "progress": progress_outputs}


def write_outputs(repo: Path = REPO_ROOT) -> tuple[Path, Path]:
    bundles = build_outputs(repo)
    freeze_path = repo / OUTPUT_RELATIVE
    progress_path = repo / PROGRESS_OUTPUT
    freeze_path.mkdir(parents=True, exist_ok=True)
    progress_path.mkdir(parents=True, exist_ok=True)
    for name, data in bundles["freeze"].items():
        (freeze_path / name).write_bytes(data)
    for name, data in bundles["progress"].items():
        (progress_path / name).write_bytes(data)
    return freeze_path, progress_path


def main() -> None:
    freeze_path, progress_path = write_outputs()
    freeze_manifest = json.loads((freeze_path / "manifest.json").read_text(encoding="utf-8"))
    progress_manifest = json.loads((progress_path / "manifest.json").read_text(encoding="utf-8"))
    print(f"wrote {freeze_path}")
    print(f"wrote {progress_path}")
    print(f"frozen_records_sha256={freeze_manifest['frozen_records_sha256']}")
    print(f"freeze_manifest_sha256={_sha((freeze_path / 'manifest.json').read_bytes())}")
    print(
        "cumulative_records_sha256="
        f"{progress_manifest['cumulative_frozen_identity_ledger_sha256']}"
    )
    print(f"progress_manifest_sha256={_sha((progress_path / 'manifest.json').read_bytes())}")
    print(f"verdict={freeze_manifest['verdict']}")


if __name__ == "__main__":
    main()
