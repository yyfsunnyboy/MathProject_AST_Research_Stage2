"""
Tests for agent_tools/finals_rebuild/math_prompt.py
"""

from __future__ import annotations

import copy
import os
import pathlib
import sys
from dataclasses import replace

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from agent_tools.finals_rebuild.artifacts import sha256_text
from agent_tools.finals_rebuild.math_prompt import (
    MATH_DOMAIN_SCAFFOLD,
    PROMPT_VERSION,
    MathPromptArtifact,
    build_math_prompt,
)
from agent_tools.finals_rebuild.math_task_schema import load_math_tasks_jsonl
from agent_tools.finals_rebuild.ollama_generation_runner import AB2G_SCAFFOLD

FIXTURES = (
    pathlib.Path(__file__).resolve().parent / "fixtures" / "math_task_schema"
)


def _tasks_by_suffix():
    tasks = load_math_tasks_jsonl(FIXTURES / "synthetic_tasks.jsonl")
    return {task.task_id.split("_")[-2] + "_" + task.task_id.split("_")[-1]: task for task in tasks}


@pytest.fixture(scope="module")
def synthetic_tasks():
    return load_math_tasks_jsonl(FIXTURES / "synthetic_tasks.jsonl")


def test_scaffold_is_single_fixed_constant():
    assert "Write one complete Python program." in MATH_DOMAIN_SCAFFOLD
    assert "Define exactly one function named solve with no arguments." in MATH_DOMAIN_SCAFFOLD
    assert "Return the final semantic answer from solve()." in MATH_DOMAIN_SCAFFOLD
    assert "input(), print()" in MATH_DOMAIN_SCAFFOLD
    assert "multiple candidate programs" in MATH_DOMAIN_SCAFFOLD
    assert "decimal approximation" in MATH_DOMAIN_SCAFFOLD
    assert "required field names" in MATH_DOMAIN_SCAFFOLD


def test_scaffold_does_not_copy_humaneval_ab2g_scaffold():
    assert AB2G_SCAFFOLD not in MATH_DOMAIN_SCAFFOLD
    assert "Additional requirements" not in MATH_DOMAIN_SCAFFOLD
    assert "Markdown code fences" not in MATH_DOMAIN_SCAFFOLD


def test_scaffold_has_no_reference_or_validator_keywords():
    lowered = MATH_DOMAIN_SCAFFOLD.lower()
    assert "reference_semantic" not in lowered
    assert "reference_display" not in lowered
    assert "validator_type" not in lowered
    assert "holdout" not in lowered


@pytest.mark.parametrize(
    "suffix",
    [
        "number_integer",
        "rational_fraction",
        "symbolic_radical",
        "coordinate_pair",
        "multi_field_answer",
    ],
)
def test_builder_supports_all_answer_types(synthetic_tasks, suffix):
    task = next(t for t in synthetic_tasks if t.task_id.endswith(suffix))
    artifact = build_math_prompt(task)
    assert isinstance(artifact, MathPromptArtifact)
    assert artifact.task_id == task.task_id
    assert artifact.prompt_version == PROMPT_VERSION


def test_prompt_section_order(synthetic_tasks):
    task = synthetic_tasks[0]
    prompt = build_math_prompt(task).prompt_text
    assert prompt.index("Task:") < prompt.index("Required entry point:")
    assert prompt.index("Required entry point:") < prompt.index("Input contract:")
    assert prompt.index("Input contract:") < prompt.index("Output contract:")
    assert prompt.index("Output contract:") < prompt.index("Instructions:")
    assert prompt.endswith(MATH_DOMAIN_SCAFFOLD + "\n")


def test_entry_point_contract_is_solve_without_arguments(synthetic_tasks):
    prompt = build_math_prompt(synthetic_tasks[0]).prompt_text
    assert "Required entry point:\ndef solve():" in prompt
    assert "Input contract:\nNo arguments." in prompt


def test_output_contract_fields_exposed(synthetic_tasks):
    radical = next(t for t in synthetic_tasks if t.task_id.endswith("symbolic_radical"))
    prompt = build_math_prompt(radical).prompt_text
    assert "- answer_type: symbolic_expression" in prompt
    assert "- representation_subtype: radical" in prompt
    assert "- python_return_type: str" in prompt
    assert "- representation_policy: semantic_only" in prompt
    assert "- allowed_tolerance: none" in prompt
    assert "- symbolic_variables: [x]" in prompt
    assert "- answer_fields: []" in prompt


def test_multi_field_keys_present(synthetic_tasks):
    task = next(t for t in synthetic_tasks if t.task_id.endswith("multi_field_answer"))
    prompt = build_math_prompt(task).prompt_text
    assert "- answer_type: multi_field_answer" in prompt
    assert "- answer_fields: [x, y]" in prompt


def test_prompt_excludes_protected_fields(synthetic_tasks):
    for task in synthetic_tasks:
        prompt = build_math_prompt(task).prompt_text
        for forbidden in (
            "reference_semantic",
            "reference_display",
            "validator_type",
            "evidence_role",
            "confirmatory_eligible",
            "metadata",
            "curriculum_level",
            "source_year",
        ):
            assert forbidden not in prompt


def test_reference_values_not_serialized(synthetic_tasks):
    radical = next(t for t in synthetic_tasks if t.task_id.endswith("symbolic_radical"))
    prompt = build_math_prompt(radical).prompt_text
    assert radical.reference_semantic not in prompt
    assert radical.reference_display not in prompt

    rational = next(t for t in synthetic_tasks if t.task_id.endswith("rational_fraction"))
    prompt = build_math_prompt(rational).prompt_text
    assert '"numerator"' not in prompt
    assert '"denominator"' not in prompt


def test_same_task_is_deterministic(synthetic_tasks):
    task = synthetic_tasks[0]
    first = build_math_prompt(task)
    second = build_math_prompt(task)
    assert first.prompt_text == second.prompt_text
    assert first.prompt_sha256 == second.prompt_sha256
    assert first.scaffold_sha256 == second.scaffold_sha256


def test_reference_changes_do_not_affect_prompt_or_hash(synthetic_tasks):
    task = synthetic_tasks[0]
    baseline = build_math_prompt(task)
    changed = build_math_prompt(
        replace(
            task,
            reference_semantic=999,
            reference_display="999",
            metadata={"synthetic_fixture": True, "confirmatory_eligible": False, "extra": 1},
        )
    )
    assert changed.prompt_text == baseline.prompt_text
    assert changed.prompt_sha256 == baseline.prompt_sha256


def test_problem_text_change_affects_prompt_and_hash(synthetic_tasks):
    task = synthetic_tasks[0]
    baseline = build_math_prompt(task)
    changed = build_math_prompt(replace(task, problem_text="What is 2 + 4?"))
    assert changed.prompt_text != baseline.prompt_text
    assert changed.prompt_sha256 != baseline.prompt_sha256


def test_output_contract_change_affects_prompt_and_hash(synthetic_tasks):
    task = synthetic_tasks[0]
    baseline = build_math_prompt(task)
    new_contract = replace(
        task.output_contract,
        representation_policy="semantic_only",
    )
    changed = build_math_prompt(replace(task, output_contract=new_contract))
    assert changed.prompt_text != baseline.prompt_text
    assert changed.prompt_sha256 != baseline.prompt_sha256


def test_scaffold_hash_is_fixed():
    expected = sha256_text(MATH_DOMAIN_SCAFFOLD)
    artifact = build_math_prompt(load_math_tasks_jsonl(FIXTURES / "synthetic_tasks.jsonl")[0])
    assert artifact.scaffold_sha256 == expected


def test_newlines_and_trailing_whitespace_are_stable(synthetic_tasks):
    task = replace(synthetic_tasks[0], problem_text="Line one\r\nLine two\r")
    prompt = build_math_prompt(task).prompt_text
    assert "\r" not in prompt
    assert "Line one\nLine two" in prompt
    assert prompt.endswith("\n")
    assert not prompt.endswith("\n\n")


def test_problem_text_may_contain_latex_without_leak_false_positive():
    task = replace(
        load_math_tasks_jsonl(FIXTURES / "synthetic_tasks.jsonl")[0],
        problem_text=r"Simplify $\sqrt{8}$ using LaTeX.",
    )
    artifact = build_math_prompt(task)
    assert r"$\sqrt{8}$" in artifact.prompt_text


def test_build_does_not_mutate_task(synthetic_tasks):
    task = synthetic_tasks[0]
    before = copy.deepcopy(task)
    build_math_prompt(task)
    assert task == before


def test_does_not_import_ollama_client():
    import agent_tools.finals_rebuild.math_prompt as module

    text = open(module.__file__, encoding="utf-8").read()
    assert "ollama" not in text.lower()
    assert "urllib" not in text


def test_number_integer_snapshot_hash(synthetic_tasks):
    task = next(t for t in synthetic_tasks if t.task_id.endswith("number_integer"))
    artifact = build_math_prompt(task)
    assert "Task:\nWhat is 2 + 3?" in artifact.prompt_text
    assert artifact.prompt_sha256 == sha256_text(artifact.prompt_text)


def test_coordinate_pair_shows_zero_tolerance(synthetic_tasks):
    task = next(t for t in synthetic_tasks if t.task_id.endswith("coordinate_pair"))
    prompt = build_math_prompt(task).prompt_text
    assert "- allowed_tolerance: 0" in prompt
