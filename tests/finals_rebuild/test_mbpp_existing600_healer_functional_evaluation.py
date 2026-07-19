from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path

import pytest

from scripts import analyze_mbpp_existing600_healer_eval as analyzer
from scripts import prepare_mbpp_existing600_healer_h0_h1 as preparation
from scripts import run_mbpp_existing600_healer_eval as evaluator


REPO_ROOT = Path(__file__).resolve().parents[2]
FROZEN_DIR = REPO_ROOT / preparation.OUTPUT_RELATIVE


def _csv_rows(value: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(value.decode("utf-8"))))


def _jsonl_rows(value: bytes) -> list[dict[str, object]]:
    return [json.loads(line) for line in value.decode("utf-8").splitlines()]


def test_materializer_recomputes_exact_frozen_counts_and_hashes() -> None:
    outputs = preparation.build_outputs(REPO_ROOT)
    accounts = _csv_rows(outputs["h0_h1_accounts.csv"])
    changed = _jsonl_rows(outputs["changed_h1_eval_input.jsonl"])
    reuse = _csv_rows(outputs["unchanged_h0_reuse_ledger.csv"])
    manifest = json.loads(outputs["manifest.json"])

    assert len(accounts) == 1200
    assert Counter(row["healer_account"] for row in accounts) == {"H0": 600, "H1": 600}
    assert len({row["program_id"] for row in accounts}) == 600
    assert len({row["evaluation_account_id"] for row in accounts}) == 1200
    assert len(changed) == 41
    assert Counter(row["prompt_condition"] for row in changed) == {"p0": 39, "scaffold_like": 2}
    assert len(reuse) == 559
    assert all(row["source_state_sha256_exact_match"] == "true" for row in reuse)
    assert all(row["existing_h0_result_complete"] == "true" for row in reuse)
    assert all(row["reuse_eligible"] == "true" for row in reuse)
    assert manifest["healer_sha256"] == preparation.EXPECTED_HEALER_SHA256
    assert manifest["pipeline_sha256"] == preparation.EXPECTED_PIPELINE_SHA256
    assert manifest["evalplus_executions"] == manifest["model_calls"] == 0
    assert hashlib.sha256(outputs["manifest.json"]).hexdigest() == evaluator.FROZEN_MANIFEST_SHA256


def test_all_changed_sources_are_alias_only_and_compile() -> None:
    outputs = preparation.build_outputs(REPO_ROOT)
    accounts = _csv_rows(outputs["h0_h1_accounts.csv"])
    changed = _jsonl_rows(outputs["changed_h1_eval_input.jsonl"])
    h1 = {row["evaluation_account_id"]: row for row in accounts if row["healer_account"] == "H1"}
    for row in changed:
        account = h1[str(row["evaluation_account_id"])]
        source = str(row["completion"])
        tree = ast.parse(source)
        compile(source, "<test-frozen-h1>", "exec")
        alias = tree.body[-1]
        assert isinstance(alias, ast.Assign)
        assert isinstance(alias.targets[0], ast.Name)
        assert alias.targets[0].id == account["expected_entry_point"]
        assert account["alias_only_verified"] == "true"
        assert account["compile_verified"] == "true"
        assert hashlib.sha256(source.encode("utf-8")).hexdigest() == row["h1_source_sha256"]


def test_materializer_is_byte_deterministic_and_excludes_new28() -> None:
    first = preparation.build_outputs(REPO_ROOT)
    second = preparation.build_outputs(REPO_ROOT)
    assert first == second
    manifest = json.loads(first["manifest.json"])
    assert all("mbpp_b28" not in path for path in manifest["source_sha256"])
    guide = first["operator_guide_zh.md"].decode("utf-8")
    assert evaluator.FROZEN_MANIFEST_SHA256 in guide
    assert "--parallel 1" in guide
    assert "/home/yehya/.venvs/ast_evalplus/bin/python" in guide


def test_frozen_evaluator_preflight_accepts_only_exact_assets() -> None:
    manifest_path = FROZEN_DIR / "manifest.json"
    manifest, changed = evaluator.validate_frozen_inputs(
        manifest_path=manifest_path,
        manifest_sha256=evaluator.FROZEN_MANIFEST_SHA256,
        parallel=1,
    )
    assert manifest["counts"]["changed"] == 41
    assert len(changed) == 41
    with pytest.raises(evaluator.EvaluationDriverError, match="parallel"):
        evaluator.validate_frozen_inputs(
            manifest_path=manifest_path,
            manifest_sha256=evaluator.FROZEN_MANIFEST_SHA256,
            parallel=2,
        )
    with pytest.raises(evaluator.EvaluationDriverError, match="manifest SHA-256"):
        evaluator.validate_frozen_inputs(
            manifest_path=manifest_path,
            manifest_sha256="0" * 64,
            parallel=1,
        )


def test_evaluator_has_no_generation_or_overwrite_dependency() -> None:
    source = (REPO_ROOT / "scripts/run_mbpp_existing600_healer_eval.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        (node.module or "")
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    assert not any("ollama" in name or "generation_runner" in name for name in imported)
    assert "open(\"wb\")" not in source
    assert "open(\"w\")" not in source
    assert "--parallel must equal 1" in source


def test_paired_analyzer_requires_and_accounts_for_all_41_results(tmp_path: Path) -> None:
    accounts = _csv_rows((FROZEN_DIR / "h0_h1_accounts.csv").read_bytes())
    h0_by_program = {
        row["program_id"]: row for row in accounts if row["healer_account"] == "H0"
    }
    changed = _jsonl_rows((FROZEN_DIR / "changed_h1_eval_input.jsonl").read_bytes())
    result_rows: list[dict[str, str]] = []
    for row in changed:
        h0 = h0_by_program[str(row["program_id"])]
        result_rows.append({
            "program_id": str(row["program_id"]),
            "evaluation_account_id": str(row["evaluation_account_id"]),
            "development_layer": str(row["development_layer"]),
            "prompt_condition": str(row["prompt_condition"]),
            "run_id": str(row["run_id"]),
            "task_id": str(row["task_id"]),
            "seed": str(row["seed"]),
            "generation_id": str(row["generation_id"]),
            "normalized_source_sha256": str(row["normalized_source_sha256"]),
            "h1_source_sha256": str(row["h1_source_sha256"]),
            "base_status": "pass" if h0["existing_h0_pass"] == "true" else "fail",
            "plus_status": "pass" if h0["existing_h0_pass"] == "true" else "fail",
            "h1_evalplus_pass": h0["existing_h0_pass"],
            "evaluator_version": evaluator.EXPECTED_EVALPLUS_VERSION,
            "evaluator_engine": evaluator.EXPECTED_EVALUATOR_ENGINE,
        })
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=evaluator.RESULT_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(result_rows)
    results_path = tmp_path / "changed_h1_evalplus_results.csv"
    results_path.write_text(buffer.getvalue(), encoding="utf-8", newline="")
    results_hash = hashlib.sha256(results_path.read_bytes()).hexdigest()
    (tmp_path / "execution_manifest.json").write_text(
        json.dumps({
            "status": "changed_h1_evaluation_complete_pending_paired_analysis",
            "frozen_manifest_sha256": evaluator.FROZEN_MANIFEST_SHA256,
            "changed_h1_cells_evaluated": 41,
            "unchanged_cells_not_re_evaluated": 559,
            "parallel": 1,
            "results_sha256": results_hash,
            "rescue_regression_conclusion_produced": False,
        }),
        encoding="utf-8",
    )
    analysis = analyzer.build_analysis(
        manifest_path=FROZEN_DIR / "manifest.json",
        manifest_sha256=evaluator.FROZEN_MANIFEST_SHA256,
        changed_results_path=results_path,
    )
    assert len(analysis["pairs"]) == 600
    assert analysis["summaries"][0]["changed"] == "41"
    assert analysis["summaries"][0]["unchanged"] == "559"
    assert analysis["decision"]["status"] == "statically_safe_no_observed_functional_benefit"


@pytest.mark.parametrize(
    ("rescue", "regression", "expected"),
    [
        (1, 0, "eligible_for_independent_prospective_qualification"),
        (0, 0, "statically_safe_no_observed_functional_benefit"),
        (100, 1, "healer_candidate_not_qualified"),
    ],
)
def test_paired_decision_rules_are_fixed(rescue: int, regression: int, expected: str) -> None:
    assert analyzer.decision_status(rescue=rescue, regression=regression) == expected
