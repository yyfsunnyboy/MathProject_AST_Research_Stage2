from __future__ import annotations

from fractions import Fraction

import pytest

from agent_tools.finals_rebuild.math_evaluator import evaluate_math_code
from agent_tools.finals_rebuild.math_spec_rules import repair_rational_literal_division
from agent_tools.finals_rebuild.math_task_schema import MathOutputContract, parse_math_task


def contract(**changes):
    values = dict(answer_type="rational", representation_subtype=None,
        python_return_type="Fraction", representation_policy="exact_answer_type",
        validator_type="rational_exact", allowed_tolerance=None,
        symbolic_variables=(), answer_fields=())
    values.update(changes)
    return MathOutputContract(**values)


def task():
    return parse_math_task({"task_id":"rational-fixture", "source":"test", "source_year":2026,
        "source_exam":"test", "source_question_number":1, "domain":"number", "subdomain":"rational",
        "curriculum_level":"grade_7", "evidence_role":"development", "problem_text":"3/5",
        "entry_point":"solve", "input_contract":{"kind":"no_arguments"},
        "output_contract":{"answer_type":"rational", "representation_subtype":None,
            "python_return_type":"Fraction", "representation_policy":"exact_answer_type",
            "validator_type":"rational_exact", "allowed_tolerance":None, "symbolic_variables":[], "answer_fields":[]},
        "reference_semantic":Fraction(3,5), "reference_display":"3/5", "metadata":{"synthetic_fixture":True}})


@pytest.mark.parametrize("source, expected", [
    ("def solve():\n    return 3 / 5\n", "Fraction(3, 5)"),
    ("def solve():\n    return -3 / 5\n", "Fraction(-3, 5)"),
    ("def solve():\n    return 3 / -5\n", "Fraction(3, -5)"),
    ("def solve():\n    return -3 / -5\n", "Fraction(-3, -5)"),
])
def test_repairs_literal_integer_division(source, expected):
    result = repair_rational_literal_division(source, contract())
    assert result.triggered and result.changed and result.reason == "repaired"
    assert expected in result.code_after
    assert "from fractions import Fraction" in result.code_after
    assert result.before_hash != result.after_hash


def test_import_follows_docstring_and_future_imports():
    source = '"""doc"""\nfrom __future__ import annotations\nimport math\ndef solve():\n return 3 / 5\n'
    repaired = repair_rational_literal_division(source, contract()).code_after
    assert repaired.index('from __future__ import annotations') < repaired.index('from fractions import Fraction') < repaired.index('import math')


@pytest.mark.parametrize("source, reason", [
    ("def solve():\n return 0.6", "unsupported_expression"),
    ("def solve():\n return 3.0 / 5", "unsupported_expression"),
    ("def solve():\n return x / 5", "unsupported_expression"),
    ("def solve():\n return 1 / 0", "zero_denominator"),
    ("def solve():\n return True / 2", "unsupported_expression"),
    ("def solve():\n return (3 / 5) / 7", "unsupported_expression"),
    ("def solve():\n if True:\n  return 3 / 5\n return 4 / 7", "unsupported_return_structure"),
    ("def solve(x):\n return 3 / 5", "invalid_solve_signature"),
    ("async def solve():\n return 3 / 5", "invalid_solve_signature"),
    ("class A:\n def solve(self):\n  return 3 / 5", "solve_not_found"),
    ("def solve(:\n pass", "parse_error"),
    ("Fraction = object\ndef solve():\n return 3 / 5", "fraction_name_conflict"),
])
def test_forbidden_shapes_are_unchanged(source, reason):
    result = repair_rational_literal_division(source, contract())
    assert not result.triggered and not result.changed and result.reason == reason
    assert result.code_before == result.code_after
    assert result.before_hash == result.after_hash


def test_contract_gate_trace_determinism_and_idempotence():
    source = "def solve():\n return 3 / 5\n"
    not_applicable = repair_rational_literal_division(source, contract(representation_policy="semantic_only"))
    assert not_applicable.reason == "contract_not_applicable"
    first = repair_rational_literal_division(source, contract())
    assert first == repair_rational_literal_division(source, contract())
    second = repair_rational_literal_division(first.code_after, contract())
    assert second.reason == "already_compliant"
    assert not second.changed and second.before_hash == second.after_hash


def test_evaluator_representation_integration():
    source = "def solve():\n return 3 / 5\n"
    before = evaluate_math_code(task(), source)
    repaired = repair_rational_literal_division(source, contract())
    after = evaluate_math_code(task(), repaired.code_after)
    # The frozen validator treats a float as invalid before it can expose
    # semantic equivalence under an exact-Fraction contract.
    assert before.math_validation.is_correct is False
    assert before.math_validation.representation_compliance is False
    assert after.math_validation.is_correct is True
    assert after.overall_status == "pass"
