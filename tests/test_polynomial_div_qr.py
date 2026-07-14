# -*- coding: utf-8 -*-
"""Targeted tests for the exact PolynomialOps.div_qr primitive."""
import os
import sys
from fractions import Fraction
from math import gcd

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.prompts.domain_function_library import PolynomialOps, POLYNOMIALOPS_HELPERS

div_qr = PolynomialOps.div_qr


def _frac(value):
    return Fraction(str(value))


def _check_identity(dividend, divisor):
    quotient, remainder = div_qr(dividend, divisor)
    d = [_frac(v) for v in divisor]
    q = [_frac(v) for v in quotient]
    r = [_frac(v) for v in remainder]
    product = [Fraction(0)] * (len(d) + len(q) - 1)
    for i, a in enumerate(d):
        for j, b in enumerate(q):
            product[i + j] += a * b
    total = list(product)
    pad = len(total) - len(r)
    for i, v in enumerate(r):
        total[pad + i] += v
    # strip leading zeros of both sides
    def strip(vals):
        i = 0
        while i < len(vals) - 1 and vals[i] == 0:
            i += 1
        return vals[i:]
    assert strip(total) == strip([_frac(v) for v in dividend])
    assert len(r) < len(d) or r == [0]
    return quotient, remainder


# ---------------------------------------------------------------------------
# A. Basic correctness
# ---------------------------------------------------------------------------

def test_source_question_case():
    assert div_qr([4, -3, -5], [1, 2]) == ([4, -11], [17])


def test_exact_division():
    # (x+2)(x+3) = x^2+5x+6
    assert div_qr([1, 5, 6], [1, 2]) == ([1, 3], [0])


def test_nonzero_remainder():
    assert div_qr([2, -1, -6], [1, -2]) == ([2, 3], [0])
    assert div_qr([3, 0, 5], [1, -4]) == ([3, 12], [53])


def test_higher_degree_dividend():
    # (x^2+1)(x-3) + 7 = x^3 -3x^2 + x + 4
    assert div_qr([1, -3, 1, 4], [1, -3]) == ([1, 0, 1], [7])


def test_missing_terms():
    assert div_qr([1, 0, -4], [1, 2]) == ([1, -2], [0])


def test_non_monic_divisor():
    # (2x+3)(x-2) = 2x^2 - x - 6
    assert div_qr([2, -1, -6], [2, 3]) == ([1, -2], [0])


def test_fraction_quotient_coefficients():
    quotient, remainder = div_qr([3, 0, 5], [2, -4])
    assert quotient == ["3/2", 3]
    assert remainder == [17]


def test_constant_divisor():
    assert div_qr([4, -6, 8], [2]) == ([2, -3, 4], [0])


def test_divisor_degree_greater_than_dividend():
    assert div_qr([3, 1], [1, 0, 0, 5]) == ([0], [3, 1])


def test_zero_dividend():
    assert div_qr([0], [1, 2]) == ([0], [0])
    assert div_qr([0, 0, 0], [1, 2]) == ([0], [0])


# ---------------------------------------------------------------------------
# B. Canonicalization
# ---------------------------------------------------------------------------

def _assert_canonical(value):
    if isinstance(value, int):
        assert not isinstance(value, bool)
        return
    assert isinstance(value, str) and "/" in value
    p, q = value.split("/")
    assert int(q) > 1 and gcd(abs(int(p)), int(q)) == 1


def test_fraction_outputs_reduced_and_positive_denominator():
    quotient, remainder = div_qr([1, 1, 1], [-2, 1])
    for value in quotient + remainder:
        _assert_canonical(value)
        if isinstance(value, str):
            assert not value.split("/")[1].startswith("-")


def test_integer_fraction_becomes_int():
    quotient, remainder = div_qr([4, 8], [2])
    assert quotient == [2, 4] and remainder == [0]
    assert all(isinstance(v, int) for v in quotient + remainder)


def test_leading_zero_removal():
    assert div_qr([0, 0, 1, 5, 6], [0, 1, 2]) == ([1, 3], [0])


def test_zero_polynomial_canonical_form():
    q, r = div_qr([1, 2], [1, 2])
    assert q == [1] and r == [0]


def test_no_float_in_outputs():
    for dividend, divisor in ([4, -3, -5], [1, 2]), ([3, 0, 5], [2, -4]), ([1, 1, 1], [3, 1]):
        quotient, remainder = div_qr(dividend, divisor)
        for value in quotient + remainder:
            assert not isinstance(value, float)


def test_accepts_fraction_strings_and_fraction_instances():
    assert div_qr(["1/2", 1], [1]) == (["1/2", 1], [0])
    assert div_qr([Fraction(1, 2), 1], ["1/2"]) == ([1, 2], [0])


# ---------------------------------------------------------------------------
# C. Invariants
# ---------------------------------------------------------------------------

CASES = [
    ([1, 5, 6], [1, 2]),
    ([4, -3, -5], [1, 2]),
    ([2, 0, -7, 3], [1, -1]),
    ([2, -1, -6], [2, 3]),
    ([5, 0, 0, 1], [3, -2]),
    ([1, 0, -4, 0, 7], [2, 5]),
    ([-3, 7, 11], [-2, 1]),
    ([9, 0, 1], [3]),
    ([1, 1], [1, 0, 1]),
]


@pytest.mark.parametrize("dividend,divisor", CASES)
def test_division_identity_and_remainder_degree(dividend, divisor):
    _check_identity(dividend, divisor)


def test_inputs_not_mutated():
    dividend = [4, -3, -5]
    divisor = [1, 2]
    div_qr(dividend, divisor)
    assert dividend == [4, -3, -5] and divisor == [1, 2]


def test_repeated_calls_deterministic():
    first = div_qr([2, 0, -7, 3], [2, 5])
    for _ in range(5):
        assert div_qr([2, 0, -7, 3], [2, 5]) == first


# ---------------------------------------------------------------------------
# D. Fail closed
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("dividend,divisor", [
    ([1, 2], [0]),            # zero divisor polynomial
    ([1, 2], [0, 0]),         # zero divisor polynomial (multi-term)
    ([1, 2], []),             # empty divisor
    ([], [1, 2]),             # empty dividend
    ([1.5, 2], [1, 2]),       # float coefficient
    ([1, 2], [1, 0.5]),       # float in divisor
    (["3//2", 1], [1, 2]),    # malformed fraction string
    (["3/0", 1], [1, 2]),     # zero denominator
    (["1.5", 1], [1, 2]),     # decimal string
    ([object(), 1], [1, 2]),  # unsupported type
    ([True, 2], [1, 2]),      # bool is not an accepted numeric type
    (None, [1, 2]),           # not a list
])
def test_fail_closed(dividend, divisor):
    with pytest.raises(ValueError):
        div_qr(dividend, divisor)


# ---------------------------------------------------------------------------
# E. Integration
# ---------------------------------------------------------------------------

def test_helpers_string_copy_has_div_qr():
    ns = {}
    exec(POLYNOMIALOPS_HELPERS, ns)
    ops = ns["PolynomialOps"]
    assert ops.div_qr([4, -3, -5], [1, 2]) == ([4, -11], [17])


def test_runtime_injection_carries_div_qr():
    from core.code_generator import _inject_domain_libs
    code = "def generate(level=1, **kwargs):\n    q, r = PolynomialOps.div_qr([4, -3, -5], [1, 2])\n    return q, r\n"
    injected, _ = _inject_domain_libs(code, skill_id="jh_數學2上_FourArithmeticOperationsOfPolynomial")
    ns = {}
    exec(injected, ns)
    assert ns["generate"]() == ([4, -11], [17])


def test_ab2d_polynomial_prompt_exposes_div_qr():
    from core.skill_policies.registry import normalize_skill_id, list_registered_skill_ids, refresh_registry
    from agent_tools.benchmark import load_prompt_from_skill
    refresh_registry()
    available = list_registered_skill_ids()
    norm = normalize_skill_id("polynomial_division_general", available)
    assert norm == "jh_數學2上_FourArithmeticOperationsOfPolynomial"
    task = {"task_id": "x", "oracle_type": "polynomial_division_general"}
    payload = load_prompt_from_skill(norm, ablation_target="Ab3", task_metadata=task,
                                     frozen_payload={"dividend_coefficients": [1, 2, 3], "divisor_coefficients": [1, 1]})
    assert "PolynomialOps.div_qr(dividend_coefficients, divisor_coefficients)" in payload
    assert "highest degree first" in payload
    assert "(quotient_coefficients, remainder_coefficients)" in payload
    # generation contract still intact
    assert "Write only complete Python source code" in payload
    assert "def generate(level=1, **kwargs):" in payload
    assert "Return exactly these three top-level keys and no others" in payload


def test_ab1_and_ab2g_do_not_gain_div_qr():
    from core.skill_policies.registry import normalize_skill_id, list_registered_skill_ids, refresh_registry
    from agent_tools.benchmark import load_prompt_from_skill
    refresh_registry()
    available = list_registered_skill_ids()
    norm = normalize_skill_id("polynomial_division_quotient_remainder", available)

    # Ab1: byte-equivalent to the bare prompt file, no div_qr text
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bare = open(os.path.join(root, "agent_skills", norm, "experiments", "ab1_bare_prompt.md"), encoding="utf-8").read()
    payload_ab1 = load_prompt_from_skill(norm, ablation_target="Ab1", task_metadata=None)
    assert payload_ab1 == bare
    assert "div_qr" not in payload_ab1

    # Ab2g (task_metadata=None): base rules stop at SKILL_END_PROMPT, so the
    # appended Ab2d-only reusable block must not appear
    payload_ab2g = load_prompt_from_skill(norm, ablation_target="Ab3", task_metadata=None)
    assert "div_qr" not in payload_ab2g
    skill_text = open(os.path.join(root, "agent_skills", norm, "SKILL.md"), encoding="utf-8").read()
    benchmark_text = open(os.path.join(root, "agent_skills", norm, "prompt_benchmark.md"), encoding="utf-8").read().strip()
    expected_ab2g = f"{skill_text.split('=== SKILL_END_PROMPT ===')[0]}\n=== SKILL_END_PROMPT ===\n\n{benchmark_text}"
    assert payload_ab2g == expected_ab2g


def test_other_families_do_not_route_to_polynomial():
    from core.skill_policies.registry import normalize_skill_id, list_registered_skill_ids, refresh_registry
    refresh_registry()
    available = list_registered_skill_ids()
    assert normalize_skill_id("radical_simplification", available) == "jh_數學2上_FourOperationsOfRadicals"
    assert normalize_skill_id("exact_rational_expression", available) == "jh_數學1上_FourArithmeticOperationsOfNumbers"
