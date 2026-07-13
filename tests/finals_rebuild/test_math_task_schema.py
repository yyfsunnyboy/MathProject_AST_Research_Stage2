"""
Tests for agent_tools/finals_rebuild/math_task_schema.py
"""

from __future__ import annotations

import copy
import json
import os
import pathlib
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from agent_tools.finals_rebuild.math_task_schema import (
    INPUT_CONTRACT_KIND_NO_ARGUMENTS,
    MATH_ENTRY_POINT,
    MathOutputContract,
    MathTask,
    MathTaskSchemaError,
    load_math_tasks_jsonl,
    math_task_to_dict,
    parse_math_task,
)

FIXTURES = (
    pathlib.Path(__file__).resolve().parent / "fixtures" / "math_task_schema"
)


def _base_task_dict(**overrides):
    payload = {
        "task_id": "task_001",
        "source": "synthetic",
        "source_year": 2026,
        "source_exam": "fixture",
        "source_question_number": 1,
        "domain": "algebra",
        "subdomain": "integers",
        "problem_text": "Compute 1 + 1.",
        "entry_point": MATH_ENTRY_POINT,
        "input_contract": {"kind": INPUT_CONTRACT_KIND_NO_ARGUMENTS},
        "output_contract": {
            "answer_type": "number",
            "representation_subtype": "integer",
            "python_return_type": "int",
            "representation_policy": "exact_answer_type",
            "validator_type": "number_exact",
            "allowed_tolerance": None,
            "symbolic_variables": [],
            "answer_fields": [],
        },
        "reference_semantic": 2,
        "reference_display": "2",
        "metadata": {
            "synthetic_fixture": True,
            "confirmatory_eligible": False,
        },
    }
    payload.update(overrides)
    return payload


def test_fixture_jsonl_loads_five_answer_types():
    tasks = load_math_tasks_jsonl(FIXTURES / "synthetic_tasks.jsonl")
    assert len(tasks) == 5
    answer_types = {task.output_contract.answer_type for task in tasks}
    assert answer_types == {
        "number",
        "rational",
        "symbolic_expression",
        "coordinate_pair",
        "multi_field_answer",
    }
    for task in tasks:
        assert task.entry_point == MATH_ENTRY_POINT
        assert task.input_contract == {"kind": INPUT_CONTRACT_KIND_NO_ARGUMENTS}
        assert task.metadata["synthetic_fixture"] is True
        assert task.metadata["confirmatory_eligible"] is False


def test_reference_semantic_and_display_are_separate():
    tasks = load_math_tasks_jsonl(FIXTURES / "synthetic_tasks.jsonl")
    radical = next(t for t in tasks if t.task_id.endswith("symbolic_radical"))
    assert radical.reference_semantic == "2*sqrt(2)"
    assert radical.reference_display == "2√2"


def test_round_trip_serialization_is_deterministic():
    tasks = load_math_tasks_jsonl(FIXTURES / "synthetic_tasks.jsonl")
    for task in tasks:
        serialized = math_task_to_dict(task)
        reparsed = parse_math_task(serialized)
        assert math_task_to_dict(reparsed) == serialized


def test_tuple_list_normalization_for_contract_fields():
    data = _base_task_dict(
        output_contract={
            "answer_type": "multi_field_answer",
            "representation_subtype": None,
            "python_return_type": "dict",
            "representation_policy": "semantic_only",
            "validator_type": "multi_field_exact",
            "allowed_tolerance": None,
            "symbolic_variables": ["a", "b"],
            "answer_fields": ["x", "y"],
        }
    )
    task = parse_math_task(data)
    assert task.output_contract.symbolic_variables == ("a", "b")
    assert task.output_contract.answer_fields == ("x", "y")


def test_missing_task_id_fails_closed():
    data = _base_task_dict()
    del data["task_id"]
    with pytest.raises(MathTaskSchemaError, match="missing required fields"):
        parse_math_task(data)


def test_blank_task_id_fails_closed():
    data = _base_task_dict(task_id="   ")
    with pytest.raises(MathTaskSchemaError, match="task_id must be a non-empty string"):
        parse_math_task(data)


def test_entry_point_must_be_solve():
    data = _base_task_dict(entry_point="generate")
    with pytest.raises(MathTaskSchemaError, match="entry_point must be 'solve'"):
        parse_math_task(data)


def test_input_contract_must_be_no_arguments():
    data = _base_task_dict(input_contract={"kind": "positional_args"})
    with pytest.raises(MathTaskSchemaError, match="input_contract must be exactly"):
        parse_math_task(data)


def test_unknown_answer_type_rejected():
    data = _base_task_dict(
        output_contract=_base_task_dict()["output_contract"]
        | {"answer_type": "matrix"}
    )
    with pytest.raises(MathTaskSchemaError, match="answer_type"):
        parse_math_task(data)


def test_illegal_representation_policy_rejected():
    data = _base_task_dict(
        output_contract=_base_task_dict()["output_contract"]
        | {"representation_policy": "display_only"}
    )
    with pytest.raises(MathTaskSchemaError, match="representation_policy"):
        parse_math_task(data)


def test_negative_tolerance_rejected():
    data = _base_task_dict(
        output_contract=_base_task_dict()["output_contract"]
        | {"allowed_tolerance": -0.1}
    )
    with pytest.raises(MathTaskSchemaError, match="non-negative"):
        parse_math_task(data)


def test_number_with_fraction_return_type_rejected():
    data = _base_task_dict(
        output_contract=_base_task_dict()["output_contract"]
        | {"python_return_type": "Fraction"}
    )
    with pytest.raises(MathTaskSchemaError, match="answer_type='number'"):
        parse_math_task(data)


def test_rational_with_float_return_type_rejected():
    data = _base_task_dict(
        output_contract={
            "answer_type": "rational",
            "representation_subtype": None,
            "python_return_type": "float",
            "representation_policy": "semantic_only",
            "validator_type": "rational_exact",
            "allowed_tolerance": None,
            "symbolic_variables": [],
            "answer_fields": [],
        }
    )
    with pytest.raises(MathTaskSchemaError, match="answer_type='rational'"):
        parse_math_task(data)


def test_symbolic_expression_requires_str_return_type():
    data = _base_task_dict(
        output_contract={
            "answer_type": "symbolic_expression",
            "representation_subtype": "radical",
            "python_return_type": "int",
            "representation_policy": "semantic_only",
            "validator_type": "symbolic_expression",
            "allowed_tolerance": None,
            "symbolic_variables": [],
            "answer_fields": [],
        }
    )
    with pytest.raises(MathTaskSchemaError, match="answer_type='symbolic_expression'"):
        parse_math_task(data)


def test_coordinate_pair_rejects_list_return_type():
    data = _base_task_dict(
        output_contract={
            "answer_type": "coordinate_pair",
            "representation_subtype": None,
            "python_return_type": "list",
            "representation_policy": "exact_answer_type",
            "validator_type": "coordinate_pair_exact",
            "allowed_tolerance": None,
            "symbolic_variables": [],
            "answer_fields": [],
        }
    )
    with pytest.raises(MathTaskSchemaError, match="answer_type='coordinate_pair'"):
        parse_math_task(data)


def test_coordinate_pair_rejects_dict_return_type():
    data = _base_task_dict(
        output_contract={
            "answer_type": "coordinate_pair",
            "representation_subtype": None,
            "python_return_type": "dict",
            "representation_policy": "exact_answer_type",
            "validator_type": "coordinate_pair_exact",
            "allowed_tolerance": None,
            "symbolic_variables": [],
            "answer_fields": [],
        }
    )
    with pytest.raises(MathTaskSchemaError, match="answer_type='coordinate_pair'"):
        parse_math_task(data)


def test_multi_field_requires_answer_fields():
    data = _base_task_dict(
        output_contract={
            "answer_type": "multi_field_answer",
            "representation_subtype": None,
            "python_return_type": "dict",
            "representation_policy": "semantic_only",
            "validator_type": "multi_field_exact",
            "allowed_tolerance": None,
            "symbolic_variables": [],
            "answer_fields": [],
        }
    )
    with pytest.raises(MathTaskSchemaError, match="answer_fields must be non-empty"):
        parse_math_task(data)


def test_multi_field_rejects_duplicate_answer_fields():
    data = _base_task_dict(
        output_contract={
            "answer_type": "multi_field_answer",
            "representation_subtype": None,
            "python_return_type": "dict",
            "representation_policy": "semantic_only",
            "validator_type": "multi_field_exact",
            "allowed_tolerance": None,
            "symbolic_variables": [],
            "answer_fields": ["x", "x"],
        }
    )
    with pytest.raises(MathTaskSchemaError, match="answer_fields must not contain duplicates"):
        parse_math_task(data)


def test_unknown_top_level_field_rejected():
    data = _base_task_dict(extra_field=True)
    with pytest.raises(MathTaskSchemaError, match="unknown top-level fields"):
        parse_math_task(data)


def test_duplicate_task_id_in_jsonl_rejected(tmp_path):
    path = tmp_path / "tasks.jsonl"
    line = json.dumps(_base_task_dict())
    path.write_text(f"{line}\n{line}\n", encoding="utf-8")
    with pytest.raises(MathTaskSchemaError, match="duplicate task_id"):
        load_math_tasks_jsonl(path)


def test_jsonl_schema_error_includes_line_number(tmp_path):
    path = tmp_path / "tasks.jsonl"
    bad = _base_task_dict(entry_point="generate")
    path.write_text(json.dumps(bad) + "\n", encoding="utf-8")
    with pytest.raises(MathTaskSchemaError, match=r"line 1"):
        load_math_tasks_jsonl(path)


def test_json_syntax_error_includes_line_number(tmp_path):
    path = tmp_path / "tasks.jsonl"
    path.write_text("{not json}\n", encoding="utf-8")
    with pytest.raises(MathTaskSchemaError, match=r"line 1: invalid JSON"):
        load_math_tasks_jsonl(path)


def test_source_fixture_not_modified():
    fixture_path = FIXTURES / "synthetic_tasks.jsonl"
    before = fixture_path.read_text(encoding="utf-8")
    load_math_tasks_jsonl(fixture_path)
    assert fixture_path.read_text(encoding="utf-8") == before


def test_parse_does_not_mutate_input_dict():
    data = _base_task_dict()
    original = copy.deepcopy(data)
    parse_math_task(data)
    assert data == original


def test_does_not_import_sympy_or_ollama():
    import agent_tools.finals_rebuild.math_task_schema as module

    text = open(module.__file__, encoding="utf-8").read()
    assert "sympy" not in text.lower()
    assert "ollama" not in text.lower()


def test_math_output_contract_post_init_validation():
    with pytest.raises(MathTaskSchemaError, match="symbolic_variables must not contain duplicates"):
        MathOutputContract(
            answer_type="number",
            representation_subtype="integer",
            python_return_type="int",
            representation_policy="exact_answer_type",
            validator_type="number_exact",
            allowed_tolerance=None,
            symbolic_variables=("x", "x"),
            answer_fields=(),
        )
