"""
Per-sample fail-closed Ollama HTTP generation runner for HumanEval/MBPP
Ab1/Ab2g.

Scope
-----
Attempts exactly two treatments — Ab1 (bare prompt) and Ab2g (bare prompt
plus a fixed, task-agnostic Generic Safety-and-Format Scaffold) — for every
task, via the local Ollama HTTP API. Every (task_id, treatment,
sample_index) is an independent *attempt*: one attempt's failure never
aborts another task, another treatment, or the batch as a whole, never
deletes an already-successful attempt, and never fabricates a completion
for a failed attempt. This module never:

  - generates Ab3-Core/Ab3-Full itself (those are deterministic
    re-derivations of an existing Ab2g completion, produced by
    core_adapter.py/spec_adapter.py via
    agent_tools.finals_rebuild.public_benchmark_runner.
    run_public_benchmark_treatments(); this module only decides *whether*
    that function may be called — by checking Ab2g completeness — and
    never regenerates Ab3 itself)
  - calls the Ollama CLI (HTTP API only, via the standard library `urllib`)
  - persists chain-of-thought: a non-empty `thinking` field in the API
    response, or a literal `<think>`/`</think>` tag in the raw `response`
    text, fails that attempt closed rather than being silently stripped
  - runs its own regex/LLM extraction, or picks the first/last of multiple
    candidate code blocks: the completion is always produced by the
    existing, unmodified `agent_tools.finals_rebuild.extraction
    .extract_code()`, called with no additional disambiguation. An
    ambiguous (multiple candidate blocks) or empty extraction fails that
    attempt closed; extraction.py itself is never modified.
  - prepends the task prompt onto the completion, or edits the code that
    `extract_code()` returned
  - retries a timed-out or non-200 request

A Markdown code fence or explanatory prose surrounding a *single* code
block is not itself a failure — `extract_code()` handles that case and
returns "extracted". Only an ambiguous, empty, or unsupported extraction
status fails an attempt closed.

Each attempt is recorded as a deterministic record (see `run_attempt()`)
regardless of outcome. `run_ollama_generation()` always writes
`generation_attempts.jsonl`, `generation_summary.json`, `ab1_raw.jsonl`,
and `ab2g_raw.jsonl` — and `ab1.jsonl`/`ab2g.jsonl` containing only the
successfully-extracted completions for that treatment (created empty, not
omitted, when a treatment has zero successes).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from agent_tools.finals_rebuild.benchmarks_adapter import (
    PublicBenchmarkTask,
    load_benchmark_tasks,
)
from agent_tools.finals_rebuild.extraction import _FENCE_RE, extract_code
from agent_tools.finals_rebuild.public_benchmark_runner import (
    run_public_benchmark_treatments,
)

DEFAULT_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_TIMEOUT_SECONDS = 120.0

MODEL = "qwen3:8b"
SEED = 20260712
TEMPERATURE = 0
THINK = False

# Fixed generation + write order: for every task, Ab1 is attempted before
# Ab2g. Never reordered based on outcome.
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

# Preflight-only stages: these abort the whole run before any attempt is
# made (nothing could succeed without them), never a single attempt.
_STAGE_STATUS: Dict[str, str] = {
    "benchmark": "failed_preflight",
    "treatment": "failed_preflight",
    "tasks_load": "failed_preflight",
    "tags_preflight": "failed_preflight",
    "version_preflight": "failed_preflight",
    "git_commit": "failed_preflight",
    "connection": "failed_generation",
    "timeout": "failed_generation",
    "http_status": "failed_generation",
    "json_parse": "failed_generation",
    "empty_response": "failed_generation",
    "think_leak": "failed_generation",
}


class OllamaGenerationError(Exception):
    """Raised on a fail-closed invariant violation. *stage* selects the
    recorded status ("failed_preflight" vs "failed_generation"). Raised
    from the HTTP/response-validation helpers; `run_attempt()` catches
    these per-attempt and converts them into a "failed" attempt record
    instead of propagating — only preflight (model/tasks) failures
    actually abort the run."""

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
    """GET /api/tags and fail closed (aborting the whole run — no attempt
    can possibly succeed) unless MODEL is present."""
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


def fetch_ollama_provenance(base_url: str, timeout_seconds: float) -> Dict[str, Any]:
    """GET /api/tags and /api/version and return the reproducibility
    provenance for MODEL: model_name, model_digest, model_size,
    model_modified_at, ollama_version, api_base_url. This metadata can only
    be captured at generation time (the model blob or server may change
    later), so every field the server is expected to provide is fail-closed:
    model missing, digest missing/blank, version endpoint failing, or a
    blank version string all abort the run — a bare model *tag* alone is
    never accepted as provenance."""
    tags_url = base_url.rstrip("/") + "/api/tags"
    tags_data = _http_get_json(tags_url, timeout_seconds, stage="tags_preflight")

    models = tags_data.get("models") if isinstance(tags_data, dict) else None
    entry: Optional[Dict[str, Any]] = None
    for m in models or []:
        if isinstance(m, dict) and (m.get("name") or m.get("model")) == MODEL:
            entry = m
            break
    if entry is None:
        available = sorted(
            n for n in (
                (m.get("name") or m.get("model"))
                for m in models or [] if isinstance(m, dict)
            ) if n
        )
        raise OllamaGenerationError(
            "tags_preflight",
            f"model {MODEL!r} not found in /api/tags (available: {available})",
        )

    digest = entry.get("digest")
    if not isinstance(digest, str) or not digest.strip():
        raise OllamaGenerationError(
            "tags_preflight",
            f"model {MODEL!r} has no digest in /api/tags — refusing to record "
            f"a bare model tag as provenance",
        )

    version_url = base_url.rstrip("/") + "/api/version"
    version_data = _http_get_json(version_url, timeout_seconds, stage="version_preflight")
    version = version_data.get("version") if isinstance(version_data, dict) else None
    if not isinstance(version, str) or not version.strip():
        raise OllamaGenerationError(
            "version_preflight",
            f"GET /api/version returned no usable version string: {version_data!r}",
        )

    return {
        "model_name": MODEL,
        "model_digest": digest,
        "model_size": entry.get("size"),
        "model_modified_at": entry.get("modified_at"),
        "ollama_version": version,
        "api_base_url": base_url,
    }


def _resolve_runner_git_commit() -> str:
    """Resolve the runner's own git commit for the generation manifest.
    Fails closed if git is unavailable or the repo state can't be read —
    a manifest without a pinned runner commit is not reproducible."""
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=30,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise OllamaGenerationError(
            "git_commit", f"failed to resolve runner git commit: {exc}"
        ) from exc
    commit = (proc.stdout or "").strip()
    if proc.returncode != 0 or not commit:
        raise OllamaGenerationError(
            "git_commit",
            f"git rev-parse HEAD failed (rc={proc.returncode}, stderr={proc.stderr!r})",
        )
    return commit


def _post_generate(prompt: str, base_url: str, timeout_seconds: float) -> Dict[str, Any]:
    """POST /api/generate with fixed model/seed/temperature/think. Never
    shells out, never retries on timeout/non-200. Raises
    OllamaGenerationError on any transport/HTTP/JSON failure — the caller
    (run_attempt) converts this into a per-attempt failure record."""
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


_THINK_PATTERN = re.compile(r"</?think>", re.IGNORECASE)


def validate_raw_response(raw_json: Dict[str, Any]) -> str:
    """Validate *raw_json* (the parsed /api/generate response body) and
    return the raw response text, unmodified. Fails closed on: empty
    response, a non-empty `thinking` field, or a `<think>`/`</think>` tag
    in the response text. Never strips a think-tag and proceeds — that
    would silently discard a chain-of-thought leak instead of refusing it."""
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

    return response_text


# ---------------------------------------------------------------------------
# Extraction (delegates entirely to extraction.extract_code(); never
# re-implements fence/prose parsing and never picks a "first"/"last"
# candidate among multiple blocks — extraction.py's own ambiguity rule is
# authoritative and unmodified).
# ---------------------------------------------------------------------------


def _has_surrounding_text(raw_text: str, extraction_method: str) -> bool:
    """True if *raw_text* has non-whitespace content outside the single
    fenced block `extract_code()` used, for diagnostics only — never used
    to alter the extracted completion itself."""
    if extraction_method not in ("fenced_python", "fenced_other"):
        return False
    match = _FENCE_RE.search(raw_text)
    if match is None:
        return False
    before = raw_text[: match.start()].strip()
    after = raw_text[match.end() :].strip()
    return bool(before or after)


def analyze_extraction(raw_text: str) -> Dict[str, Any]:
    """Run extraction.extract_code() over *raw_text* and return a
    diagnostics dict. Never raises — success/failure is reported via the
    "ok" key so the caller can build a per-attempt record either way."""
    result = extract_code(raw_text)
    had_fence = result.diagnostics.get("total_fenced_blocks", 0) > 0
    had_surrounding_text = _has_surrounding_text(raw_text, result.extraction_method)
    ok = (
        result.extraction_status == "extracted"
        and bool(result.extracted_code)
        and bool(result.extracted_code.strip())
    )
    return {
        "ok": ok,
        "completion": result.extracted_code if ok else None,
        "extraction_status": result.extraction_status,
        "extraction_method": result.extraction_method,
        "total_fenced_blocks": result.diagnostics.get("total_fenced_blocks", 0),
        "python_fenced_blocks": result.diagnostics.get("python_fenced_blocks", 0),
        "had_markdown_fence": had_fence,
        "had_surrounding_text": had_surrounding_text,
    }


# ---------------------------------------------------------------------------
# Hashing / JSON writing
# ---------------------------------------------------------------------------


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_or_none(text: Optional[str]) -> Optional[str]:
    return sha256_text(text) if text is not None else None


def _write_json_deterministic(obj: Any, path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialised = json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(serialised)


def _write_completions_jsonl(records: Sequence[Dict[str, Any]], path: pathlib.Path) -> None:
    """Write *records* as JSONL, one per line. Writes (creates) the file
    even when *records* is empty — a zero-success treatment still gets a
    valid, empty output file rather than no file at all."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Per-attempt orchestration
# ---------------------------------------------------------------------------


def _build_attempt(
    *,
    task_id: str,
    treatment: str,
    status: str,
    failure_stage: Optional[str],
    failure_reason: Optional[str],
    raw_response: Optional[str],
    completion: Optional[str],
    extraction_status: Optional[str],
    extraction_method: Optional[str],
    total_fenced_blocks: Optional[int],
    python_fenced_blocks: Optional[int],
    had_markdown_fence: Optional[bool],
    had_surrounding_text: Optional[bool],
    elapsed_seconds: float,
    metadata: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "task_id": task_id,
        "sample_index": 0,
        "treatment": treatment,
        "status": status,
        "failure_stage": failure_stage,
        "failure_reason": failure_reason,
        "raw_response": raw_response,
        "raw_response_sha256": _sha256_or_none(raw_response),
        "completion": completion,
        "completion_sha256": _sha256_or_none(completion),
        "extraction_status": extraction_status,
        "extraction_method": extraction_method,
        "total_fenced_blocks": total_fenced_blocks,
        "python_fenced_blocks": python_fenced_blocks,
        "had_markdown_fence": had_markdown_fence,
        "had_surrounding_text": had_surrounding_text,
        "elapsed_seconds": elapsed_seconds,
        "metadata": metadata,
    }


def run_attempt(
    task: PublicBenchmarkTask,
    treatment: str,
    *,
    benchmark: str,
    base_url: str,
    timeout_seconds: float,
) -> Dict[str, Any]:
    """Run exactly one (task, treatment, sample_index=0) attempt and always
    return an attempt record — never raises for a request/validation/
    extraction failure (those become status="failed" records). Only an
    invalid *treatment* itself raises, since that is a caller programming
    error, not a runtime generation failure."""
    prompt = build_prompt(task.prompt, treatment)
    metadata = {
        "benchmark": benchmark,
        "treatment": treatment,
        "model": MODEL,
        "seed": SEED,
        "temperature": TEMPERATURE,
        "think": THINK,
        "prompt_sha256": sha256_text(prompt),
    }
    start = time.monotonic()

    try:
        raw_json = _post_generate(prompt, base_url, timeout_seconds)
    except OllamaGenerationError as exc:
        return _build_attempt(
            task_id=task.task_id, treatment=treatment, status="failed",
            failure_stage="ollama_request", failure_reason=str(exc),
            raw_response=None, completion=None,
            extraction_status=None, extraction_method=None,
            total_fenced_blocks=None, python_fenced_blocks=None,
            had_markdown_fence=None, had_surrounding_text=None,
            elapsed_seconds=time.monotonic() - start, metadata=metadata,
        )

    # Preserve whatever response text the API returned, even if validation
    # below rejects it (e.g. a <think> leak) — the raw text is still saved.
    raw_response_seen = raw_json.get("response") if isinstance(raw_json.get("response"), str) else None

    try:
        validated_response = validate_raw_response(raw_json)
    except OllamaGenerationError as exc:
        return _build_attempt(
            task_id=task.task_id, treatment=treatment, status="failed",
            failure_stage="response_validation", failure_reason=str(exc),
            raw_response=raw_response_seen, completion=None,
            extraction_status=None, extraction_method=None,
            total_fenced_blocks=None, python_fenced_blocks=None,
            had_markdown_fence=None, had_surrounding_text=None,
            elapsed_seconds=time.monotonic() - start, metadata=metadata,
        )

    analysis = analyze_extraction(validated_response)
    if not analysis["ok"]:
        return _build_attempt(
            task_id=task.task_id, treatment=treatment, status="failed",
            failure_stage="extraction",
            failure_reason=(
                f"extraction_status={analysis['extraction_status']!r} "
                f"extraction_method={analysis['extraction_method']!r}"
            ),
            raw_response=validated_response, completion=None,
            extraction_status=analysis["extraction_status"],
            extraction_method=analysis["extraction_method"],
            total_fenced_blocks=analysis["total_fenced_blocks"],
            python_fenced_blocks=analysis["python_fenced_blocks"],
            had_markdown_fence=analysis["had_markdown_fence"],
            had_surrounding_text=analysis["had_surrounding_text"],
            elapsed_seconds=time.monotonic() - start, metadata=metadata,
        )

    return _build_attempt(
        task_id=task.task_id, treatment=treatment, status="success",
        failure_stage=None, failure_reason=None,
        raw_response=validated_response, completion=analysis["completion"],
        extraction_status=analysis["extraction_status"],
        extraction_method=analysis["extraction_method"],
        total_fenced_blocks=analysis["total_fenced_blocks"],
        python_fenced_blocks=analysis["python_fenced_blocks"],
        had_markdown_fence=analysis["had_markdown_fence"],
        had_surrounding_text=analysis["had_surrounding_text"],
        elapsed_seconds=time.monotonic() - start, metadata=metadata,
    )


def run_generation_attempts(
    tasks: Sequence[PublicBenchmarkTask],
    *,
    benchmark: str,
    base_url: str,
    timeout_seconds: float,
) -> List[Dict[str, Any]]:
    """Run every (task, treatment) attempt in fixed order: task order, then
    Ab1 before Ab2g within each task. A failed attempt never skips,
    reorders, or removes any other attempt."""
    attempts: List[Dict[str, Any]] = []
    for task in tasks:
        for treatment in ALLOWED_TREATMENTS:
            attempts.append(
                run_attempt(
                    task, treatment,
                    benchmark=benchmark, base_url=base_url, timeout_seconds=timeout_seconds,
                )
            )
    return attempts


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


def build_summary(attempts: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate counts over *attempts*. Never computes or claims a
    pass@1-style correctness metric — this is generation/extraction
    bookkeeping only."""

    def _count(pred) -> int:
        return sum(1 for a in attempts if pred(a))

    return {
        "total_attempts": len(attempts),
        "successful_attempts": _count(lambda a: a["status"] == "success"),
        "failed_attempts": _count(lambda a: a["status"] == "failed"),
        "ab1_attempts": _count(lambda a: a["treatment"] == "ab1"),
        "ab1_successes": _count(lambda a: a["treatment"] == "ab1" and a["status"] == "success"),
        "ab1_failures": _count(lambda a: a["treatment"] == "ab1" and a["status"] == "failed"),
        "ab2g_attempts": _count(lambda a: a["treatment"] == "ab2g"),
        "ab2g_successes": _count(lambda a: a["treatment"] == "ab2g" and a["status"] == "success"),
        "ab2g_failures": _count(lambda a: a["treatment"] == "ab2g" and a["status"] == "failed"),
        "extraction_ambiguous_count": _count(lambda a: a["extraction_status"] == "ambiguous"),
        "extraction_empty_count": _count(lambda a: a["extraction_status"] == "empty"),
        "api_failure_count": _count(lambda a: a["failure_stage"] == "ollama_request"),
        "fence_count": _count(lambda a: bool(a["had_markdown_fence"])),
        "surrounding_text_count": _count(lambda a: bool(a["had_surrounding_text"])),
    }


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def run_ollama_generation(
    *,
    tasks_path: Union[str, pathlib.Path],
    benchmark: str,
    output_dir: Union[str, pathlib.Path],
    base_url: str = DEFAULT_BASE_URL,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    runner_git_commit: Optional[str] = None,
) -> Dict[str, Any]:
    """Run every (task, treatment) attempt for *tasks_path* against the
    local Ollama HTTP API. Always writes generation_attempts.jsonl,
    generation_summary.json, generation_manifest.json, ab1_raw.jsonl,
    ab2g_raw.jsonl, ab1.jsonl, and ab2g.jsonl to *output_dir* (the last two
    contain only successful completions for that treatment, and are written
    empty rather than omitted when a treatment has zero successes). Only a
    preflight failure (invalid benchmark, no tasks, model/digest missing
    from /api/tags, /api/version unusable, unresolvable runner git commit)
    aborts the run before any attempt/output; a per-attempt failure never
    does.

    *runner_git_commit* is recorded in the manifest; when None it is
    resolved from `git rev-parse HEAD` (fail-closed if unresolvable)."""
    if benchmark not in ("humaneval", "mbpp"):
        raise OllamaGenerationError(
            "benchmark", f"benchmark must be 'humaneval' or 'mbpp', got {benchmark!r}"
        )

    output_dir = pathlib.Path(output_dir)

    tasks = load_benchmark_tasks(tasks_path, benchmark)
    if not tasks:
        raise OllamaGenerationError("tasks_load", f"{tasks_path}: no tasks loaded")

    # Captures /api/tags digest + /api/version and enforces MODEL presence
    # (subsumes the bare check_model_available() existence check).
    provenance = fetch_ollama_provenance(base_url, timeout_seconds)
    if runner_git_commit is None:
        runner_git_commit = _resolve_runner_git_commit()

    attempts = run_generation_attempts(
        tasks, benchmark=benchmark, base_url=base_url, timeout_seconds=timeout_seconds
    )

    _write_completions_jsonl(attempts, output_dir / "generation_attempts.jsonl")

    for treatment in ALLOWED_TREATMENTS:
        raw_records = [
            {
                "task_id": a["task_id"],
                "sample_index": a["sample_index"],
                "raw_response": a["raw_response"],
                "raw_response_sha256": a["raw_response_sha256"],
            }
            for a in attempts if a["treatment"] == treatment
        ]
        _write_completions_jsonl(raw_records, output_dir / f"{treatment}_raw.jsonl")

        completion_records = [
            {
                "task_id": a["task_id"],
                "sample_index": a["sample_index"],
                "completion": a["completion"],
                "metadata": a["metadata"],
            }
            for a in attempts if a["treatment"] == treatment and a["status"] == "success"
        ]
        _write_completions_jsonl(completion_records, output_dir / f"{treatment}.jsonl")

    summary = build_summary(attempts)
    _write_json_deterministic(summary, output_dir / "generation_summary.json")

    manifest = {
        **provenance,
        "runner_git_commit": runner_git_commit,
        "benchmark": benchmark,
        "model": MODEL,
        "seed": SEED,
        "temperature": TEMPERATURE,
        "think": THINK,
        "timeout_seconds": timeout_seconds,
        "task_ids": [t.task_id for t in tasks],
        "treatments": list(ALLOWED_TREATMENTS),
    }
    _write_json_deterministic(manifest, output_dir / "generation_manifest.json")
    return summary


# ---------------------------------------------------------------------------
# Treatment-stage gating (Ab3-Core/Ab3-Full)
# ---------------------------------------------------------------------------


def check_ab2g_complete(
    tasks: Sequence[PublicBenchmarkTask], attempts: Sequence[Dict[str, Any]]
) -> Tuple[bool, List[str]]:
    """Return (is_complete, missing_task_ids) — whether every task in
    *tasks* has a successful Ab2g attempt. Never inspects Ab1: Ab3-Core/
    Ab3-Full are derived only from Ab2g."""
    ab2g_success_ids = {
        a["task_id"] for a in attempts if a["treatment"] == "ab2g" and a["status"] == "success"
    }
    missing = [t.task_id for t in tasks if t.task_id not in ab2g_success_ids]
    return (not missing, missing)


def run_treatment_stage(
    *,
    tasks: Sequence[PublicBenchmarkTask],
    attempts: Sequence[Dict[str, Any]],
    tasks_path: Union[str, pathlib.Path],
    ab1_completions_path: Union[str, pathlib.Path],
    ab2g_completions_path: Union[str, pathlib.Path],
    benchmark: str,
    artifact_root: Union[str, pathlib.Path],
    evaluator_git_commit: str,
) -> Dict[str, Any]:
    """Call the existing, unmodified
    public_benchmark_runner.run_public_benchmark_treatments() only if every
    task has a successful Ab2g attempt. Never calls it, and never fabricates
    a missing Ab2g completion, otherwise — returns which task_ids are
    missing instead."""
    is_complete, missing = check_ab2g_complete(tasks, attempts)
    if not is_complete:
        return {"ran": False, "missing_ab2g_task_ids": missing}

    summary = run_public_benchmark_treatments(
        tasks_path=tasks_path,
        ab1_completions_path=ab1_completions_path,
        ab2g_completions_path=ab2g_completions_path,
        benchmark=benchmark,
        artifact_root=artifact_root,
        evaluator_git_commit=evaluator_git_commit,
    )
    return {"ran": True, "missing_ab2g_task_ids": [], "summary": summary}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m agent_tools.finals_rebuild.ollama_generation_runner",
        description="Per-sample fail-closed Ollama HTTP generation runner for HumanEval/MBPP Ab1/Ab2g.",
    )
    parser.add_argument("--tasks-path", required=True)
    parser.add_argument("--benchmark", required=True, choices=("humaneval", "mbpp"))
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--timeout-seconds", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument(
        "--runner-git-commit", default=None,
        help="Recorded in generation_manifest.json; resolved via "
             "`git rev-parse HEAD` (fail-closed) when omitted.",
    )
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
            runner_git_commit=args.runner_git_commit,
        )
        return 0
    except OllamaGenerationError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
