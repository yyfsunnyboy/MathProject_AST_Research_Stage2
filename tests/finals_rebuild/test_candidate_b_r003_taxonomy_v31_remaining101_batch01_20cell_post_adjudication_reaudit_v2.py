from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pytest

from scripts import (
    audit_candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_post_adjudication_reaudit_v2 as reaudit,
)
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
OUTPUT_DIR = REPO_ROOT / reaudit.OUTPUT_RELATIVE


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def materialized() -> Path:
    if OUTPUT_DIR.exists() and (OUTPUT_DIR / "manifest.json").is_file():
        return OUTPUT_DIR
    return reaudit.write_outputs(REPO_ROOT)


@pytest.mark.parametrize("relative,expected", list(reaudit.SOURCE_HASHES.items()))
def test_pinned_sources_byte_stable(relative: Path, expected: str):
    path = relative if relative.is_absolute() else REPO_ROOT / relative
    assert _digest(path) == expected


def test_immutable_revisions_unchanged():
    assert _digest(REPO_ROOT / v1.OUTPUT_RELATIVE / "adjudication_records.csv") == reaudit.V1_RECORDS_SHA256
    assert _digest(REPO_ROOT / audit.OUTPUT_RELATIVE / "manifest.json") == reaudit.AUDIT_MANIFEST_SHA256
    assert _digest(REPO_ROOT / v2.OUTPUT_RELATIVE / "adjudication_records.csv") == reaudit.V2_RECORDS_SHA256
    assert (
        _digest(REPO_ROOT / census_prep.OUTPUT_RELATIVE / "next_adjudication_batch_roster.csv")
        == reaudit.NEXT20_SHA256
    )


def test_identity_and_single_semantic_change(materialized: Path):
    cells = _rows(materialized / "per_cell_reaudit_records.csv")
    assert len(cells) == 20
    assert len({row["program_id"] for row in cells}) == 20
    assert len({row["source_sha256"] for row in cells}) == 20
    changed = [row for row in cells if row["semantic_change"] == "true"]
    assert len(changed) == 1
    assert changed[0]["program_id"] == reaudit.TARGET_PROGRAM_ID
    assert all(row["cell_verdict"] == "AFFIRMED" for row in cells)


def test_mbpp103_correction_and_static_chain(materialized: Path):
    cells = {row["program_id"]: row for row in _rows(materialized / "per_cell_reaudit_records.csv")}
    target = cells[reaudit.TARGET_PROGRAM_ID]
    assert target["v1_primary_layer"] == "UNRESOLVED"
    assert target["v2_primary_layer"] == "L5"
    assert target["mbpp103_correction_ok"] == "true"
    assert target["failure_chain_static_ok"] == "true"
    assert target["mechanism_transition_ok"] == "true"
    assert target["healer_ok"] == "true"
    assert target["unresolved_fields_ok"] == "true"
    assert target["correction_materiality"] == "NONE"


def test_mechanism_totals_rebuild(materialized: Path):
    mech = json.loads((materialized / "mechanism_transition_audit.json").read_text(encoding="utf-8"))
    assert mech["totals_rebuild_ok"] is True
    assert mech["v1_global_status"] == {
        "CONFIRMED": 32,
        "REJECTED": 29,
        "SUPPORTED": 15,
        "SUSPECTED": 16,
    }
    assert mech["v2_global_status"] == {
        "CONFIRMED": 33,
        "REJECTED": 33,
        "SUPPORTED": 13,
        "SUSPECTED": 13,
    }
    transitions = {row["tag"]: row["transition"] for row in mech["mbpp103_tag_transitions"]}
    assert transitions["incorrect_formula"] == "SUSPECTED→CONFIRMED"
    assert transitions["algorithm_reconstruction_required"] == "SUSPECTED→CONFIRMED"
    assert transitions["diagnostic_execution_required"] == "CONFIRMED→REJECTED"
    assert transitions["public_examples_non_discriminating"] == "SUPPORTED→REJECTED"


def test_overall_ready_to_freeze(materialized: Path):
    summary = json.loads((materialized / "reaudit_summary.json").read_text(encoding="utf-8"))
    manifest = json.loads((materialized / "manifest.json").read_text(encoding="utf-8"))
    assert summary["overall_verdict"] == "READY_TO_FREEZE_BATCH01_20CELL_V2"
    assert manifest["overall_verdict"] == "READY_TO_FREEZE_BATCH01_20CELL_V2"
    assert summary["ready_to_freeze"] is True
    assert summary["material_finding_count"] == 0
    assert summary["primary_layer_distribution"] == {"L5": 9, "UNRESOLVED": 11}
    assert summary["confidence_distribution"] == {"HIGH": 9, "LOW": 11}
    assert summary["healer_eligibility_distribution"] == {"abstain": 20}
    assert summary["unresolved_gaps"] == 11
    assert summary["mbpp103_in_unresolved_gaps"] is False


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
    assert manifest["provisional_v2_modified"] is False
    assert manifest["frozen_marker_written"] is False


def test_deterministic_rebuild(materialized: Path):
    rebuilt = reaudit.build_outputs(REPO_ROOT)
    for name, data in rebuilt.items():
        assert data == (materialized / name).read_bytes()


def test_py_compile():
    compile((REPO_ROOT / reaudit.ANALYZER).read_text(encoding="utf-8"), str(reaudit.ANALYZER), "exec")
