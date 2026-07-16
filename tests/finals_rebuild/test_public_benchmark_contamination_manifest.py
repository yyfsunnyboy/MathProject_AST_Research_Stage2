from __future__ import annotations

import csv
import io
import json
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from agent_tools.finals_rebuild import ollama_generation_runner as smoke_runner
from scripts import build_public_benchmark_contamination_manifest as builder


def _build() -> builder.GovernanceBuild:
    return builder.build_governance(REPO_ROOT)


def _row_map(build: builder.GovernanceBuild) -> dict[str, dict[str, str]]:
    return {row["task_id"]: row for row in build.rows}


def test_humaneval_counts_and_official_order_smoke_selection():
    build = _build()
    records = [
        json.loads(line)
        for line in (REPO_ROOT / builder.HUMANEVAL_TASKS).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    expected_smoke = smoke_runner.select_tasks_official_first_n(
        records, smoke_runner.SMOKE_TASK_COUNT
    )

    assert len(build.humaneval_task_ids) == 164
    assert len(build.smoke_task_ids) == 20
    assert list(build.smoke_task_ids) == [row["task_id"] for row in expected_smoke]
    assert len(build.humaneval_forensic_ids) == 38


def test_humaneval_overlap_excluded_union_and_unreviewed_counts():
    build = _build()
    smoke = set(build.smoke_task_ids)
    forensic = set(build.humaneval_forensic_ids)

    assert smoke & forensic == {"HumanEval/10", "HumanEval/19"}
    assert len(smoke | forensic) == 56
    assert len(build.humaneval_task_ids) - len(smoke | forensic) == 108


def test_mbpp_reviewed_count_and_total_unavailable():
    build = _build()
    assert len(build.mbpp_forensic_ids) == 116
    assert build.mbpp_total is None
    assert sum(row["dataset"] == "MBPP+" for row in build.rows) == 116


def test_eligibility_and_unreviewed_statuses():
    build = _build()
    rows = _row_map(build)

    excluded_ids = set(build.smoke_task_ids) | set(build.humaneval_forensic_ids)
    excluded_ids |= set(build.mbpp_forensic_ids)
    assert all(rows[task_id]["confirmatory_eligible"] == "false" for task_id in excluded_ids)

    unreviewed = [
        row for row in build.rows if row["contamination_status"] == "unreviewed_candidate"
    ]
    assert len(unreviewed) == 108
    assert all(row["confirmatory_eligible"] == "pending" for row in unreviewed)
    assert all(row["confirmatory_eligible"] != "true" for row in build.rows)


def test_multiple_sources_are_preserved_in_fixed_order():
    rows = _row_map(_build())
    assert rows["HumanEval/10"]["contamination_sources"] == (
        "engineering_smoke;individual_review;failure_census"
    )
    assert rows["Mbpp/255"]["contamination_sources"] == (
        "individual_review;failure_census;rule_development"
    )
    assert rows["Mbpp/255"]["rule_development_source"] == "true"


def test_status_classifier_supports_pending_and_ambiguous_evidence():
    assert builder.classify_contamination_status(generated_only=True) == (
        "pending_generated_or_aggregate_only"
    )
    assert builder.classify_contamination_status(aggregate_evaluated=True) == (
        "pending_generated_or_aggregate_only"
    )
    assert builder.classify_contamination_status(evidence_ambiguous=True) == (
        "evidence_ambiguous"
    )
    assert builder.classify_contamination_status(
        failure_census_source=True, rule_development_source=True
    ) == "excluded_rule_development"


def test_csv_fields_and_numeric_sort_are_deterministic():
    build = _build()
    csv_bytes = builder.render_manifest_csv(build)
    parsed = list(csv.DictReader(io.StringIO(csv_bytes.decode("utf-8"))))

    assert tuple(parsed[0]) == builder.CSV_FIELDS
    assert csv_bytes == builder.render_manifest_csv(build)
    observed = [(row["dataset"], int(row["task_numeric_id"])) for row in parsed]
    assert observed == sorted(observed)


def test_script_run_twice_produces_identical_csv_bytes(tmp_path):
    first_csv = tmp_path / "first.csv"
    second_csv = tmp_path / "second.csv"
    first_summary = tmp_path / "first.md"
    second_summary = tmp_path / "second.md"
    common = [
        "--repo-root",
        str(REPO_ROOT),
        "--starting-commit",
        "14299c855286f6fcd39d3c662f524e0caa28acc3",
        "--generated-date",
        "2026-07-16",
    ]

    assert builder.main(common + ["--manifest-out", str(first_csv), "--summary-out", str(first_summary)]) == 0
    assert builder.main(common + ["--manifest-out", str(second_csv), "--summary-out", str(second_summary)]) == 0
    assert first_csv.read_bytes() == second_csv.read_bytes()


def test_summary_uses_pending_language_and_does_not_guess_mbpp_total():
    build = _build()
    summary = builder.render_summary(
        build,
        repo_root=REPO_ROOT,
        starting_commit="14299c855286f6fcd39d3c662f524e0caa28acc3",
        generated_date="2026-07-16",
    )

    assert "The 108 remaining HumanEval+ tasks are `unreviewed_candidate`" in summary
    assert "they are not a formal confirmatory set" in summary
    assert "| Total tasks | unavailable |" in summary
    assert "does not establish a formal development, validation, or confirmatory split" in summary
    assert "No row in this manifest has `confirmatory_eligible=true`" in summary
