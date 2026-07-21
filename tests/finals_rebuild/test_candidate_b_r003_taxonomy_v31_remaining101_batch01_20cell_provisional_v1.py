from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import pytest

from scripts import (
    adjudicate_candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_provisional_v1 as adj,
)
from scripts import (
    prepare_candidate_b_r003_taxonomy_v31_remaining101_zero_execution_census_v1 as census_prep,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / adj.OUTPUT_RELATIVE
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
    return adj.write_outputs(REPO_ROOT)


@pytest.mark.parametrize("relative,expected", list(adj.SOURCE_HASHES.items()))
def test_pinned_sources_unchanged(relative: Path, expected: str):
    path = relative if relative.is_absolute() else REPO_ROOT / relative
    assert _digest(path) == expected


def test_census_and_next_batch_sha_closure():
    assert _digest(CENSUS_DIR / "remaining101_roster.csv") == adj.REMAINING101_ROSTER_SHA256
    assert _digest(CENSUS_DIR / "next_adjudication_batch_roster.csv") == adj.NEXT_BATCH_ROSTER_SHA256
    assert _digest(CENSUS_DIR / "manifest.json") == adj.CENSUS_MANIFEST_SHA256


def test_roster_is_exact_fixed_batch(materialized: Path):
    fixed = _rows(CENSUS_DIR / "next_adjudication_batch_roster.csv")
    roster = _rows(materialized / "adjudication_roster.csv")
    records = _rows(materialized / "adjudication_records.csv")
    assert len(fixed) == 20
    assert [r["program_id"] for r in roster] == [r["program_id"] for r in fixed]
    assert [r["program_id"] for r in records] == [r["program_id"] for r in fixed]
    assert len({r["program_id"] for r in roster}) == 20
    assert len({r["source_sha256"] for r in roster}) == 20
    assert all(r["proposed_primary_batch"] == adj.TARGET_PRIMARY_BATCH for r in roster)


def test_zero_intersection_with_frozen97(materialized: Path):
    analysis = adj.build_analysis(REPO_ROOT)
    roster_ids = {row["program_id"] for row in _rows(materialized / "adjudication_roster.csv")}
    assert not (roster_ids & analysis["frozen"])
    assert roster_ids <= analysis["remaining_ids"]


def test_each_cell_adjudicated_once_with_required_fields(materialized: Path):
    records = _rows(materialized / "adjudication_records.csv")
    assert len(records) == 20
    for row in records:
        assert row["review_status"] == "ADJUDICATED"
        assert row["primary_layer"] in adj.VALID_PRIMARY
        assert row["outcome_validity"] in adj.VALID_OUTCOME
        assert row["healer_eligibility"] in adj.VALID_HEALER
        assert row["confidence"] in adj.VALID_CONFIDENCE
        assert row["failure_chain"]
        assert row["evidence_citations"]
        assert row["adjudicator_identity"] == adj.ADJUDICATOR_IDENTITY
        assert row["cell_id"]
        assert row["source_sha256"]
        mechs = json.loads(row["mechanism_tags_json"])
        assert mechs
        for item in mechs:
            assert item["status"] in adj.VALID_MECH_STATUS
        if row["primary_layer"] == "UNRESOLVED":
            assert row["healer_eligibility"] == "abstain"
            assert row["unresolved_reason_code"]
            assert row["evidence_missing"]
            assert row["confidence"] == "LOW"
        if row["healer_eligibility"] in {"eligible", "conditional"}:
            assert row["eligibility_rule"]
            assert row["rejection_condition"]


def test_no_evaluator_fail_alone_to_l5_and_no_signal_alone_to_l2(materialized: Path):
    records = _rows(materialized / "adjudication_records.csv")
    summary = json.loads((materialized / "adjudication_summary.json").read_text(encoding="utf-8"))
    # This batch's planning signals are contract-related, but adjudicated L2 must be explicit.
    assert summary["true_adjudicated_L2_count"] == Counter(
        row["primary_layer"] for row in records
    ).get("L2", 0)
    for row in records:
        if row["primary_layer"] == "L5":
            assert "public" in row["evidence_summary"].lower()
            assert "FAIL→L5" not in row["evidence_summary"]


def test_execution_counts_zero(materialized: Path):
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
    assert manifest["frozen_marker_written"] is False
    assert manifest["status"] == adj.STATUS


def test_manifest_closure(materialized: Path):
    manifest = json.loads((materialized / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["adjudication_roster_sha256"] == _digest(
        materialized / "adjudication_roster.csv"
    )
    assert manifest["adjudication_records_sha256"] == _digest(
        materialized / "adjudication_records.csv"
    )
    assert manifest["fixed_next_batch_roster_sha256"] == adj.NEXT_BATCH_ROSTER_SHA256
    assert manifest["remaining101_roster_sha256"] == adj.REMAINING101_ROSTER_SHA256


def test_deterministic_rebuild(materialized: Path):
    rebuilt = adj.build_outputs(REPO_ROOT)
    for name, data in rebuilt.items():
        assert data == (materialized / name).read_bytes()


def test_py_compile():
    compile((REPO_ROOT / adj.ANALYZER).read_text(encoding="utf-8"), str(adj.ANALYZER), "exec")
