"""Offline checks for the Gemini Ab2d-local qualification runner."""
from __future__ import annotations

import json
import os
import tempfile
import uuid
from pathlib import Path

import pytest

from agent_tools.finals_rebuild.ab2d_local_prompt import TASK_LOCAL_PRIMITIVES, assemble_ab2g_math_core_prompt
from agent_tools.finals_rebuild.math_boundary_pilot import classify_response
from agent_tools.finals_rebuild.math_task_oracles import evaluate_math_task_oracle
from scripts import run_gemini_ab2d_local_qualification as runner


ROOT = Path(__file__).resolve().parents[1]


def test_local_prompts_have_only_the_required_additional_primitive() -> None:
    rows = runner.dry_run_records()
    assert [row["task_family"] for row in rows] == list(runner.FAMILIES)
    for row in rows:
        family = row["task_family"]
        ab2g = assemble_ab2g_math_core_prompt(row["answer_contract"], row["task_parameters"])
        primitive_section = f"## Task-local domain primitive: {family}\n{TASK_LOCAL_PRIMITIVES[family]}\n\n"
        expected = ab2g.replace("## Task contract\n", primitive_section + "## Task contract\n", 1)
        assert row["final_prompt"] == expected
        assert row["prompt_condition"] == "Ab2d-local"
        assert "oracle_expected" not in row["final_prompt"]


def test_ce115_q09_common_factor_reconstruction_is_exact_and_not_run() -> None:
    row = next(row for row in runner.dry_run_records() if row["task_family"] == "common_factor_quadratic_root_ordering")
    payload = row["task_parameters"]
    assert payload == {
        "shared_shift": 7,
        "leading_factor": 2,
        "subtracted_factor": 10,
        "root_order": "a>b",
        "linear_combination": {"a": 1, "b": 2},
    }
    verdict = evaluate_math_task_oracle("common_factor_quadratic_root_ordering", payload, {"value": -9})
    assert verdict["is_correct"] is True and verdict["expected_answer"] == {"value": -9}
    assert evaluate_math_task_oracle("common_factor_quadratic_root_ordering", payload, {"value": 3})["is_correct"] is False
    assert "alternating_training_progression_threshold" not in runner.FAMILIES


def test_common_factor_prompt_treatment_has_no_answer_leakage() -> None:
    row = next(row for row in runner.dry_run_records() if row["task_family"] == "common_factor_quadratic_root_ordering")
    primitive = TASK_LOCAL_PRIMITIVES["common_factor_quadratic_root_ordering"]
    assert primitive in row["final_prompt"]
    assert all(token not in primitive for token in ("5", "-7", "-9"))
    ab2g = assemble_ab2g_math_core_prompt(row["answer_contract"], row["task_parameters"])
    assert primitive not in ab2g
    assert "oracle_expected" not in row["final_prompt"]


def test_dry_run_never_calls_provider_or_creates_artifacts(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(runner, "_client_call", lambda *_: pytest.fail("provider must not be called"))
    run_id = f"pytest_dry_{uuid.uuid4().hex}"
    output, summary = runner._output_paths(run_id)
    assert runner.main(["--dry-run", "--run-id", run_id]) == 0
    details = json.loads(capsys.readouterr().out)
    assert details["task_count"] == 4 and details["api_calls"] == 0
    assert not output.exists() and not summary.exists()


@pytest.mark.parametrize("run_id", ("../escape", "two/parts", "two\\parts", "contains.dot", ""))
def test_run_id_is_safe(run_id: str) -> None:
    with pytest.raises(ValueError, match="run-id"):
        runner._output_paths(run_id)


def test_safe_run_id_paths_are_distinct() -> None:
    output, summary = runner._output_paths("20260714_local1")
    assert output == ROOT / "docs/experiments/results/gemini_ab2d_local_l1_seed_20260714_local1.jsonl"
    assert summary == ROOT / "docs/experiments/gemini_ab2d_local_l1_seed_20260714_local1_summary.md"


def test_existing_output_is_never_overwritten(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(runner, "_preset", lambda: {"model": runner.MODEL_TAG})
    with tempfile.TemporaryDirectory(dir=ROOT) as temp:
        output = Path(temp) / "existing.jsonl"
        output.write_text("existing\n", encoding="utf-8")
        with pytest.raises(FileExistsError, match="refusing to overwrite"):
            runner._run(output, lambda *_: pytest.fail("provider must not be called"))


def test_mock_execute_makes_four_calls_persists_rows_and_summary(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        text = "def generate(level=1, **kwargs):\n    return {}\n"

    calls = 0
    fsync_calls: list[int] = []

    def fake_call(_prompt: str, _preset: dict) -> FakeResponse:
        nonlocal calls
        calls += 1
        return FakeResponse()

    monkeypatch.setattr(runner, "_preset", lambda: {"model": runner.MODEL_TAG})
    monkeypatch.setattr(runner.os, "fsync", lambda fd: fsync_calls.append(fd))
    with tempfile.TemporaryDirectory(dir=ROOT) as temp:
        output, summary = Path(temp) / "rows.jsonl", Path(temp) / "summary.md"
        rows = runner._run(output, fake_call)
        runner._write_summary(summary, rows)
        persisted = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
        assert summary.exists()
    assert calls == len(rows) == len(persisted) == 4
    assert len(fsync_calls) == 4
    assert all(row["request_count"] == 1 and row["retry_count"] == 0 and row["healer_used"] is False for row in persisted)


def test_rpm_module_import_is_preserved_and_executes_locally() -> None:
    rpm_task = next(task for task in runner._tasks() if task["skill_id"] == "rpm_circumference_to_kph")
    row = runner._make_row(rpm_task)
    source = """import math

def generate(level=1, **kwargs):
    divisor = math.gcd(39, 500)
    return {"question_text": "RPM conversion", "correct_answer": {"coefficient": f"{39 // divisor}/{500 // divisor}", "unit": "km/h"}, "oracle_payload": %r}
""" % row["task_parameters"]
    outcome, candidate, _ = classify_response(source, {"oracle_payload": row["task_parameters"]}, rpm_task, execution_timeout=3)
    assert candidate is not None and candidate.startswith("import math")
    assert outcome == "passed"
