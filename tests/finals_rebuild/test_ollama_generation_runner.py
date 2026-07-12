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
import pathlib
import sys
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import pytest

import agent_tools.finals_rebuild.ollama_generation_runner as runner
from agent_tools.finals_rebuild.benchmarks_adapter import (
    PublicBenchmarkTask,
    load_benchmark_completions,
    load_benchmark_tasks,
)
from agent_tools.finals_rebuild.humaneval_plus_dataset import prepare_tasks_file, sha256_file
from agent_tools.finals_rebuild.ollama_generation_runner import (
    AB2G_SCAFFOLD,
    ANALYSIS_STATUS_SMOKE_EXCLUDED,
    ATTEMPT_POLICY_CONFIRMATORY,
    ATTEMPT_POLICY_ENGINEERING_SMOKE,
    DEFAULT_MODEL_8B,
    DEFAULT_SMOKE_MODEL,
    MODEL,
    NUM_PREDICT,
    OllamaGenerationError,
    OllamaGenerationSettings,
    RUN_TYPE_SMOKE,
    SEED,
    SMOKE_MODEL_DIGEST_PREFIX,
    SMOKE_TASK_COUNT,
    TASK_SELECTION_POLICY_FIRST_N,
    TEMPERATURE,
    TOP_K,
    TOP_P,
    TREATMENT_DERIVATION_MODE,
    analyze_extraction,
    attempt_policy_manifest_fields,
    build_arg_parser,
    build_prompt,
    build_summary,
    check_ab2g_complete,
    default_smoke_output_dir,
    detect_reasoning_leakage,
    entry_point_preflight,
    is_resume_complete,
    load_all_saved_attempts,
    load_completed_attempts,
    main,
    run_attempt,
    run_engineering_smoke_pipeline,
    run_generation_attempts,
    run_offline_artifact_replay,
    run_ollama_generation,
    run_treatment_stage,
    run_treatment_stage_from_attempts,
    select_tasks_official_first_n,
    synchronize_offline_treatment_artifacts,
    validate_chat_response,
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


_FAKE_DIGEST = "sha256:0edcdef34593abcdef0123456789abcdef0123456789abcdef0123456789ab"
_FAKE_MODEL_ENTRY = {
    "name": MODEL,
    "digest": _FAKE_DIGEST,
    "size": 2500000000,
    "modified_at": "2026-01-01T00:00:00Z",
}
_FAKE_VERSION_BODY = {"version": "0.31.2"}


def _chat_body(content: str, **extra) -> dict:
    body = {"message": {"content": content}}
    body.update(extra)
    return body


def _install_fake_urlopen(monkeypatch, tags_body=None, chat_bodies=None,
                          http_error=None, timeout_error=False,
                          version_body=None, version_http_error=None,
                          model_name=None):
    """chat_bodies: list of dicts consumed in call order for POST /api/chat."""
    model_name = model_name or MODEL
    tags_body = tags_body if tags_body is not None else {
        "models": [{**_FAKE_MODEL_ENTRY, "name": model_name}]
    }
    version_body = version_body if version_body is not None else dict(_FAKE_VERSION_BODY)
    chat_bodies = list(chat_bodies or [])
    calls = {"urls": [], "payloads": []}

    def fake_urlopen(req, timeout=None):
        url = req.full_url
        calls["urls"].append(url)
        if url.endswith("/api/tags"):
            if timeout_error and not chat_bodies:
                raise TimeoutError("timed out")
            if http_error and not chat_bodies:
                raise urllib.error.HTTPError(url, http_error, "err", {}, io.BytesIO(b""))
            return _FakeResponse(tags_body)
        if url.endswith("/api/version"):
            if version_http_error:
                raise urllib.error.HTTPError(url, version_http_error, "err", {}, io.BytesIO(b""))
            return _FakeResponse(version_body)
        if url.endswith("/api/chat"):
            if timeout_error:
                raise TimeoutError("timed out")
            if http_error:
                raise urllib.error.HTTPError(url, http_error, "err", {}, io.BytesIO(b""))
            calls["payloads"].append(json.loads(req.data.decode("utf-8")))
            body = chat_bodies.pop(0)
            return _FakeResponse(body)
        raise AssertionError(f"unexpected URL {url}")

    monkeypatch.setattr(runner.urllib.request, "urlopen", fake_urlopen)
    return calls


_FENCED_OK = _chat_body("```python\n    return True\n```")
_AMBIGUOUS = _chat_body("```python\nA\n```\n```python\nB\n```")
_DEFAULT_SETTINGS = OllamaGenerationSettings.for_model(MODEL)


def _run_generation(monkeypatch, tasks, chat_bodies):
    _install_fake_urlopen(monkeypatch, chat_bodies=chat_bodies)
    attempts, _resume = run_generation_attempts(
        tasks,
        benchmark="humaneval",
        base_url=runner.DEFAULT_BASE_URL,
        timeout_seconds=5.0,
        settings=_DEFAULT_SETTINGS,
        model_digest=_FAKE_DIGEST,
    )
    return attempts


def _run_attempt(monkeypatch, task, treatment, chat_bodies=None):
    _install_fake_urlopen(monkeypatch, chat_bodies=chat_bodies or [_FENCED_OK])
    return run_attempt(
        task,
        treatment,
        benchmark="humaneval",
        base_url=runner.DEFAULT_BASE_URL,
        timeout_seconds=5.0,
        settings=_DEFAULT_SETTINGS,
        model_digest=_FAKE_DIGEST,
    )


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


def test_chat_payload_has_fixed_params(monkeypatch):
    calls = _install_fake_urlopen(monkeypatch, chat_bodies=[_FENCED_OK])
    runner._post_chat("PROMPT", runner.DEFAULT_BASE_URL, 5.0, _DEFAULT_SETTINGS)
    payload = calls["payloads"][0]
    assert payload["model"] == MODEL
    assert payload["messages"] == [{"role": "user", "content": "PROMPT"}]
    assert payload["options"]["seed"] == SEED
    assert payload["options"]["temperature"] == TEMPERATURE
    assert payload["options"]["top_p"] == TOP_P
    assert payload["options"]["top_k"] == TOP_K
    assert payload["options"]["num_predict"] == NUM_PREDICT
    assert payload["stream"] is False
    assert "prompt" not in payload
    assert "think" not in payload


# ============================================================
# 1. first attempt fails, second still runs
# ============================================================


def test_first_attempt_fails_second_still_runs(monkeypatch):
    attempts = _run_generation(monkeypatch, [_TASK_0], [_AMBIGUOUS, _FENCED_OK])
    assert len(attempts) == 2
    assert attempts[0]["treatment"] == "ab1"
    assert attempts[0]["status"] == "failed"
    assert attempts[1]["treatment"] == "ab2g"
    assert attempts[1]["status"] == "success"


# ============================================================
# 2. Ab1 failure does not block same task's Ab2g
# ============================================================


def test_ab1_failure_does_not_block_ab2g(monkeypatch):
    attempts = _run_generation(monkeypatch, [_TASK_0], [_AMBIGUOUS, _FENCED_OK])
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
    attempt = _run_attempt(monkeypatch, _TASK_0, "ab1", chat_bodies=[_AMBIGUOUS])
    assert attempt["status"] == "failed"
    assert attempt["failure_stage"] == "extraction"
    assert attempt["extraction_status"] == "ambiguous"
    assert attempt["python_fenced_blocks"] == 2


# ============================================================
# 4. failed attempt still saves raw response
# ============================================================


def test_failed_extraction_attempt_saves_raw_response(monkeypatch):
    attempt = _run_attempt(monkeypatch, _TASK_0, "ab1", chat_bodies=[_AMBIGUOUS])
    raw_text = _AMBIGUOUS["message"]["content"]
    assert attempt["raw_response"] == raw_text
    assert attempt["raw_response_sha256"] == runner.sha256_text(raw_text)


def test_failed_validation_attempt_saves_raw_response(monkeypatch):
    body = _chat_body("<think>reasoning</think>\n    return True\n")
    attempt = _run_attempt(monkeypatch, _TASK_0, "ab1", chat_bodies=[body])
    assert attempt["status"] == "failed"
    assert attempt["failure_stage"] == "response_validation"
    assert attempt["raw_response"] == body["message"]["content"]
    assert attempt["reasoning_leakage_detected"] is True


def test_failed_request_attempt_has_null_raw_response(monkeypatch):
    _install_fake_urlopen(monkeypatch, http_error=500)
    attempt = run_attempt(
        _TASK_0, "ab1", benchmark="humaneval",
        base_url=runner.DEFAULT_BASE_URL, timeout_seconds=5.0,
        settings=_DEFAULT_SETTINGS, model_digest=_FAKE_DIGEST,
    )
    assert attempt["status"] == "failed"
    assert attempt["failure_stage"] == "ollama_request"
    assert attempt["raw_response"] is None
    assert attempt["raw_response_sha256"] is None


# ============================================================
# 5. failed attempt completion is null
# ============================================================


def test_failed_attempt_completion_is_null(monkeypatch):
    attempt = _run_attempt(monkeypatch, _TASK_0, "ab1", chat_bodies=[_AMBIGUOUS])
    assert attempt["completion"] is None
    assert attempt["completion_sha256"] is None


# ============================================================
# 6. success attempt writes to treatment JSONL
# ============================================================


def test_success_attempt_writes_treatment_jsonl(monkeypatch, tmp_path):
    tasks_path = _write_tasks(tmp_path, [_TASK_0])
    _install_fake_urlopen(monkeypatch, chat_bodies=[_FENCED_OK, _AMBIGUOUS])
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
    _install_fake_urlopen(monkeypatch, chat_bodies=[_AMBIGUOUS, _AMBIGUOUS])
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
    assert json.loads(raw_lines[0])["raw_response"] == _AMBIGUOUS["message"]["content"]


# ============================================================
# 8. summary counts correct
# ============================================================


def test_summary_counts_correct(monkeypatch):
    attempts = _run_generation(
        monkeypatch, [_TASK_0, _TASK_1],
        [_AMBIGUOUS, _FENCED_OK, _FENCED_OK, _FENCED_OK],
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
    attempts = _run_generation(
        monkeypatch, [_TASK_0, _TASK_1],
        [_FENCED_OK, _FENCED_OK, _FENCED_OK, _FENCED_OK],
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

    _install_fake_urlopen(monkeypatch, chat_bodies=_bodies())
    out1 = tmp_path / "out1"
    run_ollama_generation(
        tasks_path=tasks_path, benchmark="humaneval", output_dir=out1,
        base_url=runner.DEFAULT_BASE_URL, timeout_seconds=5.0,
    )

    _install_fake_urlopen(monkeypatch, chat_bodies=_bodies())
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
            r1.pop("generation_latency", None)
            r2.pop("generation_latency", None)
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
    raw = _chat_body("<think>reasoning</think>\n    return True\n")
    with pytest.raises(OllamaGenerationError, match="reasoning leakage"):
        validate_chat_response(raw)


def test_thinking_field_fails_closed():
    raw = {"message": {"content": "    return True\n", "thinking": "some reasoning"}}
    with pytest.raises(OllamaGenerationError, match="reasoning leakage"):
        validate_chat_response(raw)


def test_empty_response_field_fails_closed():
    with pytest.raises(OllamaGenerationError, match="empty or missing"):
        validate_chat_response({"message": {"content": "   "}})


def test_thinking_leakage_not_stripped_by_regex():
    raw = _chat_body("before <think>secret</think> after")
    assert detect_reasoning_leakage(raw, raw["message"]["content"]) is True
    with pytest.raises(OllamaGenerationError):
        validate_chat_response(raw)


# ============================================================
# Ab1/Ab2g share identical API/extraction/validation/schema
# ============================================================


def test_ab1_and_ab2g_use_same_extraction_and_schema(monkeypatch):
    ab1 = _run_attempt(monkeypatch, _TASK_0, "ab1")
    ab2g = _run_attempt(monkeypatch, _TASK_0, "ab2g")
    assert ab1["completion"] == ab2g["completion"]
    assert ab1["extraction_method"] == ab2g["extraction_method"]
    assert set(ab1.keys()) == set(ab2g.keys())
    for key in ("model", "seed", "temperature", "top_p", "top_k", "num_predict"):
        assert ab1["metadata"][key] == ab2g["metadata"][key]


# ============================================================
# API timeout / non-200 fail closed as a per-attempt failure
# ============================================================


def test_generate_timeout_is_attempt_failure(monkeypatch):
    _install_fake_urlopen(monkeypatch, timeout_error=True)
    attempt = run_attempt(
        _TASK_0, "ab1", benchmark="humaneval",
        base_url=runner.DEFAULT_BASE_URL, timeout_seconds=1.0,
        settings=_DEFAULT_SETTINGS, model_digest=_FAKE_DIGEST,
    )
    assert attempt["status"] == "failed"
    assert attempt["failure_stage"] == "ollama_request"


def test_generate_http_error_is_attempt_failure(monkeypatch):
    _install_fake_urlopen(monkeypatch, http_error=500)
    attempt = run_attempt(
        _TASK_0, "ab1", benchmark="humaneval",
        base_url=runner.DEFAULT_BASE_URL, timeout_seconds=5.0,
        settings=_DEFAULT_SETTINGS, model_digest=_FAKE_DIGEST,
    )
    assert attempt["status"] == "failed"
    assert attempt["failure_stage"] == "ollama_request"


# ============================================================
# model tags preflight (still a whole-run abort — nothing can succeed)
# ============================================================


def test_model_not_in_tags_fails_closed(monkeypatch):
    _install_fake_urlopen(monkeypatch, tags_body={"models": [{"name": "llama3:8b"}]})
    with pytest.raises(OllamaGenerationError, match="not found in /api/tags"):
        runner.check_model_available(runner.DEFAULT_BASE_URL, 5.0, model=MODEL)


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
    _install_fake_urlopen(monkeypatch, chat_bodies=[_FENCED_OK, _FENCED_OK])
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
    _install_fake_urlopen(monkeypatch, chat_bodies=[_AMBIGUOUS, _FENCED_OK])
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
        chat_bodies=urlopen_kwargs.pop("chat_bodies", [_FENCED_OK, _FENCED_OK]),
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
    assert manifest["top_p"] == TOP_P
    assert manifest["top_k"] == TOP_K
    assert manifest["num_predict"] == NUM_PREDICT
    assert manifest["timeout_seconds"] == 5.0


def test_missing_digest_fails_closed(monkeypatch, tmp_path):
    tags_body = {"models": [{"name": MODEL}]}  # no digest field
    _install_fake_urlopen(monkeypatch, tags_body=tags_body)
    with pytest.raises(OllamaGenerationError, match="no digest"):
        runner.fetch_ollama_provenance(runner.DEFAULT_BASE_URL, 5.0, model=MODEL)


def test_blank_digest_fails_closed(monkeypatch):
    tags_body = {"models": [{"name": MODEL, "digest": "   "}]}
    _install_fake_urlopen(monkeypatch, tags_body=tags_body)
    with pytest.raises(OllamaGenerationError, match="no digest"):
        runner.fetch_ollama_provenance(runner.DEFAULT_BASE_URL, 5.0, model=MODEL)


def test_version_endpoint_http_error_fails_closed(monkeypatch):
    _install_fake_urlopen(monkeypatch, version_http_error=500)
    with pytest.raises(OllamaGenerationError, match="status 500"):
        runner.fetch_ollama_provenance(runner.DEFAULT_BASE_URL, 5.0, model=MODEL)


def test_blank_version_fails_closed(monkeypatch):
    _install_fake_urlopen(monkeypatch, version_body={"version": "   "})
    with pytest.raises(OllamaGenerationError, match="no usable version"):
        runner.fetch_ollama_provenance(runner.DEFAULT_BASE_URL, 5.0, model=MODEL)


def test_model_missing_from_tags_provenance_fails_closed(monkeypatch):
    _install_fake_urlopen(monkeypatch, tags_body={"models": [{"name": "llama3:8b", "digest": "sha256:x"}]})
    with pytest.raises(OllamaGenerationError, match="not found in /api/tags"):
        runner.fetch_ollama_provenance(runner.DEFAULT_BASE_URL, 5.0, model=MODEL)


def test_digest_failure_blocks_full_run_before_any_attempt(monkeypatch, tmp_path):
    tasks_path = _write_tasks(tmp_path, [_TASK_0])
    calls = _install_fake_urlopen(monkeypatch, tags_body={"models": [{"name": MODEL}]})
    with pytest.raises(OllamaGenerationError, match="no digest"):
        run_ollama_generation(
            tasks_path=tasks_path, benchmark="humaneval", output_dir=tmp_path / "out",
            base_url=runner.DEFAULT_BASE_URL, timeout_seconds=5.0,
            runner_git_commit="deadbeef",
        )
    assert not any(u.endswith("/api/chat") for u in calls["urls"])
    assert not (tmp_path / "out" / "generation_manifest.json").exists()


def test_manifest_deterministic_fields_stable(monkeypatch, tmp_path):
    m1 = _run_full(monkeypatch, tmp_path)
    tmp2 = tmp_path / "second"
    tmp2.mkdir()
    m2 = _run_full(monkeypatch, tmp2)
    assert m1 == m2


# ============================================================
# Engineering smoke: 4B instruct model + isolated output
# ============================================================


def _smoke_digest():
    return f"sha256:{SMOKE_MODEL_DIGEST_PREFIX}0123456789abcdef0123456789abcdef0123456789ab"


def _make_n_tasks(n):
    return [
        PublicBenchmarkTask(
            benchmark="humaneval",
            task_id=f"HumanEval/{i}",
            prompt=f"def f{i}():\n    \"\"\"doc\"\"\"\n",
            entry_point=f"f{i}",
            canonical_solution=None,
        )
        for i in range(n)
    ]


def test_smoke_model_defaults():
    settings = OllamaGenerationSettings.smoke_default()
    assert settings.model == DEFAULT_SMOKE_MODEL
    assert settings.expected_digest_prefix == SMOKE_MODEL_DIGEST_PREFIX


def test_smoke_digest_mismatch_fails_closed(monkeypatch):
    tags = {"models": [{"name": DEFAULT_SMOKE_MODEL, "digest": "sha256:359d7dd4bcda"}]}
    _install_fake_urlopen(monkeypatch, tags_body=tags, model_name=DEFAULT_SMOKE_MODEL)
    with pytest.raises(OllamaGenerationError, match="does not match required prefix"):
        runner.fetch_ollama_provenance(
            runner.DEFAULT_BASE_URL, 5.0,
            model=DEFAULT_SMOKE_MODEL,
            expected_digest_prefix=SMOKE_MODEL_DIGEST_PREFIX,
        )


def test_select_first_twenty_tasks_deterministic():
    tasks = _make_n_tasks(25)
    selected = select_tasks_official_first_n(tasks, 20)
    assert [t.task_id for t in selected] == [f"HumanEval/{i}" for i in range(20)]


def test_select_insufficient_tasks_fail_closed():
    with pytest.raises(OllamaGenerationError, match="20 required"):
        select_tasks_official_first_n(_make_n_tasks(5), 20)


def test_smoke_output_dir_isolated(tmp_path):
    out = default_smoke_output_dir(tmp_path)
    assert "engineering_smoke_test" in str(out)
    assert "humaneval_plus" in str(out)
    assert "qwen3_4b_instruct_2507" in str(out)


def test_smoke_manifest_fields(monkeypatch, tmp_path):
    tasks = _make_n_tasks(20)
    tasks_path = _write_tasks(tmp_path, tasks)
    bodies = [_FENCED_OK, _FENCED_OK] * 20
    _install_fake_urlopen(
        monkeypatch,
        chat_bodies=bodies,
        model_name=DEFAULT_SMOKE_MODEL,
        tags_body={"models": [{
            "name": DEFAULT_SMOKE_MODEL,
            "digest": _smoke_digest(),
            "size": 2500000000,
        }]},
    )
    out_dir = tmp_path / "smoke_out"
    run_ollama_generation(
        tasks_path=tasks_path,
        benchmark="humaneval",
        output_dir=out_dir,
        base_url=runner.DEFAULT_BASE_URL,
        timeout_seconds=5.0,
        runner_git_commit="deadbeef",
        settings=OllamaGenerationSettings.smoke_default(),
        max_tasks=20,
        smoke=True,
    )
    manifest = json.loads((out_dir / "generation_manifest.json").read_text(encoding="utf-8"))
    assert manifest["run_type"] == RUN_TYPE_SMOKE
    assert manifest["analysis_status"] == ANALYSIS_STATUS_SMOKE_EXCLUDED
    assert manifest["benchmark"] == "humaneval_plus"
    assert manifest["task_selection_policy"] == TASK_SELECTION_POLICY_FIRST_N
    assert manifest["task_count"] == 20
    assert manifest["model_tag"] == DEFAULT_SMOKE_MODEL
    assert SMOKE_MODEL_DIGEST_PREFIX in manifest["model_digest"]
    assert manifest["api_endpoint"] == "/api/chat"
    assert manifest["response_field"] == "message.content"
    assert manifest["official_evalplus_status"] == "not_run_engineering_smoke"
    assert "pass_at_1" not in json.dumps(manifest)
    assert "official_evalplus_score" not in json.dumps(manifest)


def test_resume_skips_complete_attempt(monkeypatch, tmp_path):
    tasks_path = _write_tasks(tmp_path, [_TASK_0])
    out_dir = tmp_path / "out"
    _install_fake_urlopen(monkeypatch, chat_bodies=[_FENCED_OK, _FENCED_OK])
    run_ollama_generation(
        tasks_path=tasks_path, benchmark="humaneval", output_dir=out_dir,
        base_url=runner.DEFAULT_BASE_URL, timeout_seconds=5.0,
        runner_git_commit="deadbeef",
    )
    calls = _install_fake_urlopen(monkeypatch, chat_bodies=[])
    run_ollama_generation(
        tasks_path=tasks_path, benchmark="humaneval", output_dir=out_dir,
        base_url=runner.DEFAULT_BASE_URL, timeout_seconds=5.0,
        runner_git_commit="deadbeef",
        resume=True,
    )
    assert not any(u.endswith("/api/chat") for u in calls["urls"])


def test_resume_key_requires_model_digest_and_prompt(monkeypatch, tmp_path):
    tasks_path = _write_tasks(tmp_path, [_TASK_0])
    out_dir = tmp_path / "out"
    _install_fake_urlopen(monkeypatch, chat_bodies=[_FENCED_OK, _FENCED_OK])
    run_ollama_generation(
        tasks_path=tasks_path, benchmark="humaneval", output_dir=out_dir,
        base_url=runner.DEFAULT_BASE_URL, timeout_seconds=5.0,
        runner_git_commit="deadbeef",
    )
    completed = load_completed_attempts(out_dir / "generation_attempts.jsonl")
    assert len(completed) == 2
    for rec in completed.values():
        assert is_resume_complete(rec)
        meta = rec["metadata"]
        assert meta["model_digest"]
        assert meta["prompt_sha256"]


def test_entry_point_preflight_counts(tmp_path):
    code = "def has_close_elements(numbers, threshold):\n    return True\n"
    pre = entry_point_preflight(
        code,
        entry_point="has_close_elements",
        prompt=_TASK_0.prompt,
    )
    assert pre["parse_status"] == "success"
    assert pre["entry_point_definition_count"] == 1
    assert pre["entry_point_definition_category"] == "one"


def test_entry_point_preflight_duplicate_skeleton(tmp_path):
    code = (
        "def has_close_elements(numbers, threshold):\n    pass\n"
        "def has_close_elements(numbers, threshold):\n    return True\n"
    )
    pre = entry_point_preflight(
        code,
        entry_point="has_close_elements",
        prompt=_TASK_0.prompt,
    )
    assert pre["entry_point_definition_count"] == 2
    assert pre["entry_point_definition_category"] == "multiple"
    assert pre["duplicate_prompt_skeleton_suspected"] is True


def test_treatment_stage_from_attempts_delegates(monkeypatch, tmp_path):
    called = {}

    def _fake(**kwargs):
        called.update(kwargs)
        return {"total_tasks": 1}

    monkeypatch.setattr(runner, "run_public_benchmark_treatments_from_attempts", _fake)
    result = run_treatment_stage_from_attempts(
        tasks_path="tasks.jsonl",
        generation_attempts_path="attempts.jsonl",
        benchmark="humaneval",
        artifact_root=str(tmp_path),
        evaluator_git_commit="deadbeef",
    )
    assert result["ran"] is True
    assert called["generation_attempts_path"] == "attempts.jsonl"


def test_engineering_smoke_pipeline_writes_selected_tasks(monkeypatch, tmp_path):
    tasks = _make_n_tasks(20)
    tasks_path = _write_tasks(tmp_path, tasks)
    bodies = [_FENCED_OK, _FENCED_OK] * 20
    _install_fake_urlopen(
        monkeypatch,
        chat_bodies=bodies,
        model_name=DEFAULT_SMOKE_MODEL,
        tags_body={"models": [{
            "name": DEFAULT_SMOKE_MODEL,
            "digest": _smoke_digest(),
            "size": 2500000000,
        }]},
    )
    monkeypatch.setattr(
        runner,
        "run_public_benchmark_treatments_from_attempts",
        lambda **kwargs: type("S", (), {
            "total_tasks": 20, "ab3_target_count": 20,
            "core_changed_count": 0, "spec_changed_count": 0,
        })(),
    )
    out_dir = tmp_path / "smoke"
    result = run_engineering_smoke_pipeline(
        tasks_path=tasks_path,
        output_dir=out_dir,
        runner_git_commit="deadbeef",
        evaluator_git_commit="deadbeef",
        resume=False,
    )
    assert result["ab3_ran"] is True
    assert (out_dir / "tasks_selected.jsonl").exists()
    selected = (out_dir / "tasks_selected.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(selected) == 20


def _install_smoke_urlopen(monkeypatch, chat_bodies=None):
    return _install_fake_urlopen(
        monkeypatch,
        chat_bodies=chat_bodies,
        model_name=DEFAULT_SMOKE_MODEL,
        tags_body={"models": [{
            "name": DEFAULT_SMOKE_MODEL,
            "digest": _smoke_digest(),
            "size": 2500000000,
        }]},
    )


def _fake_ab3_summary(**kwargs):
    from agent_tools.finals_rebuild.public_benchmark_runner import (
        RawAb3RunSummary,
        load_generation_attempts,
    )

    tasks_path = pathlib.Path(kwargs["tasks_path"])
    tasks = load_benchmark_tasks(tasks_path, kwargs["benchmark"])
    attempts = load_generation_attempts(kwargs["generation_attempts_path"])
    by_key = {(a["task_id"], a["treatment"]): a for a in attempts}
    results = []
    for task in tasks:
        ab1 = by_key.get((task.task_id, "ab1"))
        ab2g = by_key.get((task.task_id, "ab2g"))
        results.append(
            {
                "task_id": task.task_id,
                "ab1_completion": ab1.get("completion") if ab1 and ab1.get("status") == "success" else None,
                "ab2g_completion": ab2g.get("completion") if ab2g and ab2g.get("status") == "success" else None,
                "ab3_core_completion": ab2g.get("completion") if ab2g and ab2g.get("status") == "success" else None,
                "ab3_full_completion": ab2g.get("completion") if ab2g and ab2g.get("status") == "success" else None,
            }
        )
    out_root = pathlib.Path(kwargs["artifact_root"]) / "public_benchmark_raw" / kwargs["benchmark"]
    evalplus_dir = out_root / "evalplus"
    evalplus_dir.mkdir(parents=True, exist_ok=True)
    for name, key in [
        ("ab1.jsonl", "ab1_completion"),
        ("ab2g.jsonl", "ab2g_completion"),
        ("ab3_core.jsonl", "ab3_core_completion"),
        ("ab3_full.jsonl", "ab3_full_completion"),
    ]:
        lines = [
            json.dumps({"task_id": r["task_id"], "completion": r[key]})
            for r in results
            if r.get(key)
        ]
        (evalplus_dir / name).write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return RawAb3RunSummary(
        benchmark=kwargs["benchmark"],
        total_tasks=len(tasks),
        ab3_target_count=len(tasks),
        core_changed_count=0,
        spec_changed_count=0,
        ab1_available_count=sum(1 for r in results if r["ab1_completion"]),
        ab1_missing_count=0,
        ab2g_raw_available_count=len(tasks),
        ab2g_raw_missing_count=0,
        ab2g_extraction_success_count=len(tasks),
        ab2g_extraction_failure_count=0,
        ab3_core_extraction_success_count=len(tasks),
        ab3_core_extraction_failure_count=0,
        ab3_full_extraction_success_count=len(tasks),
        ab3_full_extraction_failure_count=0,
        syntax_rescued_by_core=0,
        syntax_rescued_by_full=0,
        execution_rescued_by_core=0,
        execution_rescued_by_full=0,
        not_test_assessable_count=0,
    )


def test_smoke_sync_derivation_updates_evalplus_after_resume(monkeypatch, tmp_path):
    tasks_path = _write_tasks(tmp_path, [_TASK_0, _TASK_1])
    out_dir = tmp_path / "out"
    _install_smoke_urlopen(
        monkeypatch,
        chat_bodies=[_AMBIGUOUS, _FENCED_OK, _FENCED_OK, _FENCED_OK],
    )
    monkeypatch.setattr(
        runner, "run_public_benchmark_treatments_from_attempts", _fake_ab3_summary
    )
    run_ollama_generation(
        tasks_path=tasks_path,
        benchmark="humaneval",
        output_dir=out_dir,
        base_url=runner.DEFAULT_BASE_URL,
        timeout_seconds=5.0,
        runner_git_commit="deadbeef",
        smoke=True,
    )
    evalplus_ab1 = out_dir / "public_benchmark_raw/humaneval/evalplus/ab1.jsonl"
    assert len(evalplus_ab1.read_text(encoding="utf-8").splitlines()) == 1

    calls = _install_smoke_urlopen(monkeypatch, chat_bodies=[_FENCED_OK])
    run_ollama_generation(
        tasks_path=tasks_path,
        benchmark="humaneval",
        output_dir=out_dir,
        base_url=runner.DEFAULT_BASE_URL,
        timeout_seconds=5.0,
        runner_git_commit="deadbeef",
        smoke=True,
        resume=True,
    )
    assert sum(1 for u in calls["urls"] if u.endswith("/api/chat")) == 1
    assert len(evalplus_ab1.read_text(encoding="utf-8").splitlines()) == 2


def test_offline_sync_makes_no_api_calls(monkeypatch, tmp_path):
    tasks_path = _write_tasks(tmp_path, [_TASK_0])
    out_dir = tmp_path / "out"
    _install_smoke_urlopen(monkeypatch, chat_bodies=[_FENCED_OK, _FENCED_OK])
    monkeypatch.setattr(
        runner, "run_public_benchmark_treatments_from_attempts", _fake_ab3_summary
    )
    run_ollama_generation(
        tasks_path=tasks_path,
        benchmark="humaneval",
        output_dir=out_dir,
        base_url=runner.DEFAULT_BASE_URL,
        timeout_seconds=5.0,
        runner_git_commit="deadbeef",
        smoke=True,
    )
    attempts_before = (out_dir / "generation_attempts.jsonl").read_text(encoding="utf-8")

    def _forbid_attempt(*args, **kwargs):
        raise AssertionError("run_attempt must not be called during offline replay")

    monkeypatch.setattr(runner, "run_attempt", _forbid_attempt)
    calls = _install_fake_urlopen(monkeypatch, chat_bodies=[])
    run_offline_artifact_replay(
        output_dir=out_dir,
        tasks_path=tasks_path,
        benchmark="humaneval",
        runner_git_commit="deadbeef",
    )
    assert not any(u.endswith("/api/chat") for u in calls["urls"])
    assert (
        out_dir / "generation_attempts.jsonl"
    ).read_text(encoding="utf-8") == attempts_before


def test_offline_sync_rewrite_has_no_duplicate_lines(monkeypatch, tmp_path):
    tasks_path = _write_tasks(tmp_path, [_TASK_0])
    out_dir = tmp_path / "out"
    _install_smoke_urlopen(monkeypatch, chat_bodies=[_FENCED_OK, _FENCED_OK])
    monkeypatch.setattr(
        runner, "run_public_benchmark_treatments_from_attempts", _fake_ab3_summary
    )
    run_ollama_generation(
        tasks_path=tasks_path,
        benchmark="humaneval",
        output_dir=out_dir,
        base_url=runner.DEFAULT_BASE_URL,
        timeout_seconds=5.0,
        runner_git_commit="deadbeef",
        smoke=True,
    )
    evalplus_ab1 = out_dir / "public_benchmark_raw/humaneval/evalplus/ab1.jsonl"
    synchronize_offline_treatment_artifacts(
        output_dir=out_dir,
        tasks_path=tasks_path,
        benchmark="humaneval",
        evaluator_git_commit="deadbeef",
    )
    first = evalplus_ab1.read_text(encoding="utf-8")
    synchronize_offline_treatment_artifacts(
        output_dir=out_dir,
        tasks_path=tasks_path,
        benchmark="humaneval",
        evaluator_git_commit="deadbeef",
    )
    second = evalplus_ab1.read_text(encoding="utf-8")
    assert first == second
    assert len(second.strip().splitlines()) == 1


def test_ambiguous_retained_in_attempts_excluded_from_evalplus(monkeypatch, tmp_path):
    tasks_path = _write_tasks(tmp_path, [_TASK_0])
    out_dir = tmp_path / "out"
    _install_smoke_urlopen(monkeypatch, chat_bodies=[_AMBIGUOUS, _FENCED_OK])
    monkeypatch.setattr(
        runner, "run_public_benchmark_treatments_from_attempts", _fake_ab3_summary
    )
    run_ollama_generation(
        tasks_path=tasks_path,
        benchmark="humaneval",
        output_dir=out_dir,
        base_url=runner.DEFAULT_BASE_URL,
        timeout_seconds=5.0,
        runner_git_commit="deadbeef",
        smoke=True,
    )
    attempts = [
        json.loads(line)
        for line in (out_dir / "generation_attempts.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    ab1 = next(a for a in attempts if a["treatment"] == "ab1")
    assert ab1["extraction_status"] == "ambiguous"
    assert ab1["raw_response"]
    evalplus_ab1 = out_dir / "public_benchmark_raw/humaneval/evalplus/ab1.jsonl"
    assert evalplus_ab1.read_text(encoding="utf-8").strip() == ""


def test_fixture_tasks_marked_unverified_fixture(monkeypatch, tmp_path):
    tasks_path = _write_tasks(tmp_path, [_TASK_0])
    out_dir = tmp_path / "out"
    _install_smoke_urlopen(monkeypatch, chat_bodies=[_FENCED_OK, _FENCED_OK])
    monkeypatch.setattr(
        runner, "run_public_benchmark_treatments_from_attempts", _fake_ab3_summary
    )
    run_ollama_generation(
        tasks_path=tasks_path,
        benchmark="humaneval",
        output_dir=out_dir,
        base_url=runner.DEFAULT_BASE_URL,
        timeout_seconds=5.0,
        runner_git_commit="deadbeef",
        smoke=True,
    )
    manifest = json.loads((out_dir / "generation_manifest.json").read_text(encoding="utf-8"))
    assert manifest["dataset_provenance_status"] == "unverified_fixture"
    assert "tasks_sha256" not in manifest or manifest.get("tasks_sha256") is None


def _write_source_gzip(path, records):
    import gzip

    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _sample_records(n: int):
    return [
        {
            "task_id": f"HumanEval/{i}",
            "prompt": f"def f{i}():\n    \"\"\"doc {i}\"\"\"\n",
            "entry_point": f"f{i}",
            "canonical_solution": "    return 1\n",
            "test": "def check(candidate): pass",
        }
        for i in range(n)
    ]


def test_official_dataset_provenance_verified(monkeypatch, tmp_path):
    repo = tmp_path / "repo"
    data_dir = repo / "data/humaneval_plus"
    data_dir.mkdir(parents=True)
    src = data_dir / "source" / "HumanEvalPlus.jsonl.gz"
    _write_source_gzip(src, _sample_records(164))
    tasks_path = data_dir / "tasks.jsonl"
    manifest_path = data_dir / "dataset_manifest.json"
    manifest = prepare_tasks_file(
        source_path=src,
        tasks_path=tasks_path,
        manifest_path=manifest_path,
        creation_script="tests/fixture.py",
        expected_source_sha256=sha256_file(src),
    )

    out_dir = repo / "out"
    _install_smoke_urlopen(monkeypatch, chat_bodies=[_FENCED_OK, _FENCED_OK])
    monkeypatch.setattr(
        runner, "run_public_benchmark_treatments_from_attempts", _fake_ab3_summary
    )
    monkeypatch.setattr(runner, "resolve_repo_root", lambda start=None: repo)
    run_ollama_generation(
        tasks_path=tasks_path,
        benchmark="humaneval",
        output_dir=out_dir,
        base_url=runner.DEFAULT_BASE_URL,
        timeout_seconds=5.0,
        runner_git_commit="deadbeef",
        smoke=True,
        max_tasks=1,
        sync_treatment_artifacts=False,
        repo_root=repo,
        dataset_manifest_path=manifest_path,
    )
    run_manifest = json.loads((out_dir / "generation_manifest.json").read_text(encoding="utf-8"))
    assert run_manifest["dataset_provenance_status"] == "verified"
    assert run_manifest["tasks_sha256"] == manifest["tasks_sha256"]
    assert run_manifest["dataset_release_tag"] == manifest["release_tag_or_dataset_version"]


def test_tasks_sha_mismatch_fail_closed(monkeypatch, tmp_path):
    repo = tmp_path / "repo"
    data_dir = repo / "data/humaneval_plus"
    data_dir.mkdir(parents=True)
    tasks_jsonl = data_dir / "tasks.jsonl"
    tasks_jsonl.write_text(
        json.dumps(
            {
                "task_id": _TASK_0.task_id,
                "prompt": _TASK_0.prompt,
                "entry_point": _TASK_0.entry_point,
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    manifest_path = data_dir / "dataset_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "dataset_name": "HumanEval+",
                "release_tag_or_dataset_version": "v0.1.10",
                "task_count": 164,
                "source_asset_name": "HumanEvalPlus.jsonl.gz",
                "source_sha256": "0" * 64,
                "tasks_sha256": "f" * 64,
                "tasks_file": "data/humaneval_plus/tasks.jsonl",
                "task_order_policy": "official_source_order",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    out_dir = repo / "out"
    _install_smoke_urlopen(monkeypatch, chat_bodies=[_FENCED_OK, _FENCED_OK])
    monkeypatch.setattr(runner, "resolve_repo_root", lambda start=None: repo)
    with pytest.raises(OllamaGenerationError, match="SHA256 mismatch"):
        run_ollama_generation(
            tasks_path=tasks_jsonl,
            benchmark="humaneval",
            output_dir=out_dir,
            base_url=runner.DEFAULT_BASE_URL,
            timeout_seconds=5.0,
            runner_git_commit="deadbeef",
            smoke=True,
            repo_root=repo,
            dataset_manifest_path=manifest_path,
        )


def test_manifest_records_ab3_from_attempts_and_derivation_mode(monkeypatch, tmp_path):
    tasks_path = _write_tasks(tmp_path, [_TASK_0])
    out_dir = tmp_path / "out"
    _install_smoke_urlopen(monkeypatch, chat_bodies=[_FENCED_OK, _FENCED_OK])
    monkeypatch.setattr(
        runner, "run_public_benchmark_treatments_from_attempts", _fake_ab3_summary
    )
    run_ollama_generation(
        tasks_path=tasks_path,
        benchmark="humaneval",
        output_dir=out_dir,
        base_url=runner.DEFAULT_BASE_URL,
        timeout_seconds=5.0,
        runner_git_commit="deadbeef",
        smoke=True,
    )
    manifest = json.loads((out_dir / "generation_manifest.json").read_text(encoding="utf-8"))
    assert manifest["ab3_from_attempts"] is True
    assert manifest["treatment_derivation_mode"] == TREATMENT_DERIVATION_MODE


def test_engineering_smoke_allows_retry_incomplete(monkeypatch, tmp_path):
    tasks_path = _write_tasks(tmp_path, [_TASK_0])
    out_dir = tmp_path / "out"
    _install_smoke_urlopen(monkeypatch, chat_bodies=[_AMBIGUOUS, _FENCED_OK])
    run_ollama_generation(
        tasks_path=tasks_path,
        benchmark="humaneval",
        output_dir=out_dir,
        base_url=runner.DEFAULT_BASE_URL,
        timeout_seconds=5.0,
        runner_git_commit="deadbeef",
        smoke=True,
        sync_treatment_artifacts=False,
    )
    calls = _install_smoke_urlopen(monkeypatch, chat_bodies=[_FENCED_OK])
    run_ollama_generation(
        tasks_path=tasks_path,
        benchmark="humaneval",
        output_dir=out_dir,
        base_url=runner.DEFAULT_BASE_URL,
        timeout_seconds=5.0,
        runner_git_commit="deadbeef",
        smoke=True,
        resume=True,
        sync_treatment_artifacts=False,
    )
    assert any(u.endswith("/api/chat") for u in calls["urls"])
    manifest = json.loads((out_dir / "generation_manifest.json").read_text(encoding="utf-8"))
    assert manifest["attempt_policy"] == ATTEMPT_POLICY_ENGINEERING_SMOKE
    assert manifest["retry_incomplete_allowed"] is True


def test_confirmatory_resume_skips_failed_first_attempt(monkeypatch, tmp_path):
    tasks_path = _write_tasks(tmp_path, [_TASK_0])
    out_dir = tmp_path / "out"
    _install_fake_urlopen(monkeypatch, chat_bodies=[_AMBIGUOUS, _FENCED_OK])
    run_ollama_generation(
        tasks_path=tasks_path,
        benchmark="humaneval",
        output_dir=out_dir,
        base_url=runner.DEFAULT_BASE_URL,
        timeout_seconds=5.0,
        runner_git_commit="deadbeef",
        smoke=False,
        sync_treatment_artifacts=False,
    )
    before = (out_dir / "generation_attempts.jsonl").read_text(encoding="utf-8")
    calls = _install_fake_urlopen(monkeypatch, chat_bodies=[_FENCED_OK, _FENCED_OK])
    run_ollama_generation(
        tasks_path=tasks_path,
        benchmark="humaneval",
        output_dir=out_dir,
        base_url=runner.DEFAULT_BASE_URL,
        timeout_seconds=5.0,
        runner_git_commit="deadbeef",
        smoke=False,
        resume=True,
        sync_treatment_artifacts=False,
    )
    assert not any(u.endswith("/api/chat") for u in calls["urls"])
    after = (out_dir / "generation_attempts.jsonl").read_text(encoding="utf-8")
    assert before == after
    manifest = json.loads((out_dir / "generation_manifest.json").read_text(encoding="utf-8"))
    assert manifest["attempt_policy"] == ATTEMPT_POLICY_CONFIRMATORY
    assert manifest["first_attempt_is_itt"] is True
    assert manifest["retry_incomplete_allowed"] is False


def test_confirmatory_forbids_rerun_incomplete_flag():
    fields = attempt_policy_manifest_fields(ATTEMPT_POLICY_CONFIRMATORY)
    assert fields["retry_incomplete_allowed"] is False


def test_confirmatory_rerun_incomplete_flag_rejected(monkeypatch, tmp_path):
    tasks_path = _write_tasks(tmp_path, [_TASK_0])
    out_dir = tmp_path / "out"
    _install_fake_urlopen(monkeypatch, chat_bodies=[_FENCED_OK, _FENCED_OK])
    with pytest.raises(OllamaGenerationError, match="forbid --rerun-incomplete"):
        run_ollama_generation(
            tasks_path=tasks_path,
            benchmark="humaneval",
            output_dir=out_dir,
            base_url=runner.DEFAULT_BASE_URL,
            timeout_seconds=5.0,
            runner_git_commit="deadbeef",
            smoke=False,
            rerun_incomplete=True,
            sync_treatment_artifacts=False,
        )


def test_multi_fence_remains_ambiguous_without_heuristic():
    analysis = analyze_extraction(_AMBIGUOUS["message"]["content"])
    assert analysis["extraction_status"] == "ambiguous"
    assert analysis["completion"] is None
