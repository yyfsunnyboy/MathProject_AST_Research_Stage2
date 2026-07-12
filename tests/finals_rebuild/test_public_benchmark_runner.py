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
    load_generation_attempts,
    run_public_benchmark_treatments,
    run_public_benchmark_treatments_from_attempts,
    sha256_text,
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


# =============================================================================
# Raw-response-driven Ab3 pipeline (run_public_benchmark_treatments_from_attempts)
# =============================================================================

_RAW_TASKS = [
    {"task_id": "HumanEval/0", "prompt": "def add(a, b):\n", "entry_point": "add"},
    {"task_id": "HumanEval/1", "prompt": "def double(x):\n", "entry_point": "double"},
]


def _write_tasks_jsonl(tmp_path, tasks):
    path = tmp_path / "tasks.jsonl"
    with open(path, "w", encoding="utf-8") as fh:
        for rec in tasks:
            fh.write(json.dumps(rec) + "\n")
    return path


def _write_attempts_jsonl(tmp_path, attempts, name="generation_attempts.jsonl"):
    path = tmp_path / name
    with open(path, "w", encoding="utf-8") as fh:
        for rec in attempts:
            fh.write(json.dumps(rec) + "\n")
    return path


def _attempt(task_id, treatment, *, status="success", raw_response=None,
             completion=None, extraction_status=None, sample_index=0):
    return {
        "task_id": task_id,
        "sample_index": sample_index,
        "treatment": treatment,
        "status": status,
        "failure_stage": None if status == "success" else "extraction",
        "failure_reason": None,
        "raw_response": raw_response,
        "raw_response_sha256": sha256_text(raw_response) if raw_response is not None else None,
        "completion": completion,
        "completion_sha256": sha256_text(completion) if completion is not None else None,
        "extraction_status": extraction_status,
        "extraction_method": "plain_text" if extraction_status == "extracted" else None,
        "total_fenced_blocks": 0,
        "python_fenced_blocks": 0,
        "had_markdown_fence": False,
        "had_surrounding_text": False,
        "elapsed_seconds": 1.0,
        "metadata": {"benchmark": "humaneval", "treatment": treatment},
    }


def _run_from_attempts(tmp_path, tasks, attempts, benchmark="humaneval"):
    tasks_path = _write_tasks_jsonl(tmp_path, tasks)
    attempts_path = _write_attempts_jsonl(tmp_path, attempts)
    out_root = tmp_path / "artifacts"
    summary = run_public_benchmark_treatments_from_attempts(
        tasks_path=tasks_path,
        generation_attempts_path=attempts_path,
        benchmark=benchmark,
        artifact_root=out_root,
        evaluator_git_commit=_EVALUATOR_GIT_COMMIT,
    )
    results_path = out_root / "public_benchmark_raw" / benchmark / "results.json"
    results = json.loads(results_path.read_text(encoding="utf-8"))
    return summary, results, out_root


# ------------------------------------------------------------
# 1. Ab1 fully failed does not block Ab3
# ------------------------------------------------------------


def test_ab1_all_failed_does_not_block_ab3(tmp_path):
    attempts = [
        _attempt("HumanEval/0", "ab1", status="failed", raw_response="```python\nA\n```\n```python\nB\n```",
                  extraction_status="ambiguous"),
        _attempt("HumanEval/0", "ab2g", status="success",
                  raw_response="    return a + b\n", completion="    return a + b\n",
                  extraction_status="extracted"),
        _attempt("HumanEval/1", "ab1", status="failed", raw_response="```python\nA\n```\n```python\nB\n```",
                  extraction_status="ambiguous"),
        _attempt("HumanEval/1", "ab2g", status="success",
                  raw_response="    return x * 2\n", completion="    return x * 2\n",
                  extraction_status="extracted"),
    ]
    summary, results, _ = _run_from_attempts(tmp_path, _RAW_TASKS, attempts)
    assert summary.ab1_missing_count == 0
    assert summary.ab1_available_count == 2
    assert summary.ab3_target_count == 2
    for r in results:
        assert r["ab1_extraction_status"] == "ambiguous"
        assert r["has_ab3_target"] is True
        assert r["ab3_core_completion"] is not None


# ------------------------------------------------------------
# 2. Ab2g extraction success -> Core/Full built
# ------------------------------------------------------------


def test_ab2g_extraction_success_builds_core_and_full(tmp_path):
    attempts = [
        _attempt("HumanEval/0", "ab2g", status="success",
                  raw_response="    return a + b\n", completion="    return a + b\n",
                  extraction_status="extracted"),
        _attempt("HumanEval/1", "ab2g", status="success",
                  raw_response="    return x * 2\n", completion="    return x * 2\n",
                  extraction_status="extracted"),
    ]
    summary, results, _ = _run_from_attempts(tmp_path, _RAW_TASKS, attempts)
    assert summary.ab3_core_extraction_success_count == 2
    assert summary.ab3_full_extraction_success_count == 2
    for r in results:
        assert r["ab3_core_completion"] is not None
        assert r["ab3_full_completion"] is not None
        assert r["ab3_core_static"] is not None
        assert r["ab3_full_static"] is not None


# ------------------------------------------------------------
# 3. Ab2g extraction ambiguous but raw exists -> Core/Full still built
# ------------------------------------------------------------


def test_ab2g_ambiguous_raw_still_builds_ab3(tmp_path):
    raw = "```python\nA\n```\n```python\nB\n```"
    attempts = [
        _attempt("HumanEval/0", "ab2g", status="failed", raw_response=raw,
                  extraction_status="ambiguous"),
        _attempt("HumanEval/1", "ab2g", status="success",
                  raw_response="    return x * 2\n", completion="    return x * 2\n",
                  extraction_status="extracted"),
    ]
    summary, results, _ = _run_from_attempts(tmp_path, _RAW_TASKS, attempts)
    r0 = next(r for r in results if r["task_id"] == "HumanEval/0")
    assert r0["has_ab3_target"] is True
    assert r0["ab2g_extraction_status"] == "ambiguous"
    # Core received the raw response, unmodified (identity transform since
    # no fullwidth punctuation is present) -> re-extraction over Core's
    # output hits the same ambiguity extraction.py already found.
    assert r0["ab3_core_raw_output"] == raw
    assert r0["ab3_core_extraction_status"] == "ambiguous"
    assert r0["ab3_core_completion"] is None
    assert r0["ab3_core_static"] is None


# ------------------------------------------------------------
# 4. Ab2g raw missing -> no Ab3
# ------------------------------------------------------------


def test_ab2g_raw_missing_no_ab3(tmp_path):
    attempts = [
        _attempt("HumanEval/0", "ab2g", status="failed", raw_response=None,
                  extraction_status=None),
        _attempt("HumanEval/1", "ab2g", status="success",
                  raw_response="    return x * 2\n", completion="    return x * 2\n",
                  extraction_status="extracted"),
    ]
    summary, results, _ = _run_from_attempts(tmp_path, _RAW_TASKS, attempts)
    r0 = next(r for r in results if r["task_id"] == "HumanEval/0")
    assert r0["has_ab3_target"] is False
    assert r0["ab3_core_raw_output"] is None
    assert r0["ab3_core_completion"] is None
    assert r0["ab3_full_completion"] is None
    assert r0["core_trace"] is None
    assert summary.ab2g_raw_missing_count == 1
    assert summary.ab2g_raw_available_count == 1
    assert summary.ab3_target_count == 1


# ------------------------------------------------------------
# 5 & 6. hash chain: Core input == Ab2g raw hash, Full input == Core raw hash
# ------------------------------------------------------------


def test_core_input_hash_equals_ab2g_raw_hash(tmp_path):
    raw = "    return a + b\n"
    attempts = [
        _attempt("HumanEval/0", "ab2g", status="success", raw_response=raw,
                  completion=raw, extraction_status="extracted"),
        _attempt("HumanEval/1", "ab2g", status="success",
                  raw_response="    return x * 2\n", completion="    return x * 2\n",
                  extraction_status="extracted"),
    ]
    _, results, _ = _run_from_attempts(tmp_path, _RAW_TASKS, attempts)
    r0 = next(r for r in results if r["task_id"] == "HumanEval/0")
    assert r0["ab2g_raw_response_hash"] == sha256_text(raw)
    assert r0["core_trace"]["input_hash"] == sha256_text(raw)


def test_full_input_hash_equals_core_raw_hash(tmp_path):
    raw = "    return a + b\n"
    attempts = [
        _attempt("HumanEval/0", "ab2g", status="success", raw_response=raw,
                  completion=raw, extraction_status="extracted"),
        _attempt("HumanEval/1", "ab2g", status="success",
                  raw_response="    return x * 2\n", completion="    return x * 2\n",
                  extraction_status="extracted"),
    ]
    _, results, _ = _run_from_attempts(tmp_path, _RAW_TASKS, attempts)
    r0 = next(r for r in results if r["task_id"] == "HumanEval/0")
    assert r0["spec_trace"]["input_hash"] == r0["ab3_core_raw_hash"]


# ------------------------------------------------------------
# 7 & 8. re-extraction after Core and after Full
# ------------------------------------------------------------


def test_reextraction_after_core(tmp_path):
    raw = "    return a + b\n"
    attempts = [
        _attempt("HumanEval/0", "ab2g", status="success", raw_response=raw,
                  completion=raw, extraction_status="extracted"),
        _attempt("HumanEval/1", "ab2g", status="success",
                  raw_response="    return x * 2\n", completion="    return x * 2\n",
                  extraction_status="extracted"),
    ]
    _, results, _ = _run_from_attempts(tmp_path, _RAW_TASKS, attempts)
    r0 = next(r for r in results if r["task_id"] == "HumanEval/0")
    assert r0["ab3_core_extraction_status"] == "extracted"
    # Core is a no-op identity transform here; plain_text extraction strips
    # the raw text, so the completion is the stripped form of the raw.
    assert r0["ab3_core_completion"] == raw.strip()


def test_reextraction_after_full(tmp_path):
    raw = "    return a + b\n"
    attempts = [
        _attempt("HumanEval/0", "ab2g", status="success", raw_response=raw,
                  completion=raw, extraction_status="extracted"),
        _attempt("HumanEval/1", "ab2g", status="success",
                  raw_response="    return x * 2\n", completion="    return x * 2\n",
                  extraction_status="extracted"),
    ]
    _, results, _ = _run_from_attempts(tmp_path, _RAW_TASKS, attempts)
    r0 = next(r for r in results if r["task_id"] == "HumanEval/0")
    assert r0["ab3_full_extraction_status"] == "extracted"
    assert r0["ab3_full_completion"] is not None


# ------------------------------------------------------------
# 9. extraction failure -> evaluation is None
# ------------------------------------------------------------


def test_extraction_failure_evaluation_is_none(tmp_path):
    raw = "```python\nA\n```\n```python\nB\n```"
    attempts = [
        _attempt("HumanEval/0", "ab2g", status="failed", raw_response=raw,
                  extraction_status="ambiguous"),
        _attempt("HumanEval/1", "ab2g", status="success",
                  raw_response="    return x * 2\n", completion="    return x * 2\n",
                  extraction_status="extracted"),
    ]
    _, results, _ = _run_from_attempts(tmp_path, _RAW_TASKS, attempts)
    r0 = next(r for r in results if r["task_id"] == "HumanEval/0")
    assert r0["ab3_core_completion"] is None
    assert r0["ab3_core_static"] is None
    assert r0["ab3_core_execution"] is None
    assert r0["ab3_full_completion"] is None
    assert r0["ab3_full_static"] is None
    assert r0["ab3_full_execution"] is None
    assert r0["test_status"] == "not_run"
    assert r0["test_pass"] is None


# ------------------------------------------------------------
# 10. never selects a fence among ambiguous blocks
# ------------------------------------------------------------


def test_does_not_select_any_fence_among_ambiguous(tmp_path):
    raw = "```python\nFIRST\n```\n```python\nLAST\n```"
    attempts = [
        _attempt("HumanEval/0", "ab2g", status="failed", raw_response=raw,
                  extraction_status="ambiguous"),
        _attempt("HumanEval/1", "ab2g", status="success",
                  raw_response="    return x * 2\n", completion="    return x * 2\n",
                  extraction_status="extracted"),
    ]
    _, results, _ = _run_from_attempts(tmp_path, _RAW_TASKS, attempts)
    r0 = next(r for r in results if r["task_id"] == "HumanEval/0")
    assert r0["ab3_core_completion"] is None
    assert "FIRST" not in (r0["ab3_core_completion"] or "")
    assert "LAST" not in (r0["ab3_core_completion"] or "")


# ------------------------------------------------------------
# 11. extraction.py never modified — structural check
# ------------------------------------------------------------


def test_extraction_module_never_modified_structural():
    import agent_tools.finals_rebuild.extraction as extraction_mod
    # extract_code must still expose exactly the original public contract;
    # this is a smoke check that public_benchmark_runner.py's new code
    # only *calls* extract_code() and never monkeypatches/reassigns it.
    assert callable(extraction_mod.extract_code)
    src = inspect.getsource(
        __import__("agent_tools.finals_rebuild.public_benchmark_runner", fromlist=["x"])
    )
    assert "extraction.extract_code =" not in src
    assert "extraction_mod.extract_code =" not in src


# ------------------------------------------------------------
# 12. EvalPlus JSONL only contains successfully-extracted completions
# ------------------------------------------------------------


def test_evalplus_jsonl_only_successful_completions(tmp_path):
    raw_ambiguous = "```python\nA\n```\n```python\nB\n```"
    attempts = [
        _attempt("HumanEval/0", "ab1", status="failed", raw_response=raw_ambiguous,
                  extraction_status="ambiguous"),
        _attempt("HumanEval/0", "ab2g", status="success",
                  raw_response="    return a + b\n", completion="    return a + b\n",
                  extraction_status="extracted"),
        _attempt("HumanEval/1", "ab1", status="success",
                  raw_response="    return x * 2\n", completion="    return x * 2\n",
                  extraction_status="extracted"),
        _attempt("HumanEval/1", "ab2g", status="failed", raw_response=raw_ambiguous,
                  extraction_status="ambiguous"),
    ]
    _, _, out_root = _run_from_attempts(tmp_path, _RAW_TASKS, attempts)
    evalplus_dir = out_root / "public_benchmark_raw" / "humaneval" / "evalplus"

    ab1_lines = evalplus_dir.joinpath("ab1.jsonl").read_text(encoding="utf-8").splitlines()
    ab2g_lines = evalplus_dir.joinpath("ab2g.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(ab1_lines) == 1  # only HumanEval/1's Ab1 extracted
    assert json.loads(ab1_lines[0])["task_id"] == "HumanEval/1"
    assert len(ab2g_lines) == 1  # only HumanEval/0's Ab2g extracted
    assert json.loads(ab2g_lines[0])["task_id"] == "HumanEval/0"

    # HumanEval/1's Ab2g is ambiguous -> no Ab3 completion for it either.
    ab3_core_lines = evalplus_dir.joinpath("ab3_core.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(ab3_core_lines) == 1
    assert json.loads(ab3_core_lines[0])["task_id"] == "HumanEval/0"

    # Zero-success treatments still produce a valid (empty) file.
    assert evalplus_dir.joinpath("ab3_full.jsonl").exists()


# ------------------------------------------------------------
# 13. summary counts correct
# ------------------------------------------------------------


def test_raw_summary_counts_correct(tmp_path):
    raw_ambiguous = "```python\nA\n```\n```python\nB\n```"
    attempts = [
        _attempt("HumanEval/0", "ab2g", status="success",
                  raw_response="    return a + b\n", completion="    return a + b\n",
                  extraction_status="extracted"),
        _attempt("HumanEval/1", "ab2g", status="failed", raw_response=raw_ambiguous,
                  extraction_status="ambiguous"),
    ]
    summary, _, _ = _run_from_attempts(tmp_path, _RAW_TASKS, attempts)
    assert summary.total_tasks == 2
    assert summary.ab1_available_count == 0
    assert summary.ab1_missing_count == 2
    assert summary.ab2g_raw_available_count == 2
    assert summary.ab2g_raw_missing_count == 0
    assert summary.ab2g_extraction_success_count == 1
    assert summary.ab2g_extraction_failure_count == 1
    assert summary.ab3_target_count == 2
    assert summary.ab3_core_extraction_success_count == 1
    assert summary.ab3_core_extraction_failure_count == 1
    assert "pass_at_1" not in json.dumps(_raw_summary_to_dict_for_test(summary))


def _raw_summary_to_dict_for_test(summary):
    import agent_tools.finals_rebuild.public_benchmark_runner as mod
    return mod._raw_summary_to_dict(summary)


# ------------------------------------------------------------
# Identity / fail-closed
# ------------------------------------------------------------


def test_task_missing_ab2g_attempt_fails_closed(tmp_path):
    attempts = [
        _attempt("HumanEval/0", "ab2g", status="success",
                  raw_response="    return a + b\n", completion="    return a + b\n",
                  extraction_status="extracted"),
        # HumanEval/1 has no ab2g attempt at all.
    ]
    with pytest.raises(PublicBenchmarkRunnerError, match="no Ab2g generation attempt"):
        _run_from_attempts(tmp_path, _RAW_TASKS, attempts)


def test_duplicate_attempt_fails_closed(tmp_path):
    attempts = [
        _attempt("HumanEval/0", "ab2g", status="success",
                  raw_response="    return a + b\n", completion="    return a + b\n",
                  extraction_status="extracted"),
        _attempt("HumanEval/0", "ab2g", status="success",
                  raw_response="    return a + b\n", completion="    return a + b\n",
                  extraction_status="extracted"),
        _attempt("HumanEval/1", "ab2g", status="success",
                  raw_response="    return x * 2\n", completion="    return x * 2\n",
                  extraction_status="extracted"),
    ]
    with pytest.raises(PublicBenchmarkRunnerError, match="duplicate generation attempt"):
        _run_from_attempts(tmp_path, _RAW_TASKS, attempts)


def test_unknown_task_id_in_attempts_fails_closed(tmp_path):
    attempts = [
        _attempt("HumanEval/0", "ab2g", status="success",
                  raw_response="    return a + b\n", completion="    return a + b\n",
                  extraction_status="extracted"),
        _attempt("HumanEval/1", "ab2g", status="success",
                  raw_response="    return x * 2\n", completion="    return x * 2\n",
                  extraction_status="extracted"),
        _attempt("HumanEval/999", "ab2g", status="success",
                  raw_response="    return 0\n", completion="    return 0\n",
                  extraction_status="extracted"),
    ]
    with pytest.raises(PublicBenchmarkRunnerError, match="unknown task_id"):
        _run_from_attempts(tmp_path, _RAW_TASKS, attempts)


def test_ab2g_raw_hash_mismatch_fails_closed(tmp_path):
    attempts = [
        {
            **_attempt("HumanEval/0", "ab2g", status="success",
                       raw_response="    return a + b\n", completion="    return a + b\n",
                       extraction_status="extracted"),
            "raw_response_sha256": "0" * 64,  # deliberately wrong
        },
        _attempt("HumanEval/1", "ab2g", status="success",
                  raw_response="    return x * 2\n", completion="    return x * 2\n",
                  extraction_status="extracted"),
    ]
    with pytest.raises(PublicBenchmarkRunnerError, match="does not match"):
        _run_from_attempts(tmp_path, _RAW_TASKS, attempts)


# ------------------------------------------------------------
# 14. existing full Ab1/Ab2g test still pass (see rest of this file above);
# additional sanity: load_generation_attempts() itself
# ------------------------------------------------------------


def test_load_generation_attempts_missing_file(tmp_path):
    with pytest.raises(PublicBenchmarkRunnerError, match="not found"):
        load_generation_attempts(tmp_path / "missing.jsonl")


def test_load_generation_attempts_missing_field(tmp_path):
    path = tmp_path / "attempts.jsonl"
    path.write_text(json.dumps({"task_id": "HumanEval/0"}) + "\n", encoding="utf-8")
    with pytest.raises(PublicBenchmarkRunnerError, match="missing required field"):
        load_generation_attempts(path)


def test_load_generation_attempts_reads_real_schema(tmp_path):
    attempts = [_attempt("HumanEval/0", "ab1", raw_response="x", completion="x", extraction_status="extracted")]
    path = _write_attempts_jsonl(tmp_path, attempts)
    loaded = load_generation_attempts(path)
    assert len(loaded) == 1
    assert loaded[0]["task_id"] == "HumanEval/0"
