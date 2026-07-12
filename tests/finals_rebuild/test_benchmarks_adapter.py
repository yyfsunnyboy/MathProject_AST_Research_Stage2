"""
Tests for agent_tools/finals_rebuild/benchmarks_adapter.py
"""

from __future__ import annotations

import json
import os
import sys
import pathlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import pytest

from agent_tools.finals_rebuild.benchmarks_adapter import (
    BenchmarkAdapterError,
    BenchmarkCompletion,
    PublicBenchmarkTask,
    find_missing_task_ids,
    load_benchmark_completions,
    load_benchmark_tasks,
    strip_outer_code_fence,
    validate_completion_identity,
    write_evalplus_completion_jsonl,
)


def _write_jsonl(path: pathlib.Path, records: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec) + "\n")


def _write_json(path: pathlib.Path, obj) -> None:
    path.write_text(json.dumps(obj), encoding="utf-8")


# ============================================================
# 1. HumanEval JSONL normal load
# ============================================================


def test_humaneval_jsonl_normal_load(tmp_path):
    p = tmp_path / "tasks.jsonl"
    _write_jsonl(p, [
        {"task_id": "HumanEval/0", "prompt": "def f():\n", "entry_point": "f",
         "canonical_solution": "    return 1\n"},
        {"task_id": "HumanEval/1", "prompt": "def g():\n", "entry_point": "g"},
    ])
    tasks = load_benchmark_tasks(p, "humaneval")
    assert [t.task_id for t in tasks] == ["HumanEval/0", "HumanEval/1"]
    assert tasks[0].entry_point == "f"
    assert tasks[0].canonical_solution == "    return 1\n"
    assert tasks[1].canonical_solution is None


# ============================================================
# 2. MBPP uses 'text' mapped to prompt
# ============================================================


def test_mbpp_uses_text_field_as_prompt(tmp_path):
    p = tmp_path / "mbpp.jsonl"
    _write_jsonl(p, [
        {"task_id": "Mbpp/1", "text": "Write a function that adds two numbers."},
    ])
    tasks = load_benchmark_tasks(p, "mbpp")
    assert tasks[0].prompt == "Write a function that adds two numbers."
    assert tasks[0].entry_point is None
    assert tasks[0].canonical_solution is None


# ============================================================
# 3. Duplicate task_id fails
# ============================================================


def test_duplicate_task_id_fails(tmp_path):
    p = tmp_path / "dup.jsonl"
    _write_jsonl(p, [
        {"task_id": "HumanEval/0", "prompt": "p", "entry_point": "f"},
        {"task_id": "HumanEval/0", "prompt": "p2", "entry_point": "g"},
    ])
    with pytest.raises(BenchmarkAdapterError, match="duplicate task_id"):
        load_benchmark_tasks(p, "humaneval")


# ============================================================
# 4. HumanEval missing entry_point fails
# ============================================================


def test_humaneval_missing_entry_point_fails(tmp_path):
    p = tmp_path / "tasks.jsonl"
    _write_jsonl(p, [{"task_id": "HumanEval/0", "prompt": "p"}])
    with pytest.raises(BenchmarkAdapterError, match="entry_point"):
        load_benchmark_tasks(p, "humaneval")


# ============================================================
# 5. Unsupported benchmark fails
# ============================================================


def test_unsupported_benchmark_fails(tmp_path):
    p = tmp_path / "tasks.jsonl"
    _write_jsonl(p, [{"task_id": "X/0", "prompt": "p"}])
    with pytest.raises(BenchmarkAdapterError, match="benchmark"):
        load_benchmark_tasks(p, "leetcode")


# ============================================================
# 6. Outer code fence stripped correctly
# ============================================================


def test_strip_outer_code_fence_removes_single_outer_fence():
    completion = "```python\ndef f():\n    return 1\n```"
    result = strip_outer_code_fence(completion)
    assert result == "def f():\n    return 1"


def test_strip_outer_code_fence_no_fence_unchanged():
    completion = "def f():\n    return 1\n"
    assert strip_outer_code_fence(completion) == completion


# ============================================================
# 7. completion never concatenated with prompt
# ============================================================


def test_completion_not_concatenated_with_prompt(tmp_path):
    p = tmp_path / "completions.jsonl"
    _write_jsonl(p, [
        {"task_id": "HumanEval/0", "completion": "    return 1\n", "sample_index": 0},
    ])
    completions = load_benchmark_completions(p, "humaneval", "ab1")
    assert completions[0].completion == "    return 1\n"
    assert "def " not in completions[0].completion


# ============================================================
# 8. completion never re-adds function signature
# ============================================================


def test_completion_does_not_reintroduce_signature(tmp_path):
    p = tmp_path / "completions.jsonl"
    _write_jsonl(p, [
        {"task_id": "HumanEval/0", "completion": "    return 1\n", "sample_index": 0},
    ])
    completions = load_benchmark_completions(p, "humaneval", "ab1")
    assert completions[0].completion == "    return 1\n"


# ============================================================
# 9. empty completion fails
# ============================================================


def test_empty_completion_fails(tmp_path):
    p = tmp_path / "completions.jsonl"
    _write_jsonl(p, [
        {"task_id": "HumanEval/0", "completion": "   ", "sample_index": 0},
    ])
    with pytest.raises(BenchmarkAdapterError, match="completion"):
        load_benchmark_completions(p, "humaneval", "ab1")


# ============================================================
# 10. duplicate (task_id, sample_index) fails
# ============================================================


def test_duplicate_task_id_sample_index_fails(tmp_path):
    p = tmp_path / "completions.jsonl"
    _write_jsonl(p, [
        {"task_id": "HumanEval/0", "completion": "a", "sample_index": 0},
        {"task_id": "HumanEval/0", "completion": "b", "sample_index": 0},
    ])
    with pytest.raises(BenchmarkAdapterError, match="duplicate"):
        load_benchmark_completions(p, "humaneval", "ab1")


# ============================================================
# 11. unknown task_id in completion identity fails
# ============================================================


def test_unknown_task_id_in_completions_fails(tmp_path):
    tasks = [
        PublicBenchmarkTask(
            benchmark="humaneval", task_id="HumanEval/0",
            prompt="p", entry_point="f", canonical_solution=None,
        )
    ]
    completions = [
        BenchmarkCompletion(
            benchmark="humaneval", task_id="HumanEval/999", sample_index=0,
            treatment="ab1", completion="return 1", source_treatment=None,
        )
    ]
    with pytest.raises(BenchmarkAdapterError, match="unknown task_id"):
        validate_completion_identity(tasks, completions)


# ============================================================
# 12. missing task ids preserve original order
# ============================================================


def test_missing_task_ids_preserve_order(tmp_path):
    tasks = [
        PublicBenchmarkTask(
            benchmark="humaneval", task_id=f"HumanEval/{i}",
            prompt="p", entry_point="f", canonical_solution=None,
        )
        for i in range(4)
    ]
    completions = [
        BenchmarkCompletion(
            benchmark="humaneval", task_id="HumanEval/1", sample_index=0,
            treatment="ab1", completion="return 1", source_treatment=None,
        ),
        BenchmarkCompletion(
            benchmark="humaneval", task_id="HumanEval/3", sample_index=0,
            treatment="ab1", completion="return 1", source_treatment=None,
        ),
    ]
    missing = find_missing_task_ids(tasks, completions)
    assert missing == ["HumanEval/0", "HumanEval/2"]


# ============================================================
# 13. EvalPlus JSONL only contains task_id, completion
# ============================================================


def test_evalplus_jsonl_only_has_task_id_and_completion(tmp_path):
    completions = [
        BenchmarkCompletion(
            benchmark="humaneval", task_id="HumanEval/0", sample_index=0,
            treatment="ab1", completion="return 1", source_treatment=None,
        ),
    ]
    out = tmp_path / "out.jsonl"
    write_evalplus_completion_jsonl(completions, out)
    lines = out.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    obj = json.loads(lines[0])
    assert set(obj.keys()) == {"task_id", "completion"}
    assert obj["task_id"] == "HumanEval/0"
    assert obj["completion"] == "return 1"


# ============================================================
# 14. mixed benchmark cannot output to same file
# ============================================================


def test_mixed_benchmark_output_fails(tmp_path):
    completions = [
        BenchmarkCompletion(
            benchmark="humaneval", task_id="HumanEval/0", sample_index=0,
            treatment="ab1", completion="return 1", source_treatment=None,
        ),
        BenchmarkCompletion(
            benchmark="mbpp", task_id="Mbpp/1", sample_index=0,
            treatment="ab1", completion="return 2", source_treatment=None,
        ),
    ]
    out = tmp_path / "out.jsonl"
    with pytest.raises(BenchmarkAdapterError, match="benchmark"):
        write_evalplus_completion_jsonl(completions, out)


# ============================================================
# 15. mixed treatment cannot output to same file
# ============================================================


def test_mixed_treatment_output_fails(tmp_path):
    completions = [
        BenchmarkCompletion(
            benchmark="humaneval", task_id="HumanEval/0", sample_index=0,
            treatment="ab1", completion="return 1", source_treatment=None,
        ),
        BenchmarkCompletion(
            benchmark="humaneval", task_id="HumanEval/1", sample_index=0,
            treatment="ab2g", completion="return 2", source_treatment=None,
        ),
    ]
    out = tmp_path / "out.jsonl"
    with pytest.raises(BenchmarkAdapterError, match="treatment"):
        write_evalplus_completion_jsonl(completions, out)


# ============================================================
# 16. no test result fields ever produced
# ============================================================


def test_no_test_result_fields_ever_produced(tmp_path):
    completions = [
        BenchmarkCompletion(
            benchmark="humaneval", task_id="HumanEval/0", sample_index=0,
            treatment="ab1", completion="return 1", source_treatment=None,
        ),
    ]
    out = tmp_path / "out.jsonl"
    write_evalplus_completion_jsonl(completions, out)
    obj = json.loads(out.read_text(encoding="utf-8").strip())
    for forbidden in ("test_pass", "score", "syntax_pass", "execution_success"):
        assert forbidden not in obj


# ============================================================
# Additional coverage: source_treatment rules, ab3_core/full,
# repeated task_id with sample_index > 0, MBPP text/code fields
# ============================================================


def test_ab3_core_requires_ab2g_source_treatment():
    with pytest.raises(BenchmarkAdapterError, match="source_treatment"):
        BenchmarkCompletion(
            benchmark="humaneval", task_id="HumanEval/0", sample_index=0,
            treatment="ab3_core", completion="return 1", source_treatment=None,
        )
    # valid
    BenchmarkCompletion(
        benchmark="humaneval", task_id="HumanEval/0", sample_index=0,
        treatment="ab3_core", completion="return 1", source_treatment="ab2g",
    )


def test_ab1_rejects_nonnull_source_treatment():
    with pytest.raises(BenchmarkAdapterError, match="source_treatment"):
        BenchmarkCompletion(
            benchmark="humaneval", task_id="HumanEval/0", sample_index=0,
            treatment="ab1", completion="return 1", source_treatment="ab2g",
        )


def test_repeated_task_id_with_sample_index_preserved(tmp_path):
    completions = [
        BenchmarkCompletion(
            benchmark="humaneval", task_id="HumanEval/0", sample_index=0,
            treatment="ab1", completion="return 1", source_treatment=None,
        ),
        BenchmarkCompletion(
            benchmark="humaneval", task_id="HumanEval/0", sample_index=1,
            treatment="ab1", completion="return 2", source_treatment=None,
        ),
    ]
    out = tmp_path / "out.jsonl"
    write_evalplus_completion_jsonl(completions, out)
    lines = out.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    objs = [json.loads(l) for l in lines]
    assert objs[0]["task_id"] == objs[1]["task_id"] == "HumanEval/0"
    assert objs[0]["completion"] == "return 1"
    assert objs[1]["completion"] == "return 2"


def test_mbpp_code_field_maps_to_canonical_solution(tmp_path):
    p = tmp_path / "mbpp.jsonl"
    _write_jsonl(p, [
        {"task_id": "Mbpp/1", "text": "add two numbers", "code": "def f(a,b):\n    return a+b\n"},
    ])
    tasks = load_benchmark_tasks(p, "mbpp")
    assert tasks[0].canonical_solution == "def f(a,b):\n    return a+b\n"


def test_completion_sample_index_default_zero_when_unique(tmp_path):
    p = tmp_path / "completions.jsonl"
    _write_jsonl(p, [{"task_id": "HumanEval/0", "completion": "return 1"}])
    completions = load_benchmark_completions(p, "humaneval", "ab1")
    assert completions[0].sample_index == 0


def test_completion_sample_index_required_when_ambiguous(tmp_path):
    p = tmp_path / "completions.jsonl"
    _write_jsonl(p, [
        {"task_id": "HumanEval/0", "completion": "return 1"},
        {"task_id": "HumanEval/0", "completion": "return 2"},
    ])
    with pytest.raises(BenchmarkAdapterError, match="sample_index"):
        load_benchmark_completions(p, "humaneval", "ab1")


def test_json_list_format_supported(tmp_path):
    p = tmp_path / "tasks.json"
    _write_json(p, [
        {"task_id": "HumanEval/0", "prompt": "p", "entry_point": "f"},
    ])
    tasks = load_benchmark_tasks(p, "humaneval")
    assert tasks[0].task_id == "HumanEval/0"
