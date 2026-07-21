from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pytest

from scripts import prepare_candidate_b_r003_taxonomy_v3_remaining171_machine_census_v1 as analyzer


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / analyzer.OUTPUT_RELATIVE


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def materialized(tmp_path_factory) -> Path:
    if OUTPUT_DIR.exists():
        return OUTPUT_DIR
    # Materialize into repo output path once for structural tests.
    return analyzer.write_outputs(REPO_ROOT)


@pytest.mark.parametrize("relative,expected", list(analyzer.SOURCE_HASHES.items()))
def test_frozen_sources_are_hash_pinned(relative: Path, expected: str):
    path = relative if relative.is_absolute() else REPO_ROOT / relative
    assert _digest(path) == expected


def test_population_reconciliation_is_closed(materialized: Path):
    roster = _rows(materialized / "fixed_roster.csv")
    excluded = _rows(materialized / "excluded_g2_27_identity_ledger.csv")
    reconcile = {
        row["metric"]: row["value"] for row in _rows(materialized / "population_reconciliation.csv")
    }
    assert len(roster) == 171
    assert len(excluded) == 27
    assert reconcile["formal_unresolved_population"] == "198"
    assert reconcile["excluded_g2_module"] == "27"
    assert reconcile["remaining_fixed_roster"] == "171"
    assert reconcile["reconciliation_identity"] == "198=27+171"
    roster_ids = {row["program_id"] for row in roster}
    excluded_ids = {row["program_id"] for row in excluded}
    assert not (roster_ids & excluded_ids)
    assert len(roster_ids | excluded_ids) == 198


def test_roster_is_unique_sorted_and_candidate_b_only(materialized: Path):
    roster = _rows(materialized / "fixed_roster.csv")
    assert [row["roster_rank"] for row in roster] == [str(i) for i in range(1, 172)]
    assert [row["program_id"] for row in roster] == sorted(row["program_id"] for row in roster)
    assert len({row["program_id"] for row in roster}) == 171
    assert len({row["cell_identity_sha256"] for row in roster}) == 171
    assert all(row["condition_account"] == "Candidate_B/H0" for row in roster)
    assert all(row["exclusion_from_g2_27"] == "true" for row in roster)
    assert all(row["original_diagnostic_phase"] != "G2_module" for row in roster)


def test_census_does_not_emit_taxonomy_or_healer_decisions(materialized: Path):
    census = _rows(materialized / "machine_census.csv")
    assert len(census) == 171
    assert all(row["primary_failure_layer"] == "" for row in census)
    assert all(row["secondary_failure_layers"] == "" for row in census)
    assert all(row["healer_eligibility"] == "" for row in census)
    assert all(row["cluster_is_not_taxonomy_layer"] == "true" for row in census)
    assert all(row["hidden_expected_actual_used"] == "false" for row in census)
    assert all(row["h1_result_used_for_sampling"] == "false" for row in census)
    assert all(row["operational_cluster"] in analyzer.CLUSTER_ORDER for row in census)


def test_manifest_and_execution_counts_are_zero(materialized: Path):
    manifest = json.loads((materialized / "manifest.json").read_text(encoding="utf-8"))
    provenance = json.loads((materialized / "provenance.json").read_text(encoding="utf-8"))
    execution = json.loads((materialized / "execution_manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == analyzer.STATUS
    assert provenance["status"] == analyzer.STATUS
    assert execution["status"] == analyzer.STATUS
    for doc in (manifest, provenance, execution):
        assert doc["model_calls"] == 0
        assert doc["evalplus_correctness_executions"] == 0
        assert doc["diagnostics_executions"] == 0
        assert doc["healer_executions"] == 0
        assert doc["validation_executions"] == 0
    assert "MACHINE_CENSUS_NOT_TAXONOMY_ADJUDICATION" in (
        materialized / "methodology_report_zh.md"
    ).read_text(encoding="utf-8")
    assert manifest["outputs_sha256_excluding_manifest"]["fixed_roster.csv"] == _digest(
        materialized / "fixed_roster.csv"
    )


def test_deterministic_rebuild_bytes_match(materialized: Path):
    rebuilt = analyzer.build_outputs(REPO_ROOT)
    for relative, data in rebuilt.items():
        assert data == (materialized / relative).read_bytes()


def test_unresolved_issues_file_is_header_only(materialized: Path):
    assert _rows(materialized / "unresolved_source_or_identity_issues.csv") == []
