"""
Tests for agent_tools/finals_rebuild/math_validator.py
"""

from __future__ import annotations

import copy
import os
import sys
from fractions import Fraction

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from agent_tools.finals_rebuild.math_task_schema import MathOutputContract
from agent_tools.finals_rebuild.math_validator import (
    ERROR_EXTRA_FIELD,
    ERROR_INVALID_TYPE,
    ERROR_MISSING_FIELD,
    ERROR_NON_FINITE_VALUE,
    ERROR_NOT_EQUIVALENT,
    ERROR_OUT_OF_TOLERANCE,
    ERROR_PARSE_ERROR,
    ERROR_UNDECLARED_SYMBOL,
    ERROR_VALIDATOR_ERROR,
    STATUS_ERROR,
    STATUS_FAILED,
    STATUS_SUCCESS,
    validate_answer,
)


def _number_contract(
    *,
    python_return_type="int",
    representation_policy="exact_answer_type",
    representation_subtype="integer",
    allowed_tolerance=None,
):
    return MathOutputContract(
        answer_type="number",
        representation_subtype=representation_subtype,
        python_return_type=python_return_type,
        representation_policy=representation_policy,
        validator_type="number_exact",
        allowed_tolerance=allowed_tolerance,
        symbolic_variables=(),
        answer_fields=(),
    )


def _rational_contract(*, representation_policy="exact_answer_type"):
    return MathOutputContract(
        answer_type="rational",
        representation_subtype=None,
        python_return_type="Fraction",
        representation_policy=representation_policy,
        validator_type="rational_exact",
        allowed_tolerance=None,
        symbolic_variables=(),
        answer_fields=(),
    )


def _symbolic_contract(
    *,
    representation_subtype="generic",
    symbolic_variables=(),
    representation_policy="exact_answer_type",
):
    return MathOutputContract(
        answer_type="symbolic_expression",
        representation_subtype=representation_subtype,
        python_return_type="str",
        representation_policy=representation_policy,
        validator_type="symbolic_expression",
        allowed_tolerance=None,
        symbolic_variables=tuple(symbolic_variables),
        answer_fields=(),
    )


def _coordinate_contract(*, representation_policy="exact_answer_type", allowed_tolerance=None):
    return MathOutputContract(
        answer_type="coordinate_pair",
        representation_subtype=None,
        python_return_type="tuple",
        representation_policy=representation_policy,
        validator_type="coordinate_pair_exact",
        allowed_tolerance=allowed_tolerance,
        symbolic_variables=(),
        answer_fields=(),
    )


def _multi_field_contract(
    answer_fields,
    *,
    representation_policy="semantic_only",
    symbolic_variables=(),
):
    return MathOutputContract(
        answer_type="multi_field_answer",
        representation_subtype=None,
        python_return_type="dict",
        representation_policy=representation_policy,
        validator_type="multi_field_exact",
        allowed_tolerance=None,
        symbolic_variables=tuple(symbolic_variables),
        answer_fields=tuple(answer_fields),
    )


def test_number_int_correct():
    result = validate_answer(5, 5, _number_contract())
    assert result.is_correct is True
    assert result.mathematical_equivalence is True
    assert result.representation_compliance is True
    assert result.status == STATUS_SUCCESS


def test_number_int_wrong():
    result = validate_answer(4, 5, _number_contract())
    assert result.is_correct is False
    assert result.error_code == ERROR_NOT_EQUIVALENT


def test_number_bool_rejected():
    result = validate_answer(True, 1, _number_contract())
    assert result.status == STATUS_ERROR
    assert result.error_code == ERROR_INVALID_TYPE


def test_number_float_tolerance_inside():
    contract = _number_contract(
        python_return_type="float",
        representation_subtype="decimal",
        allowed_tolerance=1e-6,
    )
    result = validate_answer(1.0000001, 1.0, contract)
    assert result.is_correct is True


def test_number_float_tolerance_outside():
    contract = _number_contract(
        python_return_type="float",
        representation_subtype="decimal",
        allowed_tolerance=1e-9,
    )
    result = validate_answer(1.1, 1.0, contract)
    assert result.is_correct is False
    assert result.error_code == ERROR_NOT_EQUIVALENT


def test_number_nan_rejected():
    contract = _number_contract(
        python_return_type="float",
        representation_subtype="decimal",
    )
    result = validate_answer(float("nan"), 1.0, contract)
    assert result.status == STATUS_ERROR
    assert result.error_code == ERROR_NON_FINITE_VALUE


def test_number_inf_rejected():
    contract = _number_contract(
        python_return_type="float",
        representation_subtype="decimal",
    )
    result = validate_answer(float("inf"), 1.0, contract)
    assert result.status == STATUS_ERROR
    assert result.error_code == ERROR_NON_FINITE_VALUE


def test_number_semantic_only_int_float_equivalent():
    contract = _number_contract(
        python_return_type="float",
        representation_subtype="decimal",
        representation_policy="semantic_only",
    )
    result = validate_answer(5, 5.0, contract)
    assert result.is_correct is True
    assert result.representation_compliance is True


def test_number_exact_rejects_wrong_type_but_may_be_math_equivalent():
    contract = _number_contract()
    result = validate_answer(5.0, 5, contract)
    assert result.mathematical_equivalence is True
    assert result.representation_compliance is False
    assert result.is_correct is False
    assert result.status == STATUS_FAILED


def test_rational_fraction_exact_equal():
    contract = _rational_contract()
    result = validate_answer(Fraction(1, 2), Fraction(1, 2), contract)
    assert result.is_correct is True


def test_rational_equivalent_reduced_form():
    contract = _rational_contract()
    result = validate_answer(Fraction(2, 4), Fraction(1, 2), contract)
    assert result.is_correct is True


def test_rational_semantic_allows_int():
    contract = _rational_contract(representation_policy="semantic_only")
    result = validate_answer(1, Fraction(1, 1), contract)
    assert result.is_correct is True


def test_rational_semantic_allows_half_float_string_path():
    contract = _rational_contract(representation_policy="semantic_only")
    result = validate_answer(0.5, Fraction(1, 2), contract)
    assert result.is_correct is True


def test_rational_exact_rejects_float():
    contract = _rational_contract(representation_policy="exact_answer_type")
    result = validate_answer(0.5, Fraction(1, 2), contract)
    assert result.status == STATUS_ERROR
    assert result.error_code == ERROR_INVALID_TYPE


def test_rational_bool_rejected():
    contract = _rational_contract(representation_policy="semantic_only")
    result = validate_answer(True, Fraction(1, 2), contract)
    assert result.error_code == ERROR_INVALID_TYPE


def test_coordinate_pair_correct_tuple():
    contract = _coordinate_contract()
    result = validate_answer((1, 2), (1, 2), contract)
    assert result.is_correct is True
    assert result.canonical_actual == (1, 2)


def test_coordinate_pair_swapped_is_wrong():
    contract = _coordinate_contract()
    result = validate_answer((2, 1), (1, 2), contract)
    assert result.is_correct is False


def test_coordinate_pair_wrong_length():
    contract = _coordinate_contract()
    result = validate_answer((1, 2, 3), (1, 2), contract)
    assert result.status == STATUS_ERROR
    assert result.error_code == ERROR_PARSE_ERROR


def test_coordinate_exact_rejects_list():
    contract = _coordinate_contract(representation_policy="exact_answer_type")
    result = validate_answer([1, 2], (1, 2), contract)
    assert result.representation_compliance is False


def test_coordinate_semantic_accepts_list():
    contract = _coordinate_contract(representation_policy="semantic_only")
    result = validate_answer([1, 2], (1, 2), contract)
    assert result.is_correct is True
    assert result.representation_compliance is True


def test_coordinate_element_tolerance():
    contract = _coordinate_contract(
        representation_policy="semantic_only",
        allowed_tolerance=1e-6,
    )
    result = validate_answer((1.0000001, 2.0), (1.0, 2.0), contract)
    assert result.is_correct is True


def test_symbolic_x_plus_x_equivalent_to_two_x():
    contract = _symbolic_contract(symbolic_variables=("x",))
    result = validate_answer("x+x", "2*x", contract)
    assert result.is_correct is True


def test_symbolic_sqrt_12_equivalent_to_two_sqrt_3():
    contract = _symbolic_contract()
    result = validate_answer("sqrt(12)", "2*sqrt(3)", contract)
    assert result.is_correct is True


def test_symbolic_undeclared_symbol_rejected():
    contract = _symbolic_contract(symbolic_variables=("x",))
    result = validate_answer("y+1", "y+1", contract)
    assert result.status == STATUS_ERROR
    assert result.error_code == ERROR_UNDECLARED_SYMBOL


def test_symbolic_invalid_syntax():
    contract = _symbolic_contract()
    result = validate_answer("sqrt(", "sqrt(2)", contract)
    assert result.status == STATUS_ERROR
    assert result.error_code == ERROR_PARSE_ERROR


def test_symbolic_arbitrary_python_rejected():
    contract = _symbolic_contract(symbolic_variables=("x",))
    result = validate_answer("__import__('os')", "x", contract)
    assert result.status == STATUS_ERROR


def test_symbolic_radical_rejects_float_approximation():
    contract = _symbolic_contract(representation_subtype="radical")
    result = validate_answer("1.41421356", "sqrt(2)", contract)
    assert result.is_correct is False
    assert result.mathematical_equivalence is False


def test_multi_field_key_order_irrelevant():
    contract = _multi_field_contract(("x", "y"))
    actual = {"y": -1, "x": 1}
    reference = {"x": 1, "y": -1}
    result = validate_answer(actual, reference, contract)
    assert result.is_correct is True


def test_multi_field_missing_key():
    contract = _multi_field_contract(("x", "y"))
    result = validate_answer({"x": 1}, {"x": 1, "y": -1}, contract)
    assert result.status == STATUS_ERROR
    assert result.error_code == ERROR_MISSING_FIELD


def test_multi_field_extra_key():
    contract = _multi_field_contract(("x",))
    result = validate_answer({"x": 1, "y": 2}, {"x": 1}, contract)
    assert result.status == STATUS_ERROR
    assert result.error_code == ERROR_EXTRA_FIELD


def test_multi_field_wrong_value():
    contract = _multi_field_contract(("x", "y"))
    result = validate_answer({"x": 1, "y": 0}, {"x": 1, "y": -1}, contract)
    assert result.is_correct is False
    assert result.error_code == ERROR_NOT_EQUIVALENT


def test_multi_field_representation_noncompliant_field():
    contract = _multi_field_contract(("x",), representation_policy="exact_answer_type")
    result = validate_answer({"x": 1.0}, {"x": 1}, contract)
    assert result.is_correct is False
    assert result.representation_compliance is False


def test_semantic_only_representation_compliance_true_when_parseable():
    contract = _number_contract(representation_policy="semantic_only", python_return_type="float")
    result = validate_answer(3, 3.0, contract)
    assert result.representation_compliance is True


def test_is_correct_is_and_of_equivalence_and_representation():
    contract = _number_contract()
    result = validate_answer(5.0, 5, contract)
    assert result.mathematical_equivalence is True
    assert result.representation_compliance is False
    assert result.is_correct is False


def test_validator_exception_becomes_validator_error(monkeypatch):
    contract = _number_contract()

    def boom(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(
        "agent_tools.finals_rebuild.math_validator._validate_number",
        boom,
    )
    result = validate_answer(1, 1, contract)
    assert result.status == STATUS_ERROR
    assert result.error_code == ERROR_VALIDATOR_ERROR


def test_inputs_not_mutated():
    contract = _multi_field_contract(("x", "y"))
    actual = {"y": -1, "x": 1}
    reference = {"x": 1, "y": -1}
    actual_copy = copy.deepcopy(actual)
    reference_copy = copy.deepcopy(reference)
    contract_copy = copy.deepcopy(contract)
    validate_answer(actual, reference, contract)
    assert actual == actual_copy
    assert reference == reference_copy
    assert contract == contract_copy


def test_does_not_import_ollama_or_use_recompute_helper():
    import agent_tools.finals_rebuild.math_validator as module

    text = open(module.__file__, encoding="utf-8").read()
    assert "ollama" not in text.lower()
    assert "_recompute_correct_answer_from_question" not in text
