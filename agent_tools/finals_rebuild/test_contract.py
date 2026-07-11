"""
TestCase / TestSuite fixture contract — Commit 4C.

Scope
-----
A TestCase names a top-level function in an artifact plus JSON-compatible
args/kwargs/expected values and a comparison mode. There is NO way to
embed arbitrary Python (no assertion code, no eval string, no callable,
no class instance, no pickle) — every field is restricted to JSON-
compatible primitives (None / bool / number / string / list / dict with
string keys) and validated as such before a TestSuite is ever accepted.

This module only defines the schema, its validation, and JSON round-trip
/ hashing helpers. See test_evaluator.py for what actually runs a
TestSuite against artifact code, and test_worker.py for the disposable
subprocess entry point that calls the named functions.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List

from agent_tools.finals_rebuild.artifacts import sha256_json

COMPARISON_MODES: frozenset[str] = frozenset({
    "exact", "numeric_tolerance", "json_equal",
})

# A function_name must be a plain Python identifier — never a dotted path,
# call expression, or anything else that could be (mis)used as code. This
# is enforced independently of the JSON-compatibility check below, since
# "some_ident" is a valid JSON string but not every JSON string is a safe
# function_name.
_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class TestContractValidationError(ValueError):
    """Raised when a TestCase or TestSuite fails validation."""


# ---------------------------------------------------------------------------
# JSON-compatibility check
# ---------------------------------------------------------------------------


def is_json_compatible(value: Any) -> bool:
    """
    True iff *value* is built entirely from JSON-representable Python
    types: None, bool, int, float, str, list (of JSON-compatible values),
    or dict with str keys (and JSON-compatible values).

    Explicitly rejects: tuples, sets, bytes, callables, class instances,
    and anything else that isn't one of the above — a TestCase's args/
    kwargs/expected must never be able to carry a callable or arbitrary
    object across the JSON boundary into the worker subprocess.
    """
    if value is None or isinstance(value, (bool, int, float, str)):
        return True
    if isinstance(value, list):
        return all(is_json_compatible(item) for item in value)
    if isinstance(value, dict):
        return all(
            isinstance(key, str) and is_json_compatible(val)
            for key, val in value.items()
        )
    return False


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TestCase:
    """One fixture-driven test case.

    args/kwargs/expected are plain JSON-compatible Python values (never
    code, never a callable) — see is_json_compatible().
    """

    case_id: str
    function_name: str
    args: List[Any] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    expected: Any = None
    comparison_mode: str = "exact"


@dataclass(frozen=True)
class TestSuite:
    """A named, ordered collection of TestCases shared identically across
    all four treatments for one pair (see pipeline.py: PairedPipelineInput
    .test_suite — there is no per-treatment suite)."""

    suite_id: str
    cases: List[TestCase] = field(default_factory=list)
    timeout_seconds: float = 3.0
    numeric_tolerance: float = 1e-6


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_test_case(case: TestCase) -> None:
    if not isinstance(case.case_id, str) or not case.case_id.strip():
        raise TestContractValidationError("case_id must be a non-empty string")
    if not isinstance(case.function_name, str) or not _IDENTIFIER_RE.match(
        case.function_name
    ):
        raise TestContractValidationError(
            f"function_name must be a plain Python identifier, "
            f"got {case.function_name!r}"
        )
    if not isinstance(case.args, list):
        raise TestContractValidationError("args must be a list")
    if not is_json_compatible(case.args):
        raise TestContractValidationError(
            f"args must be JSON-compatible (case_id={case.case_id!r})"
        )
    if not isinstance(case.kwargs, dict) or not all(
        isinstance(k, str) for k in case.kwargs
    ):
        raise TestContractValidationError("kwargs must be a dict with string keys")
    if not is_json_compatible(case.kwargs):
        raise TestContractValidationError(
            f"kwargs must be JSON-compatible (case_id={case.case_id!r})"
        )
    if not is_json_compatible(case.expected):
        raise TestContractValidationError(
            f"expected must be JSON-compatible (case_id={case.case_id!r})"
        )
    if case.comparison_mode not in COMPARISON_MODES:
        raise TestContractValidationError(
            f"comparison_mode must be one of {sorted(COMPARISON_MODES)}, "
            f"got {case.comparison_mode!r} (case_id={case.case_id!r})"
        )


def validate_test_suite(suite: TestSuite) -> None:
    if not isinstance(suite.suite_id, str) or not suite.suite_id.strip():
        raise TestContractValidationError("suite_id must be a non-empty string")
    if not isinstance(suite.cases, list) or not suite.cases:
        raise TestContractValidationError("cases must be a non-empty list")

    seen_ids: set[str] = set()
    for case in suite.cases:
        if not isinstance(case, TestCase):
            raise TestContractValidationError(
                f"every entry in cases must be a TestCase, got {type(case)!r}"
            )
        validate_test_case(case)
        if case.case_id in seen_ids:
            raise TestContractValidationError(
                f"duplicate case_id {case.case_id!r} in suite {suite.suite_id!r}"
            )
        seen_ids.add(case.case_id)

    if (
        isinstance(suite.timeout_seconds, bool)
        or not isinstance(suite.timeout_seconds, (int, float))
        or suite.timeout_seconds <= 0
    ):
        raise TestContractValidationError("timeout_seconds must be a positive number")
    if (
        isinstance(suite.numeric_tolerance, bool)
        or not isinstance(suite.numeric_tolerance, (int, float))
        or suite.numeric_tolerance < 0
    ):
        raise TestContractValidationError(
            "numeric_tolerance must be a non-negative number"
        )


# ---------------------------------------------------------------------------
# JSON round-trip helpers
# ---------------------------------------------------------------------------


def test_case_to_dict(case: TestCase) -> Dict[str, Any]:
    return {
        "case_id": case.case_id,
        "function_name": case.function_name,
        "args": list(case.args),
        "kwargs": dict(case.kwargs),
        "expected": case.expected,
        "comparison_mode": case.comparison_mode,
    }


def test_case_from_dict(d: Dict[str, Any]) -> TestCase:
    return TestCase(
        case_id=d["case_id"],
        function_name=d["function_name"],
        args=list(d.get("args", [])),
        kwargs=dict(d.get("kwargs", {})),
        expected=d.get("expected"),
        comparison_mode=d.get("comparison_mode", "exact"),
    )


def test_suite_to_dict(suite: TestSuite) -> Dict[str, Any]:
    return {
        "suite_id": suite.suite_id,
        "cases": [test_case_to_dict(c) for c in suite.cases],
        "timeout_seconds": suite.timeout_seconds,
        "numeric_tolerance": suite.numeric_tolerance,
    }


def test_suite_from_dict(d: Dict[str, Any]) -> TestSuite:
    return TestSuite(
        suite_id=d["suite_id"],
        cases=[test_case_from_dict(c) for c in d.get("cases", [])],
        timeout_seconds=d.get("timeout_seconds", 3.0),
        numeric_tolerance=d.get("numeric_tolerance", 1e-6),
    )


def test_suite_json_round_trip(suite: TestSuite) -> TestSuite:
    raw_json = json.dumps(
        test_suite_to_dict(suite), sort_keys=True, separators=(",", ":"), ensure_ascii=True
    )
    return test_suite_from_dict(json.loads(raw_json))


def compute_test_suite_hash(suite: TestSuite) -> str:
    """Deterministic hash of *suite*'s full content — identical suites
    (including case order) always hash identically, and the pipeline uses
    this to guarantee all four treatments were evaluated against the
    exact same suite (see pipeline.py: PairedPipelineInput.test_suite)."""
    return sha256_json(test_suite_to_dict(suite))
