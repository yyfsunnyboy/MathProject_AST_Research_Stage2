#!/usr/bin/env python3
"""Execute the frozen Milestone 2E expansion protocol in a future milestone."""

from __future__ import annotations

import argparse
import csv
import importlib.metadata
import io
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
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
from scripts import freeze_mbpp_candidate_a_expansion_protocol as frozen  # noqa: E402
from scripts import run_mbpp_development_baseline as baseline  # noqa: E402


TASKS_PATH = REPO_ROOT / "data/mbpp_plus/tasks.jsonl"
EVALUATOR_ENGINE = "evalplus_0.3.1_check_correctness_subset"
TREATMENTS = {
    "p0": {
        "treatment_id": frozen.P0_TREATMENT_ID,
        "run_id": frozen.P0_RUN_ID,
        "physical": frozen.P0_PHYSICAL,
        "plan_name": "p0_expansion_generation_plan.json",
    },
    "candidate_a": {
        "treatment_id": frozen.CA_TREATMENT_ID,
        "run_id": frozen.CA_RUN_ID,
        "physical": frozen.CA_PHYSICAL,
        "plan_name": "candidate_a_expansion_generation_plan.json",
    },
}


class ExpansionRunError(RuntimeError):
    """Raised before unsafe or non-protocol execution."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ExpansionRunError(message)


def _treatment(name: str) -> dict[str, Any]:
    _require(name in TREATMENTS, f"unknown treatment: {name}")
    return TREATMENTS[name]


def resolve_run_dir(treatment: str, run_id: str) -> Path:
    spec = _treatment(treatment)
    _require(run_id == spec["run_id"], "run ID differs from frozen treatment mapping")
    return REPO_ROOT / spec["physical"]


def load_frozen_plan(treatment: str) -> dict[str, Any]:
    spec = _treatment(treatment)
    outputs = frozen.frozen_outputs(REPO_ROOT)
    relative = Path(spec["plan_name"])
    committed = REPO_ROOT / frozen.OUTPUT_RELATIVE / relative
    _require(committed.is_file(), "frozen generation plan missing")
    _require(committed.read_bytes() == outputs[relative], "frozen generation plan drift")
    plan = json.loads(committed.read_text(encoding="utf-8"))
    _require(plan["run_id"] == spec["run_id"], "plan run ID mismatch")
    _require(plan["treatment_id"] == spec["treatment_id"], "plan treatment mismatch")
    _require(plan["expected_cells"] == len(plan["cells"]) == 200, "plan must have 200 cells")
    _require(plan["task_count"] == len(plan["task_ids"]) == 40, "plan must have 40 tasks")
    _require(not any(plan[key] for key in ("retry", "resume", "selective_retry", "overwrite", "healer")), "forbidden policy enabled")
    _require(plan["attempts_per_cell"] == 1, "exactly one attempt is required")
    _require(plan["pipeline_correction_is_healer"] is False, "Pipeline correction is not Healer")
    return plan


def preflight() -> dict[str, Any]:
    outputs = frozen.frozen_outputs(REPO_ROOT)
    for relative, expected in outputs.items():
        path = REPO_ROOT / frozen.OUTPUT_RELATIVE / relative
        _require(path.is_file() and path.read_bytes() == expected, f"frozen output drift: {relative}")
    p0 = load_frozen_plan("p0")
    candidate = load_frozen_plan("candidate_a")
    _require(
        [(cell["task_id"], cell["seed"]) for cell in p0["cells"]]
        == [(cell["task_id"], cell["seed"]) for cell in candidate["cells"]],
        "paired schedule mismatch",
    )
    storage = frozen.build_storage_mapping(p0, candidate)
    _require(all(run["within_budget"] for run in storage["runs"]), "path budget failure")
    return {
        "status": "preflight_ok_no_model_call",
        "p0_cells": len(p0["cells"]),
        "candidate_a_cells": len(candidate["cells"]),
        "paired_identities": len(p0["cells"]),
        "windows_path_budget": storage["windows_path_budget_chars"],
        "max_path_length": max(run["longest_windows_path_length"] for run in storage["runs"]),
    }


def _load_tasks(task_ids: list[str]) -> dict[str, PublicBenchmarkTask]:
    selected = set(task_ids)
    found: dict[str, PublicBenchmarkTask] = {}
    with TASKS_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("task_id") not in selected:
                continue
            _require(set(record) == {"task_id", "prompt", "entry_point"}, "model-visible schema drift")
            found[record["task_id"]] = PublicBenchmarkTask(
                benchmark="mbpp",
                task_id=record["task_id"],
                prompt=record["prompt"],
                entry_point=record["entry_point"],
                canonical_solution=None,
            )
    _require(set(found) == selected, "frozen expansion task missing from model-visible file")
    return found


def _composed_prompt(plan: dict[str, Any], official_prompt: str) -> str:
    if plan["treatment_id"] == frozen.P0_TREATMENT_ID:
        return official_prompt
    _require(plan["candidate_exact_text_sha256"] == frozen.CANDIDATE_SHA256, "candidate hash drift")
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
    _require(request.get("model") == frozen.MODEL and request.get("think") is False, "request protocol drift")
    expected_prompt = _composed_prompt(plan, task.prompt)
    _require(request.get("messages") == [{"role": "user", "content": expected_prompt}], "prompt composition drift")
    violations = []
    if detect_reasoning_leakage(body, raw):
        violations.append("reasoning_leakage_in_message_content")
    return {
        "generation_id": cell["planned_cell_id"],
        "planned_cell_id": cell["planned_cell_id"],
        "run_id": plan["run_id"],
        "logical_run_id": plan["run_id"],
        "cell_index": cell["cell_index"],
        "task_id": cell["task_id"],
        "seed": cell["seed"],
        "sample_index": cell["sample_index"],
        "model": frozen.MODEL,
        "model_digest": frozen.MODEL_DIGEST,
        "official_prompt_sha256": frozen.sha256_text(task.prompt),
        "composed_prompt_sha256": frozen.sha256_text(expected_prompt),
        "request": request,
        "raw_response": raw,
        "raw_response_sha256": frozen.sha256_text(raw),
        "raw_http_response_body": transport["raw_body"],
        "generation_metadata": baseline._generation_metadata(attempt),
        "generation_latency_seconds": attempt["generation_latency"],
        "transport_complete": True,
        "model_generation_complete": True,
        "generation_complete": True,
        "protocol_compliant": not violations,
        "protocol_violations": violations,
        "reasoning_leakage": bool(violations),
        "first_attempt": True,
        "retry_count": 0,
        "resume": False,
        "selective_retry": False,
        "healer": False,
        "observed_account": True,
        "pipeline_correction_applied_during_generation": False,
    }


def generate(*, treatment: str, run_id: str, base_url: str, timeout_seconds: float) -> None:
    plan = load_frozen_plan(treatment)
    _require(timeout_seconds == frozen.TIMEOUT_SECONDS, "timeout must be exactly 600 seconds")
    run_dir = resolve_run_dir(treatment, run_id)
    _require(not run_dir.exists(), "run directory already exists; retry/resume/overwrite forbidden")
    preflight_result = preflight()
    protocol = load_generation_protocol(REPO_ROOT / frozen.GENERATION_PROTOCOL)
    provenance = fetch_ollama_provenance(
        base_url,
        timeout_seconds,
        model=frozen.MODEL,
        expected_digest_prefix=frozen.MODEL_DIGEST,
    )
    _require(provenance["model_digest"] == frozen.MODEL_DIGEST, "installed model digest mismatch")
    durable_write_json_new(run_dir / "generation_plan.json", plan)
    tasks = _load_tasks(plan["task_ids"])
    raw_records: list[dict[str, Any]] = []
    failed: list[str] = []
    started = time.monotonic()
    for cell in plan["cells"]:
        task = tasks[cell["task_id"]]
        prompt = _composed_prompt(plan, task.prompt)
        generated_task = PublicBenchmarkTask(
            benchmark="mbpp",
            task_id=task.task_id,
            prompt=prompt,
            entry_point=task.entry_point,
            canonical_solution=None,
        )
        settings = protocol_settings(protocol, model_role="primary_development_model", seed=cell["seed"])
        attempt = run_attempt(
            generated_task,
            "ab1",
            benchmark="mbpp",
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            settings=settings,
            model_digest=frozen.MODEL_DIGEST,
            sample_index=cell["sample_index"],
        )
        record = _attempt_record(plan, cell, task, attempt)
        if record is None:
            failed.append(cell["planned_cell_id"])
            journal = {
                "planned_cell_id": cell["planned_cell_id"],
                "run_id": plan["run_id"],
                "task_id": cell["task_id"],
                "seed": cell["seed"],
                "status": "failed_single_attempt_no_retry",
                "attempt": attempt,
                "retry_count": 0,
                "healer": False,
            }
        else:
            raw_records.append(record)
            journal = record
        durable_write_json_new(run_dir / frozen.JOURNAL_DIRECTORY / f"{cell['planned_cell_id']}.json", journal)
        print(f"cell {cell['cell_index']}/200 persisted: {cell['task_id']} seed={cell['seed']}", flush=True)
    if failed or len(raw_records) != 200:
        raise ExpansionRunError(
            f"single-attempt generation incomplete: complete={len(raw_records)} failed={len(failed)}; evaluation forbidden"
        )
    durable_write_jsonl_new(run_dir / "raw_generations.jsonl", raw_records)
    pipeline = []
    for record in raw_records:
        item = baseline.build_pipeline_record(record)
        item["run_id"] = plan["run_id"]
        item["logical_run_id"] = plan["run_id"]
        pipeline.append(item)
    durable_write_jsonl_new(run_dir / "pipeline_corrected.jsonl", pipeline)
    print(
        json.dumps(
            {
                "generation": "200/200",
                "elapsed_seconds": round(time.monotonic() - started, 3),
                "protocol_violations_in_itt": sum(not row["protocol_compliant"] for row in raw_records),
                "retry_count": 0,
                "healer": False,
                "preflight": preflight_result,
            },
            sort_keys=True,
        ),
        flush=True,
    )


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _official_check(args: tuple[Any, ...]) -> dict[str, Any]:
    from evalplus.evaluate import check_correctness

    return check_correctness(*args)


def evaluate(*, treatment: str, run_id: str, parallel: int) -> None:
    _require(os.name != "nt" and not sys.platform.startswith("win"), "evaluation must run inside WSL/Linux")
    plan = load_frozen_plan(treatment)
    run_dir = resolve_run_dir(treatment, run_id)
    results_path = run_dir / "evaluation_results.csv"
    summary_path = run_dir / "evaluation_summary.md"
    _require(not results_path.exists() and not summary_path.exists(), "evaluation overwrite forbidden")
    _require((run_dir / "generation_plan.json").read_bytes() == frozen.render_json(plan), "run plan drift")
    raw_rows = _read_jsonl(run_dir / "raw_generations.jsonl")
    pipeline_rows = _read_jsonl(run_dir / "pipeline_corrected.jsonl")
    _require(len(raw_rows) == len(pipeline_rows) == 200, "evaluation requires 200 records per account")
    raw_by_id = {row["generation_id"]: row for row in raw_rows}
    pipe_by_id = {row["generation_id"]: row for row in pipeline_rows}
    planned = {cell["planned_cell_id"] for cell in plan["cells"]}
    _require(set(raw_by_id) == set(pipe_by_id) == planned and len(planned) == 200, "evaluation identity mismatch")

    from evalplus.data import get_mbpp_plus, get_mbpp_plus_hash
    from evalplus.eval import PASS
    from evalplus.eval._special_oracle import MBPP_OUTPUT_NOT_NONE_TASKS
    from evalplus.evaluate import get_groundtruth

    all_problems = get_mbpp_plus(version=frozen.DATASET_VERSION)
    problems = {task_id: all_problems[task_id] for task_id in plan["task_ids"]}
    dataset_hash = get_mbpp_plus_hash(version=frozen.DATASET_VERSION)
    _require(dataset_hash == plan["dataset_hash"], "official dataset hash drift")
    cache_hash = dataset_hash + "-" + frozen.sha256_text("\n".join(plan["task_ids"]))[:16]
    expected = get_groundtruth(problems, cache_hash, MBPP_OUTPUT_NOT_NONE_TASKS)
    jobs: dict[Any, tuple[str, str]] = {}
    outcomes: dict[tuple[str, str], dict[str, str]] = {}
    with ProcessPoolExecutor(max_workers=max(1, parallel)) as executor:
        for generation_id, raw in raw_by_id.items():
            for account, completion in (
                ("observed", raw["raw_response"]),
                ("pipeline_corrected", pipe_by_id[generation_id]["pipeline_corrected_output"]),
            ):
                key = (generation_id, account)
                if completion is None:
                    outcomes[key] = {"base": "not_run_extraction_failed", "plus": "not_run_extraction_failed"}
                    continue
                task_id = raw["task_id"]
                args = (
                    "mbpp",
                    raw["sample_index"],
                    problems[task_id],
                    problems[task_id]["prompt"] + completion,
                    expected[task_id],
                    False,
                    True,
                    f"{generation_id}:{account}",
                )
                jobs[executor.submit(_official_check, args)] = key
        for future in as_completed(jobs):
            value = future.result()
            outcomes[jobs[future]] = {"base": value["base"][0], "plus": value["plus"][0]}

    evaluator_version = importlib.metadata.version("evalplus")
    fields = [
        "run_id", "treatment_id", "task_id", "seed", "generation_id",
        "observed_status", "pipeline_corrected_status",
        "observed_syntax_compile_status", "pipeline_corrected_syntax_compile_status",
        "observed_runtime_timeout_status", "pipeline_corrected_runtime_timeout_status",
        "observed_output_sha256", "pipeline_corrected_output_sha256",
        "protocol_compliant", "reasoning_leakage", "evaluator_version", "evaluator_engine",
    ]
    result_rows = []
    for cell in plan["cells"]:
        generation_id = cell["planned_cell_id"]
        raw = raw_by_id[generation_id]
        pipe = pipe_by_id[generation_id]
        observed = outcomes[(generation_id, "observed")]
        corrected = outcomes[(generation_id, "pipeline_corrected")]
        observed_pass = observed["base"] == observed["plus"] == PASS
        corrected_pass = corrected["base"] == corrected["plus"] == PASS
        corrected_source = pipe["pipeline_corrected_output"]
        result_rows.append(
            {
                "run_id": plan["run_id"],
                "treatment_id": plan["treatment_id"],
                "task_id": raw["task_id"],
                "seed": raw["seed"],
                "generation_id": generation_id,
                "observed_status": "pass" if observed_pass else "fail",
                "pipeline_corrected_status": "pass" if corrected_pass else "fail",
                "observed_syntax_compile_status": baseline._compile_status(problems[raw["task_id"]]["prompt"] + raw["raw_response"]),
                "pipeline_corrected_syntax_compile_status": (
                    baseline._compile_status(problems[raw["task_id"]]["prompt"] + corrected_source)
                    if corrected_source is not None else "not_run_extraction_failed"
                ),
                "observed_runtime_timeout_status": baseline._runtime_status(observed["base"], observed["plus"]),
                "pipeline_corrected_runtime_timeout_status": baseline._runtime_status(corrected["base"], corrected["plus"]),
                "observed_output_sha256": raw["raw_response_sha256"],
                "pipeline_corrected_output_sha256": pipe["pipeline_corrected_output_sha256"] or "",
                "protocol_compliant": str(raw["protocol_compliant"]).lower(),
                "reasoning_leakage": str(raw["reasoning_leakage"]).lower(),
                "evaluator_version": evaluator_version,
                "evaluator_engine": EVALUATOR_ENGINE,
            }
        )
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(result_rows)
    durable_write_text_new(results_path, buffer.getvalue())
    observed_count = sum(row["observed_status"] == "pass" for row in result_rows)
    corrected_count = sum(row["pipeline_corrected_status"] == "pass" for row in result_rows)
    leakage_count = sum(row["reasoning_leakage"] == "true" for row in result_rows)
    durable_write_text_new(
        summary_path,
        (
            f"# {plan['treatment_id']} expansion evaluation\n\n"
            f"- Cells: 200\n- Observed pass: {observed_count}\n"
            f"- Pipeline-corrected pass: {corrected_count}\n"
            f"- Reasoning leakage (separate ITT metric): {leakage_count}\n"
            "- Healer disabled; Pipeline correction is not Healer.\n"
        ),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("preflight")
    generation = commands.add_parser("generate")
    generation.add_argument("--treatment", choices=sorted(TREATMENTS), required=True)
    generation.add_argument("--run-id", required=True)
    generation.add_argument("--base-url", default=DEFAULT_BASE_URL)
    generation.add_argument("--timeout-seconds", type=float, default=frozen.TIMEOUT_SECONDS)
    evaluation = commands.add_parser("evaluate")
    evaluation.add_argument("--treatment", choices=sorted(TREATMENTS), required=True)
    evaluation.add_argument("--run-id", required=True)
    evaluation.add_argument("--parallel", type=int, default=4)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "preflight":
            print(json.dumps(preflight(), indent=2, sort_keys=True))
        elif args.command == "generate":
            generate(
                treatment=args.treatment,
                run_id=args.run_id,
                base_url=args.base_url,
                timeout_seconds=args.timeout_seconds,
            )
        else:
            evaluate(
                treatment=args.treatment,
                run_id=args.run_id,
                parallel=args.parallel,
            )
    except (ExpansionRunError, PersistenceError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
