#!/usr/bin/env python3
"""Recover complete first-attempt run_002 responses into ITT account artifacts.

This builder is journal-only: it never calls a model or evaluator, never mutates a
source journal, and never strips protocol-violating response text.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_tools.finals_rebuild.generation_persistence import (
    durable_write_json_new,
    durable_write_jsonl_new,
)
from agent_tools.finals_rebuild.ollama_generation_runner import (
    detect_reasoning_leakage,
)
from scripts import freeze_mbpp_scaffold_v0_protocol as frozen
from scripts import run_mbpp_development_baseline as p0_driver
from scripts import run_mbpp_scaffold_v0_development as driver

RUN_ID = "mbpp_qwen35_9b_scaffold_v0_dev_run_002"
RECOVERED_GENERATION_ID = (
    "d29cc128d90b26af673792782106cfb1b0b39182a0302f8bcee949d406f5ec98"
)
RECOVERED_JOURNAL_SHA256 = (
    "e074e562fc7a683b8f869fbafba9aacf48e00ff327399909c4ee43fee847ac35"
)
RECOVERED_RESPONSE_SHA256 = (
    "2c34cf6d6cff4e3dfc6648fc3c742bc53574d04280cce0b37a3ab6526f595ba8"
)
MANIFEST_NAME = "first_attempt_recovery_manifest.json"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def jsonl_bytes(records: list[dict[str, Any]]) -> bytes:
    return "".join(
        json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n"
        for record in records
    ).encode("utf-8")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise driver.ScaffoldRunError(message)


def _normalize_saved_complete_record(
    cell: dict[str, Any], record: dict[str, Any]
) -> dict[str, Any]:
    """Verify and annotate an already-complete raw journal record."""
    _require(record.get("generation_id") == cell["generation_id"], "journal identity mismatch")
    _require(record.get("task_id") == cell["task_id"], "journal task mismatch")
    _require(record.get("seed") == cell["seed"], "journal seed mismatch")
    raw_response = record.get("raw_response")
    _require(isinstance(raw_response, str) and bool(raw_response.strip()), "saved response missing")
    _require(
        record.get("raw_response_sha256") == frozen.sha256_text(raw_response),
        "saved raw response SHA-256 mismatch",
    )
    raw_body = record.get("raw_http_response_body")
    _require(isinstance(raw_body, str), "saved raw HTTP body missing")
    try:
        body = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise driver.ScaffoldRunError("saved raw HTTP body is invalid JSON") from exc
    message = body.get("message") if isinstance(body.get("message"), dict) else {}
    _require(body.get("done") is True, "partial response cannot be aggregated as complete")
    _require(message.get("content") == raw_response, "HTTP body/response byte mismatch")
    request = record.get("request")
    _require(isinstance(request, dict) and request.get("think") is False, "request identity drift")
    messages = request.get("messages")
    _require(
        isinstance(messages, list)
        and len(messages) == 1
        and frozen.sha256_text(messages[0].get("content", ""))
        == cell["composed_prompt_sha256"],
        "saved composed prompt SHA-256 mismatch",
    )
    _require(
        not detect_reasoning_leakage(body, raw_response),
        "unrecorded reasoning leakage in nominally complete journal",
    )
    normalized = dict(record)
    normalized.update(
        {
            "transport_complete": True,
            "model_generation_complete": True,
            "generation_complete": True,
            "protocol_compliant": True,
            "protocol_violations": [],
            "first_attempt": True,
            "source_attempt_status": "success",
            "source_failure_stage": None,
            "recovered_from_existing_response": False,
            "regeneration": False,
        }
    )
    return normalized


def aggregate_existing_journals(
    *,
    plan: dict[str, Any],
    journal_dir: Path,
    recovered_generation_id: str,
    expected_recovered_journal_sha256: str,
    expected_recovered_response_sha256: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Build plan-ordered raw records without altering any journal."""
    cells = plan.get("cells")
    _require(isinstance(cells, list) and len(cells) == 100, "recovery requires 100 planned cells")
    expected_names = {f"{cell['generation_id']}.json" for cell in cells}
    files = sorted(journal_dir.glob("*.json"), key=lambda path: path.name)
    _require(len(files) == 100, "recovery requires exactly 100 journal files")
    _require({path.name for path in files} == expected_names, "journal/planned identity mismatch")
    by_name = {path.name: path for path in files}
    raw_records: list[dict[str, Any]] = []
    source_journals: list[dict[str, Any]] = []
    recovered_count = 0
    for cell in cells:
        path = by_name[f"{cell['generation_id']}.json"]
        journal_bytes = path.read_bytes()
        journal_sha256 = sha256_bytes(journal_bytes)
        source_journals.append(
            {
                "generation_id": cell["generation_id"],
                "path": f"j/{path.name}",
                "sha256": journal_sha256,
                "size_bytes": len(journal_bytes),
            }
        )
        record = json.loads(journal_bytes)
        if record.get("status") == "failed_single_attempt_no_retry":
            _require(
                cell["generation_id"] == recovered_generation_id,
                "unexpected failed journal is not recoverable by this decision",
            )
            _require(
                journal_sha256 == expected_recovered_journal_sha256,
                "recovered journal SHA-256 mismatch",
            )
            attempt = record.get("attempt")
            _require(isinstance(attempt, dict), "failed journal attempt missing")
            raw_record = driver._raw_record_from_complete_attempt(
                cell=cell,
                attempt=attempt,
                recovered_from_existing_response=True,
            )
            _require(raw_record is not None, "failed journal does not contain a complete response")
            _require(
                raw_record["raw_response_sha256"] == expected_recovered_response_sha256,
                "recovered response SHA-256 mismatch",
            )
            _require(raw_record["protocol_compliant"] is False, "recovered violation marked compliant")
            _require(
                raw_record["protocol_violations"]
                == ["reasoning_leakage_in_message_content"],
                "recovered violation classification drift",
            )
            recovered_count += 1
        else:
            raw_record = _normalize_saved_complete_record(cell, record)
        raw_records.append(raw_record)
    _require(recovered_count == 1, "expected exactly one recovered first-attempt response")
    _require(
        [record["generation_id"] for record in raw_records]
        == [cell["generation_id"] for cell in cells],
        "aggregated raw record order/identity drift",
    )
    return raw_records, source_journals


def build_outputs(run_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    plan_path = run_dir / "generation_plan.json"
    _require(plan_path.read_bytes() == (REPO_ROOT / frozen.PLAN_RELATIVE).read_bytes(), "run plan drift")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    _require(plan.get("run_id") == RUN_ID == frozen.RUN_ID, "run ID mismatch")
    raw_records, source_journals = aggregate_existing_journals(
        plan=plan,
        journal_dir=run_dir / "j",
        recovered_generation_id=RECOVERED_GENERATION_ID,
        expected_recovered_journal_sha256=RECOVERED_JOURNAL_SHA256,
        expected_recovered_response_sha256=RECOVERED_RESPONSE_SHA256,
    )
    pipeline_records: list[dict[str, Any]] = []
    for raw_record in raw_records:
        pipeline_record = p0_driver.build_pipeline_record(raw_record)
        pipeline_record["run_id"] = RUN_ID
        pipeline_record["logical_run_id"] = RUN_ID
        pipeline_records.append(pipeline_record)
    raw_material = jsonl_bytes(raw_records)
    pipeline_material = jsonl_bytes(pipeline_records)
    recovered = next(
        record for record in raw_records if record["generation_id"] == RECOVERED_GENERATION_ID
    )
    recovered_pipeline = next(
        record
        for record in pipeline_records
        if record["generation_id"] == RECOVERED_GENERATION_ID
    )
    manifest = {
        "decision_version": "mbpp_scaffold_v0_first_attempt_itt_recovery_v1",
        "logical_run_id": RUN_ID,
        "physical_run_directory": frozen.PHYSICAL_RUN_RELATIVE.as_posix(),
        "decision": "RECOVER_EXISTING_RESPONSE",
        "scope": "existing first-attempt response only; no generation or evaluation",
        "planned_cells": 100,
        "aggregated_raw_cells": len(raw_records),
        "aggregated_pipeline_cells": len(pipeline_records),
        "reasoning_leakage_count": sum(
            "reasoning_leakage_in_message_content" in record["protocol_violations"]
            for record in raw_records
        ),
        "protocol_compliant_count": sum(record["protocol_compliant"] for record in raw_records),
        "protocol_violation_count": sum(not record["protocol_compliant"] for record in raw_records),
        "retry_count": 0,
        "regeneration": False,
        "healer": False,
        "pipeline_rescue": False,
        "evaluator_used": False,
        "source_journals_immutable": True,
        "source_journals": source_journals,
        "recovered_cell": {
            "task_id": recovered["task_id"],
            "seed": recovered["seed"],
            "generation_id": recovered["generation_id"],
            "transport_complete": recovered["transport_complete"],
            "model_generation_complete": recovered["model_generation_complete"],
            "generation_complete": recovered["generation_complete"],
            "protocol_compliant": recovered["protocol_compliant"],
            "violation": recovered["protocol_violations"][0],
            "raw_response_sha256": recovered["raw_response_sha256"],
            "retry_count": recovered["retry_count"],
            "regeneration": recovered["regeneration"],
            "recovered_from_existing_response": recovered[
                "recovered_from_existing_response"
            ],
            "observed_uses_original_response": True,
            "pipeline_extraction_status": recovered_pipeline["extraction_status"],
            "pipeline_extraction_method": recovered_pipeline["extraction_method"],
            "pipeline_rule_changed_for_incident": False,
        },
        "outputs": {
            "raw_generations.jsonl": {
                "sha256": sha256_bytes(raw_material),
                "record_count": len(raw_records),
            },
            "pipeline_corrected.jsonl": {
                "sha256": sha256_bytes(pipeline_material),
                "record_count": len(pipeline_records),
            },
        },
    }
    return raw_records, pipeline_records, manifest


def recover(run_dir: Path) -> None:
    for name in ("raw_generations.jsonl", "pipeline_corrected.jsonl", MANIFEST_NAME):
        _require(not (run_dir / name).exists(), f"refusing to overwrite existing recovery output: {name}")
    raw_records, pipeline_records, manifest = build_outputs(run_dir)
    durable_write_jsonl_new(run_dir / "raw_generations.jsonl", raw_records)
    durable_write_jsonl_new(run_dir / "pipeline_corrected.jsonl", pipeline_records)
    durable_write_json_new(run_dir / MANIFEST_NAME, manifest)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    _require(args.run_id == RUN_ID, f"only {RUN_ID} is allowed")
    run_dir = REPO_ROOT / frozen.PHYSICAL_RUN_RELATIVE
    recover(run_dir)
    print(
        json.dumps(
            {
                "status": "first_attempt_response_recovered_without_regeneration",
                "run_id": RUN_ID,
                "raw_cells": 100,
                "retry_count": 0,
                "evaluator_used": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
