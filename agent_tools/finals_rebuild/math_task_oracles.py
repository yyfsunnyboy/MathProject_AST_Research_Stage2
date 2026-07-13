"""Deterministic, generator-independent oracles for the CE115 pilot tasks."""
from __future__ import annotations

from fractions import Fraction
from math import isqrt
from typing import Any, Callable


def _result(oracle_type: str, expected: Any, submitted: Any, error: str | None = None) -> dict[str, Any]:
    return {"oracle_type": oracle_type, "is_correct": error is None and submitted == expected,
            "expected_answer": expected, "submitted_answer": submitted, "error": error}


def _integer(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    return value


def evaluate_polynomial_division(oracle_payload: dict[str, Any], submitted_answer: Any) -> dict[str, Any]:
    oracle_type = "polynomial_division_exact"
    try:
        coefficients = oracle_payload["dividend_coefficients"]
        root = _integer(oracle_payload["divisor_root"], "divisor_root")
        if not isinstance(coefficients, list) or len(coefficients) != 3:
            raise ValueError("dividend_coefficients must contain three integers")
        values = [_integer(value, "coefficient") for value in coefficients]
        if values[0] == 0:
            raise ValueError("dividend must be degree two")
        quotient_leading = values[0]
        quotient_constant = values[1] + root * quotient_leading
        remainder = values[2] + root * quotient_constant
        expected = {"quotient_coefficients": [quotient_leading, quotient_constant], "remainder": remainder}
        return _result(oracle_type, expected, submitted_answer)
    except (KeyError, ValueError, TypeError) as exc:
        return _result(oracle_type, None, submitted_answer, str(exc))


def _largest_proper_divisor(number: int) -> int:
    if number <= 1:
        raise ValueError("number must be greater than one")
    for factor in range(2, isqrt(number) + 1):
        if number % factor == 0:
            return number // factor
    return 1


def _smallest_prime_factor(number: int) -> int:
    for factor in range(2, isqrt(number) + 1):
        if number % factor == 0:
            return factor
    return number


def evaluate_largest_proper_divisor(oracle_payload: dict[str, Any], submitted_answer: Any) -> dict[str, Any]:
    oracle_type = "largest_proper_divisor_logic"
    try:
        declared = oracle_payload["largest_proper_divisors"]
        claims = oracle_payload["claims"]
        if not isinstance(declared, dict) or not isinstance(claims, list) or not claims:
            raise ValueError("largest_proper_divisors and non-empty claims are required")
        expected_claims = []
        for claim in claims:
            subject = claim["subject"]
            candidate = _integer(claim["candidate_factor"], "claim.candidate_factor")
            if claim.get("asks_necessity") is not True:
                raise ValueError("claim.asks_necessity must be true")
            largest = _integer(declared[subject], "largest_proper_divisor")
            if largest <= 1:
                raise ValueError("largest proper divisor must exceed one")
            # If L is the largest proper divisor of n, n = L * p where p is
            # prime and p cannot exceed the smallest prime factor of L.
            possible_numbers = [largest * prime for prime in range(2, _smallest_prime_factor(largest) + 1)
                                if _smallest_prime_factor(prime) == prime]
            if not possible_numbers or any(_largest_proper_divisor(number) != largest for number in possible_numbers):
                raise ValueError("largest proper divisor is inconsistent")
            expected_claims.append(all(number % candidate == 0 for number in possible_numbers))
        return _result(oracle_type, {"claims": expected_claims}, submitted_answer)
    except (KeyError, ValueError, TypeError) as exc:
        return _result(oracle_type, None, submitted_answer, str(exc))


def _fraction_text(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def evaluate_rpm_circumference_kph(oracle_payload: dict[str, Any], submitted_answer: Any) -> dict[str, Any]:
    oracle_type = "rpm_circumference_kph"
    try:
        circumference = _integer(oracle_payload["circumference_cm"], "circumference_cm")
        if circumference <= 0 or oracle_payload["requested_unit"] != "km/h":
            raise ValueError("positive circumference_cm and km/h are required")
        coefficient = Fraction(60 * circumference, 100000)
        expected = {"coefficient": _fraction_text(coefficient), "unit": "km/h"}
        return _result(oracle_type, expected, submitted_answer)
    except (KeyError, ValueError, TypeError) as exc:
        return _result(oracle_type, None, submitted_answer, str(exc))


def evaluate_alternating_sequence_threshold(oracle_payload: dict[str, Any], submitted_answer: Any) -> dict[str, Any]:
    oracle_type = "alternating_sequence_threshold"
    try:
        track_length = _integer(oracle_payload["track_length_m"], "track_length_m")
        initial = _integer(oracle_payload["initial_first_day_laps"], "initial_first_day_laps")
        increment = _integer(oracle_payload["same_week_increment_laps"], "same_week_increment_laps")
        threshold_km = _integer(oracle_payload["threshold_km"], "threshold_km")
        specified_week = _integer(oracle_payload["specified_week"], "specified_week")
        labels = oracle_payload["day_labels"]
        if min(track_length, initial, increment, threshold_km, specified_week) <= 0 or not isinstance(labels, list) or not labels:
            raise ValueError("positive values and non-empty day_labels are required")
        sessions_per_week = len(labels)
        specified_day = oracle_payload["specified_day"]
        if specified_day not in labels:
            raise ValueError("specified_day must be in day_labels")
        specified_day_index = labels.index(specified_day)
        # The first session each week repeats the previous week's final session;
        # only the second session increases by the stated within-week amount.
        specified_session_laps = initial + increment * (specified_week - 1 + specified_day_index)
        required_laps = Fraction(threshold_km * 1000, track_length)
        session_index = 0
        while True:
            week_index, day_index = divmod(session_index, sessions_per_week)
            laps = initial + increment * (week_index + day_index)
            if Fraction(laps, 1) > required_laps:
                break
            session_index += 1
        expected = {
            "specified_session_laps": specified_session_laps,
            "first_exceed_week": session_index // sessions_per_week + 1,
            "first_exceed_day": labels[session_index % sessions_per_week],
        }
        return _result(oracle_type, expected, submitted_answer)
    except (KeyError, ValueError, TypeError) as exc:
        return _result(oracle_type, None, submitted_answer, str(exc))


_DISPATCH: dict[str, Callable[[dict[str, Any], Any], dict[str, Any]]] = {
    "polynomial_division_exact": evaluate_polynomial_division,
    "largest_proper_divisor_logic": evaluate_largest_proper_divisor,
    "rpm_circumference_kph": evaluate_rpm_circumference_kph,
    "alternating_sequence_threshold": evaluate_alternating_sequence_threshold,
}


def evaluate_math_task_oracle(oracle_type: str, oracle_payload: dict[str, Any], submitted_answer: Any) -> dict[str, Any]:
    """Evaluate an answer from immutable task data without importing generator code."""
    evaluator = _DISPATCH.get(oracle_type)
    if evaluator is None:
        return _result(oracle_type, None, submitted_answer, "unsupported oracle_type")
    return evaluator(oracle_payload, submitted_answer)
