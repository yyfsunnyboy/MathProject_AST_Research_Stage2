from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path

import pytest

from scripts import analyze_candidate_b_r003_formal_paired as analysis


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / analysis.OUTPUT_RELATIVE


def test_formal_analysis_has_complete_unique_programs_accounts_and_cells():
    result = analysis.build_analysis(REPO_ROOT)
    assert len(result["cells"]) == 600
    assert len({row["program_id"] for row in result["cells"]}) == 600
    assert len(result["accounts"]) == 1200
    assert len({row["evaluation_account_id"] for row in result["accounts"]}) == 1200
    assert {row["prompt_condition"] for row in result["cells"]} == {"P0", "Candidate_B"}
    assert all(sum(row["prompt_condition"] == condition for row in result["cells"]) == 300 for condition in ("P0", "Candidate_B"))
    assert len(result["task_rows"]) == 60
    assert all(row["seeds"] == "5" for row in result["task_rows"])


def test_four_arms_transitions_and_frozen_gate_are_exact():
    result = analysis.build_analysis(REPO_ROOT)
    prompt = {row["prompt_condition"]: row for row in result["prompt_summaries"]}
    healer = {row["prompt_condition"]: row for row in result["healer_summaries"]}
    assert (prompt["P0"]["h0_pass"], prompt["P0"]["h1_pass"]) == ("68", "77")
    assert (prompt["Candidate_B"]["h0_pass"], prompt["Candidate_B"]["h1_pass"]) == ("76", "76")
    assert (healer["P0"]["fail_to_pass_rescue"], healer["P0"]["pass_to_fail_regression"]) == ("9", "0")
    assert (healer["Candidate_B"]["fail_to_pass_rescue"], healer["Candidate_B"]["pass_to_fail_regression"]) == ("0", "0")
    assert result["scaffold"]["absolute_pass_difference"] == 8
    assert result["gates"]["all_qualification_gates_passed"] is False
    assert result["gates"]["failed_gates"] == ["candidate_b_h0_to_h1_paired_net_change_gt_0"]
    assert result["gates"]["untouched20_validation_authorized"] is False


def test_candidate_b_unchanged_reuse_and_changed_results_are_complete():
    result = analysis.build_analysis(REPO_ROOT)
    rows = [row for row in result["cells"] if row["prompt_condition"] == "Candidate_B"]
    assert sum(row["source_changed_by_healer"] == "true" for row in rows) == 2
    unchanged = [row for row in rows if row["source_changed_by_healer"] == "false"]
    assert len(unchanged) == 298
    assert all(row["h0_source_sha256"] == row["h1_source_sha256"] for row in unchanged)
    assert all(row["h1_result_basis"] == "byte_and_sha256_identical_h0_reuse" for row in unchanged)
    assert {row["healer_transition"] for row in rows if row["source_changed_by_healer"] == "true"} == {"fail_to_fail"}


def test_duplicate_missing_hash_drift_and_reuse_drift_fail_closed():
    with pytest.raises(analysis.AnalysisError, match="duplicate"):
        analysis._index_unique([{"id": "x"}, {"id": "x"}], ("id",), "fixture")
    with pytest.raises(analysis.AnalysisError, match="missing or unexpected"):
        analysis._require_exact_keys({"a"}, {"a", "b"}, "fixture")
    with pytest.raises(analysis.AnalysisError, match="hash drift"):
        analysis._verify_bytes(b"changed", hashlib.sha256(b"expected").hexdigest(), "fixture")
    h0 = {"program_id": "p", "evaluation_account_id": "h0", "evaluation_source_sha256": "a"}
    h1 = {"program_id": "p", "evaluation_account_id": "h1", "evaluation_source_sha256": "b"}
    ledger = {"program_id": "p", "h0_evaluation_account_id": "h0", "h1_evaluation_account_id": "h1", "source_sha256_exact_match": "true", "reuse_eligible_after_h0_evalplus": "true", "h0_source_sha256": "a", "h1_source_sha256": "b"}
    with pytest.raises(analysis.AnalysisError, match="reuse ledger hash mismatch"):
        analysis._validate_reuse_row(ledger, h0, h1)


def test_outputs_are_deterministic_and_manifest_hashes_match():
    first = analysis.build_outputs(REPO_ROOT)
    second = analysis.build_outputs(REPO_ROOT)
    assert first == second
    for relative, content in first.items():
        assert (OUTPUT_DIR / relative).read_bytes() == content
    manifest = json.loads(first[Path("manifest.json")])
    for name, digest in manifest["outputs_sha256_excluding_manifest"].items():
        assert hashlib.sha256(first[Path(name)]).hexdigest() == digest
    assert manifest["model_calls"] == 0
    assert manifest["evalplus_executions"] == 0
    assert manifest["validation_not_executed"] is True


def test_committed_csv_schemas_and_report_conclusions():
    cells = list(csv.DictReader(io.StringIO((OUTPUT_DIR / "paired_cell_results.csv").read_text(encoding="utf-8"))))
    accounts = list(csv.DictReader(io.StringIO((OUTPUT_DIR / "paired_account_results.csv").read_text(encoding="utf-8"))))
    assert tuple(cells[0]) == analysis.CELL_FIELDS
    assert tuple(accounts[0]) == analysis.ACCOUNT_FIELDS
    report = (OUTPUT_DIR / "paired_analysis_report_zh.md").read_text(encoding="utf-8")
    assert "Scaffold 本身優於 P0" in report
    assert "未通過全部 qualification gates" in report
    assert "無法判定交互作用" in report
    assert "暫停正式 20 題 validation" in report
    assert "model_calls=0" in report
