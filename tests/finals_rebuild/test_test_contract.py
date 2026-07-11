"""
Tests for agent_tools/finals_rebuild/test_contract.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import pytest

from agent_tools.finals_rebuild.test_contract import (
    TestCase,
    TestContractValidationError,
    TestSuite,
    compute_test_suite_hash,
    is_json_compatible,
    validate_test_case,
    validate_test_suite,
)
# Aliased on import: these names start with "test_" (matching the
# project's to_dict/from_dict naming convention for TestSuite), which
# pytest's default collector would otherwise mistake for test functions
# if imported unqualified into this test module's namespace.
from agent_tools.finals_rebuild.test_contract import (
    test_suite_from_dict as suite_from_dict,
    test_suite_json_round_trip as suite_json_round_trip,
    test_suite_to_dict as suite_to_dict,
)


def _case(**overrides) -> TestCase:
    base = dict(
        case_id="c1",
        function_name="add",
        args=[1, 2],
        kwargs={},
        expected=3,
        comparison_mode="exact",
    )
    base.update(overrides)
    return TestCase(**base)


def _suite(cases=None, **overrides) -> TestSuite:
    base = dict(
        suite_id="s1",
        cases=cases if cases is not None else [_case()],
        timeout_seconds=3.0,
        numeric_tolerance=1e-6,
    )
    base.update(overrides)
    return TestSuite(**base)


# ---------------------------------------------------------------------------
# JSON-compatibility
# ---------------------------------------------------------------------------


def test_json_compatible_primitives():
    for value in (None, True, False, 1, 1.5, "s", [], {}, [1, "a", None], {"k": [1, 2]}):
        assert is_json_compatible(value)


def test_13_rejects_non_json_compatible_values():
    class Foo:
        pass

    for value in (Foo(), (1, 2), {1, 2}, b"bytes", lambda: None):
        assert not is_json_compatible(value)


def test_rejects_non_string_dict_keys():
    assert not is_json_compatible({1: "a"})


# ---------------------------------------------------------------------------
# TestCase validation
# ---------------------------------------------------------------------------


def test_valid_case_passes():
    validate_test_case(_case())


def test_case_id_must_be_non_empty():
    with pytest.raises(TestContractValidationError, match="case_id"):
        validate_test_case(_case(case_id=""))


def test_function_name_must_be_identifier():
    with pytest.raises(TestContractValidationError, match="function_name"):
        validate_test_case(_case(function_name="os.system"))


def test_function_name_rejects_call_expression():
    with pytest.raises(TestContractValidationError, match="function_name"):
        validate_test_case(_case(function_name="add()"))


def test_comparison_mode_must_be_allowed():
    with pytest.raises(TestContractValidationError, match="comparison_mode"):
        validate_test_case(_case(comparison_mode="regex_match"))


def test_args_must_be_json_compatible():
    with pytest.raises(TestContractValidationError, match="args"):
        validate_test_case(_case(args=[(1, 2)]))


def test_kwargs_must_be_json_compatible():
    with pytest.raises(TestContractValidationError, match="kwargs"):
        validate_test_case(_case(kwargs={"x": {1, 2}}))


def test_expected_must_be_json_compatible():
    with pytest.raises(TestContractValidationError, match="expected"):
        validate_test_case(_case(expected=object()))


def test_all_three_comparison_modes_are_allowed():
    for mode in ("exact", "numeric_tolerance", "json_equal"):
        validate_test_case(_case(comparison_mode=mode))


# ---------------------------------------------------------------------------
# TestSuite validation
# ---------------------------------------------------------------------------


def test_valid_suite_passes():
    validate_test_suite(_suite())


def test_suite_requires_at_least_one_case():
    with pytest.raises(TestContractValidationError, match="cases"):
        validate_test_suite(_suite(cases=[]))


def test_suite_rejects_duplicate_case_ids():
    with pytest.raises(TestContractValidationError, match="duplicate"):
        validate_test_suite(_suite(cases=[_case(case_id="c1"), _case(case_id="c1")]))


def test_suite_requires_positive_timeout():
    with pytest.raises(TestContractValidationError, match="timeout_seconds"):
        validate_test_suite(_suite(timeout_seconds=0))


def test_suite_requires_non_negative_tolerance():
    with pytest.raises(TestContractValidationError, match="numeric_tolerance"):
        validate_test_suite(_suite(numeric_tolerance=-1))


# ---------------------------------------------------------------------------
# JSON round-trip + deterministic hash
# ---------------------------------------------------------------------------


def test_json_round_trip_preserves_content():
    suite = _suite()
    round_tripped = suite_json_round_trip(suite)
    assert suite_to_dict(suite) == suite_to_dict(round_tripped)


def test_from_dict_to_dict_inverse():
    suite = _suite()
    d = suite_to_dict(suite)
    restored = suite_from_dict(d)
    assert restored == suite


def test_suite_hash_deterministic():
    suite = _suite()
    assert compute_test_suite_hash(suite) == compute_test_suite_hash(suite)


def test_suite_hash_changes_with_content():
    suite1 = _suite()
    suite2 = _suite(cases=[_case(case_id="different")])
    assert compute_test_suite_hash(suite1) != compute_test_suite_hash(suite2)


def test_suite_hash_is_valid_sha256():
    import re
    h = compute_test_suite_hash(_suite())
    assert re.match(r"^[0-9a-f]{64}$", h)
