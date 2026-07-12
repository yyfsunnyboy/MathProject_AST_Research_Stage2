"""
Tests for agent_tools/finals_rebuild/ollama_generation_runner.py

All Ollama HTTP calls are mocked at the urllib.request.urlopen boundary —
this suite never calls a real model.
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
from agent_tools.finals_rebuild.benchmarks_adapter import PublicBenchmarkTask
from agent_tools.finals_rebuild.ollama_generation_runner import (
    AB2G_SCAFFOLD,
    MODEL,
    OllamaGenerationError,
    SEED,
    TEMPERATURE,
    THINK,
    build_arg_parser,
    build_prompt,
    extract_completion,
    generate_treatment,
    main,
    run_ollama_generation,
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


def _install_fake_urlopen(monkeypatch, tags_body=None, generate_bodies=None, http_error=None, timeout_error=False):
    """generate_bodies: list of dicts, consumed in call order for POST /api/generate."""
    tags_body = tags_body if tags_body is not None else {"models": [{"name": MODEL}]}
    generate_bodies = list(generate_bodies or [])
    calls = {"urls": [], "payloads": []}

    def fake_urlopen(req, timeout=None):
        url = req.full_url
        calls["urls"].append(url)
        if timeout_error:
            raise TimeoutError("timed out")
        if http_error:
            raise urllib.error.HTTPError(url, http_error, "err", {}, io.BytesIO(b""))
        if url.endswith("/api/tags"):
            return _FakeResponse(tags_body)
        if url.endswith("/api/generate"):
            calls["payloads"].append(json.loads(req.data.decode("utf-8")))
            body = generate_bodies.pop(0)
            return _FakeResponse(body)
        raise AssertionError(f"unexpected URL {url}")

    monkeypatch.setattr(runner.urllib.request, "urlopen", fake_urlopen)
    return calls


# ============================================================
# 1. payload contains think=false, fixed model/seed/temperature
# ============================================================


def test_generate_payload_has_think_false_and_fixed_params(monkeypatch):
    calls = _install_fake_urlopen(
        monkeypatch, generate_bodies=[{"response": "    return True\n"}]
    )
    runner._post_generate("PROMPT", runner.DEFAULT_BASE_URL, 5.0)
    payload = calls["payloads"][0]
    assert payload["think"] is False
    assert payload["model"] == MODEL
    assert payload["options"]["seed"] == SEED
    assert payload["options"]["temperature"] == TEMPERATURE
    assert payload["stream"] is False


# ============================================================
# 3 & 4. Ab1 has no scaffold, Ab2g has fixed scaffold
# ============================================================


def test_ab1_prompt_has_no_scaffold():
    prompt = build_prompt(_TASK_0.prompt, "ab1")
    assert prompt == _TASK_0.prompt
    assert AB2G_SCAFFOLD not in prompt


def test_ab2g_prompt_has_fixed_scaffold():
    prompt = build_prompt(_TASK_0.prompt, "ab2g")
    assert prompt == _TASK_0.prompt + AB2G_SCAFFOLD


# ============================================================
# 5. duplicate function signature fails closed
# ============================================================


def test_duplicate_signature_fails_closed():
    raw = {"response": "def has_close_elements(numbers, threshold):\n    return True\n"}
    with pytest.raises(OllamaGenerationError, match="repeats the function signature"):
        extract_completion(raw, "has_close_elements")


def test_no_duplicate_signature_passes():
    raw = {"response": "    return True\n"}
    assert extract_completion(raw, "has_close_elements") == "    return True\n"


# ============================================================
# 6. empty response fails closed
# ============================================================


def test_empty_response_fails_closed():
    with pytest.raises(OllamaGenerationError, match="empty or missing"):
        extract_completion({"response": "   "}, "has_close_elements")


def test_missing_response_field_fails_closed():
    with pytest.raises(OllamaGenerationError, match="empty or missing"):
        extract_completion({}, "has_close_elements")


# ============================================================
# 7. API timeout fails closed
# ============================================================


def test_generate_timeout_fails_closed(monkeypatch):
    _install_fake_urlopen(monkeypatch, timeout_error=True)
    with pytest.raises(OllamaGenerationError, match="timed out"):
        runner._post_generate("PROMPT", runner.DEFAULT_BASE_URL, 1.0)


def test_tags_timeout_fails_closed(monkeypatch):
    _install_fake_urlopen(monkeypatch, timeout_error=True)
    with pytest.raises(OllamaGenerationError, match="timed out"):
        runner.check_model_available(runner.DEFAULT_BASE_URL, 1.0)


# ============================================================
# 8. API non-200 fails closed
# ============================================================


def test_generate_http_error_fails_closed(monkeypatch):
    _install_fake_urlopen(monkeypatch, http_error=500)
    with pytest.raises(OllamaGenerationError, match="status 500"):
        runner._post_generate("PROMPT", runner.DEFAULT_BASE_URL, 5.0)


def test_tags_http_error_fails_closed(monkeypatch):
    _install_fake_urlopen(monkeypatch, http_error=500)
    with pytest.raises(OllamaGenerationError, match="status 500"):
        runner.check_model_available(runner.DEFAULT_BASE_URL, 5.0)


# ============================================================
# 9. <think> leak fails closed
# ============================================================


def test_think_tag_in_response_fails_closed():
    raw = {"response": "<think>reasoning</think>\n    return True\n"}
    with pytest.raises(OllamaGenerationError, match="think"):
        extract_completion(raw, "has_close_elements")


def test_thinking_field_fails_closed():
    raw = {"response": "    return True\n", "thinking": "some reasoning"}
    with pytest.raises(OllamaGenerationError, match="thinking"):
        extract_completion(raw, "has_close_elements")


# ============================================================
# 10. Markdown fence fails closed
# ============================================================


def test_markdown_fence_fails_closed():
    raw = {"response": "```python\n    return True\n```"}
    with pytest.raises(OllamaGenerationError, match="fence"):
        extract_completion(raw, "has_close_elements")


# ============================================================
# 11. task identity correct across a full generation run
# ============================================================


def test_task_identity_correct(monkeypatch, tmp_path):
    tasks_path = _write_tasks(tmp_path, [_TASK_0, _TASK_1])
    _install_fake_urlopen(
        monkeypatch,
        generate_bodies=[
            {"response": "    return True\n"},
            {"response": "    return []\n"},
        ],
    )
    records = generate_treatment(
        [_TASK_0, _TASK_1], "ab1",
        benchmark="humaneval", base_url=runner.DEFAULT_BASE_URL, timeout_seconds=5.0,
    )
    assert [r["task_id"] for r in records] == ["HumanEval/0", "HumanEval/1"]
    assert all(r["sample_index"] == 0 for r in records)


# ============================================================
# 12. manifest deterministic across reruns
# ============================================================


def test_manifest_deterministic_across_reruns(monkeypatch, tmp_path):
    tasks_path = _write_tasks(tmp_path, [_TASK_0])

    def _bodies():
        return [{"response": "    return True\n"}, {"response": "    return True\n"}]

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

    m1 = json.loads((out1 / "generation_manifest.json").read_text(encoding="utf-8"))
    m2 = json.loads((out2 / "generation_manifest.json").read_text(encoding="utf-8"))
    assert m1 == m2
    assert m1["status"] == "success"
    assert m1["model"] == MODEL
    assert m1["seed"] == SEED
    assert m1["think"] is THINK


# ============================================================
# Additional: model not found in /api/tags fails closed
# ============================================================


def test_model_not_in_tags_fails_closed(monkeypatch):
    _install_fake_urlopen(monkeypatch, tags_body={"models": [{"name": "llama3:8b"}]})
    with pytest.raises(OllamaGenerationError, match="not found in /api/tags"):
        runner.check_model_available(runner.DEFAULT_BASE_URL, 5.0)


def test_model_found_in_tags_passes(monkeypatch):
    _install_fake_urlopen(monkeypatch, tags_body={"models": [{"name": MODEL}]})
    runner.check_model_available(runner.DEFAULT_BASE_URL, 5.0)  # no raise


# ============================================================
# Additional: full run writes ab1.jsonl / ab2g.jsonl with correct schema
# ============================================================


def test_full_run_writes_expected_files_and_schema(monkeypatch, tmp_path):
    tasks_path = _write_tasks(tmp_path, [_TASK_0])
    _install_fake_urlopen(
        monkeypatch,
        generate_bodies=[
            {"response": "    return True\n"},  # ab1
            {"response": "    return True\n"},  # ab2g
        ],
    )
    out_dir = tmp_path / "out"
    manifest = run_ollama_generation(
        tasks_path=tasks_path, benchmark="humaneval", output_dir=out_dir,
        base_url=runner.DEFAULT_BASE_URL, timeout_seconds=5.0,
    )
    assert manifest["counts"] == {"ab1": 1, "ab2g": 1}

    for name in ("ab1.jsonl", "ab2g.jsonl", "generation_manifest.json"):
        assert (out_dir / name).exists()

    ab1_rec = json.loads((out_dir / "ab1.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert ab1_rec["task_id"] == "HumanEval/0"
    assert ab1_rec["sample_index"] == 0
    assert ab1_rec["completion"] == "    return True\n"
    meta = ab1_rec["metadata"]
    for key in ("benchmark", "treatment", "model", "seed", "temperature", "think",
                "prompt_sha256", "raw_response_sha256"):
        assert key in meta
    assert meta["model"] == MODEL
    assert meta["seed"] == SEED
    assert meta["treatment"] == "ab1"


# ============================================================
# Additional: model not available preflight blocks the whole run
# ============================================================


def test_model_unavailable_blocks_full_run(monkeypatch, tmp_path):
    tasks_path = _write_tasks(tmp_path, [_TASK_0])
    _install_fake_urlopen(monkeypatch, tags_body={"models": [{"name": "llama3:8b"}]})
    with pytest.raises(OllamaGenerationError, match="not found in /api/tags"):
        run_ollama_generation(
            tasks_path=tasks_path, benchmark="humaneval", output_dir=tmp_path / "out",
            base_url=runner.DEFAULT_BASE_URL, timeout_seconds=5.0,
        )
    assert not (tmp_path / "out" / "generation_manifest.json").exists()


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


def test_main_returns_nonzero_on_failure(monkeypatch, tmp_path):
    tasks_path = _write_tasks(tmp_path, [_TASK_0])
    _install_fake_urlopen(monkeypatch, tags_body={"models": []})
    exit_code = main([
        "--tasks-path", str(tasks_path), "--benchmark", "humaneval",
        "--output-dir", str(tmp_path / "out"),
    ])
    assert exit_code == 1
