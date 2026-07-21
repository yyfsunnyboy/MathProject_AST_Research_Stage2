from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import pytest

from scripts import prepare_candidate_b_r003_taxonomy_v31_remaining101_zero_execution_census_v1 as planner


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / planner.OUTPUT_RELATIVE


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def materialized() -> Path:
    if OUTPUT_DIR.exists() and (OUTPUT_DIR / "manifest.json").is_file():
        return OUTPUT_DIR
    return planner.write_outputs(REPO_ROOT)


@pytest.mark.parametrize("relative,expected", list(planner.SOURCE_HASHES.items()))
def test_frozen_sources_are_hash_pinned(relative: Path, expected: str):
    path = relative if relative.is_absolute() else REPO_ROOT / relative
    assert _digest(path) == expected


def test_frozen97_sets_are_disjoint_and_union_is_97():
    analysis = planner.build_analysis(REPO_ROOT)
    frozen = analysis["frozen_by_set"]
    assert len(frozen["G2_module"]) == 27
    assert len(frozen["module_exception"]) == 37
    assert len(frozen["multiple_signal_chain"]) == 13
    assert len(frozen["output_contract_shape20"]) == 20
    assert len(analysis["frozen_ids"]) == 97


def test_remaining101_roster_closure_and_uniqueness(materialized: Path):
    roster = _rows(materialized / "remaining101_roster.csv")
    assert len(roster) == 101
    assert len({row["program_id"] for row in roster}) == 101
    assert len({row["cell_id"] for row in roster}) == 101
    assert [row["roster_rank"] for row in roster] == [str(i) for i in range(1, 102)]
    assert [row["program_id"] for row in roster] == sorted(row["program_id"] for row in roster)
    assert all(row["condition"] == "Candidate_B/H0" for row in roster)
    assert all(row["processed_frozen_status"] == "remaining_not_frozen" for row in roster)
    assert all(row["source_sha256"] == row["evaluation_source_sha256"] for row in roster)


def test_remaining101_zero_intersection_with_frozen97(materialized: Path):
    analysis = planner.build_analysis(REPO_ROOT)
    roster_ids = {row["program_id"] for row in _rows(materialized / "remaining101_roster.csv")}
    assert roster_ids == analysis["remaining_ids"]
    assert not (roster_ids & analysis["frozen_ids"])
    assert len(roster_ids) + len(analysis["frozen_ids"]) == 198


def test_proposed_batches_are_exclusive_and_sum_to_101(materialized: Path):
    inventory = _rows(materialized / "static_signal_inventory.csv")
    partition = _rows(materialized / "proposed_batch_partition.csv")
    assert len(inventory) == 101
    assert sum(int(row["cells"]) for row in partition) == 101
    inventory_batches = Counter(row["proposed_primary_batch"] for row in inventory)
    for row in partition:
        assert int(row["cells"]) == inventory_batches[row["proposed_primary_batch"]]
        assert row["planning_annotation"] == planner.PLANNING_ONLY_MARK
    assert set(inventory_batches) <= set(planner.PROPOSED_BATCH_PRIORITY)


def test_formal_adjudication_fields_are_blank(materialized: Path):
    inventory = _rows(materialized / "static_signal_inventory.csv")
    for row in inventory:
        for field in planner.FORBIDDEN_FORMAL_FIELDS:
            assert row[field] == ""
        assert row["planning_annotation"] == planner.PLANNING_ONLY_MARK
        json.loads(row["observed_signals_json"])
        json.loads(row["candidate_mechanisms_json"])


def test_next_batch_is_coherent_subset(materialized: Path):
    batch = _rows(materialized / "next_adjudication_batch_roster.csv")
    roster = _rows(materialized / "remaining101_roster.csv")
    roster_ids = {row["program_id"] for row in roster}
    batch_ids = {row["program_id"] for row in batch}
    assert batch_ids <= roster_ids
    assert 15 <= len(batch) <= 25
    assert all(
        row["proposed_primary_batch"] == planner.NEXT_BATCH_TARGET_PRIMARY_BATCH for row in batch
    )
    assert all(row["planning_annotation"] == planner.PLANNING_ONLY_MARK for row in batch)


def test_execution_counts_are_zero(materialized: Path):
    execution = json.loads((materialized / "execution_counts.json").read_text(encoding="utf-8"))
    manifest = json.loads((materialized / "manifest.json").read_text(encoding="utf-8"))
    provenance = json.loads((materialized / "provenance.json").read_text(encoding="utf-8"))
    for doc in (execution, manifest, provenance):
        assert doc["model_calls"] == 0
        assert doc["evalplus_correctness_executions"] == 0
        assert doc["diagnostics_executions"] == 0
        assert doc["healer_executions"] == 0
        assert doc["validation_executions"] == 0
        assert doc["candidate_executions"] == 0
        assert doc["programs_executed"] == 0
    assert manifest["status"] == planner.STATUS
    assert provenance["taxonomy_v31_planning_reference"]["sha256"] == planner.V31_REFERENCE_SHA256
    assert provenance["taxonomy_v31_planning_reference"]["status"] == planner.V31_REFERENCE_STATUS


def test_manifest_and_provenance_closure(materialized: Path):
    manifest = json.loads((materialized / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["outputs_sha256_excluding_manifest"]["remaining101_roster.csv"] == _digest(
        materialized / "remaining101_roster.csv"
    )
    assert manifest["remaining101_roster_sha256"] == _digest(
        materialized / "remaining101_roster.csv"
    )
    assert manifest["next_adjudication_batch_roster_sha256"] == _digest(
        materialized / "next_adjudication_batch_roster.csv"
    )
    assert manifest["remaining_total"] == 101
    assert manifest["frozen_total"] == 97
    assert manifest["freeze20_manifest_sha256"] == planner.FREEZE20_MANIFEST_SHA256
    assert manifest["progress_census_manifest_sha256"] == planner.PROGRESS_CENSUS_MANIFEST_SHA256


def test_deterministic_rebuild_bytes_match(materialized: Path):
    rebuilt = planner.build_outputs(REPO_ROOT)
    for relative, data in rebuilt.items():
        assert data == (materialized / relative).read_bytes()


def test_py_compile():
    compile(
        (REPO_ROOT / planner.ANALYZER).read_text(encoding="utf-8"),
        str(planner.ANALYZER),
        "exec",
    )
