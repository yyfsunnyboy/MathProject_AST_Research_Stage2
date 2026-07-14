"""Run or inspect the fixed four-cell Gemini Ab2g-math-core qualification."""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import multiprocessing
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_tools.finals_rebuild.ab2d_local_prompt import assemble_ab2g_math_core_prompt, measure_prompt_size
from agent_tools.finals_rebuild.math_answer_contracts import render_answer_contract
from agent_tools.finals_rebuild.math_boundary_pilot import classify_response
from agent_tools.finals_rebuild.math_task_oracles import evaluate_math_task_oracle
from agent_tools.finals_rebuild.math_task_sampler import sample_task_parameters


FAMILIES = (
    "polynomial_division_quotient_remainder",
    "largest_proper_divisor_reasoning",
    "rpm_circumference_to_kph",
    "alternating_training_progression_threshold",
)
SEED = 20260714
MODEL_TAG = "gemini-3.5-flash"
PROMPT_CONDITION = "Ab2g-math-core"
MAX_OUTPUT_TOKENS = 4096
REQUEST_TIMEOUT_SECONDS = 120
EXECUTION_TIMEOUT_SECONDS = 3.0
RESULT = ROOT / "docs/experiments/results/gemini_ab2g_math_core_l1_seed_20260714_qualification.jsonl"
SUMMARY = ROOT / "docs/experiments/gemini_ab2g_math_core_l1_seed_20260714_qualification_summary.md"
MANIFEST = ROOT / "tests/finals_rebuild/fixtures/math_generation_tasks_ce115_pilot.jsonl"
API_LOOP_ENTERED = False


def _append(path: Path, row: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def _output_paths(run_id: str | None) -> tuple[Path, Path]:
    """Return the default artifacts or a safe, distinct run-id pair."""
    if run_id is None:
        return RESULT, SUMMARY
    if not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
        raise ValueError("run-id must match [A-Za-z0-9_-]+")
    stem = f"gemini_ab2g_math_core_l1_seed_{run_id}"
    return (
        ROOT / "docs/experiments/results" / f"{stem}.jsonl",
        ROOT / "docs/experiments" / f"{stem}_summary.md",
    )


def _tasks() -> list[dict[str, Any]]:
    all_tasks = [json.loads(line) for line in MANIFEST.read_text(encoding="utf-8").splitlines() if line]
    selected = [next(task for task in all_tasks if task["skill_id"] == family and task["difficulty_level"] == 1) for family in FAMILIES]
    if [task["skill_id"] for task in selected] != list(FAMILIES):
        raise ValueError("qualification task selection is not the frozen four L1 families")
    return selected


def _runtime_version() -> str | None:
    for package in ("google-genai", "google-generativeai"):
        try:
            return f"{package} {importlib.metadata.version(package)}"
        except importlib.metadata.PackageNotFoundError:
            pass
    return None


def _preset() -> dict[str, Any]:
    from config import Config

    preset = dict(Config.CODER_PRESETS["gemini-3-flash"])
    if preset["provider"] != "google":
        raise ValueError("configured qualification preset is not a Google provider")
    preset.update({"model": MODEL_TAG, "max_tokens": MAX_OUTPUT_TOKENS})
    return preset


def _make_row(task: dict[str, Any]) -> dict[str, Any]:
    sampled = sample_task_parameters(task, SEED)
    payload = sampled["oracle_payload"]
    contract = render_answer_contract(task, payload)
    prompt = assemble_ab2g_math_core_prompt(contract, payload)
    expected = evaluate_math_task_oracle(task["oracle_type"], payload, None).get("expected_answer")
    return {
        "provider": "gemini", "model_tag": MODEL_TAG, "prompt_condition": PROMPT_CONDITION,
        "task_family": task["skill_id"], "task_id": task["task_id"], "difficulty": 1, "seed": SEED,
        "task_parameters": payload, "answer_contract": contract, "oracle_expected": expected, "final_prompt": prompt,
        "prompt_size": measure_prompt_size(prompt), "raw_first_attempt_output": None, "candidate_extracted": None,
        "parse_status": None, "evaluable": False, "oracle_pass": False, "failure_category": None,
        "failure_detail": None, "execution_timeout": None, "request_count": 1, "retry_count": 0,
        "healer_used": False, "prompt_token_count": None, "output_token_count": None, "total_token_count": None,
        "wall_clock_seconds": None, "provider_duration": None, "runtime": "gemini", "runtime_version": _runtime_version(),
        "run_status": "cloud_qualification",
    }


def _metadata(response: Any) -> tuple[int | None, int | None, int | None, float | None]:
    usage = getattr(response, "usage_metadata", None)
    prompt_tokens = getattr(response, "prompt_tokens", None) or getattr(usage, "prompt_token_count", None)
    output_tokens = getattr(response, "completion_tokens", None) or getattr(usage, "candidates_token_count", None)
    total_tokens = getattr(response, "total_tokens", None) or getattr(usage, "total_token_count", None)
    duration = getattr(response, "latency_ms", None)
    return prompt_tokens, output_tokens, total_tokens, None if duration is None else duration / 1000.0


def _apply_response(row: dict[str, Any], task: dict[str, Any], response: Any) -> None:
    raw = getattr(response, "text", None)
    if not isinstance(raw, str):
        raise ValueError("invalid Gemini response: missing text")
    outcome, candidate, detail = classify_response(raw, {"oracle_payload": row["task_parameters"]}, task, execution_timeout=EXECUTION_TIMEOUT_SECONDS)
    row.update({"raw_first_attempt_output": raw, "candidate_extracted": candidate, "parse_status": outcome,
                "evaluable": outcome not in {"empty_response", "catastrophic_truncation", "extraction_failure", "parse_minor", "missing_entry_point", "infrastructure_failure"},
                "oracle_pass": outcome == "passed", "failure_category": None if outcome == "passed" else outcome,
                "failure_detail": detail.get("runtime_error") or detail.get("parse_error") or detail.get("oracle_error")})
    row["execution_timeout"] = bool(row["failure_detail"] and "execution_timeout" in row["failure_detail"])
    row["prompt_token_count"], row["output_token_count"], row["total_token_count"], row["provider_duration"] = _metadata(response)


def _client_call(prompt: str, preset: dict[str, Any]) -> Any:
    from core.ai_wrapper import GoogleAIClient, call_ai_with_retry

    client = GoogleAIClient(preset["model"], preset["temperature"], max_tokens=preset["max_tokens"], safety_settings=preset.get("safety_settings"))
    # One first attempt and zero retry attempts.
    return call_ai_with_retry(client, prompt, max_retries=0, retry_delay=0, timeout=REQUEST_TIMEOUT_SECONDS)


def _safe_provider_failure(exc: Exception) -> tuple[str, str]:
    """Classify provider failures without retaining credentials in artifacts."""
    if isinstance(exc, TimeoutError):
        return "provider_timeout", f"TimeoutError: provider request exceeded {REQUEST_TIMEOUT_SECONDS} seconds"
    message = str(exc)
    message = re.sub(r"(?i)(api[_ -]?key\s*[=:]\s*)\S+", r"\1[REDACTED]", message)
    message = re.sub(r"AIza[0-9A-Za-z_-]+", "[REDACTED]", message)
    message = message[:500]
    return "provider_error", f"{type(exc).__name__}: {message}" if message else type(exc).__name__


def _run(output: Path, call: Callable[[str, dict[str, Any]], Any]) -> list[dict[str, Any]]:
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output}")
    preset = _preset()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("", encoding="utf-8")
    rows: list[dict[str, Any]] = []
    for task in _tasks():
        row = _make_row(task)
        started = time.monotonic()
        try:
            _apply_response(row, task, call(row["final_prompt"], preset))
        except Exception as exc:
            row["failure_category"], row["failure_detail"] = _safe_provider_failure(exc)
            row["execution_timeout"] = False
        row["wall_clock_seconds"] = time.monotonic() - started
        _append(output, row)
        rows.append(row)
    return rows


def cloud_qualified(rows: list[dict[str, Any]]) -> bool:
    return len(rows) == 4 and all(row["evaluable"] and row["oracle_pass"] and row["retry_count"] == 0 and not row.get("execution_timeout") for row in rows)


def _summary(rows: list[dict[str, Any]]) -> str:
    return "\n".join([
        "# Gemini Ab2g-math-core L1 qualification — 2026-07-14", "",
        f"- Rows: {len(rows)}", f"- Evaluable: {sum(r['evaluable'] for r in rows)} / 4",
        f"- Oracle pass: {sum(r['oracle_pass'] for r in rows)} / 4",
        f"- Provider timeouts: {sum(r['failure_category'] == 'provider_timeout' for r in rows)}",
        f"- Provider errors: {sum(r['failure_category'] == 'provider_error' for r in rows)}",
        f"- Execution timeouts: {sum(bool(r['execution_timeout']) for r in rows)}",
        f"- Cloud qualified: {cloud_qualified(rows)}", "",
    ])


def dry_run_records() -> list[dict[str, Any]]:
    """Return planned rows without creating clients, calling providers, or writing files."""
    return [_make_row(task) for task in _tasks()]


def main(argv: list[str] | None = None) -> int:
    multiprocessing.freeze_support()
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="assemble and print the planned four rows without API calls")
    mode.add_argument("--execute-api", action="store_true", help="run the one-shot cloud qualification")
    parser.add_argument("--run-id", help="safe suffix for a distinct JSONL/summary artifact pair")
    args = parser.parse_args(argv)
    try:
        result_path, summary_path = _output_paths(args.run_id)
    except ValueError as exc:
        parser.error(str(exc))
    if args.dry_run:
        print(json.dumps(dry_run_records(), ensure_ascii=False, sort_keys=True))
        return 0
    if not args.execute_api:
        parser.print_usage()
        return 2
    if not os.getenv("GEMINI_API_KEY"):
        raise SystemExit("GEMINI_API_KEY is not set")
    global API_LOOP_ENTERED
    API_LOOP_ENTERED = True
    rows = _run(result_path, _client_call)
    summary_path.write_text(_summary(rows), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
