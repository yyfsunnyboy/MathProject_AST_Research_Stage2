#!/usr/bin/env python3
"""Generate or evaluate the frozen MBPP+ Generic Code Scaffold v0 P1 run."""

from __future__ import annotations

import argparse
import csv
import importlib.metadata
import io
import json
import os
import pathlib
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Any, Optional, Sequence


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_tools.finals_rebuild.benchmarks_adapter import PublicBenchmarkTask  # noqa: E402
from agent_tools.finals_rebuild.generation_persistence import (  # noqa: E402
    PersistenceError,
    durable_write_json_new,
    durable_write_jsonl_new,
    durable_write_text_new,
)
from agent_tools.finals_rebuild.ollama_generation_runner import (  # noqa: E402
    DEFAULT_BASE_URL,
    detect_reasoning_leakage,
    fetch_ollama_provenance,
    load_generation_protocol,
    protocol_settings,
    run_attempt,
)
from scripts import freeze_mbpp_scaffold_v0_protocol as frozen  # noqa: E402
from scripts import run_mbpp_development_baseline as p0_driver  # noqa: E402


EVALUATOR_ENGINE = "evalplus_0.3.1_check_correctness_subset"
TEMP_PATH_PLACEHOLDER = ".tmp-" + ("x" * 16) + ".tmp"


class ScaffoldRunError(RuntimeError):
    """Raised on any frozen P1 run invariant violation."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ScaffoldRunError(message)


def resolve_run_dir(run_id: str) -> pathlib.Path:
    if run_id != frozen.RUN_ID:
        raise ScaffoldRunError(f"only frozen run_id {frozen.RUN_ID!r} is allowed")
    return REPO_ROOT / frozen.PHYSICAL_RUN_RELATIVE


def planned_storage_paths(
    plan: dict[str, Any], run_dir: pathlib.Path
) -> list[dict[str, Any]]:
    """Enumerate every final path and conservative temp-path shape before I/O."""
    journal_directory_name = plan.get("journal_directory_name", "generation_journal")
    finals = [
        run_dir / "generation_plan.json",
        *(
            run_dir / journal_directory_name / f"{cell['generation_id']}.json"
            for cell in plan["cells"]
        ),
        run_dir / "raw_generations.jsonl",
        run_dir / "pipeline_corrected.jsonl",
        run_dir / "evaluation_results.csv",
        run_dir / "evaluation_summary.md",
    ]
    entries: list[dict[str, Any]] = []
    temp_paths: set[pathlib.Path] = set()
    for path in finals:
        absolute = path.resolve()
        entries.append(
            {"kind": "final", "path": str(absolute), "length": len(str(absolute))}
        )
        temp_paths.add(absolute.parent / TEMP_PATH_PLACEHOLDER)
    for path in sorted(temp_paths, key=lambda value: str(value)):
        entries.append(
            {"kind": "temporary", "path": str(path), "length": len(str(path))}
        )
    return entries


def preflight_storage_paths(
    plan: dict[str, Any],
    run_dir: pathlib.Path,
    *,
    path_budget: int = frozen.WINDOWS_PATH_BUDGET,
) -> dict[str, Any]:
    _require(path_budget <= 240, "Windows storage path budget must be at most 240")
    entries = planned_storage_paths(plan, run_dir)
    longest = max(entries, key=lambda entry: entry["length"])
    over_budget = [entry for entry in entries if entry["length"] > path_budget]
    if over_budget:
        first = over_budget[0]
        raise ScaffoldRunError(
            f"storage path preflight rejected before model call: length={first['length']} "
            f"budget={path_budget} kind={first['kind']} path={first['path']}"
        )
    return {
        "path_budget": path_budget,
        "checked_path_count": len(entries),
        "longest_path": longest["path"],
        "longest_path_length": longest["length"],
    }


def load_frozen_plan(repo_root: pathlib.Path = REPO_ROOT) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    expected_outputs = frozen.frozen_outputs(repo_root)
    for relative_path, expected_bytes in expected_outputs.items():
        path = repo_root / relative_path
        _require(path.is_file(), f"frozen protocol output missing: {relative_path}")
        _require(path.read_bytes() == expected_bytes, f"frozen protocol output drift: {relative_path}")
    plan = json.loads((repo_root / frozen.PLAN_RELATIVE).read_text(encoding="utf-8"))
    _require(plan == frozen.build_plan(repo_root), "frozen P1 plan semantic mismatch")
    _require(plan["expected_cells"] == len(plan["cells"]) == 100, "P1 plan must contain 100 cells")
    _require(plan["run_id"] != plan["p0_run_id"], "P1 and P0 run IDs must differ")
    _require(not any(plan[key] for key in ("retry", "selective_retry", "resume", "overwrite", "healer")), "forbidden run policy enabled")
    _require(plan["accounts"] == ["observed", "pipeline_corrected"], "evaluation accounts drift")
    _require(plan["pipeline_correction_is_healer"] is False, "Pipeline correction cannot be Healer")
    _require(plan["run_id"] == plan["logical_run_id"] == frozen.RUN_ID, "logical run ID drift")
    _require(
        plan["physical_storage_directory"] == frozen.PHYSICAL_RUN_RELATIVE.as_posix(),
        "physical storage mapping drift",
    )
    _require(plan["journal_directory_name"] == "j", "journal directory mapping drift")
    return plan


def _task_objects(plan: dict[str, Any]) -> dict[str, PublicBenchmarkTask]:
    records = frozen.load_selected_task_records(REPO_ROOT, plan["task_ids"])
    return {
        record["task_id"]: PublicBenchmarkTask(
            benchmark="mbpp",
            task_id=record["task_id"],
            prompt=record["prompt"],
            entry_point=record["entry_point"],
            canonical_solution=None,
        )
        for record in records
    }


def _persist_attempt_journal(
    journal_dir: pathlib.Path,
    *,
    cell: dict[str, Any],
    record: dict[str, Any],
) -> None:
    _require(record["generation_id"] == cell["generation_id"], "journal generation ID mismatch")
    durable_write_json_new(journal_dir / f"{cell['generation_id']}.json", record)


def _complete_attempt_state(
    *, cell: dict[str, Any], attempt: dict[str, Any]
) -> dict[str, Any]:
    """Separate transport/generation completeness from protocol compliance."""
    raw_response = attempt.get("raw_response")
    transport = attempt.get("ollama_response_metadata")
    if not isinstance(transport, dict) or not isinstance(transport.get("raw_body"), str):
        return {
            "transport_complete": False,
            "model_generation_complete": False,
            "generation_complete": False,
            "protocol_compliant": False,
            "protocol_violations": [],
        }
    try:
        body = json.loads(transport["raw_body"])
    except json.JSONDecodeError:
        return {
            "transport_complete": False,
            "model_generation_complete": False,
            "generation_complete": False,
            "protocol_compliant": False,
            "protocol_violations": [],
        }
    message = body.get("message") if isinstance(body.get("message"), dict) else {}
    body_content = message.get("content")
    transport_complete = transport.get("http_status") == 200
    generation_complete = (
        transport_complete
        and body.get("done") is True
        and isinstance(body_content, str)
        and bool(body_content.strip())
        and isinstance(raw_response, str)
        and raw_response == body_content
    )
    if not generation_complete:
        return {
            "transport_complete": transport_complete,
            "model_generation_complete": False,
            "generation_complete": False,
            "protocol_compliant": False,
            "protocol_violations": [],
        }

    response_sha256 = frozen.sha256_text(raw_response)
    saved_sha256 = attempt.get("raw_response_sha256")
    if saved_sha256 is not None:
        _require(saved_sha256 == response_sha256, "saved raw response SHA-256 mismatch")
    request = transport.get("request_payload")
    _require(isinstance(request, dict), "complete response request payload missing")
    _require(request.get("model") == frozen.MODEL, "complete response model mismatch")
    _require(request.get("think") is False, "complete response request think flag drift")
    messages = request.get("messages")
    _require(
        isinstance(messages, list)
        and len(messages) == 1
        and messages[0].get("role") == "user"
        and isinstance(messages[0].get("content"), str),
        "complete response request message missing",
    )
    _require(
        frozen.sha256_text(messages[0]["content"]) == cell["composed_prompt_sha256"],
        "complete response composed prompt SHA-256 mismatch",
    )

    violations: list[str] = []
    if detect_reasoning_leakage(body, raw_response):
        violations.append("reasoning_leakage_in_message_content")
    elif attempt.get("status") != "success":
        stage = str(attempt.get("failure_stage") or "unknown")
        violations.append(f"response_processing_failure:{stage}")
    return {
        "transport_complete": True,
        "model_generation_complete": True,
        "generation_complete": True,
        "protocol_compliant": not violations,
        "protocol_violations": violations,
    }


def _raw_record_from_complete_attempt(
    *,
    cell: dict[str, Any],
    attempt: dict[str, Any],
    recovered_from_existing_response: bool,
) -> dict[str, Any] | None:
    state = _complete_attempt_state(cell=cell, attempt=attempt)
    if not state["generation_complete"]:
        return None
    raw_response = attempt["raw_response"]
    transport = attempt["ollama_response_metadata"]
    metadata = p0_driver._generation_metadata(attempt)
    return {
        "generation_id": cell["generation_id"],
        "run_id": frozen.RUN_ID,
        "logical_run_id": frozen.RUN_ID,
        "cell_index": cell["cell_index"],
        "task_id": cell["task_id"],
        "seed": cell["seed"],
        "sample_index": cell["sample_index"],
        "treatment": "P1_Generic_Code_Scaffold_v0",
        "runner_treatment_adapter": "ab1_with_precomposed_frozen_prompt",
        "model": frozen.MODEL,
        "model_digest": frozen.MODEL_DIGEST,
        "quantization": frozen.QUANTIZATION,
        "official_prompt_sha256": cell["official_prompt_sha256"],
        "composed_prompt_sha256": cell["composed_prompt_sha256"],
        "scaffold_sha256": frozen.SCAFFOLD_SHA256,
        "separator_sha256": frozen.PROMPT_SEPARATOR_SHA256,
        "request": transport["request_payload"],
        "raw_response": raw_response,
        "raw_response_sha256": frozen.sha256_text(raw_response),
        "raw_http_response_body": transport["raw_body"],
        "generation_metadata": metadata,
        "generation_latency_seconds": attempt["generation_latency"],
        **state,
        "first_attempt": True,
        "source_attempt_status": attempt.get("status"),
        "source_failure_stage": attempt.get("failure_stage"),
        "recovered_from_existing_response": recovered_from_existing_response,
        "regeneration": False,
        "observed_account": True,
        "pipeline_correction_applied_during_generation": False,
        "retry_count": 0,
        "selective_retry": False,
        "resume": False,
        "healer": False,
    }


def _complete_raw_record(
    *,
    cell: dict[str, Any],
    task: PublicBenchmarkTask,
    official_prompt: str,
    composed_prompt: str,
    attempt: dict[str, Any],
) -> dict[str, Any] | None:
    _require(task.task_id == cell["task_id"], "task/cell identity mismatch")
    _require(
        frozen.sha256_text(official_prompt) == cell["official_prompt_sha256"],
        "official prompt SHA-256 mismatch",
    )
    _require(
        frozen.sha256_text(composed_prompt) == cell["composed_prompt_sha256"],
        "composed prompt SHA-256 mismatch",
    )
    return _raw_record_from_complete_attempt(
        cell=cell,
        attempt=attempt,
        recovered_from_existing_response=False,
    )


def generate(*, run_id: str, base_url: str, timeout_seconds: float) -> None:
    plan = load_frozen_plan()
    _require(timeout_seconds == frozen.GENERATION_TIMEOUT_SECONDS, "timeout must equal actual P0 run_003 value 600 seconds")
    output_dir = resolve_run_dir(run_id)
    if output_dir.exists():
        raise ScaffoldRunError(f"refusing retry/resume/overwrite of existing run directory: {output_dir}")

    path_preflight = preflight_storage_paths(plan, output_dir)

    protocol = load_generation_protocol(REPO_ROOT / frozen.PROTOCOL_RELATIVE)
    provenance = fetch_ollama_provenance(
        base_url,
        timeout_seconds,
        model=frozen.MODEL,
        expected_digest_prefix=frozen.MODEL_DIGEST,
    )
    _require(provenance["model_digest"] == frozen.MODEL_DIGEST, "installed model digest mismatch")
    durable_write_json_new(output_dir / "generation_plan.json", plan)

    tasks = _task_objects(plan)
    raw_records: list[dict[str, Any]] = []
    failed_cells: list[str] = []
    journal_dir = output_dir / "j"
    started = time.monotonic()
    for cell in plan["cells"]:
        task = tasks[cell["task_id"]]
        composed_prompt = frozen.compose_prompt(task.prompt)
        _require(frozen.sha256_text(task.prompt) == cell["official_prompt_sha256"], "official prompt hash mismatch")
        _require(frozen.sha256_text(composed_prompt) == cell["composed_prompt_sha256"], "composed prompt hash mismatch")
        _require(
            frozen.generation_id(task.task_id, cell["seed"], cell["composed_prompt_sha256"])
            == cell["generation_id"],
            "generation ID mismatch",
        )
        composed_task = PublicBenchmarkTask(
            benchmark="mbpp",
            task_id=task.task_id,
            prompt=composed_prompt,
            entry_point=task.entry_point,
            canonical_solution=None,
        )
        settings = protocol_settings(
            protocol, model_role="primary_development_model", seed=cell["seed"]
        )
        attempt = run_attempt(
            composed_task,
            "ab1",
            benchmark="mbpp",
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            settings=settings,
            model_digest=frozen.MODEL_DIGEST,
            sample_index=cell["sample_index"],
        )
        raw_record = _complete_raw_record(
            cell=cell,
            task=task,
            official_prompt=task.prompt,
            composed_prompt=composed_prompt,
            attempt=attempt,
        )
        if raw_record is None:
            failed_cells.append(cell["generation_id"])
            journal_record = {
                "generation_id": cell["generation_id"],
                "run_id": frozen.RUN_ID,
                "logical_run_id": frozen.RUN_ID,
                "cell_index": cell["cell_index"],
                "task_id": cell["task_id"],
                "seed": cell["seed"],
                "sample_index": cell["sample_index"],
                "status": "failed_single_attempt_no_retry",
                "attempt": attempt,
                "retry_count": 0,
                "selective_retry": False,
                "resume": False,
                "healer": False,
            }
        else:
            raw_records.append(raw_record)
            journal_record = raw_record
        _persist_attempt_journal(journal_dir, cell=cell, record=journal_record)
        print(
            f"cell {cell['cell_index']}/100 persisted: {cell['task_id']} seed={cell['seed']} "
            f"status={'complete' if raw_record else 'failed'}",
            flush=True,
        )

    if failed_cells or len(raw_records) != 100:
        raise ScaffoldRunError(
            f"generation incomplete after exactly one attempt per cell: complete={len(raw_records)} "
            f"failed={len(failed_cells)}; retry/resume/selective retry forbidden; evaluation forbidden"
        )
    _require(len({record["generation_id"] for record in raw_records}) == 100, "duplicate generation cell")
    durable_write_jsonl_new(output_dir / "raw_generations.jsonl", raw_records)
    pipeline_records = []
    for record in raw_records:
        pipeline_record = p0_driver.build_pipeline_record(record)
        pipeline_record["run_id"] = frozen.RUN_ID
        pipeline_record["logical_run_id"] = frozen.RUN_ID
        pipeline_records.append(pipeline_record)
    durable_write_jsonl_new(output_dir / "pipeline_corrected.jsonl", pipeline_records)
    print(
        json.dumps(
            {
                "generation": "100/100",
                "elapsed_seconds": round(time.monotonic() - started, 3),
                "pipeline_extracted": sum(
                    record["extraction_status"] == "extracted" for record in pipeline_records
                ),
                "protocol_violation_count": sum(
                    not record["protocol_compliant"] for record in raw_records
                ),
                "retry_count": 0,
                "healer": False,
                "storage_path_preflight": path_preflight,
            },
            sort_keys=True,
        ),
        flush=True,
    )


def _load_jsonl(path: pathlib.Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _official_check(args: tuple[Any, ...]) -> dict[str, Any]:
    from evalplus.evaluate import check_correctness

    return check_correctness(*args)


def evaluate(*, run_id: str, parallel: int) -> None:
    if os.name == "nt" or sys.platform.startswith("win"):
        raise ScaffoldRunError("evaluation must run inside WSL/Linux")
    frozen_plan = load_frozen_plan()
    output_dir = resolve_run_dir(run_id)
    results_path = output_dir / "evaluation_results.csv"
    summary_path = output_dir / "evaluation_summary.md"
    if results_path.exists() or summary_path.exists():
        raise ScaffoldRunError("refusing retry/resume/overwrite of existing evaluation outputs")
    run_plan_path = output_dir / "generation_plan.json"
    _require(run_plan_path.is_file(), "run generation plan missing")
    _require(run_plan_path.read_bytes() == frozen.render_json(frozen_plan), "run generation plan differs from frozen plan")

    raw_records = _load_jsonl(output_dir / "raw_generations.jsonl")
    pipeline_records = _load_jsonl(output_dir / "pipeline_corrected.jsonl")
    _require(len(raw_records) == len(pipeline_records) == 100, "evaluation requires exactly 100 records in both accounts")
    raw_by_id = {record["generation_id"]: record for record in raw_records}
    pipeline_by_id = {record["generation_id"]: record for record in pipeline_records}
    planned_ids = {cell["generation_id"] for cell in frozen_plan["cells"]}
    _require(len(raw_by_id) == len(pipeline_by_id) == 100, "duplicate evaluation account cell")
    _require(set(raw_by_id) == set(pipeline_by_id) == planned_ids, "Observed/Pipeline/planned identity mismatch")

    task_ids = frozen_plan["task_ids"]
    from evalplus.data import get_mbpp_plus, get_mbpp_plus_hash
    from evalplus.eval import PASS
    from evalplus.eval._special_oracle import MBPP_OUTPUT_NOT_NONE_TASKS
    from evalplus.evaluate import get_groundtruth

    all_problems = get_mbpp_plus(version="v0.2.0")
    problems = {task_id: all_problems[task_id] for task_id in task_ids}
    dataset_hash = get_mbpp_plus_hash(version="v0.2.0")
    _require(dataset_hash == frozen_plan["dataset_hash"], "official MBPP+ dataset hash mismatch")
    subset_cache_hash = dataset_hash + "-" + frozen.sha256_text("\n".join(task_ids))[:16]
    expected_output = get_groundtruth(problems, subset_cache_hash, MBPP_OUTPUT_NOT_NONE_TASKS)

    jobs: dict[Any, tuple[str, str]] = {}
    direct: dict[tuple[str, str], dict[str, Any]] = {}
    with ProcessPoolExecutor(max_workers=max(1, parallel)) as executor:
        for cell in frozen_plan["cells"]:
            generation_id = cell["generation_id"]
            raw = raw_by_id[generation_id]
            pipeline = pipeline_by_id[generation_id]
            task_id = raw["task_id"]
            for account, completion in (
                ("observed", raw["raw_response"]),
                ("pipeline_corrected", pipeline["pipeline_corrected_output"]),
            ):
                key = (generation_id, account)
                if completion is None:
                    direct[key] = {
                        "base_status": "not_run_extraction_failed",
                        "plus_status": "not_run_extraction_failed",
                    }
                    continue
                solution = problems[task_id]["prompt"] + completion
                args = (
                    "mbpp",
                    raw["sample_index"],
                    problems[task_id],
                    solution,
                    expected_output[task_id],
                    False,
                    True,
                    f"{generation_id}:{account}",
                )
                jobs[executor.submit(_official_check, args)] = key
        for future in as_completed(jobs):
            result = future.result()
            direct[jobs[future]] = {
                "base_status": result["base"][0],
                "plus_status": result["plus"][0],
            }

    evaluator_version = importlib.metadata.version("evalplus")
    fieldnames = [
        "run_id",
        "task_id",
        "seed",
        "generation_id",
        "treatment",
        "observed_status",
        "pipeline_corrected_status",
        "observed_syntax_compile_status",
        "pipeline_corrected_syntax_compile_status",
        "observed_runtime_timeout_status",
        "pipeline_corrected_runtime_timeout_status",
        "observed_evalplus_pass",
        "pipeline_corrected_evalplus_pass",
        "observed_output_sha256",
        "pipeline_corrected_output_sha256",
        "scaffold_sha256",
        "evaluator_version",
        "evaluator_engine",
    ]
    csv_rows: list[dict[str, Any]] = []
    for cell in frozen_plan["cells"]:
        generation_id = cell["generation_id"]
        raw = raw_by_id[generation_id]
        pipeline = pipeline_by_id[generation_id]
        observed_eval = direct[(generation_id, "observed")]
        pipeline_eval = direct[(generation_id, "pipeline_corrected")]
        observed_pass = observed_eval["base_status"] == observed_eval["plus_status"] == PASS
        pipeline_pass = pipeline_eval["base_status"] == pipeline_eval["plus_status"] == PASS
        corrected = pipeline["pipeline_corrected_output"]
        csv_rows.append(
            {
                "run_id": frozen.RUN_ID,
                "task_id": raw["task_id"],
                "seed": raw["seed"],
                "generation_id": generation_id,
                "treatment": "P1_Generic_Code_Scaffold_v0",
                "observed_status": "pass" if observed_pass else "fail",
                "pipeline_corrected_status": "pass" if pipeline_pass else "fail",
                "observed_syntax_compile_status": p0_driver._compile_status(
                    problems[raw["task_id"]]["prompt"] + raw["raw_response"]
                ),
                "pipeline_corrected_syntax_compile_status": (
                    p0_driver._compile_status(problems[raw["task_id"]]["prompt"] + corrected)
                    if corrected is not None
                    else "not_run_extraction_failed"
                ),
                "observed_runtime_timeout_status": p0_driver._runtime_status(
                    observed_eval["base_status"], observed_eval["plus_status"]
                ),
                "pipeline_corrected_runtime_timeout_status": p0_driver._runtime_status(
                    pipeline_eval["base_status"], pipeline_eval["plus_status"]
                ),
                "observed_evalplus_pass": str(observed_pass).lower(),
                "pipeline_corrected_evalplus_pass": str(pipeline_pass).lower(),
                "observed_output_sha256": raw["raw_response_sha256"],
                "pipeline_corrected_output_sha256": pipeline["pipeline_corrected_output_sha256"] or "",
                "scaffold_sha256": frozen.SCAFFOLD_SHA256,
                "evaluator_version": evaluator_version,
                "evaluator_engine": EVALUATOR_ENGINE,
            }
        )
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(csv_rows)
    durable_write_text_new(results_path, buffer.getvalue())

    observed_pass_count = sum(row["observed_evalplus_pass"] == "true" for row in csv_rows)
    pipeline_pass_count = sum(row["pipeline_corrected_evalplus_pass"] == "true" for row in csv_rows)
    summary = (
        "# MBPP+ Qwen3.5 9B Generic Code Scaffold v0 development evaluation\n\n"
        f"- Logical run ID: `{frozen.RUN_ID}`\n"
        f"- Generation cells: 100\n"
        f"- Observed: {observed_pass_count} pass / {100 - observed_pass_count} fail\n"
        f"- Pipeline-corrected: {pipeline_pass_count} pass / {100 - pipeline_pass_count} fail\n"
        f"- Evaluator: EvalPlus {evaluator_version}, `{EVALUATOR_ENGINE}`\n"
        f"- Scaffold SHA-256: `{frozen.SCAFFOLD_SHA256}`\n"
        "- Healer: disabled; Pipeline correction is accounted separately and is not Healer.\n"
    )
    durable_write_text_new(summary_path, summary)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    generation = commands.add_parser("generate")
    generation.add_argument("--run-id", required=True)
    generation.add_argument("--base-url", default=DEFAULT_BASE_URL)
    generation.add_argument(
        "--timeout-seconds", type=float, default=frozen.GENERATION_TIMEOUT_SECONDS
    )
    evaluation = commands.add_parser("evaluate")
    evaluation.add_argument("--run-id", required=True)
    evaluation.add_argument("--parallel", type=int, default=4)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "generate":
            generate(
                run_id=args.run_id,
                base_url=args.base_url,
                timeout_seconds=args.timeout_seconds,
            )
        else:
            evaluate(run_id=args.run_id, parallel=args.parallel)
    except (ScaffoldRunError, frozen.ScaffoldProtocolError, PersistenceError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
