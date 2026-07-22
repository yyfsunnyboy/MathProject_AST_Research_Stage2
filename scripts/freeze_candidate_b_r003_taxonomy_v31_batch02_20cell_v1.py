#!/usr/bin/env python3
"""Formal freeze for taxonomy v3.1 Batch02 provisional v2.

FORMALLY_FROZEN_AI_ASSISTED_PROVISIONAL_ADJUDICATION

Creates an independent freeze revision and a new progress census revision.
Does not overwrite Batch02 provisional/audit/reaudit, Batch01 frozen, or progress v2.
Does not re-adjudicate cells or execute programs/models.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from scripts import (
        adjudicate_candidate_b_r003_taxonomy_v31_batch02_20cell_provisional_v2 as provisional_v2,
    )
except ModuleNotFoundError as exc:
    if exc.name != "scripts":
        raise
    import adjudicate_candidate_b_r003_taxonomy_v31_batch02_20cell_provisional_v2 as provisional_v2


REPO_ROOT = Path(__file__).resolve().parents[1]
FREEZE_OUTPUT = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_batch02_20cell_frozen_v1"
)
PROGRESS_OUTPUT = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_frozen_progress_census_v3"
)

START_HEAD = "79a6543ae888a0cedf3694a9985d88c4f97e0713"
STATUS = "FORMALLY_FROZEN_AI_ASSISTED_PROVISIONAL_ADJUDICATION"
PROGRESS_STATUS = "TAXONOMY_V31_FROZEN_PROGRESS_CENSUS"
FREEZE_BASIS_VERDICT = "READY_TO_FREEZE_BATCH02_PROVISIONAL_V2"
ANALYZER = Path("scripts/freeze_candidate_b_r003_taxonomy_v31_batch02_20cell_v1.py")
TESTS = Path("tests/finals_rebuild/test_candidate_b_r003_taxonomy_v31_batch02_20cell_frozen_v1.py")

TARGET_CELLS = 20
PREVIOUSLY_FROZEN = 117
NEWLY_FROZEN = 20
TOTAL_FROZEN = 137
REMAINING = 61
FORMAL_POPULATION = 198
REMAINING81_CELLS = 81

ROSTER_DIR = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_remaining81_batch02_20cell_roster_v1"
)
ROSTER = ROSTER_DIR / "batch02_roster.csv"
ROSTER_MANIFEST = ROSTER_DIR / "manifest.json"
ROSTER_SHA256 = "8742e496ce63a834d6b72237319c8b2419fd749b2e2af971700aaef4055c435d"
ROSTER_MANIFEST_SHA256 = "05aa6192198ba4e7c6bf2ea04e043e7bd3c14a2619ba41b623496cf34e21c0a0"

V1_DIR = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_batch02_20cell_provisional_v1"
)
V1_RECORDS = V1_DIR / "adjudication_records.csv"
V1_MANIFEST = V1_DIR / "manifest.json"
V1_RECORDS_SHA256 = "cb4101111e610faeadc292f8d26dbbb5088848011bf9d4527dbbe029b07252e9"
V1_MANIFEST_SHA256 = "888873b1ec39831511e53b9d41b6b07e71752faaf1aff23f12817e8576dc3d01"

AUDIT_DIR = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_batch02_20cell_provisional_v1_independent_audit_v1"
)
AUDIT_MANIFEST = AUDIT_DIR / "manifest.json"
AUDIT_MATERIAL = AUDIT_DIR / "material_findings.csv"
AUDIT_MANIFEST_SHA256 = "c0dc812fc114bd251e97ee69e770d9613a5209c59ef251aa3c5bd5d2d872c620"
AUDIT_MATERIAL_SHA256 = "47160a3054e2bd634a1530f4f25e663209164d5d45c7f618fb02af1cb3182e9c"

V2_DIR = provisional_v2.OUTPUT_RELATIVE
V2_RECORDS = V2_DIR / "adjudication_records.csv"
V2_ROSTER = V2_DIR / "adjudication_roster.csv"
V2_SUMMARY = V2_DIR / "adjudication_summary.json"
V2_MANIFEST = V2_DIR / "manifest.json"
V2_GAPS = V2_DIR / "unresolved_evidence_gaps.csv"
V2_RECORDS_SHA256 = "dc6d4a4fa0f0027eb87e3af48b3567c72443255fcda2e2779acf7fe0fbf70f04"
V2_ROSTER_SHA256 = "ca1544ad12d0336638425ac770e7bf40c19e94ca59522e7cf0a90f3d122d6e4c"
V2_SUMMARY_SHA256 = "a61e382dd3a52c6ea7ce0bc4f46f759cb862249d1e993ba9cf0c7fae9be1a442"
V2_MANIFEST_SHA256 = "0f3bb9c0c106f4bed5942b4883132c92cc460f87fec1e4c146d4333f68346c0d"
V2_GAPS_SHA256 = "90c14c69ff97a850a7f699e3da1a2ad6d819da42f7220bb23dc0aec5b277f44a"

REAUDIT_DIR = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_batch02_20cell_provisional_v2_independent_reaudit_v1"
)
REAUDIT_MANIFEST = REAUDIT_DIR / "manifest.json"
REAUDIT_FINDINGS = REAUDIT_DIR / "per_cell_change_findings.csv"
REAUDIT_SUMMARY = REAUDIT_DIR / "reaudit_summary.json"
REAUDIT_MANIFEST_SHA256 = "de160c2ccabe5280e7fd35b34788442b28c383a50089025b6388e69b310391c6"
REAUDIT_FINDINGS_SHA256 = "59799471e645883e5e7969b3d4f58f785249161cae4038090c44ad8f98d1bfa6"
REAUDIT_SUMMARY_SHA256 = "843577362e81b274406cd4175303880e9b59e0361f8157db357d591964d74505"

PROGRESS_V2_MANIFEST = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_frozen_progress_census_v2/manifest.json"
)
PROGRESS_V2_MANIFEST_SHA256 = "67fcd910bbfb5c07beb9c9231464b871e196931f6874059c59d28b2cacaddd71"
PROGRESS_V2_REGISTRY = PROGRESS_V2_MANIFEST.with_name("batch_registry.csv")

BATCH01_FROZEN_DIR = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_frozen_v1"
)
BATCH01_FROZEN_RECORDS = BATCH01_FROZEN_DIR / "frozen_adjudication.csv"
BATCH01_FROZEN_MANIFEST = BATCH01_FROZEN_DIR / "manifest.json"
BATCH01_FROZEN_RECORDS_SHA256 = "8f2410122205610f41d4e7dfbbc4b958d05c1e3da40176b9dc9269880512c0cb"
BATCH01_FROZEN_MANIFEST_SHA256 = "8cbed23b396ba7149fac485abf30160327ad6b483166ca22cccb3a6e1e4210ae"

REMAINING101 = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_remaining101_zero_execution_census_v1/"
    "remaining101_roster.csv"
)
REMAINING101_SHA256 = "8fe0f5d95e7c6e86cda5f18dabfecae486120c50eeaf1baad6fe6c12b23143f6"

RECORD_FIELDS = provisional_v2.RECORD_FIELDS
ROSTER_FIELDS = provisional_v2.ROSTER_FIELDS
GAP_FIELDS = provisional_v2.GAP_FIELDS

INDEX_FIELDS = (
    "freeze_rank",
    "cell_identity_sha256",
    "program_id",
    "source_sha256",
    "frozen_from_revision",
    "freeze_status",
    "freeze_basis_verdict",
)

BATCH_REGISTRY_FIELDS = (
    "batch_id",
    "cells",
    "unique_program_id",
    "unique_source_sha256",
    "unique_task_id",
    "source_revision",
    "source_manifest_sha256",
    "freeze_revision",
    "notes",
)

SOURCE_HASHES: dict[Path, str] = {
    ROSTER: ROSTER_SHA256,
    ROSTER_MANIFEST: ROSTER_MANIFEST_SHA256,
    V1_RECORDS: V1_RECORDS_SHA256,
    V1_MANIFEST: V1_MANIFEST_SHA256,
    AUDIT_MANIFEST: AUDIT_MANIFEST_SHA256,
    AUDIT_MATERIAL: AUDIT_MATERIAL_SHA256,
    V2_RECORDS: V2_RECORDS_SHA256,
    V2_ROSTER: V2_ROSTER_SHA256,
    V2_SUMMARY: V2_SUMMARY_SHA256,
    V2_MANIFEST: V2_MANIFEST_SHA256,
    V2_GAPS: V2_GAPS_SHA256,
    REAUDIT_MANIFEST: REAUDIT_MANIFEST_SHA256,
    REAUDIT_FINDINGS: REAUDIT_FINDINGS_SHA256,
    REAUDIT_SUMMARY: REAUDIT_SUMMARY_SHA256,
    PROGRESS_V2_MANIFEST: PROGRESS_V2_MANIFEST_SHA256,
    BATCH01_FROZEN_RECORDS: BATCH01_FROZEN_RECORDS_SHA256,
    BATCH01_FROZEN_MANIFEST: BATCH01_FROZEN_MANIFEST_SHA256,
    REMAINING101: REMAINING101_SHA256,
}


class FreezeError(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise FreezeError(message)


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


def _path(repo: Path, relative: Path) -> Path:
    return relative if relative.is_absolute() else repo / relative


def verify_sources(repo: Path = REPO_ROOT, expected: dict[Path, str] | None = None) -> None:
    for relative, digest in (expected or SOURCE_HASHES).items():
        path = _path(repo, relative)
        _require(path.is_file(), f"missing source: {path}")
        _require(_sha(path.read_bytes()) == digest, f"source hash drift: {path}")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _normalize_secondary(value: str) -> str:
    return value if value else "empty"


def build_freeze_payload(repo: Path = REPO_ROOT) -> dict[str, Any]:
    verify_sources(repo)
    reaudit_manifest = json.loads((repo / REAUDIT_MANIFEST).read_text(encoding="utf-8"))
    reaudit_summary = json.loads((repo / REAUDIT_SUMMARY).read_text(encoding="utf-8"))
    _require(reaudit_manifest.get("verdict") == FREEZE_BASIS_VERDICT, "reaudit verdict drift")
    _require(reaudit_summary.get("material_findings") == 0, "reaudit material findings drift")
    _require(reaudit_summary.get("unauthorized_differences") == 0, "unauthorized differences drift")
    _require(reaudit_manifest.get("unauthorized_differences") == 0, "manifest unauthorized drift")

    v2_bytes = (repo / V2_RECORDS).read_bytes()
    roster_bytes = (repo / V2_ROSTER).read_bytes()
    gaps_bytes = (repo / V2_GAPS).read_bytes()
    _require(_sha(v2_bytes) == V2_RECORDS_SHA256, "v2 records sha drift")
    _require(_sha(roster_bytes) == V2_ROSTER_SHA256, "v2 roster sha drift")
    _require(_sha(gaps_bytes) == V2_GAPS_SHA256, "v2 gaps sha drift")

    v2_rows = _read_csv(repo / V2_RECORDS)
    roster_rows = _read_csv(repo / ROSTER)
    v2_roster_rows = _read_csv(repo / V2_ROSTER)
    gaps = _read_csv(repo / V2_GAPS)
    batch01_rows = _read_csv(repo / BATCH01_FROZEN_RECORDS)
    remaining101 = _read_csv(repo / REMAINING101)

    _require(len(v2_rows) == TARGET_CELLS, "v2 cells drift")
    _require([row["program_id"] for row in v2_rows] == [row["program_id"] for row in roster_rows], "v2/roster program drift")
    _require(
        [row["cell_identity_sha256"] for row in v2_rows]
        == [row["cell_identity_sha256"] for row in roster_rows],
        "v2/roster identity drift",
    )
    _require(
        [row["source_sha256"] for row in v2_rows] == [row["source_sha256"] for row in roster_rows],
        "v2/roster source drift",
    )
    _require([row["program_id"] for row in v2_roster_rows] == [row["program_id"] for row in roster_rows], "v2 roster drift")
    _require(len({row["program_id"] for row in v2_rows}) == 20, "program uniqueness")
    _require(len({row["cell_identity_sha256"] for row in v2_rows}) == 20, "cell uniqueness")
    _require(len({row["source_sha256"] for row in v2_rows}) == 19, "source uniqueness")

    primary = Counter(row["primary_layer"] for row in v2_rows)
    secondary = Counter(_normalize_secondary(row["secondary_layer"]) for row in v2_rows)
    confidence = Counter(row["confidence"] for row in v2_rows)
    outcome = Counter(row["outcome_validity"] for row in v2_rows)
    healer = Counter(row["healer_eligibility"] for row in v2_rows)
    _require(primary == Counter({"L2": 3, "L4": 1, "L5": 5, "UNRESOLVED": 11}), f"primary drift {primary}")
    _require(secondary == Counter({"L5": 4, "empty": 16}), f"secondary drift {secondary}")
    _require(confidence == Counter({"HIGH": 7, "MEDIUM": 2, "LOW": 11}), f"confidence drift {confidence}")
    _require(outcome == Counter({"VALID_MODEL_OUTCOME": 20}), f"outcome drift {outcome}")
    _require(healer == Counter({"abstain": 20}), f"healer drift {healer}")
    _require(len(gaps) == 11, "gaps drift")

    batch01_programs = {row["program_id"] for row in batch01_rows}
    batch02_programs = {row["program_id"] for row in v2_rows}
    batch02_cells = {row["cell_identity_sha256"] for row in v2_rows}
    _require(not (batch01_programs & batch02_programs), "batch01/batch02 program overlap")
    _require(batch02_cells <= {row["cell_identity_sha256"] for row in remaining101}, "batch02 outside remaining101")
    remaining_after = REMAINING81_CELLS - TARGET_CELLS
    _require(remaining_after == REMAINING, "remaining81-batch02 must equal 61")
    _require(PREVIOUSLY_FROZEN + NEWLY_FROZEN == TOTAL_FROZEN, "frozen arithmetic")
    _require(FORMAL_POPULATION == TOTAL_FROZEN + REMAINING, "population closure")

    index_rows = [
        {
            "freeze_rank": str(rank),
            "cell_identity_sha256": row["cell_identity_sha256"],
            "program_id": row["program_id"],
            "source_sha256": row["source_sha256"],
            "frozen_from_revision": V2_DIR.name,
            "freeze_status": STATUS,
            "freeze_basis_verdict": FREEZE_BASIS_VERDICT,
        }
        for rank, row in enumerate(v2_rows, 1)
    ]
    return {
        "v2_bytes": v2_bytes,
        "roster_bytes": roster_bytes,
        "gaps_bytes": gaps_bytes,
        "v2_rows": v2_rows,
        "index_rows": index_rows,
        "primary": primary,
        "secondary": secondary,
        "confidence": confidence,
        "outcome": outcome,
        "healer": healer,
        "unique_tasks": len({row["task_id"] for row in v2_rows}),
    }


def _freeze_report(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Frozen batch：taxonomy v3.1 Batch02 provisional v2",
            "",
            f"**狀態：`{STATUS}`**",
            "",
            f"**Freeze basis：`{FREEZE_BASIS_VERDICT}`**",
            "",
            "## 來源",
            "",
            f"- roster：`{ROSTER_SHA256}`",
            f"- provisional v1 records：`{V1_RECORDS_SHA256}`",
            f"- audit manifest：`{AUDIT_MANIFEST_SHA256}`",
            f"- provisional v2 records：`{V2_RECORDS_SHA256}`",
            f"- re-audit manifest：`{REAUDIT_MANIFEST_SHA256}`",
            f"- re-audit findings：`{REAUDIT_FINDINGS_SHA256}`",
            "",
            "## 統計",
            "",
            f"- primary：{dict(sorted(payload['primary'].items()))}",
            f"- secondary：{dict(sorted(payload['secondary'].items()))}",
            f"- confidence：{dict(sorted(payload['confidence'].items()))}",
            f"- outcome：{dict(sorted(payload['outcome'].items()))}",
            "- Healer：eligible=0，conditional=0，abstain=20",
            "",
            "## 進度",
            "",
            f"- previously frozen={PREVIOUSLY_FROZEN}",
            f"- newly frozen={NEWLY_FROZEN}",
            f"- total frozen={TOTAL_FROZEN}",
            f"- remaining={REMAINING}",
            "",
            "本 freeze 無新裁決、無 candidate／模型執行；未建立 remaining61 roster；Batch03 尚未開始。",
        ]
    ) + "\n"


def _progress_report() -> str:
    return "\n".join(
        [
            "# Taxonomy v3.1 frozen progress census v3",
            "",
            f"**狀態：`{PROGRESS_STATUS}`**",
            "",
            "## 總進度",
            "",
            f"- formal population={FORMAL_POPULATION}",
            f"- previously frozen={PREVIOUSLY_FROZEN}",
            f"- newly frozen this revision={NEWLY_FROZEN}（Batch02）",
            f"- total frozen={TOTAL_FROZEN}",
            f"- remaining={REMAINING}",
            f"- reconciliation：{FORMAL_POPULATION}={TOTAL_FROZEN}+{REMAINING}",
            "",
            "## 研究敘述",
            "",
            "已凍結137格，剩餘61格；Batch02 20格全部 Healer abstain。"
            "不得把 Batch02 結果外推至其餘61格，也不得宣稱 remaining81／remaining101 已完成。",
            "",
            "## 邊界",
            "",
            "- 本 census 為新的 immutable progress revision，不覆寫 progress v2",
            "- 未建立 remaining61 roster",
            "- Batch03 尚未開始",
        ]
    ) + "\n"


def build_outputs(repo: Path = REPO_ROOT) -> dict[str, dict[str, bytes]]:
    payload = build_freeze_payload(repo)
    execution_counts = {
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
    primary = payload["primary"]
    secondary = payload["secondary"]
    confidence = payload["confidence"]
    healer = payload["healer"]
    unique_tasks = payload["unique_tasks"]

    freeze_summary = {
        "revision": FREEZE_OUTPUT.name,
        "status": STATUS,
        "freeze_basis_verdict": FREEZE_BASIS_VERDICT,
        "cells": TARGET_CELLS,
        "unique_program_id": 20,
        "unique_cell_identity": 20,
        "unique_source_sha256": 19,
        "unique_task_id": unique_tasks,
        "primary_layer_distribution": dict(sorted(primary.items())),
        "secondary_layer_distribution": dict(sorted(secondary.items())),
        "confidence_distribution": dict(sorted(confidence.items())),
        "outcome_validity_distribution": {"VALID_MODEL_OUTCOME": 20},
        "healer_eligibility_distribution": {"eligible": 0, "conditional": 0, "abstain": 20},
        "unresolved_gaps": 11,
        "unauthorized_adjudication_differences": 0,
        "previously_frozen": PREVIOUSLY_FROZEN,
        "newly_frozen": NEWLY_FROZEN,
        "total_frozen": TOTAL_FROZEN,
        "remaining": REMAINING,
        "roster_sha256": ROSTER_SHA256,
        "provisional_v2_records_sha256": V2_RECORDS_SHA256,
        "provisional_v2_manifest_sha256": V2_MANIFEST_SHA256,
        "reaudit_manifest_sha256": REAUDIT_MANIFEST_SHA256,
        "reaudit_findings_sha256": REAUDIT_FINDINGS_SHA256,
        "frozen_records_sha256": V2_RECORDS_SHA256,
        "no_new_adjudication": True,
        "no_model_or_candidate_execution": True,
        "remaining61_roster_created": False,
        "batch03_started": False,
    }
    sha_ledger = {
        "freeze_basis_verdict": FREEZE_BASIS_VERDICT,
        "start_head": START_HEAD,
        "roster_sha256": ROSTER_SHA256,
        "provisional_v1_records_sha256": V1_RECORDS_SHA256,
        "provisional_v1_manifest_sha256": V1_MANIFEST_SHA256,
        "audit_manifest_sha256": AUDIT_MANIFEST_SHA256,
        "audit_material_findings_sha256": AUDIT_MATERIAL_SHA256,
        "provisional_v2_records_sha256": V2_RECORDS_SHA256,
        "provisional_v2_roster_sha256": V2_ROSTER_SHA256,
        "provisional_v2_manifest_sha256": V2_MANIFEST_SHA256,
        "provisional_v2_gaps_sha256": V2_GAPS_SHA256,
        "reaudit_manifest_sha256": REAUDIT_MANIFEST_SHA256,
        "reaudit_findings_sha256": REAUDIT_FINDINGS_SHA256,
        "reaudit_summary_sha256": REAUDIT_SUMMARY_SHA256,
        "batch01_frozen_records_sha256": BATCH01_FROZEN_RECORDS_SHA256,
        "batch01_frozen_manifest_sha256": BATCH01_FROZEN_MANIFEST_SHA256,
        "progress_v2_manifest_sha256": PROGRESS_V2_MANIFEST_SHA256,
        "frozen_records_byte_identical_to_v2": True,
        "source_hashes": {path.as_posix(): digest for path, digest in SOURCE_HASHES.items()},
    }
    freeze_provenance = {
        **freeze_summary,
        "start_head": START_HEAD,
        "provenance_chain": [
            "roster",
            "provisional_v1",
            "audit",
            "provisional_v2",
            "reaudit",
            "frozen",
        ],
        "sha_ledger": sha_ledger,
        "analyzer": ANALYZER.as_posix(),
        "tests": TESTS.as_posix(),
        "upstream_modified": False,
        **execution_counts,
    }

    prior_registry = _read_csv(repo / PROGRESS_V2_REGISTRY)
    batch_registry = list(prior_registry) + [
        {
            "batch_id": "remaining81_batch02_20",
            "cells": "20",
            "unique_program_id": "20",
            "unique_source_sha256": "19",
            "unique_task_id": str(unique_tasks),
            "source_revision": V2_DIR.name,
            "source_manifest_sha256": V2_MANIFEST_SHA256,
            "freeze_revision": FREEZE_OUTPUT.name,
            "notes": "Batch02 freeze; no remaining61 roster; not an extrapolation claim",
        }
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
        "remaining81_minus_batch02": REMAINING,
        "batch02_frozen_cells": NEWLY_FROZEN,
        "batch02_roster_sha256": ROSTER_SHA256,
        "batch02_freeze_revision": FREEZE_OUTPUT.name,
        "batch02_freeze_basis_verdict": FREEZE_BASIS_VERDICT,
        "batch02_primary_layer_distribution": dict(sorted(primary.items())),
        "batch02_secondary_layer_distribution": dict(sorted(secondary.items())),
        "batch02_healer_eligibility_distribution": {"eligible": 0, "conditional": 0, "abstain": 20},
        "remaining61_roster_created": False,
        "batch03_started": False,
        "research_statement_zh": (
            "已凍結137格，剩餘61格；Batch02 20格全部Healer abstain。"
            "不得外推至其餘61格，不得宣稱remaining81已全部完成。"
        ),
        "overwrites_prior_census": False,
        **execution_counts,
    }
    progress_provenance = {
        **progress_summary,
        "start_head": START_HEAD,
        "prior_progress_census_manifest_sha256": PROGRESS_V2_MANIFEST_SHA256,
        "provisional_v2_records_sha256": V2_RECORDS_SHA256,
        "reaudit_manifest_sha256": REAUDIT_MANIFEST_SHA256,
        "immutable_new_revision": True,
        "analyzer": ANALYZER.as_posix(),
        "tests": TESTS.as_posix(),
    }

    return {
        "freeze": {
            Path("frozen_adjudication.csv"): payload["v2_bytes"],
            Path("frozen_roster.csv"): payload["roster_bytes"],
            Path("frozen_unresolved_evidence_gaps.csv"): payload["gaps_bytes"],
            Path("freeze_index.csv"): _csv_bytes(INDEX_FIELDS, payload["index_rows"]),
            Path("sha_ledger.json"): _json_bytes(sha_ledger),
            Path("frozen_batch_summary.json"): _json_bytes(freeze_summary),
            Path("frozen_batch_report_zh.md"): _freeze_report(payload).encode("utf-8"),
            Path("execution_counts.json"): _json_bytes(execution_counts),
            Path("provenance.json"): _json_bytes(freeze_provenance),
        },
        "progress": {
            Path("batch_registry.csv"): _csv_bytes(BATCH_REGISTRY_FIELDS, batch_registry),
            Path("frozen_progress_summary.json"): _json_bytes(progress_summary),
            Path("frozen_progress_report_zh.md"): _progress_report().encode("utf-8"),
            Path("execution_counts.json"): _json_bytes(execution_counts),
            Path("provenance.json"): _json_bytes(progress_provenance),
        },
    }


def write_outputs(repo: Path = REPO_ROOT) -> tuple[Path, Path]:
    freeze_dest = repo / FREEZE_OUTPUT
    progress_dest = repo / PROGRESS_OUTPUT
    _require(not freeze_dest.exists(), f"freeze output exists: {freeze_dest}")
    _require(not progress_dest.exists(), f"progress output exists: {progress_dest}")
    guarded = {
        V2_RECORDS: V2_RECORDS_SHA256,
        V2_MANIFEST: V2_MANIFEST_SHA256,
        REAUDIT_MANIFEST: REAUDIT_MANIFEST_SHA256,
        REAUDIT_FINDINGS: REAUDIT_FINDINGS_SHA256,
        ROSTER: ROSTER_SHA256,
        V1_RECORDS: V1_RECORDS_SHA256,
        AUDIT_MANIFEST: AUDIT_MANIFEST_SHA256,
        BATCH01_FROZEN_RECORDS: BATCH01_FROZEN_RECORDS_SHA256,
        BATCH01_FROZEN_MANIFEST: BATCH01_FROZEN_MANIFEST_SHA256,
        PROGRESS_V2_MANIFEST: PROGRESS_V2_MANIFEST_SHA256,
    }
    before = {path: (repo / path).read_bytes() for path in guarded}
    bundles = build_outputs(repo)
    freeze_dest.mkdir(parents=True)
    progress_dest.mkdir(parents=True)
    freeze_hashes = {p.as_posix(): _sha(d) for p, d in bundles["freeze"].items()}
    progress_hashes = {p.as_posix(): _sha(d) for p, d in bundles["progress"].items()}
    for path, data in bundles["freeze"].items():
        (freeze_dest / path).write_bytes(data)
    for path, data in bundles["progress"].items():
        (progress_dest / path).write_bytes(data)

    freeze_manifest = {
        "revision": FREEZE_OUTPUT.name,
        "status": STATUS,
        "freeze_basis_verdict": FREEZE_BASIS_VERDICT,
        "cells": TARGET_CELLS,
        "newly_frozen": NEWLY_FROZEN,
        "previously_frozen": PREVIOUSLY_FROZEN,
        "total_frozen": TOTAL_FROZEN,
        "remaining": REMAINING,
        "roster_sha256": ROSTER_SHA256,
        "provisional_v2_records_sha256": V2_RECORDS_SHA256,
        "provisional_v2_manifest_sha256": V2_MANIFEST_SHA256,
        "reaudit_manifest_sha256": REAUDIT_MANIFEST_SHA256,
        "reaudit_findings_sha256": REAUDIT_FINDINGS_SHA256,
        "frozen_records_sha256": V2_RECORDS_SHA256,
        "frozen_records_byte_identical_to_v2": True,
        "unauthorized_adjudication_differences": 0,
        "upstream_modified": False,
        "no_new_adjudication": True,
        "remaining61_roster_created": False,
        "batch03_started": False,
        "analyzer": ANALYZER.as_posix(),
        "tests": TESTS.as_posix(),
        "outputs_sha256_excluding_manifest": freeze_hashes,
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
    progress_manifest = {
        "revision": PROGRESS_OUTPUT.name,
        "status": PROGRESS_STATUS,
        "formal_population": FORMAL_POPULATION,
        "previously_frozen": PREVIOUSLY_FROZEN,
        "newly_frozen": NEWLY_FROZEN,
        "total_frozen": TOTAL_FROZEN,
        "remaining": REMAINING,
        "freeze_revision": FREEZE_OUTPUT.name,
        "batch02_roster_sha256": ROSTER_SHA256,
        "freeze_basis_verdict": FREEZE_BASIS_VERDICT,
        "overwrites_prior_census": False,
        "remaining61_roster_created": False,
        "batch03_started": False,
        "outputs_sha256_excluding_manifest": progress_hashes,
        "model_calls": 0,
        "candidate_executions": 0,
        "evalplus_correctness_executions": 0,
        "diagnostics_executions": 0,
        "validation_executions": 0,
        "healer_executions": 0,
        "programs_executed": 0,
    }
    (freeze_dest / "manifest.json").write_bytes(_json_bytes(freeze_manifest))
    (progress_dest / "manifest.json").write_bytes(_json_bytes(progress_manifest))
    for path, expected in before.items():
        _require((repo / path).read_bytes() == expected, f"upstream mutated: {path}")
        _require(_sha(expected) == guarded[path], f"sha drift after write: {path}")
    _require(
        _sha((freeze_dest / "frozen_adjudication.csv").read_bytes()) == V2_RECORDS_SHA256,
        "frozen records must equal v2 records sha",
    )
    return freeze_dest, progress_dest


def main() -> None:
    freeze_path, progress_path = write_outputs()
    freeze_manifest = json.loads((freeze_path / "manifest.json").read_text(encoding="utf-8"))
    progress_manifest = json.loads((progress_path / "manifest.json").read_text(encoding="utf-8"))
    print(freeze_path)
    print(progress_path)
    print(f"freeze_manifest_sha={_sha((freeze_path / 'manifest.json').read_bytes())}")
    print(f"progress_manifest_sha={_sha((progress_path / 'manifest.json').read_bytes())}")
    print(f"frozen_records_sha={_sha((freeze_path / 'frozen_adjudication.csv').read_bytes())}")
    print(f"total_frozen={freeze_manifest['total_frozen']} remaining={freeze_manifest['remaining']}")
    print(f"progress_remaining={progress_manifest['remaining']}")


if __name__ == "__main__":
    main()
