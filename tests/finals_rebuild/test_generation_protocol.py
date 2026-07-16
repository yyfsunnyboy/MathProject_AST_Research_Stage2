from __future__ import annotations

import io
import json
import pathlib
import urllib.error

import pytest

import agent_tools.finals_rebuild.ollama_generation_runner as runner
from agent_tools.finals_rebuild.benchmarks_adapter import PublicBenchmarkTask
from scripts.verify_generation_protocol import SYNTHETIC_PROMPT

ROOT = pathlib.Path(__file__).resolve().parents[2]
PROTOCOL_PATH = ROOT / "configs/public_benchmark_generation_protocol_v1.json"
PROBE_PATH = ROOT / "artifacts/public_benchmark_governance/synthetic_probe_manifest.json"


class _Response:
    def __init__(self, body: dict, status: int = 200) -> None:
        self._body = json.dumps(body).encode("utf-8")
        self._status = status

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def getcode(self) -> int:
        return self._status

    def read(self) -> bytes:
        return self._body


def _response_body(model: str = "qwen3.5:9b") -> dict:
    return {
        "model": model,
        "created_at": "2026-07-16T00:00:00Z",
        "message": {"role": "assistant", "content": "PROTOCOL_OK"},
        "done": True,
        "done_reason": "stop",
        "total_duration": 1,
        "load_duration": 1,
        "prompt_eval_count": 1,
        "prompt_eval_duration": 1,
        "eval_count": 1,
        "eval_duration": 1,
    }


def test_protocol_reloads_identically_and_freezes_models():
    first = runner.load_generation_protocol(PROTOCOL_PATH)
    second = runner.load_generation_protocol(PROTOCOL_PATH)
    assert first == second
    assert first["models"]["primary_development_model"]["tag"] == "qwen3.5:9b"
    assert first["models"]["primary_development_model"]["public_benchmark_execution_allowed"] is True
    transfer = first["models"]["frozen_transfer_model"]
    assert transfer["tag"] == "qwen3.5:4b"
    assert transfer["role"] == "transfer_only"
    assert transfer["public_benchmark_execution_allowed"] is False
    assert all(len(model["digest"]) == 64 for model in first["models"].values())


def test_protocol_parameters_and_policies_are_exact():
    protocol = runner.load_generation_protocol(PROTOCOL_PATH)
    assert protocol["generation"] == {
        "thinking": False,
        "temperature": 0.2,
        "top_p": 0.95,
        "top_k": 20,
        "num_ctx": 8192,
        "num_predict": 2048,
        "stream": False,
    }
    assert protocol["samples_per_task"] == 5
    assert protocol["seeds"] == [11, 22, 33, 44, 55]
    assert len(set(protocol["seeds"])) == 5
    assert protocol["policies"]["automatic_retry"] is False
    assert protocol["policies"]["evaluator_feedback_to_model"] is False
    assert protocol["policies"]["llm_post_rewrite"] is False
    assert protocol["policies"]["preserve_raw_response"] is True


def test_protocol_settings_reach_http_payload_and_request_is_saved(monkeypatch):
    captured = []

    def fake_urlopen(request, timeout):
        captured.append(json.loads(request.data.decode("utf-8")))
        return _Response(_response_body())

    monkeypatch.setattr(runner.urllib.request, "urlopen", fake_urlopen)
    protocol = runner.load_generation_protocol(PROTOCOL_PATH)
    settings = runner.protocol_settings(
        protocol, model_role="primary_development_model", seed=11
    )
    response = runner._post_chat(SYNTHETIC_PROMPT, runner.DEFAULT_BASE_URL, 5.0, settings)
    payload = captured[0]
    assert payload["model"] == "qwen3.5:9b"
    assert payload["think"] is False
    assert payload["stream"] is False
    assert payload["options"] == {
        "temperature": 0.2,
        "seed": 11,
        "top_p": 0.95,
        "top_k": 20,
        "num_predict": 2048,
        "num_ctx": 8192,
    }
    metadata = response["_ollama_response_metadata"]
    assert metadata["request_payload"] == payload
    assert metadata["raw_body"]


def test_generation_pairs_arms_across_all_five_seeds(monkeypatch):
    protocol = runner.load_generation_protocol(PROTOCOL_PATH)
    settings = [
        runner.protocol_settings(protocol, model_role="primary_development_model", seed=seed)
        for seed in protocol["seeds"]
    ]
    observed = []

    def fake_attempt(task, treatment, **kwargs):
        observed.append((task.task_id, treatment, kwargs["sample_index"], kwargs["settings"].seed))
        return {"task_id": task.task_id, "treatment": treatment, "status": "success"}

    monkeypatch.setattr(runner, "run_attempt", fake_attempt)
    task = PublicBenchmarkTask("humaneval", "synthetic/0", "def synthetic():\n", "synthetic", None)
    attempts, _ = runner.run_generation_attempts(
        [task],
        benchmark="humaneval",
        base_url=runner.DEFAULT_BASE_URL,
        timeout_seconds=5.0,
        settings=settings[0],
        sample_settings=settings,
        model_digest=protocol["models"]["primary_development_model"]["digest"],
    )
    assert len(attempts) == 10
    for sample_index, seed in enumerate(protocol["seeds"]):
        assert ("synthetic/0", "ab1", sample_index, seed) in observed
        assert ("synthetic/0", "ab2g", sample_index, seed) in observed


def test_http_failure_is_not_retried(monkeypatch):
    calls = 0

    def fail_once(request, timeout):
        nonlocal calls
        calls += 1
        raise urllib.error.HTTPError(request.full_url, 500, "failed", {}, io.BytesIO())

    monkeypatch.setattr(runner.urllib.request, "urlopen", fail_once)
    protocol = runner.load_generation_protocol(PROTOCOL_PATH)
    settings = runner.protocol_settings(
        protocol, model_role="primary_development_model", seed=11
    )
    with pytest.raises(runner.OllamaGenerationError):
        runner._post_chat(SYNTHETIC_PROMPT, runner.DEFAULT_BASE_URL, 5.0, settings)
    assert calls == 1


def test_protocol_run_refuses_existing_output(tmp_path):
    output = tmp_path / "existing"
    output.mkdir()
    (output / "keep.txt").write_text("do not overwrite", encoding="utf-8")
    with pytest.raises(runner.OllamaGenerationError, match="refuses to overwrite"):
        runner.run_ollama_generation(
            tasks_path=tmp_path / "not-read.jsonl",
            benchmark="humaneval",
            output_dir=output,
            generation_protocol_path=PROTOCOL_PATH,
        )
    assert (output / "keep.txt").read_text(encoding="utf-8") == "do not overwrite"


def test_saved_probes_prove_no_thinking_without_benchmark_tasks():
    manifest = json.loads(PROBE_PATH.read_text(encoding="utf-8"))
    assert manifest["probe_count"] == 2
    assert manifest["public_benchmark_task_content_used"] is False
    assert "humaneval" not in manifest["synthetic_prompt"].lower()
    assert "mbpp" not in manifest["synthetic_prompt"].lower()
    assert [probe["model_tag"] for probe in manifest["probes"]] == [
        "qwen3.5:9b",
        "qwen3.5:4b",
    ]
    for probe in manifest["probes"]:
        assert probe["request"]["think"] is False
        assert probe["no_thinking_verified"] is True
        assert probe["response_contains_think_tag"] is False
        assert probe["metadata_complete"] is True
        assert probe["raw_response_body"]
        assert probe["response"]["message"].get("thinking") in (None, "")
