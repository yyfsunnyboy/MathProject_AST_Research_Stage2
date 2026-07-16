from __future__ import annotations

import csv
import hashlib
import io
import pathlib
import sys
from collections import Counter

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts import freeze_public_benchmark_split as freezer


def _build() -> freezer.FrozenSplitBuild:
    return freezer.build_frozen_split(REPO_ROOT)


def _proposal_rows() -> dict[tuple[str, str], dict[str, str]]:
    path = REPO_ROOT / freezer.SPLIT_PROPOSAL
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return {
            (row["dataset"], row["task_id"]): row for row in csv.DictReader(handle)
        }


def test_frozen_counts_and_unique_assignments():
    rows = _build().rows
    eligible = [row for row in rows if row["confirmatory_eligible"] == "true"]

    assert len(rows) == 542
    assert len({(row["dataset"], row["task_id"]) for row in rows}) == 542
    assert all(row["split_assignment_status"] == "frozen" for row in rows)
    assert len(eligible) == 168
    assert Counter(row["dataset"] for row in eligible) == {
        "HumanEval+": 108,
        "MBPP+": 60,
    }
    assert sum(row["confirmatory_eligible"] == "false" for row in rows) == 374


def test_only_confirmatory_candidate_roles_are_eligible():
    rows = _build().rows
    for row in rows:
        expected = row["proposed_role"] in freezer.CONFIRMATORY_ROLES
        assert (row["confirmatory_eligible"] == "true") == expected
        if expected:
            assert row["project_contamination_status"] == "attested_no_project_exposure"
            assert row["source_contamination_status"] == "pending"


def test_selection_hash_role_and_rank_match_proposal_exactly():
    proposal = _proposal_rows()
    for row in _build().rows:
        source = proposal[(row["dataset"], row["task_id"])]
        assert row["selection_hash"] == source["selection_hash"]
        assert row["selection_rank_within_pool"] == source["selection_rank_within_pool"]
        assert row["proposed_role"] == source["proposed_role"]
        assert row["active_development_generation_subset"] == source[
            "active_development_generation_subset"
        ]


def test_csv_schema_excludes_sensitive_fields():
    rows = list(
        csv.DictReader(io.StringIO(freezer.render_frozen_csv(_build()).decode("utf-8")))
    )
    assert tuple(rows[0]) == freezer.CSV_FIELDS
    assert not (
        {"prompt", "answer", "tests", "output", "canonical_solution"} & set(rows[0])
    )


def test_researcher_attestation_contains_exact_statement_and_limits():
    text = (REPO_ROOT / freezer.ATTESTATION).read_text(encoding="utf-8")
    assert freezer.ATTESTATION_TEXT in text
    assert "attestation_date: `2026-07-16`" in text
    assert "scope: `project-process contamination`" in text
    assert "model pretraining" in text
    assert "must not be overwritten" in text


def test_freeze_is_byte_deterministic_and_does_not_change_sources(tmp_path):
    source_paths = [
        REPO_ROOT / freezer.CONTAMINATION_MANIFEST,
        REPO_ROOT / freezer.SPLIT_PROPOSAL,
    ]
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in source_paths}
    first_csv = tmp_path / "first.csv"
    second_csv = tmp_path / "second.csv"
    first_summary = tmp_path / "first.md"
    second_summary = tmp_path / "second.md"
    common = [
        "--repo-root",
        str(REPO_ROOT),
        "--starting-commit",
        "23a430538f44fbe8e57a025a19ca0f49778e1ab1",
        "--generated-date",
        "2026-07-16",
    ]

    assert freezer.main(common + ["--csv-out", str(first_csv), "--summary-out", str(first_summary)]) == 0
    assert freezer.main(common + ["--csv-out", str(second_csv), "--summary-out", str(second_summary)]) == 0
    assert first_csv.read_bytes() == second_csv.read_bytes()
    after = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in source_paths}
    assert before == after
