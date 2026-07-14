"""Offline checks for the Ab2g-math-core prompt and qualification runner."""
from __future__ import annotations

import hashlib
import json
import multiprocessing
import os
import tempfile
import uuid
from pathlib import Path

import pytest
import core.ai_wrapper as ai_wrapper

from agent_tools.finals_rebuild.ab2d_local_prompt import (
    MATH_CORE_SCAFFOLD,
    TASK_LOCAL_PRIMITIVES,
    assemble_ab2d_local_prompt,
    assemble_ab2g_math_core_prompt,
)
from agent_tools.finals_rebuild.math_answer_contracts import render_answer_contract
from agent_tools.finals_rebuild.math_task_sampler import sample_task_parameters
from scripts import run_gemini_ab2g_math_core_qualification as runner


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tests/finals_rebuild/fixtures/math_generation_tasks_ce115_pilot.jsonl"
SNAPSHOTS = ROOT / "tests/fixtures/ab2g_math_core_prompt_snapshots.json"


def _spawn_import(queue: multiprocessing.queues.Queue) -> None:
    from scripts import run_gemini_ab2g_math_core_qualification as child_runner

    queue.put(child_runner.API_LOOP_ENTERED)


def _tasks() -> dict[str, dict]:
    rows = [json.loads(line) for line in MANIFEST.read_text(encoding="utf-8").splitlines() if line]
    return {row["skill_id"]: row for row in rows if row["skill_id"] in runner.FAMILIES and row["difficulty_level"] == 1}


def _parts(family: str) -> tuple[dict, dict, str]:
    task = _tasks()[family]
    payload = sample_task_parameters(task, runner.SEED)["oracle_payload"]
    return task, payload, render_answer_contract(task, payload)


def test_shared_core_and_snapshots_are_deterministic() -> None:
    snapshots = {row["task_family"]: row for row in json.loads(SNAPSHOTS.read_text(encoding="utf-8"))}
    assert set(snapshots) == set(runner.FAMILIES)
    for family in runner.FAMILIES:
        _, payload, contract = _parts(family)
        ab2g = assemble_ab2g_math_core_prompt(contract, payload)
        ab2d_local = assemble_ab2d_local_prompt(family, contract, payload)
        assert ab2g.startswith(MATH_CORE_SCAFFOLD)
        assert ab2d_local.startswith(MATH_CORE_SCAFFOLD)
        assert not any(primitive in ab2g for primitive in TASK_LOCAL_PRIMITIVES.values())
        assert TASK_LOCAL_PRIMITIVES[family] in ab2d_local
        assert hashlib.sha256(ab2g.encode("utf-8")).hexdigest() == snapshots[family]["sha256"]
        assert ab2g.encode("utf-8").decode("utf-8") == ab2g


def test_dry_run_never_calls_provider_or_writes_artifacts(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(runner, "_client_call", lambda *_: pytest.fail("provider must not be called"))
    rows = runner.dry_run_records()
    assert len(rows) == 4
    assert [row["task_family"] for row in rows] == list(runner.FAMILIES)
    assert all(row["model_tag"] == "gemini-3.5-flash" and row["prompt_condition"] == "Ab2g-math-core" for row in rows)
    assert all(row["request_count"] == 1 and row["retry_count"] == 0 and row["healer_used"] is False for row in rows)
    assert all(row["prompt_size"]["character_count"] > 0 for row in rows)


def test_cli_help_and_safe_default_never_enter_execution(capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(runner, "_run", lambda *_: pytest.fail("execution must require --execute-api"))
    assert runner.main([]) == 2
    assert "usage:" in capsys.readouterr().out
    with pytest.raises(SystemExit) as exit_info:
        runner.main(["--help"])
    assert exit_info.value.code == 0
    help_text = capsys.readouterr().out
    assert "--dry-run" in help_text
    assert "--execute-api" in help_text
    assert "--run-id" in help_text
    assert "--task-family" in help_text


def test_cli_dry_run_and_conflicting_flags_never_enter_execution(capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(runner, "_run", lambda *_: pytest.fail("dry run must not execute"))
    assert runner.main(["--dry-run"]) == 0
    rows = json.loads(capsys.readouterr().out)
    assert len(rows) == 4
    with pytest.raises(SystemExit) as exit_info:
        runner.main(["--dry-run", "--execute-api"])
    assert exit_info.value.code == 2


def test_execute_api_is_the_only_execution_path(monkeypatch: pytest.MonkeyPatch) -> None:
    called: list[tuple[Path, object]] = []
    summary: list[str] = []

    class SummarySink:
        def write_text(self, text: str, *, encoding: str) -> None:
            assert encoding == "utf-8"
            summary.append(text)

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    run_id = "20260714_rerun1"
    result_path, summary_path = runner._output_paths(run_id)
    monkeypatch.setattr(runner, "_output_paths", lambda value: (result_path, SummarySink()))
    monkeypatch.setattr(runner, "_run", lambda output, call, task_family=None: called.append((output, call, task_family)) or [])
    monkeypatch.setattr(runner, "API_LOOP_ENTERED", False)
    assert runner.main(["--execute-api", "--run-id", run_id]) == 0
    assert called == [(result_path, runner._client_call, None)]
    assert runner.API_LOOP_ENTERED is True
    assert summary


def test_safe_run_id_derives_distinct_artifact_pair() -> None:
    result, summary = runner._output_paths("20260714_rerun1")
    assert result == ROOT / "docs/experiments/results/gemini_ab2g_math_core_l1_seed_20260714_rerun1.jsonl"
    assert summary == ROOT / "docs/experiments/gemini_ab2g_math_core_l1_seed_20260714_rerun1_summary.md"
    assert runner._output_paths(None) == (runner.RESULT, runner.SUMMARY)


@pytest.mark.parametrize("run_id", ("../escape", "two/parts", "two\\parts", "contains.dot", ""))
def test_invalid_run_id_is_rejected(run_id: str) -> None:
    with pytest.raises(ValueError, match="run-id"):
        runner._output_paths(run_id)


def test_dry_run_with_run_id_does_not_create_artifacts(capsys: pytest.CaptureFixture[str]) -> None:
    run_id = f"pytest_dry_{uuid.uuid4().hex}"
    result, summary = runner._output_paths(run_id)
    assert not result.exists() and not summary.exists()
    assert runner.main(["--dry-run", "--run-id", run_id]) == 0
    assert len(json.loads(capsys.readouterr().out)) == 4
    assert not result.exists() and not summary.exists()


def test_task_family_filter_is_single_cell_and_unknown_fails_before_execution(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    family = "common_factor_quadratic_root_ordering"
    assert [row["task_family"] for row in runner.dry_run_records(family)] == [family]
    assert len(runner.dry_run_records()) == 4
    monkeypatch.setattr(runner, "_run", lambda *_: pytest.fail("unknown family must not execute"))
    with pytest.raises(SystemExit) as error:
        runner.main(["--dry-run", "--task-family", "unknown_family"])
    assert error.value.code == 2
    assert "invalid choice" in capsys.readouterr().err


def test_single_task_dry_run_and_mock_execute_write_one_row(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    family = "common_factor_quadratic_root_ordering"
    assert runner.main(["--dry-run", "--task-family", family]) == 0
    assert len(json.loads(capsys.readouterr().out)) == 1

    class FakeResponse:
        text = "def generate(level=1, **kwargs):\n    return {}\n"

    calls = 0
    def fake_call(_prompt: str, _preset: dict) -> FakeResponse:
        nonlocal calls
        calls += 1
        return FakeResponse()

    monkeypatch.setattr(runner, "_preset", lambda: {"model": runner.MODEL_TAG})
    with tempfile.TemporaryDirectory(dir=ROOT) as temp:
        output = Path(temp) / "single.jsonl"
        rows = runner._run(output, fake_call, family)
        assert "task_count: 1" in runner._summary(rows)
        persisted = output.read_text(encoding="utf-8").splitlines()
    assert calls == len(rows) == len(persisted) == 1


def test_existing_run_id_output_is_never_overwritten(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(runner, "_preset", lambda: {"model": runner.MODEL_TAG})
    with tempfile.TemporaryDirectory(dir=ROOT) as temp:
        output = Path(temp) / "existing.jsonl"
        output.write_text("existing\n", encoding="utf-8")
        with pytest.raises(FileExistsError, match="refusing to overwrite"):
            runner._run(output, lambda *_: pytest.fail("provider must not be called"))


def test_incremental_append_flushes_and_fsyncs(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []

    class Handle:
        def __enter__(self): return self
        def __exit__(self, *_): return False
        def write(self, value: str): events.append(f"write:{value}")
        def flush(self): events.append("flush")
        def fileno(self): return 17

    monkeypatch.setattr(Path, "open", lambda *_args, **_kwargs: Handle())
    monkeypatch.setattr(os, "fsync", lambda descriptor: events.append(f"fsync:{descriptor}"))
    runner._append(Path("unused.jsonl"), {"row": 1})
    assert events[1:] == ["flush", "fsync:17"]


def test_mock_provider_runs_all_four_cells_and_persists_each_row(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        text = "def generate(level=1, **kwargs):\n    return {}\n"

    calls = 0
    fsync_calls: list[int] = []

    def fake_call(_prompt: str, _preset: dict) -> FakeResponse:
        nonlocal calls
        calls += 1
        return FakeResponse()

    monkeypatch.setattr(runner, "_preset", lambda: {"model": runner.MODEL_TAG})
    monkeypatch.setattr(runner.os, "fsync", lambda descriptor: fsync_calls.append(descriptor))
    with tempfile.TemporaryDirectory(dir=ROOT) as temp:
        output = Path(temp) / "rows.jsonl"
        rows = runner._run(output, fake_call)
        persisted = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert calls == 4
    assert len(rows) == len(persisted) == 4
    assert len(fsync_calls) == 4
    assert all(row["request_count"] == 1 and row["retry_count"] == 0 and row["healer_used"] is False for row in persisted)


def test_mock_provider_failure_preserves_prior_incremental_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        text = "def generate(level=1, **kwargs):\n    return {}\n"

    calls = 0

    def fake_call(_prompt: str, _preset: dict) -> FakeResponse:
        nonlocal calls
        calls += 1
        if calls == 3:
            raise RuntimeError("provider failure")
        return FakeResponse()

    monkeypatch.setattr(runner, "_preset", lambda: {"model": runner.MODEL_TAG})
    with tempfile.TemporaryDirectory(dir=ROOT) as temp:
        output = Path(temp) / "rows.jsonl"
        rows = runner._run(output, fake_call)
        persisted = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert calls == 4
    assert len(rows) == len(persisted) == 4
    assert persisted[2]["failure_category"] == "provider_error"
    assert all(row["task_family"] == runner.FAMILIES[index] for index, row in enumerate(persisted))


def test_provider_failure_taxonomy_and_secret_redaction(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        text = "def generate(level=1, **kwargs):\n    return {}\n"

    calls = 0

    def fake_call(_prompt: str, _preset: dict) -> FakeResponse:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise TimeoutError("not used in persisted detail")
        if calls == 2:
            raise RuntimeError("model not found; GEMINI_API_KEY=secret-value; AIzaSecretToken")
        return FakeResponse()

    monkeypatch.setattr(runner, "_preset", lambda: {"model": runner.MODEL_TAG})
    with tempfile.TemporaryDirectory(dir=ROOT) as temp:
        rows = runner._run(Path(temp) / "rows.jsonl", fake_call)
    assert rows[0]["failure_category"] == "provider_timeout"
    assert rows[0]["failure_detail"] == "TimeoutError: provider request exceeded 120 seconds"
    assert rows[1]["failure_category"] == "provider_error"
    assert "model not found" in rows[1]["failure_detail"]
    assert "secret-value" not in rows[1]["failure_detail"]
    assert "AIzaSecretToken" not in rows[1]["failure_detail"]


def test_client_call_preserves_model_and_passes_timeout_without_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class FakeClient:
        def __init__(self, model, temperature, **kwargs):
            captured.update(model=model, temperature=temperature, **kwargs)

    def fake_helper(client, prompt, **kwargs):
        captured.update(client=client, prompt=prompt, **kwargs)
        return "response"

    monkeypatch.setattr(ai_wrapper, "GoogleAIClient", FakeClient)
    monkeypatch.setattr(ai_wrapper, "call_ai_with_retry", fake_helper)
    result = runner._client_call("prompt", {"model": "gemini-3.5-flash", "temperature": 0.0, "max_tokens": 4096})
    assert result == "response"
    assert captured["model"] == "gemini-3.5-flash"
    assert captured["timeout"] == 120
    assert captured["max_retries"] == 0  # one first attempt, zero retry attempts


def test_retry_helper_zero_retries_makes_one_provider_call() -> None:
    class Client:
        def __init__(self): self.calls = 0
        def generate_content(self, _prompt, image_path=None):
            self.calls += 1
            return "ok"

    client = Client()
    assert ai_wrapper.call_ai_with_retry(client, "prompt", max_retries=0, timeout=1) == "ok"
    assert client.calls == 1


def test_retry_helper_one_retry_stops_after_first_success() -> None:
    class Client:
        def __init__(self): self.calls = 0
        def generate_content(self, _prompt, image_path=None):
            self.calls += 1
            return "ok"

    client = Client()
    assert ai_wrapper.call_ai_with_retry(client, "prompt", max_retries=1, retry_delay=0, timeout=1) == "ok"
    assert client.calls == 1


def test_retry_helper_one_retry_makes_second_attempt_after_failure() -> None:
    class Client:
        def __init__(self): self.calls = 0
        def generate_content(self, _prompt, image_path=None):
            self.calls += 1
            if self.calls == 1:
                raise ValueError("first")
            return "ok"

    client = Client()
    assert ai_wrapper.call_ai_with_retry(client, "prompt", max_retries=1, retry_delay=0, timeout=1) == "ok"
    assert client.calls == 2


def test_retry_helper_preserves_last_exception_after_all_attempts() -> None:
    second = RuntimeError("second failure")

    class Client:
        def __init__(self): self.calls = 0
        def generate_content(self, _prompt, image_path=None):
            self.calls += 1
            if self.calls == 1:
                raise ValueError("first failure")
            raise second

    client = Client()
    with pytest.raises(RuntimeError) as error:
        ai_wrapper.call_ai_with_retry(client, "prompt", max_retries=1, retry_delay=0, timeout=1)
    assert error.value is second
    assert client.calls == 2


def test_fixed_runner_settings_and_qualification_gate() -> None:
    assert (runner.REQUEST_TIMEOUT_SECONDS, runner.EXECUTION_TIMEOUT_SECONDS, runner.MAX_OUTPUT_TOKENS) == (120, 3.0, 4096)
    rows = runner.dry_run_records()
    assert runner.cloud_qualified(rows) is False
    passed = [{**row, "evaluable": True, "oracle_pass": True, "execution_timeout": False} for row in rows]
    assert runner.cloud_qualified(passed) is True
    assert runner.cloud_qualified(passed[:3]) is False


def test_unknown_contract_fails_closed() -> None:
    with pytest.raises(ValueError, match="task_contract"):
        assemble_ab2g_math_core_prompt("", {})


def test_windows_spawn_import_does_not_enter_api_loop() -> None:
    context = multiprocessing.get_context("spawn")
    queue = context.Queue()
    child = context.Process(target=_spawn_import, args=(queue,))
    child.start()
    assert queue.get(timeout=10) is False
    child.join(timeout=10)
    assert child.exitcode == 0
