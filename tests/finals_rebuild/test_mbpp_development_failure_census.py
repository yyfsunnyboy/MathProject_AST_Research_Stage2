from __future__ import annotations

import csv
import io
import json
from pathlib import Path

import pytest

from scripts import build_mbpp_development_failure_census as census


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_census_reconciles_run_003_and_has_required_scope():
    rows, manifest = census.build_census(REPO_ROOT)

    assert len(rows) == 70
    assert len({row["task_id"] for row in rows}) == 19
    assert len({row["cell_id"] for row in rows}) == 70
    assert manifest["generation_cells"] == 100
    assert manifest["evaluated_account_rows"] == 200
    assert manifest["observed_pass"] == 0
    assert manifest["observed_fail"] == 100
    assert manifest["pipeline_pass"] == 30
    assert manifest["pipeline_fail"] == 70
    assert manifest["expansion_triggered"] is False
    assert manifest["generation_journal"]["file_count"] == 100


def test_census_schema_hashes_and_conservative_classification():
    rows, manifest = census.build_census(REPO_ROOT)

    assert tuple(rows[0]) == census.CSV_FIELDS
    assert sum(manifest["category_counts"].values()) == 70
    assert set(manifest["category_counts"]) == set(census.CATEGORIES)
    assert all(len(row["raw_generation_sha256"]) == 64 for row in rows)
    assert all(
        not row["extracted_program_sha256"] or len(row["extracted_program_sha256"]) == 64
        for row in rows
    )
    assert all(
        row["failure_category"] != "functional_test_failure"
        or row["healer_candidate"] == "false"
        for row in rows
    )
    assert all(
        row["failure_category"] != "unknown"
        or row["review_status"] == "manual_review_required"
        for row in rows
    )


def test_rendering_is_byte_deterministic(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"

    census.write_outputs(REPO_ROOT, first)
    census.write_outputs(REPO_ROOT, second)

    for name in (
        "failure_census.csv",
        "failure_census_manifest.json",
        "failure_census_summary.md",
    ):
        assert (first / name).read_bytes() == (second / name).read_bytes()


def test_integrity_failure_occurs_before_output_write(tmp_path, monkeypatch):
    monkeypatch.setitem(census.EXPECTED_SOURCE_HASHES, "generation_plan.json", "0" * 64)
    output = tmp_path / "must-not-exist"

    with pytest.raises(census.CensusIntegrityError, match="source artifact hash mismatch"):
        census.write_outputs(REPO_ROOT, output)

    assert not output.exists()


def test_committed_csv_matches_builder_bytes():
    rows, _ = census.build_census(REPO_ROOT)
    committed = REPO_ROOT / census.OUTPUT_RELATIVE / "failure_census.csv"

    assert committed.read_bytes() == census.render_csv(rows)
    parsed = list(csv.DictReader(io.StringIO(committed.read_text(encoding="utf-8"))))
    assert len(parsed) == 70


def test_manifest_and_summary_explain_two_evaluation_accounts():
    output = REPO_ROOT / census.OUTPUT_RELATIVE
    manifest = json.loads((output / "failure_census_manifest.json").read_text(encoding="utf-8"))
    summary = (output / "failure_census_summary.md").read_text(encoding="utf-8")

    assert manifest["evaluation_accounts"] == ["observed", "pipeline_corrected"]
    assert manifest["pipeline_rescues_excluded_from_healer_effect"] == 30
    assert "does not mean 200 generations" in summary
    assert "Pipeline correction and Healer accounting remain completely separate" in summary
