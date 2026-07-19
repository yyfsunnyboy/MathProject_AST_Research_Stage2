#!/usr/bin/env python3
"""Fail-closed runner for frozen MBPP+ validation P0 x Healer-v0.

The runner has no EvalPlus path.  H1 is materialized from the same frozen
Pipeline-normalized program as H0 and never causes another model call.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_tools.finals_rebuild.benchmarks_adapter import PublicBenchmarkTask  # noqa: E402
from agent_tools.finals_rebuild.extraction import extract_code  # noqa: E402
from agent_tools.finals_rebuild.generation_persistence import (  # noqa: E402
    PersistenceError,
    durable_write_json_new,
    durable_write_jsonl_new,
    durable_write_text_new,
)
from agent_tools.finals_rebuild.mbpp_evaluator_blind_healer import apply_healer  # noqa: E402
from agent_tools.finals_rebuild.ollama_generation_runner import (  # noqa: E402
    DEFAULT_BASE_URL,
    fetch_ollama_provenance,
    load_generation_protocol,
    protocol_settings,
    run_attempt,
)
from scripts import freeze_mbpp_healer_v0_validation_p0 as frozen  # noqa: E402


FROZEN_MANIFEST_RELATIVE = frozen.OUTPUT_RELATIVE / "manifest.json"
FROZEN_MANIFEST_SHA256 = "f32d67f62f1af9de5f07db489700f940edd7bf1e348f90275a4d9177a6b53fb0"
TIMEOUT_SECONDS = 300.0


class ValidationRunError(RuntimeError):
    """Raised on any immutable input, persistence, or generation drift."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationRunError(message)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def zero_model_preflight(
    *, manifest_path: Path, manifest_sha256: str,
    require_output_absent: bool = True,
) -> dict[str, Any]:
    expected_manifest_path = (REPO_ROOT / FROZEN_MANIFEST_RELATIVE).resolve()
    _require(manifest_path.resolve() == expected_manifest_path, "only the frozen validation manifest path is accepted")
    _require(manifest_sha256 == FROZEN_MANIFEST_SHA256, "manifest SHA-256 argument is not frozen")
    manifest_bytes = manifest_path.read_bytes()
    _require(_sha256_bytes(manifest_bytes) == FROZEN_MANIFEST_SHA256, "frozen validation manifest bytes drift")
    manifest = json.loads(manifest_bytes)
    _require(manifest["status"] == "prepared_not_executed", "manifest status drift")
    _require(manifest["run_id"] == frozen.RUN_ID, "run ID drift")
    _require(manifest["run_output_relative"] == frozen.RUN_OUTPUT_RELATIVE.as_posix(), "run output binding drift")
    _require(manifest["dataset_version"] == frozen.EXPECTED_DATASET_VERSION, "dataset version drift")
    _require(manifest["dataset_hash"] == frozen.EXPECTED_DATASET_HASH, "dataset hash drift")
    _require(manifest["validation_task_count"] == 20, "validation task count drift")
    _require(manifest["generation_cells"] == 100, "generation cell count drift")
    _require(manifest["evaluation_accounts"] == 200, "evaluation account count drift")
    _require(manifest["model"] == frozen.EXPECTED_MODEL, "model tag drift")
    _require(manifest["model_digest"] == frozen.EXPECTED_MODEL_DIGEST, "model digest drift")
    _require(manifest["quantization"] == frozen.EXPECTED_QUANTIZATION, "quantization drift")
    _require(manifest["generation_parameters"] == frozen.EXPECTED_GENERATION_OPTIONS, "generation settings drift")
    _require(manifest["pipeline_sha256"] == frozen.EXPECTED_PIPELINE_SHA256, "Pipeline hash drift")
    _require(manifest["healer_sha256"] == frozen.EXPECTED_HEALER_SHA256, "Healer hash drift")
    _require(manifest["healer_rule_order"] == [frozen.EXPECTED_RULE_ID], "Healer rule/version drift")
    _require(manifest["scaffold"] is False and manifest["h1_regeneration"] is False, "P0/H1 design drift")
    isolation = manifest["identity_isolation"]
    _require(isolation["validation_development_intersection"] == 0, "validation/development overlap")
    _require(isolation["individually_reviewed"] == 0, "validation individual review detected")
    _require(isolation["rule_development_sources"] == 0, "validation rule-development exposure detected")
    _require(isolation["failure_census_sources"] == 0, "validation failure-census exposure detected")

    for relative, digest in manifest["source_sha256"].items():
        path = REPO_ROOT / relative
        _require(path.is_file(), f"frozen source missing: {relative}")
        _require(_sha256_bytes(path.read_bytes()) == digest, f"frozen source hash drift: {relative}")

    expected_outputs = frozen.build_outputs(REPO_ROOT)
    _require(expected_outputs["manifest.json"] == manifest_bytes, "mechanically rebuilt validation manifest drift")
    locked = manifest["output_sha256_excluding_manifest_and_operator_guide"]
    expected_lock_names = {
        "generation_cells.csv", "evaluation_accounts.csv",
        "execution_spec.json", "zero_model_preflight.json",
    }
    _require(set(locked) == expected_lock_names, "frozen asset lock set drift")
    for name, digest in locked.items():
        path = manifest_path.parent / name
        _require(path.is_file(), f"frozen validation asset missing: {name}")
        _require(_sha256_bytes(path.read_bytes()) == digest, f"frozen validation asset hash drift: {name}")
        _require(path.read_bytes() == expected_outputs[name], f"frozen validation asset deterministic drift: {name}")

    cells = _read_csv(manifest_path.parent / "generation_cells.csv")
    accounts = _read_csv(manifest_path.parent / "evaluation_accounts.csv")
    _require(len(cells) == len({row["generation_id"] for row in cells}) == 100, "100 generation identities incomplete or duplicate")
    _require(len({(row["task_id"], row["seed"]) for row in cells}) == 100, "task-seed generation identity drift")
    _require(len({row["task_id"] for row in cells}) == 20, "validation task identity count drift")
    _require(len(accounts) == len({row["evaluation_account_id"] for row in accounts}) == 200, "200 evaluation accounts incomplete or duplicate")
    _require(sum(row["healer_account"] == "H0" for row in accounts) == 100, "H0 account count drift")
    _require(sum(row["healer_account"] == "H1" for row in accounts) == 100, "H1 account count drift")
    _require({row["generation_id"] for row in accounts} == {row["generation_id"] for row in cells}, "generation/evaluation identity mismatch")

    run_dir = REPO_ROOT / frozen.RUN_OUTPUT_RELATIVE
    if require_output_absent:
        _require(not run_dir.exists(), "frozen run directory exists; resume/retry/overwrite forbidden")
    return {
        "status": "zero_model_preflight_passed",
        "manifest_sha256": FROZEN_MANIFEST_SHA256,
        "validation_tasks": 20,
        "generation_cells": 100,
        "evaluation_accounts": 200,
        "model_calls": 0,
        "evalplus_executions": 0,
        "run_output_absent": not run_dir.exists(),
    }


def _generation_metadata(attempt: dict[str, Any]) -> dict[str, Any]:
    transport = attempt.get("ollama_response_metadata")
    _require(isinstance(transport, dict), "generation transport metadata missing")
    raw_body = transport.get("raw_body")
    _require(isinstance(raw_body, str), "raw HTTP response body missing")
    parsed = json.loads(raw_body)
    fields = (
        "model", "created_at", "done", "done_reason", "total_duration",
        "load_duration", "prompt_eval_count", "prompt_eval_duration",
        "eval_count", "eval_duration",
    )
    _require(all(field in parsed for field in fields), "generation metadata field missing")
    _require(parsed["done"] is True, "generation transport did not finish")
    return {field: parsed[field] for field in fields}


def _complete_raw_record(
    *, cell: dict[str, str], task: dict[str, Any], attempt: dict[str, Any],
) -> dict[str, Any] | None:
    raw_response = attempt.get("raw_response")
    transport = attempt.get("ollama_response_metadata")
    if not isinstance(raw_response, str) or not raw_response.strip() or not isinstance(transport, dict):
        return None
    request = transport.get("request_payload")
    if not isinstance(request, dict):
        return None
    expected_options = {
        "num_ctx": frozen.EXPECTED_GENERATION_OPTIONS["num_ctx"],
        "num_predict": frozen.EXPECTED_GENERATION_OPTIONS["num_predict"],
        "seed": int(cell["seed"]),
        "temperature": frozen.EXPECTED_GENERATION_OPTIONS["temperature"],
        "top_k": frozen.EXPECTED_GENERATION_OPTIONS["top_k"],
        "top_p": frozen.EXPECTED_GENERATION_OPTIONS["top_p"],
    }
    if (
        request.get("model") != frozen.EXPECTED_MODEL
        or request.get("stream") is not False
        or request.get("think") is not False
        or request.get("options") != expected_options
        or request.get("messages") != [{"role": "user", "content": task["prompt"]}]
    ):
        return None
    try:
        metadata = _generation_metadata(attempt)
        parsed_body = json.loads(transport["raw_body"])
    except (ValidationRunError, json.JSONDecodeError):
        return None
    message = parsed_body.get("message")
    if not isinstance(message, dict) or message.get("content") != raw_response:
        return None
    return {
        "run_id": frozen.RUN_ID,
        "cell_index": int(cell["cell_index"]),
        "task_id": cell["task_id"],
        "seed": int(cell["seed"]),
        "sample_index": int(cell["sample_index"]),
        "generation_id": cell["generation_id"],
        "program_id": cell["program_id"],
        "model": frozen.EXPECTED_MODEL,
        "model_digest": frozen.EXPECTED_MODEL_DIGEST,
        "quantization": frozen.EXPECTED_QUANTIZATION,
        "prompt_sha256": cell["prompt_sha256"],
        "request": request,
        "raw_response": raw_response,
        "raw_response_sha256": _sha256_text(raw_response),
        "raw_http_response_body": transport["raw_body"],
        "generation_metadata": metadata,
        "generation_latency_seconds": attempt.get("generation_latency"),
        "first_attempt": True,
        "retry_count": 0,
        "resume": False,
        "selective_retry": False,
        "scaffold": False,
        "healer_during_generation": False,
        "evalplus_executed": False,
    }


def _pipeline_record(raw: dict[str, Any]) -> dict[str, Any]:
    extraction = extract_code(raw["raw_response"])
    normalized = (
        extraction.extracted_code
        if extraction.extraction_status == "extracted"
        else None
    )
    return {
        "run_id": frozen.RUN_ID,
        "generation_id": raw["generation_id"],
        "program_id": raw["program_id"],
        "task_id": raw["task_id"],
        "seed": raw["seed"],
        "sample_index": raw["sample_index"],
        "source_raw_response_sha256": raw["raw_response_sha256"],
        "pipeline_sha256": frozen.EXPECTED_PIPELINE_SHA256,
        "pipeline_correction_spec": "agent_tools.finals_rebuild.extraction.extract_code",
        "extraction_status": extraction.extraction_status,
        "extraction_method": extraction.extraction_method,
        "pipeline_normalized_source": normalized,
        "pipeline_normalized_source_sha256": _sha256_text(normalized) if normalized is not None else None,
        "pipeline_correction_is_healer": False,
    }


def generate(
    *, manifest_path: Path, manifest_sha256: str,
    base_url: str = DEFAULT_BASE_URL, timeout_seconds: float = TIMEOUT_SECONDS,
) -> None:
    _require(timeout_seconds == TIMEOUT_SECONDS, "timeout must equal frozen 300 seconds")
    zero_model_preflight(
        manifest_path=manifest_path,
        manifest_sha256=manifest_sha256,
        require_output_absent=True,
    )
    validation_rows = frozen.load_validation_rows(REPO_ROOT)
    task_records = frozen.load_validation_tasks(validation_rows, REPO_ROOT)
    tasks = {record["task_id"]: record for record in task_records}
    cells = _read_csv(manifest_path.parent / "generation_cells.csv")
    account_plan = _read_csv(manifest_path.parent / "evaluation_accounts.csv")
    protocol = load_generation_protocol(REPO_ROOT / frozen.PROTOCOL_RELATIVE)

    provenance = fetch_ollama_provenance(
        base_url,
        timeout_seconds,
        model=frozen.EXPECTED_MODEL,
        expected_digest_prefix=frozen.EXPECTED_MODEL_DIGEST,
    )
    _require(provenance["model_digest"] == frozen.EXPECTED_MODEL_DIGEST, "installed model digest drift")
    _require(provenance.get("quantization") == frozen.EXPECTED_QUANTIZATION, "installed quantization drift")

    run_dir = REPO_ROOT / frozen.RUN_OUTPUT_RELATIVE
    _require(not run_dir.exists(), "run directory appeared; overwrite forbidden")
    durable_write_text_new(run_dir / "frozen_manifest.json", manifest_path.read_text(encoding="utf-8"))
    durable_write_json_new(run_dir / "model_provenance.json", provenance)

    raw_records: list[dict[str, Any]] = []
    failed: list[str] = []
    started = time.monotonic()
    for cell in cells:
        task = tasks[cell["task_id"]]
        _require(_sha256_text(task["prompt"]) == cell["prompt_sha256"], "prompt hash drift before generation")
        expected, arities = frozen.prompt_contract(task["prompt"])
        _require(
            frozen._identity_hash({"entry_point": expected, "positional_arities": arities})
            == cell["prompt_contract_sha256"],
            "prompt contract hash drift before generation",
        )
        settings = protocol_settings(
            protocol,
            model_role="primary_development_model",
            seed=int(cell["seed"]),
        )
        attempt = run_attempt(
            PublicBenchmarkTask(
                benchmark="mbpp",
                task_id=task["task_id"],
                prompt=task["prompt"],
                entry_point=task["entry_point"],
                canonical_solution=None,
            ),
            "ab1",
            benchmark="mbpp",
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            settings=settings,
            model_digest=frozen.EXPECTED_MODEL_DIGEST,
            sample_index=int(cell["sample_index"]),
        )
        raw = _complete_raw_record(cell=cell, task=task, attempt=attempt)
        if raw is None:
            failed.append(cell["generation_id"])
            journal = {
                "run_id": frozen.RUN_ID,
                "cell_index": int(cell["cell_index"]),
                "task_id": cell["task_id"],
                "seed": int(cell["seed"]),
                "generation_id": cell["generation_id"],
                "status": "failed_single_attempt_no_retry",
                "attempt": attempt,
                "retry_count": 0,
                "resume": False,
                "selective_retry": False,
            }
        else:
            raw_records.append(raw)
            journal = {"status": "complete_single_attempt", **raw}
        durable_write_json_new(
            run_dir / "j" / f"{cell['generation_id']}.json",
            journal,
        )
        print(
            f"cell {cell['cell_index']}/100 persisted status={journal['status']}",
            flush=True,
        )

    if failed or len(raw_records) != 100:
        raise ValidationRunError(
            f"generation incomplete after exactly one attempt per cell: complete={len(raw_records)} failed={len(failed)}; resume/retry forbidden; H0/H1 materialization forbidden"
        )
    _require(len({row["generation_id"] for row in raw_records}) == 100, "duplicate completed generation")
    durable_write_jsonl_new(run_dir / "raw_generations.jsonl", raw_records)

    pipeline_records = [_pipeline_record(raw) for raw in raw_records]
    durable_write_jsonl_new(run_dir / "pipeline_normalized.jsonl", pipeline_records)
    raw_by_id = {row["generation_id"]: row for row in raw_records}
    pipeline_by_id = {row["generation_id"]: row for row in pipeline_records}
    planned_accounts = {row["evaluation_account_id"]: row for row in account_plan}
    materialized: list[dict[str, Any]] = []
    for cell in cells:
        raw = raw_by_id[cell["generation_id"]]
        pipeline = pipeline_by_id[cell["generation_id"]]
        task = tasks[cell["task_id"]]
        expected, arities = frozen.prompt_contract(task["prompt"])
        truncated = raw["generation_metadata"]["done_reason"] != "stop"
        normalized = pipeline["pipeline_normalized_source"]
        result = apply_healer(normalized, expected, arities, truncated)
        for arm in ("H0", "H1"):
            account_id = frozen._identity_hash(
                {"program_id": cell["program_id"], "healer_account": arm}
            )
            _require(account_id in planned_accounts, "materialized account not planned")
            source = normalized if arm == "H0" else result.output_source
            materialized.append({
                "run_id": frozen.RUN_ID,
                "cell_index": int(cell["cell_index"]),
                "program_id": cell["program_id"],
                "evaluation_account_id": account_id,
                "healer_account": arm,
                "task_id": cell["task_id"],
                "seed": int(cell["seed"]),
                "generation_id": cell["generation_id"],
                "raw_response_sha256": raw["raw_response_sha256"],
                "pipeline_normalized_source_sha256": pipeline["pipeline_normalized_source_sha256"],
                "evaluation_source": source,
                "evaluation_source_sha256": _sha256_text(source) if source is not None else None,
                "healer_status": "not_applied_control" if arm == "H0" else result.status,
                "healer_diagnostic": "not_applied_control" if arm == "H0" else result.diagnostic,
                "healer_sha256": "not_applied_control" if arm == "H0" else frozen.EXPECTED_HEALER_SHA256,
                "healer_rule_id": "not_applied_control" if arm == "H0" else frozen.EXPECTED_RULE_ID,
                "source_changed_by_healer": arm == "H1" and result.output_source != normalized,
                "same_raw_generation_h0_h1": True,
                "same_pipeline_normalized_input_h0_h1": True,
                "h1_regeneration": False,
                "evalplus_status": "not_executed",
            })
    _require(len(materialized) == 200, "materialized evaluation account count drift")
    _require(len({row["evaluation_account_id"] for row in materialized}) == 200, "duplicate materialized account")
    _require(set(planned_accounts) == {row["evaluation_account_id"] for row in materialized}, "planned/materialized account identity drift")
    durable_write_jsonl_new(run_dir / "h0_h1_accounts.jsonl", materialized)
    durable_write_json_new(
        run_dir / "materialization_manifest.json",
        {
            "status": "generation_and_h0_h1_materialization_complete_pending_manual_evalplus",
            "run_id": frozen.RUN_ID,
            "generation_cells": 100,
            "evaluation_accounts": 200,
            "h0_accounts": 100,
            "h1_accounts": 100,
            "healer_transformed": sum(
                row["source_changed_by_healer"]
                for row in materialized
                if row["healer_account"] == "H1"
            ),
            "model_calls": 100,
            "retry_count": 0,
            "resume": False,
            "selective_retry": False,
            "evalplus_executions": 0,
            "elapsed_seconds": round(time.monotonic() - started, 3),
        },
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("preflight", "generate"):
        command = commands.add_parser(name)
        command.add_argument("--manifest", type=Path, required=True)
        command.add_argument("--manifest-sha256", required=True)
    generation = commands.choices["generate"]
    generation.add_argument("--base-url", default=DEFAULT_BASE_URL)
    generation.add_argument("--timeout-seconds", type=float, default=TIMEOUT_SECONDS)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "preflight":
            print(json.dumps(zero_model_preflight(
                manifest_path=args.manifest,
                manifest_sha256=args.manifest_sha256,
            ), sort_keys=True))
        else:
            generate(
                manifest_path=args.manifest,
                manifest_sha256=args.manifest_sha256,
                base_url=args.base_url,
                timeout_seconds=args.timeout_seconds,
            )
    except (ValidationRunError, frozen.ValidationFreezeError, PersistenceError, KeyError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
