"""Stage A paired Math failure-boundary pilot (Ab1 only)."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

from agent_tools.finals_rebuild.extraction import extract_code
from agent_tools.finals_rebuild.math_generation_runner import ALLOWED_MODELS, call_ollama_chat
from agent_tools.finals_rebuild.math_task_oracles import evaluate_math_task_oracle
from agent_tools.finals_rebuild.math_task_sampler import sample_task_parameters

RUN_ID_DEFAULT = "math-boundary-stage-a-20260713"
REPEAT_SEEDS = (2026071301, 2026071302, 2026071303)
MODEL_TAGS = ("qwen3:4b-instruct-2507-q4_K_M", "qwen3:8b")
TASK_IDS = (
    "ce115_q07_polynomial_division_l1",
    "ce115_q24_rotation_speed_conversion_l1",
    "ce115_q24_rotation_speed_conversion_l2",
    "ce115_q20_largest_proper_divisor_l3",
    "ce115_cr01_training_sequence_threshold_l3",
)
OUTCOMES = frozenset(("passed", "empty_response", "catastrophic_truncation", "extraction_failure", "parse_minor", "missing_entry_point", "schema_failure", "runtime_failure", "answer_incorrect", "intrinsic_safety", "infrastructure_failure"))


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def load_pilot_tasks(path: str | Path) -> tuple[dict[str, Any], ...]:
    all_tasks = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    by_id = {task["task_id"]: task for task in all_tasks}
    missing = set(TASK_IDS) - set(by_id)
    if missing:
        raise ValueError(f"pilot manifest is missing tasks: {sorted(missing)}")
    return tuple(by_id[task_id] for task_id in TASK_IDS)


def frozen_payloads(tasks: Iterable[dict[str, Any]], repeat_seeds: Iterable[int] = REPEAT_SEEDS) -> list[dict[str, Any]]:
    records = []
    for rank, task in enumerate(tasks, 1):
        for seed in repeat_seeds:
            sampled = sample_task_parameters(task, seed)
            records.append({"task_id": task["task_id"], "difficulty_rank": rank, "difficulty_level": task["difficulty_level"], "repeat_seed": seed, "oracle_type": task["oracle_type"], "oracle_payload": sampled["oracle_payload"]})
    return records


def build_ab1_prompt(task: dict[str, Any], frozen: dict[str, Any]) -> str:
    answer_contract = ""
    if task["oracle_type"] == "polynomial_division_exact":
        answer_contract = (
            "correct_answer must be a JSON-compatible dict with exactly "
            "quotient_coefficients (a two-number list ordered from highest degree to constant) "
            "and remainder (a number). Do not return correct_answer as natural-language text. "
        )
    elif task["oracle_type"] == "rpm_circumference_kph":
        answer_contract = (
            "correct_answer must be a JSON-compatible dict with exactly coefficient (the exact speed "
            "coefficient for 1 rpm as a p/q string) and unit (the requested unit). Do not return a "
            "speed for an assumed rpm value or natural-language text. "
        )
    elif task["oracle_type"] == "largest_proper_divisor_logic":
        answer_contract = (
            "correct_answer must be a JSON-compatible dict with exactly claims (a boolean list in the "
            "frozen claims order, answering whether each candidate factor is necessary). Do not return "
            "largest proper divisor values or natural-language text. "
        )
    elif task["oracle_type"] == "alternating_sequence_threshold":
        answer_contract = (
            "correct_answer must be a JSON-compatible dict with exactly specified_session_laps (a number), "
            "first_exceed_week (a number), and first_exceed_day (a frozen day label). Do not return only "
            "a distance, a partial answer, or natural-language text. "
        )
    return (
        "Write only Python source. Implement def generate(level=1, **kwargs).\n"
        f"Task: {task['task_id']} ({task['domain']}, difficulty level {task['difficulty_level']}).\n"
        f"Task specification: {task['skill_id']}.\n"
        f"Frozen sampled parameters: {json.dumps(frozen['oracle_payload'], sort_keys=True)}\n"
        "generate() must return a dict with exactly question_text, correct_answer, and oracle_payload. "
        + answer_contract
        + "oracle_payload must exactly equal the frozen sampled parameters. Do not use input, files, network, subprocess, Markdown fences, or explanations."
    )


def build_ab2g_prompt(task: dict[str, Any], frozen: dict[str, Any]) -> str:
    return (
        build_ab1_prompt(task, frozen)
        + "\n\nGeneric Safety-and-Format Scaffold: output only complete Python source, with no Markdown "
        "fences and no explanatory prose. Define generate() exactly as specified above. Use the frozen "
        "sampled parameters exactly as given, without altering any value. Before returning, verify that "
        "field names, types, and structure match the required schema, and that question_text, "
        "correct_answer, and oracle_payload are mutually consistent."
    )


def build_ab2d_prompt(task: dict[str, Any], frozen: dict[str, Any]) -> str:
    from core.skill_policies.registry import list_registered_skill_ids, normalize_skill_id
    from agent_tools.prompt_loader import load_prompt_from_skill

    skill_name = normalize_skill_id(task["skill_id"], list_registered_skill_ids())
    if skill_name == "Unknown":
        raise ValueError(f"Ab2d routing failed for skill_id: {task['skill_id']!r}")
    prompt = load_prompt_from_skill(skill_name, ablation_target="Ab3", task_metadata=task,
                                    frozen_payload=frozen["oracle_payload"])
    if not prompt:
        raise ValueError(f"Ab2d prompt assembly failed for task: {task['task_id']!r}")
    return prompt


def _domain_execution_namespace(skill_id: str) -> dict[str, Any]:
    """Return the documented Domain APIs available to a pilot candidate.

    The normal production generator injects these helpers before execution.  The
    pilot runs candidates in a clean subprocess, so it must provide the same
    runtime names rather than leaving Ab2d's API contract prompt-only.
    """
    from core.prompts.domain_function_library import FractionOps, IntegerOps, PolynomialOps, RadicalOps

    names = {"IntegerOps": IntegerOps, "FractionOps": FractionOps}
    if skill_id == "radical_simplification":
        names["RadicalOps"] = RadicalOps
    if skill_id in {"polynomial_division_quotient_remainder", "polynomial_division_general", "polynomial_factor_roots"}:
        names["PolynomialOps"] = PolynomialOps
    return names


def _execute_generate(source: str, timeout: float = 3.0, *, skill_id: str | None = None) -> tuple[str, Any, str | None]:
    wrapper = """import json, sys, traceback
source = sys.stdin.read()
try:
    from core.prompts.domain_function_library import FractionOps, IntegerOps, PolynomialOps, RadicalOps
    ns = {'__name__': '__main__'}
    ns.update({name: globals()[name] for name in json.loads(sys.argv[1])})
    exec(compile(source, 'candidate.py', 'exec'), ns)
    print(json.dumps({'ok': True, 'value': ns['generate']()}, ensure_ascii=False))
except BaseException as exc:
    print(json.dumps({'ok': False, 'type': type(exc).__name__, 'message': str(exc)}))
"""
    try:
        environment = os.environ | {"PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
        namespace = _domain_execution_namespace(skill_id or "")
        proc = subprocess.run([sys.executable, "-X", "utf8", "-c", wrapper, json.dumps(list(namespace))], input=source, capture_output=True, text=True, encoding="utf-8", errors="replace", env=environment, timeout=timeout)
    except subprocess.TimeoutExpired:
        return "runtime_failure", None, "timeout"
    if proc.returncode:
        return "infrastructure_failure", None, proc.stderr
    try:
        result = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return "infrastructure_failure", None, "invalid evaluator response"
    return ("passed", result.get("value"), None) if result.get("ok") else ("runtime_failure", None, result.get("message") or result.get("type"))


def _looks_truncated(raw: str) -> bool:
    stripped = raw.rstrip()
    return stripped.count("```") % 2 == 1


def classify_response(raw: str, frozen: dict[str, Any], task: dict[str, Any]) -> tuple[str, str | None, dict[str, Any]]:
    if not raw.strip():
        return "empty_response", None, {}
    if _looks_truncated(raw):
        return "catastrophic_truncation", None, {}
    extracted = extract_code(raw)
    if extracted.extraction_status != "extracted" or not extracted.extracted_code:
        return "extraction_failure", extracted.extracted_code, {"extraction_status": extracted.extraction_status}
    source = extracted.extracted_code
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return "parse_minor", source, {"parse_error": str(exc)}
    entries = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "generate"]
    if len(entries) != 1:
        return "missing_entry_point", source, {"entry_point_count": len(entries)}
    status, value, error = _execute_generate(source, skill_id=task["skill_id"])
    if status != "passed":
        return status, source, {"runtime_error": error}
    if not isinstance(value, dict) or set(value) != {"question_text", "correct_answer", "oracle_payload"} or not isinstance(value.get("question_text"), str) or value.get("oracle_payload") != frozen["oracle_payload"]:
        return "schema_failure", source, {}
    verdict = evaluate_math_task_oracle(task["oracle_type"], frozen["oracle_payload"], value["correct_answer"])
    if verdict.get("error"):
        return "intrinsic_safety", source, {"oracle_error": verdict["error"]}
    if not verdict["is_correct"]:
        return "answer_incorrect", source, {"expected_answer": verdict["expected_answer"]}
    return "passed", source, {}


CONDITIONS = {"ab1": ("Ab1", build_ab1_prompt), "ab2g": ("Ab2g", build_ab2g_prompt), "ab2d": ("Ab2d", build_ab2d_prompt)}


def run_pilot(tasks: Sequence[dict[str, Any]], *, output_root: str | Path, run_id: str = RUN_ID_DEFAULT, repeat_seeds: Sequence[int] = REPEAT_SEEDS, models: Sequence[str] = MODEL_TAGS, ollama_url: str = "http://localhost:11434", timeout: int = 300, client: Callable[..., dict[str, Any]] = call_ollama_chat, supersedes_run_id: str | None = None, supersede_reason: str | None = None, condition: str = "ab1") -> dict[str, Any]:
    if tuple(models) != MODEL_TAGS:
        raise ValueError("Stage A requires the fixed 4B and 8B model pair")
    if condition not in CONDITIONS:
        raise ValueError(f"unsupported condition: {condition!r}")
    treatment, build_prompt = CONDITIONS[condition]
    root = Path(output_root) / run_id
    if root.exists():
        raise ValueError(f"output directory already exists: {root}")
    root.mkdir(parents=True)
    frozen = frozen_payloads(tasks, repeat_seeds)
    (root / "frozen_payloads.jsonl").write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in frozen), encoding="utf-8")
    results = []
    started_run = time.monotonic()
    for index, payload in enumerate(frozen):
        task = next(item for item in tasks if item["task_id"] == payload["task_id"])
        prompt = build_prompt(task, payload)
        for model in models:
            started = time.monotonic()
            row = {"run_id": run_id, "task_id": task["task_id"], "difficulty_rank": payload["difficulty_rank"], "difficulty_level": task["difficulty_level"], "model_tag": model, "model_digest": ALLOWED_MODELS[model]["model_digest"], "treatment": treatment, "repeat_seed": payload["repeat_seed"], "frozen_oracle_payload": payload["oracle_payload"], "prompt_text": prompt, "started_at": time.time(), "cold_start_or_warm_run": "cold_start" if not results else "warm_run"}
            try:
                response = client(ollama_url, {"model": model, "messages": [{"role": "user", "content": prompt}], "stream": False, "options": {"temperature": 0.0, "seed": payload["repeat_seed"]}}, timeout)
                raw = response.get("message", {}).get("content")
                if not isinstance(raw, str):
                    raise ValueError("missing message.content")
                outcome, source, details = classify_response(raw, payload, task)
                row.update({"outcome": outcome, "raw_response": raw, "extracted_source": source, "source_hash": _hash(source) if source is not None else None, **details})
                for key in ("prompt_eval_count", "eval_count", "total_duration", "load_duration", "prompt_eval_duration", "eval_duration"):
                    row[key] = response.get(key)
                row["total_token_count"] = (response.get("prompt_eval_count") or 0) + (response.get("eval_count") or 0)
            except Exception as exc:
                row.update({"outcome": "infrastructure_failure", "exception_type": type(exc).__name__, "exception_message": str(exc), "raw_response": None, "extracted_source": None, "source_hash": None})
            row["completed_at"] = time.time(); row["wall_clock_seconds"] = time.monotonic() - started
            results.append(row)
    summary = summarize_results(results, run_id, time.monotonic() - started_run)
    (root / "cell_results.jsonl").write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in results), encoding="utf-8")
    (root / "failure_examples.jsonl").write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in results if row["outcome"] != "passed"), encoding="utf-8")
    (root / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = {"run_id": run_id, "treatment": treatment, "condition": condition, "task_ids": list(TASK_IDS), "repeat_seeds": list(repeat_seeds), "models": list(models), "expected_cells": len(tasks) * len(repeat_seeds) * len(models), "healer_executed": False, "retry_executed": False, "supersedes_run_id": supersedes_run_id, "supersede_reason": supersede_reason}
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def mark_engineering_invalid(run_directory: str | Path) -> None:
    root = Path(run_directory)
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else {"run_id": root.name}
    manifest.update({"analysis_status": "engineering_invalid", "invalid_reason": "Windows CP950 subprocess encoding corrupted Unicode candidate execution"})
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def summarize_results(rows: Sequence[dict[str, Any]], run_id: str, duration: float = 0.0) -> dict[str, Any]:
    counts = Counter(row["outcome"] for row in rows)
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows: groups[(row["model_tag"], row["task_id"])].append(row)
    marginal = [{"model_tag": model, "task_id": task, "pass_count": sum(row["outcome"] == "passed" for row in group)} for (model, task), group in groups.items() if 1 <= sum(row["outcome"] == "passed" for row in group) <= 2 or any(row["outcome"] in {"parse_minor", "schema_failure", "missing_entry_point"} for row in group)]
    rate = lambda subset: sum(row["outcome"] == "passed" for row in subset) / len(subset) if subset else 0.0
    return {"run_id": run_id, "total_cells": len(rows), "completed_cells": len(rows) - counts["infrastructure_failure"], "infrastructure_failures": counts["infrastructure_failure"], "duration_seconds": duration, "outcome_counts": dict(sorted(counts.items())), "pass_rate_by_model": {model: rate([row for row in rows if row["model_tag"] == model]) for model in MODEL_TAGS}, "pass_rate_by_difficulty": {str(level): rate([row for row in rows if row["difficulty_level"] == level]) for level in sorted({row["difficulty_level"] for row in rows})}, "stable_pass_cells": [dict(model_tag=m, task_id=t) for (m, t), group in groups.items() if len(group) == 3 and all(row["outcome"] == "passed" for row in group)], "unstable_cells": [dict(model_tag=m, task_id=t) for (m, t), group in groups.items() if 0 < sum(row["outcome"] == "passed" for row in group) < 3], "stable_failure_cells": [dict(model_tag=m, task_id=t) for (m, t), group in groups.items() if len(group) == 3 and not any(row["outcome"] == "passed" for row in group)], "candidate_marginal_cells": marginal}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--task-manifest", required=True); parser.add_argument("--output-root", required=True); parser.add_argument("--run-id", default=RUN_ID_DEFAULT); parser.add_argument("--ollama-url", default="http://localhost:11434"); parser.add_argument("--timeout", type=int, default=300); parser.add_argument("--supersedes-run-id"); parser.add_argument("--supersede-reason"); parser.add_argument("--condition", choices=("ab1", "ab2g", "ab2d"), default="ab1")
    args = parser.parse_args(argv)
    run_pilot(load_pilot_tasks(args.task_manifest), output_root=args.output_root, run_id=args.run_id, ollama_url=args.ollama_url, timeout=args.timeout, supersedes_run_id=args.supersedes_run_id, supersede_reason=args.supersede_reason, condition=args.condition)
    return 0


if __name__ == "__main__": raise SystemExit(main())
