from __future__ import annotations

import hashlib
import json

import pytest

from agent_tools.finals_rebuild.benchmarks_adapter import PublicBenchmarkTask
from scripts import freeze_mbpp_factorial_qualification_operator_binding_v1 as binding
from scripts import run_mbpp_factorial_development_qualification as runner


def test_operator_plans_are_paired_140_by_140() -> None:
    outputs = binding.build_outputs()
    p0 = json.loads(outputs["p0_generation_plan.json"])
    p1 = json.loads(outputs["candidate_b_generation_plan.json"])
    assert len(p0["cells"]) == len(p1["cells"]) == 140
    assert [(row["task_id"], row["seed"]) for row in p0["cells"]] == [
        (row["task_id"], row["seed"]) for row in p1["cells"]
    ]
    assert p0["treatment"] == "p0"
    assert p1["treatment"] == "candidate_b"
    assert p0["candidate_exact_text_utf8"] is None
    assert hashlib.sha256(p1["candidate_exact_text_utf8"].encode()).hexdigest() == p1["candidate_exact_text_sha256"]


def test_generation_invariants_are_identical_except_prompt_arm() -> None:
    outputs = binding.build_outputs()
    plans = [json.loads(outputs[name]) for name in ("p0_generation_plan.json", "candidate_b_generation_plan.json")]
    for plan in plans:
        assert plan["model"] == "qwen3.5:9b"
        assert plan["think"] is False
        assert plan["timeout_seconds"] == 600
        assert plan["attempts_per_cell"] == 1
        assert plan["retry"] is plan["resume"] is plan["selective_retry"] is plan["overwrite"] is False
        assert plan["healer"] is False
        assert plan["pipeline_correction_is_healer"] is False
        assert len(plan["operator_driver_sha256"]) == 64


def test_operator_driver_hash_is_pinned() -> None:
    plan = json.loads(binding.build_outputs()["p0_generation_plan.json"])
    actual = hashlib.sha256((binding.REPO_ROOT / binding.RUNNER_SOURCE).read_bytes()).hexdigest()
    assert plan["operator_driver_sha256"] == actual


def test_storage_paths_are_short_and_no_directory_is_created() -> None:
    storage = json.loads(binding.build_outputs()["storage_mapping.json"])
    assert storage["all_paths_within_budget"] is True
    assert all(row["longest_planned_windows_path_length"] < 240 for row in storage["runs"])
    assert storage["run_directories_created"] is False
    assert not (binding.REPO_ROOT / "artifacts/pbd/mbpp_b28/p0/r001").exists()
    assert not (binding.REPO_ROOT / "artifacts/pbd/mbpp_b28/cb/r001").exists()
    assert not (binding.REPO_ROOT / binding.FACTORIAL_PATH).exists()


def test_manifest_does_not_enable_evaluator_or_execute_calls() -> None:
    manifest = json.loads(binding.build_outputs()["operator_binding_manifest.json"])
    assert manifest["status"] == "frozen_not_executed_development_only"
    assert manifest["counts"] == {
        "candidate_b_generation_cells": 140,
        "future_factorial_accounts": 560,
        "p0_generation_cells": 140,
        "paired_identities": 140,
    }
    assert manifest["model_calls"] == manifest["evalplus_executions"] == 0
    assert manifest["run_directories_created"] is False
    assert manifest["evaluation_driver_enabled"] is False


def test_runner_preflight_is_read_only_and_reports_not_started() -> None:
    result = runner.preflight()
    assert result["status"] == "preflight_ok_no_model_or_evaluator_call"
    assert result["run_states"] == {"candidate_b": "not_started", "p0": "not_started"}
    assert result["factorial_materialization_state"] == "not_started"
    assert result["planned_generation_cells"] == 280
    assert result["planned_factorial_accounts"] == 560


def test_wrong_run_id_is_rejected_before_model_contact() -> None:
    with pytest.raises(runner.FactorialQualificationRunError, match="run ID differs"):
        runner.generate(
            treatment="p0", run_id="wrong", base_url="http://127.0.0.1:1", timeout_seconds=600.0
        )


def test_prompt_composition_changes_only_candidate_arm() -> None:
    p0 = runner.load_frozen_plan("p0")
    p1 = runner.load_frozen_plan("candidate_b")
    official = '"""\nassert expected(1) == 1\n"""\n'
    assert runner._composed_prompt(p0, official) == official
    composed = runner._composed_prompt(p1, official)
    assert composed == official + p1["separator_exact_text_utf8"] + p1["candidate_exact_text_utf8"]


def _synthetic_runs() -> tuple[dict, dict, dict, dict]:
    plans = {name: runner.load_frozen_plan(name) for name in runner.TREATMENTS}
    runs = {}
    tasks = {}
    for task_id in plans["p0"]["task_ids"]:
        tasks[task_id] = PublicBenchmarkTask(
            benchmark="mbpp", task_id=task_id,
            prompt='"""\nassert expected(1) == 1\n"""\n',
            entry_point="expected", canonical_solution=None,
        )
    for treatment, plan in plans.items():
        raw = {}
        pipeline = {}
        for cell in plan["cells"]:
            generation_id = cell["planned_cell_id"]
            source = "def wrong(x):\n    return x\n"
            source_hash = hashlib.sha256(source.encode()).hexdigest()
            raw[generation_id] = {
                "generation_id": generation_id,
                "raw_response_sha256": source_hash,
                "generation_metadata": {"done_reason": "stop"},
            }
            pipeline[generation_id] = {
                "generation_id": generation_id,
                "pipeline_corrected_output": source,
                "pipeline_corrected_output_sha256": source_hash,
            }
        runs[treatment] = {"raw": raw, "pipeline": pipeline}
    return plans, runs, tasks, runner._account_plan()


def test_factorial_materialization_uses_same_generation_for_h0_h1() -> None:
    plans, runs, tasks, accounts = _synthetic_runs()
    records = runner.build_factorial_records(plans, runs, tasks, accounts)
    assert len(records) == 560
    assert {row["factorial_arm"] for row in records} == {"P0_H0", "P0_H1", "P1_H0", "P1_H1"}
    for generation_id in {row["generation_id"] for row in records}:
        pair = [row for row in records if row["generation_id"] == generation_id]
        assert len(pair) == 2
        assert pair[0]["raw_response_sha256"] == pair[1]["raw_response_sha256"]
        assert pair[0]["pipeline_input_sha256"] == pair[1]["pipeline_input_sha256"]
        h0 = next(row for row in pair if row["healer_account"] == "H0")
        h1 = next(row for row in pair if row["healer_account"] == "H1")
        assert h0["evaluation_source"].endswith("return x\n")
        assert h1["evaluation_source"].endswith("\nexpected = wrong\n")
        assert h1["healer_triggered_rule_ids"] == ["entrypoint_alias_unique_arity_compatible_v0"]
        assert h0["model_regeneration_for_healer"] is h1["model_regeneration_for_healer"] is False


def test_truncation_abstains_without_changing_h1_source() -> None:
    plans, runs, tasks, accounts = _synthetic_runs()
    first = plans["p0"]["cells"][0]["planned_cell_id"]
    runs["p0"]["raw"][first]["generation_metadata"]["done_reason"] = "length"
    records = runner.build_factorial_records(plans, runs, tasks, accounts)
    pair = [row for row in records if row["generation_id"] == first]
    h0 = next(row for row in pair if row["healer_account"] == "H0")
    h1 = next(row for row in pair if row["healer_account"] == "H1")
    assert h1["healer_status"] == "abstained"
    assert h1["healer_diagnostic"] == "generation_truncated"
    assert h1["evaluation_source_sha256"] == h0["evaluation_source_sha256"]


def test_deterministic_operator_outputs_and_hashes() -> None:
    first = binding.build_outputs()
    second = binding.build_outputs()
    assert first == second
    manifest = json.loads(first["operator_binding_manifest.json"])
    for name, digest in manifest["output_sha256_excluding_manifest"].items():
        assert hashlib.sha256(first[name]).hexdigest() == digest


def test_frozen_operator_bytes_match_builder() -> None:
    binding.write_outputs(check=True)
