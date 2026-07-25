from __future__ import annotations

import hashlib
from pathlib import Path

from agent_tools.finals_rebuild import mbpp_h1_h2_cumulative_pipeline as pipeline
from scripts import run_mbpp_h1_h2_cumulative_pipeline_v1 as runner


ROOT = Path(__file__).resolve().parents[1]


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_h1_only_transform() -> None:
    source = "def helper(x):\n    return x + 1\n"
    result = pipeline.run_h1_then_h2(
        normalized_source=source,
        entry_point="solve",
        expected_positional_arities=(1,),
        generation_truncated=False,
        extraction_unambiguous=True,
        source_complete=True,
    )
    assert result.h1.changed is True
    assert result.h2.changed is False
    assert result.transform_class == "H1_ONLY"
    assert "solve = helper" in (result.final_source or "")
    assert result.h1.rule_id == "entrypoint_alias_unique_arity_compatible_v0"
    assert result.h1.diff


def test_h2_only_transform() -> None:
    source = "def solve(x):\n    return x + 1\n\nassert solve(1) == 2\n"
    result = pipeline.run_h1_then_h2(
        normalized_source=source,
        entry_point="solve",
        expected_positional_arities=(1,),
        generation_truncated=False,
        extraction_unambiguous=True,
        source_complete=True,
    )
    assert result.h1.changed is False
    assert result.h2.changed is True
    assert result.transform_class == "H2_ONLY"
    assert result.h2.rule_id == "module_assert_entrypoint_selftest_quarantine_v0"
    assert "if __name__" in (result.final_source or "")


def test_h1_then_triggers_h2() -> None:
    """After H1 stage, H2 must run on H1 output; here H1 is no-op and H2 transforms."""
    source = "def solve(x):\n    return x + 1\n\nassert solve(1) == 2\n"
    result = pipeline.run_h1_then_h2(
        normalized_source=source,
        entry_point="solve",
        expected_positional_arities=(1,),
        generation_truncated=False,
        extraction_unambiguous=True,
        source_complete=True,
    )
    assert result.h1.changed is False
    assert result.h2.input_source == result.h1.output_source
    assert result.h2.changed is True
    assert result.transform_class == "H2_ONLY"
    assert "if __name__" in (result.final_source or "")


def test_transform_class_h1_and_h2_label_exists() -> None:
    assert pipeline.classify_transform(h1_changed=True, h2_changed=True) == "H1_AND_H2"


def test_both_abstain() -> None:
    source = "def solve(x):\n    return x\n\nassert solve(1) == 1\nassert solve(2) == 2\n"
    result = pipeline.run_h1_then_h2(
        normalized_source=source,
        entry_point="solve",
        expected_positional_arities=(1,),
        generation_truncated=False,
        extraction_unambiguous=True,
        source_complete=True,
    )
    assert result.h1.changed is False
    assert result.h2.changed is False
    assert result.h2.abstained is True
    assert result.transform_class == "UNCHANGED"
    assert result.final_source == source
    assert result.final_sha256 == _sha(source)


def test_ambiguous_entry_refuses_repair() -> None:
    source = (
        "def a(x):\n    return x\n\n"
        "def b(x):\n    return x\n"
    )
    result = pipeline.run_h1_then_h2(
        normalized_source=source,
        entry_point="solve",
        expected_positional_arities=(1,),
        generation_truncated=False,
        extraction_unambiguous=True,
        source_complete=True,
    )
    assert result.h1.changed is False
    assert result.h1.abstained is True
    assert result.h1.reason == "top_level_function_count_not_one"
    assert result.transform_class == "UNCHANGED"


def test_correct_program_does_not_regress() -> None:
    source = "def solve(x):\n    return x\n"
    first = pipeline.run_h1_then_h2(
        normalized_source=source,
        entry_point="solve",
        expected_positional_arities=(1,),
        generation_truncated=False,
        extraction_unambiguous=True,
        source_complete=True,
    )
    second = pipeline.run_h1_then_h2(
        normalized_source=source,
        entry_point="solve",
        expected_positional_arities=(1,),
        generation_truncated=False,
        extraction_unambiguous=True,
        source_complete=True,
    )
    assert first.transform_class == "UNCHANGED"
    assert first.final_source == source
    assert first.final_sha256 == second.final_sha256 == _sha(source)
    assert first.h1.reason == "expected_entry_point_present"


def test_replay_hash_idempotent() -> None:
    source = "def helper(x):\n    return x\n\nassert solve(0) == 0\n"
    first = pipeline.run_h1_then_h2(
        normalized_source=source,
        entry_point="solve",
        expected_positional_arities=(1,),
        generation_truncated=False,
        extraction_unambiguous=True,
        source_complete=True,
    )
    second = pipeline.run_h1_then_h2(
        normalized_source=source,
        entry_point="solve",
        expected_positional_arities=(1,),
        generation_truncated=False,
        extraction_unambiguous=True,
        source_complete=True,
    )
    assert first.to_dict(include_sources=True) == second.to_dict(include_sources=True)
    # Re-applying on final output should be stable for H2 idempotence.
    third = pipeline.run_h1_then_h2(
        normalized_source=first.final_source,
        entry_point="solve",
        expected_positional_arities=(1,),
        generation_truncated=False,
        extraction_unambiguous=True,
        source_complete=True,
    )
    assert third.final_sha256 == first.final_sha256


def test_h2_receives_h1_output_bytes() -> None:
    source = "def helper(x):\n    return 1\n"
    result = pipeline.run_h1_then_h2(
        normalized_source=source,
        entry_point="solve",
        expected_positional_arities=(1,),
        generation_truncated=False,
        extraction_unambiguous=True,
        source_complete=True,
    )
    assert result.h2.input_sha256 == result.h1.output_sha256
    assert result.h2.input_source == result.h1.output_source


def test_evalplus_hook_refuses_execution() -> None:
    import pytest

    with pytest.raises(RuntimeError, match="refuses live EvalPlus"):
        pipeline.evalplus_stage_hook(final_source="def solve():\n    return 0\n", execute=True)


def test_development_validation_preserves_h1_rescue_and_h2_counts() -> None:
    report = runner.validate_all(ROOT)
    assert report["model_calls"] == 0
    assert report["evalplus_executed"] is False
    assert report["existing600_h1_rescue_check"]["verified_rescue_count"] == 9
    assert report["h2_ninety_one_check"]["transformed"] == 71
    assert report["h2_ninety_one_check"]["unchanged"] == 20
    assert report["h2_ninety_one_check"]["partial_repair"] == 46
    assert report["h2_ninety_one_check"]["verified_rescue"] == 0
    assert report["differences_vs_prior"]["h1_verified_rescue_preserved"] is True
    assert report["differences_vs_prior"]["h2_transformed_unchanged_preserved"] is True
    assert report["differences_vs_prior"]["h2_partial_repair_not_relabeled_rescue"] is True
    classes = report["existing600_cumulative"]["transform_classes"]
    assert set(classes) == set(pipeline.TRANSFORM_CLASSES)
    assert sum(classes.values()) == 600
    assert report["existing600_cumulative"]["frozen_verified_rescue"] == 9
    assert report["existing600_cumulative"]["frozen_regression"] == 0
