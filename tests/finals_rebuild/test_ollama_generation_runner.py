"""
Tests for agent_tools/finals_rebuild/ollama_generation_runner.py

All Ollama HTTP calls are mocked at the urllib.request.urlopen boundary —
this suite never calls a real model. Extraction itself is delegated to the
real, unmocked agent_tools.finals_rebuild.extraction.extract_code().
run_public_benchmark_treatments() is monkeypatched where its invocation
(not its internal behavior) is under test.
"""

from __future__ import annotations

import io
import json
import os
import sys
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import pytest

import agent_tools.finals_rebuild.ollama_generation_runner as runner
from agent_tools.finals_rebuild.benchmarks_adapter import (
    PublicBenchmarkTask,
    load_benchmark_completions,
)
from agent_tools.finals_rebuild.ollama_generation_runner import (
    AB2G_SCAFFOLD,
    MODEL,
    OllamaGenerationError,
    SEED,
    TEMPERATURE,
    THINK,
    analyze_extraction,
    build_arg_parser,
    build_prompt,
    build_summary,
    check_ab2g_complete,
    main,
    run_attempt,
    run_generation_attempts,
    run_ollama_generation,
    run_treatment_stage,
    validate_raw_response,
)


_TASK_0 = PublicBenchmarkTask(
    benchmark="humaneval", task_id="HumanEval/0",
    prompt="def has_close_elements(numbers, threshold):\n    \"\"\"doc\"\"\"\n",
    entry_point="has_close_elements", canonical_solution=None,
)
_TASK_1 = PublicBenchmarkTask(
    benchmark="humaneval", task_id="HumanEval/1",
    prompt="def separate_paren_groups(s):\n    \"\"\"doc\"\"\"\n",
    entry_point="separate_paren_groups", canonical_solution=None,
)


def _write_tasks(tmp_path, tasks):
    path = tmp_path / "tasks.json"
    records = [
        {"task_id": t.task_id, "prompt": t.prompt, "entry_point": t.entry_point}
        for t in tasks
    ]
    path.write_text(json.dumps(records), encoding="utf-8")
    return path


class _FakeResponse:
    def __init__(self, body: dict, status: int = 200):
        self._body = json.dumps(body).encode("utf-8")
        self._status = status

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self):
        return self._body

    def getcode(self):
        return self._status


_FAKE_DIGEST = "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
_FAKE_MODEL_ENTRY = {
    "name": MODEL,
    "digest": _FAKE_DIGEST,
    "size": 5200000000,
    "modified_at": "2026-01-01T00:00:00Z",
}
_FAKE_VERSION_BODY = {"version": "0.31.2"}


def _install_fake_urlopen(monkeypatch, tags_body=None, generate_bodies=None,
                          http_error=None, timeout_error=False,
                          version_body=None, version_http_error=None):
    """generate_bodies: list of dicts, consumed in call order for POST /api/generate."""
    tags_body = tags_body if tags_body is not None else {"models": [dict(_FAKE_MODEL_ENTRY)]}
    version_body = version_body if version_body is not None else dict(_FAKE_VERSION_BODY)
    generate_bodies = list(generate_bodies or [])
    calls = {"urls": [], "payloads": []}

    def fake_urlopen(req, timeout=None):
        url = req.full_url
        calls["urls"].append(url)
        if url.endswith("/api/tags"):
            if timeout_error and not generate_bodies:
                raise TimeoutError("timed out")
            if http_error and not generate_bodies:
                raise urllib.error.HTTPError(url, http_error, "err", {}, io.BytesIO(b""))
            return _FakeResponse(tags_body)
        if url.endswith("/api/version"):
            if version_http_error:
                raise urllib.error.HTTPError(url, version_http_error, "err", {}, io.BytesIO(b""))
            return _FakeResponse(version_body)
        if url.endswith("/api/generate"):
            if timeout_error:
                raise TimeoutError("timed out")
            if http_error:
                raise urllib.error.HTTPError(url, http_error, "err", {}, io.BytesIO(b""))
            calls["payloads"].append(json.loads(req.data.decode("utf-8")))
            body = generate_bodies.pop(0)
            return _FakeResponse(body)
        raise AssertionError(f"unexpected URL {url}")

    monkeypatch.setattr(runner.urllib.request, "urlopen", fake_urlopen)
    return calls


_FENCED_OK = {"response": "```python\n    return True\n```"}
_AMBIGUOUS = {"response": "```python\nA\n```\n```python\nB\n```"}


# ============================================================
# Prompt construction (Ab1 no scaffold, Ab2g fixed scaffold)
# ============================================================


def test_ab1_prompt_has_no_scaffold():
    prompt = build_prompt(_TASK_0.prompt, "ab1")
    assert prompt == _TASK_0.prompt
    assert AB2G_SCAFFOLD not in prompt


def test_ab2g_prompt_has_fixed_scaffold():
    prompt = build_prompt(_TASK_0.prompt, "ab2g")
    assert prompt == _TASK_0.prompt + AB2G_SCAFFOLD


def test_generate_payload_has_think_false_and_fixed_params(monkeypatch):
    calls = _install_fake_urlopen(monkeypatch, generate_bodies=[_FENCED_OK])
    runner._post_generate("PROMPT", runner.DEFAULT_BASE_URL, 5.0)
    payload = calls["payloads"][0]
    assert payload["think"] is False
    assert payload["model"] == MODEL
    assert payload["options"]["seed"] == SEED
    assert payload["options"]["temperature"] == TEMPERATURE
    assert payload["stream"] is False


# ============================================================
# 1. first attempt fails, second still runs
# ============================================================


def test_first_attempt_fails_second_still_runs(monkeypatch):
    _install_fake_urlopen(monkeypatch, generate_bodies=[_AMBIGUOUS, _FENCED_OK])
    attempts = run_generation_attempts(
        [_TASK_0], benchmark="humaneval",
        base_url=runner.DEFAULT_BASE_URL, timeout_seconds=5.0,
    )
    assert len(attempts) == 2
    assert attempts[0]["treatment"] == "ab1"
    assert attempts[0]["status"] == "failed"
    assert attempts[1]["treatment"] == "ab2g"
    assert attempts[1]["status"] == "success"


# ============================================================
# 2. Ab1 failure does not block same task's Ab2g
# ============================================================


def test_ab1_failure_does_not_block_ab2g(monkeypatch):
    _install_fake_urlopen(monkeypatch, generate_bodies=[_AMBIGUOUS, _FENCED_OK])
    attempts = run_generation_attempts(
        [_TASK_0], benchmark="humaneval",
        base_url=runner.DEFAULT_BASE_URL, timeout_seconds=5.0,
    )
    ab1 = next(a for a in attempts if a["treatment"] == "ab1")
    ab2g = next(a for a in attempts if a["treatment"] == "ab2g")
    assert ab1["status"] == "failed"
    assert ab2g["status"] == "success"
    assert ab1["task_id"] == ab2g["task_id"] == "HumanEval/0"


# ============================================================
# 3. ambiguous extraction recorded as failed
# ============================================================


def test_ambiguous_extraction_recorded_failed():
    analysis = analyze_extraction("```python\nA\n```\n```python\nB\n```")
    assert analysis["ok"] is False
    assert analysis["extraction_status"] == "ambiguous"


def test_ambiguous_attempt_has_failed_status(monkeypatch):
    _install_fake_urlopen(monkeypatch, generate_bodies=[_AMBIGUOUS])
    attempt = run_attempt(
        _TASK_0, "ab1", benchmark="humaneval",
        base_url=runner.DEFAULT_BASE_URL, timeout_seconds=5.0,
    )
    assert attempt["status"] == "failed"
    assert attempt["failure_stage"] == "extraction"
    assert attempt["extraction_status"] == "ambiguous"
    assert attempt["python_fenced_blocks"] == 2


# ============================================================
# 4. failed attempt still saves raw response
# ============================================================


def test_failed_extraction_attempt_saves_raw_response(monkeypatch):
    _install_fake_urlopen(monkeypatch, generate_bodies=[_AMBIGUOUS])
    attempt = run_attempt(
        _TASK_0, "ab1", benchmark="humaneval",
        base_url=runner.DEFAULT_BASE_URL, timeout_seconds=5.0,
    )
    assert attempt["raw_response"] == _AMBIGUOUS["response"]
    assert attempt["raw_response_sha256"] == runner.sha256_text(_AMBIGUOUS["response"])


def test_failed_validation_attempt_saves_raw_response(monkeypatch):
    body = {"response": "<think>reasoning</think>\n    return True\n"}
    _install_fake_urlopen(monkeypatch, generate_bodies=[body])
    attempt = run_attempt(
        _TASK_0, "ab1", benchmark="humaneval",
        base_url=runner.DEFAULT_BASE_URL, timeout_seconds=5.0,
    )
    assert attempt["status"] == "failed"
    assert attempt["failure_stage"] == "response_validation"
    assert attempt["raw_response"] == body["response"]


def test_failed_request_attempt_has_null_raw_response(monkeypatch):
    _install_fake_urlopen(monkeypatch, http_error=500)
    attempt = run_attempt(
        _TASK_0, "ab1", benchmark="humaneval",
        base_url=runner.DEFAULT_BASE_URL, timeout_seconds=5.0,
    )
    assert attempt["status"] == "failed"
    assert attempt["failure_stage"] == "ollama_request"
    assert attempt["raw_response"] is None
    assert attempt["raw_response_sha256"] is None


# ============================================================
# 5. failed attempt completion is null
# ============================================================


def test_failed_attempt_completion_is_null(monkeypatch):
    _install_fake_urlopen(monkeypatch, generate_bodies=[_AMBIGUOUS])
    attempt = run_attempt(
        _TASK_0, "ab1", benchmark="humaneval",
        base_url=runner.DEFAULT_BASE_URL, timeout_seconds=5.0,
    )
    assert attempt["completion"] is None
    assert attempt["completion_sha256"] is None


# ============================================================
# 6. success attempt writes to treatment JSONL
# ============================================================


def test_success_attempt_writes_treatment_jsonl(monkeypatch, tmp_path):
    tasks_path = _write_tasks(tmp_path, [_TASK_0])
    _install_fake_urlopen(monkeypatch, generate_bodies=[_FENCED_OK, _AMBIGUOUS])
    out_dir = tmp_path / "out"
    run_ollama_generation(
        tasks_path=tasks_path, benchmark="humaneval", output_dir=out_dir,
        base_url=runner.DEFAULT_BASE_URL, timeout_seconds=5.0,
    )
    ab1_lines = (out_dir / "ab1.jsonl").read_text(encoding="utf-8").splitlines()
    ab2g_lines = (out_dir / "ab2g.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(ab1_lines) == 1
    assert len(ab2g_lines) == 0  # ambiguous -> failed -> not written
    rec = json.loads(ab1_lines[0])
    assert rec["task_id"] == "HumanEval/0"
    assert rec["completion"] == "    return True\n"


# ============================================================
# 7. zero successes still creates empty JSONL
# ============================================================


def test_zero_successes_creates_empty_jsonl(monkeypatch, tmp_path):
    tasks_path = _write_tasks(tmp_path, [_TASK_0])
    _install_fake_urlopen(monkeypatch, generate_bodies=[_AMBIGUOUS, _AMBIGUOUS])
    out_dir = tmp_path / "out"
    run_ollama_generation(
        tasks_path=tasks_path, benchmark="humaneval", output_dir=out_dir,
        base_url=runner.DEFAULT_BASE_URL, timeout_seconds=5.0,
    )
    assert (out_dir / "ab1.jsonl").exists()
    assert (out_dir / "ab2g.jsonl").exists()
    assert (out_dir / "ab1.jsonl").read_text(encoding="utf-8") == ""
    assert (out_dir / "ab2g.jsonl").read_text(encoding="utf-8") == ""
    # raw files must still contain the failed attempts' raw responses
    raw_lines = (out_dir / "ab1_raw.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(raw_lines) == 1
    assert json.loads(raw_lines[0])["raw_response"] == _AMBIGUOUS["response"]


# ============================================================
# 8. summary counts correct
# ============================================================


def test_summary_counts_correct(monkeypatch):
    _install_fake_urlopen(
        monkeypatch, generate_bodies=[_AMBIGUOUS, _FENCED_OK, _FENCED_OK, _FENCED_OK]
    )
    attempts = run_generation_attempts(
        [_TASK_0, _TASK_1], benchmark="humaneval",
        base_url=runner.DEFAULT_BASE_URL, timeout_seconds=5.0,
    )
    summary = build_summary(attempts)
    assert summary["total_attempts"] == 4
    assert summary["successful_attempts"] == 3
    assert summary["failed_attempts"] == 1
    assert summary["ab1_attempts"] == 2
    assert summary["ab1_successes"] == 1
    assert summary["ab1_failures"] == 1
    assert summary["ab2g_attempts"] == 2
    assert summary["ab2g_successes"] == 2
    assert summary["ab2g_failures"] == 0
    assert summary["extraction_ambiguous_count"] == 1
    assert summary["extraction_empty_count"] == 0
    assert summary["api_failure_count"] == 0
    assert summary["fence_count"] == 4
    assert "pass_at_1" not in summary
    assert "pass@1" not in summary


# ============================================================
# 9. output order fixed: task order, then Ab1, Ab2g
# ============================================================


def test_attempt_order_is_task_then_ab1_ab2g(monkeypatch):
    _install_fake_urlopen(
        monkeypatch, generate_bodies=[_FENCED_OK, _FENCED_OK, _FENCED_OK, _FENCED_OK]
    )
    attempts = run_generation_attempts(
        [_TASK_0, _TASK_1], benchmark="humaneval",
        base_url=runner.DEFAULT_BASE_URL, timeout_seconds=5.0,
    )
    order = [(a["task_id"], a["treatment"]) for a in attempts]
    assert order == [
        ("HumanEval/0", "ab1"), ("HumanEval/0", "ab2g"),
        ("HumanEval/1", "ab1"), ("HumanEval/1", "ab2g"),
    ]


# ============================================================
# 10. reruns deterministic
# ============================================================


def test_manifest_deterministic_across_reruns(monkeypatch, tmp_path):
    tasks_path = _write_tasks(tmp_path, [_TASK_0])

    def _bodies():
        return [_FENCED_OK, _FENCED_OK]

    _install_fake_urlopen(monkeypatch, generate_bodies=_bodies())
    out1 = tmp_path / "out1"
    run_ollama_generation(
        tasks_path=tasks_path, benchmark="humaneval", output_dir=out1,
        base_url=runner.DEFAULT_BASE_URL, timeout_seconds=5.0,
    )

    _install_fake_urlopen(monkeypatch, generate_bodies=_bodies())
    out2 = tmp_path / "out2"
    run_ollama_generation(
        tasks_path=tasks_path, benchmark="humaneval", output_dir=out2,
        base_url=runner.DEFAULT_BASE_URL, timeout_seconds=5.0,
    )

    s1 = json.loads((out1 / "generation_summary.json").read_text(encoding="utf-8"))
    s2 = json.loads((out2 / "generation_summary.json").read_text(encoding="utf-8"))
    assert s1 == s2

    for name in ("ab1.jsonl", "ab2g.jsonl", "ab1_raw.jsonl", "ab2g_raw.jsonl", "generation_attempts.jsonl"):
        c1 = (out1 / name).read_text(encoding="utf-8")
        c2 = (out2 / name).read_text(encoding="utf-8")
        # elapsed_seconds is wall-clock and not compared; compare the rest.
        recs1 = [json.loads(l) for l in c1.splitlines()]
        recs2 = [json.loads(l) for l in c2.splitlines()]
        for r1, r2 in zip(recs1, recs2):
            r1.pop("elapsed_seconds", None)
            r2.pop("elapsed_seconds", None)
            if isinstance(r1.get("metadata"), dict):
                r1["metadata"].pop("generation_seconds", None)
            if isinstance(r2.get("metadata"), dict):
                r2["metadata"].pop("generation_seconds", None)
            assert r1 == r2


# ============================================================
# 11. never selects first/last fence among ambiguous blocks
# ============================================================


def test_does_not_select_first_or_last_of_ambiguous_blocks():
    raw = "```python\nFIRST\n```\n```python\nLAST\n```"
    analysis = analyze_extraction(raw)
    assert analysis["ok"] is False
    assert analysis["completion"] is None
    assert analysis["extraction_status"] == "ambiguous"


# ============================================================
# 12. extraction.py is never imported for writing / never modified —
# structural check: this module only calls extract_code(), never defines
# its own fence-selection helper that returns a code string.
# ============================================================


def test_module_only_uses_extract_code_for_extraction():
    import inspect
    src = inspect.getsource(runner)
    # extract_code is the only extraction entrypoint used.
    assert "extract_code(" in src
    # No local re-implementation of fence stripping/selection logic.
    assert "def strip_fence" not in src
    assert "def pick_code_block" not in src


# ============================================================
# 13 & 14. treatment runner gating
# ============================================================


def test_treatment_stage_runs_when_ab2g_complete(monkeypatch, tmp_path):
    tasks = [_TASK_0, _TASK_1]
    attempts = [
        {"task_id": "HumanEval/0", "treatment": "ab2g", "status": "success"},
        {"task_id": "HumanEval/1", "treatment": "ab2g", "status": "success"},
    ]
    called = {}

    def _fake_run_public_benchmark_treatments(**kwargs):
        called.update(kwargs)
        return {"status": "ok"}

    monkeypatch.setattr(runner, "run_public_benchmark_treatments", _fake_run_public_benchmark_treatments)
    result = run_treatment_stage(
        tasks=tasks, attempts=attempts,
        tasks_path="tasks.json", ab1_completions_path="ab1.jsonl",
        ab2g_completions_path="ab2g.jsonl", benchmark="humaneval",
        artifact_root=str(tmp_path), evaluator_git_commit="deadbeef",
    )
    assert result["ran"] is True
    assert result["missing_ab2g_task_ids"] == []
    assert called  # run_public_benchmark_treatments was actually invoked


def test_treatment_stage_skipped_when_ab2g_incomplete(monkeypatch, tmp_path):
    tasks = [_TASK_0, _TASK_1]
    attempts = [
        {"task_id": "HumanEval/0", "treatment": "ab2g", "status": "success"},
        {"task_id": "HumanEval/1", "treatment": "ab2g", "status": "failed"},
    ]
    called = {"invoked": False}

    def _fake_run_public_benchmark_treatments(**kwargs):
        called["invoked"] = True
        return {"status": "ok"}

    monkeypatch.setattr(runner, "run_public_benchmark_treatments", _fake_run_public_benchmark_treatments)
    result = run_treatment_stage(
        tasks=tasks, attempts=attempts,
        tasks_path="tasks.json", ab1_completions_path="ab1.jsonl",
        ab2g_completions_path="ab2g.jsonl", benchmark="humaneval",
        artifact_root=str(tmp_path), evaluator_git_commit="deadbeef",
    )
    assert result["ran"] is False
    assert result["missing_ab2g_task_ids"] == ["HumanEval/1"]
    assert called["invoked"] is False


def test_check_ab2g_complete():
    tasks = [_TASK_0, _TASK_1]
    attempts = [
        {"task_id": "HumanEval/0", "treatment": "ab2g", "status": "success"},
        {"task_id": "HumanEval/1", "treatment": "ab2g", "status": "failed"},
        {"task_id": "HumanEval/0", "treatment": "ab1", "status": "failed"},
    ]
    complete, missing = check_ab2g_complete(tasks, attempts)
    assert complete is False
    assert missing == ["HumanEval/1"]


# ============================================================
# Extraction correctness (single fence, prose + fence)
# ============================================================


def test_single_fenced_code_extracts():
    analysis = analyze_extraction("```python\n    return True\n```")
    assert analysis["ok"] is True
    assert analysis["completion"] == "    return True\n"
    assert analysis["had_markdown_fence"] is True
    assert analysis["had_surrounding_text"] is False


def test_prose_plus_single_fenced_code_extracts():
    raw = "Here is the solution:\n\n```python\n    return True\n```\n\nLet me know!"
    analysis = analyze_extraction(raw)
    assert analysis["ok"] is True
    assert analysis["completion"] == "    return True\n"
    assert analysis["had_markdown_fence"] is True
    assert analysis["had_surrounding_text"] is True


def test_no_fence_no_surrounding_text():
    analysis = analyze_extraction("    return True\n")
    assert analysis["ok"] is True
    assert analysis["had_markdown_fence"] is False
    assert analysis["had_surrounding_text"] is False


def test_empty_fenced_block_fails():
    analysis = analyze_extraction("```python\n\n```")
    assert analysis["ok"] is False
    assert analysis["extraction_status"] == "empty"


# ============================================================
# <think> / thinking leak fails closed (per-attempt, at the
# response_validation stage)
# ============================================================


def test_think_tag_in_response_fails_closed():
    raw = {"response": "<think>reasoning</think>\n    return True\n"}
    with pytest.raises(OllamaGenerationError, match="think"):
        validate_raw_response(raw)


def test_thinking_field_fails_closed():
    raw = {"response": "    return True\n", "thinking": "some reasoning"}
    with pytest.raises(OllamaGenerationError, match="thinking"):
        validate_raw_response(raw)


def test_empty_response_field_fails_closed():
    with pytest.raises(OllamaGenerationError, match="empty or missing"):
        validate_raw_response({"response": "   "})


# ============================================================
# Ab1/Ab2g share identical API/extraction/validation/schema
# ============================================================


def test_ab1_and_ab2g_use_same_extraction_and_schema(monkeypatch):
    _install_fake_urlopen(monkeypatch, generate_bodies=[_FENCED_OK, _FENCED_OK])
    ab1 = run_attempt(_TASK_0, "ab1", benchmark="humaneval", base_url=runner.DEFAULT_BASE_URL, timeout_seconds=5.0)
    ab2g = run_attempt(_TASK_0, "ab2g", benchmark="humaneval", base_url=runner.DEFAULT_BASE_URL, timeout_seconds=5.0)
    assert ab1["completion"] == ab2g["completion"]
    assert ab1["extraction_method"] == ab2g["extraction_method"]
    assert set(ab1.keys()) == set(ab2g.keys())
    for key in ("model", "seed", "temperature", "think"):
        assert ab1["metadata"][key] == ab2g["metadata"][key]


# ============================================================
# API timeout / non-200 fail closed as a per-attempt failure
# ============================================================


def test_generate_timeout_is_attempt_failure(monkeypatch):
    _install_fake_urlopen(monkeypatch, timeout_error=True)
    attempt = run_attempt(_TASK_0, "ab1", benchmark="humaneval", base_url=runner.DEFAULT_BASE_URL, timeout_seconds=1.0)
    assert attempt["status"] == "failed"
    assert attempt["failure_stage"] == "ollama_request"


def test_generate_http_error_is_attempt_failure(monkeypatch):
    _install_fake_urlopen(monkeypatch, http_error=500)
    attempt = run_attempt(_TASK_0, "ab1", benchmark="humaneval", base_url=runner.DEFAULT_BASE_URL, timeout_seconds=5.0)
    assert attempt["status"] == "failed"
    assert attempt["failure_stage"] == "ollama_request"


# ============================================================
# model tags preflight (still a whole-run abort — nothing can succeed)
# ============================================================


def test_model_not_in_tags_fails_closed(monkeypatch):
    _install_fake_urlopen(monkeypatch, tags_body={"models": [{"name": "llama3:8b"}]})
    with pytest.raises(OllamaGenerationError, match="not found in /api/tags"):
        runner.check_model_available(runner.DEFAULT_BASE_URL, 5.0)


def test_model_unavailable_blocks_full_run(monkeypatch, tmp_path):
    tasks_path = _write_tasks(tmp_path, [_TASK_0])
    _install_fake_urlopen(monkeypatch, tags_body={"models": [{"name": "llama3:8b"}]})
    with pytest.raises(OllamaGenerationError, match="not found in /api/tags"):
        run_ollama_generation(
            tasks_path=tasks_path, benchmark="humaneval", output_dir=tmp_path / "out",
            base_url=runner.DEFAULT_BASE_URL, timeout_seconds=5.0,
        )
    assert not (tmp_path / "out" / "generation_summary.json").exists()


# ============================================================
# output JSONL loadable by load_benchmark_completions()
# ============================================================


def test_output_jsonl_loadable_by_benchmarks_adapter(monkeypatch, tmp_path):
    tasks_path = _write_tasks(tmp_path, [_TASK_0])
    _install_fake_urlopen(monkeypatch, generate_bodies=[_FENCED_OK, _FENCED_OK])
    out_dir = tmp_path / "out"
    run_ollama_generation(
        tasks_path=tasks_path, benchmark="humaneval", output_dir=out_dir,
        base_url=runner.DEFAULT_BASE_URL, timeout_seconds=5.0,
    )
    loaded = load_benchmark_completions(out_dir / "ab1.jsonl", "humaneval", "ab1")
    assert len(loaded) == 1
    assert loaded[0].task_id == "HumanEval/0"
    assert loaded[0].completion == "    return True\n"


# ============================================================
# CLI
# ============================================================


def test_cli_parser_basic():
    parser = build_arg_parser()
    args = parser.parse_args([
        "--tasks-path", "t.json", "--benchmark", "humaneval", "--output-dir", "out",
    ])
    assert args.tasks_path == "t.json"
    assert args.benchmark == "humaneval"
    assert args.base_url == runner.DEFAULT_BASE_URL


def test_main_returns_nonzero_on_preflight_failure(monkeypatch, tmp_path):
    tasks_path = _write_tasks(tmp_path, [_TASK_0])
    _install_fake_urlopen(monkeypatch, tags_body={"models": []})
    exit_code = main([
        "--tasks-path", str(tasks_path), "--benchmark", "humaneval",
        "--output-dir", str(tmp_path / "out"),
    ])
    assert exit_code == 1


def test_main_returns_zero_even_with_some_failed_attempts(monkeypatch, tmp_path):
    tasks_path = _write_tasks(tmp_path, [_TASK_0])
    _install_fake_urlopen(monkeypatch, generate_bodies=[_AMBIGUOUS, _FENCED_OK])
    exit_code = main([
        "--tasks-path", str(tasks_path), "--benchmark", "humaneval",
        "--output-dir", str(tmp_path / "out"),
        "--runner-git-commit", "deadbeef",
    ])
    assert exit_code == 0
    assert (tmp_path / "out" / "generation_summary.json").exists()


# ============================================================
# Ollama provenance (model digest / server version) in the manifest
# ============================================================


def _run_full(monkeypatch, tmp_path, **urlopen_kwargs):
    tasks_path = _write_tasks(tmp_path, [_TASK_0])
    _install_fake_urlopen(
        monkeypatch,
        generate_bodies=urlopen_kwargs.pop("generate_bodies", [_FENCED_OK, _FENCED_OK]),
        **urlopen_kwargs,
    )
    out_dir = tmp_path / "out"
    run_ollama_generation(
        tasks_path=tasks_path, benchmark="humaneval", output_dir=out_dir,
        base_url=runner.DEFAULT_BASE_URL, timeout_seconds=5.0,
        runner_git_commit="deadbeef",
    )
    return json.loads((out_dir / "generation_manifest.json").read_text(encoding="utf-8"))


def test_manifest_records_model_digest(monkeypatch, tmp_path):
    manifest = _run_full(monkeypatch, tmp_path)
    assert manifest["model_digest"] == _FAKE_DIGEST
    assert manifest["model_name"] == MODEL
    assert manifest["model_size"] == _FAKE_MODEL_ENTRY["size"]
    assert manifest["model_modified_at"] == _FAKE_MODEL_ENTRY["modified_at"]
    assert manifest["api_base_url"] == runner.DEFAULT_BASE_URL


def test_manifest_records_ollama_version(monkeypatch, tmp_path):
    manifest = _run_full(monkeypatch, tmp_path)
    assert manifest["ollama_version"] == "0.31.2"


def test_manifest_records_run_parameters(monkeypatch, tmp_path):
    manifest = _run_full(monkeypatch, tmp_path)
    assert manifest["runner_git_commit"] == "deadbeef"
    assert manifest["benchmark"] == "humaneval"
    assert manifest["model"] == MODEL
    assert manifest["seed"] == SEED
    assert manifest["temperature"] == TEMPERATURE
    assert manifest["think"] is THINK
    assert manifest["timeout_seconds"] == 5.0


def test_missing_digest_fails_closed(monkeypatch, tmp_path):
    tags_body = {"models": [{"name": MODEL}]}  # no digest field
    _install_fake_urlopen(monkeypatch, tags_body=tags_body)
    with pytest.raises(OllamaGenerationError, match="no digest"):
        runner.fetch_ollama_provenance(runner.DEFAULT_BASE_URL, 5.0)


def test_blank_digest_fails_closed(monkeypatch):
    tags_body = {"models": [{"name": MODEL, "digest": "   "}]}
    _install_fake_urlopen(monkeypatch, tags_body=tags_body)
    with pytest.raises(OllamaGenerationError, match="no digest"):
        runner.fetch_ollama_provenance(runner.DEFAULT_BASE_URL, 5.0)


def test_version_endpoint_http_error_fails_closed(monkeypatch):
    _install_fake_urlopen(monkeypatch, version_http_error=500)
    with pytest.raises(OllamaGenerationError, match="status 500"):
        runner.fetch_ollama_provenance(runner.DEFAULT_BASE_URL, 5.0)


def test_blank_version_fails_closed(monkeypatch):
    _install_fake_urlopen(monkeypatch, version_body={"version": "   "})
    with pytest.raises(OllamaGenerationError, match="no usable version"):
        runner.fetch_ollama_provenance(runner.DEFAULT_BASE_URL, 5.0)


def test_model_missing_from_tags_provenance_fails_closed(monkeypatch):
    _install_fake_urlopen(monkeypatch, tags_body={"models": [{"name": "llama3:8b", "digest": "sha256:x"}]})
    with pytest.raises(OllamaGenerationError, match="not found in /api/tags"):
        runner.fetch_ollama_provenance(runner.DEFAULT_BASE_URL, 5.0)


def test_digest_failure_blocks_full_run_before_any_attempt(monkeypatch, tmp_path):
    tasks_path = _write_tasks(tmp_path, [_TASK_0])
    calls = _install_fake_urlopen(monkeypatch, tags_body={"models": [{"name": MODEL}]})
    with pytest.raises(OllamaGenerationError, match="no digest"):
        run_ollama_generation(
            tasks_path=tasks_path, benchmark="humaneval", output_dir=tmp_path / "out",
            base_url=runner.DEFAULT_BASE_URL, timeout_seconds=5.0,
            runner_git_commit="deadbeef",
        )
    assert not any(u.endswith("/api/generate") for u in calls["urls"])
    assert not (tmp_path / "out" / "generation_manifest.json").exists()


def test_manifest_deterministic_fields_stable(monkeypatch, tmp_path):
    m1 = _run_full(monkeypatch, tmp_path)
    tmp2 = tmp_path / "second"
    tmp2.mkdir()
    m2 = _run_full(monkeypatch, tmp2)
    assert m1 == m2
