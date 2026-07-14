"""Run the fixed four-family Ab2d minimal smoke once, without retry or Healer."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_tools.finals_rebuild.math_boundary_pilot import build_ab2d_prompt, classify_response
from agent_tools.finals_rebuild.math_generation_runner import ALLOWED_MODELS, OllamaHTTPError, call_ollama_chat
from agent_tools.finals_rebuild.math_task_sampler import sample_task_parameters
from agent_tools.finals_rebuild.math_answer_contracts import render_answer_contract

MODEL = "qwen3:4b-instruct-2507-q4_K_M"
SEED = 20260714
CONDITION = "Ab2d"
CANDIDATE_EXECUTION_TIMEOUT_SECONDS = 3.0
FAMILIES = (
    "polynomial_division_quotient_remainder",
    "largest_proper_divisor_reasoning",
    "rpm_circumference_to_kph",
    "alternating_training_progression_threshold",
)
MANIFEST = ROOT / "tests/finals_rebuild/fixtures/math_generation_tasks_ce115_pilot.jsonl"
RESULT = ROOT / "docs/experiments/results/ab2d_qwen3_4b_l1_seed_20260714_smoke.jsonl"
SUMMARY = ROOT / "docs/experiments/ab2d_qwen3_4b_l1_seed_20260714_smoke_summary.md"


def _output_paths(model: str) -> tuple[Path, Path]:
    model_label = "4b" if model == MODEL else "8b"
    stem = f"ab2d_qwen3_{model_label}_l1_seed_20260714_smoke"
    return ROOT / "docs/experiments/results" / f"{stem}.jsonl", ROOT / "docs/experiments" / f"{stem}_summary.md"


def _run_metadata(model: str) -> dict[str, Any]:
    if model == "qwen3:8b":
        return {"run_status": "engineering_diagnostic_rerun", "prior_unrecorded_attempts": 2,
                "itt_first_attempt_claim": False}
    return {"run_status": "standard", "prior_unrecorded_attempts": 0, "itt_first_attempt_claim": True}


def append_jsonl_record(path: Path, row: dict[str, Any]) -> None:
    """Persist one completed attempt before the next generation begins."""
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def _runtime_version() -> str | None:
    try:
        completed = subprocess.run(["ollama", "--version"], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        completed = None
    if completed:
        version = (completed.stdout or completed.stderr).strip()
        if version:
            return version
    try:
        with urllib.request.urlopen("http://localhost:11434/api/version", timeout=10) as response:
            return json.loads(response.read()).get("version")
    except Exception:
        return None


def _load_tasks() -> list[dict[str, Any]]:
    tasks = [json.loads(line) for line in MANIFEST.read_text(encoding="utf-8").splitlines() if line.strip()]
    selected = [next(task for task in tasks if task["skill_id"] == family and task["difficulty_level"] == 1) for family in FAMILIES]
    if [task["skill_id"] for task in selected] != list(FAMILIES):
        raise ValueError("the minimal smoke task selection is not the four required L1 families")
    return selected


def _row(task: dict[str, Any], index: int, runtime_version: str | None, model: str) -> dict[str, Any]:
    sampled = sample_task_parameters(task, SEED)
    frozen = {"task_id": task["task_id"], "difficulty_level": task["difficulty_level"], "repeat_seed": SEED,
              "oracle_type": task["oracle_type"], "oracle_payload": sampled["oracle_payload"]}
    prompt = build_ab2d_prompt(task, frozen)
    request = {"model": model, "messages": [{"role": "user", "content": prompt}], "stream": False,
               "options": {"temperature": 0.0, "seed": SEED}}
    row: dict[str, Any] = {
        "task_family": task["skill_id"], "task_id": task["task_id"], "difficulty": 1, "seed": SEED,
        "model_tag": model, "prompt_condition": CONDITION, "task_parameters": sampled["oracle_payload"],
        "question": None, "answer_contract": render_answer_contract(task, sampled["oracle_payload"]), "oracle_expected": None, "final_prompt": prompt,
        "raw_first_attempt_output": None, "candidate_extracted": None, "parse_status": None, "evaluable": False,
        "oracle_pass": False, "failure_category": None, "failure_detail": None, "http_status": None, "http_error_body": None,
        "prompt_eval_count": None, "eval_count": None, "total_token_count": None, "total_duration": None,
        "load_duration": None, "prompt_eval_duration": None, "eval_duration": None, "wall_clock_seconds": None,
        "cold_start_or_warm_run": "cold_start" if index == 0 else "warm_run", "runtime": "ollama",
        "runtime_version": runtime_version, "retry_count": 0, "healer_enabled": False, **_run_metadata(model),
    }
    started = time.monotonic()
    try:
        response = call_ollama_chat("http://localhost:11434", request, timeout=300)
        raw = response.get("message", {}).get("content")
        if not isinstance(raw, str):
            raise ValueError("missing message.content")
        outcome, extracted, details = classify_response(raw, frozen, task, execution_timeout=CANDIDATE_EXECUTION_TIMEOUT_SECONDS)
        row.update({"raw_first_attempt_output": raw, "candidate_extracted": extracted, "parse_status": outcome,
                    "evaluable": outcome not in {"empty_response", "catastrophic_truncation", "extraction_failure", "parse_minor", "missing_entry_point", "infrastructure_failure"},
                    "oracle_pass": outcome == "passed", "failure_category": None if outcome == "passed" else outcome})
        row["question"] = None
        for key in ("prompt_eval_count", "eval_count", "total_duration", "load_duration", "prompt_eval_duration", "eval_duration"):
            row[key] = response.get(key)
        row["total_token_count"] = (row["prompt_eval_count"] or 0) + (row["eval_count"] or 0)
        if details.get("expected_answer") is not None:
            row["oracle_expected"] = details["expected_answer"]
        row["failure_detail"] = details.get("runtime_error") or details.get("parse_error")
    except OllamaHTTPError as exc:
        row.update({"failure_category": "infrastructure_failure", "failure_detail": str(exc), "http_status": exc.status, "http_error_body": exc.body})
    except Exception as exc:
        detail = f"{type(exc).__name__}: {exc}"
        row.update({"failure_category": "infrastructure_failure", "failure_detail": detail, "http_error_body": detail})
    row["wall_clock_seconds"] = time.monotonic() - started
    return row


def _summary(rows: list[dict[str, Any]], model: str) -> str:
    lines = [f"# Ab2d {model} L1 Minimal Smoke — 2026-07-14", "", "One generation per required L1 family; retry=0 and Healer disabled.", "", "| task_family | generation | extraction | evaluable | oracle_pass | failure_category |", "|---|---|---|---|---|---|"]
    for row in rows:
        generation = "done" if row["http_status"] is None else f"HTTP {row['http_status']}"
        extraction = row["parse_status"] or "N/A"
        lines.append(f"| {row['task_family']} | {generation} | {extraction} | {row['evaluable']} | {row['oracle_pass']} | {row['failure_category'] or 'none'} |")
    metadata = _run_metadata(model)
    lines += ["", f"- Tasks attempted: {len(rows)}", f"- Tasks completed: {sum(row['http_status'] is None for row in rows)}", f"- Evaluable: {sum(row['evaluable'] for row in rows)}", f"- Oracle pass: {sum(row['oracle_pass'] for row in rows)}", "- Retry used: 0", "- Healer used: no", f"- run_status: {metadata['run_status']}", f"- prior_unrecorded_attempts: {metadata['prior_unrecorded_attempts']}", f"- itt_first_attempt_claim: {metadata['itt_first_attempt_claim']}", ""]
    if model == "qwen3:8b":
        four_b_rows = {row["task_family"]: row for row in (json.loads(line) for line in RESULT.read_text(encoding="utf-8").splitlines() if line.strip())}
        lines += ["", "## 4B comparison", "", "| task_family | 4B outcome | 8B outcome |", "|---|---|---|"]
        for row in rows:
            four_b = four_b_rows[row["task_family"]]
            four_b_outcome = four_b["failure_category"] or four_b["parse_status"]
            eight_b_outcome = row["failure_category"] or row["parse_status"]
            lines.append(f"| {row['task_family']} | {four_b_outcome} | {eight_b_outcome} |")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=MODEL, choices=tuple(ALLOWED_MODELS))
    args = parser.parse_args(argv)
    runtime_version = _runtime_version()
    result, summary = _output_paths(args.model)
    result.parent.mkdir(parents=True, exist_ok=True)
    result.write_text("", encoding="utf-8")
    rows = []
    for index, task in enumerate(_load_tasks()):
        row = _row(task, index, runtime_version, args.model)
        append_jsonl_record(result, row)
        rows.append(row)
    summary.write_text(_summary(rows, args.model), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
