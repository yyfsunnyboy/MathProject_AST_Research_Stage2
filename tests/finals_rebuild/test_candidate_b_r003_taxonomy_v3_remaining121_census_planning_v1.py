from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import pytest

from scripts import prepare_candidate_b_r003_taxonomy_v3_remaining121_census_planning_v1 as planner


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / planner.OUTPUT_RELATIVE


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def materialized() -> Path:
    if OUTPUT_DIR.exists():
        return OUTPUT_DIR
    return planner.write_outputs(REPO_ROOT)


@pytest.mark.parametrize("relative,expected", list(planner.SOURCE_HASHES.items()))
def test_frozen_sources_are_hash_pinned(relative: Path, expected: str):
    path = relative if relative.is_absolute() else REPO_ROOT / relative
    assert _digest(path) == expected


def test_processed77_sets_are_disjoint_and_union_is_77():
    analysis = planner.build_analysis(REPO_ROOT)
    g2 = analysis["processed_by_set"]["G2_module"]
    module_exc = analysis["processed_by_set"]["module_exception"]
    multi = analysis["processed_by_set"]["multiple_signal_chain"]
    assert len(g2) == 27
    assert len(module_exc) == 37
    assert len(multi) == 13
    assert not (g2 & module_exc)
    assert not (g2 & multi)
    assert not (module_exc & multi)
    assert len(g2 | module_exc | multi) == 77


def test_remaining121_roster_closure_and_uniqueness(materialized: Path):
    roster = _rows(materialized / "remaining121_roster.csv")
    assert len(roster) == 121
    assert len({row["program_id"] for row in roster}) == 121
    assert [row["roster_rank"] for row in roster] == [str(i) for i in range(1, 122)]
    assert [row["program_id"] for row in roster] == sorted(row["program_id"] for row in roster)
    assert all(row["condition"] == "Candidate_B/H0" for row in roster)


def test_processed77_exclusion_audit_and_zero_intersection(materialized: Path):
    audit = _rows(materialized / "processed77_exclusion_audit.csv")
    roster = _rows(materialized / "remaining121_roster.csv")
    remaining_ids = {row["program_id"] for row in roster}
    audit_ids = {row["program_id"] for row in audit}
    assert len(audit_ids) == 77
    assert not (remaining_ids & audit_ids)
    excluded_from_121 = {row["program_id"] for row in audit if row["excluded_from_remaining121"] == "true"}
    assert len(excluded_from_121) == 50
    g2_only = {row["program_id"] for row in audit if row["processed_set"] == "G2_module"}
    assert len(g2_only) == 27
    assert all(row["in_remaining171"] == "false" for row in audit if row["program_id"] in g2_only)


def test_mutually_exclusive_clusters_sum_to_121(materialized: Path):
    inventory = _rows(materialized / "signal_inventory.csv")
    summary = _rows(materialized / "mutually_exclusive_cluster_summary.csv")
    assert len(inventory) == 121
    assert sum(int(row["cells"]) for row in summary) == 121
    inventory_clusters = Counter(row["work_cluster"] for row in inventory)
    for row in summary:
        assert int(row["cells"]) == inventory_clusters[row["work_cluster"]]
    assert len(inventory_clusters) == sum(1 for row in summary if int(row["cells"]) > 0)


def test_each_cell_has_exactly_one_work_cluster(materialized: Path):
    inventory = _rows(materialized / "signal_inventory.csv")
    for row in inventory:
        assert row["work_cluster"] in planner.WORK_CLUSTER_PRIORITY
        json.loads(row["all_signal_tags"])


def test_next_batch_is_proper_subset_with_zero_processed_intersection(materialized: Path):
    batch = _rows(materialized / "next_batch_roster.csv")
    roster = _rows(materialized / "remaining121_roster.csv")
    audit = _rows(materialized / "processed77_exclusion_audit.csv")
    roster_ids = {row["program_id"] for row in roster}
    batch_ids = {row["program_id"] for row in batch}
    processed_ids = {row["program_id"] for row in audit}
    assert batch_ids <= roster_ids
    assert not (batch_ids & processed_ids)
    assert 10 <= len(batch) <= 25
    assert all(row["work_cluster"] == planner.NEXT_BATCH_TARGET_CLUSTER for row in batch)


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
    assert execution["candidate_executions"] == 0
    assert execution["programs_executed"] == 0
    assert manifest["status"] == planner.STATUS


def test_manifest_and_provenance_closure(materialized: Path):
    manifest = json.loads((materialized / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["outputs_sha256_excluding_manifest"]["remaining121_roster.csv"] == _digest(
        materialized / "remaining121_roster.csv"
    )
    assert manifest["next_batch_roster_sha256"] == _digest(materialized / "next_batch_roster.csv")
    assert manifest["remaining121_roster"] == 121
    assert manifest["processed77_total"] == 77


def test_deterministic_rebuild_bytes_match(materialized: Path):
    rebuilt = planner.build_outputs(REPO_ROOT)
    for relative, data in rebuilt.items():
        assert data == (materialized / relative).read_bytes()


def test_py_compile():
    compile(
        (REPO_ROOT / planner.ANALYZER).read_text(encoding="utf-8"),
        planner.ANALYZER,
        "exec",
    )
