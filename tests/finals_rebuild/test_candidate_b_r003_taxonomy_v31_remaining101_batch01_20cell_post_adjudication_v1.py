from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pytest

from scripts import (
    audit_candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_post_adjudication_v1 as audit,
)
from scripts import (
    adjudicate_candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_provisional_v1 as provisional,
)
from scripts import (
    prepare_candidate_b_r003_taxonomy_v31_remaining101_zero_execution_census_v1 as census_prep,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / audit.OUTPUT_RELATIVE
PROV_DIR = REPO_ROOT / provisional.OUTPUT_RELATIVE
CENSUS_DIR = REPO_ROOT / census_prep.OUTPUT_RELATIVE


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def materialized() -> Path:
    if OUTPUT_DIR.exists() and (OUTPUT_DIR / "manifest.json").is_file():
        return OUTPUT_DIR
    return audit.write_outputs(REPO_ROOT)


@pytest.mark.parametrize("relative,expected", list(audit.SOURCE_HASHES.items()))
def test_pinned_sources_byte_stable(relative: Path, expected: str):
    path = relative if relative.is_absolute() else REPO_ROOT / relative
    assert _digest(path) == expected


def test_provisional_and_census_unchanged():
    assert _digest(PROV_DIR / "adjudication_records.csv") == audit.PROV_RECORDS_SHA256
    assert _digest(PROV_DIR / "manifest.json") == audit.PROV_MANIFEST_SHA256
    assert _digest(CENSUS_DIR / "next_adjudication_batch_roster.csv") == audit.NEXT20_SHA256
    assert _digest(CENSUS_DIR / "remaining101_roster.csv") == audit.REMAINING101_SHA256


def test_twenty_cell_identity_closure(materialized: Path):
    cells = _rows(materialized / "per_cell_audit_records.csv")
    next20 = _rows(CENSUS_DIR / "next_adjudication_batch_roster.csv")
    prov = _rows(PROV_DIR / "adjudication_records.csv")
    assert len(cells) == 20
    assert [row["program_id"] for row in cells] == [row["program_id"] for row in next20]
    assert [row["program_id"] for row in cells] == [row["program_id"] for row in prov]
    assert len({row["source_sha256"] for row in cells}) == 20


def test_each_cell_has_materiality_and_verdicts(materialized: Path):
    cells = _rows(materialized / "per_cell_audit_records.csv")
    for row in cells:
        assert row["primary_layer_verdict"] in audit.VALID_PRIMARY_VERDICT
        assert row["correction_materiality"] in audit.VALID_MATERIALITY
        assert row["auditor_identity"] == audit.AUDITOR_IDENTITY
        if row["primary_layer_verdict"] == "CHALLENGED":
            assert row["correction_materiality"] == "MATERIAL"
            assert row["requires_provisional_v2"] == "true"
            assert row["required_correction"]


def test_material_challenge_on_mbpp103(materialized: Path):
    cells = {row["program_id"]: row for row in _rows(materialized / "per_cell_audit_records.csv")}
    pid = "bfa80269cd8ac74c1987bbbac1e79a24054e0e85f65cf1a4afe972f89b56e57b"
    assert cells[pid]["provisional_primary_layer"] == "UNRESOLVED"
    assert cells[pid]["audited_primary_layer"] == "L5"
    assert cells[pid]["primary_layer_verdict"] == "CHALLENGED"
    assert cells[pid]["correction_materiality"] == "MATERIAL"


def test_l5_eight_and_remaining_unresolved_affirmed_or_challenged(materialized: Path):
    cells = _rows(materialized / "per_cell_audit_records.csv")
    l5 = [row for row in cells if row["provisional_primary_layer"] == "L5"]
    unresolved = [row for row in cells if row["provisional_primary_layer"] == "UNRESOLVED"]
    assert len(l5) == 8
    assert len(unresolved) == 12
    assert all(row["primary_layer_verdict"] == "AFFIRMED" for row in l5)
    challenged = [row for row in unresolved if row["primary_layer_verdict"] == "CHALLENGED"]
    affirmed = [row for row in unresolved if row["primary_layer_verdict"] == "AFFIRMED"]
    assert len(challenged) == 1
    assert len(affirmed) == 11


def test_l2_reverse_and_healer_abstain(materialized: Path):
    summary = json.loads((materialized / "audit_summary.json").read_text(encoding="utf-8"))
    healer = json.loads((materialized / "healer_decision_audit.json").read_text(encoding="utf-8"))
    assert summary["l2_reverse_audit"]["verdict"] == "AFFIRMED_L2_EQUALS_ZERO"
    assert healer["abstain"] == 20
    assert healer["eligible"] == 0
    assert healer["conditional"] == 0
    cells = _rows(materialized / "per_cell_audit_records.csv")
    assert all(row["l2_reverse_audit_verdict"] == "AFFIRMED" for row in cells)
    assert all(row["healer_decision_verdict"] == "AFFIRMED" for row in cells)


def test_overall_verdict_requires_revision(materialized: Path):
    summary = json.loads((materialized / "audit_summary.json").read_text(encoding="utf-8"))
    manifest = json.loads((materialized / "manifest.json").read_text(encoding="utf-8"))
    assert summary["overall_verdict"] == "POST_ADJUDICATION_REVISION_REQUIRED"
    assert manifest["overall_verdict"] == "POST_ADJUDICATION_REVISION_REQUIRED"
    assert summary["ready_to_plan_freeze"] is False
    assert len(summary["cells_requiring_provisional_v2"]) == 1


def test_execution_counts_zero_and_no_overwrite_flags(materialized: Path):
    for name in ("execution_counts.json", "manifest.json", "provenance.json"):
        doc = json.loads((materialized / name).read_text(encoding="utf-8"))
        for key in (
            "model_calls",
            "candidate_executions",
            "candidate_imports",
            "public_test_executions",
            "hidden_test_executions",
            "evalplus_correctness_executions",
            "diagnostics_executions",
            "validation_executions",
            "healer_executions",
            "programs_executed",
        ):
            assert doc[key] == 0
    manifest = json.loads((materialized / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["provisional_v1_modified"] is False
    assert manifest["frozen_marker_written"] is False


def test_deterministic_rebuild(materialized: Path):
    rebuilt = audit.build_outputs(REPO_ROOT)
    for name, data in rebuilt.items():
        assert data == (materialized / name).read_bytes()


def test_py_compile():
    compile((REPO_ROOT / audit.ANALYZER).read_text(encoding="utf-8"), str(audit.ANALYZER), "exec")
