from __future__ import annotations

import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path

import pytest

from scripts import build_mbpp_scaffold_v0_paired_analysis as paired


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / paired.OUTPUT_RELATIVE


def test_exact_mcnemar_and_effect_size_helpers():
    observed = paired.paired_statistics(
        Counter({"fail_to_fail": 70, "fail_to_pass": 30})
    )
    pipeline = paired.paired_statistics(
        Counter(
            {
                "fail_to_fail": 53,
                "fail_to_pass": 17,
                "pass_to_fail": 17,
                "pass_to_pass": 13,
            }
        )
    )

    assert observed["exact_mcnemar_two_sided_p"] == pytest.approx(2 / 2**30)
    assert observed["paired_risk_difference"] == pytest.approx(0.30)
    assert observed["matched_pairs_odds_ratio"] == "infinity"
    assert observed["discordant_superiority_exact_95ci"][0] == pytest.approx(
        0.8842966915
    )
    assert pipeline["exact_mcnemar_two_sided_p"] == 1.0
    assert pipeline["paired_risk_difference"] == 0.0
    assert pipeline["matched_pairs_odds_ratio"] == 1.0
    assert pipeline["discordant_superiority_exact_95ci"] == pytest.approx(
        [0.324269, 0.675731], abs=1e-6
    )


def test_build_has_100_unique_complete_pairs_and_exact_transitions():
    result = paired.build_analysis(REPO_ROOT)
    rows = result["paired_rows"]

    assert len(rows) == 100
    assert len({(row["task_id"], row["seed"]) for row in rows}) == 100
    assert result["transition_counts"]["observed"] == {
        "fail_to_fail": 70,
        "fail_to_pass": 30,
        "pass_to_fail": 0,
        "pass_to_pass": 0,
    }
    assert result["transition_counts"]["pipeline"] == {
        "fail_to_fail": 53,
        "fail_to_pass": 17,
        "pass_to_fail": 17,
        "pass_to_pass": 13,
    }
    assert sum(row["observed_scaffold_rescue"] == "true" for row in rows) == 30
    assert sum(row["observed_scaffold_regression"] == "true" for row in rows) == 0
    assert sum(row["pipeline_scaffold_rescue"] == "true" for row in rows) == 17
    assert sum(row["pipeline_scaffold_regression"] == "true" for row in rows) == 17


def test_format_diagnostics_are_evidence_based_and_accounts_remain_separate():
    result = paired.build_analysis(REPO_ROOT)
    p0 = result["format_summary"]["p0"]
    p1 = result["format_summary"]["p1"]

    assert p0["strict_python_only_compliant"] == 0
    assert p1["strict_python_only_compliant"] == 91
    assert (p0["code_fence"], p1["code_fence"]) == (96, 0)
    assert (p0["extra_text_outside_fences"], p1["extra_text_outside_fences"]) == (
        79,
        0,
    )
    assert (p0["multiple_program_segments"], p1["multiple_program_segments"]) == (
        25,
        0,
    )
    assert (p0["raw_compile_pass"], p1["raw_compile_pass"]) == (0, 94)
    assert p0["pipeline_compile_status"] == {
        "fail": 6,
        "not_run_extraction_failed": 21,
        "pass": 73,
    }
    assert p1["pipeline_compile_status"] == {"fail": 6, "pass": 94}
    assert (p0["reasoning_leakage"], p1["reasoning_leakage"]) == (0, 1)
    assert p1["extraction_actions"] == {"pass_through:plain_text": 100}
    assert result["statistics"]["observed"]["net_change_cells"] == 30
    assert result["statistics"]["pipeline"]["net_change_cells"] == 0


def test_p1_failure_census_reuses_p0_taxonomy_without_guessing_unknowns():
    result = paired.build_analysis(REPO_ROOT)
    rows = result["p1_census_rows"]
    categories = Counter(row["failure_category"] for row in rows)

    assert len(rows) == 70
    assert categories == {
        "unknown": 61,
        "syntax_failure": 6,
        "missing_or_wrong_entry_point": 3,
    }
    unknowns = [row for row in rows if row["failure_category"] == "unknown"]
    assert len(unknowns) == 61
    assert all(row["review_status"] == "manual_review_required" for row in unknowns)
    assert all(row["exception_type_or_evaluator_outcome"] == "evalplus_failure_unspecified" for row in unknowns)
    assert not any(row["failure_category"] == "functional_test_failure" for row in rows)


def test_pipeline_success_sets_are_not_mistaken_for_the_same_cells():
    rows = paired.build_analysis(REPO_ROOT)["paired_rows"]
    p0_pass = {
        (row["task_id"], row["seed"])
        for row in rows
        if row["p0_pipeline_status"] == "pass"
    }
    p1_pass = {
        (row["task_id"], row["seed"])
        for row in rows
        if row["p1_pipeline_status"] == "pass"
    }

    assert len(p0_pass) == len(p1_pass) == 30
    assert len(p0_pass & p1_pass) == 13
    assert p0_pass != p1_pass


def test_outputs_are_byte_deterministic_and_match_manifest():
    first = paired.build_outputs(REPO_ROOT)
    second = paired.build_outputs(REPO_ROOT)

    assert first == second
    for relative, expected in first.items():
        assert (OUTPUT_DIR / relative).read_bytes() == expected
    manifest = json.loads(first[Path("paired_analysis_manifest.json")])
    assert manifest["paired_cells"] == 100
    assert manifest["duplicate_pairs"] == manifest["missing_pairs"] == 0
    assert manifest["exploratory_development_analysis"] is True
    assert manifest["external_generalization_claimed"] is False
    assert manifest["pipeline_correction_is_healer"] is False
    assert manifest["model_calls"] == manifest["evalplus_executions"] == 0
    for name, metadata in manifest["outputs"].items():
        content = first[Path(name)]
        assert hashlib.sha256(content).hexdigest() == metadata["sha256"]
        assert len(content) == metadata["size_bytes"]


def test_committed_csv_schemas_and_reports_state_governance_conclusion():
    paired_rows = list(
        csv.DictReader(
            io.StringIO((OUTPUT_DIR / "paired_cell_comparison.csv").read_text(encoding="utf-8"))
        )
    )
    census_rows = list(
        csv.DictReader(
            io.StringIO((OUTPUT_DIR / "p1_failure_census.csv").read_text(encoding="utf-8"))
        )
    )
    report = (OUTPUT_DIR / "scaffold_v0_development_analysis_zh.md").read_text(
        encoding="utf-8"
    )

    assert len(paired_rows) == 100
    assert tuple(paired_rows[0]) == paired.PAIRED_FIELDS
    assert len(census_rows) == 70
    assert tuple(census_rows[0]) == paired.CENSUS_FIELDS
    assert "提升直接可評估性" in report
    assert "沒有提升Pipeline-corrected correctness" in report
    assert "17個paired regressions" in report
    assert "development exploratory analysis" in report
    assert "只能另提Scaffold v1候選" in report
    assert "Pipeline correction不是Healer" in report
