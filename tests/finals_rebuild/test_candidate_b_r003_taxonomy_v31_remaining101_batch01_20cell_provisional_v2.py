from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pytest

from scripts import (
    adjudicate_candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_provisional_v1 as v1,
)
from scripts import (
    adjudicate_candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_provisional_v2 as v2,
)
from scripts import (
    audit_candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_post_adjudication_v1 as audit,
)
from scripts import (
    prepare_candidate_b_r003_taxonomy_v31_remaining101_zero_execution_census_v1 as census_prep,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / v2.OUTPUT_RELATIVE
V1_DIR = REPO_ROOT / v1.OUTPUT_RELATIVE
AUDIT_DIR = REPO_ROOT / audit.OUTPUT_RELATIVE
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
    return v2.write_outputs(REPO_ROOT)


@pytest.mark.parametrize("relative,expected", list(v2.SOURCE_HASHES.items()))
def test_pinned_sources_unchanged(relative: Path, expected: str):
    path = relative if relative.is_absolute() else REPO_ROOT / relative
    assert _digest(path) == expected


def test_immutable_inputs_byte_stable():
    assert _digest(V1_DIR / "adjudication_records.csv") == v2.V1_RECORDS_SHA256
    assert _digest(V1_DIR / "adjudication_roster.csv") == v2.V1_ROSTER_SHA256
    assert _digest(AUDIT_DIR / "manifest.json") == v2.AUDIT_MANIFEST_SHA256
    assert _digest(CENSUS_DIR / "next_adjudication_batch_roster.csv") == v2.NEXT20_SHA256
    assert _digest(CENSUS_DIR / "remaining101_roster.csv") == v2.REMAINING101_SHA256


def test_roster_matches_next20_and_v1(materialized: Path):
    roster = _rows(materialized / "adjudication_roster.csv")
    next20 = _rows(CENSUS_DIR / "next_adjudication_batch_roster.csv")
    v1_roster = _rows(V1_DIR / "adjudication_roster.csv")
    assert [row["program_id"] for row in roster] == [row["program_id"] for row in next20]
    assert [row["program_id"] for row in roster] == [row["program_id"] for row in v1_roster]
    assert len({row["source_sha256"] for row in roster}) == 20


def test_only_mbpp103_semantic_changes(materialized: Path):
    v1_rows = _rows(V1_DIR / "adjudication_records.csv")
    v2_rows = _rows(materialized / "adjudication_records.csv")
    changed = []
    for left, right in zip(v1_rows, v2_rows, strict=True):
        diffs = [
            field
            for field in v2.SEMANTIC_FIELDS
            if left.get(field, "") != right.get(field, "")
        ]
        if diffs:
            changed.append((left["program_id"], diffs))
    assert len(changed) == 1
    assert changed[0][0] == v2.TARGET_PROGRAM_ID
    assert set(changed[0][1]) <= v2.ALLOWED_CHANGE_FIELDS


def test_mbpp103_corrected(materialized: Path):
    rows = {row["program_id"]: row for row in _rows(materialized / "adjudication_records.csv")}
    target = rows[v2.TARGET_PROGRAM_ID]
    assert target["task_id"] == "Mbpp/103"
    assert target["source_sha256"] == v2.TARGET_SOURCE_SHA256
    assert target["primary_layer"] == "L5"
    assert target["confidence"] == "HIGH"
    assert target["healer_eligibility"] == "abstain"
    assert target["unresolved_reason_code"] == ""
    assert target["evidence_missing"] == ""
    assert target["minimal_future_diagnostic"] == ""
    assert "STATIC" in target["failure_chain"]
    mechs = {item["tag"]: item["status"] for item in json.loads(target["mechanism_tags_json"])}
    assert mechs["incorrect_formula"] == "CONFIRMED"
    assert mechs["algorithm_reconstruction_required"] == "CONFIRMED"
    assert mechs["diagnostic_execution_required"] == "REJECTED"
    assert mechs["public_examples_non_discriminating"] == "REJECTED"


def test_statistics(materialized: Path):
    summary = json.loads((materialized / "adjudication_summary.json").read_text(encoding="utf-8"))
    assert summary["primary_layer_distribution"] == {"L5": 9, "UNRESOLVED": 11}
    assert summary["confidence_distribution"] == {"HIGH": 9, "LOW": 11}
    assert summary["healer_eligibility_distribution"] == {"abstain": 20}
    assert summary["outcome_validity_distribution"] == {"VALID_MODEL_OUTCOME": 20}
    assert summary["true_adjudicated_L2_count"] == 0
    gaps = _rows(materialized / "unresolved_evidence_gaps.csv")
    assert len(gaps) == 11
    assert v2.TARGET_PROGRAM_ID not in {row["program_id"] for row in gaps}
    assert all(row["unresolved_reason_code"] for row in gaps)


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
    assert manifest["provisional_v1_modified"] is False
    assert manifest["audit_v1_modified"] is False
    assert manifest["frozen_marker_written"] is False


def test_deterministic_rebuild(materialized: Path):
    rebuilt = v2.build_outputs(REPO_ROOT)
    for name, data in rebuilt.items():
        assert data == (materialized / name).read_bytes()


def test_py_compile():
    compile((REPO_ROOT / v2.ANALYZER).read_text(encoding="utf-8"), str(v2.ANALYZER), "exec")
