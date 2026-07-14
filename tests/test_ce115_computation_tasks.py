# -*- coding: utf-8 -*-
"""Targeted tests for the four computation-only CE115 task families."""
import json
import os
import sys
from fractions import Fraction
from math import isqrt
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.skill_policies.registry import normalize_skill_id, list_registered_skill_ids, refresh_registry
from agent_tools.finals_rebuild.math_task_sampler import sample_task_parameters
from agent_tools.finals_rebuild.math_task_oracles import evaluate_math_task_oracle
from agent_tools.finals_rebuild.math_answer_contracts import render_answer_contract, CONTRACTS, NEUTRAL_TASK_STATEMENTS

MANIFEST = Path(__file__).parent / "finals_rebuild" / "fixtures" / "math_generation_tasks_ce115_pilot.jsonl"
SEEDS = (2026071401, 2026071402, 2026071403)

FAMILY_TASK_IDS = [
    f"ce115_calc_{family}_l{level}"
    for family in ("radical_simplification", "exact_rational_expression",
                   "polynomial_division", "polynomial_factor_roots")
    for level in (1, 2, 3)
]

ROUTING_EXPECTATIONS = {
    "radical_simplification": "jh_數學2上_FourOperationsOfRadicals",
    "exact_rational_expression": "jh_數學1上_FourArithmeticOperationsOfNumbers",
    "polynomial_division_general": "jh_數學2上_FourArithmeticOperationsOfPolynomial",
    "polynomial_factor_roots": "jh_數學2上_FourArithmeticOperationsOfPolynomial",
}


def load_tasks() -> dict:
    rows = [json.loads(line) for line in MANIFEST.read_text(encoding="utf-8").splitlines() if line.strip()]
    return {row["task_id"]: row for row in rows}


def _assert_json_ints_only(node):
    """Recursively assert no float appears anywhere in a payload."""
    if isinstance(node, float):
        pytest.fail(f"float leaked into payload: {node!r}")
    if isinstance(node, dict):
        for value in node.values():
            _assert_json_ints_only(value)
    if isinstance(node, list):
        for value in node:
            _assert_json_ints_only(value)


def _is_square_free(n: int) -> bool:
    factor = 2
    while factor * factor <= n:
        if n % (factor * factor) == 0:
            return False
        factor += 1
    return True


def _canonical_ok(value) -> bool:
    if isinstance(value, int):
        return True
    if isinstance(value, str) and "/" in value:
        p, q = value.split("/")
        p, q = int(p), int(q)
        from math import gcd
        return q > 1 and gcd(abs(p), q) == 1
    return False


# ---------------------------------------------------------------------------
# Determinism and sampling
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("task_id", FAMILY_TASK_IDS)
def test_deterministic_sampling(task_id):
    task = load_tasks()[task_id]
    payloads = []
    for seed in SEEDS:
        first = sample_task_parameters(task, seed)
        second = sample_task_parameters(task, seed)
        assert first == second, "same seed must reproduce the same frozen payload"
        payloads.append(json.dumps(first["oracle_payload"], sort_keys=True))
    assert len(set(payloads)) > 1, "different seeds must vary at least some parameters"


@pytest.mark.parametrize("task_id", FAMILY_TASK_IDS)
def test_no_float_in_payload(task_id):
    task = load_tasks()[task_id]
    for seed in SEEDS:
        _assert_json_ints_only(sample_task_parameters(task, seed)["oracle_payload"])


# ---------------------------------------------------------------------------
# Oracle correctness against frozen payloads + invariants
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("task_id", FAMILY_TASK_IDS)
def test_oracle_accepts_expected_and_rejects_wrong(task_id):
    task = load_tasks()[task_id]
    for seed in SEEDS:
        payload = sample_task_parameters(task, seed)["oracle_payload"]
        verdict = evaluate_math_task_oracle(task["oracle_type"], payload, None)
        assert verdict["error"] is None, f"oracle failed on valid frozen payload: {verdict['error']}"
        expected = verdict["expected_answer"]

        ok = evaluate_math_task_oracle(task["oracle_type"], payload, expected)
        assert ok["is_correct"] is True

        wrong = json.loads(json.dumps(expected))
        # perturb one leaf value
        key = next(iter(wrong))
        if isinstance(wrong[key], list):
            wrong[key] = wrong[key] + [999]
        else:
            wrong[key] = 999999
        bad = evaluate_math_task_oracle(task["oracle_type"], payload, wrong)
        assert bad["is_correct"] is False


@pytest.mark.parametrize("level", [1, 2, 3])
def test_radical_invariants(level):
    task = load_tasks()[f"ce115_calc_radical_simplification_l{level}"]
    for seed in SEEDS:
        payload = sample_task_parameters(task, seed)["oracle_payload"]
        radicand = payload["radicand"]
        outer = payload.get("outer_coefficient", 1)
        assert radicand > 1 and isqrt(radicand) ** 2 != radicand, "radicand must not be a perfect square"
        expected = evaluate_math_task_oracle(task["oracle_type"], payload, None)["expected_answer"]
        k, m = expected["coefficient"], expected["radicand"]
        assert k > 0 and m > 1 and _is_square_free(m)
        assert (k // outer) ** 2 * m == radicand and k % outer == 0


@pytest.mark.parametrize("level", [1, 2, 3])
def test_rational_invariants(level):
    task = load_tasks()[f"ce115_calc_exact_rational_expression_l{level}"]
    for seed in SEEDS:
        payload = sample_task_parameters(task, seed)["oracle_payload"]
        assert len(payload["products"]) >= 2
        total = sum(p["sign"] * Fraction(p["left"]) * Fraction(p["right"]) for p in payload["products"])
        assert total != 0
        expected = evaluate_math_task_oracle(task["oracle_type"], payload, None)["expected_answer"]
        value = expected["value"]
        assert isinstance(value, str) and "." not in value
        assert Fraction(value) == total
        if "/" in value:
            p, q = value.split("/")
            from math import gcd
            assert int(q) > 1 and gcd(abs(int(p)), int(q)) == 1


@pytest.mark.parametrize("level", [1, 2, 3])
def test_polynomial_division_identity(level):
    task = load_tasks()[f"ce115_calc_polynomial_division_l{level}"]
    for seed in SEEDS:
        payload = sample_task_parameters(task, seed)["oracle_payload"]
        divisor = payload["divisor_coefficients"]
        assert len(divisor) == 2 and divisor[0] != 0
        expected = evaluate_math_task_oracle(task["oracle_type"], payload, None)["expected_answer"]
        quotient = [Fraction(str(v)) for v in expected["quotient_coefficients"]]
        remainder = [Fraction(str(v)) for v in expected["remainder_coefficients"]]
        assert len(remainder) == 1, "remainder degree must be lower than divisor degree"
        # reconstruct dividend = divisor * quotient + remainder
        product = [Fraction(0)] * (len(quotient) + 1)
        for i, q in enumerate(quotient):
            product[i] += q * divisor[0]
            product[i + 1] += q * divisor[1]
        product[-1] += remainder[0]
        assert product == [Fraction(c) for c in payload["dividend_coefficients"]]
        for value in expected["quotient_coefficients"] + expected["remainder_coefficients"]:
            assert _canonical_ok(value)


@pytest.mark.parametrize("level", [1, 2, 3])
def test_factor_roots_invariants(level):
    task = load_tasks()[f"ce115_calc_polynomial_factor_roots_l{level}"]
    for seed in SEEDS:
        payload = sample_task_parameters(task, seed)["oracle_payload"]
        a, b, c = payload["quadratic_coefficients"]
        assert a != 0
        expected = evaluate_math_task_oracle(task["oracle_type"], payload, None)["expected_answer"]
        roots = [Fraction(str(v)) for v in expected["roots"]]
        assert len(roots) == 2 and roots[0] < roots[1], "two distinct roots in ascending order"
        for root in roots:
            assert a * root * root + b * root + c == 0
        for value in expected["roots"]:
            assert _canonical_ok(value)


# ---------------------------------------------------------------------------
# Golden cases anchored to the four source questions (development set)
# ---------------------------------------------------------------------------

def test_golden_radical_504():
    verdict = evaluate_math_task_oracle("radical_simplification", {"radicand": 504}, {"coefficient": 6, "radicand": 14})
    assert verdict["is_correct"] is True


def test_golden_rational_expression():
    payload = {"products": [
        {"sign": 1, "left": "2.45", "right": "98.7"},
        {"sign": -1, "left": "-0.55", "right": "98.7"},
    ]}
    verdict = evaluate_math_task_oracle("exact_rational_expression", payload, {"value": "2961/10"})
    assert verdict["is_correct"] is True  # 3 * 98.7 = 296.1


def test_golden_polynomial_division():
    payload = {"dividend_coefficients": [4, -3, -5], "divisor_coefficients": [1, 2]}
    expected = {"quotient_coefficients": [4, -11], "remainder_coefficients": [17]}
    verdict = evaluate_math_task_oracle("polynomial_division_general", payload, expected)
    assert verdict["is_correct"] is True


def test_golden_factor_roots():
    # 2x(x+7) - 10(x+7) = 0  ->  2x^2 + 4x - 70 = 0  ->  roots -7 and 5
    payload = {"quadratic_coefficients": [2, 4, -70]}
    verdict = evaluate_math_task_oracle("polynomial_factor_roots", payload, {"roots": [-7, 5]})
    assert verdict["is_correct"] is True


# ---------------------------------------------------------------------------
# Oracle fail-closed behaviour
# ---------------------------------------------------------------------------

def test_oracle_fails_closed_on_degenerate_payloads():
    assert evaluate_math_task_oracle("radical_simplification", {"radicand": 36}, None)["error"]  # perfect square
    assert evaluate_math_task_oracle("exact_rational_expression", {"products": []}, None)["error"]
    assert evaluate_math_task_oracle("polynomial_division_general", {"dividend_coefficients": [1, 2], "divisor_coefficients": [0, 1]}, None)["error"]
    assert evaluate_math_task_oracle("polynomial_factor_roots", {"quadratic_coefficients": [1, 2, 1]}, None)["error"]  # repeated root
    assert evaluate_math_task_oracle("polynomial_factor_roots", {"quadratic_coefficients": [1, 0, 1]}, None)["error"]  # complex roots
    assert evaluate_math_task_oracle("unknown_type_xyz", {}, None)["error"] == "unsupported oracle_type"


# ---------------------------------------------------------------------------
# Contracts, neutral statements, leakage
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("oracle_type", ["radical_simplification", "exact_rational_expression",
                                         "polynomial_division_general", "polynomial_factor_roots"])
def test_contract_and_statement_registered(oracle_type):
    assert oracle_type in CONTRACTS
    assert oracle_type in NEUTRAL_TASK_STATEMENTS
    contract = render_answer_contract({"oracle_type": oracle_type})
    assert "Required return schema" in contract
    assert "Write only complete Python source code" in contract
    assert "def generate(level=1, **kwargs):" in contract


@pytest.mark.parametrize("task_id", FAMILY_TASK_IDS)
def test_no_expected_answer_leakage_in_prompt_text(task_id):
    task = load_tasks()[task_id]
    payload = sample_task_parameters(task, SEEDS[0])["oracle_payload"]
    expected = evaluate_math_task_oracle(task["oracle_type"], payload, None)["expected_answer"]
    contract = render_answer_contract(task, payload)
    assert json.dumps(expected) not in contract
    statement = NEUTRAL_TASK_STATEMENTS[task["oracle_type"]]
    # neutral statements must not carry any fixed numbers from source questions
    for token in ("504", "98.7", "2.45", "0.55", "4x", "x+7", "296"):
        assert token not in statement


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

def test_routing_direct_alias_for_new_families(monkeypatch):
    import core.skill_policies.registry as reg
    reg.refresh_registry()
    available = reg.list_registered_skill_ids()

    import difflib
    def no_fuzzy(*args, **kwargs):
        raise RuntimeError("fuzzy fallback must not be used")
    monkeypatch.setattr(difflib, "get_close_matches", no_fuzzy)

    for alias, target in ROUTING_EXPECTATIONS.items():
        assert reg.normalize_skill_id(alias, available) == target
