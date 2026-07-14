"""Run the fixed four-family Ab2d minimal smoke once, without retry or Healer."""
from __future__ import annotations

import json
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
FAMILIES = (
    "polynomial_division_quotient_remainder",
    "largest_proper_divisor_reasoning",
    "rpm_circumference_to_kph",
    "alternating_training_progression_threshold",
)
MANIFEST = ROOT / "tests/finals_rebuild/fixtures/math_generation_tasks_ce115_pilot.jsonl"
RESULT = ROOT / "docs/experiments/results/ab2d_qwen3_4b_l1_seed_20260714_smoke.jsonl"
SUMMARY = ROOT / "docs/experiments/ab2d_qwen3_4b_l1_seed_20260714_smoke_summary.md"


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


def _row(task: dict[str, Any], index: int, runtime_version: str | None) -> dict[str, Any]:
    sampled = sample_task_parameters(task, SEED)
    frozen = {"task_id": task["task_id"], "difficulty_level": task["difficulty_level"], "repeat_seed": SEED,
              "oracle_type": task["oracle_type"], "oracle_payload": sampled["oracle_payload"]}
    prompt = build_ab2d_prompt(task, frozen)
    request = {"model": MODEL, "messages": [{"role": "user", "content": prompt}], "stream": False,
               "options": {"temperature": 0.0, "seed": SEED}}
    row: dict[str, Any] = {
        "task_family": task["skill_id"], "task_id": task["task_id"], "difficulty": 1, "seed": SEED,
        "model_tag": MODEL, "prompt_condition": CONDITION, "task_parameters": sampled["oracle_payload"],
        "question": None, "answer_contract": render_answer_contract(task, sampled["oracle_payload"]), "oracle_expected": None, "final_prompt": prompt,
        "raw_first_attempt_output": None, "candidate_extracted": None, "parse_status": None, "evaluable": False,
        "oracle_pass": False, "failure_category": None, "http_status": None, "http_error_body": None,
        "prompt_eval_count": None, "eval_count": None, "total_token_count": None, "total_duration": None,
        "load_duration": None, "prompt_eval_duration": None, "eval_duration": None, "wall_clock_seconds": None,
        "cold_start_or_warm_run": "cold_start" if index == 0 else "warm_run", "runtime": "ollama",
        "runtime_version": runtime_version, "retry_count": 0, "healer_enabled": False,
    }
    started = time.monotonic()
    try:
        response = call_ollama_chat("http://localhost:11434", request, timeout=300)
        raw = response.get("message", {}).get("content")
        if not isinstance(raw, str):
            raise ValueError("missing message.content")
        outcome, extracted, details = classify_response(raw, frozen, task)
        row.update({"raw_first_attempt_output": raw, "candidate_extracted": extracted, "parse_status": outcome,
                    "evaluable": outcome not in {"empty_response", "catastrophic_truncation", "extraction_failure", "parse_minor", "missing_entry_point", "infrastructure_failure"},
                    "oracle_pass": outcome == "passed", "failure_category": None if outcome == "passed" else outcome})
        row["question"] = None
        for key in ("prompt_eval_count", "eval_count", "total_duration", "load_duration", "prompt_eval_duration", "eval_duration"):
            row[key] = response.get(key)
        row["total_token_count"] = (row["prompt_eval_count"] or 0) + (row["eval_count"] or 0)
        if details.get("expected_answer") is not None:
            row["oracle_expected"] = details["expected_answer"]
    except OllamaHTTPError as exc:
        row.update({"failure_category": "infrastructure_failure", "http_status": exc.status, "http_error_body": exc.body})
    except Exception as exc:
        row.update({"failure_category": "infrastructure_failure", "http_error_body": f"{type(exc).__name__}: {exc}"})
    row["wall_clock_seconds"] = time.monotonic() - started
    return row


def _summary(rows: list[dict[str, Any]]) -> str:
    lines = ["# Ab2d 4B L1 Minimal Smoke — 2026-07-14", "", "One generation per required L1 family; retry=0 and Healer disabled.", "", "| task_family | generation | extraction | evaluable | oracle_pass | failure_category |", "|---|---|---|---|---|---|"]
    for row in rows:
        generation = "done" if row["http_status"] is None else f"HTTP {row['http_status']}"
        extraction = row["parse_status"] or "N/A"
        lines.append(f"| {row['task_family']} | {generation} | {extraction} | {row['evaluable']} | {row['oracle_pass']} | {row['failure_category'] or 'none'} |")
    lines += ["", f"- Tasks attempted: {len(rows)}", f"- Tasks completed: {sum(row['http_status'] is None for row in rows)}", f"- Evaluable: {sum(row['evaluable'] for row in rows)}", f"- Oracle pass: {sum(row['oracle_pass'] for row in rows)}", "- Retry used: 0", "- Healer used: no", ""]
    return "\n".join(lines)


def main() -> int:
    runtime_version = _runtime_version()
    rows = [_row(task, index, runtime_version) for index, task in enumerate(_load_tasks())]
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    SUMMARY.write_text(_summary(rows), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
