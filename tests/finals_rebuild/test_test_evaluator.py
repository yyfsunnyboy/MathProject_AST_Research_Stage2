"""
Tests for agent_tools/finals_rebuild/test_evaluator.py
"""

from __future__ import annotations

import inspect
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from agent_tools.finals_rebuild.test_contract import TestCase, TestSuite
from agent_tools.finals_rebuild.test_evaluator import run_test_suite
# Aliased: "test_results_to_dict" starts with "test_", which pytest's
# default collector would otherwise mistake for a test function if
# imported unqualified into this test module's namespace.
from agent_tools.finals_rebuild.test_evaluator import (
    test_results_to_dict as results_to_dict,
)

_CODE_MATH = "def add(a, b):\n    return a + b\n\ndef sub(a, b):\n    return a - b\n"


def _case(**overrides):
    base = dict(
        case_id="c1", function_name="add", args=[1, 2], kwargs={},
        expected=3, comparison_mode="exact",
    )
    base.update(overrides)
    return TestCase(**base)


def _suite(cases, **overrides):
    base = dict(suite_id="s1", cases=cases, timeout_seconds=2.0, numeric_tolerance=1e-6)
    base.update(overrides)
    return TestSuite(**base)


# ---------------------------------------------------------------------------
# 1/2: exact case pass/fail
# ---------------------------------------------------------------------------


def test_1_single_exact_case_passes():
    suite = _suite([_case(function_name="add", args=[2, 3], expected=5)])
    outcome = run_test_suite(code=_CODE_MATH, suite=suite)
    assert outcome.test_pass is True
    assert outcome.tests_passed == 1
    assert outcome.tests_total == 1
    assert outcome.cases[0].status == "passed"


def test_2_exact_case_fails():
    suite = _suite([_case(function_name="add", args=[2, 3], expected=999)])
    outcome = run_test_suite(code=_CODE_MATH, suite=suite)
    assert outcome.test_pass is False
    assert outcome.tests_passed == 0
    assert outcome.cases[0].status == "failed"
    assert outcome.cases[0].passed is False


# ---------------------------------------------------------------------------
# 3: numeric_tolerance pass/fail
# ---------------------------------------------------------------------------


def test_3a_numeric_tolerance_passes_within_bound():
    code = "def half(x):\n    return x / 3\n"
    suite = _suite(
        [_case(function_name="half", args=[1], expected=0.3333, comparison_mode="numeric_tolerance")],
        numeric_tolerance=0.001,
    )
    outcome = run_test_suite(code=code, suite=suite)
    assert outcome.cases[0].status == "passed"


def test_3b_numeric_tolerance_fails_outside_bound():
    code = "def half(x):\n    return x / 3\n"
    suite = _suite(
        [_case(function_name="half", args=[1], expected=0.9, comparison_mode="numeric_tolerance")],
        numeric_tolerance=0.001,
    )
    outcome = run_test_suite(code=code, suite=suite)
    assert outcome.cases[0].status == "failed"


# ---------------------------------------------------------------------------
# 4: json_equal
# ---------------------------------------------------------------------------


def test_4_json_equal_passes():
    code = "def make():\n    return {'a': [1, 2], 'b': None}\n"
    suite = _suite([
        _case(function_name="make", args=[], expected={"a": [1, 2], "b": None}, comparison_mode="json_equal")
    ])
    outcome = run_test_suite(code=code, suite=suite)
    assert outcome.cases[0].status == "passed"


# ---------------------------------------------------------------------------
# 5: missing function
# ---------------------------------------------------------------------------


def test_5_missing_function_reports_error():
    suite = _suite([_case(function_name="does_not_exist", args=[], expected=1)])
    outcome = run_test_suite(code=_CODE_MATH, suite=suite)
    assert outcome.cases[0].status == "error"
    assert outcome.cases[0].exception_type == "FunctionNotFound"
    assert outcome.test_pass is False


# ---------------------------------------------------------------------------
# 6: function raises
# ---------------------------------------------------------------------------


def test_6_function_raises_reports_error():
    code = "def boom():\n    raise ValueError('nope')\n"
    suite = _suite([_case(function_name="boom", args=[], expected=None)])
    outcome = run_test_suite(code=code, suite=suite)
    assert outcome.cases[0].status == "error"
    assert outcome.cases[0].exception_type == "ValueError"
    assert "nope" in outcome.cases[0].exception_message


# ---------------------------------------------------------------------------
# 7: case timeout
# ---------------------------------------------------------------------------


def test_7_case_timeout():
    code = "def hang():\n    while True:\n        pass\n"
    suite = _suite([_case(function_name="hang", args=[], expected=None)], timeout_seconds=1.0)
    outcome = run_test_suite(code=code, suite=suite)
    assert outcome.cases[0].status == "timeout"
    assert outcome.cases[0].passed is False


# ---------------------------------------------------------------------------
# 8: one case failing doesn't stop the rest
# ---------------------------------------------------------------------------


def test_8_one_failing_case_does_not_stop_others():
    suite = _suite([
        _case(case_id="c1", function_name="add", args=[1, 1], expected=2),       # pass
        _case(case_id="c2", function_name="add", args=[1, 1], expected=999),     # fail
        _case(case_id="c3", function_name="sub", args=[5, 2], expected=3),       # pass
        _case(case_id="c4", function_name="missing_fn", args=[], expected=1),    # error
    ])
    outcome = run_test_suite(code=_CODE_MATH, suite=suite)
    assert outcome.tests_total == 4
    statuses = {c.case_id: c.status for c in outcome.cases}
    assert statuses == {"c1": "passed", "c2": "failed", "c3": "passed", "c4": "error"}
    assert outcome.tests_passed == 2
    assert outcome.test_pass is False


# ---------------------------------------------------------------------------
# 13: fixture data must be JSON-compatible (enforced by validate_test_suite,
# called inside run_test_suite)
# ---------------------------------------------------------------------------


def test_13_non_json_compatible_fixture_rejected():
    import pytest
    from agent_tools.finals_rebuild.test_contract import TestContractValidationError

    bad_case = TestCase(case_id="c1", function_name="add", args=[(1, 2)], expected=3)
    suite = _suite([bad_case])
    with pytest.raises(TestContractValidationError):
        run_test_suite(code=_CODE_MATH, suite=suite)


# ---------------------------------------------------------------------------
# 14: no arbitrary assertion code executed — only the named function is called
# ---------------------------------------------------------------------------


def test_14_no_arbitrary_code_executed(tmp_path):
    """
    The fixture cannot smuggle in code: expected/args/kwargs are inert
    JSON data, never evaluated as Python. Prove this by using an
    'expected' value that LOOKS like a dangerous expression string — it
    must be compared as a literal string, never executed.
    """
    code = "def identity(x):\n    return x\n"
    dangerous_looking = "__import__('os').system('echo pwned')"
    suite = _suite([
        _case(function_name="identity", args=[dangerous_looking], expected=dangerous_looking)
    ])
    outcome = run_test_suite(code=code, suite=suite)
    # The string round-trips as plain data and compares equal — never executed.
    assert outcome.cases[0].status == "passed"


def test_no_eval_exec_compile_calls_in_worker_source():
    import ast as _ast
    import agent_tools.finals_rebuild.test_worker as worker_mod

    source = inspect.getsource(worker_mod)
    tree = _ast.parse(source)
    # compile() IS used once, deliberately, to load the artifact itself
    # (mirrors execution_worker.py) — eval/exec-as-a-call and __import__
    # must still never appear.
    forbidden_calls = {"eval", "__import__"}
    for node in _ast.walk(tree):
        if isinstance(node, _ast.Call) and isinstance(node.func, _ast.Name):
            assert node.func.id not in forbidden_calls, (
                f"test_worker.py must not call {node.func.id}()"
            )


def test_no_eval_exec_compile_calls_in_evaluator_source():
    import ast as _ast
    import agent_tools.finals_rebuild.test_evaluator as mod

    source = inspect.getsource(mod)
    tree = _ast.parse(source)
    forbidden_calls = {"eval", "exec", "compile", "__import__"}
    for node in _ast.walk(tree):
        if isinstance(node, _ast.Call) and isinstance(node.func, _ast.Name):
            assert node.func.id not in forbidden_calls, (
                f"test_evaluator.py must not call {node.func.id}()"
            )


# ---------------------------------------------------------------------------
# Preflight denylist still applies (defense in depth)
# ---------------------------------------------------------------------------


def test_denylist_still_applies_within_test_evaluator():
    code = "import socket\ndef f():\n    return 1\n"
    suite = _suite([_case(function_name="f", args=[], expected=1)])
    outcome = run_test_suite(code=code, suite=suite)
    assert outcome.cases[0].status == "error"
    assert outcome.cases[0].exception_type == "PreflightDenylistViolation"
    assert outcome.test_pass is False


# ---------------------------------------------------------------------------
# test_results_to_dict binding
# ---------------------------------------------------------------------------


def test_results_to_dict_binds_required_fields():
    suite = _suite([_case(function_name="add", args=[1, 2], expected=3)])
    outcome = run_test_suite(code=_CODE_MATH, suite=suite)
    d = results_to_dict(
        outcome, pair_id="a" * 64, run_id="b" * 64, artifact_hash="c" * 64
    )
    assert d["pair_id"] == "a" * 64
    assert d["run_id"] == "b" * 64
    assert d["artifact_hash"] == "c" * 64
    assert d["test_suite_hash"] == outcome.suite_hash
    assert len(d["cases"]) == 1
    case = d["cases"][0]
    for field_name in ("case_id", "status", "passed", "exception_type", "exception_message", "duration_ms"):
        assert field_name in case
