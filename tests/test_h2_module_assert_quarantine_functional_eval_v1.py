from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
from pathlib import Path

from scripts import finalize_h2_module_assert_quarantine_functional_eval_v1 as finalize
from scripts import prepare_h2_module_assert_quarantine_functional_eval_v1 as prepare
from scripts import run_h2_module_assert_quarantine_functional_eval_v1 as runner


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = (
    ROOT
    / "artifacts/public_benchmark_governance/"
    "h2_module_assert_quarantine_functional_evaluation_v1"
)


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def test_preregistration_rebuild_and_frozen_counts() -> None:
    first = prepare.build_outputs()
    second = prepare.build_outputs()
    assert first == second
    assert set(first) == {
        "cell_roster.jsonl",
        "post_h2_eval_input.jsonl",
        "preregistration.json",
    }
    prereg = json.loads(first["preregistration.json"])
    assert prereg["status"] == "preregistered_not_executed"
    assert prereg["counts"] == {
        "roster": 91,
        "transformed_to_execute": 71,
        "abstained_identity_only": 20,
    }
    assert prereg["rule"]["sha256"] == prepare.EXPECTED_RULE_SHA
    assert prereg["frozen_files"]["cell_roster.jsonl"] == sha(
        first["cell_roster.jsonl"]
    )
    assert prereg["frozen_files"]["post_h2_eval_input.jsonl"] == sha(
        first["post_h2_eval_input.jsonl"]
    )
    assert prereg["execution"]["model_calls"] == 0
    assert prereg["execution"]["parallel"] == 1


def test_runner_preflight_accepts_only_frozen_71_cells() -> None:
    prereg_path = ARTIFACT / "preregistration.json"
    prereg_sha = sha(prereg_path.read_bytes())
    prereg, rows = runner._validate_preregistration(
        prereg_path, prereg_sha, parallel=1
    )
    assert prereg["freeze_criteria"]["priority"] == "C, then A, then B"
    assert len(rows) == 71
    assert len({row["source_record_id"] for row in rows}) == 71
    assert all(row["transformed"] is True for row in rows)
    for row in rows:
        tree = ast.parse(row["completion"])
        assert not any(isinstance(node, ast.Assert) for node in tree.body)


def test_execution_scope_and_receipt_are_exact() -> None:
    result_path = (
        ARTIFACT
        / "manual_post_h2_evalplus_run_001/post_h2_evalplus_results.csv"
    )
    results = list(
        csv.DictReader(io.StringIO(result_path.read_text(encoding="utf-8")))
    )
    execution = json.loads(
        (
            ARTIFACT
            / "manual_post_h2_evalplus_run_001/execution_record.json"
        ).read_text(encoding="utf-8")
    )
    roster = [
        json.loads(line)
        for line in (ARTIFACT / "cell_roster.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert len(results) == execution["candidate_executions"] == 71
    assert execution["abstained_cells_executed"] == 0
    assert execution["model_calls"] == 0
    assert execution["candidate_generations"] == 0
    assert {row["source_record_id"] for row in results} == {
        row["source_record_id"] for row in roster if row["transformed"]
    }
    assert all(
        row["blocker_removed_execution_evidence"] == "true" for row in results
    )


def test_final_outputs_are_deterministic_and_apply_criterion_b() -> None:
    first = finalize.build_outputs()
    second = finalize.build_outputs()
    assert first == second
    freeze = json.loads(first["freeze_decision.json"])
    assert freeze["criterion"] == "B"
    assert freeze["decision"] == "development_candidate_not_frozen"
    assert freeze["regression"] == 0
    assert freeze["verified_rescue"] == 0
    assert freeze["all_raw_pass_preserved"] is True
    summary = json.loads(first["aggregate_summary.json"])
    combined = summary["cohorts"]["combined"]
    assert combined["transformed"] == 71
    assert combined["abstained"] == 20
    assert combined["blocker_removed"] == 71
    assert combined["partial_repair"] == 46
    assert combined["preserved_pass"] == 25
    assert combined["regression"] == 0
    assert summary["four_b_transformed_raw_pass_controls"] == {
        "count": 25,
        "preserved": 25,
        "regressed": 0,
    }
    assert summary["nine_b_all_raw_pass_controls"] == {
        "count": 0,
        "preserved": 0,
        "regressed": 0,
    }


def test_paired_ledger_separates_raw_pipeline_and_post_h2() -> None:
    rows = [
        json.loads(line)
        for line in (ARTIFACT / "paired_cell_ledger.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert len(rows) == 91
    assert sum(row["outcome"] == "partial_repair" for row in rows) == 46
    assert sum(row["outcome"] == "preserved_pass" for row in rows) == 25
    assert sum(row["outcome"] == "abstained_unchanged" for row in rows) == 20
    assert not any(row["outcome"] in {"verified_rescue", "regression"} for row in rows)
    for row in rows:
        assert row["generation_raw_response_sha256"]
        assert row["pipeline_source_sha256"]
        assert row["post_h2_source_sha256"]
        if row["abstained"]:
            assert (
                row["pipeline_source_sha256"]
                == row["post_h2_source_sha256"]
            )
            assert row["post_h2_result_basis"].endswith("no_candidate_execution")


def test_rule_sha_and_credential_scan_unchanged() -> None:
    rule = ROOT / prepare.RULE_RELATIVE
    assert sha(rule.read_bytes()) == prepare.EXPECTED_RULE_SHA
    scan = json.loads((ARTIFACT / "credential_scan.json").read_text())
    assert scan["status"] == "pass"
    assert scan["finding_count"] == 0
