"""
Tests for agent_tools/finals_rebuild/public_benchmark_runner.py
"""

from __future__ import annotations

import inspect
import json
import os
import sys
import pathlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import pytest

from agent_tools.finals_rebuild.public_benchmark_runner import (
    PublicBenchmarkRunnerError,
    build_public_benchmark_pair_id,
    run_public_benchmark_treatments,
)

_FIXTURES = pathlib.Path(__file__).parent / "fixtures"
_TASKS = _FIXTURES / "public_benchmark_tasks.jsonl"
_AB1 = _FIXTURES / "public_benchmark_ab1.jsonl"
_AB2G = _FIXTURES / "public_benchmark_ab2g.jsonl"
_EVALUATOR_GIT_COMMIT = "e3d2e1b"


def _run(tmp_path, tasks=_TASKS, ab1=_AB1, ab2g=_AB2G, benchmark="humaneval"):
    out_root = tmp_path / "artifacts"
    summary = run_public_benchmark_treatments(
        tasks_path=tasks,
        ab1_completions_path=ab1,
        ab2g_completions_path=ab2g,
        benchmark=benchmark,
        artifact_root=out_root,
        evaluator_git_commit=_EVALUATOR_GIT_COMMIT,
    )
    results_path = out_root / "public_benchmark" / benchmark / "results.json"
    results = json.loads(results_path.read_text(encoding="utf-8"))
    return summary, results, out_root


def _write_manifest_files(tmp_path, tasks, ab1, ab2g):
    tasks_path = tmp_path / "tasks.jsonl"
    ab1_path = tmp_path / "ab1.jsonl"
    ab2g_path = tmp_path / "ab2g.jsonl"
    with open(tasks_path, "w", encoding="utf-8") as fh:
        for rec in tasks:
            fh.write(json.dumps(rec) + "\n")
    with open(ab1_path, "w", encoding="utf-8") as fh:
        for rec in ab1:
            fh.write(json.dumps(rec) + "\n")
    with open(ab2g_path, "w", encoding="utf-8") as fh:
        for rec in ab2g:
            fh.write(json.dumps(rec) + "\n")
    return tasks_path, ab1_path, ab2g_path


_BASE_TASKS = [
    {"task_id": "HumanEval/0", "prompt": "def add(a, b):\n", "entry_point": "add"},
    {"task_id": "HumanEval/1", "prompt": "def double(x):\n", "entry_point": "double"},
]
_BASE_AB1 = [
    {"task_id": "HumanEval/0", "sample_index": 0, "completion": "def add(a, b):\n    return a + b\n"},
    {"task_id": "HumanEval/1", "sample_index": 0, "completion": "def double(x):\n    return x * 2\n"},
]
_BASE_AB2G = [
    {"task_id": "HumanEval/0", "sample_index": 0, "completion": "def add(a，b)：\n    return a + b\n"},
    {"task_id": "HumanEval/1", "sample_index": 0, "completion": "def double(x):\n    return x * 2\n"},
]


# ============================================================
# 1. 2 pairs fully loaded
# ============================================================


def test_two_pairs_fully_loaded(tmp_path):
    summary, results, _ = _run(tmp_path)
    assert summary.total_pairs == 2
    assert len(results) == 2


# ============================================================
# 2. Ab1 never passed to Healer/adapters
# ============================================================


def test_ab1_not_passed_to_core_or_spec(tmp_path, monkeypatch):
    import agent_tools.finals_rebuild.public_benchmark_runner as mod

    seen_core_inputs = []
    seen_spec_inputs = []
    orig_core = mod.run_core_adapter
    orig_spec = mod.run_spec_adapter

    def spy_core(*, pair_id, input_code):
        seen_core_inputs.append(input_code)
        return orig_core(pair_id=pair_id, input_code=input_code)

    def spy_spec(*, pair_id, skill_id, input_code):
        seen_spec_inputs.append(input_code)
        return orig_spec(pair_id=pair_id, skill_id=skill_id, input_code=input_code)

    monkeypatch.setattr(mod, "run_core_adapter", spy_core)
    monkeypatch.setattr(mod, "run_spec_adapter", spy_spec)
    _, results, _ = _run(tmp_path)

    with open(_AB2G, encoding="utf-8") as fh:
        ab2g_by_task = {
            json.loads(line)["task_id"]: json.loads(line)["completion"]
            for line in fh if line.strip()
        }
    # Core's inputs must be exactly the Ab2g completions (in some order),
    # never an Ab1 completion — checked by construction, not text overlap
    # (an Ab1 and Ab2g completion may legitimately be textually identical).
    assert sorted(seen_core_inputs) == sorted(ab2g_by_task.values())
    # Spec's inputs must be exactly Core's own outputs (the ab3_core
    # completions actually produced), never the raw Ab2g completion.
    ab3_core_by_task = {r["task_id"]: r["ab3_core_completion"] for r in results}
    assert sorted(seen_spec_inputs) == sorted(ab3_core_by_task.values())


# ============================================================
# 3. Ab2g original completion not overwritten
# ============================================================


def test_ab2g_completion_not_overwritten(tmp_path):
    _, results, _ = _run(tmp_path)
    with open(_AB2G, encoding="utf-8") as fh:
        original_by_task = {
            json.loads(line)["task_id"]: json.loads(line)["completion"]
            for line in fh if line.strip()
        }
    for r in results:
        assert r["ab2g_completion"] == original_by_task[r["task_id"]]


# ============================================================
# 4 & 5. Core input == Ab2g completion; Full input == Core output
# ============================================================


def test_core_input_equals_ab2g_and_full_input_equals_core_output(tmp_path):
    _, results, _ = _run(tmp_path)
    for r in results:
        assert r["core_trace"]["input_hash"] == r["ab2g_hash"]
        assert r["spec_trace"]["input_hash"] == r["ab3_core_hash"]


# ============================================================
# 6. Core/Full source identity both point to the same Ab2g
# ============================================================


def test_core_and_full_share_same_ab2g_source(tmp_path):
    _, results, _ = _run(tmp_path)
    for r in results:
        # Both derive (transitively) from the same ab2g_hash: core's input
        # is ab2g_hash directly; full's input is core's output, which in
        # turn was derived from ab2g_hash.
        assert r["core_trace"]["input_hash"] == r["ab2g_hash"]
        assert r["spec_trace"]["input_hash"] == r["ab3_core_hash"]


# ============================================================
# 7 & 8. Fixable fixture changes; unfixable stays unchanged
# ============================================================


def test_fixable_fixture_is_changed(tmp_path):
    _, results, _ = _run(tmp_path)
    r0 = next(r for r in results if r["task_id"] == "HumanEval/0")
    assert r0["core_changed"] is True
    assert r0["core_fix_count"] >= 1
    assert "，" not in r0["ab3_core_completion"]
    assert "：" not in r0["ab3_core_completion"]


def test_unfixable_fixture_stays_unchanged(tmp_path):
    _, results, _ = _run(tmp_path)
    r1 = next(r for r in results if r["task_id"] == "HumanEval/1")
    assert r1["core_changed"] is False
    assert r1["ab3_core_completion"] == r1["ab2g_completion"]


# ============================================================
# 9. Four treatment hashes are correct
# ============================================================


def test_four_treatment_hashes_correct(tmp_path):
    from agent_tools.finals_rebuild.artifacts import sha256_text

    _, results, _ = _run(tmp_path)
    for r in results:
        assert r["ab1_hash"] == sha256_text(r["ab1_completion"])
        assert r["ab2g_hash"] == sha256_text(r["ab2g_completion"])
        assert r["ab3_core_hash"] == sha256_text(r["ab3_core_completion"])
        assert r["ab3_full_hash"] == sha256_text(r["ab3_full_completion"])


# ============================================================
# 10 & 11. static/execution evaluation ran for all 4 treatments
# ============================================================


def test_static_evaluation_ran_for_all_four_treatments(tmp_path):
    _, results, _ = _run(tmp_path)
    for r in results:
        for key in ("ab1_static", "ab2g_static", "ab3_core_static", "ab3_full_static"):
            assert isinstance(r[key]["syntax_pass"], bool)


def test_execution_evaluation_ran_for_all_four_treatments(tmp_path):
    _, results, _ = _run(tmp_path)
    for r in results:
        for key in ("ab1_execution", "ab2g_execution", "ab3_core_execution", "ab3_full_execution"):
            assert r[key]["execution_status"] != "not_run"


# ============================================================
# 12 & 13. test_status not_run, test_pass None/absent
# ============================================================


def test_test_status_is_not_run(tmp_path):
    _, results, _ = _run(tmp_path)
    for r in results:
        assert r["test_status"] == "not_run"


def test_test_pass_is_none_everywhere(tmp_path):
    _, results, _ = _run(tmp_path)
    for r in results:
        for key in ("ab1_execution", "ab2g_execution", "ab3_core_execution", "ab3_full_execution"):
            assert r[key]["test_pass"] is None


# ============================================================
# 14. identity set mismatch -> fail closed
# ============================================================


def test_identity_set_mismatch_fails_closed(tmp_path):
    ab1_extra = _BASE_AB1 + [
        {"task_id": "HumanEval/0", "sample_index": 1, "completion": "def add(a, b):\n    return a + b\n"}
    ]
    tasks_path, ab1_path, ab2g_path = _write_manifest_files(tmp_path, _BASE_TASKS, ab1_extra, _BASE_AB2G)
    with pytest.raises(PublicBenchmarkRunnerError, match="identity sets"):
        run_public_benchmark_treatments(
            tasks_path=tasks_path, ab1_completions_path=ab1_path,
            ab2g_completions_path=ab2g_path, benchmark="humaneval",
            artifact_root=tmp_path / "out", evaluator_git_commit=_EVALUATOR_GIT_COMMIT,
        )


# ============================================================
# 15. sample_index mismatch -> fail closed
# ============================================================


def test_sample_index_mismatch_fails_closed(tmp_path):
    ab2g_shifted = [
        {"task_id": "HumanEval/0", "sample_index": 5, "completion": "def add(a, b):\n    return a + b\n"},
        _BASE_AB2G[1],
    ]
    tasks_path, ab1_path, ab2g_path = _write_manifest_files(tmp_path, _BASE_TASKS, _BASE_AB1, ab2g_shifted)
    with pytest.raises(PublicBenchmarkRunnerError, match="identity sets"):
        run_public_benchmark_treatments(
            tasks_path=tasks_path, ab1_completions_path=ab1_path,
            ab2g_completions_path=ab2g_path, benchmark="humaneval",
            artifact_root=tmp_path / "out", evaluator_git_commit=_EVALUATOR_GIT_COMMIT,
        )


# ============================================================
# 16. task not present -> fail closed
# ============================================================


def test_unknown_task_id_fails_closed(tmp_path):
    from agent_tools.finals_rebuild.benchmarks_adapter import BenchmarkAdapterError

    ab2g_unknown = [
        {"task_id": "HumanEval/999", "sample_index": 0, "completion": "def f():\n    return 1\n"},
        _BASE_AB2G[1],
    ]
    ab1_unknown = [
        {"task_id": "HumanEval/999", "sample_index": 0, "completion": "def f():\n    return 1\n"},
        _BASE_AB1[1],
    ]
    tasks_path, ab1_path, ab2g_path = _write_manifest_files(
        tmp_path, [_BASE_TASKS[1]], ab1_unknown, ab2g_unknown
    )
    with pytest.raises(BenchmarkAdapterError, match="unknown task_id"):
        run_public_benchmark_treatments(
            tasks_path=tasks_path, ab1_completions_path=ab1_path,
            ab2g_completions_path=ab2g_path, benchmark="humaneval",
            artifact_root=tmp_path / "out", evaluator_git_commit=_EVALUATOR_GIT_COMMIT,
        )


# ============================================================
# 17. benchmark mismatch -> fail closed
# ============================================================


def test_benchmark_mismatch_fails_closed(tmp_path):
    from agent_tools.finals_rebuild.benchmarks_adapter import BenchmarkAdapterError

    mbpp_tasks = [{"task_id": "Mbpp/1", "text": "add two numbers"}]
    tasks_path, ab1_path, ab2g_path = _write_manifest_files(
        tmp_path, mbpp_tasks, _BASE_AB1, _BASE_AB2G
    )
    # Loading humaneval-format completions against an mbpp task file with
    # mismatched task_ids fails via validate_completion_identity /
    # load_benchmark_tasks's own benchmark-specific field requirements.
    with pytest.raises((BenchmarkAdapterError, PublicBenchmarkRunnerError)):
        run_public_benchmark_treatments(
            tasks_path=tasks_path, ab1_completions_path=ab1_path,
            ab2g_completions_path=ab2g_path, benchmark="mbpp",
            artifact_root=tmp_path / "out", evaluator_git_commit=_EVALUATOR_GIT_COMMIT,
        )


# ============================================================
# 18. duplicate identity -> fail closed
# ============================================================


def test_duplicate_identity_fails_closed(tmp_path):
    from agent_tools.finals_rebuild.benchmarks_adapter import BenchmarkAdapterError

    # load_benchmark_completions itself already rejects duplicate
    # (task_id, sample_index) within one file — confirms the runner
    # inherits that fail-closed behaviour rather than bypassing it.
    ab2g_dup = [_BASE_AB2G[0], _BASE_AB2G[0]]
    tasks_path, ab1_path, ab2g_path = _write_manifest_files(
        tmp_path, _BASE_TASKS, _BASE_AB1, ab2g_dup
    )
    with pytest.raises(BenchmarkAdapterError, match="duplicate"):
        run_public_benchmark_treatments(
            tasks_path=tasks_path, ab1_completions_path=ab1_path,
            ab2g_completions_path=ab2g_path, benchmark="humaneval",
            artifact_root=tmp_path / "out", evaluator_git_commit=_EVALUATOR_GIT_COMMIT,
        )


# ============================================================
# 19 & 20. Four EvalPlus JSONL outputs correct, task_id/completion only
# ============================================================


def test_four_evalplus_jsonl_outputs_correct(tmp_path):
    _, _, out_root = _run(tmp_path)
    evalplus_dir = out_root / "public_benchmark" / "humaneval" / "evalplus"
    for name in ("ab1.jsonl", "ab2g.jsonl", "ab3_core.jsonl", "ab3_full.jsonl"):
        path = evalplus_dir / name
        assert path.exists(), f"{name} missing"
        lines = path.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 2
        for line in lines:
            obj = json.loads(line)
            assert set(obj.keys()) == {"task_id", "completion"}


# ============================================================
# 21. Same input reruns deterministically
# ============================================================


def test_rerun_is_deterministic(tmp_path):
    summary1, results1, out1 = _run(tmp_path / "run1")
    summary2, results2, out2 = _run(tmp_path / "run2")
    assert summary1 == summary2
    for r1, r2 in zip(results1, results2):
        for key in (
            "task_id", "sample_index", "ab1_hash", "ab2g_hash",
            "ab3_core_hash", "ab3_full_hash", "core_changed", "spec_changed",
            "core_fix_count", "spec_fix_count", "test_status",
        ):
            assert r1[key] == r2[key]
        assert r1["core_trace"] == r2["core_trace"]
        assert r1["spec_trace"] == r2["spec_trace"]


# ============================================================
# 22. summary counts correct
# ============================================================


def test_summary_counts_correct(tmp_path):
    summary, results, _ = _run(tmp_path)
    assert summary.total_pairs == 2
    assert summary.core_changed_count == sum(1 for r in results if r["core_changed"])
    assert summary.spec_changed_count == sum(1 for r in results if r["spec_changed"])
    assert summary.core_unchanged_count == summary.total_pairs - summary.core_changed_count
    assert summary.not_test_assessable_count == summary.total_pairs


# ============================================================
# 23 & 24. No model calls, no semantic healer
# ============================================================


def test_no_model_or_semantic_healer_calls_structural():
    import agent_tools.finals_rebuild.public_benchmark_runner as mod

    src = inspect.getsource(mod)
    for forbidden in (
        "openai", "anthropic", "google.generativeai", "call_ai_with_retry",
        "semantic_heal", "RegexHealer", "ASTHealer",
    ):
        assert forbidden not in src, f"forbidden reference {forbidden!r} found"


# ============================================================
# 25. No EvalPlus execution
# ============================================================


def test_no_evalplus_execution_structural():
    import agent_tools.finals_rebuild.public_benchmark_runner as mod

    src = inspect.getsource(mod)
    # write_evalplus_completion_jsonl (existing helper) IS expected to be
    # called — this module only ever writes the completion JSONL, it never
    # invokes the EvalPlus tool itself or computes any of its metrics.
    # (The module's own docstring legitimately *mentions* pass@1/McNemar by
    # name to disclaim them, so those substrings are not checked here.)
    for forbidden in ("pass_at_1", "mcnemar", "subprocess.run", "subprocess.Popen"):
        assert forbidden not in src


# ============================================================
# Additional: pair_id determinism, no fake test_pass fields anywhere
# ============================================================


def test_build_pair_id_deterministic():
    a = build_public_benchmark_pair_id("humaneval", "HumanEval/0", 0)
    b = build_public_benchmark_pair_id("humaneval", "HumanEval/0", 0)
    assert a == b
    c = build_public_benchmark_pair_id("humaneval", "HumanEval/1", 0)
    assert a != c


def test_no_fake_test_pass_in_output_json(tmp_path):
    _, results, out_root = _run(tmp_path)
    results_path = out_root / "public_benchmark" / "humaneval" / "results.json"
    blob = results_path.read_text(encoding="utf-8")
    summary_path = out_root / "public_benchmark" / "humaneval" / "summary.json"
    summary_blob = summary_path.read_text(encoding="utf-8")
    for forbidden in ("pass_at_1", "pass_rate", "\"accuracy\"", "\"score\""):
        assert forbidden not in blob
        assert forbidden not in summary_blob
