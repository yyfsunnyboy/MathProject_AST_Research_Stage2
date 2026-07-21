from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pytest

from scripts import (
    audit_candidate_b_r003_taxonomy_v3_remaining121_output_contract_shape20_v2_final_freeze_v1 as audit,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / audit.OUTPUT_RELATIVE


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def materialized() -> Path:
    if OUTPUT_DIR.exists():
        return OUTPUT_DIR
    return audit.write_outputs(REPO_ROOT)


@pytest.mark.parametrize("relative,expected", list(audit.SOURCE_HASHES.items()))
def test_frozen_sources_are_hash_pinned(relative: Path, expected: str):
    path = relative if relative.is_absolute() else REPO_ROOT / relative
    assert _digest(path) == expected


def test_v1_and_v2_unmodified(materialized: Path):
    assert _digest(REPO_ROOT / audit.V1_MANIFEST) == audit.V1_FILE_SHA256[audit.V1_MANIFEST]
    assert _digest(REPO_ROOT / audit.V1_CSV) == audit.V1_FILE_SHA256[audit.V1_CSV]
    assert _digest(REPO_ROOT / audit.V2_MANIFEST) == audit.V2_MANIFEST_SHA256
    assert _digest(REPO_ROOT / audit.V2_CSV) == audit.V2_CSV_SHA256
    manifest = json.loads((materialized / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["v1_modified"] is False
    assert manifest["v2_modified"] is False
    assert manifest["freeze_written"] is False


def test_delta_closure_exactly_four(materialized: Path):
    delta = _rows(materialized / "v1_v2_delta_closure_audit.csv")
    assert len(delta) == 4
    assert all(row["approved"] == "true" for row in delta)
    assert all(row["closure_verdict"] == "accept" for row in delta)
    assert {row["program_id"] for row in delta} == set(audit.APPROVED_PIDS)


def test_cell_audits_all_accept(materialized: Path):
    rows = _rows(materialized / "final_freeze_audit.csv")
    assert len(rows) == 20
    assert len({row["program_id"] for row in rows}) == 20
    assert all(row["cell_verdict"] == "accept" for row in rows)


def test_statistics_match_expected(materialized: Path):
    stats = json.loads((materialized / "final_statistics_audit.json").read_text(encoding="utf-8"))
    assert stats["primary_layer_distribution"] == audit.EXPECTED_PRIMARY
    assert stats["healer_eligibility_distribution"] == audit.EXPECTED_HEALER
    assert stats["confidence_distribution"] == audit.EXPECTED_CONFIDENCE
    assert stats["unresolved_cells"] == 12
    assert stats["healer_eligible_or_conditional"] == 0
    assert stats["unapproved_diffs"] == 0
    assert stats["audit_verdict"] == "READY_TO_FREEZE_COMMIT_AND_PUSH_20_CELL_V2"


def test_sha_closure_all_match(materialized: Path):
    rows = _rows(materialized / "roster_and_sha_closure_audit.csv")
    assert rows
    assert all(row["match"] == "true" for row in rows)


def test_execution_counts_zero(materialized: Path):
    execution = json.loads((materialized / "execution_counts.json").read_text(encoding="utf-8"))
    for key in (
        "model_calls",
        "candidate_executions",
        "evalplus_correctness_executions",
        "diagnostics_executions",
        "validation_executions",
        "healer_executions",
        "programs_executed",
    ):
        assert execution[key] == 0


def test_deterministic_rebuild_bytes_match(materialized: Path):
    rebuilt = audit.build_outputs(REPO_ROOT)
    for relative, data in rebuilt.items():
        assert data == (materialized / relative).read_bytes()


def test_py_compile():
    compile(
        (REPO_ROOT / audit.ANALYZER).read_text(encoding="utf-8"),
        audit.ANALYZER,
        "exec",
    )
