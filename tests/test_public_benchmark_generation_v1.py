"""Targeted unit tests for model-parameterized public benchmark generation runner."""

from __future__ import annotations

import pathlib
import pytest

from scripts import run_public_benchmark_generation_v1 as gen_runner

REPO = pathlib.Path(__file__).resolve().parents[1]


def test_zero_model_generation_preflight() -> None:
    preflight = gen_runner.zero_model_preflight(
        model="qwen3.5:4b", dataset="all", repo_root=REPO
    )
    assert preflight["status"] == "zero_model_generation_preflight_passed"
    assert preflight["model_calls"] == 0
    assert preflight["total_tasks"] == 542
    assert preflight["humaneval_tasks"] == 164
    assert preflight["mbpp_tasks"] == 378


def test_generation_dry_run_four_groups_breakdown() -> None:
    res = gen_runner.run_dry_run(
        model="qwen3.5:4b", dataset="all", treatment="all", repo_root=REPO
    )
    assert res["status"] == "generation_dry_run_completed"
    assert res["model_calls"] == 0

    prov = res["provenance_audit"]
    assert prov["readiness_status"] == "NOT_READY"

    breakdown = prov["four_groups_breakdown"]
    assert "4B_HumanEval" in breakdown
    assert "4B_MBPP" in breakdown
    assert "9B_HumanEval" in breakdown
    assert "9B_MBPP" in breakdown

    assert breakdown["4B_HumanEval"]["required_raw"] == 328
    assert breakdown["4B_HumanEval"]["exact_reusable"] == 0
    assert breakdown["4B_HumanEval"]["remaining_to_generate"] == 328

    assert breakdown["4B_MBPP"]["required_raw"] == 756
    assert breakdown["4B_MBPP"]["exact_reusable"] == 0
    assert breakdown["4B_MBPP"]["incompatible_existing"] == 40
    assert breakdown["4B_MBPP"]["remaining_to_generate"] == 756

    assert breakdown["9B_HumanEval"]["required_raw"] == 328
    assert breakdown["9B_HumanEval"]["exact_reusable"] == 0
    assert breakdown["9B_HumanEval"]["remaining_to_generate"] == 328

    assert breakdown["9B_MBPP"]["required_raw"] == 756
    assert breakdown["9B_MBPP"]["exact_reusable"] == 0
    assert breakdown["9B_MBPP"]["incompatible_existing"] == 40
    assert breakdown["9B_MBPP"]["remaining_to_generate"] == 756


def test_validation20_incompatible_verdict() -> None:
    prov = gen_runner.audit_generation_provenance(
        model_tag="qwen3.5:4b", dataset_name="all", repo_root=REPO
    )
    v20 = prov["validation20_audit"]
    assert v20["status"] == "incompatible_existing_generation"
    assert v20["reusable_exact_match_count"] == 0
    assert v20["validation20_generation_count"] == 40


def test_composed_prompt_building() -> None:
    task_rec = {"task_id": "HumanEval/0", "prompt": "def solve(x):\n    pass\n"}
    p_ab1 = gen_runner.build_composed_prompt(task_rec, "ab1")
    p_ab2g = gen_runner.build_composed_prompt(task_rec, "ab2g")
    assert p_ab1 == "def solve(x):\n    pass\n"
    assert p_ab2g == "def solve(x):\n    pass\n"
