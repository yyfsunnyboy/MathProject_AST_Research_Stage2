#!/usr/bin/env python3
"""Fail-closed Candidate B runner for the frozen 60-task development replay.

The runner has no EvalPlus path.  ``preflight`` is zero-model; ``generate`` is
the separately manual operation bound to one immutable manifest.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import os
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
    detect_reasoning_leakage,
    fetch_ollama_provenance,
    load_generation_protocol,
    normalize_ollama_quantization,
    protocol_settings,
    run_attempt,
)
from scripts import freeze_mbpp_candidate_b_development60_replay as frozen  # noqa: E402


FROZEN_MANIFEST_RELATIVE = frozen.OUTPUT_RELATIVE / "manifest.json"
FROZEN_MANIFEST_SHA256 = "e8d0f8e9198848e8708d910f6c859622c272de850a2b1045d62993c114c98fbd"
TIMEOUT_SECONDS = 300.0


class CandidateBRunError(RuntimeError):
    """Raised when a frozen execution invariant fails."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CandidateBRunError(message)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _journal_count(path: Path) -> int:
    if not path.is_dir():
        return -1
    return len(os.listdir(path))


def validate_installed_model_provenance(provenance: dict[str, Any]) -> dict[str, Any]:
    """Require exact digest and normalized API-reported quantization identity."""
    digest = provenance.get("model_digest")
    _require(isinstance(digest, str), "installed model digest missing or non-string")
    _require(digest == frozen.EXPECTED_MODEL_DIGEST, "installed model digest drift")
    raw_quantization = provenance.get("quantization_api_value")
    normalized_quantization = normalize_ollama_quantization(raw_quantization)
    _require(
        normalized_quantization is not None,
        "installed quantization missing at /api/tags models[].details.quantization_level",
    )
    _require(
        normalized_quantization == frozen.EXPECTED_QUANTIZATION,
        "installed quantization drift",
    )
    return {
        "digest_value": digest,
        "digest_type": type(digest).__name__,
        "quantization_json_path": "models[].details.quantization_level",
        "quantization_raw_value": raw_quantization,
        "quantization_raw_type": type(raw_quantization).__name__,
        "quantization_normalized_value": normalized_quantization,
        "quantization_expected_value": frozen.EXPECTED_QUANTIZATION,
    }


def validate_r001_zero_cell_incident(path: Path) -> dict[str, Any]:
    """Inspect only r001 directory existence and journal filenames, never contents."""
    _require(path.is_dir(), "registered r001 incident directory is missing; manual review required")
    journal_dir = path / "j"
    _require(journal_dir.is_dir(), "registered r001 incident journal directory is missing; manual review required")
    _require(
        _journal_count(journal_dir) == 0,
        "registered r001 incident unexpectedly contains generation journal(s); manual review required",
    )
    return {
        "classification": "ZERO_CELL_PREFLIGHT_INCIDENT",
        "run_id": frozen.R001_RUN_ID,
        "directory_exists": True,
        "generation_journals": 0,
        "model_call_status": "model_call_confirmed_0",
        "result_source": False,
        "content_read_or_compared": False,
    }


def validate_r002_first_cell_persistence_incident(path: Path) -> dict[str, Any]:
    """Inspect only r002 structure and journal filenames, never journal contents."""
    _require(path.is_dir(), "registered r002 incident directory is missing; manual review required")
    journal_dir = path / "j"
    _require(journal_dir.is_dir(), "registered r002 incident journal directory is missing; manual review required")
    _require(
        _journal_count(journal_dir) == 0,
        "registered r002 incident unexpectedly contains generation journal(s); manual review required",
    )
    _require((path / "frozen_manifest.json").is_file(), "registered r002 frozen manifest missing")
    _require((path / "model_provenance.json").is_file(), "registered r002 model provenance missing")
    return {
        "classification": "FIRST_CELL_JOURNAL_PERSISTENCE_FAILURE",
        "run_id": frozen.R002_RUN_ID,
        "directory_exists": True,
        "generation_journals": 0,
        "persisted_responses": 0,
        "selectable_responses": 0,
        "evaluator_executions": 0,
        "model_call_status": "model_call_confirmed_1",
        "eligible_for_analysis_or_reuse": False,
        "result_source": False,
        "content_read_or_compared": False,
    }


def require_r003_absent(path: Path) -> None:
    _require(not path.exists(), "r003 run directory exists; resume/retry/overwrite forbidden")


def zero_model_preflight(
    *, manifest_path: Path, manifest_sha256: str, require_output_absent: bool = True,
) -> dict[str, Any]:
    expected_path = (REPO_ROOT / FROZEN_MANIFEST_RELATIVE).resolve()
    _require(manifest_path.resolve() == expected_path, "only the frozen Candidate B manifest path is accepted")
    _require(manifest_sha256 == FROZEN_MANIFEST_SHA256, "manifest SHA-256 argument is not frozen")
    manifest_bytes = manifest_path.read_bytes()
    _require(_sha256_bytes(manifest_bytes) == FROZEN_MANIFEST_SHA256, "frozen manifest bytes drift")
    manifest = json.loads(manifest_bytes)
    _require(manifest["status"] == "prepared_not_executed", "manifest status drift")
    _require(manifest["manifest_version"] == "candidate_b_development60_replay_r003_v1", "manifest version drift")
    _require(manifest["development_replay_only"] is True, "evidence role drift")
    _require(manifest["validation_or_confirmatory_evidence"] is False, "evidence claim drift")
    _require(manifest["run_id"] == frozen.RUN_ID, "run ID drift")
    _require(manifest["run_output_relative"] == frozen.RUN_OUTPUT_RELATIVE.as_posix(), "run path drift")
    counts = manifest["counts"]
    _require(counts == {
        "tasks": 60, "task_seed_identities": 300, "existing_p0_programs": 300,
        "candidate_b_new_generation_cells": 300, "candidate_b_new_accounts": 600,
        "factorial_programs": 600, "factorial_accounts": 1200,
    }, "manifest count drift")
    _require(manifest["existing_p0_results"] == {"h0_pass": 68, "h1_pass": 77, "programs": 300, "reexecuted": False}, "P0 result binding drift")
    _require(manifest["candidate_b"]["exact_text_sha256"] == frozen.EXPECTED_CANDIDATE_TEXT_SHA256, "Candidate B version drift")
    _require(manifest["model"] == frozen.EXPECTED_MODEL, "model tag drift")
    _require(manifest["model_digest"] == frozen.EXPECTED_MODEL_DIGEST, "model digest drift")
    _require(manifest["quantization"] == frozen.EXPECTED_QUANTIZATION, "quantization drift")
    _require(manifest["generation_parameters"] == frozen.GENERATION_OPTIONS, "generation parameter drift")
    _require(manifest["seeds"] == list(frozen.SEEDS), "seed drift")
    _require(manifest["pipeline_sha256"] == frozen.EXPECTED_PIPELINE_SHA256, "Pipeline version drift")
    _require(manifest["healer_sha256"] == frozen.EXPECTED_HEALER_SHA256, "Healer version drift")
    _require(manifest["healer_rule_order"] == [frozen.EXPECTED_HEALER_RULE], "Healer rule drift")
    _require(manifest["interrupted_mbpp_b28_used"] is False, "interrupted b28 evidence contamination")
    for relative, digest in manifest["source_sha256"].items():
        source = REPO_ROOT / relative
        _require(source.is_file(), f"frozen source missing: {relative}")
        _require(_sha256_bytes(source.read_bytes()) == digest, f"frozen source hash drift: {relative}")

    rebuilt = frozen.build_outputs(REPO_ROOT)
    _require(rebuilt["manifest.json"] == manifest_bytes, "deterministic manifest rebuild drift")
    lock = manifest["output_sha256_excluding_manifest_and_operator_guide"]
    expected_lock = set(rebuilt) - {"manifest.json", "operator_guide_zh.md"}
    _require(set(lock) == expected_lock, "frozen output lock set drift")
    for name, digest in lock.items():
        path = manifest_path.parent / name
        _require(path.is_file(), f"frozen asset missing: {name}")
        _require(_sha256_bytes(path.read_bytes()) == digest, f"frozen asset SHA-256 drift: {name}")
        _require(path.read_bytes() == rebuilt[name], f"frozen asset deterministic bytes drift: {name}")

    cells = _read_csv(manifest_path.parent / "candidate_b_generation_cells.csv")
    accounts = _read_csv(manifest_path.parent / "development_2x2_accounts.csv")
    reuse = _read_csv(manifest_path.parent / "p0_identity_hash_reuse_ledger.csv")
    mapping = _read_csv(manifest_path.parent / "r001_r002_r003_identity_mapping.csv")
    _require(len(cells) == len({row["generation_id"] for row in cells}) == 300, "300 Candidate B generation identities incomplete or duplicate")
    _require(len({(row["task_id"], row["seed"]) for row in cells}) == 300, "Candidate B task-seed identity drift")
    _require(len({row["task_id"] for row in cells}) == 60, "development task identity count drift")
    _require(len(accounts) == len({row["evaluation_account_id"] for row in accounts}) == 1200, "1200 factorial accounts incomplete or duplicate")
    _require(len(reuse) == len({row["program_id"] for row in reuse}) == 300, "P0 reuse ledger drift")
    _require(len(mapping) == 300, "r001/r002/r003 identity mapping count drift")
    _require(all(row["same_task_seed_identity"] == "true" for row in mapping), "r001/r002/r003 task-seed identity drift")
    _require(all(
        row["r001_result_reused"] == "false" and row["r001_response_available"] == "false"
        and row["r002_result_reused"] == "false" and row["r002_response_available"] == "false"
        for row in mapping
    ), "r001/r002 improperly marked as result source")
    _require(sum(row["prompt_condition"] == "Candidate_B" for row in accounts) == 600, "Candidate B account count drift")
    _require(sum(row["prompt_condition"] == "P0" for row in accounts) == 600, "P0 account count drift")
    _require(all(row["result_reexecution"] == "false" for row in reuse), "P0 reexecution flag drift")
    candidate_accounts = [row for row in accounts if row["prompt_condition"] == "Candidate_B"]
    _require(all(row["run_id"] == frozen.RUN_ID for row in candidate_accounts), "Candidate B account references non-r003 run")
    _require(not (REPO_ROOT / frozen.VALIDATION_RUN_RELATIVE).exists(), "2K-A validation run must remain absent")
    r001 = validate_r001_zero_cell_incident(REPO_ROOT / frozen.R001_RUN_OUTPUT_RELATIVE)
    r002 = validate_r002_first_cell_persistence_incident(REPO_ROOT / frozen.R002_RUN_OUTPUT_RELATIVE)
    run_dir = REPO_ROOT / frozen.RUN_OUTPUT_RELATIVE
    if require_output_absent:
        require_r003_absent(run_dir)
    return {
        "status": "zero_model_preflight_passed",
        "manifest_sha256": FROZEN_MANIFEST_SHA256,
        "development_tasks": 60,
        "candidate_b_generation_cells": 300,
        "candidate_b_accounts": 600,
        "factorial_programs": 600,
        "factorial_accounts": 1200,
        "existing_p0_h0_pass": 68,
        "existing_p0_h1_pass": 77,
        "model_calls": 0,
        "evalplus_executions": 0,
        "candidate_b_run_absent": not run_dir.exists(),
        "validation_run_absent": True,
        "r001_incident": r001,
        "r002_incident": r002,
    }


def _generation_metadata(attempt: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    transport = attempt.get("ollama_response_metadata")
    _require(isinstance(transport, dict), "generation transport metadata missing")
    raw_body = transport.get("raw_body")
    _require(isinstance(raw_body, str), "raw HTTP response body missing")
    body = json.loads(raw_body)
    fields = (
        "model", "created_at", "done", "done_reason", "total_duration",
        "load_duration", "prompt_eval_count", "prompt_eval_duration",
        "eval_count", "eval_duration",
    )
    _require(all(field in body for field in fields), "generation metadata field missing")
    _require(body["done"] is True, "generation transport did not finish")
    return body, {field: body[field] for field in fields}


def _strict_python_only(source: str) -> bool:
    if "```" in source:
        return False
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    return bool(tree.body)


def _complete_raw_record(
    *, cell: dict[str, str], task: PublicBenchmarkTask, attempt: dict[str, Any],
) -> dict[str, Any] | None:
    raw_response = attempt.get("raw_response")
    transport = attempt.get("ollama_response_metadata")
    if not isinstance(raw_response, str) or not raw_response.strip() or not isinstance(transport, dict):
        return None
    request = transport.get("request_payload")
    if not isinstance(request, dict):
        return None
    expected_prompt = task.prompt + frozen.SEPARATOR + frozen.CANDIDATE_B_TEXT
    expected_options = {
        "num_ctx": frozen.GENERATION_OPTIONS["num_ctx"],
        "num_predict": frozen.GENERATION_OPTIONS["num_predict"],
        "seed": int(cell["seed"]),
        "temperature": frozen.GENERATION_OPTIONS["temperature"],
        "top_k": frozen.GENERATION_OPTIONS["top_k"],
        "top_p": frozen.GENERATION_OPTIONS["top_p"],
    }
    if (
        request.get("model") != frozen.EXPECTED_MODEL
        or request.get("stream") is not False
        or request.get("think") is not False
        or request.get("options") != expected_options
        or request.get("messages") != [{"role": "user", "content": expected_prompt}]
    ):
        return None
    try:
        body, metadata = _generation_metadata(attempt)
    except (CandidateBRunError, json.JSONDecodeError):
        return None
    message = body.get("message")
    if not isinstance(message, dict) or message.get("content") != raw_response:
        return None
    leakage = detect_reasoning_leakage(body, raw_response)
    return {
        "run_id": frozen.RUN_ID,
        "cell_index": int(cell["cell_index"]),
        "task_id": cell["task_id"], "seed": int(cell["seed"]),
        "sample_index": int(cell["sample_index"]),
        "generation_id": cell["generation_id"], "program_id": cell["program_id"],
        "model": frozen.EXPECTED_MODEL, "model_digest": frozen.EXPECTED_MODEL_DIGEST,
        "quantization": frozen.EXPECTED_QUANTIZATION,
        "official_prompt_sha256": cell["official_prompt_sha256"],
        "candidate_b_text_sha256": frozen.EXPECTED_CANDIDATE_TEXT_SHA256,
        "composed_prompt_sha256": cell["composed_prompt_sha256"],
        "request": request, "raw_response": raw_response,
        "raw_response_sha256": _sha256_text(raw_response),
        "raw_http_response_body": transport["raw_body"],
        "generation_metadata": metadata,
        "generation_latency_seconds": attempt.get("generation_latency"),
        "strict_python_only": _strict_python_only(raw_response),
        "code_fence_count": raw_response.count("```"),
        "reasoning_leakage": leakage,
        "first_attempt": True, "retry_count": 0, "resume": False,
        "selective_retry": False, "healer_during_generation": False,
        "evalplus_executed": False,
    }


def _pipeline_record(raw: dict[str, Any]) -> dict[str, Any]:
    extraction = extract_code(raw["raw_response"])
    normalized = extraction.extracted_code if extraction.extraction_status == "extracted" else None
    return {
        "run_id": frozen.RUN_ID, "generation_id": raw["generation_id"],
        "program_id": raw["program_id"], "task_id": raw["task_id"],
        "seed": raw["seed"], "sample_index": raw["sample_index"],
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
    zero_model_preflight(manifest_path=manifest_path, manifest_sha256=manifest_sha256)
    p0 = frozen.load_existing_p0(REPO_ROOT)
    task_by_id: dict[str, PublicBenchmarkTask] = {}
    for row in p0:
        task = PublicBenchmarkTask(
            benchmark="mbpp", task_id=row["task_id"], prompt=row["prompt"],
            entry_point=row["prompt_contract"][0], canonical_solution=None,
        )
        previous = task_by_id.setdefault(row["task_id"], task)
        _require(previous.prompt == task.prompt and previous.entry_point == task.entry_point, "official prompt drift across seeds")
    cells = _read_csv(manifest_path.parent / "candidate_b_generation_cells.csv")
    account_plan = [row for row in _read_csv(manifest_path.parent / "development_2x2_accounts.csv") if row["prompt_condition"] == "Candidate_B"]
    protocol = load_generation_protocol(REPO_ROOT / frozen.PROTOCOL_RELATIVE)
    provenance = fetch_ollama_provenance(
        base_url, timeout_seconds, model=frozen.EXPECTED_MODEL,
        expected_digest_prefix=frozen.EXPECTED_MODEL_DIGEST,
    )
    provenance["candidate_b_identity_validation"] = validate_installed_model_provenance(provenance)
    run_dir = REPO_ROOT / frozen.RUN_OUTPUT_RELATIVE
    require_r003_absent(run_dir)
    durable_write_text_new(run_dir / "frozen_manifest.json", manifest_path.read_text(encoding="utf-8"))
    durable_write_json_new(run_dir / "model_provenance.json", provenance)

    raw_records: list[dict[str, Any]] = []
    failed: list[str] = []
    started = time.monotonic()
    for cell in cells:
        task = task_by_id[cell["task_id"]]
        _require(_sha256_text(task.prompt) == cell["official_prompt_sha256"], "official prompt hash drift")
        _require(_sha256_text(task.prompt + frozen.SEPARATOR + frozen.CANDIDATE_B_TEXT) == cell["composed_prompt_sha256"], "composed prompt hash drift")
        settings = protocol_settings(protocol, model_role="primary_development_model", seed=int(cell["seed"]))
        generated_task = PublicBenchmarkTask(
            benchmark="mbpp", task_id=task.task_id,
            prompt=task.prompt + frozen.SEPARATOR + frozen.CANDIDATE_B_TEXT,
            entry_point=task.entry_point, canonical_solution=None,
        )
        attempt = run_attempt(
            generated_task, "ab1", benchmark="mbpp", base_url=base_url,
            timeout_seconds=timeout_seconds, settings=settings,
            model_digest=frozen.EXPECTED_MODEL_DIGEST,
            sample_index=int(cell["sample_index"]),
        )
        # Validation below expects the official task plus Candidate B exactly once.
        validation_task = PublicBenchmarkTask(
            benchmark="mbpp", task_id=task.task_id, prompt=task.prompt,
            entry_point=task.entry_point, canonical_solution=None,
        )
        raw = _complete_raw_record(cell=cell, task=validation_task, attempt=attempt)
        if raw is None:
            failed.append(cell["generation_id"])
            journal = {
                "run_id": frozen.RUN_ID, "cell_index": int(cell["cell_index"]),
                "task_id": cell["task_id"], "seed": int(cell["seed"]),
                "generation_id": cell["generation_id"],
                "status": "failed_single_attempt_no_retry", "attempt": attempt,
                "retry_count": 0, "resume": False, "selective_retry": False,
            }
        else:
            raw_records.append(raw)
            journal = {"status": "complete_single_attempt", **raw}
        durable_write_json_new(run_dir / "j" / f"{cell['generation_id']}.json", journal)
        print(f"cell {cell['cell_index']}/300 persisted status={journal['status']}", flush=True)

    if failed or len(raw_records) != 300:
        raise CandidateBRunError(
            f"generation incomplete after exactly one attempt per cell: complete={len(raw_records)} failed={len(failed)}; resume/retry forbidden; aggregate and H0/H1 materialization forbidden"
        )
    _require(len({row["generation_id"] for row in raw_records}) == 300, "duplicate completed generation")
    durable_write_jsonl_new(run_dir / "raw_generations.jsonl", raw_records)
    pipeline_records = [_pipeline_record(raw) for raw in raw_records]
    durable_write_jsonl_new(run_dir / "pipeline_normalized.jsonl", pipeline_records)

    raw_by_id = {row["generation_id"]: row for row in raw_records}
    pipeline_by_id = {row["generation_id"]: row for row in pipeline_records}
    planned = {row["evaluation_account_id"]: row for row in account_plan}
    materialized: list[dict[str, Any]] = []
    for cell in cells:
        raw = raw_by_id[cell["generation_id"]]
        pipeline = pipeline_by_id[cell["generation_id"]]
        task = task_by_id[cell["task_id"]]
        contract = frozen._prompt_contract(task.prompt)
        normalized = pipeline["pipeline_normalized_source"]
        truncated = raw["generation_metadata"]["done_reason"] != "stop"
        healed = apply_healer(normalized, contract[0], contract[1], truncated)
        for arm in ("H0", "H1"):
            account_id = frozen._identity_hash({"program_id": cell["program_id"], "healer_account": arm})
            _require(account_id in planned, "materialized Candidate B account was not frozen")
            source = normalized if arm == "H0" else healed.output_source
            materialized.append({
                "run_id": frozen.RUN_ID, "cell_index": int(cell["cell_index"]),
                "program_id": cell["program_id"], "evaluation_account_id": account_id,
                "factorial_arm": f"Candidate_B_{arm}", "healer_account": arm,
                "task_id": cell["task_id"], "seed": int(cell["seed"]),
                "generation_id": cell["generation_id"],
                "raw_response_sha256": raw["raw_response_sha256"],
                "pipeline_normalized_source_sha256": pipeline["pipeline_normalized_source_sha256"],
                "evaluation_source": source,
                "evaluation_source_sha256": _sha256_text(source) if source is not None else None,
                "healer_status": "not_applied_control" if arm == "H0" else healed.status,
                "healer_diagnostic": "not_applied_control" if arm == "H0" else healed.diagnostic,
                "healer_sha256": "not_applied_control" if arm == "H0" else frozen.EXPECTED_HEALER_SHA256,
                "healer_rule_id": "not_applied_control" if arm == "H0" else frozen.EXPECTED_HEALER_RULE,
                "source_changed_by_healer": arm == "H1" and healed.output_source != normalized,
                "same_raw_generation_h0_h1": True,
                "same_pipeline_normalized_input_h0_h1": True,
                "h1_regeneration": False, "pipeline_correction_is_healer": False,
                "evaluator_result_used_by_healer": False, "evalplus_status": "not_executed",
            })
    _require(len(materialized) == len({row["evaluation_account_id"] for row in materialized}) == 600, "Candidate B H0/H1 account drift")
    _require(set(planned) == {row["evaluation_account_id"] for row in materialized}, "planned/materialized Candidate B account mismatch")
    durable_write_jsonl_new(run_dir / "h0_h1_accounts.jsonl", materialized)
    durable_write_json_new(run_dir / "materialization_manifest.json", {
        "status": "candidate_b_generation_and_h0_h1_materialization_complete_pending_separately_authorized_evalplus",
        "evidence_role": "development_replay_only", "run_id": frozen.RUN_ID,
        "generation_cells": 300, "candidate_b_accounts": 600,
        "factorial_programs_after_p0_reuse": 600, "factorial_accounts_after_p0_reuse": 1200,
        "healer_transformed": sum(row["source_changed_by_healer"] for row in materialized if row["healer_account"] == "H1"),
        "model_calls": 300, "retry_count": 0, "resume": False,
        "selective_retry": False, "evalplus_executions": 0,
        "elapsed_seconds": round(time.monotonic() - started, 3),
    })


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
                manifest_path=args.manifest, manifest_sha256=args.manifest_sha256,
            ), sort_keys=True))
        else:
            generate(
                manifest_path=args.manifest, manifest_sha256=args.manifest_sha256,
                base_url=args.base_url, timeout_seconds=args.timeout_seconds,
            )
    except (CandidateBRunError, frozen.CandidateBFreezeError, PersistenceError, KeyError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
