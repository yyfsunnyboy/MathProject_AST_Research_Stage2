"""Run the frozen Gemini Ab2d-local qualification only when explicitly enabled."""

from __future__ import annotations

import argparse
import json
import re
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_tools.finals_rebuild.ab2d_local_prompt import (
    assemble_ab2d_local_prompt,
    measure_prompt_size,
)
from agent_tools.finals_rebuild.math_answer_contracts import render_answer_contract
from agent_tools.finals_rebuild.math_task_oracles import evaluate_math_task_oracle
from agent_tools.finals_rebuild.math_task_sampler import sample_task_parameters
from scripts.run_gemini_ab2g_math_core_qualification import (
    EXECUTION_TIMEOUT_SECONDS,
    FAMILIES,
    MAX_OUTPUT_TOKENS,
    MODEL_TAG,
    REQUEST_TIMEOUT_SECONDS,
    SEED,
    _append,
    _apply_response,
    _client_call,
    _preset,
    _tasks,
    cloud_qualified,
)

PROMPT_CONDITION = "Ab2d-local"
RESULT = ROOT / "docs/experiments/results/gemini_ab2d_local_l1_seed_20260714_qualification.jsonl"
SUMMARY = ROOT / "docs/experiments/gemini_ab2d_local_l1_seed_20260714_qualification_summary.md"
API_LOOP_ENTERED = False


def _output_paths(run_id: str | None) -> tuple[Path, Path]:
    if run_id is None:
        return RESULT, SUMMARY
    if not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
        raise ValueError("--run-id must match [A-Za-z0-9_-]+")
    stem = f"gemini_ab2d_local_l1_seed_{run_id}"
    return (
        ROOT / "docs/experiments/results" / f"{stem}.jsonl",
        ROOT / "docs/experiments" / f"{stem}_summary.md",
    )


def _make_row(task: dict[str, Any]) -> dict[str, Any]:
    payload = sample_task_parameters(task, SEED)["oracle_payload"]
    contract = render_answer_contract(task, payload)
    prompt = assemble_ab2d_local_prompt(task["skill_id"], contract, payload)
    expected = evaluate_math_task_oracle(task["oracle_type"], payload, None).get("expected_answer")
    return {
        "task_family": task["skill_id"],
        "prompt_condition": PROMPT_CONDITION,
        "model_tag": MODEL_TAG,
        "seed": SEED,
        "difficulty": "L1",
        "task_id": task["task_id"],
        "task_parameters": payload,
        "oracle_expected": expected,
        "answer_contract": contract,
        "final_prompt": prompt,
        "prompt_size": measure_prompt_size(prompt),
        "request_count": 1,
        "retry_count": 0,
        "healer_used": False,
        "raw_first_attempt_output": None,
        "candidate_extracted": None,
        "parse_status": None,
        "evaluable": False,
        "oracle_pass": False,
        "failure_category": None,
        "failure_detail": None,
        "execution_timeout": None,
        "prompt_token_count": None,
        "output_token_count": None,
        "total_token_count": None,
        "wall_clock_seconds": None,
        "provider_duration": None,
    }


def _run(output: Path, call: Callable[[str, dict[str, Any]], Any] = _client_call) -> list[dict[str, Any]]:
    global API_LOOP_ENTERED
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing qualification output: {output}")
    preset = _preset()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("", encoding="utf-8")
    records: list[dict[str, Any]] = []
    API_LOOP_ENTERED = True
    for task in _tasks():
        row = _make_row(task)
        started = time.monotonic()
        try:
            _apply_response(row, task, call(row["final_prompt"], preset))
        except Exception as exc:
            from scripts.run_gemini_ab2g_math_core_qualification import _safe_provider_failure
            row["failure_category"], row["failure_detail"] = _safe_provider_failure(exc)
            row["execution_timeout"] = False
        row["wall_clock_seconds"] = time.monotonic() - started
        _append(output, row)
        records.append(row)
    return records


def dry_run_records() -> list[dict[str, Any]]:
    return [_make_row(task) for task in _tasks()]


def _write_summary(path: Path, records: list[dict[str, Any]]) -> None:
    lines = [
        "# Gemini Ab2d-local qualification summary", "",
        f"- condition: {PROMPT_CONDITION}", f"- model: {MODEL_TAG}",
        f"- seed: {SEED}", f"- task_count: {len(records)}", f"- cloud_qualified: {cloud_qualified(records)}", "",
        "| task_family | evaluable | oracle_pass | evaluation_status | failure_category |",
        "|---|---:|---:|---|---|",
    ]
    for row in records:
        lines.append("| {task_family} | {evaluable} | {oracle_pass} | {evaluation_status} | {failure_category} |".format(
            task_family=row["task_family"], evaluable=row.get("evaluable"), oracle_pass=row.get("oracle_pass"),
            evaluation_status=row.get("evaluation_status"), failure_category=row.get("failure_category", "")))
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="assemble and validate without API calls")
    mode.add_argument("--execute-api", action="store_true", help="explicitly execute the four provider requests")
    parser.add_argument("--run-id", help="safe output suffix: [A-Za-z0-9_-]+")
    args = parser.parse_args(argv)
    try:
        output, summary = _output_paths(args.run_id)
    except ValueError as exc:
        parser.error(str(exc))
    if args.dry_run:
        records = dry_run_records()
        print(json.dumps({"condition": PROMPT_CONDITION, "model": MODEL_TAG, "task_count": len(records), "api_calls": 0, "retry_count": 0, "first_attempt_only": True, "healer_enabled": False, "provider_timeout_seconds": REQUEST_TIMEOUT_SECONDS, "candidate_timeout_seconds": EXECUTION_TIMEOUT_SECONDS, "max_output_tokens": MAX_OUTPUT_TOKENS}, indent=2))
        return 0
    if not args.execute_api:
        parser.print_usage()
        return 2
    if not os.environ.get("GEMINI_API_KEY"):
        parser.error("GEMINI_API_KEY is required for --execute-api")
    records = _run(output)
    _write_summary(summary, records)
    print(json.dumps({"output": str(output), "summary": str(summary), "records": len(records)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
