"""Run the fixed eight-cell Gemini Ab1 versus Ab2d-v1 diagnostic."""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import multiprocessing
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_tools.finals_rebuild.math_answer_contracts import render_answer_contract
from agent_tools.finals_rebuild.math_boundary_pilot import build_ab1_prompt, build_ab2d_prompt, classify_response
from agent_tools.finals_rebuild.math_task_oracles import evaluate_math_task_oracle
from agent_tools.finals_rebuild.math_task_sampler import sample_task_parameters

FAMILIES = (
    "polynomial_division_quotient_remainder",
    "largest_proper_divisor_reasoning",
    "rpm_circumference_to_kph",
    "alternating_training_progression_threshold",
)
CONDITIONS: tuple[tuple[str, Callable[[dict[str, Any], dict[str, Any]], str]], ...] = (
    ("Ab1", build_ab1_prompt),
    ("Ab2d", build_ab2d_prompt),
)
SEED = 20260714
PRESET_KEY = "gemini-3-flash"
MODEL_TAG = "gemini-3.5-flash"
MAX_OUTPUT_TOKENS = 4096
RESULT = ROOT / "docs/experiments/results/gemini_ab1_ab2d_l1_seed_20260714_diagnostic.jsonl"
SUMMARY = ROOT / "docs/experiments/gemini_ab1_ab2d_l1_seed_20260714_diagnostic_summary.md"
MANIFEST = ROOT / "tests/finals_rebuild/fixtures/math_generation_tasks_ce115_pilot.jsonl"
RUN_STATUS = "cloud_upper_bound_diagnostic"
EXECUTION_TIMEOUT_SECONDS = 3.0
REQUEST_TIMEOUT_SECONDS = 120
API_LOOP_ENTERED = False


def _append(path: Path, row: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def _tasks() -> list[dict[str, Any]]:
    all_tasks = [json.loads(line) for line in MANIFEST.read_text(encoding="utf-8").splitlines() if line]
    selected = [next(task for task in all_tasks if task["skill_id"] == family and task["difficulty_level"] == 1) for family in FAMILIES]
    if [task["skill_id"] for task in selected] != list(FAMILIES):
        raise ValueError("diagnostic task selection is not the frozen four L1 families")
    return selected


def _preset() -> dict[str, Any]:
    from config import Config

    preset = dict(Config.CODER_PRESETS[PRESET_KEY])
    if preset["provider"] != "google":
        raise ValueError("configured Gemini diagnostic preset is not a Google provider")
    # The diagnostic fixes its cloud model and output budget independently of
    # the broader historical preset while retaining its provider, temperature,
    # and safety configuration.
    preset.update({"model": MODEL_TAG, "max_tokens": MAX_OUTPUT_TOKENS})
    return preset


def _runtime_version() -> str | None:
    for package in ("google-genai", "google-generativeai"):
        try:
            return f"{package} {importlib.metadata.version(package)}"
        except importlib.metadata.PackageNotFoundError:
            pass
    return None


def _metadata(response: Any) -> tuple[int | None, int | None, int | None, float | None]:
    usage = getattr(response, "usage_metadata", None)
    prompt_tokens = getattr(response, "prompt_tokens", None) or getattr(usage, "prompt_token_count", None)
    output_tokens = getattr(response, "completion_tokens", None) or getattr(usage, "candidates_token_count", None)
    total_tokens = getattr(response, "total_tokens", None) or getattr(usage, "total_token_count", None)
    duration = getattr(response, "latency_ms", None)
    return prompt_tokens, output_tokens, total_tokens, None if duration is None else duration / 1000.0


def _make_row(task: dict[str, Any], condition: str, builder: Callable[[dict[str, Any], dict[str, Any]], str], model_tag: str) -> dict[str, Any]:
    sampled = sample_task_parameters(task, SEED)
    frozen = {"task_id": task["task_id"], "difficulty_level": 1, "repeat_seed": SEED,
              "oracle_type": task["oracle_type"], "oracle_payload": sampled["oracle_payload"]}
    prompt = builder(task, frozen)
    expected = evaluate_math_task_oracle(task["oracle_type"], sampled["oracle_payload"], None).get("expected_answer")
    return {
        "provider": "gemini", "model_tag": model_tag, "task_family": task["skill_id"], "task_id": task["task_id"],
        "difficulty": 1, "seed": SEED, "prompt_condition": condition, "task_parameters": sampled["oracle_payload"],
        "answer_contract": render_answer_contract(task, sampled["oracle_payload"]), "oracle_expected": expected,
        "final_prompt": prompt, "raw_first_attempt_output": None, "candidate_extracted": None,
        "parse_status": None, "evaluable": False, "oracle_pass": False, "failure_category": None,
        "failure_detail": None, "execution_timeout": None, "request_count": 1, "retry_count": 0,
        "healer_used": False, "prompt_token_count": None, "output_token_count": None, "total_token_count": None,
        "wall_clock_seconds": None, "provider_duration": None, "runtime": "gemini", "runtime_version": _runtime_version(),
        "run_status": RUN_STATUS,
    }


def _apply_response(row: dict[str, Any], task: dict[str, Any], response: Any) -> None:
    raw = getattr(response, "text", None)
    if not isinstance(raw, str):
        raise ValueError("invalid Gemini response: missing text")
    frozen = {"oracle_payload": row["task_parameters"]}
    outcome, candidate, detail = classify_response(raw, frozen, task, execution_timeout=EXECUTION_TIMEOUT_SECONDS)
    row.update({"raw_first_attempt_output": raw, "candidate_extracted": candidate, "parse_status": outcome,
                "evaluable": outcome not in {"empty_response", "catastrophic_truncation", "extraction_failure", "parse_minor", "missing_entry_point", "infrastructure_failure"},
                "oracle_pass": outcome == "passed", "failure_category": None if outcome == "passed" else outcome,
                "failure_detail": detail.get("runtime_error") or detail.get("parse_error") or detail.get("oracle_error")})
    row["execution_timeout"] = bool(row["failure_detail"] and "execution_timeout" in row["failure_detail"])
    row["prompt_token_count"], row["output_token_count"], row["total_token_count"], row["provider_duration"] = _metadata(response)


def _client_call(prompt: str, preset: dict[str, Any]) -> Any:
    """Use the existing production client and retry helper with exactly one attempt."""
    from core.ai_wrapper import GoogleAIClient, call_ai_with_retry

    client = GoogleAIClient(preset["model"], preset["temperature"], max_tokens=preset["max_tokens"], safety_settings=preset.get("safety_settings"))
    return call_ai_with_retry(client, prompt, max_retries=1, retry_delay=0, timeout=REQUEST_TIMEOUT_SECONDS)


def _run(output: Path, call: Callable[[str, dict[str, Any]], Any]) -> list[dict[str, Any]]:
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output}")
    preset = _preset()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("", encoding="utf-8")
    rows = []
    for task in _tasks():
        for condition, builder in CONDITIONS:
            row = _make_row(task, condition, builder, preset["model"])
            started = time.monotonic()
            try:
                _apply_response(row, task, call(row["final_prompt"], preset))
            except Exception as exc:
                # Preserve the error class, but do not record provider headers or request details.
                row["failure_category"] = "infrastructure_failure"
                row["failure_detail"] = type(exc).__name__
            row["wall_clock_seconds"] = time.monotonic() - started
            if "GEMINI_API_KEY" in json.dumps(row, ensure_ascii=False):
                raise AssertionError("key environment variable name unexpectedly entered output")
            _append(output, row)
            rows.append(row)
    if len(rows) != 8 or len({(r["task_family"], r["prompt_condition"]) for r in rows}) != 8:
        raise AssertionError("diagnostic must contain exactly eight unique cells")
    return rows


def _summary(rows: list[dict[str, Any]]) -> str:
    by_cell = {(row["task_family"], row["prompt_condition"]): row for row in rows}
    lines = ["# Gemini Ab1 vs Ab2d-v1 L1 diagnostic — 2026-07-14", "", "| task_family | Gemini Ab1 outcome | Gemini Ab2d outcome |", "|---|---|---|"]
    for family in FAMILIES:
        outcome = lambda condition: by_cell[(family, condition)]["failure_category"] or "passed"
        lines.append(f"| {family} | {outcome('Ab1')} | {outcome('Ab2d')} |")
    subset = lambda condition: [r for r in rows if r["prompt_condition"] == condition]
    ab1, ab2d = subset("Ab1"), subset("Ab2d")
    label = "incomplete diagnostic"
    if all(r["oracle_pass"] for r in ab1 + ab2d): label = "Gemini Ab1 and Ab2d both performed well"
    elif sum(r["oracle_pass"] for r in ab1) > sum(r["oracle_pass"] for r in ab2d): label = "Gemini Ab1 outperformed Ab2d"
    elif sum(r["oracle_pass"] for r in ab2d) > sum(r["oracle_pass"] for r in ab1): label = "Gemini Ab2d outperformed Ab1"
    elif not any(r["oracle_pass"] for r in ab1 + ab2d): label = "Gemini Ab1 and Ab2d both performed poorly"
    failure_counts = lambda rows: {kind: sum(r["failure_category"] == kind for r in rows) for kind in ("extraction_failure", "runtime_failure", "answer_incorrect")}
    lines += ["", f"- Ab1 evaluable / 4: {sum(r['evaluable'] for r in ab1)} / 4", f"- Ab1 oracle pass / 4: {sum(r['oracle_pass'] for r in ab1)} / 4", f"- Ab2d evaluable / 4: {sum(r['evaluable'] for r in ab2d)} / 4", f"- Ab2d oracle pass / 4: {sum(r['oracle_pass'] for r in ab2d)} / 4", f"- Ab1 extraction/runtime/answer failures: {failure_counts(ab1)}", f"- Ab2d extraction/runtime/answer failures: {failure_counts(ab2d)}", f"- Interpretation: {label}", ""]
    return "\n".join(lines)


def _offline_validate() -> None:
    class FakeResponse:
        text = "def generate(level=1, **kwargs):\n    return {}\n"
        prompt_tokens, completion_tokens, total_tokens, latency_ms = 1, 1, 2, 1
    with tempfile.TemporaryDirectory(prefix="gemini_diagnostic_") as temp:
        path = Path(temp) / "rows.jsonl"
        rows = _run(path, lambda _prompt, _preset: FakeResponse())
        persisted = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
        assert len(rows) == len(persisted) == 8
        assert len({(r["task_family"], r["prompt_condition"]) for r in persisted}) == 8
        assert all(r["request_count"] == 1 and r["retry_count"] == 0 for r in persisted)
        assert all("GEMINI_API_KEY" not in json.dumps(r, ensure_ascii=False) for r in persisted)


def main() -> int:
    # Required on Windows: a spawned child must exit its bootstrap path without
    # falling through into this diagnostic's API orchestration.
    multiprocessing.freeze_support()
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline-validate", action="store_true")
    args = parser.parse_args()
    if args.offline_validate:
        _offline_validate()
        return 0
    if not os.getenv("GEMINI_API_KEY"):
        raise SystemExit("GEMINI_API_KEY is not set")
    global API_LOOP_ENTERED
    API_LOOP_ENTERED = True
    rows = _run(RESULT, _client_call)
    SUMMARY.write_text(_summary(rows), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
