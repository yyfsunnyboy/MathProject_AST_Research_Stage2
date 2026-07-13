from __future__ import annotations

from fractions import Fraction

from agent_tools.finals_rebuild.math_evaluator import (
    evaluate_math_code,
    evaluate_math_raw_response,
)
from agent_tools.finals_rebuild.math_task_schema import parse_math_task


def task(answer_type="number", return_type="int", reference=4):
    return parse_math_task({
        "task_id": "fixture", "source": "test", "source_year": 2026,
        "source_exam": "test", "source_question_number": 1, "domain": "number",
        "subdomain": "integer", "curriculum_level": "grade_7",
        "evidence_role": "development", "problem_text": "2 + 2", "entry_point": "solve",
        "input_contract": {"kind": "no_arguments"}, "reference_semantic": reference,
        "reference_display": str(reference), "metadata": {"synthetic_fixture": True},
        "output_contract": {"answer_type": answer_type, "representation_subtype": None,
          "python_return_type": return_type, "representation_policy": "exact_answer_type",
          "validator_type": "test", "allowed_tolerance": None, "symbolic_variables": [],
          "answer_fields": []},
    })


def test_happy_path_and_raw_python_fence():
    result = evaluate_math_raw_response(task(), "text\n```python\ndef solve():\n return 4\n```")
    assert result.overall_status == "pass"
    assert result.extraction_status == "success"
    assert result.returned_value == 4


def test_parse_entry_point_and_signature_failures():
    assert evaluate_math_code(task(), "def solve(:\n pass").failure_stage == "parse"
    assert evaluate_math_code(task(), "def other():\n return 4").failure_stage == "entry_point"
    result = evaluate_math_code(task(), "def solve(x):\n return x")
    assert result.error_code == "invalid_entry_point_signature"


def test_timeout_security_and_output_failures():
    assert evaluate_math_code(task(), "def solve():\n while True: pass", timeout_seconds=.1).execution_status == "timeout"
    assert evaluate_math_code(task(), "import os\ndef solve(): return 4").error_code == "forbidden_operation"
    result = evaluate_math_code(task(), "def solve():\n print('x')\n return 4")
    assert result.error_code == "unexpected_stdout"


def test_fraction_tuple_and_wrong_math():
    rational = task("rational", "Fraction", Fraction(1, 2))
    result = evaluate_math_code(rational, "from fractions import Fraction\ndef solve(): return Fraction(1, 2)")
    assert result.overall_status == "pass"
    assert evaluate_math_code(task(), "def solve(): return 3").failure_stage == "math_validation"


def test_extraction_failure_does_not_parse_or_run():
    result = evaluate_math_raw_response(task(), "```python\ndef solve(): return 4\n```\n```python\ndef solve(): return 4\n```")
    assert result.extraction_status == "ambiguous"
    assert result.parse_status == "not_run"
    assert result.execution_status == "not_run"
