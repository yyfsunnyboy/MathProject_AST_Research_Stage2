#!/usr/bin/env python3
"""Provisional adjudication v2 for remaining101 batch01 (20 cells).

AI_ASSISTED_PROVISIONAL_ADJUDICATION_NOT_FORMAL_HUMAN_REVIEW

Applies only the single MATERIAL correction from post-adjudication audit v1:
Mbpp/103 (bfa80269…) UNRESOLVED/LOW → L5/HIGH with mechanism upgrades.
Does not overwrite provisional v1, audit v1, census, next20, or frozen97.
Does not execute candidates, diagnostics, Healer, or models.
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
    from scripts import prepare_candidate_b_r003_taxonomy_v3_formal_classification as preparation
    from scripts import (
        prepare_candidate_b_r003_taxonomy_v31_remaining101_zero_execution_census_v1 as census_prep,
    )
    from scripts import (
        adjudicate_candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_provisional_v1 as provisional_v1,
    )
    from scripts import (
        audit_candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_post_adjudication_v1 as audit_v1,
    )
except ModuleNotFoundError as exc:
    if exc.name != "scripts":
        raise
    import prepare_candidate_b_r003_taxonomy_v3_formal_classification as preparation
    import prepare_candidate_b_r003_taxonomy_v31_remaining101_zero_execution_census_v1 as census_prep
    import adjudicate_candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_provisional_v1 as provisional_v1
    import audit_candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_post_adjudication_v1 as audit_v1


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_provisional_v2"
)
START_HEAD = "b5a425bd9fb3b698fd83a66e25b01b979feba96b"
STATUS = "AI_ASSISTED_PROVISIONAL_ADJUDICATION_NOT_FORMAL_HUMAN_REVIEW"
ANALYZER = Path(
    "scripts/adjudicate_candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_provisional_v2.py"
)
TESTS = Path(
    "tests/finals_rebuild/"
    "test_candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_provisional_v2.py"
)
ADJUDICATOR_IDENTITY = "taxonomy_v31_batch01_provisional_v2_static_adjudicator"
ADJUDICATION_TIMESTAMP = "2026-07-21T15:03:00+08:00"

TARGET_CELLS = 20
TARGET_PROGRAM_ID = "bfa80269cd8ac74c1987bbbac1e79a24054e0e85f65cf1a4afe972f89b56e57b"
TARGET_TASK_ID = "Mbpp/103"
TARGET_SOURCE_SHA256 = "ee91cbd1e4e843a20ad5e517135995220881374956c3be0191c2a442ddafbd77"

V1_DIR = provisional_v1.OUTPUT_RELATIVE
V1_RECORDS = V1_DIR / "adjudication_records.csv"
V1_ROSTER = V1_DIR / "adjudication_roster.csv"
V1_SUMMARY = V1_DIR / "adjudication_summary.json"
V1_MANIFEST = V1_DIR / "manifest.json"
V1_PROVENANCE = V1_DIR / "provenance.json"
V1_EXECUTION = V1_DIR / "execution_counts.json"
V1_MECHANISM = V1_DIR / "mechanism_counts.json"
V1_HEALER = V1_DIR / "healer_eligibility_summary.json"
V1_GAPS = V1_DIR / "unresolved_evidence_gaps.csv"
V1_REPORT = V1_DIR / "adjudication_report_zh.md"

V1_RECORDS_SHA256 = "e08f1eab72275d7c37884883b1a439438daee6a2be0d8df408ba758b2364990b"
V1_ROSTER_SHA256 = "9f475868806c9a73bd25f96cb2c731f6357cafe0e6e08b53aa1fd0a374f13533"
V1_SUMMARY_SHA256 = "82b92391e56b92fead7237c29121b74526d77042e0df1d595897383f8f6bb5bb"
V1_MANIFEST_SHA256 = "710ef4fd707291db650e5b14d5594ed7920f1a9c2370ee3d5cde2f09a24a627e"
V1_PROVENANCE_SHA256 = "45bdf1a8b32258365a85643e4ce2b8d3828f6b7e82072a6c31af5e6203b3a74c"
V1_EXECUTION_SHA256 = "a2689e5b6dca7db3a16ca8460cda80476eea60a6907dda92bee875e294f3d4a7"
V1_MECHANISM_SHA256 = "992c179dc80b5732649354908905184ac3034ceb270d7dea4ef19a456373f1e8"
V1_HEALER_SHA256 = "2c1cc13e6742b52c599ce6d88fe642f5c7a35753f015e596698a538d6a9eb78a"
V1_GAPS_SHA256 = "93e359567abbb1572cfa980d7a2a7995d5ca7bbc1c3b7d7e52035cde1db4257e"
V1_REPORT_SHA256 = "301b354a18fbcd3e93661b7106102d41d9a8f26408f7a2f67b9f81d1439c5ea2"
V1_ANALYZER_SHA256 = "f13d14593c08b6455911c6195024327136d83abd05f9b35dc995c1fcf2c183d3"

AUDIT_DIR = audit_v1.OUTPUT_RELATIVE
AUDIT_MANIFEST = AUDIT_DIR / "manifest.json"
AUDIT_SUMMARY = AUDIT_DIR / "audit_summary.json"
AUDIT_RECORDS = AUDIT_DIR / "per_cell_audit_records.csv"
AUDIT_FINDINGS = AUDIT_DIR / "audit_findings.csv"
AUDIT_MANIFEST_SHA256 = "37438e79a8aa5ac68edafa5291c5c0601085dbdf96b3a92015e2b4de20905adf"
AUDIT_SUMMARY_SHA256 = "96df5df91f27e211715995d4005d65490999b955f1bfca2828fce4967eac17eb"
AUDIT_RECORDS_SHA256 = "997b7ff0bbf588c000a794f4b2f96dafbcb643cbafb12eb88eb1500dd3802ebe"
AUDIT_FINDINGS_SHA256 = "ab33751e000136da4713b24292b388979e9ed641f492cac366dad3c32c30fb92"
AUDIT_ANALYZER_SHA256 = "27190416b88eaf3a7777337a98b34b5da5b6f7643888c9b55f9be03483994863"

CENSUS_DIR = census_prep.OUTPUT_RELATIVE
NEXT20 = CENSUS_DIR / "next_adjudication_batch_roster.csv"
REMAINING101 = CENSUS_DIR / "remaining101_roster.csv"
CENSUS_MANIFEST = CENSUS_DIR / "manifest.json"
NEXT20_SHA256 = "a22f086ba7d61995de98dafd57edcbdcb01fe46e780bd595163a6eabf813eb91"
REMAINING101_SHA256 = "8fe0f5d95e7c6e86cda5f18dabfecae486120c50eeaf1baad6fe6c12b23143f6"
CENSUS_MANIFEST_SHA256 = "d2a7478da6852ba1a6592d2d1701b8ad3aee3bc018824a365aab9670fa0438bd"

# Fields compared for semantic cell identity (exclude revision metadata).
SEMANTIC_FIELDS = (
    "batch_rank",
    "cell_id",
    "program_id",
    "source_sha256",
    "task_id",
    "dataset",
    "model",
    "condition",
    "seed",
    "generation_id",
    "raw_generation_reference",
    "review_status",
    "outcome_validity",
    "primary_layer",
    "secondary_layer",
    "mechanism_tags_json",
    "failure_chain",
    "healer_eligibility",
    "abstain_reason",
    "eligibility_rule",
    "rejection_condition",
    "unresolved_reason_code",
    "evidence_present",
    "evidence_missing",
    "minimal_future_diagnostic",
    "confidence",
    "evidence_citations",
    "source_structure_locator",
    "public_contract_locator",
    "evaluator_provenance_locator",
    "evidence_summary",
    "planning_signal_note",
)

ALLOWED_CHANGE_FIELDS = frozenset(
    {
        "primary_layer",
        "confidence",
        "failure_chain",
        "mechanism_tags_json",
        "unresolved_reason_code",
        "evidence_present",
        "evidence_missing",
        "minimal_future_diagnostic",
        "abstain_reason",
        "evidence_summary",
        "planning_signal_note",
        "evidence_citations",
        "adjudicator_identity",
        "adjudication_timestamp",
    }
)

RECORD_FIELDS = provisional_v1.RECORD_FIELDS
ROSTER_FIELDS = provisional_v1.ROSTER_FIELDS
UNRESOLVED_GAP_FIELDS = provisional_v1.UNRESOLVED_GAP_FIELDS

SOURCE_HASHES: dict[Path, str] = {
    preparation.JOURNAL: preparation.SOURCE_HASHES[preparation.JOURNAL],
    preparation.TASKS: preparation.SOURCE_HASHES[preparation.TASKS],
    NEXT20: NEXT20_SHA256,
    REMAINING101: REMAINING101_SHA256,
    CENSUS_MANIFEST: CENSUS_MANIFEST_SHA256,
    V1_RECORDS: V1_RECORDS_SHA256,
    V1_ROSTER: V1_ROSTER_SHA256,
    V1_SUMMARY: V1_SUMMARY_SHA256,
    V1_MANIFEST: V1_MANIFEST_SHA256,
    V1_PROVENANCE: V1_PROVENANCE_SHA256,
    V1_EXECUTION: V1_EXECUTION_SHA256,
    V1_MECHANISM: V1_MECHANISM_SHA256,
    V1_HEALER: V1_HEALER_SHA256,
    V1_GAPS: V1_GAPS_SHA256,
    V1_REPORT: V1_REPORT_SHA256,
    provisional_v1.ANALYZER: V1_ANALYZER_SHA256,
    AUDIT_MANIFEST: AUDIT_MANIFEST_SHA256,
    AUDIT_SUMMARY: AUDIT_SUMMARY_SHA256,
    AUDIT_RECORDS: AUDIT_RECORDS_SHA256,
    AUDIT_FINDINGS: AUDIT_FINDINGS_SHA256,
    audit_v1.ANALYZER: AUDIT_ANALYZER_SHA256,
    census_prep.G2_PROVISIONAL_CSV: census_prep.G2_PROVISIONAL_CSV_SHA256,
    census_prep.MODULE_EXCEPTION_CSV: census_prep.MODULE_EXCEPTION_CSV_SHA256,
    census_prep.MULTIPLE_SIGNAL_CSV: census_prep.MULTIPLE_SIGNAL_CSV_SHA256,
    census_prep.FREEZE20_CSV: census_prep.FREEZE20_CSV_SHA256,
}


class AdjudicationError(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AdjudicationError(message)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


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


def _mech_counts(rows: list[dict[str, str]]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for row in rows:
        for item in json.loads(row["mechanism_tags_json"]):
            counter[item["status"]] += 1
    return counter


def _tag_counts(rows: list[dict[str, str]]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for row in rows:
        for item in json.loads(row["mechanism_tags_json"]):
            counter[item["tag"]] += 1
    return counter


def _apply_mbpp103_correction(row: dict[str, str]) -> dict[str, str]:
    updated = deepcopy(row)
    _require(updated["program_id"] == TARGET_PROGRAM_ID, "target program_id mismatch")
    _require(updated["task_id"] == TARGET_TASK_ID, "target task_id mismatch")
    _require(updated["source_sha256"] == TARGET_SOURCE_SHA256, "target source sha mismatch")
    _require(updated["primary_layer"] == "UNRESOLVED", "v1 primary must be UNRESOLVED")
    _require(updated["confidence"] == "LOW", "v1 confidence must be LOW")
    _require(updated["healer_eligibility"] == "abstain", "v1 healer must be abstain")

    mechanisms = [
        {
            "tag": "incorrect_formula",
            "status": "CONFIRMED",
            "note": (
                "STATIC structural expansion (not a new execution): nested loops never write "
                "A[3][1]; return A[n][m] remains initializer 0, contradicting public assert ==4"
            ),
        },
        {
            "tag": "algorithm_reconstruction_required",
            "status": "CONFIRMED",
            "note": "DP write-set/boundary design wrong; repair requires reconstructing recurrence",
        },
        {
            "tag": "public_examples_non_discriminating",
            "status": "REJECTED",
            "note": "public assert eulerian_num(3,1)==4 uniquely closes L5 via static expansion",
        },
        {
            "tag": "diagnostic_execution_required",
            "status": "REJECTED",
            "note": "no longer required after static A[3][1]=0 proof",
        },
        {
            "tag": "runtime_vs_semantic_not_closed",
            "status": "REJECTED",
            "note": "semantic/algorithm layer closed; not an L4/L5 ambiguity",
        },
        {
            "tag": "return_shape_mismatch",
            "status": "REJECTED",
            "note": "int scalar return family matches; planning signal is not root cause",
        },
        {
            "tag": "entry_point_unique_candidate",
            "status": "REJECTED",
            "note": "expected entry point present; not an error",
        },
    ]

    citations = json.loads(updated["evidence_citations"])
    citations.append(
        {
            "kind": "post_adjudication_audit",
            "path": (AUDIT_DIR / "per_cell_audit_records.csv").as_posix(),
            "locator": f"program_id={TARGET_PROGRAM_ID};primary_layer_verdict=CHALLENGED",
        }
    )
    citations.append(
        {
            "kind": "post_adjudication_finding",
            "path": (AUDIT_DIR / "audit_findings.csv").as_posix(),
            "locator": f"program_id={TARGET_PROGRAM_ID};materiality=MATERIAL",
        }
    )

    updated["primary_layer"] = "L5"
    updated["secondary_layer"] = ""
    updated["confidence"] = "HIGH"
    updated["healer_eligibility"] = "abstain"
    updated["review_status"] = "ADJUDICATED"
    updated["outcome_validity"] = "VALID_MODEL_OUTCOME"
    updated["unresolved_reason_code"] = ""
    updated["evidence_missing"] = ""
    updated["minimal_future_diagnostic"] = ""
    updated["evidence_present"] = (
        "public assert eulerian_num(3,1)==4; static DP write-path expansion showing A[3][1] never updated"
    )
    updated["mechanism_tags_json"] = _json(mechanisms)
    updated["failure_chain"] = (
        "STATIC DP table/loop-boundary expansion (not a new candidate execution) → "
        "A[3][1] is never written by any i/j update path → "
        "return A[n][m] reads that uninitialized slot as 0 for public input (3,1) → "
        "contradicts public assert requiring 4 → "
        "root cause is DP state-transition/boundary design → "
        "repair requires reconstructing algorithmic semantics → "
        "primary=L5 → deterministic Healer abstain"
    )
    updated["abstain_reason"] = (
        "L5 DP algorithm reconstruction is not a unique contract-local safe edit; "
        "deterministic Healer abstain."
    )
    updated["evidence_summary"] = (
        "Post-adjudication audit MATERIAL correction: static expansion of the written "
        "DP loops shows A[3][1] is never assigned, so eulerian_num(3,1) structurally "
        "returns initializer 0 ≠ public assert 4. This is structural static reasoning, "
        "not a newly executed candidate run. HIGH L5 closed; healer remains abstain."
    )
    updated["planning_signal_note"] = (
        "audit_v1_material_correction; return_shape planning signal remains rejected as root cause"
    )
    updated["evidence_citations"] = _json(citations)
    updated["adjudicator_identity"] = ADJUDICATOR_IDENTITY
    updated["adjudication_timestamp"] = ADJUDICATION_TIMESTAMP
    updated["eligibility_rule"] = ""
    updated["rejection_condition"] = ""
    return updated


def build_analysis(repo: Path = REPO_ROOT) -> dict[str, Any]:
    verify_sources(repo)
    audit_summary = json.loads((repo / AUDIT_SUMMARY).read_text(encoding="utf-8"))
    _require(
        audit_summary["overall_verdict"] == "POST_ADJUDICATION_REVISION_REQUIRED",
        "audit verdict drift",
    )
    _require(audit_summary["primary_layer_verdict_distribution"] == {"AFFIRMED": 19, "CHALLENGED": 1}, "audit AFFIRMED/CHALLENGED drift")
    _require(audit_summary["correction_materiality_distribution"] == {"MATERIAL": 1, "NONE": 19}, "audit materiality drift")
    _require(
        audit_summary["cells_requiring_provisional_v2"] == [TARGET_PROGRAM_ID],
        "audit target cell drift",
    )

    v1_rows = _read_csv(repo / V1_RECORDS)
    v1_roster = _read_csv(repo / V1_ROSTER)
    next20 = _read_csv(repo / NEXT20)
    _require(len(v1_rows) == TARGET_CELLS, "v1 records count drift")
    _require([row["program_id"] for row in v1_rows] == [row["program_id"] for row in next20], "v1/next20 identity drift")
    _require([row["program_id"] for row in v1_roster] == [row["program_id"] for row in next20], "roster/next20 drift")

    v2_rows: list[dict[str, str]] = []
    changed = 0
    for row in v1_rows:
        if row["program_id"] == TARGET_PROGRAM_ID:
            v2_rows.append(_apply_mbpp103_correction(row))
            changed += 1
        else:
            v2_rows.append(deepcopy(row))
    _require(changed == 1, "exactly one cell must change")

    # Semantic diff constraints.
    diffs: list[dict[str, Any]] = []
    for v1_row, v2_row in zip(v1_rows, v2_rows, strict=True):
        field_diffs = {
            field: {"from": v1_row[field], "to": v2_row[field]}
            for field in SEMANTIC_FIELDS
            if v1_row.get(field, "") != v2_row.get(field, "")
        }
        meta_diffs = {
            field: {"from": v1_row[field], "to": v2_row[field]}
            for field in ("adjudicator_identity", "adjudication_timestamp")
            if v1_row.get(field, "") != v2_row.get(field, "")
        }
        if field_diffs or meta_diffs:
            _require(v1_row["program_id"] == TARGET_PROGRAM_ID, f"unexpected cell change: {v1_row['program_id']}")
            unexpected = set(field_diffs) - ALLOWED_CHANGE_FIELDS
            _require(not unexpected, f"disallowed field changes: {sorted(unexpected)}")
            diffs.append(
                {
                    "program_id": TARGET_PROGRAM_ID,
                    "task_id": TARGET_TASK_ID,
                    "semantic_field_diffs": field_diffs,
                    "revision_metadata_diffs": meta_diffs,
                }
            )
    _require(len(diffs) == 1, "must have exactly one changed cell")

    target = next(row for row in v2_rows if row["program_id"] == TARGET_PROGRAM_ID)
    _require(target["primary_layer"] == "L5", "target primary must be L5")
    _require(target["confidence"] == "HIGH", "target confidence must be HIGH")
    _require(target["healer_eligibility"] == "abstain", "target healer must abstain")
    _require(target["unresolved_reason_code"] == "", "target unresolved code must be cleared")
    _require(target["evidence_missing"] == "", "target evidence_missing must be cleared")
    _require(target["minimal_future_diagnostic"] == "", "target diagnostic must be cleared")

    gaps = [
        {
            "program_id": row["program_id"],
            "task_id": row["task_id"],
            "primary_layer": row["primary_layer"],
            "unresolved_reason_code": row["unresolved_reason_code"],
            "evidence_present": row["evidence_present"],
            "evidence_missing": row["evidence_missing"],
            "minimal_future_diagnostic": row["minimal_future_diagnostic"],
            "healer_eligibility": row["healer_eligibility"],
        }
        for row in v2_rows
        if row["primary_layer"] == "UNRESOLVED"
    ]
    _require(len(gaps) == 11, f"expected 11 unresolved gaps, got {len(gaps)}")
    _require(TARGET_PROGRAM_ID not in {row["program_id"] for row in gaps}, "target still in gaps")

    primary = Counter(row["primary_layer"] for row in v2_rows)
    secondary = Counter(row["secondary_layer"] or "(empty)" for row in v2_rows)
    confidence = Counter(row["confidence"] for row in v2_rows)
    healer = Counter(row["healer_eligibility"] for row in v2_rows)
    outcome = Counter(row["outcome_validity"] for row in v2_rows)
    _require(primary == Counter({"L5": 9, "UNRESOLVED": 11}), f"primary drift: {primary}")
    _require(confidence == Counter({"HIGH": 9, "LOW": 11}), f"confidence drift: {confidence}")
    _require(healer == Counter({"abstain": 20}), f"healer drift: {healer}")
    _require(outcome == Counter({"VALID_MODEL_OUTCOME": 20}), f"outcome drift: {outcome}")
    _require(primary.get("L2", 0) == 0, "L2 must remain 0")

    v1_mech_status = _mech_counts(v1_rows)
    v2_mech_status = _mech_counts(v2_rows)
    v1_mech_tags = _tag_counts(v1_rows)
    v2_mech_tags = _tag_counts(v2_rows)

    summary = {
        "status": STATUS,
        "cells": TARGET_CELLS,
        "unique_program_id": len({row["program_id"] for row in v2_rows}),
        "unique_source_sha256": len({row["source_sha256"] for row in v2_rows}),
        "unique_task_id": len({row["task_id"] for row in v2_rows}),
        "primary_layer_distribution": dict(sorted(primary.items())),
        "secondary_layer_distribution": dict(sorted(secondary.items())),
        "confidence_distribution": dict(sorted(confidence.items())),
        "healer_eligibility_distribution": dict(sorted(healer.items())),
        "outcome_validity_distribution": dict(sorted(outcome.items())),
        "true_adjudicated_L2_count": 0,
        "material_correction_cells": 1,
        "unchanged_cells": 19,
        "cells_needing_future_diagnostics": sum(
            1 for row in v2_rows if row["minimal_future_diagnostic"]
        ),
        "based_on_provisional_v1_records_sha256": V1_RECORDS_SHA256,
        "based_on_audit_v1_manifest_sha256": AUDIT_MANIFEST_SHA256,
        "single_material_correction": {
            "program_id": TARGET_PROGRAM_ID,
            "task_id": TARGET_TASK_ID,
            "source_sha256": TARGET_SOURCE_SHA256,
            "transition": "UNRESOLVED/LOW → L5/HIGH",
            "healer": "abstain (unchanged decision)",
        },
    }

    revision_transition = {
        "changed_cells": 1,
        "unchanged_cells": 19,
        "primary_transitions": {"UNRESOLVED→L5": 1, "unchanged": 19},
        "confidence_transitions": {"LOW→HIGH": 1, "unchanged": 19},
        "healer_transitions": {"abstain→abstain": 1, "unchanged": 19},
        "semantic_diffs": diffs,
        "allowed_change_fields": sorted(ALLOWED_CHANGE_FIELDS),
        "note": "Only Mbpp/103 has substantive adjudication field changes.",
    }

    mechanism_counts = {
        "by_status": dict(sorted(v2_mech_status.items())),
        "by_tag": dict(sorted(v2_mech_tags.items())),
        "note": "recomputed from v2 records; not hard-coded",
    }

    mechanism_transition = {
        "v1_by_status": dict(sorted(v1_mech_status.items())),
        "v2_by_status": dict(sorted(v2_mech_status.items())),
        "status_delta": {
            status: int(v2_mech_status.get(status, 0) - v1_mech_status.get(status, 0))
            for status in sorted(set(v1_mech_status) | set(v2_mech_status))
        },
        "mbpp103_mechanism_policy": {
            "incorrect_formula": "SUSPECTED→CONFIRMED",
            "algorithm_reconstruction_required": "SUSPECTED→CONFIRMED",
            "public_examples_non_discriminating": "SUPPORTED→REJECTED",
            "diagnostic_execution_required": "CONFIRMED→REJECTED",
            "runtime_vs_semantic_not_closed": "SUPPORTED→REJECTED",
            "return_shape_mismatch": "SUSPECTED→REJECTED",
            "entry_point_unique_candidate": "REJECTED→REJECTED",
        },
        "note": (
            "Expected naive +2 CONFIRMED/-2 SUSPECTED only if unresolved-binding tags were left "
            "untouched; audit requires rejecting those tags, so status totals differ from that naive forecast."
        ),
    }

    healer_summary = {
        "distribution": dict(sorted(healer.items())),
        "eligible_count": 0,
        "conditional_count": 0,
        "abstain_count": 20,
        "rule": "Mbpp/103 remains abstain; no new Healer candidates introduced.",
    }

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

    return {
        "v1_rows": v1_rows,
        "v2_rows": v2_rows,
        "roster_rows": v1_roster,
        "gaps": gaps,
        "summary": summary,
        "revision_transition": revision_transition,
        "mechanism_counts": mechanism_counts,
        "mechanism_transition": mechanism_transition,
        "healer_summary": healer_summary,
        "execution_counts": execution_counts,
    }


def _report(analysis: dict[str, Any], records_sha: str) -> str:
    s = analysis["summary"]
    mt = analysis["mechanism_transition"]
    lines = [
        "# Candidate B r003 taxonomy v3.1：remaining101 batch01 20-cell provisional v2",
        "",
        f"**狀態：`{STATUS}`**",
        "",
        "## 修訂範圍",
        "",
        "- 僅套用 post-adjudication audit v1 的單一 MATERIAL correction：Mbpp/103。",
        "- provisional v1／audit v1／census／next20／frozen97 均未修改。",
        "- 19 格裁決內容逐語意沿用 v1；不重審、不新增 Healer 候選、不執行 candidate。",
        "",
        "## Mbpp/103",
        "",
        f"- program_id：`{TARGET_PROGRAM_ID}`",
        f"- source_sha256：`{TARGET_SOURCE_SHA256}`",
        "- UNRESOLVED/LOW → **L5/HIGH**；healer 維持 **abstain**",
        "- 靜態 DP 展開證明 `A[3][1]` 從未寫入 → 結構上回傳初始化 0 ≠ 公開 assert 4",
        "- 非新執行觀察；failure_chain 明確標示 STATIC expansion",
        "",
        "## 統計（由 v2 records 重建）",
        "",
        f"- primary：{s['primary_layer_distribution']}",
        f"- confidence：{s['confidence_distribution']}",
        f"- healer：{s['healer_eligibility_distribution']}",
        f"- outcome：{s['outcome_validity_distribution']}",
        f"- unresolved gaps remaining：{len(analysis['gaps'])}",
        f"- mechanism status v1→v2：{mt['v1_by_status']} → {mt['v2_by_status']}",
        f"- status delta：{mt['status_delta']}",
        f"- records SHA-256：`{records_sha}`",
        "",
        "## 停止點",
        "",
        "- 不進行 re-audit／freeze／commit／push（本輪）。",
        "",
    ]
    return "\n".join(lines) + "\n"


def build_outputs(repo: Path = REPO_ROOT) -> dict[str, bytes]:
    analysis = build_analysis(repo)
    roster_bytes = _csv_bytes(ROSTER_FIELDS, analysis["roster_rows"])
    records_bytes = _csv_bytes(RECORD_FIELDS, analysis["v2_rows"])
    gaps_bytes = _csv_bytes(UNRESOLVED_GAP_FIELDS, analysis["gaps"])
    summary_bytes = _json_bytes(analysis["summary"])
    transition_bytes = _json_bytes(analysis["revision_transition"])
    mechanism_bytes = _json_bytes(analysis["mechanism_counts"])
    mechanism_transition_bytes = _json_bytes(analysis["mechanism_transition"])
    healer_bytes = _json_bytes(analysis["healer_summary"])
    execution_bytes = _json_bytes(analysis["execution_counts"])
    records_sha = _sha(records_bytes)
    roster_sha = _sha(roster_bytes)
    report_bytes = _report(analysis, records_sha).encode("utf-8")

    outputs_wo = {
        "adjudication_roster.csv": roster_bytes,
        "adjudication_records.csv": records_bytes,
        "adjudication_summary.json": summary_bytes,
        "revision_transition.json": transition_bytes,
        "mechanism_counts.json": mechanism_bytes,
        "mechanism_transition.json": mechanism_transition_bytes,
        "unresolved_evidence_gaps.csv": gaps_bytes,
        "healer_eligibility_summary.json": healer_bytes,
        "adjudication_report_zh.md": report_bytes,
        "execution_counts.json": execution_bytes,
    }
    outputs_sha = {name: _sha(data) for name, data in outputs_wo.items()}

    provenance = {
        "revision": OUTPUT_RELATIVE.as_posix(),
        "status": STATUS,
        "start_head": START_HEAD,
        "based_on_provisional_v1": {
            "path": V1_DIR.as_posix(),
            "records_sha256": V1_RECORDS_SHA256,
            "roster_sha256": V1_ROSTER_SHA256,
            "manifest_sha256": V1_MANIFEST_SHA256,
        },
        "based_on_post_adjudication_audit_v1": {
            "path": AUDIT_DIR.as_posix(),
            "manifest_sha256": AUDIT_MANIFEST_SHA256,
            "summary_sha256": AUDIT_SUMMARY_SHA256,
            "verdict": "POST_ADJUDICATION_REVISION_REQUIRED",
        },
        "next20_roster_sha256": NEXT20_SHA256,
        "remaining101_roster_sha256": REMAINING101_SHA256,
        "taxonomy_v31_planning_reference": {
            "filename": census_prep.V31_REFERENCE_FILENAME,
            "sha256": census_prep.V31_REFERENCE_SHA256,
            "status": census_prep.V31_REFERENCE_STATUS,
        },
        "single_material_correction_program_id": TARGET_PROGRAM_ID,
        "adjudication_records_sha256": records_sha,
        "adjudication_roster_sha256": roster_sha,
        "primary_layer_distribution": analysis["summary"]["primary_layer_distribution"],
        "healer_eligibility_distribution": analysis["summary"]["healer_eligibility_distribution"],
        "source_hashes": {path.as_posix(): digest for path, digest in SOURCE_HASHES.items()},
        "analyzer": ANALYZER.as_posix(),
        "tests": TESTS.as_posix(),
        "provisional_v1_modified": False,
        "audit_v1_modified": False,
        "frozen_marker_written": False,
        "no_new_candidate_execution": True,
        "no_model_calls": True,
        **analysis["execution_counts"],
    }
    provenance_bytes = _json_bytes(provenance)
    outputs_wo["provenance.json"] = provenance_bytes
    outputs_sha["provenance.json"] = _sha(provenance_bytes)

    manifest = {
        "revision": OUTPUT_RELATIVE.as_posix(),
        "status": STATUS,
        "start_head": START_HEAD,
        "cells": TARGET_CELLS,
        "provisional_v1_records_sha256": V1_RECORDS_SHA256,
        "provisional_v1_roster_sha256": V1_ROSTER_SHA256,
        "audit_v1_manifest_sha256": AUDIT_MANIFEST_SHA256,
        "next20_roster_sha256": NEXT20_SHA256,
        "remaining101_roster_sha256": REMAINING101_SHA256,
        "adjudication_records_sha256": records_sha,
        "adjudication_roster_sha256": roster_sha,
        "primary_layer_distribution": analysis["summary"]["primary_layer_distribution"],
        "confidence_distribution": analysis["summary"]["confidence_distribution"],
        "healer_eligibility_distribution": analysis["summary"]["healer_eligibility_distribution"],
        "material_correction_program_id": TARGET_PROGRAM_ID,
        "outputs_sha256_excluding_manifest": outputs_sha,
        "analyzer": ANALYZER.as_posix(),
        "tests": TESTS.as_posix(),
        "provisional_v1_modified": False,
        "audit_v1_modified": False,
        "frozen_marker_written": False,
        **analysis["execution_counts"],
    }
    outputs = dict(outputs_wo)
    outputs["manifest.json"] = _json_bytes(manifest)
    return outputs


def write_outputs(repo: Path = REPO_ROOT) -> Path:
    # Pin audit analyzer hash at write-time verification via SOURCE_HASHES already checked.
    output_dir = repo / OUTPUT_RELATIVE
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, data in build_outputs(repo).items():
        (output_dir / name).write_bytes(data)
    return output_dir


def main() -> None:
    output_dir = write_outputs(REPO_ROOT)
    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    print(f"wrote {output_dir}")
    print(f"primary={manifest['primary_layer_distribution']}")
    print(f"confidence={manifest['confidence_distribution']}")
    print(f"healer={manifest['healer_eligibility_distribution']}")
    print(f"corrected={manifest['material_correction_program_id']}")


if __name__ == "__main__":
    main()
