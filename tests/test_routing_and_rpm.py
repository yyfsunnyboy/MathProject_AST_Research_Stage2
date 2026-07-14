# -*- coding: utf-8 -*-
import json
import os
import sys
from pathlib import Path
from fractions import Fraction

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import core.skill_policies.registry as reg
from agent_tools.finals_rebuild.math_boundary_pilot import classify_response, frozen_payloads
from agent_tools.finals_rebuild.math_task_sampler import sample_task_parameters
from agent_tools.finals_rebuild.math_task_oracles import evaluate_math_task_oracle

MANIFEST = Path(__file__).parent / "finals_rebuild" / "fixtures" / "math_generation_tasks_ce115_pilot.jsonl"


# =====================================================================
# ROUTING TESTS (Direct Manifest-Alias Resolution)
# =====================================================================

def test_routing_direct_alias_table_resolution():
    """Verify that the 4 unique aliases resolve directly via alias table mappings

    without relying on fuzzy edit-distance or substring fallback.
    """
    reg.refresh_registry()

    # Prove they exist in the direct lookup table
    assert "polynomial_division_quotient_remainder" in reg._ALIAS_TABLE
    assert reg._ALIAS_TABLE["polynomial_division_quotient_remainder"] == "jh_數學2上_FourArithmeticOperationsOfPolynomial"

    assert "rpm_circumference_to_kph" in reg._ALIAS_TABLE
    assert reg._ALIAS_TABLE["rpm_circumference_to_kph"] == "jh_數學1上_FourArithmeticOperationsOfNumbers"

    assert "largest_proper_divisor_reasoning" in reg._ALIAS_TABLE
    assert reg._ALIAS_TABLE["largest_proper_divisor_reasoning"] == "jh_數學1上_FourArithmeticOperationsOfIntegers"

    assert "alternating_training_progression_threshold" in reg._ALIAS_TABLE
    assert reg._ALIAS_TABLE["alternating_training_progression_threshold"] == "jh_數學1上_FourArithmeticOperationsOfIntegers"


def test_routing_normalization_behavior():
    """Verify standard normalize_skill_id contract."""
    reg.refresh_registry()
    available = reg.list_registered_skill_ids()

    assert reg.normalize_skill_id("polynomial_division_quotient_remainder", available) == "jh_數學2上_FourArithmeticOperationsOfPolynomial"
    assert reg.normalize_skill_id("rpm_circumference_to_kph", available) == "jh_數學1上_FourArithmeticOperationsOfNumbers"
    assert reg.normalize_skill_id("largest_proper_divisor_reasoning", available) == "jh_數學1上_FourArithmeticOperationsOfIntegers"
    assert reg.normalize_skill_id("alternating_training_progression_threshold", available) == "jh_數學1上_FourArithmeticOperationsOfIntegers"

    # Unregistered random skill ID should resolve to "Unknown"
    assert reg.normalize_skill_id("random_unknown_skill_id_123", available) == "Unknown"

    # Existing aliases resolve correctly
    assert reg.normalize_skill_id("Fractions", available) == "jh_數學1上_FourArithmeticOperationsOfNumbers"
    assert reg.normalize_skill_id("Arithmetic", available) == "jh_數學1上_FourArithmeticOperationsOfIntegers"


def test_routing_exact_match_no_fuzzy_fallback(monkeypatch):
    """Verify exact match resolves via direct alias table without triggering fuzzy matching."""
    reg.refresh_registry()
    available = reg.list_registered_skill_ids()

    # We mock difflib.get_close_matches to raise an error.
    import difflib
    def mock_get_close_matches(*args, **kwargs):
        raise RuntimeError("Fuzzy edit-distance fallback was triggered!")

    monkeypatch.setattr(difflib, "get_close_matches", mock_get_close_matches)

    # These should resolve via alias table lookup directly
    assert reg.normalize_skill_id("polynomial_division_quotient_remainder", available) == "jh_數學2上_FourArithmeticOperationsOfPolynomial"
    assert reg.normalize_skill_id("rpm_circumference_to_kph", available) == "jh_數學1上_FourArithmeticOperationsOfNumbers"
    assert reg.normalize_skill_id("largest_proper_divisor_reasoning", available) == "jh_數學1上_FourArithmeticOperationsOfIntegers"
    assert reg.normalize_skill_id("alternating_training_progression_threshold", available) == "jh_數學1上_FourArithmeticOperationsOfIntegers"


# =====================================================================
# RPM GOLDEN PATH helper functions
# =====================================================================

def load_pilot_tasks() -> list[dict]:
    return [json.loads(line) for line in MANIFEST.read_text(encoding="utf-8").splitlines() if line.strip()]


def compute_expected_coefficient(circumference_cm: int, rpm: int = 1) -> Fraction:
    """Exact rational conversion from rpm and circumference_cm to km/h coefficient."""
    return Fraction(rpm * circumference_cm * 60, 100000)


def generate_source_code(circumference_cm, coefficient_val, unit_val="km/h", omit_coefficient=False, omit_unit=False):
    """Generate raw Python response string containing the generate function."""
    payload_str = json.dumps({"circumference_cm": circumference_cm, "rpm_symbol": "rpm", "requested_unit": "km/h"})

    if omit_coefficient:
        correct_answer_str = f'{{"unit": "{unit_val}"}}'
    elif omit_unit:
        if isinstance(coefficient_val, str):
            correct_answer_str = f'{{"coefficient": "{coefficient_val}"}}'
        else:
            correct_answer_str = f'{{"coefficient": {coefficient_val}}}'
    else:
        if isinstance(coefficient_val, str):
            coef_repr = f'"{coefficient_val}"'
        else:
            coef_repr = str(coefficient_val)
        correct_answer_str = f'{{"coefficient": {coef_repr}, "unit": "{unit_val}"}}'

    # Wrap inside Markdown code fences to test the full extraction chain as well
    return f"""```python
def generate(level=1, **kwargs):
    return {{
        "question_text": "A wheel with circumference {circumference_cm} cm has rotational speed...",
        "correct_answer": {correct_answer_str},
        "oracle_payload": {payload_str}
    }}
```"""


# =====================================================================
# SPEC_ASSERTION_TESTS
# =====================================================================

def test_rpm_spec_assertion_l1_and_l2():
    """SPEC_ASSERTION_TEST: Verify that correct RPM outputs pass the complete production chain.

    Fixture -> Source -> Extraction -> Sandbox Execution -> Oracle Evaluator -> Passed classification.
    """
    tasks = load_pilot_tasks()
    task_l1 = next(t for t in tasks if t["task_id"] == "ce115_q24_rotation_speed_conversion_l1")
    task_l2 = next(t for t in tasks if t["task_id"] == "ce115_q24_rotation_speed_conversion_l2")

    # 1. L1 exact canonical fraction
    frozen_l1 = sample_task_parameters(task_l1, 2026071301)
    circumference_cm = frozen_l1["oracle_payload"]["circumference_cm"]

    expected_fraction = compute_expected_coefficient(circumference_cm, rpm=1)
    expected_coef_str = str(expected_fraction.numerator) if expected_fraction.denominator == 1 else f"{expected_fraction.numerator}/{expected_fraction.denominator}"

    raw_response_l1 = generate_source_code(circumference_cm, expected_coef_str)
    outcome, source, details = classify_response(raw_response_l1, frozen_l1, task_l1)
    assert outcome == "passed", f"L1 failed with: {details}"

    # 2. L2 exact canonical fraction
    frozen_l2 = sample_task_parameters(task_l2, 2026071302)
    circumference_cm_l2 = frozen_l2["oracle_payload"]["circumference_cm"]

    expected_fraction_l2 = compute_expected_coefficient(circumference_cm_l2, rpm=1)
    expected_coef_str_l2 = str(expected_fraction_l2.numerator) if expected_fraction_l2.denominator == 1 else f"{expected_fraction_l2.numerator}/{expected_fraction_l2.denominator}"

    raw_response_l2 = generate_source_code(circumference_cm_l2, expected_coef_str_l2)
    outcome, source, details = classify_response(raw_response_l2, frozen_l2, task_l2)
    assert outcome == "passed", f"L2 failed with: {details}"


def test_rpm_spec_assertion_reducible_fraction():
    """SPEC_ASSERTION_TEST: Verify fully simplified reducible fraction results."""
    tasks = load_pilot_tasks()
    task_l1 = next(t for t in tasks if t["task_id"] == "ce115_q24_rotation_speed_conversion_l1")

    # 3. Reducible result must be fully simplified.
    # We choose a valid parameter within L1 schema constraints (e.g. circumference_cm = 100)
    # expected_fraction = 100 * 60 / 100000 = 3/50 (already simplified)
    frozen = {"task_id": task_l1["task_id"], "oracle_payload": {"circumference_cm": 100, "rpm_symbol": "rpm", "requested_unit": "km/h"}}

    raw_response = generate_source_code(100, "3/50")
    outcome, _, details = classify_response(raw_response, frozen, task_l1)
    assert outcome == "passed", f"Reducible simplified fraction failed: {details}"


# =====================================================================
# CHARACTERIZATION_TESTS (Recording Actual Evaluator Behavior)
# =====================================================================

def test_characterization_rpm_coefficient_types():
    """CHARACTERIZATION_TEST: Record evaluator behavior when coefficient is numeric instead of string."""
    tasks = load_pilot_tasks()
    task_l1 = next(t for t in tasks if t["task_id"] == "ce115_q24_rotation_speed_conversion_l1")
    frozen = {"task_id": task_l1["task_id"], "oracle_payload": {"circumference_cm": 150, "rpm_symbol": "rpm", "requested_unit": "km/h"}}

    # If coefficient is float 0.09
    raw_float = generate_source_code(150, 0.09)
    outcome_float, _, _ = classify_response(raw_float, frozen, task_l1)
    # Record actual behavior: fails with answer_incorrect
    assert outcome_float == "answer_incorrect"


def test_characterization_rpm_unit_mismatch():
    """CHARACTERIZATION_TEST: Record evaluator behavior when unit is not km/h."""
    tasks = load_pilot_tasks()
    task_l1 = next(t for t in tasks if t["task_id"] == "ce115_q24_rotation_speed_conversion_l1")
    frozen = {"task_id": task_l1["task_id"], "oracle_payload": {"circumference_cm": 150, "rpm_symbol": "rpm", "requested_unit": "km/h"}}

    # Non km/h unit
    raw_bad_unit = generate_source_code(150, "9/100", unit_val="m/s")
    outcome_bad_unit, _, _ = classify_response(raw_bad_unit, frozen, task_l1)
    # Record actual behavior: fails with answer_incorrect
    assert outcome_bad_unit == "answer_incorrect"


def test_characterization_rpm_non_canonical_fraction():
    """CHARACTERIZATION_TEST: Record evaluator behavior for mathematically equivalent but non-canonical strings."""
    tasks = load_pilot_tasks()
    task_l1 = next(t for t in tasks if t["task_id"] == "ce115_q24_rotation_speed_conversion_l1")
    frozen = {"task_id": task_l1["task_id"], "oracle_payload": {"circumference_cm": 150, "rpm_symbol": "rpm", "requested_unit": "km/h"}}

    # equivalent but not canonical (18/200 vs 9/100)
    raw_non_canonical = generate_source_code(150, "18/200")
    outcome_non_canonical, _, _ = classify_response(raw_non_canonical, frozen, task_l1)
    # Record actual behavior: fails with answer_incorrect
    assert outcome_non_canonical == "answer_incorrect"


def test_characterization_rpm_missing_keys():
    """CHARACTERIZATION_TEST: Record evaluator behavior when keys are missing from correct_answer dict."""
    tasks = load_pilot_tasks()
    task_l1 = next(t for t in tasks if t["task_id"] == "ce115_q24_rotation_speed_conversion_l1")
    frozen = {"task_id": task_l1["task_id"], "oracle_payload": {"circumference_cm": 150, "rpm_symbol": "rpm", "requested_unit": "km/h"}}

    # missing coefficient
    raw_missing_coef = generate_source_code(150, "9/100", omit_coefficient=True)
    outcome_missing_coef, _, _ = classify_response(raw_missing_coef, frozen, task_l1)
    # Record actual behavior: fails with answer_incorrect
    assert outcome_missing_coef == "answer_incorrect"

    # missing unit
    raw_missing_unit = generate_source_code(150, "9/100", omit_unit=True)
    outcome_missing_unit, _, _ = classify_response(raw_missing_unit, frozen, task_l1)
    # Record actual behavior: fails with answer_incorrect
    assert outcome_missing_unit == "answer_incorrect"
