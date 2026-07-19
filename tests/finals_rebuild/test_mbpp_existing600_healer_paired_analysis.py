from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path

import pytest

from scripts import analyze_mbpp_existing600_healer_eval as analyzer
from scripts import run_mbpp_existing600_healer_eval as evaluator


REPO_ROOT = Path(__file__).resolve().parents[2]
FROZEN_DIR = REPO_ROOT / evaluator.FROZEN_MANIFEST_RELATIVE.parent
RESULTS_PATH = REPO_ROOT / analyzer.FROZEN_CHANGED_RESULTS_RELATIVE


def _csv_rows(value: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(value.decode("utf-8"))))


def _write_synthetic_result_set(tmp_path: Path, rows: list[dict[str, str]]) -> Path:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=evaluator.RESULT_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    results_path = tmp_path / "changed_h1_evalplus_results.csv"
    results_path.write_bytes(buffer.getvalue().encode("utf-8"))
    (tmp_path / "execution_manifest.json").write_text(
        json.dumps({
            "status": "changed_h1_evaluation_complete_pending_paired_analysis",
            "frozen_manifest_sha256": evaluator.FROZEN_MANIFEST_SHA256,
            "changed_h1_cells_evaluated": 41,
            "unchanged_cells_not_re_evaluated": 559,
            "parallel": 1,
            "results_sha256": hashlib.sha256(results_path.read_bytes()).hexdigest(),
            "rescue_regression_conclusion_produced": False,
        }),
        encoding="utf-8",
    )
    return results_path


def test_formal_paired_outputs_are_complete_and_deterministic() -> None:
    kwargs = {
        "manifest_path": FROZEN_DIR / "manifest.json",
        "manifest_sha256": evaluator.FROZEN_MANIFEST_SHA256,
        "changed_results_path": RESULTS_PATH,
    }
    first = analyzer.build_outputs(**kwargs)
    second = analyzer.build_outputs(**kwargs)
    assert first == second
    assert hashlib.sha256(RESULTS_PATH.read_bytes()).hexdigest() == analyzer.EXPECTED_CHANGED_RESULTS_SHA256

    pairs = _csv_rows(first["paired_cell_results.csv"])
    accounts = _csv_rows(first["paired_account_results.csv"])
    summaries = {row["stratum"]: row for row in _csv_rows(first["stratified_transition_summary.csv"])}
    tasks = _csv_rows(first["task_transition_summary.csv"])
    decision = json.loads(first["qualification_decision.json"])
    manifest = json.loads(first["paired_analysis_manifest.json"])

    assert len(pairs) == len({row["program_id"] for row in pairs}) == 600
    assert len(accounts) == len({row["evaluation_account_id"] for row in accounts}) == 1200
    assert sum(row["healer_account"] == "H0" for row in accounts) == 600
    assert sum(row["healer_account"] == "H1" for row in accounts) == 600
    assert len(tasks) == len({row["task_id"] for row in tasks}) == 60
    assert summaries["all"]["fail_to_fail"] == "440"
    assert summaries["all"]["fail_to_pass_rescue"] == "9"
    assert summaries["all"]["pass_to_fail_regression"] == "0"
    assert summaries["all"]["pass_to_pass"] == "151"
    assert summaries["all"]["changed"] == "41"
    assert summaries["all"]["unchanged"] == "559"
    assert summaries["p0"]["fail_to_pass_rescue"] == "9"
    assert summaries["scaffold_like"]["fail_to_pass_rescue"] == "0"
    assert summaries["changed"]["programs"] == "41"
    assert summaries["unchanged"]["programs"] == "559"
    assert decision["status"] == "eligible_for_independent_prospective_qualification"
    assert decision["rescue"] == 9 and decision["regression"] == 0
    assert manifest["programs"] == 600 and manifest["accounts"] == 1200
    assert manifest["evalplus_reexecuted"] is False and manifest["model_calls"] == 0


def test_pipeline_healer_and_identity_reuse_are_distinct() -> None:
    outputs = analyzer.build_outputs(
        manifest_path=FROZEN_DIR / "manifest.json",
        manifest_sha256=evaluator.FROZEN_MANIFEST_SHA256,
        changed_results_path=RESULTS_PATH,
    )
    accounts = _csv_rows(outputs["paired_account_results.csv"])
    h1 = [row for row in accounts if row["healer_account"] == "H1"]
    assert all(row["pipeline_correction_precedes_healer"] == "true" for row in accounts)
    assert all(row["pipeline_correction_is_healer"] == "false" for row in accounts)
    assert sum(row["result_basis"] == "manual_evalplus_changed_h1" for row in h1) == 41
    assert sum(row["result_basis"] == "exact_source_state_sha256_h0_reuse" for row in h1) == 559
    assert sum(row["verified_rescue"] == "true" for row in h1) == 9
    assert sum(row["regression"] == "true" for row in h1) == 0


def test_exact_mcnemar_is_frozen_and_applicability_is_explicit() -> None:
    assert analyzer.exact_mcnemar_two_sided(rescue=9, regression=0) == pytest.approx(0.00390625)
    assert analyzer.exact_mcnemar_two_sided(rescue=0, regression=0) == 1.0


def test_missing_changed_result_fails_closed(tmp_path: Path) -> None:
    rows = _csv_rows(RESULTS_PATH.read_bytes())[:-1]
    path = _write_synthetic_result_set(tmp_path, rows)
    with pytest.raises(analyzer.PairedAnalysisError, match="41"):
        analyzer.build_analysis(
            manifest_path=FROZEN_DIR / "manifest.json",
            manifest_sha256=evaluator.FROZEN_MANIFEST_SHA256,
            changed_results_path=path,
            enforce_frozen_result_path=False,
        )


def test_duplicate_changed_result_fails_closed(tmp_path: Path) -> None:
    rows = _csv_rows(RESULTS_PATH.read_bytes())
    rows[-1] = dict(rows[0])
    path = _write_synthetic_result_set(tmp_path, rows)
    with pytest.raises(analyzer.PairedAnalysisError, match="duplicate"):
        analyzer.build_analysis(
            manifest_path=FROZEN_DIR / "manifest.json",
            manifest_sha256=evaluator.FROZEN_MANIFEST_SHA256,
            changed_results_path=path,
            enforce_frozen_result_path=False,
        )
