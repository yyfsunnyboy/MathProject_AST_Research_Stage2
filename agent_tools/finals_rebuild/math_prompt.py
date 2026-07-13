"""
Math domain scaffold and deterministic prompt builder (v1).

Builds model-facing prompts from frozen MathTask records without leaking
reference answers, validator logic, or metadata governance fields.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from agent_tools.finals_rebuild.artifacts import sha256_text
from agent_tools.finals_rebuild.math_task_schema import (
    MATH_ENTRY_POINT,
    MathOutputContract,
    MathTask,
)

PROMPT_VERSION = "math_prompt_v1"

MATH_DOMAIN_SCAFFOLD = (
    "Write one complete Python program.\n"
    "Define exactly one function named solve with no arguments.\n"
    "Return the final semantic answer from solve().\n"
    "Do not use input(), print(), network access, files, subprocesses, or "
    "interactive input.\n"
    "Do not output explanations, multiple candidate programs, or extra prose.\n"
    "Return a value matching the required Python return type and answer contract.\n"
    "Do not replace an exact symbolic answer with a decimal approximation "
    "unless the contract permits it.\n"
    "For multi-field answers, use exactly the required field names."
)

_FORBIDDEN_PROMPT_TOKENS: Tuple[str, ...] = (
    "reference_semantic",
    "reference_display",
    "validator_type",
    "evidence_role",
    "confirmatory_eligible",
    "metadata",
    "synthetic_fixture",
)


class MathPromptError(ValueError):
    """Raised when a math prompt cannot be built safely."""


@dataclass(frozen=True)
class MathPromptArtifact:
    task_id: str
    prompt_text: str
    prompt_sha256: str
    scaffold_sha256: str
    prompt_version: str


def _normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _format_optional_text(value: str | None) -> str:
    if value is None:
        return "none"
    return value


def _format_tolerance(value: float | None) -> str:
    if value is None:
        return "none"
    return format(float(value), ".15g")


def _format_string_list(items: Tuple[str, ...]) -> str:
    if not items:
        return "[]"
    return "[" + ", ".join(items) + "]"


def _format_output_contract_section(contract: MathOutputContract) -> str:
    lines = [
        "Output contract:",
        f"- answer_type: {contract.answer_type}",
        f"- representation_subtype: {_format_optional_text(contract.representation_subtype)}",
        f"- python_return_type: {contract.python_return_type}",
        f"- representation_policy: {contract.representation_policy}",
        f"- allowed_tolerance: {_format_tolerance(contract.allowed_tolerance)}",
        f"- symbolic_variables: {_format_string_list(contract.symbolic_variables)}",
        f"- answer_fields: {_format_string_list(contract.answer_fields)}",
    ]
    return "\n".join(lines)


def _build_prompt_text(task: MathTask) -> str:
    if task.entry_point != MATH_ENTRY_POINT:
        raise MathPromptError(
            f"unsupported entry_point {task.entry_point!r}; expected {MATH_ENTRY_POINT!r}"
        )

    sections: List[str] = [
        "Task:",
        _normalize_newlines(task.problem_text),
        "",
        "Required entry point:",
        "def solve():",
        "",
        "Input contract:",
        "No arguments.",
        "",
        _format_output_contract_section(task.output_contract),
        "",
        "Instructions:",
        MATH_DOMAIN_SCAFFOLD,
    ]
    return "\n".join(sections) + "\n"


def _assert_prompt_has_no_leaks(prompt_text: str) -> None:
    for token in _FORBIDDEN_PROMPT_TOKENS:
        if token in prompt_text:
            raise MathPromptError(
                f"prompt must not contain forbidden token {token!r}"
            )


def build_math_prompt(task: MathTask) -> MathPromptArtifact:
    """Build a deterministic, leak-safe prompt for one Math task."""
    prompt_text = _build_prompt_text(task)
    _assert_prompt_has_no_leaks(prompt_text)
    return MathPromptArtifact(
        task_id=task.task_id,
        prompt_text=prompt_text,
        prompt_sha256=sha256_text(prompt_text),
        scaffold_sha256=sha256_text(MATH_DOMAIN_SCAFFOLD),
        prompt_version=PROMPT_VERSION,
    )
