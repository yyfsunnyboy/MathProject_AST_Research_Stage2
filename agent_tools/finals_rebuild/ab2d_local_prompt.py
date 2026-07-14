"""Deterministic, task-local prompt assembly for the Ab2d-local experiment.

This module is deliberately not wired into production routing or any runner.
It provides a compact experimental treatment whose inputs are explicit and
whose output can be snapshotted byte-for-byte.
"""
from __future__ import annotations

import json
import re
from typing import Any, Mapping


MATH_CORE_SCAFFOLD = """Write only complete Python source code.
No Markdown fences, prose, explanations, or prompt echoes.
Implement exactly:
def generate(level=1, **kwargs):
Return exactly these top-level keys and no others:
question_text
correct_answer
oracle_payload
oracle_payload must exactly equal the frozen parameters below.
correct_answer must follow the task-specific schema.
Do not use input(), file I/O, network, subprocess, os.system, eval, or exec.
Do not use float when exact arithmetic is required by the task contract.
Make one complete first attempt; do not self-retry.
"""

# Retained as a compatibility alias for the existing Ab2d-local experiment.
CORE_SCAFFOLD = MATH_CORE_SCAFFOLD


TASK_LOCAL_PRIMITIVES: dict[str, str] = {
    "polynomial_division_quotient_remainder": """Use PolynomialOps.div_qr(dividend_coefficients, [1, -divisor_root]).
Coefficients are highest degree first.  Divide by x - r using [1, -r].
Keep exact arithmetic.  Return quotient coefficients and the scalar remainder
required by the task contract; do not generalize to unrelated polynomial families.""",
    "largest_proper_divisor_reasoning": """For a composite n with largest proper divisor L, use n = L * p where p is
the smallest prime factor of n.  Test each necessity claim against that
invariant and return only the requested Boolean claims in frozen order.  Do
not replace the reasoning task with a request for divisor values.""",
    "rpm_circumference_to_kph": """Use exact fractions.Fraction arithmetic.  One rpm is 60 rotations per hour;
convert centimetres to kilometres by dividing by 100000.  The coefficient is
circumference_cm * 60 / 100000.  Return a reduced p/q fraction string and
the unit exactly as km/h; do not use float.""",
    "alternating_training_progression_threshold": """Follow the frozen alternating training-day recurrence exactly.  Derive the
odd/even session formula or iterate the recurrence without changing its day
order.  Compute the requested session and search cumulative distance for the
first day that strictly crosses the threshold; check the boundary exactly and
return that first qualifying week and day.""",
}


def assemble_ab2d_local_prompt(
    task_family: str,
    task_contract: str,
    frozen_parameters: Mapping[str, Any],
) -> str:
    """Assemble the compact Ab2d-local treatment without external dependencies."""
    try:
        primitive = TASK_LOCAL_PRIMITIVES[task_family]
    except KeyError as exc:
        raise ValueError(f"unsupported Ab2d-local task family: {task_family!r}") from exc
    if not isinstance(task_contract, str) or not task_contract.strip():
        raise ValueError("task_contract must be a non-empty string")
    frozen = json.dumps(dict(frozen_parameters), ensure_ascii=False, sort_keys=True)
    return (
        f"{MATH_CORE_SCAFFOLD}\n"
        f"## Task-local domain primitive: {task_family}\n{primitive}\n\n"
        f"## Task contract\n{task_contract.strip()}\n\n"
        f"## Frozen parameters\n{frozen}\n"
    )


def assemble_ab2g_math_core_prompt(
    task_contract: str,
    frozen_parameters: Mapping[str, Any],
) -> str:
    """Assemble the shared-core-only Ab2g treatment deterministically."""
    if not isinstance(task_contract, str) or not task_contract.strip():
        raise ValueError("task_contract must be a non-empty string")
    frozen = json.dumps(dict(frozen_parameters), ensure_ascii=False, sort_keys=True)
    return (
        f"{MATH_CORE_SCAFFOLD}\n"
        f"## Task contract\n{task_contract.strip()}\n\n"
        f"## Frozen parameters\n{frozen}\n"
    )


def measure_prompt_size(prompt: str) -> dict[str, int]:
    """Return deterministic local size metadata, not a provider token count."""
    return {
        "character_count": len(prompt),
        "utf8_byte_count": len(prompt.encode("utf-8")),
        "approx_wordpiece_count": len(re.findall(r"\S+", prompt)),
    }
