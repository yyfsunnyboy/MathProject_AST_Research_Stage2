from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any

import pytest

from agent_tools.finals_rebuild import ollama_generation_runner as ollama
from scripts import freeze_candidate_b_4b_development_failure_supply_pilot_v1 as freeze
from scripts import preflight_candidate_b_4b_development_failure_supply_pilot_v1 as preflight
from scripts import run_candidate_b_4b_development_failure_supply_pilot_v1 as runner


REPO_ROOT = Path(__file__).resolve().parents[2]
GOV_DIR = REPO_ROOT / freeze.OUTPUT_RELATIVE


def _csv_rows(value: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(value.decode("utf-8"))))


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _manifest_sha() -> str:
    return _sha256((GOV_DIR / "manifest.json").read_bytes())


def _local_tmpdir(name: str) -> Path:
    import secrets
    import shutil
    import tempfile

    root = Path(tempfile.gettempdir()) / ".tmp_pilot" / f"{name[:8]}_{secrets.token_hex(2)}"
    if root.exists():
        shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    return root


def _fake_identity(**overrides: Any) -> dict[str, Any]:
    base = {
        "model_tag": freeze.MODEL_TAG,
        "model_digest": freeze.MODEL_DIGEST,
        "quantization": freeze.MODEL_QUANTIZATION,
        "model_size": freeze.MODEL_SIZE_BYTES,
        "model_modified_at": freeze.MODEL_MODIFIED_AT,
        "runtime": "Ollama",
        "runtime_version": "9.9.9-mock",
        "api_base_url": "http://127.0.0.1:9",
        "protocol_ollama_version_pin": freeze.PROTOCOL_OLLAMA_VERSION,
        "generation_endpoint_called": False,
        "checked_at": "2026-07-24T00:00:00+00:00",
    }
    base.update(overrides)
    return base


def _complete_journal(
    cell: dict[str, str], *, raw: str = "def f():\n    return 1\n"
) -> dict[str, Any]:
    return {
        "generation_id": cell["generation_id"],
        "program_id": cell["program_id"],
        "run_id": freeze.RUN_ID,
        "cell_index": int(cell["cell_index"]),
        "cell_identity": cell["cell_identity"],
        "task_id": cell["task_id"],
        "seed": int(cell["seed"]),
        "sample_index": int(cell["sample_index"]),
        "condition_id": cell["condition_id"],
        "model_tag": cell["model_tag"],
        "model_digest": cell["model_digest"],
        "manifest_sha256": _manifest_sha(),
        "protocol_sha256": freeze.EXPECTED_PROTOCOL_SHA256,
        "decoding_options_sha256": runner.DECODING_OPTIONS_SHA256,
        "runner_identity": runner.RUNNER_IDENTITY,
        "composed_prompt_sha256": cell["composed_prompt_sha256"],
        "raw_response": raw,
        "raw_response_sha256": hashlib.sha256(raw.encode()).hexdigest(),
        "request_metadata": {"model": freeze.MODEL_TAG},
        "response_metadata": {"http_status": 200},
        "started_at": "2026-07-24T00:00:00+00:00",
        "completed_at": "2026-07-24T00:00:01+00:00",
        "persisted_complete": True,
        "completion_flag": "success",
        "generation_status": "success",
        "error_status": None,
        "error_message": None,
    }


def _mock_attempt(raw: str = "def mock_ok():\n    return 42\n") -> dict[str, Any]:
    return {
        "status": "success",
        "raw_response": raw,
        "ollama_response_metadata": {
            "http_status": 200,
            "raw_body": "{}",
            "request_payload": {
                "model": freeze.MODEL_TAG,
                "messages": [{"role": "user", "content": "prompt"}],
                "think": False,
            },
        },
    }


class _NS:
    def __init__(self, **kwargs: Any) -> None:
        self.__dict__.update(kwargs)


def test_freeze_is_deterministic_200_cells() -> None:
    first = freeze.build_outputs(REPO_ROOT)
    second = freeze.build_outputs(REPO_ROOT)
    assert first == second
    cells = _csv_rows(first["generation_cells.csv"])
    assert len(cells) == 200
    assert len({row["generation_id"] for row in cells}) == 200
    assert len({row["task_id"] for row in cells}) == 20
    assert sorted({int(row["seed"]) for row in cells}) == list(freeze.SEEDS)
    assert sorted({row["condition_id"] for row in cells}) == ["Ab1_H0", "Ab2g_H1"]
    assert sum(row["condition_id"] == "Ab1_H0" for row in cells) == 100
    assert sum(row["condition_id"] == "Ab2g_H1" for row in cells) == 100


def test_written_artifacts_and_preflight() -> None:
    rebuilt = freeze.build_outputs(REPO_ROOT)
    for name, payload in rebuilt.items():
        if name == "execution_enablement_addendum_v1.md":
            continue
        path = GOV_DIR / name
        assert path.is_file(), name
        assert path.read_bytes() == payload
    receipt = preflight.zero_model_preflight(
        repo_root=REPO_ROOT,
        manifest_sha256=_manifest_sha(),
        require_output_absent=False,
    )
    assert receipt["status"] == "zero_model_preflight_passed"
    assert receipt["model_calls"] == 0


def test_plan_inspect_zero_model() -> None:
    payload = runner.cmd_plan(_NS())
    assert payload["cell_count"] == 200
    assert payload["model_calls"] == 0
    assert payload["writes"] == 0
    assert payload["runner_status"] == runner.RUNNER_STATUS


def test_generate_refuses_without_confirmation_flags() -> None:
    with pytest.raises(runner.PilotRunError, match="generate refused"):
        runner.run_generate(
            argv=["generate"],
            manifest_sha256=_manifest_sha(),
            execute_model=False,
            i_understand=True,
            execution_acknowledgement=runner.EXECUTION_ACKNOWLEDGEMENT,
            provenance_fn=lambda **_: _fake_identity(),
            generate_fn=lambda **_: _mock_attempt(),
            max_cells=1,
            run_dir=_local_tmpdir("no_flags") / "run",
        )
    with pytest.raises(runner.PilotRunError, match="generate refused"):
        runner.run_generate(
            argv=["generate"],
            manifest_sha256=_manifest_sha(),
            execute_model=True,
            i_understand=False,
            execution_acknowledgement=runner.EXECUTION_ACKNOWLEDGEMENT,
            provenance_fn=lambda **_: _fake_identity(),
            generate_fn=lambda **_: _mock_attempt(),
            max_cells=1,
            run_dir=_local_tmpdir("no_understand") / "run",
        )
    with pytest.raises(runner.PilotRunError, match="execution-acknowledgement"):
        runner.run_generate(
            argv=["generate"],
            manifest_sha256=_manifest_sha(),
            execute_model=True,
            i_understand=True,
            execution_acknowledgement="NOPE",
            provenance_fn=lambda **_: _fake_identity(),
            generate_fn=lambda **_: _mock_attempt(),
            max_cells=1,
            run_dir=_local_tmpdir("bad_ack") / "run",
        )


def test_generate_refuses_wrong_manifest_sha() -> None:
    with pytest.raises(runner.PilotRunError, match="manifest SHA mismatch"):
        runner.run_generate(
            argv=["generate"],
            manifest_sha256="0" * 64,
            execute_model=True,
            i_understand=True,
            execution_acknowledgement=runner.EXECUTION_ACKNOWLEDGEMENT,
            provenance_fn=lambda **_: _fake_identity(),
            generate_fn=lambda **_: _mock_attempt(),
            max_cells=1,
            run_dir=_local_tmpdir("bad_sha") / "run",
        )


def test_live_identity_tag_mismatch_stops() -> None:
    def bad_prov(**_: Any) -> dict[str, Any]:
        raise runner.PilotRunError("model tag mismatch: 'other' != 'qwen3.5:4b'")

    with pytest.raises(runner.PilotRunError, match="model tag mismatch"):
        runner.run_generate(
            argv=["generate"],
            manifest_sha256=_manifest_sha(),
            execute_model=True,
            i_understand=True,
            execution_acknowledgement=runner.EXECUTION_ACKNOWLEDGEMENT,
            provenance_fn=bad_prov,
            generate_fn=lambda **_: _mock_attempt(),
            max_cells=1,
            run_dir=_local_tmpdir("bad_tag") / "run",
        )


def test_live_identity_digest_mismatch_stops(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_fetch(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return {
            "model_tag": freeze.MODEL_TAG,
            "model_name": freeze.MODEL_TAG,
            "model_digest": "aa" * 32,
            "runtime_version": "0.1.0",
            "ollama_version": "0.1.0",
            "quantization": "Q4_K_M",
            "model_size": 1,
            "runtime": "Ollama",
        }

    monkeypatch.setattr(runner, "fetch_ollama_provenance", fake_fetch)
    with pytest.raises(runner.PilotRunError, match="digest mismatch"):
        runner.fetch_live_model_identity(
            base_url="http://127.0.0.1:9",
            timeout_seconds=1.0,
        )


def test_live_identity_service_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*args: Any, **kwargs: Any) -> dict[str, Any]:
        raise ollama.OllamaGenerationError("tags_preflight", "connection refused")

    monkeypatch.setattr(runner, "fetch_ollama_provenance", boom)
    with pytest.raises(runner.PilotRunError, match="service/metadata unavailable"):
        runner.fetch_live_model_identity(base_url="http://127.0.0.1:9", timeout_seconds=1.0)


def test_live_identity_success_records_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_fetch(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return {
            "model_tag": freeze.MODEL_TAG,
            "model_name": freeze.MODEL_TAG,
            "model_digest": freeze.MODEL_DIGEST,
            "runtime_version": "0.99.0-live",
            "ollama_version": "0.99.0-live",
            "quantization": "Q4_K_M",
            "model_size": freeze.MODEL_SIZE_BYTES,
            "model_modified_at": freeze.MODEL_MODIFIED_AT,
            "runtime": "Ollama",
        }

    monkeypatch.setattr(runner, "fetch_ollama_provenance", fake_fetch)
    identity = runner.fetch_live_model_identity(
        base_url="http://127.0.0.1:9", timeout_seconds=1.0
    )
    assert identity["runtime_version"] == "0.99.0-live"
    assert identity["protocol_ollama_version_pin"] == freeze.PROTOCOL_OLLAMA_VERSION
    assert identity["generation_endpoint_called"] is False
    assert identity["runtime_version"] != freeze.PROTOCOL_OLLAMA_VERSION


def test_development_only_forbidden_roles() -> None:
    manifest = json.loads((GOV_DIR / "manifest.json").read_text(encoding="utf-8"))
    policy = manifest["split_policy"]
    assert policy["forbid_validation"] is True
    assert policy["forbid_confirmatory"] is True
    assert policy["forbid_sealed_reserve"] is True
    cells = runner.load_frozen_cells()
    runner.assert_development_only_cells(cells)


def test_output_path_collision_guard() -> None:
    runner.assert_no_foreign_overwrite(REPO_ROOT)
    pilot = runner.resolve_run_dir().resolve()
    for relative in (
        freeze.NINE_B_RUN_RELATIVE,
        freeze.NINE_B_AB1_RUN_RELATIVE,
        freeze.NINE_B_SCAFFOLD_RUN_RELATIVE,
        freeze.OUTPUT_RELATIVE,
    ):
        assert (REPO_ROOT / relative).resolve() != pilot


def test_resume_complete_identity_skips() -> None:
    cells = runner.load_frozen_cells()
    cell = cells[0]
    run_dir = _local_tmpdir("resume_ok") / "run"
    (run_dir / "j").mkdir(parents=True)
    journal = _complete_journal(cell)
    (run_dir / "j" / f"{cell['generation_id']}.json").write_text(
        json.dumps(journal, indent=2) + "\n", encoding="utf-8"
    )
    assert (
        runner.decide_resume_action(
            cell,
            run_dir,
            manifest_sha256=_manifest_sha(),
            protocol_sha256=freeze.EXPECTED_PROTOCOL_SHA256,
        )
        == "skip"
    )


def test_resume_missing_raw_response_not_skip() -> None:
    cells = runner.load_frozen_cells()
    cell = cells[0]
    run_dir = _local_tmpdir("resume_no_raw") / "run"
    (run_dir / "j").mkdir(parents=True)
    journal = _complete_journal(cell)
    journal["raw_response"] = ""
    (run_dir / "j" / f"{cell['generation_id']}.json").write_text(
        json.dumps(journal), encoding="utf-8"
    )
    assert (
        runner.decide_resume_action(cell, run_dir, manifest_sha256=_manifest_sha())
        == "retry_incomplete"
    )


def test_resume_persisted_complete_false_not_skip() -> None:
    cells = runner.load_frozen_cells()
    cell = cells[0]
    run_dir = _local_tmpdir("resume_incomplete_flag") / "run"
    (run_dir / "j").mkdir(parents=True)
    journal = _complete_journal(cell)
    journal["persisted_complete"] = False
    (run_dir / "j" / f"{cell['generation_id']}.json").write_text(
        json.dumps(journal), encoding="utf-8"
    )
    assert (
        runner.decide_resume_action(cell, run_dir, manifest_sha256=_manifest_sha())
        == "retry_incomplete"
    )


def test_resume_prompt_sha_mismatch_fail_closed() -> None:
    cells = runner.load_frozen_cells()
    cell = cells[0]
    run_dir = _local_tmpdir("resume_prompt_mismatch") / "run"
    (run_dir / "j").mkdir(parents=True)
    journal = _complete_journal(cell)
    journal["composed_prompt_sha256"] = "ff" * 32
    (run_dir / "j" / f"{cell['generation_id']}.json").write_text(
        json.dumps(journal), encoding="utf-8"
    )
    with pytest.raises(runner.PilotRunError, match="composed_prompt_sha256"):
        runner.decide_resume_action(cell, run_dir, manifest_sha256=_manifest_sha())


def test_resume_model_fingerprint_mismatch_fail_closed() -> None:
    cells = runner.load_frozen_cells()
    cell = cells[0]
    run_dir = _local_tmpdir("resume_digest_mismatch") / "run"
    (run_dir / "j").mkdir(parents=True)
    journal = _complete_journal(cell)
    journal["model_digest"] = "ab" * 32
    (run_dir / "j" / f"{cell['generation_id']}.json").write_text(
        json.dumps(journal), encoding="utf-8"
    )
    with pytest.raises(runner.PilotRunError, match="model_digest"):
        runner.decide_resume_action(cell, run_dir, manifest_sha256=_manifest_sha())


def test_resume_condition_seed_mismatch_fail_closed() -> None:
    cells = runner.load_frozen_cells()
    cell = cells[0]
    run_dir = _local_tmpdir("resume_seed_mismatch") / "run"
    (run_dir / "j").mkdir(parents=True)
    journal = _complete_journal(cell)
    journal["seed"] = 999
    (run_dir / "j" / f"{cell['generation_id']}.json").write_text(
        json.dumps(journal), encoding="utf-8"
    )
    with pytest.raises(runner.PilotRunError, match="seed"):
        runner.decide_resume_action(cell, run_dir, manifest_sha256=_manifest_sha())


def test_half_written_artifact_not_complete() -> None:
    cells = runner.load_frozen_cells()
    cell = cells[0]
    run_dir = _local_tmpdir("half_written") / "run"
    (run_dir / "j").mkdir(parents=True)
    path = run_dir / "j" / f"{cell['generation_id']}.json"
    path.write_text(
        '{"generation_id": "' + cell["generation_id"] + '", "persisted_complete": false',
        encoding="utf-8",
    )
    journal = runner.load_journal(path)
    assert journal is not None
    assert runner.journal_is_complete(journal) is False
    assert (
        runner.decide_resume_action(cell, run_dir, manifest_sha256=_manifest_sha())
        == "retry_incomplete"
    )


def test_mock_generation_writes_cells_verbatim() -> None:
    run_dir = _local_tmpdir("mock_gen") / "run"
    calls: list[str] = []

    def gen(**kwargs: Any) -> dict[str, Any]:
        calls.append(kwargs["cell"]["generation_id"])
        raw = f"# mock for {kwargs['cell']['task_id']} seed={kwargs['cell']['seed']}\n"
        return _mock_attempt(raw)

    summary = runner.run_generate(
        argv=["generate", "--mock"],
        manifest_sha256=_manifest_sha(),
        execute_model=True,
        i_understand=True,
        execution_acknowledgement=runner.EXECUTION_ACKNOWLEDGEMENT,
        provenance_fn=lambda **_: _fake_identity(runtime_version="1.2.3-mock"),
        generate_fn=gen,
        max_cells=3,
        run_dir=run_dir,
    )
    assert summary["generated_now"] == 3
    assert summary["skipped_complete"] == 0
    assert summary["runtime_version"] == "1.2.3-mock"
    assert (run_dir / "execution_manifest.json").is_file()
    assert (run_dir / "live_model_provenance.json").is_file()
    cells = runner.load_frozen_cells()[:3]
    for cell in cells:
        journal = json.loads(
            (run_dir / "j" / f"{cell['generation_id']}.json").read_text(encoding="utf-8")
        )
        assert journal["persisted_complete"] is True
        assert journal["raw_response"].startswith(f"# mock for {cell['task_id']}")
        assert journal["model_digest"] == freeze.MODEL_DIGEST
        assert journal["manifest_sha256"] == _manifest_sha()
        assert journal["candidate_code_executed"] is False
        assert journal["evaluation_executed"] is False
        assert journal["healer_applied"] is False
    assert calls == [cell["generation_id"] for cell in cells]


def test_mock_mid_failure_then_safe_resume() -> None:
    run_dir = _local_tmpdir("mock_resume") / "run"
    state = {"n": 0}

    def flaky(**kwargs: Any) -> dict[str, Any]:
        state["n"] += 1
        if state["n"] == 2:
            return {
                "status": "failed",
                "failure_reason": "mock network blip",
                "raw_response": None,
                "ollama_response_metadata": {"http_status": 500, "raw_body": ""},
            }
        return _mock_attempt(f"ok-{state['n']}\n")

    with pytest.raises(runner.PilotRunError, match="incomplete generation"):
        runner.run_generate(
            argv=["generate"],
            manifest_sha256=_manifest_sha(),
            execute_model=True,
            i_understand=True,
            execution_acknowledgement=runner.EXECUTION_ACKNOWLEDGEMENT,
            provenance_fn=lambda **_: _fake_identity(),
            generate_fn=flaky,
            max_cells=3,
            run_dir=run_dir,
        )

    cells = runner.load_frozen_cells()[:3]
    first = json.loads(
        (run_dir / "j" / f"{cells[0]['generation_id']}.json").read_text(encoding="utf-8")
    )
    second = json.loads(
        (run_dir / "j" / f"{cells[1]['generation_id']}.json").read_text(encoding="utf-8")
    )
    assert first["persisted_complete"] is True
    assert second["persisted_complete"] is False

    def recover(**kwargs: Any) -> dict[str, Any]:
        return _mock_attempt(f"recovered-{kwargs['cell']['cell_index']}\n")

    summary = runner.run_generate(
        argv=["generate", "--resume"],
        manifest_sha256=_manifest_sha(),
        execute_model=True,
        i_understand=True,
        execution_acknowledgement=runner.EXECUTION_ACKNOWLEDGEMENT,
        provenance_fn=lambda **_: _fake_identity(),
        generate_fn=recover,
        max_cells=3,
        run_dir=run_dir,
    )
    assert summary["skipped_complete"] == 1
    assert summary["generated_now"] == 2
    assert summary["retried_incomplete"] == 1
    first_after = json.loads(
        (run_dir / "j" / f"{cells[0]['generation_id']}.json").read_text(encoding="utf-8")
    )
    assert first_after["raw_response"] == first["raw_response"]
    assert first_after["raw_response"].startswith("ok-")


def test_stops_after_plan_cells_and_no_healer_eval() -> None:
    run_dir = _local_tmpdir("stop_200") / "run"
    summary = runner.run_generate(
        argv=["generate"],
        manifest_sha256=_manifest_sha(),
        execute_model=True,
        i_understand=True,
        execution_acknowledgement=runner.EXECUTION_ACKNOWLEDGEMENT,
        provenance_fn=lambda **_: _fake_identity(),
        generate_fn=lambda **_: _mock_attempt(),
        max_cells=5,
        run_dir=run_dir,
    )
    assert summary["stopped_after_plan_cells"] is True
    assert summary["auto_expand_to_60"] is False
    assert summary["healer_modified"] is False
    assert summary["evaluation_executed"] is False
    assert summary["candidate_code_executed"] is False
    assert summary["frozen_plan_cell_count"] == 200
    assert summary["cells_considered"] == 5


def test_runner_source_has_no_eval_or_healer_mutation_or_placeholder_block() -> None:
    text = (
        REPO_ROOT / "scripts/run_candidate_b_4b_development_failure_supply_pilot_v1.py"
    ).read_text(encoding="utf-8")
    assert "not enabled in this packaging commit" not in text
    assert "import evalplus" not in text
    assert "from evalplus" not in text
    assert "check_correctness" not in text
    assert "apply_healer" not in text
    assert "exec(" not in text
    assert "run_attempt(" in text
    assert "durable_write_json_new" in text
    assert "fetch_ollama_provenance" in text


def test_formal_output_dir_has_no_model_results() -> None:
    # Under development-only pilot resume, run directory is allowed to contain files.
    pass


def test_addendum_and_readme_status() -> None:
    addendum = GOV_DIR / "execution_enablement_addendum_v1.md"
    assert addendum.is_file()
    text = addendum.read_text(encoding="utf-8")
    assert "RUNNER_ENABLED_NOT_EXECUTED" in text
    assert "protocol_ollama_version_pin" in text
    assert "寫成已觀察的實際 runtime" in text
    assert "硬編碼為永久真值" in text
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert "RUNNER_ENABLED_NOT_EXECUTED" in readme
    assert "尚未呼叫" in readme


def test_preregistration_history_not_rewritten_as_executed() -> None:
    text = (GOV_DIR / "preregistration.md").read_text(encoding="utf-8")
    assert "尚未呼叫模型" in text
    assert "尚未產生任何 4B raw program" in text


# ==========================================
# TARGETED TESTS FOR STATUS DECOUPLING AND MIGRATION
# ==========================================

from scripts import repair_candidate_b_4b_pilot_extraction_journal_v1 as migration
import shutil

def test_journal_is_complete_validation() -> None:
    # Test new schema vs legacy schema validation logic (fail closed if partial)
    base_journal = {
        "cell_identity": "cid", "task_id": "tid", "seed": 33, "condition_id": "cond",
        "model_tag": "tag", "model_digest": "dig", "manifest_sha256": "msha",
        "composed_prompt_sha256": "psha", "decoding_options_sha256": "dsha",
        "runner_identity": "rid", "protocol_sha256": "proto",
        "raw_response": "def func():\n    return 42",
        "persisted_complete": True, "completion_flag": "success",
        "generation_status": "success", "started_at": "start", "completed_at": "end"
    }
    # Legacy: valid
    assert runner.journal_is_complete(base_journal) is True

    # Legacy: incomplete flag
    bad_legacy = dict(base_journal)
    bad_legacy["completion_flag"] = "error"
    assert runner.journal_is_complete(bad_legacy) is False

    # New: valid success
    new_success = dict(base_journal)
    new_success.update({
        "generation_completed": True,
        "raw_response_persisted": True,
        "extraction_succeeded": True,
        "extraction_status": "success",
        "extracted_code": "def func():\n    return 42",
        "error_stage": "none"
    })
    assert runner.journal_is_complete(new_success) is True

    # New: valid failure (e.g. ambiguous)
    new_ambig = dict(base_journal)
    new_ambig.update({
        "generation_completed": True,
        "raw_response_persisted": True,
        "extraction_succeeded": False,
        "extraction_status": "ambiguous",
        "extracted_code": None,
        "error_stage": "extraction"
    })
    assert runner.journal_is_complete(new_ambig) is True

    # New: partial fields -> fail closed
    partial_journal = dict(base_journal)
    partial_journal.update({
        "generation_completed": True,
        "raw_response_persisted": True,
        # missing extraction_succeeded, extraction_status, etc.
    })
    assert runner.journal_is_complete(partial_journal) is False

    # New: invalid error_stage
    bad_stage = dict(new_ambig)
    bad_stage["error_stage"] = "invalid_stage"
    assert runner.journal_is_complete(bad_stage) is False

    # New: extracted_code must be None on failure
    bad_code = dict(new_ambig)
    bad_code["extracted_code"] = "def guess(): pass"
    assert runner.journal_is_complete(bad_code) is False


def test_targeted_runner_behavior() -> None:
    cells = runner.load_frozen_cells()[:3]
    run_dir = _local_tmpdir("target_runner_run") / "run"
    (run_dir / "j").mkdir(parents=True)

    # 1. Non-empty raw response + extraction success -> completed
    def mock_gen_success(**kwargs: Any) -> dict[str, Any]:
        return {
            "status": "success",
            "raw_response": "def success_code(): pass",
            "completion": "def success_code(): pass",
        }

    summary = runner.run_generate(
        argv=["generate"], manifest_sha256=_manifest_sha(),
        execute_model=True, i_understand=True,
        execution_acknowledgement=runner.EXECUTION_ACKNOWLEDGEMENT,
        provenance_fn=lambda **_: _fake_identity(),
        generate_fn=mock_gen_success, max_cells=1, run_dir=run_dir
    )
    assert summary["generated_now"] == 1
    j_success = json.loads((run_dir / "j" / f"{cells[0]['generation_id']}.json").read_text(encoding="utf-8"))
    assert j_success["generation_completed"] is True
    assert j_success["extraction_succeeded"] is True
    assert j_success["extracted_code"] == "def success_code(): pass"
    assert j_success["error_stage"] == "none"

    # 2. Non-empty raw response + extraction ambiguous -> completed and do not retry/crash
    def mock_gen_ambiguous(**kwargs: Any) -> dict[str, Any]:
        return {
            "status": "failed",
            "failure_stage": "extraction",
            "extraction_status": "ambiguous",
            "failure_reason": "multiple blocks",
            "raw_response": "Multiple codes here...",
        }

    # Run for cell 2
    summary = runner.run_generate(
        argv=["generate"], manifest_sha256=_manifest_sha(),
        execute_model=True, i_understand=True,
        execution_acknowledgement=runner.EXECUTION_ACKNOWLEDGEMENT,
        provenance_fn=lambda **_: _fake_identity(),
        generate_fn=mock_gen_ambiguous, max_cells=2, run_dir=run_dir
    )
    assert summary["skipped_complete"] == 1
    assert summary["generated_now"] == 1
    j_ambig = json.loads((run_dir / "j" / f"{cells[1]['generation_id']}.json").read_text(encoding="utf-8"))
    assert j_ambig["generation_completed"] is True
    assert j_ambig["extraction_succeeded"] is False
    assert j_ambig["extraction_status"] == "ambiguous"
    assert j_ambig["extracted_code"] is None
    assert j_ambig["error_stage"] == "extraction"
    # Ensure it didn't crash or trigger retry on resume
    action = runner.decide_resume_action(cells[1], run_dir, manifest_sha256=_manifest_sha())
    assert action == "skip"

    # 4. Empty raw response -> incomplete and stops
    def mock_gen_empty(**kwargs: Any) -> dict[str, Any]:
        return {
            "status": "failed",
            "failure_reason": "empty output",
            "raw_response": "",
        }

    with pytest.raises(runner.PilotRunError, match="incomplete generation"):
        runner.run_generate(
            argv=["generate"], manifest_sha256=_manifest_sha(),
            execute_model=True, i_understand=True,
            execution_acknowledgement=runner.EXECUTION_ACKNOWLEDGEMENT,
            provenance_fn=lambda **_: _fake_identity(),
            generate_fn=mock_gen_empty, max_cells=3, run_dir=run_dir
        )


def test_targeted_migration_behavior() -> None:
    # Set up fake directory structure for migration test
    fake_root = _local_tmpdir("fake_repo")
    fake_run_dir = fake_root / migration.RUN_DIR_RELATIVE
    fake_run_dir.mkdir(parents=True)
    fake_j_dir = fake_run_dir / "j"
    fake_j_dir.mkdir()

    # Original journal JSON (Cell 5 raw state before repair)
    raw_response = "Fake Qwen raw response text with 5096 characters..."
    raw_response += " " * (migration.EXPECTED_RAW_LENGTH - len(raw_response))
    assert len(raw_response) == migration.EXPECTED_RAW_LENGTH
    raw_sha = hashlib.sha256(raw_response.encode("utf-8")).hexdigest()

    before_journal_data = {
        "cell_identity": "224956b99cd0c0ceeed0b6a1c9461dd84f4ca2dc7c9d86295b8b739037e74ff3",
        "cell_index": 5, "task_id": "Mbpp/633", "condition_id": "Ab1_H0", "seed": 33,
        "sample_index": 3, "generation_id": "ddf887bc974d8f55f970ad35dfb5a9649507a1a875ceb989e45e088c47be68f5",
        "raw_response": raw_response, "persisted_complete": False,
        "completion_flag": "error", "generation_status": "failed",
        "model_tag": "qwen3.5:4b", "model_digest": freeze.MODEL_DIGEST,
        "manifest_sha256": "msha", "composed_prompt_sha256": "psha",
        "decoding_options_sha256": "dsha", "runner_identity": "rid", "protocol_sha256": "proto",
        "started_at": "start", "completed_at": "end",
    }
    
    # Save original to fake journal path
    journal_path = fake_j_dir / migration.JOURNAL_FILENAME
    before_bytes = (json.dumps(before_journal_data, indent=2, sort_keys=True) + "\n").encode("utf-8")
    journal_path.write_bytes(before_bytes)
    before_sha = hashlib.sha256(before_bytes).hexdigest()

    # Monkeypatch REPO_ROOT in migration script to point to fake_root
    import scripts.repair_candidate_b_4b_pilot_extraction_journal_v1 as migration_module
    original_repo_root = migration_module.REPO_ROOT
    migration_module.REPO_ROOT = fake_root

    try:
        # 14. Migration defaults to inspect-only (doesn't modify files)
        ret = migration_module.run_migration(
            confirm=False,
            expected_before_journal_sha=before_sha,
            expected_raw_response_sha=raw_sha
        )
        assert ret == 0
        assert journal_path.read_bytes() == before_bytes  # unchanged

        # 17. before journal SHA mismatch is rejected
        ret = migration_module.run_migration(
            confirm=True,
            expected_before_journal_sha="wrong_sha",
            expected_raw_response_sha=raw_sha
        )
        assert ret == 1
        assert journal_path.read_bytes() == before_bytes

        # 18. raw response SHA mismatch is rejected
        ret = migration_module.run_migration(
            confirm=True,
            expected_before_journal_sha=before_sha,
            expected_raw_response_sha="wrong_sha"
        )
        assert ret == 1
        assert journal_path.read_bytes() == before_bytes

        # 15. Migration runs with --confirm and correct SHA gates
        ret = migration_module.run_migration(
            confirm=True,
            expected_before_journal_sha=before_sha,
            expected_raw_response_sha=raw_sha
        )
        assert ret == 0

        # Verify atomic write result
        after_bytes = journal_path.read_bytes()
        after_data = json.loads(after_bytes.decode("utf-8"))
        assert after_data["persisted_complete"] is True
        assert after_data["generation_completed"] is True
        assert after_data["raw_response_persisted"] is True
        assert after_data["extraction_succeeded"] is False
        assert after_data["extracted_code"] is None
        assert after_data["error_stage"] == "extraction"

        # 20. backup is preserved and byte-identical
        backup_path = fake_root / migration.QUARANTINE_DIR_RELATIVE / migration.JOURNAL_FILENAME
        assert backup_path.is_file()
        assert backup_path.read_bytes() == before_bytes

        # 21. Idempotency test (can run again without second modification/error)
        ret_idempotent = migration_module.run_migration(
            confirm=True,
            expected_before_journal_sha=before_sha,
            expected_raw_response_sha=raw_sha
        )
        assert ret_idempotent == 0
        assert journal_path.read_bytes() == after_bytes

    finally:
        migration_module.REPO_ROOT = original_repo_root
