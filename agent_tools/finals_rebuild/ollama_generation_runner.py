"""
Fail-closed Ollama HTTP generation runner for HumanEval/MBPP Ab1/Ab2g.

Scope
-----
Generates exactly two treatments — Ab1 (bare prompt) and Ab2g (bare prompt
plus a fixed, task-agnostic Generic Safety-and-Format Scaffold) — via the
local Ollama HTTP API. This module never:

  - generates Ab3-Core/Ab3-Full (those are deterministic re-derivations of
    an existing Ab2g completion, produced by core_adapter.py/spec_adapter.py
    via agent_tools.finals_rebuild.public_benchmark_runner; this module
    never regenerates them and never calls those adapters)
  - calls the Ollama CLI (HTTP API only, via `requests`)
  - persists chain-of-thought: a non-empty `thinking` field in the API
    response, or a literal `<think>`/`</think>` tag in the `response` text,
    fails the run closed rather than being silently stripped
  - silently strips Markdown code fences from a completion — a fenced
    response fails closed instead of being "cleaned up" into a fabricated
    completion
  - prepends the task prompt onto the completion, or accepts a completion
    that repeats the task's `def <entry_point>(...)` signature
  - retries a timed-out or non-200 request

Every failure mode is fail-closed: raises OllamaGenerationError (stage
selects "failed_preflight" vs "failed_generation") before any output file
is written for that task/treatment.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Sequence, Union

from agent_tools.finals_rebuild.benchmarks_adapter import (
    PublicBenchmarkTask,
    load_benchmark_tasks,
)

DEFAULT_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_TIMEOUT_SECONDS = 120.0

MODEL = "qwen3:8b"
SEED = 20260712
TEMPERATURE = 0
THINK = False

ALLOWED_TREATMENTS: Sequence[str] = ("ab1", "ab2g")

# Fixed, task-agnostic scaffold. Contains only the six allowed instruction
# categories — never a task-specific solution hint.
AB2G_SCAFFOLD = (
    "\n\n# Additional requirements:\n"
    "# - Return only executable Python code that completes the function above.\n"
    "# - Do not wrap the code in Markdown code fences (no ``` or ```python).\n"
    "# - Do not output any explanation or commentary outside the code.\n"
    "# - Preserve the given function name and signature exactly as provided.\n"
    "# - Do not change the intended meaning/behavior of the task.\n"
    "# - Do not add hints or solution guidance specific to this task.\n"
)

_STAGE_STATUS: Dict[str, str] = {
    "benchmark": "failed_preflight",
    "treatment": "failed_preflight",
    "tasks_load": "failed_preflight",
    "tags_preflight": "failed_preflight",
    "connection": "failed_generation",
    "timeout": "failed_generation",
    "http_status": "failed_generation",
    "json_parse": "failed_generation",
    "empty_response": "failed_generation",
    "think_leak": "failed_generation",
    "markdown_fence": "failed_generation",
    "duplicate_signature": "failed_generation",
    "empty_completion": "failed_generation",
}


class OllamaGenerationError(Exception):
    """Raised on any fail-closed invariant violation. *stage* selects the
    recorded status ("failed_preflight" vs "failed_generation")."""

    def __init__(self, stage: str, message: str) -> None:
        super().__init__(message)
        self.stage = stage
        self.status = _STAGE_STATUS[stage]


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------


def build_prompt(task_prompt: str, treatment: str) -> str:
    """Build the model-facing prompt for *treatment* from the official task
    prompt. Ab1 is the bare official prompt, byte-for-byte. Ab2g is the same
    official prompt with the fixed AB2G_SCAFFOLD appended — never a
    per-task-modified prompt."""
    if treatment == "ab1":
        return task_prompt
    if treatment == "ab2g":
        return task_prompt + AB2G_SCAFFOLD
    raise OllamaGenerationError(
        "treatment", f"treatment must be one of {ALLOWED_TREATMENTS}, got {treatment!r}"
    )


# ---------------------------------------------------------------------------
# Ollama HTTP API
# ---------------------------------------------------------------------------
#
# Uses only the standard library (urllib) — never shells out to the Ollama
# CLI, never adds a third-party HTTP dependency.


def _http_get_json(url: str, timeout_seconds: float, *, stage: str) -> Any:
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
            status = resp.getcode()
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise OllamaGenerationError(stage, f"GET {url} returned status {exc.code}") from exc
    except TimeoutError as exc:
        raise OllamaGenerationError(stage, f"GET {url} timed out after {timeout_seconds}s") from exc
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, TimeoutError):
            raise OllamaGenerationError(
                stage, f"GET {url} timed out after {timeout_seconds}s"
            ) from exc
        raise OllamaGenerationError(stage, f"GET {url} failed: {exc}") from exc

    if status != 200:
        raise OllamaGenerationError(stage, f"GET {url} returned status {status}")
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise OllamaGenerationError(stage, f"GET {url} returned invalid JSON: {exc}") from exc


def check_model_available(base_url: str, timeout_seconds: float) -> None:
    """GET /api/tags and fail closed unless MODEL is present. Never
    silently proceeds against a different/unpinned model."""
    url = base_url.rstrip("/") + "/api/tags"
    data = _http_get_json(url, timeout_seconds, stage="tags_preflight")

    models = data.get("models") if isinstance(data, dict) else None
    names = {
        m.get("name") or m.get("model")
        for m in models or []
        if isinstance(m, dict)
    }
    if MODEL not in names:
        raise OllamaGenerationError(
            "tags_preflight",
            f"model {MODEL!r} not found in /api/tags (available: {sorted(n for n in names if n)})",
        )


def _post_generate(prompt: str, base_url: str, timeout_seconds: float) -> Dict[str, Any]:
    """POST /api/generate with fixed model/seed/temperature/think. Never
    shells out, never retries on timeout/non-200."""
    url = base_url.rstrip("/") + "/api/generate"
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "think": THINK,
        "options": {
            "temperature": TEMPERATURE,
            "seed": SEED,
        },
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, method="POST", headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
            status = resp.getcode()
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise OllamaGenerationError(
            "http_status", f"POST /api/generate returned status {exc.code}"
        ) from exc
    except TimeoutError as exc:
        raise OllamaGenerationError(
            "timeout", f"POST /api/generate timed out after {timeout_seconds}s"
        ) from exc
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, TimeoutError):
            raise OllamaGenerationError(
                "timeout", f"POST /api/generate timed out after {timeout_seconds}s"
            ) from exc
        raise OllamaGenerationError(
            "connection", f"POST /api/generate failed: {exc}"
        ) from exc

    if status != 200:
        raise OllamaGenerationError(
            "http_status", f"POST /api/generate returned status {status}"
        )

    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise OllamaGenerationError(
            "json_parse", f"POST /api/generate returned invalid JSON: {exc}"
        ) from exc


_FENCE_PATTERN = re.compile(r"```")
_THINK_PATTERN = re.compile(r"</?think>", re.IGNORECASE)


def extract_completion(raw_json: Dict[str, Any], entry_point: Optional[str]) -> str:
    """Validate *raw_json* (the parsed /api/generate response body) and
    return the completion text, unmodified. Fails closed on: empty
    response, a non-empty `thinking` field, a `<think>`/`</think>` tag in
    the response text, a Markdown code fence, or a repeated function
    signature. Never strips a fence or a think-tag and proceeds — that
    would silently fabricate a "clean" completion from tainted output."""
    response_text = raw_json.get("response")
    if not isinstance(response_text, str) or not response_text.strip():
        raise OllamaGenerationError(
            "empty_response", f"empty or missing 'response' field: {raw_json!r}"
        )

    thinking = raw_json.get("thinking")
    if isinstance(thinking, str) and thinking.strip():
        raise OllamaGenerationError(
            "think_leak",
            "response contains a non-empty 'thinking' field despite think=false; "
            "refusing to discard it and proceed",
        )

    if _THINK_PATTERN.search(response_text):
        raise OllamaGenerationError(
            "think_leak",
            "response text contains a <think>/</think> tag; refusing to strip it "
            "and proceed",
        )

    if _FENCE_PATTERN.search(response_text):
        raise OllamaGenerationError(
            "markdown_fence",
            "response text contains a Markdown code fence ('```'); refusing to "
            "strip it and proceed",
        )

    if entry_point and re.search(rf"\bdef\s+{re.escape(entry_point)}\s*\(", response_text):
        raise OllamaGenerationError(
            "duplicate_signature",
            f"response repeats the function signature for entry_point={entry_point!r}",
        )

    return response_text


# ---------------------------------------------------------------------------
# Hashing / JSON writing
# ---------------------------------------------------------------------------


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _write_json_deterministic(obj: Any, path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialised = json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(serialised)


def _write_completions_jsonl(records: Sequence[Dict[str, Any]], path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def generate_treatment(
    tasks: Sequence[PublicBenchmarkTask],
    treatment: str,
    *,
    benchmark: str,
    base_url: str,
    timeout_seconds: float,
) -> List[Dict[str, Any]]:
    """Generate one treatment's completions for every task in *tasks*, in
    order. Fails closed (raises) on the first invalid task/treatment/HTTP
    outcome; never partially writes output for a failed task."""
    if treatment not in ALLOWED_TREATMENTS:
        raise OllamaGenerationError(
            "treatment", f"treatment must be one of {ALLOWED_TREATMENTS}, got {treatment!r}"
        )

    records: List[Dict[str, Any]] = []
    for task in tasks:
        prompt = build_prompt(task.prompt, treatment)
        start = time.monotonic()
        raw_json = _post_generate(prompt, base_url, timeout_seconds)
        elapsed_seconds = time.monotonic() - start

        completion = extract_completion(raw_json, task.entry_point)
        if not completion.strip():
            raise OllamaGenerationError(
                "empty_completion", f"task_id={task.task_id!r}: completion is empty"
            )

        records.append({
            "task_id": task.task_id,
            "sample_index": 0,
            "completion": completion,
            "metadata": {
                "benchmark": benchmark,
                "treatment": treatment,
                "model": MODEL,
                "seed": SEED,
                "temperature": TEMPERATURE,
                "think": THINK,
                "prompt_sha256": sha256_text(prompt),
                "raw_response_sha256": sha256_text(json.dumps(raw_json, sort_keys=True)),
                "generation_seconds": elapsed_seconds,
            },
        })
    return records


def run_ollama_generation(
    *,
    tasks_path: Union[str, pathlib.Path],
    benchmark: str,
    output_dir: Union[str, pathlib.Path],
    base_url: str = DEFAULT_BASE_URL,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> Dict[str, Any]:
    """Run the full fail-closed Ab1+Ab2g generation for every task in
    *tasks_path*, against the local Ollama HTTP API. Writes ab1.jsonl,
    ab2g.jsonl, and generation_manifest.json to *output_dir* only after
    every task/treatment has succeeded."""
    if benchmark not in ("humaneval", "mbpp"):
        raise OllamaGenerationError(
            "benchmark", f"benchmark must be 'humaneval' or 'mbpp', got {benchmark!r}"
        )

    output_dir = pathlib.Path(output_dir)

    tasks = load_benchmark_tasks(tasks_path, benchmark)
    if not tasks:
        raise OllamaGenerationError("tasks_load", f"{tasks_path}: no tasks loaded")

    check_model_available(base_url, timeout_seconds)

    per_treatment: Dict[str, List[Dict[str, Any]]] = {}
    for treatment in ALLOWED_TREATMENTS:
        per_treatment[treatment] = generate_treatment(
            tasks, treatment,
            benchmark=benchmark, base_url=base_url, timeout_seconds=timeout_seconds,
        )

    for treatment, records in per_treatment.items():
        _write_completions_jsonl(records, output_dir / f"{treatment}.jsonl")

    manifest = {
        "benchmark": benchmark,
        "model": MODEL,
        "seed": SEED,
        "temperature": TEMPERATURE,
        "think": THINK,
        "base_url": base_url,
        "task_ids": [t.task_id for t in tasks],
        "treatments": list(ALLOWED_TREATMENTS),
        "counts": {t: len(r) for t, r in per_treatment.items()},
        "status": "success",
    }
    _write_json_deterministic(manifest, output_dir / "generation_manifest.json")
    return manifest


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m agent_tools.finals_rebuild.ollama_generation_runner",
        description="Fail-closed Ollama HTTP generation runner for HumanEval/MBPP Ab1/Ab2g.",
    )
    parser.add_argument("--tasks-path", required=True)
    parser.add_argument("--benchmark", required=True, choices=("humaneval", "mbpp"))
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--timeout-seconds", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    try:
        run_ollama_generation(
            tasks_path=args.tasks_path,
            benchmark=args.benchmark,
            output_dir=args.output_dir,
            base_url=args.base_url,
            timeout_seconds=args.timeout_seconds,
        )
        return 0
    except OllamaGenerationError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
