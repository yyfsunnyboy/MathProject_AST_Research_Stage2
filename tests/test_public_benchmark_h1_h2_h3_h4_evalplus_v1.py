"""Targeted tests for the public benchmark cumulative H1->H2->H3->H4 EvalPlus
runner (development-candidate evidence). Covers transition-category
classification (all 7 buckets, schema-limited fields marked unavailable
rather than guessed), preflight/dry-run wiring, output isolation, and a
small zero-model-call end-to-end replay->evalplus smoke test.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from scripts import run_public_benchmark_h1_h2_h3_h4_evalplus_v1 as ev_runner
from scripts import run_public_benchmark_h1_h2_h3_h4_replay_v1 as replay_runner

REPO = pathlib.Path(__file__).resolve().parents[1]


def test_output_directory_isolation_rejects_h2_only_paths() -> None:
    with pytest.raises(ev_runner.CumulativeEvalPlusError, match="collides"):
        ev_runner.zero_eval_preflight(
            model="qwen3.5:4b",
            dataset="humaneval",
            output_dir_arg="artifacts/public_benchmark_governance/qwen35_4b_h2_full_evalplus_v1",
            repo_root=REPO,
        )


def test_dry_run_not_ready_when_no_cumulative_replay_journals(tmp_path: pathlib.Path) -> None:
    res = ev_runner.run_dry_run(
        model="qwen3.5:9b",
        dataset="all",
        output_dir_arg=str(tmp_path / "out"),
        repo_root=REPO,
    )
    assert res["model_calls"] == 0
    assert res["evalplus_executed"] is False
    assert res["planned_pairs"] == 1084
    assert res["planned_executions"] == 2168


@pytest.mark.parametrize(
    "modified,raw_base,raw_plus,raw_final,cum_base,cum_plus,cum_final,any_abstained,expected",
    [
        (True, False, False, False, True, True, True, False, "verified_rescue"),
        (True, True, True, True, False, False, False, False, "regression"),
        (False, True, True, True, True, True, True, False, "preserved_pass"),
        (False, False, False, False, False, False, False, False, "unchanged_failure"),
        (True, False, False, False, False, False, False, False, "modified_but_still_failed"),
        (True, False, False, False, True, False, False, False, "blocker_removed_but_incorrect"),
        (False, False, False, False, False, False, False, True, "abstained_unchanged"),
    ],
)
def test_classify_transition_all_seven_categories(
    modified, raw_base, raw_plus, raw_final, cum_base, cum_plus, cum_final, any_abstained, expected
) -> None:
    result = ev_runner.classify_transition(
        modified=modified,
        raw_base_pass=raw_base,
        raw_plus_pass=raw_plus,
        raw_final_pass=raw_final,
        cumulative_base_pass=cum_base,
        cumulative_plus_pass=cum_plus,
        cumulative_final_pass=cum_final,
        any_layer_abstained=any_abstained,
    )
    assert result == expected
    assert result in ev_runner.TRANSITION_CATEGORIES


def test_replay_then_evalplus_humaneval_smoke_4b(tmp_path: pathlib.Path) -> None:
    replay_dir = tmp_path / "replay"
    eval_dir = tmp_path / "eval"

    replay_res = replay_runner.run_replay_execution(
        model="qwen3.5:4b",
        dataset="humaneval",
        resume=True,
        output_dir_arg=str(replay_dir),
        repo_root=REPO,
    )
    assert replay_res["executed_cells"] == 328

    # Point the EvalPlus runner at the just-produced replay directory by
    # monkeypatching only the replay_dir lookup for this one call.
    original_spec = ev_runner.MODEL_SPECS["qwen3.5:4b"]["replay_dir"]
    ev_runner.MODEL_SPECS["qwen3.5:4b"]["replay_dir"] = replay_dir
    try:
        dry = ev_runner.run_dry_run(
            model="qwen3.5:4b",
            dataset="humaneval",
            output_dir_arg=str(eval_dir),
            repo_root=REPO,
        )
        assert dry["readiness_status"] == "READY"
        assert dry["present_replay_pairs"] == 328

        res = ev_runner.run_evalplus_execution(
            model="qwen3.5:4b",
            dataset="humaneval",
            resume=True,
            output_dir_arg=str(eval_dir),
            repo_root=REPO,
        )
    finally:
        ev_runner.MODEL_SPECS["qwen3.5:4b"]["replay_dir"] = original_spec

    assert res["status"] == "cumulative_evalplus_execution_completed"
    assert res["model_calls"] == 0
    assert res["duplicate"] == 0
    assert res["missing"] == 0
    assert res["total_pairs"] == 328
    assert res["executed_pairs"] == 328

    journals = list((eval_dir / "j").glob("*.json"))
    assert len(journals) == 328
    sample = json.loads(journals[0].read_text(encoding="utf-8"))
    for field in (
        "raw_base_pass", "raw_plus_pass", "raw_final_pass",
        "cumulative_base_pass", "cumulative_plus_pass", "cumulative_final_pass",
        "transition_category", "raw_execution_status", "cumulative_execution_status",
    ):
        assert field in sample
    assert sample["raw_execution_status"] == "unavailable"
    assert sample["cumulative_execution_status"] == "unavailable"
    assert sample["transition_category"] in ev_runner.TRANSITION_CATEGORIES
