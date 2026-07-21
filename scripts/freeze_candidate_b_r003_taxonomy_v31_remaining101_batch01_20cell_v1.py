#!/usr/bin/env python3
"""Formal freeze for remaining101 batch01 20-cell provisional v2.

FORMALLY_FROZEN_AI_ASSISTED_PROVISIONAL_ADJUDICATION

Creates an independent freeze revision and a new progress census revision.
Does not overwrite provisional v1/v2, audits, census, next20, or prior progress.
Does not re-adjudicate cells or execute programs/models.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any

try:
    from scripts import (
        prepare_candidate_b_r003_taxonomy_v31_remaining101_zero_execution_census_v1 as census_prep,
    )
    from scripts import (
        adjudicate_candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_provisional_v1 as provisional_v1,
    )
    from scripts import (
        adjudicate_candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_provisional_v2 as provisional_v2,
    )
    from scripts import (
        audit_candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_post_adjudication_v1 as audit_v1,
    )
    from scripts import (
        audit_candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_post_adjudication_reaudit_v2 as reaudit_v2,
    )
except ModuleNotFoundError as exc:
    if exc.name != "scripts":
        raise
    import prepare_candidate_b_r003_taxonomy_v31_remaining101_zero_execution_census_v1 as census_prep
    import adjudicate_candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_provisional_v1 as provisional_v1
    import adjudicate_candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_provisional_v2 as provisional_v2
    import audit_candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_post_adjudication_v1 as audit_v1
    import audit_candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_post_adjudication_reaudit_v2 as reaudit_v2


REPO_ROOT = Path(__file__).resolve().parents[1]
FREEZE_OUTPUT = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_frozen_v1"
)
PROGRESS_OUTPUT = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_frozen_progress_census_v2"
)
PRIOR_PROGRESS_MANIFEST = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_frozen_progress_census_v1/manifest.json"
)
PRIOR_PROGRESS_MANIFEST_SHA256 = (
    "7eee4c9e94ae8ea3b42bfb8921e546533e12ac618b18703edf7d18993f254e1a"
)

START_HEAD = "b5a425bd9fb3b698fd83a66e25b01b979feba96b"
STATUS = "FORMALLY_FROZEN_AI_ASSISTED_PROVISIONAL_ADJUDICATION"
PROGRESS_STATUS = "TAXONOMY_V31_FROZEN_PROGRESS_CENSUS"
FREEZE_BASIS_VERDICT = "READY_TO_FREEZE_BATCH01_20CELL_V2"
ANALYZER = Path(
    "scripts/freeze_candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_v1.py"
)
TESTS = Path(
    "tests/finals_rebuild/"
    "test_candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_frozen_v1.py"
)

TARGET_CELLS = 20
PREVIOUSLY_FROZEN = 97
NEWLY_FROZEN = 20
TOTAL_FROZEN = 117
REMAINING = 81
FORMAL_POPULATION = 198

CENSUS_DIR = census_prep.OUTPUT_RELATIVE
NEXT20 = CENSUS_DIR / "next_adjudication_batch_roster.csv"
REMAINING101 = CENSUS_DIR / "remaining101_roster.csv"
CENSUS_MANIFEST = CENSUS_DIR / "manifest.json"
NEXT20_SHA256 = "a22f086ba7d61995de98dafd57edcbdcb01fe46e780bd595163a6eabf813eb91"
REMAINING101_SHA256 = "8fe0f5d95e7c6e86cda5f18dabfecae486120c50eeaf1baad6fe6c12b23143f6"
CENSUS_MANIFEST_SHA256 = "d2a7478da6852ba1a6592d2d1701b8ad3aee3bc018824a365aab9670fa0438bd"

V1_DIR = provisional_v1.OUTPUT_RELATIVE
V1_RECORDS = V1_DIR / "adjudication_records.csv"
V1_ROSTER = V1_DIR / "adjudication_roster.csv"
V1_MANIFEST = V1_DIR / "manifest.json"
V1_RECORDS_SHA256 = "e08f1eab72275d7c37884883b1a439438daee6a2be0d8df408ba758b2364990b"
V1_ROSTER_SHA256 = "9f475868806c9a73bd25f96cb2c731f6357cafe0e6e08b53aa1fd0a374f13533"
V1_MANIFEST_SHA256 = "710ef4fd707291db650e5b14d5594ed7920f1a9c2370ee3d5cde2f09a24a627e"

V2_DIR = provisional_v2.OUTPUT_RELATIVE
V2_RECORDS = V2_DIR / "adjudication_records.csv"
V2_ROSTER = V2_DIR / "adjudication_roster.csv"
V2_SUMMARY = V2_DIR / "adjudication_summary.json"
V2_MANIFEST = V2_DIR / "manifest.json"
V2_GAPS = V2_DIR / "unresolved_evidence_gaps.csv"
V2_RECORDS_SHA256 = "4f4d7479050b4a7bab8b0384169f5407331d720a33a3af47d2f45477a4ef6596"
V2_ROSTER_SHA256 = "9f475868806c9a73bd25f96cb2c731f6357cafe0e6e08b53aa1fd0a374f13533"
V2_SUMMARY_SHA256 = "8e2d1893cd7df3d1c29093aed15b12b5a9222d2e9e8296c654af572f9102e809"
V2_MANIFEST_SHA256 = "30af6d5deaacfc0400e71936b532b5b52987f28f2ce2a04ea2da478a55e88d47"
V2_GAPS_SHA256 = "4c1d7a72db70444e4fe032f33f65dc42795c17565543c5c420c15eec99221c93"

AUDIT_MANIFEST = audit_v1.OUTPUT_RELATIVE / "manifest.json"
AUDIT_MANIFEST_SHA256 = "37438e79a8aa5ac68edafa5291c5c0601085dbdf96b3a92015e2b4de20905adf"

REAUDIT_DIR = reaudit_v2.OUTPUT_RELATIVE
REAUDIT_MANIFEST = REAUDIT_DIR / "manifest.json"
REAUDIT_SUMMARY = REAUDIT_DIR / "reaudit_summary.json"
REAUDIT_MANIFEST_SHA256 = "23dbbc7f1c0939b9ece5fa4175d3b91fa0e3b1cbd49d230b3b8b55519c89a525"
REAUDIT_SUMMARY_SHA256 = "a1329c83695941449204f2ba6e8b1285a433725af191c16ca321a624d736d4b9"

RECORD_FIELDS = provisional_v2.RECORD_FIELDS
ROSTER_FIELDS = provisional_v2.ROSTER_FIELDS
UNRESOLVED_GAP_FIELDS = provisional_v2.UNRESOLVED_GAP_FIELDS

FROZEN_FIELDS = ("freeze_rank", "frozen_from_revision", "freeze_status", "freeze_basis_verdict") + RECORD_FIELDS

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
    NEXT20: NEXT20_SHA256,
    REMAINING101: REMAINING101_SHA256,
    CENSUS_MANIFEST: CENSUS_MANIFEST_SHA256,
    V1_RECORDS: V1_RECORDS_SHA256,
    V1_ROSTER: V1_ROSTER_SHA256,
    V1_MANIFEST: V1_MANIFEST_SHA256,
    V2_RECORDS: V2_RECORDS_SHA256,
    V2_ROSTER: V2_ROSTER_SHA256,
    V2_SUMMARY: V2_SUMMARY_SHA256,
    V2_MANIFEST: V2_MANIFEST_SHA256,
    V2_GAPS: V2_GAPS_SHA256,
    AUDIT_MANIFEST: AUDIT_MANIFEST_SHA256,
    REAUDIT_MANIFEST: REAUDIT_MANIFEST_SHA256,
    REAUDIT_SUMMARY: REAUDIT_SUMMARY_SHA256,
    PRIOR_PROGRESS_MANIFEST: PRIOR_PROGRESS_MANIFEST_SHA256,
    census_prep.G2_PROVISIONAL_CSV: census_prep.G2_PROVISIONAL_CSV_SHA256,
    census_prep.MODULE_EXCEPTION_CSV: census_prep.MODULE_EXCEPTION_CSV_SHA256,
    census_prep.MULTIPLE_SIGNAL_CSV: census_prep.MULTIPLE_SIGNAL_CSV_SHA256,
    census_prep.FREEZE20_CSV: census_prep.FREEZE20_CSV_SHA256,
    census_prep.FREEZE20_MANIFEST: census_prep.FREEZE20_MANIFEST_SHA256,
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


def build_freeze_rows(repo: Path = REPO_ROOT) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    verify_sources(repo)
    reaudit_manifest = json.loads((repo / REAUDIT_MANIFEST).read_text(encoding="utf-8"))
    reaudit_summary = json.loads((repo / REAUDIT_SUMMARY).read_text(encoding="utf-8"))
    _require(
        reaudit_manifest.get("overall_verdict") == FREEZE_BASIS_VERDICT,
        f"reaudit verdict drift: {reaudit_manifest.get('overall_verdict')}",
    )
    _require(reaudit_summary.get("ready_to_freeze") is True, "reaudit not ready_to_freeze")
    _require(reaudit_summary.get("material_finding_count") == 0, "reaudit has material findings")

    v2_rows = _read_csv(repo / V2_RECORDS)
    roster = _read_csv(repo / V2_ROSTER)
    next20 = _read_csv(repo / NEXT20)
    gaps = _read_csv(repo / V2_GAPS)
    _require(len(v2_rows) == TARGET_CELLS, "v2 cells drift")
    _require([row["program_id"] for row in v2_rows] == [row["program_id"] for row in next20], "v2/next20 drift")
    _require([row["program_id"] for row in roster] == [row["program_id"] for row in next20], "roster/next20 drift")
    _require(len({row["source_sha256"] for row in v2_rows}) == TARGET_CELLS, "source uniqueness")

    primary = Counter(row["primary_layer"] for row in v2_rows)
    healer = Counter(row["healer_eligibility"] for row in v2_rows)
    confidence = Counter(row["confidence"] for row in v2_rows)
    outcome = Counter(row["outcome_validity"] for row in v2_rows)
    secondary = Counter(row["secondary_layer"] or "(empty)" for row in v2_rows)
    _require(primary == Counter({"L5": 9, "UNRESOLVED": 11}), f"primary drift {primary}")
    _require(healer == Counter({"abstain": 20}), f"healer drift {healer}")
    _require(confidence == Counter({"HIGH": 9, "LOW": 11}), f"confidence drift {confidence}")
    _require(outcome == Counter({"VALID_MODEL_OUTCOME": 20}), f"outcome drift {outcome}")
    _require(secondary == Counter({"(empty)": 20}), "secondary must be empty")
    _require(len(gaps) == 11, "gaps drift")
    _require(primary.get("L2", 0) == 0, "L2 must be 0")

    frozen_rows: list[dict[str, str]] = []
    for rank, row in enumerate(v2_rows, 1):
        frozen = deepcopy(row)
        frozen["freeze_rank"] = str(rank)
        frozen["frozen_from_revision"] = V2_DIR.name
        frozen["freeze_status"] = STATUS
        frozen["freeze_basis_verdict"] = FREEZE_BASIS_VERDICT
        # Ensure adjudication fields are unchanged copies.
        for field in RECORD_FIELDS:
            _require(frozen[field] == row[field], f"adjudication field mutated: {field}")
        frozen_rows.append(frozen)
    return frozen_rows, roster, gaps


def _freeze_report(rows: list[dict[str, str]]) -> str:
    primary = Counter(row["primary_layer"] for row in rows)
    return "\n".join(
        [
            "# Frozen batch：remaining101 batch01 20-cell provisional v2",
            "",
            f"**狀態：`{STATUS}`**",
            "",
            f"**Freeze basis：`{FREEZE_BASIS_VERDICT}`**",
            "",
            "## 來源",
            "",
            f"- provisional v2 records：`{V2_RECORDS_SHA256}`",
            f"- provisional v2 manifest：`{V2_MANIFEST_SHA256}`",
            f"- re-audit v2 manifest：`{REAUDIT_MANIFEST_SHA256}`",
            f"- next20 roster：`{NEXT20_SHA256}`",
            "",
            "## 統計",
            "",
            f"- primary：{dict(sorted(primary.items()))}",
            "- secondary：全空",
            "- healer：abstain=20",
            "- confidence：HIGH=9，LOW=11",
            "- outcome：VALID_MODEL_OUTCOME=20",
            "- L2=0；unresolved gaps=11",
            "",
            "## 進度",
            "",
            f"- previously frozen={PREVIOUSLY_FROZEN}",
            f"- newly frozen={NEWLY_FROZEN}",
            f"- total frozen={TOTAL_FROZEN}",
            f"- remaining={REMAINING}",
            "",
            "本 freeze 無新裁決、無 candidate／模型執行；其餘 81 格尚未開始。",
        ]
    ) + "\n"


def _progress_report() -> str:
    return "\n".join(
        [
            "# Taxonomy v3.1 frozen progress census v2",
            "",
            f"**狀態：`{PROGRESS_STATUS}`**",
            "",
            "## 總進度",
            "",
            f"- formal population={FORMAL_POPULATION}",
            f"- previously frozen={PREVIOUSLY_FROZEN}",
            f"- newly frozen this revision={NEWLY_FROZEN}（remaining101 batch01）",
            f"- total frozen={TOTAL_FROZEN}",
            f"- remaining={REMAINING}",
            "",
            "## 研究敘述",
            "",
            "已凍結 117 格，剩餘 81 格；batch01 20 格全部 Healer abstain。"
            "不得把 batch01 結果外推至其餘 81 格，也不得宣稱全部 remaining101 已完成。",
            "",
            "## 邊界",
            "",
            "- 本 census 為新的 immutable progress revision，不覆寫 v1 progress census",
            "- 下一批尚未開始",
        ]
    ) + "\n"


def build_outputs(repo: Path = REPO_ROOT) -> dict[str, dict[str, bytes]]:
    frozen_rows, roster_rows, gaps = build_freeze_rows(repo)
    primary = Counter(row["primary_layer"] for row in frozen_rows)
    healer = Counter(row["healer_eligibility"] for row in frozen_rows)
    confidence = Counter(row["confidence"] for row in frozen_rows)
    unique_tasks = len({row["task_id"] for row in frozen_rows})
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

    # Prove adjudication payload matches provisional v2 records projection.
    v2_bytes = (repo / V2_RECORDS).read_bytes()
    projected = [{field: row[field] for field in RECORD_FIELDS} for row in frozen_rows]
    projected_bytes = _csv_bytes(RECORD_FIELDS, projected)
    _require(projected_bytes == v2_bytes, "frozen adjudication payload must match provisional v2 records bytes")

    freeze_summary = {
        "revision": FREEZE_OUTPUT.name,
        "status": STATUS,
        "freeze_basis_verdict": FREEZE_BASIS_VERDICT,
        "cells": TARGET_CELLS,
        "unique_program_id": TARGET_CELLS,
        "unique_source_sha256": TARGET_CELLS,
        "unique_task_id": unique_tasks,
        "primary_layer_distribution": dict(sorted(primary.items())),
        "secondary_nonempty_cells": 0,
        "healer_eligibility_distribution": dict(sorted(healer.items())),
        "confidence_distribution": dict(sorted(confidence.items())),
        "outcome_validity_distribution": {"VALID_MODEL_OUTCOME": 20},
        "true_adjudicated_L2_count": 0,
        "unresolved_gaps": 11,
        "previously_frozen": PREVIOUSLY_FROZEN,
        "newly_frozen": NEWLY_FROZEN,
        "total_frozen": TOTAL_FROZEN,
        "remaining": REMAINING,
        "provisional_v2_records_sha256": V2_RECORDS_SHA256,
        "provisional_v2_manifest_sha256": V2_MANIFEST_SHA256,
        "reaudit_v2_manifest_sha256": REAUDIT_MANIFEST_SHA256,
        "next20_roster_sha256": NEXT20_SHA256,
        "no_new_adjudication": True,
        "no_model_or_candidate_execution": True,
    }
    freeze_provenance = {
        **freeze_summary,
        "start_head": START_HEAD,
        "remaining101_roster_sha256": REMAINING101_SHA256,
        "taxonomy_v31_reference_sha256": census_prep.V31_REFERENCE_SHA256,
        "provisional_v1_records_sha256": V1_RECORDS_SHA256,
        "audit_v1_manifest_sha256": AUDIT_MANIFEST_SHA256,
        "prior_progress_census_manifest_sha256": PRIOR_PROGRESS_MANIFEST_SHA256,
        "source_hashes": {path.as_posix(): digest for path, digest in SOURCE_HASHES.items()},
        "analyzer": ANALYZER.as_posix(),
        "tests": TESTS.as_posix(),
        "upstream_modified": False,
        **execution_counts,
    }

    batch_registry = [
        {
            "batch_id": "previously_frozen_97",
            "cells": "97",
            "unique_program_id": "97",
            "unique_source_sha256": "",
            "unique_task_id": "",
            "source_revision": "candidate_b_r003_taxonomy_v3_frozen_progress_census_v1",
            "source_manifest_sha256": PRIOR_PROGRESS_MANIFEST_SHA256,
            "freeze_revision": "previously_frozen",
            "notes": "G2 27 + module_exception 37 + multiple_signal 13 + output_contract_shape 20",
        },
        {
            "batch_id": "remaining101_batch01_20",
            "cells": "20",
            "unique_program_id": "20",
            "unique_source_sha256": "20",
            "unique_task_id": str(unique_tasks),
            "source_revision": V2_DIR.name,
            "source_manifest_sha256": V2_MANIFEST_SHA256,
            "freeze_revision": FREEZE_OUTPUT.name,
            "notes": "this freeze; source-level units across tasks; not an extrapolation claim",
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
        "batch01_frozen_cells": NEWLY_FROZEN,
        "batch01_roster_sha256": NEXT20_SHA256,
        "batch01_freeze_revision": FREEZE_OUTPUT.name,
        "batch01_freeze_basis_verdict": FREEZE_BASIS_VERDICT,
        "batch01_primary_layer_distribution": dict(sorted(primary.items())),
        "batch01_healer_eligibility_distribution": dict(sorted(healer.items())),
        "next_batch_started": False,
        "research_statement_zh": (
            "已凍結117格，剩餘81格；batch01 20格全部Healer abstain。"
            "不得外推至其餘81格，不得宣稱remaining101已全部完成。"
        ),
        "overwrites_prior_census": False,
        **execution_counts,
    }
    progress_provenance = {
        **progress_summary,
        "start_head": START_HEAD,
        "prior_progress_census_manifest_sha256": PRIOR_PROGRESS_MANIFEST_SHA256,
        "provisional_v2_records_sha256": V2_RECORDS_SHA256,
        "reaudit_v2_manifest_sha256": REAUDIT_MANIFEST_SHA256,
        "immutable_new_revision": True,
        "analyzer": ANALYZER.as_posix(),
        "tests": TESTS.as_posix(),
    }

    return {
        "freeze": {
            Path("frozen_adjudication.csv"): _csv_bytes(FROZEN_FIELDS, frozen_rows),
            Path("frozen_roster.csv"): _csv_bytes(ROSTER_FIELDS, roster_rows),
            Path("frozen_unresolved_evidence_gaps.csv"): _csv_bytes(UNRESOLVED_GAP_FIELDS, gaps),
            Path("frozen_batch_summary.json"): _json_bytes(freeze_summary),
            Path("frozen_batch_report_zh.md"): _freeze_report(frozen_rows).encode("utf-8"),
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
        V1_RECORDS: V1_RECORDS_SHA256,
        AUDIT_MANIFEST: AUDIT_MANIFEST_SHA256,
        NEXT20: NEXT20_SHA256,
        REMAINING101: REMAINING101_SHA256,
        PRIOR_PROGRESS_MANIFEST: PRIOR_PROGRESS_MANIFEST_SHA256,
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
        "provisional_v2_records_sha256": V2_RECORDS_SHA256,
        "provisional_v2_manifest_sha256": V2_MANIFEST_SHA256,
        "reaudit_v2_manifest_sha256": REAUDIT_MANIFEST_SHA256,
        "next20_roster_sha256": NEXT20_SHA256,
        "remaining101_roster_sha256": REMAINING101_SHA256,
        "upstream_modified": False,
        "no_new_adjudication": True,
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
        "batch01_roster_sha256": NEXT20_SHA256,
        "freeze_basis_verdict": FREEZE_BASIS_VERDICT,
        "overwrites_prior_census": False,
        "next_batch_started": False,
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
    return freeze_dest, progress_dest


def main() -> None:
    freeze_path, progress_path = write_outputs()
    freeze_manifest = json.loads((freeze_path / "manifest.json").read_text(encoding="utf-8"))
    progress_manifest = json.loads((progress_path / "manifest.json").read_text(encoding="utf-8"))
    print(freeze_path)
    print(progress_path)
    print(f"freeze_manifest_sha={_sha((freeze_path / 'manifest.json').read_bytes())}")
    print(f"progress_manifest_sha={_sha((progress_path / 'manifest.json').read_bytes())}")
    print(f"total_frozen={freeze_manifest['total_frozen']} remaining={freeze_manifest['remaining']}")
    print(f"progress_remaining={progress_manifest['remaining']}")


if __name__ == "__main__":
    main()
