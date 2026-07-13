from __future__ import annotations

from dataclasses import FrozenInstanceError
from fractions import Fraction

import pytest

from agent_tools.finals_rebuild.math_dev_replay import (
    MathDevReplayCase,
    replay_math_dev_case,
    replay_math_dev_cases,
)
from agent_tools.finals_rebuild.math_spec_rules import RATIONAL_LITERAL_DIVISION_RULE_ID
from agent_tools.finals_rebuild.math_task_schema import parse_math_task


def _task(reference=Fraction(3, 5)):
    return parse_math_task({
        "task_id": "replay-rational", "source": "synthetic", "source_year": 2026,
        "source_exam": "test", "source_question_number": 1, "domain": "number",
        "subdomain": "rational", "curriculum_level": "grade_7",
        "evidence_role": "development", "problem_text": "3 / 5", "entry_point": "solve",
        "input_contract": {"kind": "no_arguments"}, "reference_semantic": reference,
        "reference_display": "3/5", "metadata": {"synthetic_fixture": True},
        "output_contract": {"answer_type": "rational", "representation_subtype": None,
            "python_return_type": "Fraction", "representation_policy": "exact_answer_type",
            "validator_type": "rational_exact", "allowed_tolerance": None,
            "symbolic_variables": [], "answer_fields": []},
    })


def _case(case_id, code, *, enabled=(RATIONAL_LITERAL_DIVISION_RULE_ID,), task=None):
    return MathDevReplayCase(case_id, task or _task(), code, tuple(enabled))


def test_replay_repairs_rational_literal_representation():
    result = replay_math_dev_case(_case("repair", "def solve():\n return 3 / 5\n"))
    assert result.before_evaluation.overall_status == "fail"
    assert result.after_evaluation.overall_status == "pass"
    assert result.changed and result.repaired and result.failure_reason is None
    assert "Fraction(3, 5)" in result.code_after


def test_replay_preserves_code_when_rule_not_enabled():
    result = replay_math_dev_case(_case("disabled", "def solve():\n return 3 / 5\n", enabled=()))
    assert result.code_after == result.code_before
    assert not result.repaired
    assert result.failure_reason == "adapter_no_change"


def test_replay_records_unsupported_expression_without_repair():
    source = "def get_value():\n return 3\ndef solve():\n return get_value() / 5\n"
    result = replay_math_dev_case(_case("unsupported", source))
    step = next(s for s in result.adapter_trace.steps if s.rule_id == RATIONAL_LITERAL_DIVISION_RULE_ID)
    assert not result.changed and not result.repaired
    assert result.failure_reason == "adapter_no_change"
    assert step.reason == "unsupported_expression"


def test_replay_marks_already_passing_case():
    source = "from fractions import Fraction\ndef solve():\n return Fraction(3, 5)\n"
    result = replay_math_dev_case(_case("passing", source))
    assert result.before_evaluation.overall_status == "pass"
    assert result.after_evaluation.overall_status == "pass"
    assert not result.changed and not result.repaired
    assert result.failure_reason == "before_already_passed"


def test_replay_does_not_claim_semantic_rescue():
    result = replay_math_dev_case(_case("wrong", "def solve():\n return 4 / 5\n"))
    assert result.changed
    assert result.before_evaluation.overall_status == "fail"
    assert result.after_evaluation.overall_status == "fail"
    assert not result.repaired
    assert result.failure_reason == "after_still_failed"


def test_replay_cases_preserves_order_and_accepts_empty_sequence():
    cases = (_case("first", "def solve():\n return 3 / 5\n"), _case("second", "def solve():\n return 3 / 5\n", enabled=()))
    assert tuple(result.case_id for result in replay_math_dev_cases(cases)) == ("first", "second")
    assert replay_math_dev_cases(()) == ()


def test_case_and_result_are_deterministic_and_case_is_frozen():
    case = _case("deterministic", "def solve():\n return 3 / 5\n")
    assert replay_math_dev_case(case) == replay_math_dev_case(case)
    with pytest.raises(FrozenInstanceError):
        case.code = "changed"
