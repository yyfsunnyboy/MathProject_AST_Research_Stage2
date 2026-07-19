from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path

import pytest

from scripts import freeze_mbpp_healer_v0_validation_p0 as freeze
from scripts import run_mbpp_healer_v0_validation_p0 as runner


REPO_ROOT = Path(__file__).resolve().parents[2]
GOV_DIR = REPO_ROOT / freeze.OUTPUT_RELATIVE


def _csv_rows(value: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(value.decode("utf-8"))))


def test_freeze_is_deterministic_complete_and_identity_only() -> None:
    first = freeze.build_outputs(REPO_ROOT)
    second = freeze.build_outputs(REPO_ROOT)
    assert first == second
    cells = _csv_rows(first["generation_cells.csv"])
    accounts = _csv_rows(first["evaluation_accounts.csv"])
    manifest = json.loads(first["manifest.json"])
    preflight = json.loads(first["zero_model_preflight.json"])

    assert hashlib.sha256(first["manifest.json"]).hexdigest() == runner.FROZEN_MANIFEST_SHA256
    assert len(cells) == len({row["generation_id"] for row in cells}) == 100
    assert len({(row["task_id"], row["seed"]) for row in cells}) == 100
    assert len({row["task_id"] for row in cells}) == 20
    assert len(accounts) == len({row["evaluation_account_id"] for row in accounts}) == 200
    assert sum(row["healer_account"] == "H0" for row in accounts) == 100
    assert sum(row["healer_account"] == "H1" for row in accounts) == 100
    assert manifest["seeds"] == [11, 22, 33, 44, 55]
    assert manifest["model_calls_during_freeze"] == 0
    assert manifest["evalplus_executions_during_freeze"] == 0
    assert preflight["validation_development_intersection"] == 0
    assert preflight["individually_reviewed"] == 0
    assert preflight["rule_development_sources"] == 0
    assert preflight["failure_census_sources"] == 0
    assert "prompt" not in cells[0]


def test_zero_model_preflight_accepts_only_frozen_manifest() -> None:
    receipt = runner.zero_model_preflight(
        manifest_path=GOV_DIR / "manifest.json",
        manifest_sha256=runner.FROZEN_MANIFEST_SHA256,
    )
    assert receipt["status"] == "zero_model_preflight_passed"
    assert receipt["model_calls"] == receipt["evalplus_executions"] == 0
    assert receipt["generation_cells"] == 100
    assert receipt["evaluation_accounts"] == 200
    with pytest.raises(runner.ValidationRunError, match="SHA-256"):
        runner.zero_model_preflight(
            manifest_path=GOV_DIR / "manifest.json",
            manifest_sha256="0" * 64,
        )


def test_validation_isolation_fails_on_review_or_rule_exposure(monkeypatch: pytest.MonkeyPatch) -> None:
    validation = freeze.load_validation_rows(REPO_ROOT)
    original = freeze._read_csv

    def contaminated(path: Path) -> list[dict[str, str]]:
        rows = original(path)
        if Path(path).name == freeze.CONTAMINATION_RELATIVE.name:
            target_ids = {row["task_id"] for row in validation}
            rows = [dict(row) for row in rows]
            next(row for row in rows if row["task_id"] in target_ids)["individually_reviewed"] = "true"
        return rows

    monkeypatch.setattr(freeze, "_read_csv", contaminated)
    with pytest.raises(freeze.ValidationFreezeError, match="individually reviewed"):
        freeze.validate_isolation(validation, REPO_ROOT)


def _fake_success_attempt(task: object, **kwargs: object) -> dict[str, object]:
    settings = kwargs["settings"]
    source = f"def {task.entry_point}(*args):\n    return None\n"
    request = {
        "model": freeze.EXPECTED_MODEL,
        "stream": False,
        "think": False,
        "messages": [{"role": "user", "content": task.prompt}],
        "options": {
            "num_ctx": settings.context_window,
            "num_predict": settings.num_predict,
            "seed": settings.seed,
            "temperature": settings.temperature,
            "top_k": settings.top_k,
            "top_p": settings.top_p,
        },
    }
    body = {
        "model": freeze.EXPECTED_MODEL,
        "created_at": "synthetic",
        "done": True,
        "done_reason": "stop",
        "total_duration": 1,
        "load_duration": 1,
        "prompt_eval_count": 1,
        "prompt_eval_duration": 1,
        "eval_count": 1,
        "eval_duration": 1,
        "message": {"content": source},
    }
    return {
        "raw_response": source,
        "generation_latency": 0.0,
        "ollama_response_metadata": {
            "raw_body": json.dumps(body),
            "request_payload": request,
        },
    }


def _patch_model_calls(
    monkeypatch: pytest.MonkeyPatch, run_dir: Path, attempt: object,
) -> None:
    monkeypatch.setattr(runner, "zero_model_preflight", lambda **kwargs: {"status": "ok"})
    monkeypatch.setattr(
        runner,
        "fetch_ollama_provenance",
        lambda *args, **kwargs: {
            "model_digest": freeze.EXPECTED_MODEL_DIGEST,
            "quantization": freeze.EXPECTED_QUANTIZATION,
        },
    )
    monkeypatch.setattr(runner, "run_attempt", attempt)
    monkeypatch.setattr(freeze, "RUN_OUTPUT_RELATIVE", run_dir)


def test_synthetic_generation_persists_100_journals_then_200_accounts(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    run_dir = tmp_path / "complete_run"
    _patch_model_calls(monkeypatch, run_dir, lambda task, treatment, **kwargs: _fake_success_attempt(task, **kwargs))
    runner.generate(
        manifest_path=GOV_DIR / "manifest.json",
        manifest_sha256=runner.FROZEN_MANIFEST_SHA256,
    )
    assert len(list((run_dir / "j").glob("*.json"))) == 100
    raw = [json.loads(line) for line in (run_dir / "raw_generations.jsonl").read_text(encoding="utf-8").splitlines()]
    accounts = [json.loads(line) for line in (run_dir / "h0_h1_accounts.jsonl").read_text(encoding="utf-8").splitlines()]
    materialization = json.loads((run_dir / "materialization_manifest.json").read_text(encoding="utf-8"))
    assert len(raw) == 100
    assert len(accounts) == 200
    assert len({row["evaluation_account_id"] for row in accounts}) == 200
    assert materialization["evalplus_executions"] == 0
    assert materialization["retry_count"] == 0
    assert materialization["resume"] is False


def test_incomplete_generation_keeps_journals_but_forbids_materialization(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    run_dir = tmp_path / "incomplete_run"
    call_count = 0

    def one_failure(task: object, treatment: str, **kwargs: object) -> dict[str, object]:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return {}
        return _fake_success_attempt(task, **kwargs)

    _patch_model_calls(monkeypatch, run_dir, one_failure)
    with pytest.raises(runner.ValidationRunError, match="resume/retry forbidden"):
        runner.generate(
            manifest_path=GOV_DIR / "manifest.json",
            manifest_sha256=runner.FROZEN_MANIFEST_SHA256,
        )
    assert call_count == 100
    assert len(list((run_dir / "j").glob("*.json"))) == 100
    assert not (run_dir / "raw_generations.jsonl").exists()
    assert not (run_dir / "pipeline_normalized.jsonl").exists()
    assert not (run_dir / "h0_h1_accounts.jsonl").exists()


def test_runner_has_no_evalplus_or_scaffold_execution_path() -> None:
    source = (REPO_ROOT / "scripts/run_mbpp_healer_v0_validation_p0.py").read_text(encoding="utf-8")
    assert "from evalplus" not in source
    assert "import evalplus" not in source
    assert "commands.add_parser(\"evaluate\")" not in source
    assert "h1_regeneration\": False" in source
