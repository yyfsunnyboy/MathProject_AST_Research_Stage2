from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts import analyze_mbpp_candidate_a_expansion as analyzer
from scripts import freeze_mbpp_candidate_a_expansion_protocol as frozen
from scripts import run_mbpp_candidate_a_expansion as driver


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / frozen.OUTPUT_RELATIVE


def _plans():
    inputs = frozen._load_inputs(REPO_ROOT)
    return (
        frozen.build_generation_plan(inputs, treatment_id=frozen.P0_TREATMENT_ID),
        frozen.build_generation_plan(inputs, treatment_id=frozen.CA_TREATMENT_ID),
    )


def test_sources_candidate_hash_and_expansion_scope_are_frozen():
    inputs = frozen._load_inputs(REPO_ROOT)
    expansion = inputs["expansion"]
    discovery = {
        row["task_id"]
        for row in expansion["development_tasks"]
        if row["development_layer"] == "discovery_development"
    }

    assert inputs["source_hashes"] == frozen.EXPECTED_SOURCE_HASHES
    assert hashlib.sha256(inputs["candidate_text"].encode("utf-8")).hexdigest() == (
        frozen.CANDIDATE_SHA256
    )
    assert frozen.CANDIDATE_SHA256 == (
        "bffa1e7e3d1ff77b0de326083bf6c7fd441b2f3b050b45e205a5ba51be87f058"
    )
    assert len(inputs["task_ids"]) == len(set(inputs["task_ids"])) == 40
    assert not (set(inputs["task_ids"]) & discovery)
    assert expansion["zero_overlap"]["verified_total_forbidden_overlap"] == 0
    assert inputs["zero_overlap"] == {
        "excluded_historical": 0,
        "external_confirmatory_candidate": 0,
        "internal_confirmatory_candidate": 0,
        "sealed_reserve": 0,
        "validation": 0,
    }


def test_two_treatments_have_200_fully_paired_unique_cells_each():
    p0, candidate = _plans()
    p0_keys = [(cell["task_id"], cell["seed"]) for cell in p0["cells"]]
    candidate_keys = [(cell["task_id"], cell["seed"]) for cell in candidate["cells"]]

    assert p0["task_count"] == candidate["task_count"] == 40
    assert len(p0["cells"]) == p0["expected_cells"] == 200
    assert len(candidate["cells"]) == candidate["expected_cells"] == 200
    assert len(set(p0_keys)) == len(set(candidate_keys)) == 200
    assert p0_keys == candidate_keys
    assert {seed for _, seed in p0_keys} == {11, 22, 33, 44, 55}
    assert len({cell["planned_cell_id"] for cell in p0["cells"]}) == 200
    assert len({cell["planned_cell_id"] for cell in candidate["cells"]}) == 200


def test_prompt_treatments_and_candidate_status_are_exact():
    p0, candidate = _plans()

    assert p0["prompt_composition_order"] == ["official_prompt_verbatim"]
    assert p0["scaffold"] is False
    assert p0["candidate_exact_text_utf8"] is None
    assert candidate["prompt_composition_order"] == [
        "official_prompt_verbatim",
        "fixed_separator",
        "candidate_a_exact_text",
    ]
    assert candidate["candidate_status"] == (
        "frozen_experimental_candidate_not_official_v1"
    )
    assert candidate["candidate_exact_text_sha256"] == frozen.CANDIDATE_SHA256
    assert hashlib.sha256(
        candidate["candidate_exact_text_utf8"].encode("utf-8")
    ).hexdigest() == frozen.CANDIDATE_SHA256
    assert candidate["separator_exact_text_utf8"] == frozen.PROMPT_SEPARATOR
    assert hashlib.sha256(
        candidate["separator_exact_text_utf8"].encode("utf-8")
    ).hexdigest() == frozen.PROMPT_SEPARATOR_SHA256


def test_model_sampling_timeout_attempt_and_accounting_are_frozen():
    for plan in _plans():
        assert plan["model"] == "qwen3.5:9b"
        assert plan["model_digest"] == frozen.MODEL_DIGEST
        assert plan["quantization"] == "Q4_K_M"
        assert plan["dataset_hash"] == frozen.DATASET_HASH
        assert plan["generation_parameters"] == {
            "num_ctx": 8192,
            "num_predict": 2048,
            "stream": False,
            "temperature": 0.2,
            "thinking": False,
            "top_k": 20,
            "top_p": 0.95,
        }
        assert plan["ollama_request_timeout_seconds"] == 600.0
        assert plan["attempts_per_cell"] == 1
        assert not any(
            plan[key]
            for key in ("retry", "resume", "selective_retry", "overwrite", "healer")
        )
        assert plan["accounts"] == ["observed", "pipeline_corrected"]
        assert plan["pipeline_correction_is_healer"] is False
        assert plan["itt_policy"] == {
            "reasoning_leakage_counted_separately": True,
            "regenerate_on_protocol_violation": False,
            "thinking_content_silently_removed": False,
            "transport_complete_protocol_violations_included": True,
        }


def test_promotion_gates_and_failure_governance_are_exact():
    gates = frozen.build_promotion_gates()

    assert gates["format_gate"] == {
        "all_required": True,
        "code_fence_rate_max": 0.05,
        "extra_text_rate_max": 0.05,
        "pipeline_extraction_success_rate_min": 0.95,
        "strict_python_only_compliance_rate_min": 0.90,
    }
    safety = gates["pipeline_correctness_safety_gate"]
    assert safety["candidate_pipeline_pass_count_gte_paired_p0"] is True
    assert safety["paired_rescues_gte_paired_regressions"] is True
    assert safety["all_regressions_fully_disclosed"] is True
    assert gates["claim_rule"]["pipeline_correctness_improvement"] == {
        "exact_mcnemar_two_sided_p_lt": 0.05,
        "paired_rescues_gt_paired_regressions": True,
    }
    assert "must not be promoted" in gates["claim_rule"]["safety_gate_failure_consequence"]
    assert all(gates["failure_governance"].values())


def test_short_storage_mapping_passes_windows_budget_without_creating_runs():
    p0, candidate = _plans()
    mapping = frozen.build_storage_mapping(p0, candidate)

    assert mapping["windows_path_budget_chars"] == 240
    assert mapping["requires_windows_long_path_registry_change"] is False
    assert mapping["run_directories_created_by_freezer"] is False
    assert all(run["within_budget"] for run in mapping["runs"])
    assert max(run["longest_windows_path_length"] for run in mapping["runs"]) < 240
    assert mapping["paired_analysis"]["within_budget"] is True
    assert not (REPO_ROOT / frozen.P0_PHYSICAL).exists()
    assert not (REPO_ROOT / frozen.CA_PHYSICAL).exists()
    assert not (REPO_ROOT / frozen.PAIRED_PHYSICAL).exists()


def test_driver_read_only_preflight_and_cli_have_no_retry_flags(monkeypatch):
    called = False

    def forbidden(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("model call forbidden")

    monkeypatch.setattr(driver, "fetch_ollama_provenance", forbidden)
    result = driver.preflight()
    assert result["status"] == "preflight_ok_no_model_call"
    assert result["p0_cells"] == result["candidate_a_cells"] == 200
    assert called is False

    parser = driver.build_parser()
    generation = parser.parse_args(
        [
            "generate",
            "--treatment",
            "p0",
            "--run-id",
            frozen.P0_RUN_ID,
            "--timeout-seconds",
            "600",
        ]
    )
    assert generation.timeout_seconds == 600.0
    for name in ("retry", "resume", "selective_retry", "overwrite", "healer"):
        assert not hasattr(generation, name)


def test_wrong_timeout_stops_before_model_call_or_run_directory(monkeypatch):
    called = False

    def forbidden(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("model call forbidden")

    monkeypatch.setattr(driver, "fetch_ollama_provenance", forbidden)
    with pytest.raises(driver.ExpansionRunError, match="600"):
        driver.generate(
            treatment="p0",
            run_id=frozen.P0_RUN_ID,
            base_url="http://127.0.0.1:1",
            timeout_seconds=300.0,
        )
    assert called is False
    assert not (REPO_ROOT / frozen.P0_PHYSICAL).exists()


def test_paired_analysis_plan_and_driver_cli_are_prospective():
    p0, candidate = _plans()
    plan = frozen.build_paired_analysis_plan(p0, candidate)

    assert plan["paired_identities"] == 200
    assert plan["planned_generation_cells_total"] == 400
    assert plan["pairing_key"] == ["task_id", "seed"]
    assert plan["all_regression_rows_required"] is True
    assert plan["reasoning_leakage_separate_metric"] is True
    assert plan["unknown_evaluator_failure_must_not_be_guessed"] is True
    args = analyzer.build_parser().parse_args(
        [
            "--p0-run-id",
            frozen.P0_RUN_ID,
            "--candidate-run-id",
            frozen.CA_RUN_ID,
        ]
    )
    assert args.p0_run_id == frozen.P0_RUN_ID
    assert args.candidate_run_id == frozen.CA_RUN_ID


def test_outputs_are_byte_deterministic_and_manifest_hashes_match():
    first = frozen.frozen_outputs(REPO_ROOT)
    second = frozen.frozen_outputs(REPO_ROOT)

    assert first == second
    assert len(first) == 7
    for relative, expected in first.items():
        assert (OUTPUT_DIR / relative).read_bytes() == expected
    manifest = json.loads(first[Path("milestone_2e_manifest.json")])
    assert manifest["counts"] == {
        "candidate_a_cells": 200,
        "expansion_tasks": 40,
        "p0_cells": 200,
        "paired_identities": 200,
        "seeds_per_task": 5,
        "total_planned_cells": 400,
    }
    assert manifest["candidate_a"]["official_v1"] is False
    assert manifest["zero_overlap"]["verified_total_forbidden_overlap"] == 0
    assert manifest["zero_overlap"]["discovery_development"] == 0
    assert manifest["prohibited_actions_attestation"] == {
        "candidate_a_promoted_to_official_v1": False,
        "evalplus_executions": 0,
        "formal_commands_executed": False,
        "healer_built": False,
        "model_calls": 0,
        "run_directories_created": False,
    }
    for name, metadata in manifest["outputs"].items():
        content = first[Path(name)]
        assert hashlib.sha256(content).hexdigest() == metadata["sha256"]
        assert len(content) == metadata["size_bytes"]


def test_operator_guide_separates_windows_wsl_and_paired_commands():
    guide = (OUTPUT_DIR / "operator_guide_zh.md").read_text(encoding="utf-8")

    assert "Windows 生成指令（未執行）" in guide
    assert "WSL EvalPlus 評估指令（未執行）" in guide
    assert "Paired analysis 指令（未執行）" in guide
    assert guide.count("run_mbpp_candidate_a_expansion.py generate") == 2
    assert guide.count("run_mbpp_candidate_a_expansion.py evaluate") == 2
    assert guide.count("analyze_mbpp_candidate_a_expansion.py") == 1
    assert frozen.P0_RUN_ID in guide and frozen.CA_RUN_ID in guide
    assert "不是正式 Scaffold v1" in guide
    assert "不得執行" in guide
