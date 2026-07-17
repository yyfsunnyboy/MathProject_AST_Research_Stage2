from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

from scripts import freeze_mbpp_scaffold_v0_protocol as frozen
from scripts import recover_mbpp_scaffold_v0_run_002 as recovery
from scripts import run_mbpp_scaffold_v0_development as driver


REPO_ROOT = Path(__file__).resolve().parents[2]


def _cell(index: int) -> dict:
    prompt = f"synthetic prompt {index}"
    return {
        "cell_index": index,
        "task_id": f"Synthetic/{index}",
        "seed": index,
        "sample_index": 0,
        "generation_id": f"{index:064x}",
        "official_prompt_sha256": frozen.sha256_text(prompt),
        "composed_prompt_sha256": frozen.sha256_text(prompt),
    }


def _attempt(cell: dict, raw: str, *, done: bool, leakage: bool) -> dict:
    body = {
        "model": frozen.MODEL,
        "created_at": "synthetic",
        "message": {"role": "assistant", "content": raw},
        "done": done,
        "done_reason": "stop" if done else None,
        "total_duration": 1,
        "load_duration": 1,
        "prompt_eval_count": 1,
        "prompt_eval_duration": 1,
        "eval_count": 1,
        "eval_duration": 1,
    }
    return {
        "status": "failed" if leakage else "success",
        "failure_stage": "response_validation" if leakage else None,
        "failure_reason": (
            "response contains reasoning leakage; refusing to discard it and proceed"
            if leakage
            else None
        ),
        "reasoning_leakage_detected": leakage,
        "raw_response": raw,
        "raw_response_sha256": frozen.sha256_text(raw),
        "generation_latency": 0.1,
        "ollama_response_metadata": {
            "http_status": 200,
            "api_endpoint": "/api/chat",
            "request_payload": {
                "model": frozen.MODEL,
                "messages": [
                    {"role": "user", "content": f"synthetic prompt {cell['cell_index']}"}
                ],
                "think": False,
            },
            "raw_body": json.dumps(body, sort_keys=True),
        },
    }


def test_http_200_done_reasoning_leak_is_complete_but_noncompliant_and_verbatim():
    cell = _cell(1)
    raw = "<think>internal text</think>\ndef requested():\n    return 1\n"
    record = driver._raw_record_from_complete_attempt(
        cell=cell,
        attempt=_attempt(cell, raw, done=True, leakage=True),
        recovered_from_existing_response=True,
    )

    assert record is not None
    assert record["transport_complete"] is True
    assert record["generation_complete"] is True
    assert record["model_generation_complete"] is True
    assert record["protocol_compliant"] is False
    assert record["protocol_violations"] == [
        "reasoning_leakage_in_message_content"
    ]
    assert record["raw_response"] == raw
    assert "<think>internal text</think>" in record["raw_response"]
    assert record["raw_response_sha256"] == frozen.sha256_text(raw)
    assert record["retry_count"] == 0
    assert record["regeneration"] is False
    assert record["recovered_from_existing_response"] is True


def test_saved_response_sha_mismatch_fails_closed():
    cell = _cell(1)
    attempt = _attempt(cell, "def requested():\n    return 1\n", done=True, leakage=False)
    attempt["raw_response_sha256"] = "0" * 64

    with pytest.raises(driver.ScaffoldRunError, match="SHA-256 mismatch"):
        driver._raw_record_from_complete_attempt(
            cell=cell,
            attempt=attempt,
            recovered_from_existing_response=True,
        )


def test_partial_done_false_response_is_not_recoverable_as_complete():
    cell = _cell(1)
    raw = "def requested():\n"
    record = driver._raw_record_from_complete_attempt(
        cell=cell,
        attempt=_attempt(cell, raw, done=False, leakage=False),
        recovered_from_existing_response=True,
    )

    assert record is None


def test_synthetic_100_cell_aggregation_preserves_one_violation(tmp_path):
    journal_dir = tmp_path / "j"
    journal_dir.mkdir()
    cells = [_cell(index) for index in range(1, 101)]
    recovered_cell = cells[62]
    recovered_raw = "<think>do not strip</think>\ndef requested():\n    return 63\n"
    recovered_journal_path = journal_dir / f"{recovered_cell['generation_id']}.json"
    for cell in cells:
        raw = f"def requested():\n    return {cell['cell_index']}\n"
        attempt = _attempt(cell, raw, done=True, leakage=False)
        if cell == recovered_cell:
            attempt = _attempt(cell, recovered_raw, done=True, leakage=True)
            journal = {
                "generation_id": cell["generation_id"],
                "cell_index": cell["cell_index"],
                "task_id": cell["task_id"],
                "seed": cell["seed"],
                "sample_index": cell["sample_index"],
                "status": "failed_single_attempt_no_retry",
                "attempt": attempt,
            }
        else:
            journal = driver._raw_record_from_complete_attempt(
                cell=cell,
                attempt=attempt,
                recovered_from_existing_response=False,
            )
        (journal_dir / f"{cell['generation_id']}.json").write_text(
            json.dumps(journal, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    recovered_journal_sha = hashlib.sha256(recovered_journal_path.read_bytes()).hexdigest()
    records, sources = recovery.aggregate_existing_journals(
        plan={"cells": cells},
        journal_dir=journal_dir,
        recovered_generation_id=recovered_cell["generation_id"],
        expected_recovered_journal_sha256=recovered_journal_sha,
        expected_recovered_response_sha256=frozen.sha256_text(recovered_raw),
    )

    assert len(records) == len(sources) == 100
    assert [record["generation_id"] for record in records] == [
        cell["generation_id"] for cell in cells
    ]
    recovered = records[62]
    assert recovered["raw_response"] == recovered_raw
    assert recovered["protocol_compliant"] is False
    assert sum(record["recovered_from_existing_response"] for record in records) == 1
    assert all(record["retry_count"] == 0 for record in records)


def test_actual_recovery_build_is_deterministic_and_preserves_source_hashes():
    run_dir = REPO_ROOT / frozen.PHYSICAL_RUN_RELATIVE
    first = recovery.build_outputs(run_dir)
    second = recovery.build_outputs(run_dir)
    raw_records, pipeline_records, manifest = first

    assert recovery.jsonl_bytes(raw_records) == recovery.jsonl_bytes(second[0])
    assert recovery.jsonl_bytes(pipeline_records) == recovery.jsonl_bytes(second[1])
    assert manifest == second[2]
    assert (run_dir / "raw_generations.jsonl").read_bytes() == recovery.jsonl_bytes(
        raw_records
    )
    assert (run_dir / "pipeline_corrected.jsonl").read_bytes() == recovery.jsonl_bytes(
        pipeline_records
    )
    assert json.loads(
        (run_dir / recovery.MANIFEST_NAME).read_text(encoding="utf-8")
    ) == manifest
    assert len(raw_records) == len(pipeline_records) == 100
    assert manifest["reasoning_leakage_count"] == 1
    assert manifest["protocol_compliant_count"] == 99
    assert manifest["protocol_violation_count"] == 1
    assert manifest["retry_count"] == 0
    assert manifest["regeneration"] is False
    recovered = manifest["recovered_cell"]
    assert recovered["generation_id"] == recovery.RECOVERED_GENERATION_ID
    assert recovered["raw_response_sha256"] == recovery.RECOVERED_RESPONSE_SHA256
    assert recovered["protocol_compliant"] is False
    failed_path = run_dir / "j" / f"{recovery.RECOVERED_GENERATION_ID}.json"
    assert hashlib.sha256(failed_path.read_bytes()).hexdigest() == (
        recovery.RECOVERED_JOURNAL_SHA256
    )
    assert all(
        record["pipeline_correction_spec"]
        == "agent_tools.finals_rebuild.extraction.extract_code"
        for record in pipeline_records
    )
    recovered_raw = next(
        record
        for record in raw_records
        if record["generation_id"] == recovery.RECOVERED_GENERATION_ID
    )
    recovered_pipeline = next(
        record
        for record in pipeline_records
        if record["generation_id"] == recovery.RECOVERED_GENERATION_ID
    )
    assert recovered_pipeline["changed_from_observed"] is False
    assert recovered_pipeline["pipeline_corrected_output"] == recovered_raw["raw_response"]
    assert re.search(r"</?think>", recovered_raw["raw_response"], re.IGNORECASE)
    for source in manifest["source_journals"]:
        source_path = run_dir / source["path"]
        assert hashlib.sha256(source_path.read_bytes()).hexdigest() == source["sha256"]
