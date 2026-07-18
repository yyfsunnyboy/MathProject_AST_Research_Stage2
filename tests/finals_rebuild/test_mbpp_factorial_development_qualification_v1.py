from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path

from scripts import freeze_mbpp_factorial_development_qualification_v1 as freeze


def _rows(value: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(value.decode("utf-8"))))


def test_completion_gap_does_not_authorize_validation() -> None:
    gap = json.loads(freeze.build_outputs()["completion_gap_audit.json"])
    assert gap["overall_status"] == "incomplete_formal_validation_not_authorized"
    assert gap["formal_validation_allowed"] is False
    statuses = {row["requirement"]: row["status"] for row in gap["requirements"]}
    assert statuses["final P1"] == "missing_independent_qualification"
    assert statuses["prospective validation identities"] == "missing_and_unread"


def test_new_selection_is_next_28_unused_hash_ranks() -> None:
    rows = _rows(freeze.build_outputs()["candidate_b_new28_selection.csv"])
    assert len(rows) == 28
    assert [int(row["prior_selection_rank"]) for row in rows] == list(range(41, 69))
    assert len({row["task_id"] for row in rows}) == 28
    assert all(row["prompt_answer_tests_read"] == "false" for row in rows)
    assert all(row["source_frozen_governance_role"] == "historical_development_pool" for row in rows)


def test_new_selection_has_zero_overlap_with_active_60() -> None:
    outputs = freeze.build_outputs()
    selected = {row["task_id"] for row in _rows(outputs["candidate_b_new28_selection.csv"])}
    expansion = json.loads((freeze.REPO_ROOT / freeze.EXPANSION_MANIFEST).read_text(encoding="utf-8"))
    active = {row["task_id"] for row in expansion["development_tasks"]}
    assert len(active) == 60
    assert not (selected & active)
    assert 116 - len(active) - len(selected) == 28


def test_candidate_b_exact_text_and_status_are_pinned() -> None:
    outputs = freeze.build_outputs()
    assert outputs["candidate_b_exact_text.txt"] == freeze.CANDIDATE_B_TEXT.encode("utf-8")
    plan = json.loads(outputs["candidate_b_2x2_development_plan.json"])
    candidate = plan["candidate_b"]
    assert candidate["status"] == "frozen_experimental_candidate_not_official_p1"
    assert candidate["exact_text_sha256"] == hashlib.sha256(outputs["candidate_b_exact_text.txt"]).hexdigest()
    assert candidate["same_candidate_a_40_retest_allowed"] is False


def test_generation_plan_has_140_paired_identities_and_280_cells() -> None:
    plan = json.loads(freeze.build_outputs()["candidate_b_2x2_development_plan.json"])
    cells = plan["generation"]["cells"]
    assert len(cells) == 280
    assert len({(cell["task_id"], cell["seed"]) for cell in cells}) == 140
    assert sum(cell["prompt_condition"] == "P0" for cell in cells) == 140
    assert sum(cell["prompt_condition"] == "P1_candidate_b" for cell in cells) == 140
    assert all(cell["attempt_count"] == 1 for cell in cells)
    assert plan["generation"]["retry_resume_selective_retry_overwrite"] is False


def test_new_factorial_plan_has_four_accounts_and_no_healer_regeneration() -> None:
    outputs = freeze.build_outputs()
    rows = _rows(outputs["candidate_b_2x2_account_plan.csv"])
    assert len(rows) == 560
    assert {
        (row["prompt_condition"], row["healer_account"]) for row in rows
    } == {("P0", "H0"), ("P0", "H1"), ("P1_candidate_b", "H0"), ("P1_candidate_b", "H1")}
    assert all(row["same_generation_h0_h1"] == "true" for row in rows)
    assert all(row["model_regeneration_for_healer"] == "false" for row in rows)
    for planned_id in {row["generation_planned_cell_id"] for row in rows}:
        pair = [row for row in rows if row["generation_planned_cell_id"] == planned_id]
        assert len(pair) == 2
        assert {row["healer_account"] for row in pair} == {"H0", "H1"}


def test_existing_600_fork_to_1200_h0_h1_accounts() -> None:
    rows = _rows(freeze.build_outputs()["existing_600_h0_h1_account_plan.csv"])
    assert len(rows) == 1200
    assert len({row["generation_id"] for row in rows}) == 600
    assert sum(row["healer_account"] == "H0" for row in rows) == 600
    assert sum(row["healer_account"] == "H1" for row in rows) == 600
    for generation_id in {row["generation_id"] for row in rows}:
        pair = [row for row in rows if row["generation_id"] == generation_id]
        assert len(pair) == 2
        assert pair[0]["shared_pipeline_input_sha256"] == pair[1]["shared_pipeline_input_sha256"]
    assert all(row["evaluator_not_yet_executed"] == "true" for row in rows)


def test_pipeline_and_healer_are_pinned_and_separately_accounted() -> None:
    plan = json.loads(freeze.build_outputs()["candidate_b_2x2_development_plan.json"])
    evaluation = plan["evaluation"]
    assert len(evaluation["pipeline_sha256"]) == len(evaluation["healer_sha256"]) == 64
    assert evaluation["same_healer_version_order_guards"] is True
    assert evaluation["healer_model_regeneration"] is False
    assert evaluation["pipeline_packaging_is_healer"] is False


def test_model_protocol_and_path_budget_are_frozen() -> None:
    plan = json.loads(freeze.build_outputs()["candidate_b_2x2_development_plan.json"])
    model = plan["model_protocol"]
    assert model["model"] == "qwen3.5:9b"
    assert model["think"] is False
    assert model["timeout_seconds"] == 600
    assert model["seeds"] == [11, 22, 33, 44, 55]
    assert plan["windows_path_budget"]["passed"] is True
    assert plan["generation"]["run_directories_created_by_this_freeze"] is False
    assert not (freeze.REPO_ROOT / freeze.P0_PATH).exists()
    assert not (freeze.REPO_ROOT / freeze.P1_PATH).exists()


def test_promotion_gates_require_separate_p1_and_healer_qualification() -> None:
    plan = json.loads(freeze.build_outputs()["candidate_b_2x2_development_plan.json"])
    gates = plan["promotion_gates"]
    assert gates["p1_format"]["strict_python_only_min"] == 0.9
    assert gates["p1_correctness_safety"]["rescues_at_least_regressions"] is True
    assert gates["healer_static"]["changes_outside_trigger"] == 0
    assert gates["healer_evidence"]["transformed_pass_to_fail_regressions_max"] == 0
    assert "both final P1 and final Healer" in gates["joint_activation"]


def test_manifest_has_no_calls_or_sealed_reads() -> None:
    manifest = json.loads(freeze.build_outputs()["factorial_development_qualification_manifest.json"])
    assert manifest["status"] == "frozen_not_executed_development_only"
    assert manifest["model_calls"] == manifest["evalplus_executions"] == 0
    assert manifest["validation_tasks_read"] is False
    assert manifest["confirmatory_or_sealed_tasks_read"] is False
    assert manifest["run_directories_created"] is False
    assert manifest["counts"] == {
        "existing_programs": 600,
        "new_task_seed_identities": 140,
        "new_tasks": 28,
        "planned_existing_h0_h1_accounts": 1200,
        "planned_generations": 280,
        "planned_new_factorial_accounts": 560,
        "remaining_unused_development_tasks": 28,
    }


def test_deterministic_bytes_and_hashes() -> None:
    first = freeze.build_outputs()
    second = freeze.build_outputs()
    assert first == second
    manifest = json.loads(first["factorial_development_qualification_manifest.json"])
    for name, digest in manifest["output_sha256_excluding_manifest"].items():
        assert hashlib.sha256(first[name]).hexdigest() == digest


def test_frozen_bytes_match_builder() -> None:
    freeze.write_outputs(check=True)


def test_no_forbidden_role_words_in_selected_task_rows() -> None:
    rows = _rows(freeze.build_outputs()["candidate_b_new28_selection.csv"])
    forbidden = ("validation", "confirmatory", "sealed", "excluded")
    assert all(not any(word in "|".join(row.values()).lower() for word in forbidden) for row in rows)


def test_output_directory_contains_no_run_artifacts() -> None:
    outputs = freeze.build_outputs()
    assert not any(name.endswith("raw_generations.jsonl") for name in outputs)
    assert not any("evaluation_results" in name for name in outputs)
    assert not any(Path(name).name == "generation_plan.json" for name in outputs)
