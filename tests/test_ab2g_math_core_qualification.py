"""Offline checks for the Ab2g-math-core prompt and qualification runner."""
from __future__ import annotations

import hashlib
import json
import multiprocessing
import os
from pathlib import Path

import pytest

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
    monkeypatch.setattr(runner, "SUMMARY", SummarySink())
    monkeypatch.setattr(runner, "_run", lambda output, call: called.append((output, call)) or [])
    monkeypatch.setattr(runner, "API_LOOP_ENTERED", False)
    assert runner.main(["--execute-api"]) == 0
    assert called == [(runner.RESULT, runner._client_call)]
    assert runner.API_LOOP_ENTERED is True
    assert summary


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
