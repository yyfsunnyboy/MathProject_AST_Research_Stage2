from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path

import pytest

from agent_tools.finals_rebuild import ollama_generation_runner as ollama
from scripts import freeze_mbpp_candidate_b_development60_replay as freeze
from scripts import run_mbpp_candidate_b_development60_replay as runner


REPO_ROOT = Path(__file__).resolve().parents[2]
GOV_DIR = REPO_ROOT / freeze.OUTPUT_RELATIVE


def _csv_rows(value: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(value.decode("utf-8"))))


def test_freeze_is_deterministic_and_complete_2x2() -> None:
    first = freeze.build_outputs(REPO_ROOT)
    second = freeze.build_outputs(REPO_ROOT)
    assert first == second
    assert hashlib.sha256(first["manifest.json"]).hexdigest() == runner.FROZEN_MANIFEST_SHA256
    cells = _csv_rows(first["candidate_b_generation_cells.csv"])
    accounts = _csv_rows(first["development_2x2_accounts.csv"])
    reuse = _csv_rows(first["p0_identity_hash_reuse_ledger.csv"])
    mapping = _csv_rows(first["r001_r002_r003_identity_mapping.csv"])
    manifest = json.loads(first["manifest.json"])
    r001_incident = json.loads(first["r001_incident_ledger.json"])
    r002_incident = json.loads(first["r002_incident_ledger.json"])

    assert len(cells) == len({row["generation_id"] for row in cells}) == 300
    assert len({(row["task_id"], row["seed"]) for row in cells}) == 300
    assert len({row["task_id"] for row in cells}) == 60
    assert len(accounts) == len({row["evaluation_account_id"] for row in accounts}) == 1200
    assert len(reuse) == len({row["program_id"] for row in reuse}) == 300
    assert len(mapping) == 300
    assert all(row["same_task_seed_identity"] == "true" for row in mapping)
    assert all(row["r001_generation_id"] != row["r002_generation_id"] for row in mapping)
    assert all(row["r002_generation_id"] != row["r003_generation_id"] for row in mapping)
    assert all(row["r001_result_reused"] == "false" for row in mapping)
    assert all(row["r002_result_reused"] == "false" for row in mapping)
    assert sum(row["factorial_arm"] == "P0_H0" for row in accounts) == 300
    assert sum(row["factorial_arm"] == "P0_H1" for row in accounts) == 300
    assert sum(row["factorial_arm"] == "Candidate_B_H0" for row in accounts) == 300
    assert sum(row["factorial_arm"] == "Candidate_B_H1" for row in accounts) == 300
    assert all(row["result_reexecution"] == "false" for row in reuse)
    assert manifest["existing_p0_results"] == {
        "h0_pass": 68, "h1_pass": 77, "programs": 300, "reexecuted": False,
    }
    assert manifest["model_calls_during_freeze"] == 0
    assert manifest["evalplus_executions_during_freeze"] == 0
    assert manifest["validation_run_directory_created"] is False
    assert manifest["run_id"] == freeze.RUN_ID
    assert manifest["predecessor_incidents"][0]["classification"] == "ZERO_CELL_PREFLIGHT_INCIDENT"
    assert manifest["predecessor_incidents"][1]["classification"] == "FIRST_CELL_JOURNAL_PERSISTENCE_FAILURE"
    assert r001_incident["classification"] == "ZERO_CELL_PREFLIGHT_INCIDENT"
    assert r001_incident["model_calls"] == r001_incident["generation_journals"] == 0
    assert r002_incident["classification"] == "FIRST_CELL_JOURNAL_PERSISTENCE_FAILURE"
    assert r002_incident["model_call_status"] == "model_call_confirmed_1"
    assert r002_incident["model_calls"] == 1
    assert r002_incident["generation_journals"] == 0
    assert r002_incident["persisted_responses"] == r002_incident["selectable_responses"] == 0
    assert r002_incident["evaluator_executions"] == 0
    assert r002_incident["eligible_for_analysis_or_reuse"] is False
    assert r002_incident["r002_content_used_by_r003"] is False


def test_candidate_b_exact_text_and_frozen_gates() -> None:
    outputs = freeze.build_outputs(REPO_ROOT)
    assert outputs["candidate_b_exact_text.txt"] == freeze.CANDIDATE_B_TEXT.encode("utf-8")
    assert hashlib.sha256(outputs["candidate_b_exact_text.txt"]).hexdigest() == freeze.EXPECTED_CANDIDATE_TEXT_SHA256
    spec = json.loads(outputs["paired_analysis_spec.json"])
    assert spec["candidate_b_format_gates"] == {
        "strict_python_only_min": 0.9,
        "code_fence_count_max": 0,
        "reasoning_leakage_count_max": 0,
        "undisclosed_prompt_contamination_count_max": 0,
    }
    assert spec["candidate_b_functional_gate"]["candidate_b_h0_pass_gt_p0_h0"] is True
    assert spec["candidate_b_functional_gate"]["paired_net_change_gt_0"] is True
    assert "H0_to_H1_rescue" in spec["healer_results_separate_from_candidate_b_prompt_gate"]
    assert freeze.R001_RUN_ID in spec["excluded_incident_runs"]
    assert freeze.R002_RUN_ID in spec["excluded_incident_runs"]


def test_zero_model_preflight_accepts_only_exact_manifest() -> None:
    receipt = runner.zero_model_preflight(
        manifest_path=GOV_DIR / "manifest.json",
        manifest_sha256=runner.FROZEN_MANIFEST_SHA256,
    )
    assert receipt["status"] == "zero_model_preflight_passed"
    assert receipt["model_calls"] == receipt["evalplus_executions"] == 0
    assert receipt["candidate_b_generation_cells"] == 300
    assert receipt["factorial_accounts"] == 1200
    assert receipt["validation_run_absent"] is True
    assert receipt["candidate_b_run_absent"] is True
    assert receipt["r001_incident"]["generation_journals"] == 0
    assert receipt["r002_incident"]["classification"] == "FIRST_CELL_JOURNAL_PERSISTENCE_FAILURE"
    assert receipt["r002_incident"]["model_call_status"] == "model_call_confirmed_1"
    assert receipt["r002_incident"]["generation_journals"] == 0
    with pytest.raises(runner.CandidateBRunError, match="SHA-256"):
        runner.zero_model_preflight(
            manifest_path=GOV_DIR / "manifest.json", manifest_sha256="0" * 64,
        )


def test_r001_empty_journal_incident_allows_r003_without_creating_it(
    tmp_path: Path,
) -> None:
    r001 = tmp_path / "r001"
    (r001 / "j").mkdir(parents=True)
    r003 = tmp_path / "r003"
    receipt = runner.validate_r001_zero_cell_incident(r001)
    runner.require_r003_absent(r003)
    assert receipt["classification"] == "ZERO_CELL_PREFLIGHT_INCIDENT"
    assert receipt["generation_journals"] == 0
    assert receipt["result_source"] is False
    assert not r003.exists()


def test_r002_persistence_incident_validation(tmp_path: Path) -> None:
    r002 = tmp_path / "r002"
    (r002 / "j").mkdir(parents=True)
    (r002 / "frozen_manifest.json").write_text("{}", encoding="utf-8")
    (r002 / "model_provenance.json").write_text("{}", encoding="utf-8")
    receipt = runner.validate_r002_first_cell_persistence_incident(r002)
    assert receipt["classification"] == "FIRST_CELL_JOURNAL_PERSISTENCE_FAILURE"
    assert receipt["model_call_status"] == "model_call_confirmed_1"
    assert receipt["generation_journals"] == 0
    assert receipt["eligible_for_analysis_or_reuse"] is False


def test_r003_existing_fails_closed(tmp_path: Path) -> None:
    r003 = tmp_path / "r003"
    r003.mkdir()
    with pytest.raises(runner.CandidateBRunError, match="r003 run directory exists"):
        runner.require_r003_absent(r003)


def test_r001_any_journal_requires_manual_review(tmp_path: Path) -> None:
    r001 = tmp_path / "r001"
    journal = r001 / "j" / "unexpected.json"
    journal.parent.mkdir(parents=True)
    journal.write_text("{}", encoding="utf-8")
    with pytest.raises(runner.CandidateBRunError, match="manual review required"):
        runner.validate_r001_zero_cell_incident(r001)


def test_r002_any_journal_requires_manual_review(tmp_path: Path) -> None:
    r002 = tmp_path / "r002"
    journal = r002 / "j" / "unexpected.json"
    journal.parent.mkdir(parents=True)
    journal.write_text("{}", encoding="utf-8")
    (r002 / "frozen_manifest.json").write_text("{}", encoding="utf-8")
    (r002 / "model_provenance.json").write_text("{}", encoding="utf-8")
    with pytest.raises(runner.CandidateBRunError, match="manual review required"):
        runner.validate_r002_first_cell_persistence_incident(r002)


def test_r001_and_r002_are_never_candidate_b_result_sources() -> None:
    outputs = freeze.build_outputs(REPO_ROOT)
    accounts = _csv_rows(outputs["development_2x2_accounts.csv"])
    candidate = [row for row in accounts if row["prompt_condition"] == "Candidate_B"]
    mapping = _csv_rows(outputs["r001_r002_r003_identity_mapping.csv"])
    assert len(candidate) == 600
    assert all(row["run_id"] == freeze.RUN_ID for row in candidate)
    assert all(row["run_id"] != freeze.R001_RUN_ID for row in candidate)
    assert all(row["run_id"] != freeze.R002_RUN_ID for row in candidate)
    assert all(row["r001_result_reused"] == "false" for row in mapping)
    assert all(row["r002_result_reused"] == "false" for row in mapping)
    assert all(row["r001_response_available"] == "false" for row in mapping)
    assert all(row["r002_response_available"] == "false" for row in mapping)


def test_r003_preserves_prompt_healer_pipeline_model_and_research_identities() -> None:
    outputs = freeze.build_outputs(REPO_ROOT)
    manifest = json.loads(outputs["manifest.json"])
    cells = _csv_rows(outputs["candidate_b_generation_cells.csv"])
    assert manifest["candidate_b"]["exact_text_sha256"] == freeze.EXPECTED_CANDIDATE_TEXT_SHA256
    assert manifest["healer_sha256"] == freeze.EXPECTED_HEALER_SHA256
    assert manifest["pipeline_sha256"] == freeze.EXPECTED_PIPELINE_SHA256
    assert manifest["model_digest"] == freeze.EXPECTED_MODEL_DIGEST
    assert manifest["quantization"] == "Q4_K_M"
    assert manifest["generation_parameters"]["thinking"] is False
    assert manifest["seeds"] == [11, 22, 33, 44, 55]
    assert len(cells) == len({(row["task_id"], row["seed"]) for row in cells}) == 300


def test_quantization_extraction_accepts_api_show_shape() -> None:
    payload = {
        "format": "gguf",
        "details": {
            "family": "qwen35", "parameter_size": "9.7B",
            "quantization_level": "Q4_K_M",
        },
    }
    assert ollama.extract_ollama_quantization(payload) == "Q4_K_M"


def test_quantization_extraction_accepts_api_tags_shape() -> None:
    payload = {
        "models": [{
            "name": freeze.EXPECTED_MODEL,
            "digest": freeze.EXPECTED_MODEL_DIGEST,
            "details": {"quantization_level": "Q4_K_M"},
        }]
    }
    assert ollama.extract_ollama_quantization(
        payload, model=freeze.EXPECTED_MODEL,
    ) == "Q4_K_M"


def test_provenance_fetch_reads_api_tags_details_quantization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tags = {
        "models": [{
            "name": freeze.EXPECTED_MODEL,
            "digest": freeze.EXPECTED_MODEL_DIGEST,
            "details": {"quantization_level": "Q4_K_M"},
        }]
    }

    def fake_get(url: str, timeout_seconds: float, *, stage: str) -> dict[str, object]:
        return {"version": "0.32.0"} if url.endswith("/api/version") else tags

    monkeypatch.setattr(ollama, "_http_get_json", fake_get)
    provenance = ollama.fetch_ollama_provenance(
        "http://127.0.0.1:11434", 300.0,
        model=freeze.EXPECTED_MODEL,
        expected_digest_prefix=freeze.EXPECTED_MODEL_DIGEST,
    )
    assert provenance["quantization_api_value"] == "Q4_K_M"
    assert provenance["quantization"] == "Q4_K_M"
    assert provenance["quantization_api_source"] == (
        "/api/tags models[].details.quantization_level"
    )


def test_installed_model_identity_accepts_only_exact_normalized_quantization() -> None:
    receipt = runner.validate_installed_model_provenance({
        "model_digest": freeze.EXPECTED_MODEL_DIGEST,
        "quantization_api_value": " q4_k_m ",
    })
    assert receipt["digest_type"] == "str"
    assert receipt["quantization_raw_type"] == "str"
    assert receipt["quantization_normalized_value"] == "Q4_K_M"


def test_installed_model_identity_rejects_different_quantization() -> None:
    with pytest.raises(runner.CandidateBRunError, match="quantization drift"):
        runner.validate_installed_model_provenance({
            "model_digest": freeze.EXPECTED_MODEL_DIGEST,
            "quantization_api_value": "Q8_0",
        })


def test_installed_model_identity_rejects_missing_quantization() -> None:
    with pytest.raises(runner.CandidateBRunError, match="quantization missing"):
        runner.validate_installed_model_provenance({
            "model_digest": freeze.EXPECTED_MODEL_DIGEST,
        })


def test_installed_model_identity_rejects_digest_drift() -> None:
    with pytest.raises(runner.CandidateBRunError, match="digest drift"):
        runner.validate_installed_model_provenance({
            "model_digest": "0" * 64,
            "quantization_api_value": "Q4_K_M",
        })


def test_existing_p0_duplicate_or_missing_identity_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = freeze._read_csv

    def duplicate(path: Path) -> list[dict[str, str]]:
        rows = original(path)
        if Path(path) == REPO_ROOT / freeze.PAIRED_CELLS_RELATIVE:
            p0 = next(row for row in rows if row["prompt_condition"] == "p0")
            rows = rows + [dict(p0)]
        return rows

    monkeypatch.setattr(freeze, "_read_csv", duplicate)
    with pytest.raises(freeze.CandidateBFreezeError, match="count must be 300"):
        freeze.load_existing_p0(REPO_ROOT)

    def missing(path: Path) -> list[dict[str, str]]:
        rows = original(path)
        if Path(path) == REPO_ROOT / freeze.EXISTING_ACCOUNTS_RELATIVE:
            removed = False
            kept = []
            for row in rows:
                if row["prompt_condition"] == "p0" and not removed:
                    removed = True
                    continue
                kept.append(row)
            return kept
        return rows

    monkeypatch.setattr(freeze, "_read_csv", missing)
    with pytest.raises(freeze.CandidateBFreezeError, match="count must be 600"):
        freeze.load_existing_p0(REPO_ROOT)


def _fake_success(task: object, **kwargs: object) -> dict[str, object]:
    settings = kwargs["settings"]
    source = f"def {task.entry_point}(*args):\n    return None\n"
    request = {
        "model": freeze.EXPECTED_MODEL, "stream": False, "think": False,
        "messages": [{"role": "user", "content": task.prompt}],
        "options": {
            "num_ctx": settings.context_window, "num_predict": settings.num_predict,
            "seed": settings.seed, "temperature": settings.temperature,
            "top_k": settings.top_k, "top_p": settings.top_p,
        },
    }
    body = {
        "model": freeze.EXPECTED_MODEL, "created_at": "synthetic", "done": True,
        "done_reason": "stop", "total_duration": 1, "load_duration": 1,
        "prompt_eval_count": 1, "prompt_eval_duration": 1,
        "eval_count": 1, "eval_duration": 1, "message": {"content": source},
    }
    return {
        "raw_response": source, "generation_latency": 0.0,
        "ollama_response_metadata": {
            "raw_body": json.dumps(body), "request_payload": request,
        },
    }


def _patch_generation(
    monkeypatch: pytest.MonkeyPatch, run_dir: Path, attempt: object,
) -> None:
    monkeypatch.setattr(runner, "zero_model_preflight", lambda **kwargs: {"status": "ok"})
    monkeypatch.setattr(runner, "fetch_ollama_provenance", lambda *args, **kwargs: {
        "model_digest": freeze.EXPECTED_MODEL_DIGEST,
        "quantization": freeze.EXPECTED_QUANTIZATION,
        "quantization_api_value": freeze.EXPECTED_QUANTIZATION,
    })
    monkeypatch.setattr(runner, "run_attempt", attempt)
    monkeypatch.setattr(freeze, "RUN_OUTPUT_RELATIVE", run_dir)


def test_synthetic_generation_persists_300_journals_and_600_accounts(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    run_dir = tmp_path / "complete"
    _patch_generation(
        monkeypatch, run_dir,
        lambda task, treatment, **kwargs: _fake_success(task, **kwargs),
    )
    runner.generate(
        manifest_path=GOV_DIR / "manifest.json",
        manifest_sha256=runner.FROZEN_MANIFEST_SHA256,
    )
    assert len(list((run_dir / "j").glob("*.json"))) == 300
    raw = [json.loads(line) for line in (run_dir / "raw_generations.jsonl").read_text(encoding="utf-8").splitlines()]
    accounts = [json.loads(line) for line in (run_dir / "h0_h1_accounts.jsonl").read_text(encoding="utf-8").splitlines()]
    materialization = json.loads((run_dir / "materialization_manifest.json").read_text(encoding="utf-8"))
    assert len(raw) == 300
    assert len(accounts) == len({row["evaluation_account_id"] for row in accounts}) == 600
    assert materialization["factorial_programs_after_p0_reuse"] == 600
    assert materialization["factorial_accounts_after_p0_reuse"] == 1200
    assert materialization["retry_count"] == 0
    assert materialization["evalplus_executions"] == 0


def test_one_failed_cell_keeps_all_journals_and_forbids_aggregate(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    run_dir = tmp_path / "incomplete"
    calls = 0

    def one_failure(task: object, treatment: str, **kwargs: object) -> dict[str, object]:
        nonlocal calls
        calls += 1
        return {} if calls == 1 else _fake_success(task, **kwargs)

    _patch_generation(monkeypatch, run_dir, one_failure)
    with pytest.raises(runner.CandidateBRunError, match="resume/retry forbidden"):
        runner.generate(
            manifest_path=GOV_DIR / "manifest.json",
            manifest_sha256=runner.FROZEN_MANIFEST_SHA256,
        )
    assert calls == 300
    assert len(list((run_dir / "j").glob("*.json"))) == 300
    assert not (run_dir / "raw_generations.jsonl").exists()
    assert not (run_dir / "pipeline_normalized.jsonl").exists()
    assert not (run_dir / "h0_h1_accounts.jsonl").exists()


def test_runner_has_no_evalplus_resume_retry_or_overwrite_path() -> None:
    source = (REPO_ROOT / "scripts/run_mbpp_candidate_b_development60_replay.py").read_text(encoding="utf-8")
    assert "from evalplus" not in source
    assert "import evalplus" not in source
    assert "commands.add_parser(\"evaluate\")" not in source
    assert "commands.add_parser(\"resume\")" not in source
    assert "commands.add_parser(\"retry\")" not in source
    assert "commands.add_parser(\"overwrite\")" not in source


def test_r003_run_and_validation_directories_remain_absent() -> None:
    assert not (REPO_ROOT / freeze.RUN_OUTPUT_RELATIVE).exists()
    assert not (REPO_ROOT / freeze.VALIDATION_RUN_RELATIVE).exists()
