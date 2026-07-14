# -*- coding: utf-8 -*-
from typing import Any, Mapping

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

CONTRACTS: Mapping[str, str] = {
    "polynomial_division_exact": POLYNOMIAL_DIVISION_CONTRACT,
    "rpm_circumference_kph": RPM_CIRCUMFERENCE_CONTRACT,
    "largest_proper_divisor_logic": LARGEST_PROPER_DIVISOR_CONTRACT,
    "alternating_sequence_threshold": ALTERNATING_SEQUENCE_CONTRACT,
}


def render_answer_contract(task_metadata: Mapping[str, Any]) -> str:
    if not isinstance(task_metadata, Mapping):
        raise ValueError("ANSWER_CONTRACT_NOT_FOUND")
    oracle_type = task_metadata.get("oracle_type")
    if not oracle_type or oracle_type not in CONTRACTS:
        raise ValueError("ANSWER_CONTRACT_NOT_FOUND")
    return f"\n\n# Answer Schema Contract\n{CONTRACTS[oracle_type]}\n"
