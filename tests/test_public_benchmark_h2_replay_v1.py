"""Targeted unit tests for model-parameterized public benchmark H2 replay runner (no live model/EvalPlus)."""

from __future__ import annotations

import pathlib
import pytest

from scripts import run_public_benchmark_h2_replay_v1 as runner

REPO = pathlib.Path(__file__).resolve().parents[1]


def test_roster_validation_humaneval_and_mbpp() -> None:
    roster = runner.validate_roster("all", repo_root=REPO)
    assert roster["status"] == "roster_validation_passed"
    assert roster["humaneval_tasks"] == 164
    assert roster["mbpp_tasks"] == 378
    assert roster["total_tasks"] == 542
    assert roster["unique_task_ids"] == 542


def test_zero_model_preflight_fail_closed() -> None:
    preflight = runner.zero_model_preflight(model="qwen3.5:4b", dataset="all", repo_root=REPO)
    assert preflight["status"] == "zero_model_preflight_passed"
    assert preflight["model_calls"] == 0
    assert preflight["rule_hash"] == runner.EXPECTED_RULE_SHA256

    with pytest.raises(runner.BenchmarkRunnerError):
        runner.zero_model_preflight(model="invalid_model", dataset="all", repo_root=REPO)


def test_4b_dry_run_audit_statistics() -> None:
    res = runner.run_dry_run(model="qwen3.5:4b", dataset="all", repo_root=REPO)
    assert res["status"] == "dry_run_completed"
    assert res["model_calls"] == 0
    assert res["evalplus_executed"] is False

    inv = res["inventory"]
    assert inv["model_tag"] == "qwen3.5:4b"
    assert inv["total_tasks"] == 542
    assert inv["humaneval_tasks"] == 164
    assert inv["mbpp_tasks"] == 378
    assert inv["conditions_count"] == 4
    assert inv["total_planned_itt_states"] == 2168
    assert inv["readiness_status"] == "NOT_READY"
    assert inv["breakdown"]["humaneval"]["missing_raw"] == 328
    assert inv["breakdown"]["mbpp"]["missing_raw"] == 716


def test_9b_dry_run_audit_statistics() -> None:
    res = runner.run_dry_run(model="qwen3.5:9b", dataset="all", repo_root=REPO)
    assert res["status"] == "dry_run_completed"
    assert res["model_calls"] == 0
    assert res["evalplus_executed"] is False

    inv = res["inventory"]
    assert inv["model_tag"] == "qwen3.5:9b"
    assert inv["total_tasks"] == 542
    assert inv["humaneval_tasks"] == 164
    assert inv["mbpp_tasks"] == 378
    assert inv["conditions_count"] == 4
    assert inv["total_planned_itt_states"] == 2168
    assert inv["readiness_status"] == "NOT_READY"
    assert inv["breakdown"]["humaneval"]["missing_raw"] == 328
    assert inv["breakdown"]["mbpp"]["missing_raw"] == 716


def test_extractor_and_h2_quarantine_deterministic() -> None:
    raw_code = "```python\ndef solve(x):\n    return x + 1\n\nassert solve(1) == 2\n```"
    ext = runner.extract_code(raw_code)
    assert ext.extraction_status == "extracted"
    assert ext.extracted_code is not None

    h2_res = runner.quarantine_module_assert_entrypoint_selftest(
        ext.extracted_code, "solve", extraction_unambiguous=True, source_complete=True
    )
    assert h2_res.triggered is True
    assert 'if __name__ == "__main__":' in h2_res.output_source
