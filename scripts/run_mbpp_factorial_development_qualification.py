#!/usr/bin/env python3
"""Execute or materialize the frozen b28 development qualification protocol."""

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
from agent_tools.finals_rebuild.generation_persistence import (  # noqa: E402
    PersistenceError,
    durable_write_json_new,
    durable_write_jsonl_new,
)
from agent_tools.finals_rebuild.mbpp_evaluator_blind_healer import (  # noqa: E402
    CANDIDATE_ID as HEALER_CANDIDATE_ID,
    RULE_ORDER,
    apply_healer,
)
from agent_tools.finals_rebuild.ollama_generation_runner import (  # noqa: E402
    DEFAULT_BASE_URL,
    detect_reasoning_leakage,
    fetch_ollama_provenance,
    load_generation_protocol,
    protocol_settings,
    run_attempt,
)
from scripts import build_mbpp_integrated_development_evidence as integrated  # noqa: E402
from scripts import freeze_mbpp_factorial_development_qualification_v1 as qualification  # noqa: E402
from scripts import freeze_mbpp_factorial_qualification_operator_binding_v1 as binding  # noqa: E402
from scripts import run_mbpp_development_baseline as baseline  # noqa: E402


TASKS_PATH = REPO_ROOT / "data/mbpp_plus/tasks.jsonl"
TREATMENTS = {
    "p0": {"plan": "p0_generation_plan.json", "run_id": qualification.P0_RUN_ID},
    "candidate_b": {"plan": "candidate_b_generation_plan.json", "run_id": qualification.P1_RUN_ID},
}


class FactorialQualificationRunError(RuntimeError):
    """Raised before an unsafe or protocol-divergent operation."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise FactorialQualificationRunError(message)


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256(value.encode("utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _index(rows: list[dict[str, Any]], label: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = row["generation_id"]
        _require(key not in result, f"duplicate {label} generation ID: {key}")
        result[key] = row
    return result


def _binding_outputs() -> dict[str, bytes]:
    outputs = binding.build_outputs(REPO_ROOT)
    root = REPO_ROOT / binding.OUTPUT_RELATIVE
    for name, content in outputs.items():
        _require((root / name).is_file(), f"operator binding missing: {name}")
        _require((root / name).read_bytes() == content, f"operator binding drift: {name}")
    return outputs


def load_frozen_plan(treatment: str) -> dict[str, Any]:
    _require(treatment in TREATMENTS, f"unknown treatment: {treatment}")
    outputs = _binding_outputs()
    name = TREATMENTS[treatment]["plan"]
    plan = json.loads(outputs[name])
    _require(plan["run_id"] == TREATMENTS[treatment]["run_id"], "run ID drift")
    _require(plan["treatment"] == treatment, "treatment drift")
    _require(plan["expected_cells"] == len(plan["cells"]) == 140, "plan must contain 140 cells")
    _require(plan["task_count"] == len(plan["task_ids"]) == 28, "plan must contain 28 tasks")
    _require(plan["attempts_per_cell"] == 1, "exactly one attempt required")
    _require(not any(plan[key] for key in ("retry", "resume", "selective_retry", "overwrite", "healer")), "forbidden generation policy enabled")
    _require(plan["pipeline_correction_is_healer"] is False, "Pipeline/Healer accounting drift")
    return plan


def resolve_run_dir(treatment: str, run_id: str) -> Path:
    plan = load_frozen_plan(treatment)
    _require(run_id == plan["run_id"], "run ID differs from frozen plan")
    return REPO_ROOT / plan["physical_storage_directory"]


def _load_tasks(task_ids: list[str]) -> dict[str, PublicBenchmarkTask]:
    selected = set(task_ids)
    found: dict[str, PublicBenchmarkTask] = {}
    with TASKS_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("task_id") not in selected:
                continue
            _require(set(record) == {"task_id", "prompt", "entry_point"}, "model-visible task schema drift")
            found[record["task_id"]] = PublicBenchmarkTask(
                benchmark="mbpp",
                task_id=record["task_id"],
                prompt=record["prompt"],
                entry_point=record["entry_point"],
                canonical_solution=None,
            )
    _require(set(found) == selected, "frozen task missing from model-visible file")
    return found


def _composed_prompt(plan: dict[str, Any], official_prompt: str) -> str:
    if plan["treatment"] == "p0":
        return official_prompt
    _require(_sha256_text(plan["candidate_exact_text_utf8"]) == plan["candidate_exact_text_sha256"], "Candidate B text hash drift")
    _require(_sha256_text(plan["separator_exact_text_utf8"]) == plan["separator_sha256"], "separator hash drift")
    return official_prompt + plan["separator_exact_text_utf8"] + plan["candidate_exact_text_utf8"]


def _attempt_record(
    plan: dict[str, Any], cell: dict[str, Any], task: PublicBenchmarkTask, attempt: dict[str, Any]
) -> dict[str, Any] | None:
    raw = attempt.get("raw_response")
    transport = attempt.get("ollama_response_metadata")
    if not isinstance(transport, dict) or not isinstance(transport.get("raw_body"), str):
        return None
    try:
        body = json.loads(transport["raw_body"])
    except json.JSONDecodeError:
        return None
    content = body.get("message", {}).get("content") if isinstance(body.get("message"), dict) else None
    complete = (
        transport.get("http_status") == 200
        and body.get("done") is True
        and isinstance(content, str)
        and bool(content.strip())
        and raw == content
    )
    if not complete:
        return None
    request = transport.get("request_payload")
    _require(isinstance(request, dict), "complete response request missing")
    _require(request.get("model") == plan["model"] and request.get("think") is False, "request protocol drift")
    expected_prompt = _composed_prompt(plan, task.prompt)
    _require(request.get("messages") == [{"role": "user", "content": expected_prompt}], "prompt composition drift")
    leakage = detect_reasoning_leakage(body, raw)
    return {
        "generation_id": cell["planned_cell_id"],
        "planned_cell_id": cell["planned_cell_id"],
        "run_id": plan["run_id"],
        "logical_run_id": plan["run_id"],
        "cell_index": cell["cell_index"],
        "task_id": cell["task_id"],
        "seed": cell["seed"],
        "sample_index": cell["sample_index"],
        "model": plan["model"],
        "model_digest": plan["model_digest"],
        "official_prompt_sha256": _sha256_text(task.prompt),
        "composed_prompt_sha256": _sha256_text(expected_prompt),
        "request": request,
        "raw_response": raw,
        "raw_response_sha256": _sha256_text(raw),
        "raw_http_response_body": transport["raw_body"],
        "generation_metadata": baseline._generation_metadata(attempt),
        "generation_latency_seconds": attempt["generation_latency"],
        "transport_complete": True,
        "model_generation_complete": True,
        "generation_complete": True,
        "protocol_compliant": not leakage,
        "protocol_violations": ["reasoning_leakage_in_message_content"] if leakage else [],
        "reasoning_leakage": leakage,
        "first_attempt": True,
        "retry_count": 0,
        "resume": False,
        "selective_retry": False,
        "healer": False,
        "observed_account": True,
        "pipeline_correction_applied_during_generation": False,
    }


def _validate_complete_run(plan: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    required = ("generation_plan.json", "raw_generations.jsonl", "pipeline_corrected.jsonl")
    _require(all((run_dir / name).is_file() for name in required), f"incomplete run artifact set: {run_dir}")
    expected_plan = json.loads((REPO_ROOT / binding.OUTPUT_RELATIVE / TREATMENTS[plan["treatment"]]["plan"]).read_text(encoding="utf-8"))
    _require(json.loads((run_dir / "generation_plan.json").read_text(encoding="utf-8")) == expected_plan, "persisted run plan drift")
    raw = _index(_read_jsonl(run_dir / "raw_generations.jsonl"), "raw")
    pipeline = _index(_read_jsonl(run_dir / "pipeline_corrected.jsonl"), "Pipeline")
    cells = {cell["planned_cell_id"]: cell for cell in plan["cells"]}
    planned = set(cells)
    _require(set(raw) == set(pipeline) == planned and len(planned) == 140, "complete run identity drift")
    journal_files = list((run_dir / binding.JOURNAL_DIRECTORY).glob("*.json"))
    _require(len(journal_files) == 140, "journal count drift")
    for generation_id in planned:
        cell = cells[generation_id]
        _require(raw[generation_id]["task_id"] == pipeline[generation_id]["task_id"] == cell["task_id"], "task relation drift")
        _require(int(raw[generation_id]["seed"]) == int(pipeline[generation_id]["seed"]) == int(cell["seed"]), "seed relation drift")
        _require(raw[generation_id]["model"] == plan["model"], "model tag drift")
        _require(raw[generation_id]["model_digest"] == plan["model_digest"], "model digest drift")
        _require(raw[generation_id]["request"].get("think") is False, "think=false drift")
        _require(raw[generation_id]["generation_complete"] is True and raw[generation_id]["transport_complete"] is True, "generation completeness drift")
        _require(_sha256_text(raw[generation_id]["raw_response"]) == raw[generation_id]["raw_response_sha256"], "raw response hash drift")
        _require(raw[generation_id]["raw_response_sha256"] == pipeline[generation_id]["source_raw_response_sha256"], "raw/Pipeline hash drift")
        _require(raw[generation_id]["retry_count"] == 0, "retry count drift")
        _require(raw[generation_id]["resume"] is False and raw[generation_id]["selective_retry"] is False, "resume policy drift")
        normalized = pipeline[generation_id]["pipeline_corrected_output"]
        normalized_hash = _sha256_text(normalized) if normalized is not None else None
        _require(normalized_hash == pipeline[generation_id]["pipeline_corrected_output_sha256"], "Pipeline output hash drift")
    return {"raw": raw, "pipeline": pipeline}


def preflight() -> dict[str, Any]:
    outputs = _binding_outputs()
    states = {}
    for treatment in TREATMENTS:
        plan = load_frozen_plan(treatment)
        run_dir = REPO_ROOT / plan["physical_storage_directory"]
        if not run_dir.exists():
            states[treatment] = "not_started"
        else:
            try:
                _validate_complete_run(plan, run_dir)
            except FactorialQualificationRunError:
                states[treatment] = "existing_directory_invalid_no_resume"
            else:
                states[treatment] = "complete_140_no_retry"
    factorial_dir = REPO_ROOT / binding.FACTORIAL_PATH
    return {
        "status": "preflight_ok_no_model_or_evaluator_call",
        "binding_manifest_sha256": _sha256(outputs["operator_binding_manifest.json"]),
        "run_states": states,
        "factorial_materialization_state": "not_started" if not factorial_dir.exists() else "existing_directory_no_overwrite",
        "planned_generation_cells": 280,
        "planned_factorial_accounts": 560,
    }


def generate(*, treatment: str, run_id: str, base_url: str, timeout_seconds: float) -> None:
    plan = load_frozen_plan(treatment)
    _require(run_id == plan["run_id"], "run ID differs from frozen plan")
    _require(timeout_seconds == 600.0, "timeout must be exactly 600 seconds")
    run_dir = REPO_ROOT / plan["physical_storage_directory"]
    _require(not run_dir.exists(), "run directory already exists; retry/resume/overwrite forbidden")
    protocol = load_generation_protocol(REPO_ROOT / binding.GENERATION_PROTOCOL)
    provenance = fetch_ollama_provenance(
        base_url, timeout_seconds, model=plan["model"], expected_digest_prefix=plan["model_digest"]
    )
    _require(provenance["model_digest"] == plan["model_digest"], "installed model digest mismatch")
    durable_write_json_new(run_dir / "generation_plan.json", plan)
    tasks = _load_tasks(plan["task_ids"])
    raw_records: list[dict[str, Any]] = []
    failed: list[str] = []
    started = time.monotonic()
    for cell in plan["cells"]:
        task = tasks[cell["task_id"]]
        prompt = _composed_prompt(plan, task.prompt)
        generated_task = PublicBenchmarkTask(
            benchmark="mbpp", task_id=task.task_id, prompt=prompt,
            entry_point=task.entry_point, canonical_solution=None,
        )
        settings = protocol_settings(protocol, model_role="primary_development_model", seed=cell["seed"])
        attempt = run_attempt(
            generated_task, "ab1", benchmark="mbpp", base_url=base_url,
            timeout_seconds=timeout_seconds, settings=settings,
            model_digest=plan["model_digest"], sample_index=cell["sample_index"],
        )
        record = _attempt_record(plan, cell, task, attempt)
        if record is None:
            failed.append(cell["planned_cell_id"])
            journal = {
                "planned_cell_id": cell["planned_cell_id"], "run_id": plan["run_id"],
                "task_id": cell["task_id"], "seed": cell["seed"],
                "status": "failed_single_attempt_no_retry", "attempt": attempt,
                "retry_count": 0, "healer": False,
            }
        else:
            raw_records.append(record)
            journal = record
        durable_write_json_new(run_dir / binding.JOURNAL_DIRECTORY / f"{cell['planned_cell_id']}.json", journal)
        print(f"cell {cell['cell_index']}/140 persisted: {cell['task_id']} seed={cell['seed']}", flush=True)
    if failed or len(raw_records) != 140:
        raise FactorialQualificationRunError(
            f"single-attempt generation incomplete: complete={len(raw_records)} failed={len(failed)}; run permanently invalid, resume forbidden"
        )
    durable_write_jsonl_new(run_dir / "raw_generations.jsonl", raw_records)
    pipeline_records = []
    for record in raw_records:
        item = baseline.build_pipeline_record(record)
        item["run_id"] = plan["run_id"]
        item["logical_run_id"] = plan["run_id"]
        pipeline_records.append(item)
    durable_write_jsonl_new(run_dir / "pipeline_corrected.jsonl", pipeline_records)
    print(json.dumps({
        "generation": "140/140", "elapsed_seconds": round(time.monotonic() - started, 3),
        "protocol_violations_in_itt": sum(not row["protocol_compliant"] for row in raw_records),
        "retry_count": 0, "healer": False,
    }, sort_keys=True), flush=True)


def _account_plan() -> dict[tuple[str, str], dict[str, str]]:
    path = REPO_ROOT / qualification.OUTPUT_RELATIVE / "candidate_b_2x2_account_plan.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    result = {(row["generation_planned_cell_id"], row["healer_account"]): row for row in rows}
    _require(len(rows) == len(result) == 560, "frozen factorial account plan drift")
    return result


def build_factorial_records(
    plans: dict[str, dict[str, Any]], runs: dict[str, dict[str, Any]],
    tasks: dict[str, PublicBenchmarkTask], account_plan: dict[tuple[str, str], dict[str, str]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for treatment in ("p0", "candidate_b"):
        plan = plans[treatment]
        raw_by_id = runs[treatment]["raw"]
        pipeline_by_id = runs[treatment]["pipeline"]
        for cell in plan["cells"]:
            generation_id = cell["planned_cell_id"]
            raw = raw_by_id[generation_id]
            pipeline = pipeline_by_id[generation_id]
            normalized = pipeline["pipeline_corrected_output"]
            expected_name, arities = integrated._prompt_contract(tasks[cell["task_id"]].prompt)
            truncated = raw.get("generation_metadata", {}).get("done_reason") != "stop"
            healed = apply_healer(normalized, expected_name, arities, truncated)
            for account in ("H0", "H1"):
                frozen_account = account_plan[(generation_id, account)]
                source = normalized if account == "H0" else healed.output_source
                source_hash = _sha256_text(source) if source is not None else ""
                if account == "H0":
                    _require(source_hash == (pipeline["pipeline_corrected_output_sha256"] or ""), "H0 Pipeline hash drift")
                else:
                    _require(source_hash == (healed.output_sha256 or ""), "H1 Healer hash drift")
                records.append({
                    "evaluation_account_id": frozen_account["evaluation_account_id"],
                    "factorial_arm": f"{'P0' if treatment == 'p0' else 'P1'}_{account}",
                    "prompt_condition": frozen_account["prompt_condition"],
                    "healer_account": account,
                    "run_id": plan["run_id"],
                    "treatment": treatment,
                    "task_id": cell["task_id"],
                    "seed": cell["seed"],
                    "sample_index": cell["sample_index"],
                    "generation_id": generation_id,
                    "raw_response_sha256": raw["raw_response_sha256"],
                    "pipeline_input_sha256": pipeline["pipeline_corrected_output_sha256"],
                    "evaluation_source": source,
                    "evaluation_source_sha256": source_hash or None,
                    "healer_candidate_id": HEALER_CANDIDATE_ID if account == "H1" else None,
                    "healer_rule_order": list(RULE_ORDER) if account == "H1" else [],
                    "healer_status": healed.status if account == "H1" else "not_applied_control",
                    "healer_triggered_rule_ids": list(healed.triggered_rule_ids) if account == "H1" else [],
                    "healer_applied_rule_ids": list(healed.applied_rule_ids) if account == "H1" else [],
                    "healer_diagnostic": healed.diagnostic if account == "H1" else "H0_control",
                    "generation_truncated": truncated,
                    "model_regeneration_for_healer": False,
                    "pipeline_packaging_is_healer": False,
                    "development_only": True,
                    "evaluator_result_used": False,
                })
    _require(len(records) == 560, "factorial materialization count drift")
    _require(len({row["evaluation_account_id"] for row in records}) == 560, "factorial account ID drift")
    return records


def materialize_factorial() -> None:
    factorial_dir = REPO_ROOT / binding.FACTORIAL_PATH
    _require(not factorial_dir.exists(), "factorial directory already exists; resume/overwrite forbidden")
    plans = {name: load_frozen_plan(name) for name in TREATMENTS}
    runs = {
        name: _validate_complete_run(plan, REPO_ROOT / plan["physical_storage_directory"])
        for name, plan in plans.items()
    }
    tasks = _load_tasks(plans["p0"]["task_ids"])
    _require(plans["p0"]["task_ids"] == plans["candidate_b"]["task_ids"], "P0/P1 task order drift")
    records = build_factorial_records(plans, runs, tasks, _account_plan())
    plan_record = {
        "materialization_id": "mbpp_b28_factorial_materialization_r001",
        "status": "development_only_pre_evaluation",
        "source_run_ids": [plans["p0"]["run_id"], plans["candidate_b"]["run_id"]],
        "generation_cells": 280,
        "factorial_accounts": 560,
        "factorial_arms": ["P0_H0", "P0_H1", "P1_H0", "P1_H1"],
        "same_generation_h0_h1": True,
        "model_regeneration_for_healer": False,
        "pipeline_packaging_is_healer": False,
        "evaluator_executed": False,
    }
    durable_write_json_new(factorial_dir / "factorial_materialization_plan.json", plan_record)
    receipt = durable_write_jsonl_new(factorial_dir / "factorial_sources.jsonl", records)
    durable_write_json_new(factorial_dir / "factorial_materialization_manifest.json", {
        **plan_record,
        "factorial_sources_sha256": receipt.sha256,
        "healer_source_sha256": _sha256((REPO_ROOT / qualification.HEALER_SOURCE).read_bytes()),
        "pipeline_source_sha256": _sha256((REPO_ROOT / qualification.PIPELINE_SOURCE).read_bytes()),
        "trigger_counts": {
            condition: sum(row["prompt_condition"] == condition and row["healer_account"] == "H1" and bool(row["healer_triggered_rule_ids"]) for row in records)
            for condition in ("P0", "P1_candidate_b")
        },
        "evalplus_executions": 0,
    })


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("preflight")
    generation = commands.add_parser("generate")
    generation.add_argument("--treatment", choices=sorted(TREATMENTS), required=True)
    generation.add_argument("--run-id", required=True)
    generation.add_argument("--base-url", default=DEFAULT_BASE_URL)
    generation.add_argument("--timeout-seconds", type=float, default=600.0)
    commands.add_parser("materialize-factorial")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "preflight":
            print(json.dumps(preflight(), indent=2, sort_keys=True))
        elif args.command == "generate":
            generate(treatment=args.treatment, run_id=args.run_id, base_url=args.base_url, timeout_seconds=args.timeout_seconds)
        else:
            materialize_factorial()
    except (FactorialQualificationRunError, PersistenceError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
