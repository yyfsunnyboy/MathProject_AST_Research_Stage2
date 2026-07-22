#!/usr/bin/env python3
"""Freeze Final Batch05 v2 and close the immutable 198-cell taxonomy set."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
FREEZE_OUTPUT = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_final_batch05_21cell_frozen_v1")
CLOSURE_OUTPUT = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_complete_198cell_closure_v1")
START_HEAD = "1aa7b692c4d499ada2e0b6e0799b3475f2f68b18"
FREEZE_STATUS = "FORMALLY_FROZEN_FINAL_BATCH05_PROVISIONAL_V2"
CLOSURE_STATUS = "COMPLETE_198_CELL_TAXONOMY_SET_CLOSED"
VERDICT = "FINAL_BATCH05_FROZEN_198_CELL_TAXONOMY_CLOSED"
FREEZE_BASIS = "READY_TO_FREEZE_FINAL_BATCH05_PROVISIONAL_V2"

PREVIOUSLY_FROZEN = 177
NEWLY_FROZEN = 21
TOTAL_FROZEN = 198
REMAINING = 0

TAXONOMY = Path("C:/Users/yehya/Downloads/AI_生成程式共同失敗分類標準_實際使用版_v3.1.md")
BATCH04_FROZEN = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_batch04_20cell_frozen_v1/frozen_adjudication_records.csv")
BATCH04_MANIFEST = BATCH04_FROZEN.with_name("manifest.json")
FROZEN177 = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_frozen_progress_census_v4/cumulative_frozen_identity_ledger.csv")
FROZEN177_MANIFEST = FROZEN177.with_name("manifest.json")
REMAINING21 = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_remaining41_batch04_20cell_roster_v1/remaining21_roster.csv")
ROSTER = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_final_batch05_21cell_roster_v1/batch05_roster.csv")
ROSTER_MANIFEST = ROSTER.with_name("manifest.json")
ROSTER_AUDIT_MANIFEST = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_final_batch05_21cell_roster_v1_independent_audit_v1/manifest.json")
V1_RECORDS = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_final_batch05_21cell_provisional_v1/adjudication_records.csv")
V1_AUDIT_MANIFEST = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_final_batch05_21cell_provisional_v1_independent_audit_v1/manifest.json")
V2_DIR = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_final_batch05_21cell_provisional_v2")
V2_RECORDS = V2_DIR / "adjudication_records.csv"
V2_MANIFEST = V2_DIR / "manifest.json"
V2_DIFFERENCES = V2_DIR / "approved_difference_ledger.csv"
V2_MECHANISMS = V2_DIR / "mechanism_ledger.csv"
V2_CHAINS = V2_DIR / "failure_chain_ledger.csv"
V2_GAPS = V2_DIR / "unresolved_evidence_gaps.csv"
V2_SUMMARY = V2_DIR / "adjudication_summary.json"
REAUDIT_DIR = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_final_batch05_21cell_provisional_v2_independent_reaudit_v1")
REAUDIT_FINDINGS = REAUDIT_DIR / "per_cell_v2_reaudit_findings.csv"
REAUDIT_APPROVED = REAUDIT_DIR / "approved_change_verification.csv"
REAUDIT_SUMMARY = REAUDIT_DIR / "reaudit_summary.json"
REAUDIT_MANIFEST = REAUDIT_DIR / "manifest.json"
PREPARATION = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v3_formal_classification_preparation_v1/classification_preparation.csv")

SOURCE_HASHES = {
    TAXONOMY: "93908ec8e4721f0039acc779fb948988b6c25e712c29890bd98aa7c21a8422a0",
    BATCH04_FROZEN: "03cf83d8f295815f5f5f66dbdc3eb347556606245e542d052d88d0a50d945028",
    BATCH04_MANIFEST: "b56f1796c9b97bdbb854a5699dcdce38326c26300d9ad7bb8411c9d0499e5ea4",
    FROZEN177: "d91c7d7f215f9e4a086aaa806958d1f8782686f0e0f71f2fa0df6a6c025f9422",
    FROZEN177_MANIFEST: "ba024d82aa7f2c6b8af4790fbc503b962c406ea258314981a43e1bed9d94b68f",
    REMAINING21: "48647e94065311f5f8376fb9e3e3299b96b8a95176d97a890be90919ff2ed07b",
    ROSTER: "4ec24e450a66c50db46230a5b950137af6e6a4cb3d9a067f182a545818851764",
    ROSTER_MANIFEST: "b48500bf4be94e00ec9e836c21ff72cce7218476660b231785357b383b05731e",
    ROSTER_AUDIT_MANIFEST: "bb1603b8eeaf9890a85d13291628f7985cc67bfbdc2d3221f39328295e506312",
    V1_RECORDS: "ab6b389c1c9d04d72e6bed6a415b422eb222f9b4a8a1cec238ba2af6c34c291c",
    V1_AUDIT_MANIFEST: "5cef1a885e710ede709d97c02d7bb261c8ad2a979b233790a1f81a4d86f6705c",
    V2_RECORDS: "22faba56d483e172064338f2649533e4758bfd1110e64467d8ce6eff2a47cf34",
    V2_MANIFEST: "326604be78641011c7121c157dfc5c0ba2c1082dfcd1228c078bf1c67685a595",
    V2_DIFFERENCES: "0d575930ee91d521e3ae2d11a3b989e578d922da9185744cf5b9915915acef01",
    V2_MECHANISMS: "5598e35524a33371e4aca38697e5cf51c9e4264cd2e4e38490419e4e13cf4fa2",
    V2_CHAINS: "d397088f5c067a4cefad360dc5ea4cb34a66c0fee227cc90961ba635007dd025",
    V2_GAPS: "72866c3b068c76576c3744b06bdf61d7d8b87d28af1ac0285ebfbd9e6df44ee7",
    V2_SUMMARY: "d4e0e3abbab18e492af1d11b8b122cecf63449d6f598f8d87d012a6e72e92596",
    REAUDIT_FINDINGS: "012edbcdaccda0331c7fafd5677e65f4ec1dc8e1794aa32508ae2ddac0e77588",
    REAUDIT_APPROVED: "6c612033b0c5e93ffb63595659ad4176e148f2a2b5df5532225f20cb940ba03d",
    REAUDIT_SUMMARY: "8631d257f4e128cd6f7853d52745ac68421ba359dc736697ccfb6f9d6f2f3cc9",
    REAUDIT_MANIFEST: "bbd6a216717b6229537faf1bc1d3158737db861c22f8d9a8f63a818b760410be",
    PREPARATION: "5b0106b93f2d192d89c740659f83021956c15113397f1a54b70e65b7cc7a128c",
}

AUTH_FIELDS = ("check_id", "expected", "observed", "status", "evidence")
CUMULATIVE_FIELDS = (
    "freeze_order", "cell_identity_sha256", "program_id", "source_sha256", "task_id", "membership",
)
REGISTRY_FIELDS = (
    "batch_id", "cells", "freeze_order_range", "unique_program_id", "unique_cell_identity",
    "unique_source_sha256", "source_revision", "source_manifest_sha256", "notes",
)


class FreezeError(RuntimeError):
    pass


def _require(value: bool, message: str) -> None:
    if not value:
        raise FreezeError(message)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _path(repo: Path, value: Path) -> Path:
    return value if value.is_absolute() else repo / value


def _read_csv(repo: Path, value: Path) -> list[dict[str, str]]:
    with _path(repo, value).open(encoding="utf-8", newline="") as handle:
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
    for relative, digest in SOURCE_HASHES.items():
        path = _path(repo, relative)
        _require(path.is_file(), f"missing upstream: {relative.as_posix()}")
        _require(_sha(path.read_bytes()) == digest, f"upstream byte drift: {relative.as_posix()}")


def build_payload(repo: Path = REPO_ROOT) -> dict[str, Any]:
    verify_sources(repo)
    records_bytes = _path(repo, V2_RECORDS).read_bytes()
    mechanisms_bytes = _path(repo, V2_MECHANISMS).read_bytes()
    chains_bytes = _path(repo, V2_CHAINS).read_bytes()
    gaps_bytes = _path(repo, V2_GAPS).read_bytes()
    differences_bytes = _path(repo, V2_DIFFERENCES).read_bytes()
    records = _read_csv(repo, V2_RECORDS)
    mechanisms = _read_csv(repo, V2_MECHANISMS)
    roster = _read_csv(repo, ROSTER)
    remaining21 = _read_csv(repo, REMAINING21)
    old_cumulative = _read_csv(repo, FROZEN177)
    preparation = _read_csv(repo, PREPARATION)
    findings = _read_csv(repo, REAUDIT_FINDINGS)
    re_summary = json.loads(_path(repo, REAUDIT_SUMMARY).read_text(encoding="utf-8"))
    re_manifest = json.loads(_path(repo, REAUDIT_MANIFEST).read_text(encoding="utf-8"))
    _require(_sha(records_bytes) == SOURCE_HASHES[V2_RECORDS], "v2 records byte drift")
    _require(re_manifest["verdict"] == FREEZE_BASIS, "freeze authorization verdict drift")
    _require(re_summary["affirmed"] == 21 and re_summary["non_material"] == re_summary["material"] == 0, "reaudit authorization drift")
    _require(len(findings) == 21 and all(row["reaudit_status"] == "AFFIRMED" for row in findings), "21/21 re-audit findings drift")
    _require(len(records) == len(roster) == len(remaining21) == 21, "Batch05 count drift")
    _require([row["program_id"] for row in records] == [row["program_id"] for row in roster] == [row["program_id"] for row in remaining21], "Batch05 program/order drift")
    _require([row["cell_identity_sha256"] for row in records] == [row["cell_identity_sha256"] for row in roster] == [row["cell_identity_sha256"] for row in remaining21], "Batch05 cell/order drift")
    _require([row["source_sha256"] for row in records] == [row["source_sha256"] for row in roster] == [row["source_sha256"] for row in remaining21], "Batch05 source/order drift")

    primary = Counter(row["primary_layer"] for row in records)
    secondary = Counter(row["secondary_layer"] or "empty" for row in records)
    confidence = Counter(row["confidence"] for row in records)
    outcome = Counter(row["outcome_validity"] for row in records)
    healer = Counter(row["healer_eligibility"] for row in records)
    mechanism_counts = Counter(row["mechanism_tag"] for row in mechanisms)
    _require(primary == {"L5": 10, "UNRESOLVED": 11}, "primary stats drift")
    _require(secondary == {"empty": 21} and confidence == {"HIGH": 10, "LOW": 11}, "secondary/confidence stats drift")
    _require(outcome == {"VALID_MODEL_OUTCOME": 21} and healer == {"abstain": 21}, "outcome/healer stats drift")
    _require(mechanism_counts["algorithm_reconstruction_required"] == 9, "algorithm reconstruction tag drift")
    rank17_tags = {tag["tag"] for tag in json.loads(records[16]["mechanism_tags_json"])}
    _require(rank17_tags == {"end_index_off_by_one", "wrong_boundary_condition"}, "rank17 frozen tag drift")

    batch_programs = {row["program_id"] for row in records}
    batch_cells = {row["cell_identity_sha256"] for row in records}
    batch_sources = {row["source_sha256"] for row in records}
    _require(len(batch_programs) == len(batch_cells) == 21 and len(batch_sources) == 20, "Batch05 uniqueness drift")
    shared = [row for row in records if row["batch_rank"] in {"5", "21"}]
    _require(len(shared) == 2 and len({row["source_sha256"] for row in shared}) == 1 and len({row["cell_identity_sha256"] for row in shared}) == 2, "legal shared source drift")

    _require(len(old_cumulative) == 177, "frozen177 row drift")
    _require([row["freeze_order"] for row in old_cumulative] == [str(i) for i in range(1, 178)], "frozen177 order drift")
    old_programs = {row["program_id"] for row in old_cumulative}
    old_cells = {row["cell_identity_sha256"] for row in old_cumulative}
    _require(len(old_programs) == len(old_cells) == 177, "frozen177 uniqueness drift")
    _require(old_programs.isdisjoint(batch_programs) and old_cells.isdisjoint(batch_cells), "frozen177/Batch05 overlap")
    cumulative = [dict(row) for row in old_cumulative]
    for rank, row in enumerate(records, 1):
        cumulative.append({
            "freeze_order": str(PREVIOUSLY_FROZEN + rank),
            "cell_identity_sha256": row["cell_identity_sha256"],
            "program_id": row["program_id"], "source_sha256": row["source_sha256"],
            "task_id": row["task_id"], "membership": "final_batch05_newly_frozen",
        })
    _require(len(cumulative) == 198 and [row["freeze_order"] for row in cumulative] == [str(i) for i in range(1, 199)], "cumulative198 order/count drift")
    cumulative_programs = {row["program_id"] for row in cumulative}
    cumulative_cells = {row["cell_identity_sha256"] for row in cumulative}
    cumulative_sources = {row["source_sha256"] for row in cumulative}
    _require(len(cumulative_programs) == len(cumulative_cells) == 198, "cumulative198 identity uniqueness drift")
    prep_programs = {row["program_id"] for row in preparation}
    prep_cells = {row["cell_identity_sha256"] for row in preparation}
    _require(len(preparation) == len(prep_programs) == len(prep_cells) == 198, "formal198 identity drift")
    _require(cumulative_programs == prep_programs and cumulative_cells == prep_cells, "formal198/cumulative198 omission drift")
    _require(sum(row["membership"] == "final_batch05_newly_frozen" for row in cumulative) == 21, "Batch05 cumulative membership drift")

    stats = {
        "primary": dict(sorted(primary.items())), "secondary": dict(sorted(secondary.items())),
        "confidence": dict(sorted(confidence.items())), "outcome": dict(sorted(outcome.items())),
        "healer": {"eligible": 0, "conditional": 0, "abstain": 21},
        "mechanisms": dict(sorted(mechanism_counts.items())),
    }
    authorization = [
        {"check_id": "reaudit_verdict", "expected": FREEZE_BASIS, "observed": re_manifest["verdict"], "status": "PASS", "evidence": REAUDIT_MANIFEST.as_posix()},
        {"check_id": "reaudit_affirmed", "expected": "21", "observed": str(re_summary["affirmed"]), "status": "PASS", "evidence": REAUDIT_SUMMARY.as_posix()},
        {"check_id": "reaudit_material", "expected": "0", "observed": str(re_summary["material"]), "status": "PASS", "evidence": REAUDIT_SUMMARY.as_posix()},
        {"check_id": "records_byte_identity", "expected": SOURCE_HASHES[V2_RECORDS], "observed": _sha(records_bytes), "status": "PASS", "evidence": V2_RECORDS.as_posix()},
        {"check_id": "rank17_tags", "expected": "end_index_off_by_one,wrong_boundary_condition", "observed": ",".join(sorted(rank17_tags)), "status": "PASS", "evidence": V2_RECORDS.as_posix()+"#batch_rank=17"},
        {"check_id": "set_closure", "expected": "198=177+21", "observed": "198=177+21", "status": "PASS", "evidence": FROZEN177.as_posix()+" + "+V2_RECORDS.as_posix()},
        {"check_id": "unfrozen_remaining", "expected": "0", "observed": "0", "status": "PASS", "evidence": PREPARATION.as_posix()},
    ]
    freeze_summary = {
        "revision": FREEZE_OUTPUT.name, "status": FREEZE_STATUS, "verdict": VERDICT,
        "cells": 21, "freeze_basis": FREEZE_BASIS, "freeze_authorized": True,
        "reaudit_affirmed": 21, "reaudit_non_material": 0, "reaudit_material": 0,
        "frozen_records_byte_identical_to_v2": True,
        "previously_frozen": 177, "newly_frozen": 21, "total_frozen": 198,
        "remaining": 0, "reconciliation": "198=177+21",
        "unique_program_id": 21, "unique_cell_identity": 21, "unique_source_sha256": 20,
        "rank5_rank21_legal_shared_source": True, "intersection_with_frozen177": 0,
        "statistics": stats, "upstream_modified": False,
    }
    closure_summary = {
        "revision": CLOSURE_OUTPUT.name, "status": CLOSURE_STATUS, "verdict": VERDICT,
        "formal_population": 198, "previously_frozen": 177, "batch05_newly_frozen": 21,
        "total_frozen": 198, "unfrozen_remaining": 0, "reconciliation": "198=177+21",
        "unique_program_id": len(cumulative_programs), "unique_cell_identity": len(cumulative_cells),
        "unique_source_sha256": len(cumulative_sources), "overlap_frozen177_batch05": 0,
        "duplicate_programs": 0, "duplicate_cells": 0, "omitted_programs": 0, "omitted_cells": 0,
        "frozen177_order_preserved": True, "batch05_rank_order_appended": True,
        "batch05_freeze_order_range": "178-198", "remaining": 0,
        "upstream_frozen177_modified": False, "research_synthesis_created": False,
    }
    return {
        "records_bytes": records_bytes, "mechanisms_bytes": mechanisms_bytes,
        "chains_bytes": chains_bytes, "gaps_bytes": gaps_bytes,
        "differences_bytes": differences_bytes, "authorization": authorization,
        "freeze_summary": freeze_summary, "closure_summary": closure_summary,
        "cumulative": cumulative, "stats": stats,
    }


def _freeze_report(summary: dict[str, Any]) -> str:
    return (
        "# Frozen Final Batch05：Candidate B r003 taxonomy v3.1\n\n"
        f"**狀態：`{FREEZE_STATUS}`**\n\n"
        "- Batch05共21格；frozen records與provisional v2逐byte一致。\n"
        "- Primary：L5=10、UNRESOLVED=11；Secondary empty=21。\n"
        "- Confidence：HIGH=10、LOW=11；VALID_MODEL_OUTCOME=21。\n"
        "- Healer：eligible=0、conditional=0、abstain=21。\n"
        "- algorithm_reconstruction_required=9；rank 17只保留end_index_off_by_one與wrong_boundary_condition。\n"
        "- 198=177+21；未凍結剩餘=0。\n"
        "- 本freeze未重新裁決，所有執行計數為0。\n"
    )


def _closure_report(summary: dict[str, Any]) -> str:
    return (
        "# Candidate B r003 taxonomy v3.1：198-cell complete closure\n\n"
        f"**狀態：`{CLOSURE_STATUS}`**\n\n"
        "- 198=既有frozen177+Final Batch05 frozen21。\n"
        "- program identity=198 unique；cell identity=198 unique。\n"
        f"- source identity={summary['unique_source_sha256']} unique（依權威records重建）。\n"
        "- frozen177與Batch05 overlap=0；duplicate=0；omission=0。\n"
        "- frozen177既有順序保留；Batch05 rank 1–21追加為freeze order 178–198。\n"
        "- 未凍結剩餘=0；本revision不包含198格研究統整。\n"
    )


def build_outputs(repo: Path = REPO_ROOT) -> dict[str, dict[str, bytes]]:
    payload = build_payload(repo)
    execution = {
        "model_calls": 0, "candidate_executions": 0, "candidate_imports": 0,
        "candidate_test_executions": 0, "public_test_executions": 0,
        "hidden_test_executions": 0, "evalplus_correctness_executions": 0,
        "diagnostics_executions": 0, "validation_executions": 0,
        "healer_executions": 0, "programs_executed": 0,
    }
    freeze_outputs = {
        "frozen_adjudication_records.csv": payload["records_bytes"],
        "frozen_approved_difference_ledger.csv": payload["differences_bytes"],
        "frozen_mechanism_ledger.csv": payload["mechanisms_bytes"],
        "frozen_failure_chain_ledger.csv": payload["chains_bytes"],
        "frozen_unresolved_evidence_gaps.csv": payload["gaps_bytes"],
        "freeze_authorization_closure_ledger.csv": _csv_bytes(AUTH_FIELDS, payload["authorization"]),
        "frozen_summary.json": _json_bytes(payload["freeze_summary"]),
        "report_zh.md": _freeze_report(payload["freeze_summary"]).encode("utf-8"),
        "execution_counts.json": _json_bytes(execution),
    }
    freeze_outputs["sha_ledger.json"] = _json_bytes({
        "taxonomy_sha256": SOURCE_HASHES[TAXONOMY], "frozen177_ledger_sha256": SOURCE_HASHES[FROZEN177],
        "remaining21_sha256": SOURCE_HASHES[REMAINING21], "roster_sha256": SOURCE_HASHES[ROSTER],
        "provisional_v2_records_sha256": SOURCE_HASHES[V2_RECORDS], "provisional_v2_manifest_sha256": SOURCE_HASHES[V2_MANIFEST],
        "reaudit_findings_sha256": SOURCE_HASHES[REAUDIT_FINDINGS], "reaudit_manifest_sha256": SOURCE_HASHES[REAUDIT_MANIFEST],
        "frozen_records_sha256": _sha(payload["records_bytes"]),
    })
    freeze_outputs["provenance.json"] = _json_bytes({
        **payload["freeze_summary"], **execution, "start_head": START_HEAD,
        "provenance_chain": [
            {"stage": "roster", "sha256": SOURCE_HASHES[ROSTER]},
            {"stage": "roster_audit", "sha256": SOURCE_HASHES[ROSTER_AUDIT_MANIFEST]},
            {"stage": "provisional_v1", "sha256": SOURCE_HASHES[V1_RECORDS]},
            {"stage": "v1_independent_audit", "sha256": SOURCE_HASHES[V1_AUDIT_MANIFEST]},
            {"stage": "provisional_v2", "sha256": SOURCE_HASHES[V2_RECORDS]},
            {"stage": "v2_independent_reaudit", "sha256": SOURCE_HASHES[REAUDIT_MANIFEST]},
            {"stage": "frozen_final_batch05"},
        ],
        "source_hashes": {path.as_posix(): digest for path, digest in SOURCE_HASHES.items()},
        "no_new_adjudication": True,
    })
    freeze_outputs["manifest.json"] = _json_bytes({
        "revision": FREEZE_OUTPUT.as_posix(), "status": FREEZE_STATUS, "verdict": VERDICT,
        "start_head": START_HEAD, "cells": 21, "freeze_basis_verdict": FREEZE_BASIS,
        "freeze_authorized": True, "reaudit_affirmed": 21, "reaudit_material": 0,
        "frozen_records_byte_identical_to_v2": True,
        "frozen_records_sha256": _sha(payload["records_bytes"]),
        "provisional_v2_records_sha256": SOURCE_HASHES[V2_RECORDS],
        "previously_frozen": 177, "newly_frozen": 21, "total_frozen": 198, "remaining": 0,
        "outputs_sha256_excluding_manifest": {name: _sha(data) for name, data in freeze_outputs.items()},
        **execution,
    })

    cumulative_bytes = _csv_bytes(CUMULATIVE_FIELDS, payload["cumulative"])
    registry = [
        {"batch_id": "frozen_through_batch04", "cells": "177", "freeze_order_range": "1-177", "unique_program_id": "177", "unique_cell_identity": "177", "unique_source_sha256": "", "source_revision": FROZEN177.parent.name, "source_manifest_sha256": SOURCE_HASHES[FROZEN177_MANIFEST], "notes": "immutable prior cumulative ledger retained byte-for-byte as prefix"},
        {"batch_id": "final_batch05", "cells": "21", "freeze_order_range": "178-198", "unique_program_id": "21", "unique_cell_identity": "21", "unique_source_sha256": "20", "source_revision": V2_DIR.name, "source_manifest_sha256": SOURCE_HASHES[V2_MANIFEST], "notes": "all remaining21 frozen in roster rank order"},
    ]
    closure_outputs = {
        "complete_cumulative_frozen_identity_ledger.csv": cumulative_bytes,
        "batch_registry.csv": _csv_bytes(REGISTRY_FIELDS, registry),
        "complete_taxonomy_summary.json": _json_bytes(payload["closure_summary"]),
        "report_zh.md": _closure_report(payload["closure_summary"]).encode("utf-8"),
        "execution_counts.json": _json_bytes(execution),
    }
    closure_outputs["sha_ledger.json"] = _json_bytes({
        "formal198_sha256": SOURCE_HASHES[PREPARATION], "frozen177_ledger_sha256": SOURCE_HASHES[FROZEN177],
        "batch05_frozen_records_sha256": _sha(payload["records_bytes"]),
        "complete_cumulative_ledger_sha256": _sha(cumulative_bytes),
    })
    closure_outputs["provenance.json"] = _json_bytes({
        **payload["closure_summary"], **execution, "start_head": START_HEAD,
        "closure_rule": "preserve frozen177 rows/order then append all Batch05 ranks 1-21 as freeze_order 178-198",
        "source_hashes": {FROZEN177.as_posix(): SOURCE_HASHES[FROZEN177], V2_RECORDS.as_posix(): SOURCE_HASHES[V2_RECORDS], PREPARATION.as_posix(): SOURCE_HASHES[PREPARATION]},
        "no_result_based_selection_reordering_or_deduplication": True,
    })
    closure_outputs["manifest.json"] = _json_bytes({
        "revision": CLOSURE_OUTPUT.as_posix(), "status": CLOSURE_STATUS, "verdict": VERDICT,
        "start_head": START_HEAD, "formal_population": 198, "total_frozen": 198,
        "remaining": 0, "reconciliation": "198=177+21",
        "complete_cumulative_ledger_sha256": _sha(cumulative_bytes),
        "frozen177_ledger_sha256": SOURCE_HASHES[FROZEN177],
        "batch05_frozen_records_sha256": _sha(payload["records_bytes"]),
        "outputs_sha256_excluding_manifest": {name: _sha(data) for name, data in closure_outputs.items()},
        **execution,
    })
    return {"freeze": freeze_outputs, "closure": closure_outputs}


def write_outputs(repo: Path = REPO_ROOT) -> tuple[Path, Path]:
    bundles = build_outputs(repo)
    freeze_path = repo / FREEZE_OUTPUT
    closure_path = repo / CLOSURE_OUTPUT
    freeze_path.mkdir(parents=True, exist_ok=True)
    closure_path.mkdir(parents=True, exist_ok=True)
    for name, data in bundles["freeze"].items():
        (freeze_path / name).write_bytes(data)
    for name, data in bundles["closure"].items():
        (closure_path / name).write_bytes(data)
    return freeze_path, closure_path


def main() -> None:
    freeze_path, closure_path = write_outputs()
    freeze_manifest = json.loads((freeze_path / "manifest.json").read_text(encoding="utf-8"))
    closure_manifest = json.loads((closure_path / "manifest.json").read_text(encoding="utf-8"))
    print(f"wrote {freeze_path}")
    print(f"wrote {closure_path}")
    print(f"frozen_records_sha256={freeze_manifest['frozen_records_sha256']}")
    print(f"freeze_manifest_sha256={_sha((freeze_path / 'manifest.json').read_bytes())}")
    print(f"cumulative198_sha256={closure_manifest['complete_cumulative_ledger_sha256']}")
    print(f"closure_manifest_sha256={_sha((closure_path / 'manifest.json').read_bytes())}")
    print(f"verdict={freeze_manifest['verdict']}")


if __name__ == "__main__":
    main()
