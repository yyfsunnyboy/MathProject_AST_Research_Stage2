from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from agent_tools.finals_rebuild.generator_evaluator import evaluate_generator_code


def test_valid_generator_and_stdout_and_tuple_normalisation():
    result = evaluate_generator_code("def generate():\n print('debug')\n return {'question_text':'q', 'correct_answer':(1,2)}")
    assert result.success and result.status == "passed"
    assert result.stdout == "debug\n"
    assert result.returned_instance["correct_answer"] == [1, 2]
    with pytest.raises(FrozenInstanceError): result.status = "failed"


def test_level_keyword_and_positional_are_supported():
    keyword = evaluate_generator_code("def generate(level=1, **kwargs):\n return {'question_text':'q', 'correct_answer':level}", level=4)
    positional = evaluate_generator_code("def generate(value):\n return {'question_text':'q', 'correct_answer':value}", level=5)
    assert keyword.returned_instance["correct_answer"] == 4
    assert positional.returned_instance["correct_answer"] == 5


@pytest.mark.parametrize("code, stage, error", [
    ("def generate(:\n pass", "parse", "SyntaxError"),
    ("x=1", "entry_point", "GenerateEntryPointMissing"),
    ("generate=1", "entry_point", "GenerateEntryPointNotCallable"),
    ("def generate(a,b):\n pass", "entry_point", "UnsupportedGenerateSignature"),
    ("def generate():\n raise RuntimeError('boom')", "execution", "RuntimeError"),
    ("def generate():\n return []", "output", "GeneratorOutputNotDict"),
    ("def generate():\n return {'correct_answer':2}", "instance_schema", "QuestionTextMissing"),
    ("def generate():\n return {'question_text':' ', 'correct_answer':2}", "instance_schema", "QuestionTextInvalid"),
    ("def generate():\n return {'question_text':'q'}", "instance_schema", "CorrectAnswerMissing"),
    ("def generate():\n return {'question_text':'q', 'correct_answer':None}", "instance_schema", "CorrectAnswerInvalid"),
    ("def generate():\n return {'question_text':'q', 'correct_answer':{1,2}}", "output", "UnsafeReturnType"),
])
def test_failure_classification(code, stage, error):
    result = evaluate_generator_code(code)
    assert not result.success and result.failure_stage == stage and result.error_type == error


@pytest.mark.parametrize("code", [
    "import os\ndef generate(): return {}", "from subprocess import run\ndef generate(): return {}",
    "def generate():\n open('x','w')", "def generate():\n return eval('1+1')",
    "def generate():\n return __import__('os')", "async def generate():\n return {}",
])
def test_unsafe_code_is_rejected_before_subprocess(code):
    result = evaluate_generator_code(code)
    assert result.status == "rejected" and result.safety_status == "rejected"
    assert result.returned_instance is None


def test_timeout_and_invalid_input():
    timeout = evaluate_generator_code("def generate():\n while True: pass", timeout_seconds=.1)
    invalid = evaluate_generator_code(3)  # type: ignore[arg-type]
    assert timeout.status == "timeout" and timeout.error_type == "TimeoutExpired"
    assert invalid.error_type == "InvalidEvaluatorInput"
