"""
Tests for agent_tools/finals_rebuild/evaluation.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import pytest

from agent_tools.finals_rebuild.evaluation import (
    EvaluationResult,
    EvaluationValidationError,
    compute_evaluation_hash,
    evaluation_result_from_dict,
    evaluation_result_json_round_trip,
    evaluation_result_to_dict,
    validate_evaluation_result,
)

_PAIR_ID = "a" * 64
_RUN_ID = "b" * 64
_HASH = "c" * 64
_TS = "2026-07-11T09:00:00+00:00"


def _result(**overrides) -> EvaluationResult:
    base = dict(
        pair_id=_PAIR_ID,
        run_id=_RUN_ID,
        treatment="ab1",
        artifact_hash=_HASH,
        evaluator_version="test-v1",
        evaluator_git_commit="deadbeef",
        evaluator_config_hash="d" * 64,
        syntax_pass=True,
        contract_status="not_required",
        required_functions=[],
        discovered_functions=["generate"],
        execution_status="not_run",
        execution_success=None,
        test_status="not_run",
        test_pass=None,
        tests_passed=None,
        tests_total=None,
        mcri_code=None,
        mcri_math=None,
        timeout=None,
        exception_type=None,
        exception_message=None,
        fail_closed=True,
        created_at_utc=_TS,
    )
    base.update(overrides)
    return EvaluationResult(**base)


# ---------------------------------------------------------------------------
# Basic validation
# ---------------------------------------------------------------------------


def test_valid_result_passes():
    validate_evaluation_result(_result())


def test_bad_pair_id_rejected():
    with pytest.raises(EvaluationValidationError, match="pair_id"):
        validate_evaluation_result(_result(pair_id="not-a-hash"))


def test_bad_treatment_rejected():
    with pytest.raises(EvaluationValidationError, match="treatment"):
        validate_evaluation_result(_result(treatment="ab5_bogus"))


def test_bad_contract_status_rejected():
    with pytest.raises(EvaluationValidationError, match="contract_status"):
        validate_evaluation_result(_result(contract_status="maybe"))


# ---------------------------------------------------------------------------
# execution_status="not_run" requires execution_success=None
# ---------------------------------------------------------------------------


def test_not_run_execution_requires_none_success():
    with pytest.raises(EvaluationValidationError, match="execution_success"):
        validate_evaluation_result(
            _result(execution_status="not_run", execution_success=False)
        )


def test_not_run_execution_with_none_success_passes():
    validate_evaluation_result(
        _result(execution_status="not_run", execution_success=None)
    )


def test_non_not_run_execution_requires_bool_success():
    with pytest.raises(EvaluationValidationError, match="execution_success"):
        validate_evaluation_result(
            _result(execution_status="success", execution_success=None)
        )


def test_non_not_run_execution_with_bool_passes():
    validate_evaluation_result(
        _result(
            execution_status="success",
            execution_success=True,
            isolation_level="guarded_subprocess_not_security_sandbox",
        )
    )


# ---------------------------------------------------------------------------
# test_status="not_run" requires all test/mcri fields None
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "field_name,bad_value",
    [
        ("test_pass", False),
        ("tests_passed", 0),
        ("tests_total", 0),
        ("mcri_code", 0.0),
        ("mcri_math", 0.0),
    ],
)
def test_not_run_test_status_rejects_non_none_fields(field_name, bad_value):
    with pytest.raises(EvaluationValidationError, match=field_name):
        validate_evaluation_result(
            _result(test_status="not_run", **{field_name: bad_value})
        )


def test_non_not_run_test_status_requires_full_fields():
    validate_evaluation_result(
        _result(
            test_status="passed",
            test_pass=True,
            tests_passed=5,
            tests_total=5,
            mcri_code=1.0,
            mcri_math=1.0,
        )
    )


def test_tests_passed_cannot_exceed_tests_total():
    with pytest.raises(EvaluationValidationError, match="tests_passed"):
        validate_evaluation_result(
            _result(
                test_status="passed",
                test_pass=False,
                tests_passed=6,
                tests_total=5,
            )
        )


# ---------------------------------------------------------------------------
# syntax_pass=False requires exception_type
# ---------------------------------------------------------------------------


def test_syntax_fail_without_exception_type_rejected():
    with pytest.raises(EvaluationValidationError, match="exception_type"):
        validate_evaluation_result(
            _result(syntax_pass=False, discovered_functions=[], exception_type=None)
        )


def test_syntax_fail_with_exception_type_passes():
    validate_evaluation_result(
        _result(
            syntax_pass=False,
            discovered_functions=[],
            exception_type="SyntaxError",
            exception_message="invalid syntax",
        )
    )


# ---------------------------------------------------------------------------
# timeout / created_at_utc
# ---------------------------------------------------------------------------


def test_negative_timeout_rejected():
    with pytest.raises(EvaluationValidationError, match="timeout"):
        validate_evaluation_result(_result(timeout=-1))


def test_positive_timeout_accepted():
    validate_evaluation_result(_result(timeout=30.0))


def test_bad_created_at_utc_rejected():
    with pytest.raises(EvaluationValidationError, match="created_at_utc"):
        validate_evaluation_result(_result(created_at_utc="not-a-date"))


# ---------------------------------------------------------------------------
# JSON round-trip
# ---------------------------------------------------------------------------


def test_json_round_trip_preserves_content():
    result = _result()
    round_tripped = evaluation_result_json_round_trip(result)
    assert evaluation_result_to_dict(result) == evaluation_result_to_dict(round_tripped)


def test_from_dict_to_dict_inverse():
    result = _result()
    d = evaluation_result_to_dict(result)
    restored = evaluation_result_from_dict(d)
    assert restored == result


# ---------------------------------------------------------------------------
# compute_evaluation_hash determinism
# ---------------------------------------------------------------------------


def test_compute_evaluation_hash_is_deterministic():
    result = _result()
    assert compute_evaluation_hash(result) == compute_evaluation_hash(result)


def test_compute_evaluation_hash_changes_with_content():
    a = _result()
    b = _result(syntax_pass=False, discovered_functions=[], exception_type="SyntaxError")
    assert compute_evaluation_hash(a) != compute_evaluation_hash(b)


def test_compute_evaluation_hash_is_valid_sha256():
    import re
    h = compute_evaluation_hash(_result())
    assert re.match(r"^[0-9a-f]{64}$", h)


# ---------------------------------------------------------------------------
# not-evaluated fields are None, never False/0 (schema-level defaults)
# ---------------------------------------------------------------------------


def test_default_construction_uses_none_not_false_or_zero():
    result = EvaluationResult(
        pair_id=_PAIR_ID,
        run_id=_RUN_ID,
        treatment="ab1",
        artifact_hash=_HASH,
        evaluator_version="test-v1",
        evaluator_git_commit="deadbeef",
        evaluator_config_hash="d" * 64,
        syntax_pass=True,
        contract_status="not_required",
        created_at_utc=_TS,
    )
    assert result.execution_status == "not_run"
    assert result.execution_success is None
    assert result.test_status == "not_run"
    assert result.test_pass is None
    assert result.tests_passed is None
    assert result.tests_total is None
    assert result.mcri_code is None
    assert result.mcri_math is None
    validate_evaluation_result(result)
