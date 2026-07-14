# -*- coding: utf-8 -*-
import json
from typing import Any, Mapping

GENERATION_INSTRUCTIONS = """Write only complete Python source code.
Do not use Markdown fences, prose, explanations, or prompt echoes.
Implement exactly one function:

def generate(level=1, **kwargs):

`generate()` must return exactly the three-key dictionary specified below."""

OVERRIDE_STATEMENT = """Return exactly these three top-level keys and no others:
`question_text`, `correct_answer`, and `oracle_payload`.
Do not return `answer`, `mode`, or any additional key.
The task-specific `correct_answer` schema below supersedes any earlier generic `correct_answer: str` instruction."""

NEUTRAL_TASK_STATEMENTS = {
    "polynomial_division_exact": """# Task Specification: Polynomial Division
- Task Name: Polynomial Division
- Input Parameters: `dividend_coefficients` (coefficients of the dividend polynomial) and `divisor_root` (the root of the linear divisor).
- Output: `question_text` must ask the user to divide the dividend polynomial by the linear divisor (i.e. x - divisor_root) to find the quotient and remainder.
- Calculation: `correct_answer` must calculate and return the quotient coefficients and remainder.
- Data Contract: `oracle_payload` must return exactly the input parameters.""",

    "rpm_circumference_kph": """# Task Specification: Rotation Speed Conversion
- Task Name: Rotation Speed Conversion
- Input Parameters: `circumference_cm` (wheel circumference in cm), `rpm_symbol` (symbol for rpm), and `requested_unit` ("km/h").
- Output: `question_text` must ask to calculate the linear speed in km/h for 1 RPM.
- Calculation: `correct_answer` must calculate the speed coefficient for 1 RPM as a reduced fraction string, and the unit "km/h".
- Data Contract: `oracle_payload` must return exactly the input parameters.""",

    "largest_proper_divisor_logic": """# Task Specification: Largest Proper Divisor Logic Reasoning
- Task Name: Largest Proper Divisor Logic Reasoning
- Input Parameters: `largest_proper_divisors` (mapping from labels to largest proper divisors) and `claims` (list of necessity claims).
- Output: `question_text` must present the claims and ask whether each necessity claim is logically true or false.
- Calculation: `correct_answer` must evaluate and return the boolean truth value (True or False) of each claim in the exact frozen order.
- Data Contract: `oracle_payload` must return exactly the input parameters.""",

    "radical_simplification": """# Task Specification: Radical Simplification
- Task Name: Radical Simplification
- Input Parameters: `radicand` (positive integer under the square root) and optional `outer_coefficient` (positive integer multiplier outside the root; treat as 1 when absent).
- Output: `question_text` must ask to rewrite outer_coefficient * sqrt(radicand) in simplest radical form coefficient * sqrt(square_free_radicand).
- Calculation: `correct_answer` must return the simplified integer coefficient and the square-free radicand.
- Data Contract: `oracle_payload` must return exactly the input parameters.""",

    "exact_rational_expression": """# Task Specification: Exact Rational Expression Evaluation
- Task Name: Exact Rational Expression Evaluation
- Input Parameters: `products` (ordered list of terms; each term has `sign` (1 or -1), `left` and `right` exact decimal strings). The expression value is the sum over terms of sign * left * right.
- Output: `question_text` must present the arithmetic expression built from these terms.
- Calculation: `correct_answer` must evaluate the expression with exact rational arithmetic (no floats) and return the canonical value string.
- Data Contract: `oracle_payload` must return exactly the input parameters.""",

    "polynomial_division_general": """# Task Specification: Polynomial Division (General Linear Divisor)
- Task Name: Polynomial Division with Quotient and Remainder
- Input Parameters: `dividend_coefficients` (highest degree first) and `divisor_coefficients` (two values: leading and constant of the linear divisor).
- Output: `question_text` must ask to divide the dividend polynomial by the linear divisor and report the quotient and the remainder.
- Calculation: `correct_answer` must return the quotient coefficients (highest degree first) and the remainder coefficients computed with exact arithmetic.
- Data Contract: `oracle_payload` must return exactly the input parameters.""",

    "polynomial_factor_roots": """# Task Specification: Polynomial Factorization and Roots
- Task Name: Quadratic Factorization and Roots
- Input Parameters: `quadratic_coefficients` (three integers a, b, c of a x^2 + b x + c, highest degree first).
- Output: `question_text` must ask to factor the quadratic (for example by extracting a common factor) and find both roots.
- Calculation: `correct_answer` must return the two distinct exact roots in ascending numeric order.
- Data Contract: `oracle_payload` must return exactly the input parameters.""",

    "alternating_sequence_threshold": """# Task Specification: Alternating Sequence Threshold Crossing
- Task Name: Alternating Sequence Threshold Crossing
- Input Parameters: `track_length_m` (track length in meters), `initial_first_day_laps` (laps on first training day), `same_week_increment_laps` (lap increment), `threshold_km` (distance threshold in km), `specified_week` (specified week number), `specified_day` (specified day of week), and `day_labels` (list of training days in a week).
- Output: `question_text` must ask to find the laps completed in the specified week/day, and the week and day when total cumulative distance first exceeds the threshold.
- Calculation: `correct_answer` must compute the specified session laps, the first exceed week, and the first exceed day.
- Data Contract: `oracle_payload` must return exactly the input parameters."""
}

POLYNOMIAL_DIVISION_CONTRACT = """Required return schema:
{
  "question_text": str,
  "correct_answer": {
      "quotient_coefficients": list[int | str],  # coefficients of the quotient (integers or fraction strings "p/q")
      "remainder": int | str                    # remainder of the division (integer or fraction string "p/q")
  },
  "oracle_payload": dict
}
- Formatting rules: Output integers directly, or irreducible fraction strings in the format "p/q" if fractional. Do not use float values.
- Equality: Exact matching via dictionary structure. No tolerance."""

RPM_CIRCUMFERENCE_CONTRACT = """Required return schema:
{
  "question_text": str,
  "correct_answer": {
      "coefficient": str,  # speed coefficient for 1 rpm in the format "p/q" (reduced fraction string, or "n" if denominator is 1)
      "unit": str          # must be exactly "km/h"
  },
  "oracle_payload": dict
}
- Formatting rules: Reduce the fraction completely. Output integer if the denominator is 1.
- Equality: Exact dictionary match. No tolerance."""

LARGEST_PROPER_DIVISOR_CONTRACT = """Required return schema:
{
  "question_text": str,
  "correct_answer": {
      "claims": list[bool]  # boolean list indicating the truth value of the necessity claims in the frozen order
  },
  "oracle_payload": dict
}
- Formatting rules: boolean values (True or False) only.
- Equality: Exact dictionary match. No tolerance."""

ALTERNATING_SEQUENCE_CONTRACT = """Required return schema:
{
  "question_text": str,
  "correct_answer": {
      "specified_session_laps": int,  # laps completed in the specified week and day
      "first_exceed_week": int,        # 1-indexed week number when the total distance first exceeds threshold_km
      "first_exceed_day": str         # day label of the first exceed session
  },
  "oracle_payload": dict
}
- Formatting rules: match day label strings exactly from the list provided.
- Equality: Exact dictionary match. No tolerance."""

RADICAL_SIMPLIFICATION_CONTRACT = """Required return schema:
{
  "question_text": str,
  "correct_answer": {
      "coefficient": int,  # simplified positive integer coefficient outside the square root
      "radicand": int      # square-free integer remaining under the square root (> 1)
  },
  "oracle_payload": dict
}
- Formatting rules: integers only; the radicand must be square-free; do not use float values.
- Equality: Exact dictionary match. No tolerance."""

EXACT_RATIONAL_EXPRESSION_CONTRACT = """Required return schema:
{
  "question_text": str,
  "correct_answer": {
      "value": str  # canonical exact value: integer string, or irreducible "p/q" with positive denominator
  },
  "oracle_payload": dict
}
- Formatting rules: reduce completely; output the integer string if the denominator is 1; never use decimal or float approximations.
- Equality: Exact dictionary match. No tolerance."""

POLYNOMIAL_DIVISION_GENERAL_CONTRACT = """Required return schema:
{
  "question_text": str,
  "correct_answer": {
      "quotient_coefficients": list[int | str],   # highest degree first; integers, or irreducible fraction strings "p/q"
      "remainder_coefficients": list[int | str]   # coefficients of the remainder (degree < divisor degree; one value for a linear divisor)
  },
  "oracle_payload": dict
}
- Formatting rules: exact arithmetic only; integers directly, irreducible "p/q" strings when fractional; no float values.
- Equality: Exact dictionary match. No tolerance."""

POLYNOMIAL_FACTOR_ROOTS_CONTRACT = """Required return schema:
{
  "question_text": str,
  "correct_answer": {
      "roots": list[int | str]  # the two distinct roots in ascending numeric order; integers, or irreducible fraction strings "p/q"
  },
  "oracle_payload": dict
}
- Formatting rules: ascending order; exact values only; irreducible "p/q" with positive denominator when fractional; no float values.
- Equality: Exact dictionary match. No tolerance."""

CONTRACTS: Mapping[str, str] = {
    "radical_simplification": RADICAL_SIMPLIFICATION_CONTRACT,
    "exact_rational_expression": EXACT_RATIONAL_EXPRESSION_CONTRACT,
    "polynomial_division_general": POLYNOMIAL_DIVISION_GENERAL_CONTRACT,
    "polynomial_factor_roots": POLYNOMIAL_FACTOR_ROOTS_CONTRACT,
    "polynomial_division_exact": POLYNOMIAL_DIVISION_CONTRACT,
    "rpm_circumference_kph": RPM_CIRCUMFERENCE_CONTRACT,
    "largest_proper_divisor_logic": LARGEST_PROPER_DIVISOR_CONTRACT,
    "alternating_sequence_threshold": ALTERNATING_SEQUENCE_CONTRACT,
}


def render_answer_contract(task_metadata: Mapping[str, Any], frozen_payload: Mapping[str, Any] | None = None) -> str:
    if not isinstance(task_metadata, Mapping):
        raise ValueError("ANSWER_CONTRACT_NOT_FOUND")
    oracle_type = task_metadata.get("oracle_type")
    if not oracle_type or oracle_type not in CONTRACTS:
        raise ValueError("ANSWER_CONTRACT_NOT_FOUND")

    parts = []

    # 1. Neutral task statement
    parts.append(NEUTRAL_TASK_STATEMENTS[oracle_type])

    # 2. Frozen sampled parameters
    if frozen_payload is not None:
        parts.append(f"Frozen sampled parameters:\n{json.dumps(frozen_payload, sort_keys=True)}\n\n`oracle_payload` must exactly equal the frozen sampled parameters above.")

    # 3. Generation output instructions (entry point + output format)
    parts.append(GENERATION_INSTRUCTIONS)

    # 4. Override statement (B1)
    parts.append(OVERRIDE_STATEMENT)

    # 5. Task-specific contract
    parts.append(CONTRACTS[oracle_type])

    return "\n\n" + "\n\n".join(parts) + "\n"
