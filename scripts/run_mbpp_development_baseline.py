"""Generate and evaluate the frozen 20-task MBPP+ Ab1 development baseline."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import os
import pathlib
import re
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Sequence

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
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
from agent_tools.finals_rebuild.ollama_generation_runner import (  # noqa: E402
    DEFAULT_BASE_URL,
    fetch_ollama_provenance,
    load_generation_protocol,
    protocol_settings,
    run_attempt,
)

FROZEN_SPLIT = REPO_ROOT / "artifacts/public_benchmark_governance/frozen_split.csv"
TASKS_PATH = REPO_ROOT / "data/mbpp_plus/tasks.jsonl"
DATASET_MANIFEST = REPO_ROOT / "data/mbpp_plus/dataset_manifest.json"
PROTOCOL_PATH = REPO_ROOT / "configs/public_benchmark_generation_protocol_v1.json"
OUTPUT_ROOT = REPO_ROOT / "artifacts/public_benchmark_development/mbpp_qwen35_9b_ab1"

EXPECTED_MODEL = "qwen3.5:9b"
EXPECTED_DIGEST = "6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7"
EXPECTED_TASK_COUNT = 20
EXPECTED_CELL_COUNT = 100
EXPECTED_SEEDS = [11, 22, 33, 44, 55]
EXTRACTION_SPEC_COMMIT = "c5094bb7"
EVALUATOR_ENGINE = "evalplus_0.3.1_check_correctness_subset"


class BaselineError(RuntimeError):
    pass


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def _load_jsonl(path: pathlib.Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def resolve_run_dir(run_id: str) -> pathlib.Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", run_id):
        raise BaselineError("run_id must contain only letters, digits, dot, underscore, or hyphen")
    return OUTPUT_ROOT / "runs" / run_id


def load_active_task_rows(path: pathlib.Path = FROZEN_SPLIT) -> List[Dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = [
            row
            for row in csv.DictReader(handle)
            if row["dataset"] == "MBPP+"
            and row["proposed_role"] == "historical_development_pool"
            and row["active_development_generation_subset"].lower() == "true"
        ]
    task_ids = [row["task_id"] for row in rows]
    if len(rows) != EXPECTED_TASK_COUNT or len(set(task_ids)) != EXPECTED_TASK_COUNT:
        raise BaselineError(f"expected 20 unique active MBPP+ tasks, got {len(rows)}")
    if any(row["confirmatory_eligible"].lower() != "false" for row in rows):
        raise BaselineError("active development subset contains confirmatory-eligible task")
    return rows


def load_selected_tasks(
    selected_ids: Sequence[str], path: pathlib.Path = TASKS_PATH
) -> List[PublicBenchmarkTask]:
    selected = set(selected_ids)
    found: Dict[str, PublicBenchmarkTask] = {}
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            record = json.loads(line)
            task_id = record.get("task_id")
            if task_id not in selected:
                continue
            if set(record) != {"task_id", "prompt", "entry_point"}:
                raise BaselineError(f"{path}:{line_no}: unexpected model-visible fields")
            found[task_id] = PublicBenchmarkTask(
                benchmark="mbpp",
                task_id=task_id,
                prompt=record["prompt"],
                entry_point=record["entry_point"],
                canonical_solution=None,
            )
    missing = [task_id for task_id in selected_ids if task_id not in found]
    if missing:
        raise BaselineError(f"selected task IDs missing from model-visible tasks file: {missing}")
    return [found[task_id] for task_id in selected_ids]


def verify_dataset_manifest() -> Dict[str, Any]:
    manifest = json.loads(DATASET_MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("evalplus_package_version") != "0.3.1":
        raise BaselineError("MBPP+ manifest EvalPlus version drift")
    if manifest.get("release_tag_or_dataset_version") != "v0.2.0":
        raise BaselineError("MBPP+ dataset version drift")
    if manifest.get("tasks_sha256") != sha256_bytes(TASKS_PATH.read_bytes()):
        raise BaselineError("model-visible MBPP+ tasks file hash drift")
    if manifest.get("official_tests_and_canonical_solutions_included") is not False:
        raise BaselineError("model-visible task file must exclude tests and answers")
    return manifest


def generation_id(task_id: str, seed: int, protocol_hash: str) -> str:
    material = f"mbpp_qwen35_9b_ab1|{task_id}|{seed}|{EXPECTED_DIGEST}|{protocol_hash}"
    return sha256_text(material)


def _generation_metadata(attempt: Dict[str, Any]) -> Dict[str, Any]:
    transport = attempt.get("ollama_response_metadata")
    if not isinstance(transport, dict) or not isinstance(transport.get("raw_body"), str):
        raise BaselineError("generation response metadata/raw body missing")
    parsed = json.loads(transport["raw_body"])
    fields = (
        "model",
        "created_at",
        "done",
        "done_reason",
        "total_duration",
        "load_duration",
        "prompt_eval_count",
        "prompt_eval_duration",
        "eval_count",
        "eval_duration",
    )
    missing = [field for field in fields if field not in parsed]
    if missing:
        raise BaselineError(f"generation metadata missing fields: {missing}")
    return {field: parsed[field] for field in fields}


def build_pipeline_record(raw_record: Dict[str, Any]) -> Dict[str, Any]:
    extraction = extract_code(raw_record["raw_response"])
    corrected = extraction.extracted_code if extraction.extraction_status == "extracted" else None
    return {
        "generation_id": raw_record["generation_id"],
        "task_id": raw_record["task_id"],
        "seed": raw_record["seed"],
        "sample_index": raw_record["sample_index"],
        "source_raw_response_sha256": raw_record["raw_response_sha256"],
        "pipeline_correction_spec": "agent_tools.finals_rebuild.extraction.extract_code",
        "pipeline_correction_spec_commit": EXTRACTION_SPEC_COMMIT,
        "extraction_status": extraction.extraction_status,
        "extraction_method": extraction.extraction_method,
        "pipeline_corrected_output": corrected,
        "pipeline_corrected_output_sha256": sha256_text(corrected) if corrected is not None else None,
        "changed_from_observed": corrected != raw_record["raw_response"] if corrected is not None else None,
    }


def generate(*, run_id: str, base_url: str, timeout_seconds: float) -> None:
    output_dir = resolve_run_dir(run_id)
    if output_dir.exists() and any(output_dir.iterdir()):
        raise BaselineError(f"refusing to overwrite non-empty output directory: {output_dir}")
    rows = load_active_task_rows()
    task_ids = [row["task_id"] for row in rows]
    tasks = load_selected_tasks(task_ids)
    dataset_manifest = verify_dataset_manifest()
    protocol = load_generation_protocol(PROTOCOL_PATH)
    protocol_hash = sha256_bytes(PROTOCOL_PATH.read_bytes())
    primary = protocol["models"]["primary_development_model"]
    if primary["tag"] != EXPECTED_MODEL or primary["digest"] != EXPECTED_DIGEST:
        raise BaselineError("primary model identity differs from Milestone 1B")
    provenance = fetch_ollama_provenance(
        base_url,
        timeout_seconds,
        model=EXPECTED_MODEL,
        expected_digest_prefix=EXPECTED_DIGEST,
    )
    if provenance["model_digest"] != EXPECTED_DIGEST:
        raise BaselineError("installed qwen3.5:9b digest mismatch")

    plan = {
        "run_id": run_id,
        "experiment": "mbpp_qwen35_9b_ab1_active_development_v1",
        "dataset": "MBPP+",
        "dataset_version": dataset_manifest["release_tag_or_dataset_version"],
        "dataset_hash": dataset_manifest["evalplus_dataset_hash"],
        "frozen_split_sha256": sha256_bytes(FROZEN_SPLIT.read_bytes()),
        "selection_policy": "frozen historical_development_pool active subset only",
        "task_count": len(tasks),
        "task_ids": task_ids,
        "model": EXPECTED_MODEL,
        "model_digest": EXPECTED_DIGEST,
        "protocol_sha256": protocol_hash,
        "treatment": "Ab1",
        "prompt_policy": "official_prompt_verbatim",
        "samples_per_task": 5,
        "seeds": EXPECTED_SEEDS,
        "expected_cells": EXPECTED_CELL_COUNT,
        "retry": False,
        "resume": False,
        "overwrite": False,
        "scaffold": False,
        "healer": False,
        "post_healer_account": False,
        "evaluator_feedback_to_model": False,
        "pipeline_correction_spec": "agent_tools.finals_rebuild.extraction.extract_code",
        "pipeline_correction_spec_commit": EXTRACTION_SPEC_COMMIT,
    }
    durable_write_json_new(output_dir / "generation_plan.json", plan)
    journal_dir = output_dir / "generation_journal"

    raw_records: List[Dict[str, Any]] = []
    started = time.monotonic()
    cell_number = 0
    for task in tasks:
        prompt_hash = sha256_text(task.prompt)
        for sample_index, seed in enumerate(EXPECTED_SEEDS):
            cell_number += 1
            settings = protocol_settings(
                protocol, model_role="primary_development_model", seed=seed
            )
            attempt = run_attempt(
                task,
                "ab1",
                benchmark="mbpp",
                base_url=base_url,
                timeout_seconds=timeout_seconds,
                settings=settings,
                model_digest=EXPECTED_DIGEST,
                sample_index=sample_index,
            )
            raw_response = attempt.get("raw_response")
            transport = attempt.get("ollama_response_metadata")
            request = transport.get("request_payload") if isinstance(transport, dict) else None
            complete = (
                isinstance(raw_response, str)
                and bool(raw_response.strip())
                and isinstance(request, dict)
                and request.get("think") is False
                and request.get("model") == EXPECTED_MODEL
                and request.get("messages") == [{"role": "user", "content": task.prompt}]
            )
            if not complete:
                print(f"cell {cell_number}/100 incomplete: {task.task_id} seed={seed}", flush=True)
                continue
            metadata = _generation_metadata(attempt)
            raw_record = {
                    "generation_id": generation_id(task.task_id, seed, protocol_hash),
                    "task_id": task.task_id,
                    "seed": seed,
                    "sample_index": sample_index,
                    "model": EXPECTED_MODEL,
                    "model_digest": EXPECTED_DIGEST,
                    "prompt_sha256": prompt_hash,
                    "request": request,
                    "raw_response": raw_response,
                    "raw_response_sha256": sha256_text(raw_response),
                    "raw_http_response_body": transport["raw_body"],
                    "generation_metadata": metadata,
                    "generation_latency_seconds": attempt["generation_latency"],
                    "observed_account": True,
                    "pipeline_correction_applied_during_generation": False,
                    "retry_count": 0,
                }
            durable_write_json_new(
                journal_dir / f"{raw_record['generation_id']}.json", raw_record
            )
            raw_records.append(raw_record)
            print(f"cell {cell_number}/100 complete: {task.task_id} seed={seed}", flush=True)

    if len(raw_records) != EXPECTED_CELL_COUNT:
        raise BaselineError(f"generation incomplete: {len(raw_records)}/100; evaluation forbidden")
    keys = {(record["task_id"], record["seed"]) for record in raw_records}
    if len(keys) != EXPECTED_CELL_COUNT:
        raise BaselineError("duplicate generation cell detected")
    durable_write_jsonl_new(output_dir / "raw_generations.jsonl", raw_records)
    pipeline_records = [build_pipeline_record(record) for record in raw_records]
    durable_write_jsonl_new(
        output_dir / "pipeline_corrected.jsonl", pipeline_records
    )
    print(
        json.dumps(
            {
                "generation": "100/100",
                "elapsed_seconds": round(time.monotonic() - started, 3),
                "pipeline_extracted": sum(
                    record["extraction_status"] == "extracted" for record in pipeline_records
                ),
            },
            sort_keys=True,
        ),
        flush=True,
    )


def _compile_status(source: str) -> str:
    try:
        compile(source, "<mbpp-development-cell>", "exec")
    except (SyntaxError, ValueError, OverflowError):
        return "fail"
    return "pass"


def _official_check(args: tuple) -> Dict[str, Any]:
    from evalplus.evaluate import check_correctness

    return check_correctness(*args)


def _runtime_status(base_status: str, plus_status: str) -> str:
    joined = f"{base_status} {plus_status}".lower()
    if "timeout" in joined:
        return "timeout"
    if base_status == "pass" and plus_status == "pass":
        return "success"
    return "failure"


def evaluate(*, run_id: str, parallel: int) -> None:
    if os.name == "nt" or sys.platform.startswith("win"):
        raise BaselineError("evaluation must run inside WSL/Linux")
    output_dir = resolve_run_dir(run_id)
    results_path = output_dir / "evaluation_results.csv"
    summary_path = output_dir / "failure_census_summary.md"
    if results_path.exists() or summary_path.exists():
        raise BaselineError("refusing to overwrite existing evaluation outputs")
    raw_records = _load_jsonl(output_dir / "raw_generations.jsonl")
    pipeline_records = _load_jsonl(output_dir / "pipeline_corrected.jsonl")
    if len(raw_records) != EXPECTED_CELL_COUNT or len(pipeline_records) != EXPECTED_CELL_COUNT:
        raise BaselineError("evaluation requires exactly 100 records in both accounts")
    raw_by_id = {record["generation_id"]: record for record in raw_records}
    pipeline_by_id = {record["generation_id"]: record for record in pipeline_records}
    if set(raw_by_id) != set(pipeline_by_id) or len(raw_by_id) != EXPECTED_CELL_COUNT:
        raise BaselineError("Observed/Pipeline-corrected account identity mismatch")

    plan = json.loads((output_dir / "generation_plan.json").read_text(encoding="utf-8"))
    if plan.get("run_id") != run_id:
        raise BaselineError("generation plan run_id mismatch")
    task_ids = plan["task_ids"]
    from evalplus.data import get_mbpp_plus, get_mbpp_plus_hash
    from evalplus.eval import PASS
    from evalplus.eval._special_oracle import MBPP_OUTPUT_NOT_NONE_TASKS
    from evalplus.evaluate import get_groundtruth

    all_problems = get_mbpp_plus(version="v0.2.0")
    problems = {task_id: all_problems[task_id] for task_id in task_ids}
    dataset_hash = get_mbpp_plus_hash(version="v0.2.0")
    if dataset_hash != plan["dataset_hash"]:
        raise BaselineError("WSL official MBPP+ dataset hash differs from generation plan")
    subset_cache_hash = dataset_hash + "-" + sha256_text("\n".join(task_ids))[:16]
    expected_output = get_groundtruth(
        problems, subset_cache_hash, MBPP_OUTPUT_NOT_NONE_TASKS
    )

    jobs: Dict[Any, tuple[str, str]] = {}
    direct: Dict[tuple[str, str], Dict[str, Any]] = {}
    with ProcessPoolExecutor(max_workers=max(1, parallel)) as executor:
        for generation_id_value, raw in raw_by_id.items():
            task_id = raw["task_id"]
            for account, completion in (
                ("observed", raw["raw_response"]),
                ("pipeline_corrected", pipeline_by_id[generation_id_value]["pipeline_corrected_output"]),
            ):
                key = (generation_id_value, account)
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
                    f"{generation_id_value}:{account}",
                )
                jobs[executor.submit(_official_check, args)] = key
        for future in as_completed(jobs):
            key = jobs[future]
            result = future.result()
            direct[key] = {
                "base_status": result["base"][0],
                "plus_status": result["plus"][0],
            }
            print(f"evaluated {len(direct)}/200", flush=True)

    evaluator_version = importlib.metadata.version("evalplus")
    fieldnames = [
        "task_id",
        "seed",
        "generation_id",
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
        "evaluator_version",
        "evaluator_engine",
    ]
    csv_rows: List[Dict[str, Any]] = []
    for raw in raw_records:
        generation_id_value = raw["generation_id"]
        pipeline = pipeline_by_id[generation_id_value]
        observed_eval = direct[(generation_id_value, "observed")]
        pipeline_eval = direct[(generation_id_value, "pipeline_corrected")]
        observed_pass = observed_eval["base_status"] == observed_eval["plus_status"] == PASS
        pipeline_pass = pipeline_eval["base_status"] == pipeline_eval["plus_status"] == PASS
        corrected = pipeline["pipeline_corrected_output"]
        csv_rows.append(
            {
                "task_id": raw["task_id"],
                "seed": raw["seed"],
                "generation_id": generation_id_value,
                "observed_status": "pass" if observed_pass else "fail",
                "pipeline_corrected_status": "pass" if pipeline_pass else "fail",
                "observed_syntax_compile_status": _compile_status(
                    problems[raw["task_id"]]["prompt"] + raw["raw_response"]
                ),
                "pipeline_corrected_syntax_compile_status": (
                    _compile_status(problems[raw["task_id"]]["prompt"] + corrected)
                    if corrected is not None
                    else "not_run_extraction_failed"
                ),
                "observed_runtime_timeout_status": _runtime_status(
                    observed_eval["base_status"], observed_eval["plus_status"]
                ),
                "pipeline_corrected_runtime_timeout_status": _runtime_status(
                    pipeline_eval["base_status"], pipeline_eval["plus_status"]
                ),
                "observed_evalplus_pass": str(observed_pass).lower(),
                "pipeline_corrected_evalplus_pass": str(pipeline_pass).lower(),
                "observed_output_sha256": raw["raw_response_sha256"],
                "pipeline_corrected_output_sha256": pipeline["pipeline_corrected_output_sha256"] or "",
                "evaluator_version": evaluator_version,
                "evaluator_engine": EVALUATOR_ENGINE,
            }
        )

    import io

    csv_buffer = io.StringIO(newline="")
    writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(csv_rows)
    durable_write_text_new(results_path, csv_buffer.getvalue())

    observed_pass_count = sum(row["observed_evalplus_pass"] == "true" for row in csv_rows)
    pipeline_pass_count = sum(
        row["pipeline_corrected_evalplus_pass"] == "true" for row in csv_rows
    )
    failed_tasks = {
        row["task_id"] for row in csv_rows if row["pipeline_corrected_evalplus_pass"] == "false"
    }
    pipeline_fail_count = EXPECTED_CELL_COUNT - pipeline_pass_count
    expansion_triggered = pipeline_fail_count < 20 or len(failed_tasks) < 5
    eval_counts = [record["generation_metadata"]["eval_count"] for record in raw_records]
    prompt_counts = [record["generation_metadata"]["prompt_eval_count"] for record in raw_records]
    durations = [record["generation_metadata"]["total_duration"] / 1_000_000_000 for record in raw_records]
    summary = (
        "# MBPP+ Qwen3.5 9B Ab1 Failure Census\n\n"
        f"- Generation: 100/100 across 20 tasks and seeds {EXPECTED_SEEDS}\n"
        f"- Observed: {observed_pass_count} pass / {100 - observed_pass_count} fail\n"
        f"- Pipeline-corrected: {pipeline_pass_count} pass / {pipeline_fail_count} fail\n"
        f"- Pipeline-corrected failures cover {len(failed_tasks)} unique task IDs\n"
        f"- Next-milestone expansion threshold triggered: {str(expansion_triggered).lower()}\n"
        f"- Evaluator: EvalPlus {evaluator_version}, `{EVALUATOR_ENGINE}`\n"
        f"- Prompt tokens: total {sum(prompt_counts)}, mean {sum(prompt_counts) / 100:.2f}\n"
        f"- Generated tokens: total {sum(eval_counts)}, mean {sum(eval_counts) / 100:.2f}\n"
        f"- Ollama generation duration: total {sum(durations):.3f}s, mean {sum(durations) / 100:.3f}s\n\n"
        "The expansion rule was fixed before evaluation: expand next milestone when "
        "Pipeline-corrected failures are fewer than 20 cells or cover fewer than 5 tasks. "
        "No expansion was executed in this milestone. No hidden test inputs, expected "
        "outputs, canonical solutions, or evaluator diagnostics are stored in repository artifacts.\n"
    )
    durable_write_text_new(summary_path, summary)
    print(
        json.dumps(
            {
                "observed_pass": observed_pass_count,
                "observed_fail": 100 - observed_pass_count,
                "pipeline_pass": pipeline_pass_count,
                "pipeline_fail": pipeline_fail_count,
                "failed_unique_tasks": len(failed_tasks),
                "expansion_triggered": expansion_triggered,
            },
            sort_keys=True,
        ),
        flush=True,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    generation_parser = subparsers.add_parser("generate")
    generation_parser.add_argument("--run-id", required=True)
    generation_parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    generation_parser.add_argument("--timeout-seconds", type=float, default=300.0)
    evaluation_parser = subparsers.add_parser("evaluate")
    evaluation_parser.add_argument("--run-id", required=True)
    evaluation_parser.add_argument("--parallel", type=int, default=4)
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
    except (BaselineError, PersistenceError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
