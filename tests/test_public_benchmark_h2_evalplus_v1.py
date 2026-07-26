"""Targeted unit tests for model-parameterized public benchmark H2 EvalPlus runner."""

from __future__ import annotations

import pathlib
import pytest

from scripts import run_public_benchmark_h2_evalplus_v1 as runner

REPO = pathlib.Path(__file__).resolve().parents[1]


def test_zero_eval_preflight_fail_closed() -> None:
    preflight = runner.zero_eval_preflight(model="qwen3.5:4b", dataset="all", repo_root=REPO)
    assert preflight["status"] == "zero_eval_preflight_passed"
    assert preflight["model_calls"] == 0
    assert preflight["evalplus_executed"] is False
    assert preflight["evalplus_version"] == "0.3.1"
    assert preflight["planned_eval_cells"] == 2168
    assert preflight["humaneval_eval_cells"] == 656
    assert preflight["mbpp_eval_cells"] == 1512

    with pytest.raises(runner.EvalPlusRunnerError):
        runner.zero_eval_preflight(model="invalid_model", dataset="all", repo_root=REPO)


def test_4b_evalplus_dry_run_ready() -> None:
    res = runner.run_dry_run(model="qwen3.5:4b", dataset="all", repo_root=REPO)
    assert res["status"] == "dry_run_completed"
    assert res["model_tag"] == "qwen3.5:4b"
    assert res["readiness_status"] == "READY"
    assert res["planned_eval_cells"] == 2168
    assert res["humaneval_eval_cells"] == 656
    assert res["mbpp_eval_cells"] == 1512
    assert res["present_replay_journals"] == 2168
    assert res["humaneval_present_journals"] == 656
    assert res["mbpp_present_journals"] == 1512
    assert res["missing_replay_journals"] == 0
    assert res["model_calls"] == 0
    assert res["evalplus_executed"] is False


def test_9b_evalplus_dry_run_not_ready() -> None:
    res = runner.run_dry_run(model="qwen3.5:9b", dataset="all", repo_root=REPO)
    assert res["status"] == "dry_run_completed"
    assert res["model_tag"] == "qwen3.5:9b"
    assert res["readiness_status"] == "NOT_READY"
    assert res["planned_eval_cells"] == 2168
    assert res["present_replay_journals"] == 0
    assert res["missing_replay_journals"] == 2168


def test_missing_replay_journals_fail_closed() -> None:
    with pytest.raises(runner.EvalPlusRunnerError):
        runner.run_evalplus_execution(model="qwen3.5:9b", dataset="all", repo_root=REPO)
