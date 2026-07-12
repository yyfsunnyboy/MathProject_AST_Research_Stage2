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
import ast
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
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from agent_tools.finals_rebuild.benchmarks_adapter import (
    PublicBenchmarkTask,
    load_benchmark_tasks,
)
from agent_tools.finals_rebuild.extraction import _FENCE_RE, extract_code
from agent_tools.finals_rebuild.public_benchmark_runner import (
    run_public_benchmark_treatments,
    run_public_benchmark_treatments_from_attempts,
)

DEFAULT_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_TIMEOUT_SECONDS = 120.0

DEFAULT_MODEL_8B = "qwen3:8b"
MODEL = DEFAULT_MODEL_8B  # backward-compat alias for existing 8B runs/tests

DEFAULT_SMOKE_MODEL = "qwen3:4b-instruct-2507-q4_K_M"
SMOKE_MODEL_DIGEST_PREFIX = "0edcdef34593"
SMOKE_TASK_COUNT = 20

SEED = 20260712
TEMPERATURE = 0
TOP_P = 1.0
TOP_K = 1
NUM_PREDICT = 2048  # conservative fixed cap for HumanEval-length completions
API_ENDPOINT = "/api/chat"
RESPONSE_FIELD = "message.content"

PROMPT_TEMPLATE_VERSION = "humaneval_official_prompt_v1"
BENCHMARK_VERSION_HUMANEVAL_PLUS = "evalplus_humaneval+"
TASK_SELECTION_POLICY_FIRST_N = "official_input_order_first_n"
RUN_TYPE_SMOKE = "engineering_smoke_test"
ANALYSIS_STATUS_SMOKE_EXCLUDED = "excluded_from_confirmatory_results"
OFFICIAL_EVALPLUS_STATUS_SMOKE = "not_run_engineering_smoke"
OFFICIAL_EVALPLUS_BLOCKER = "requires_wsl_linux_and_supported_coverage"

SMOKE_OUTPUT_RELATIVE = pathlib.Path(
    "artifacts/engineering_smoke_test/humaneval_plus/qwen3_4b_instruct_2507"
)

_MODEL_PROFILES: Dict[str, Dict[str, Any]] = {
    DEFAULT_SMOKE_MODEL: {
        "architecture": "qwen3",
        "parameters": "4.0B",
        "quantization": "Q4_K_M",
        "expected_digest_prefix": SMOKE_MODEL_DIGEST_PREFIX,
    },
    DEFAULT_MODEL_8B: {
        "architecture": "qwen3",
        "parameters": "8B",
        "quantization": None,
        "expected_digest_prefix": None,
    },
}


@dataclass(frozen=True)
class OllamaGenerationSettings:
    """Fixed generation parameters sent to Ollama /api/chat on every call."""

    model: str
    seed: int = SEED
    temperature: float = TEMPERATURE
    top_p: float = TOP_P
    top_k: int = TOP_K
    num_predict: int = NUM_PREDICT
    api_endpoint: str = API_ENDPOINT
    response_field: str = RESPONSE_FIELD
    expected_digest_prefix: Optional[str] = None

    @classmethod
    def for_model(cls, model: str) -> "OllamaGenerationSettings":
        profile = _MODEL_PROFILES.get(model, {})
        return cls(
            model=model,
            expected_digest_prefix=profile.get("expected_digest_prefix"),
        )

    @classmethod
    def smoke_default(cls) -> "OllamaGenerationSettings":
        return cls.for_model(DEFAULT_SMOKE_MODEL)

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


def check_model_available(
    base_url: str, timeout_seconds: float, *, model: str = MODEL
) -> None:
    """GET /api/tags and fail closed unless *model* is present."""
    url = base_url.rstrip("/") + "/api/tags"
    data = _http_get_json(url, timeout_seconds, stage="tags_preflight")

    models = data.get("models") if isinstance(data, dict) else None
    names = {
        m.get("name") or m.get("model")
        for m in models or []
        if isinstance(m, dict)
    }
    if model not in names:
        raise OllamaGenerationError(
            "tags_preflight",
            f"model {model!r} not found in /api/tags (available: {sorted(n for n in names if n)})",
        )


def fetch_ollama_provenance(
    base_url: str,
    timeout_seconds: float,
    *,
    model: str = MODEL,
    expected_digest_prefix: Optional[str] = None,
) -> Dict[str, Any]:
    """GET /api/tags and /api/version and return reproducibility provenance
    for *model*. When *expected_digest_prefix* is set, the model digest must
    contain that prefix or the run aborts fail-closed."""
    tags_url = base_url.rstrip("/") + "/api/tags"
    tags_data = _http_get_json(tags_url, timeout_seconds, stage="tags_preflight")

    models = tags_data.get("models") if isinstance(tags_data, dict) else None
    entry: Optional[Dict[str, Any]] = None
    for m in models or []:
        if isinstance(m, dict) and (m.get("name") or m.get("model")) == model:
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
            f"model {model!r} not found in /api/tags (available: {available})",
        )

    digest = entry.get("digest")
    if not isinstance(digest, str) or not digest.strip():
        raise OllamaGenerationError(
            "tags_preflight",
            f"model {model!r} has no digest in /api/tags — refusing to record "
            f"a bare model tag as provenance",
        )

    if expected_digest_prefix and expected_digest_prefix not in digest:
        raise OllamaGenerationError(
            "tags_preflight",
            f"model {model!r} digest {digest!r} does not match required prefix "
            f"{expected_digest_prefix!r}; refusing to generate",
        )

    version_url = base_url.rstrip("/") + "/api/version"
    version_data = _http_get_json(version_url, timeout_seconds, stage="version_preflight")
    version = version_data.get("version") if isinstance(version_data, dict) else None
    if not isinstance(version, str) or not version.strip():
        raise OllamaGenerationError(
            "version_preflight",
            f"GET /api/version returned no usable version string: {version_data!r}",
        )

    profile = _MODEL_PROFILES.get(model, {})
    model_size_gb = None
    if isinstance(entry.get("size"), (int, float)) and entry["size"] > 0:
        model_size_gb = round(entry["size"] / (1024 ** 3), 1)

    return {
        "model_tag": model,
        "model_name": model,
        "model_digest": digest,
        "model_size": entry.get("size"),
        "model_size_gb": model_size_gb,
        "model_modified_at": entry.get("modified_at"),
        "architecture": profile.get("architecture"),
        "parameters": profile.get("parameters"),
        "quantization": profile.get("quantization"),
        "runtime": "Ollama",
        "runtime_version": version,
        "ollama_version": version,
        "api_endpoint": API_ENDPOINT,
        "response_field": RESPONSE_FIELD,
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


def _post_chat(
    prompt: str,
    base_url: str,
    timeout_seconds: float,
    settings: OllamaGenerationSettings,
) -> Dict[str, Any]:
    """POST /api/chat with fixed model/seed/temperature/top_p/top_k/num_predict.
    Never shells out, never retries on timeout/non-200."""
    url = base_url.rstrip("/") + settings.api_endpoint
    payload = {
        "model": settings.model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {
            "temperature": settings.temperature,
            "seed": settings.seed,
            "top_p": settings.top_p,
            "top_k": settings.top_k,
            "num_predict": settings.num_predict,
        },
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, method="POST", headers={"Content-Type": "application/json"}
    )
    endpoint_label = settings.api_endpoint
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
            status = resp.getcode()
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise OllamaGenerationError(
            "http_status", f"POST {endpoint_label} returned status {exc.code}"
        ) from exc
    except TimeoutError as exc:
        raise OllamaGenerationError(
            "timeout", f"POST {endpoint_label} timed out after {timeout_seconds}s"
        ) from exc
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, TimeoutError):
            raise OllamaGenerationError(
                "timeout", f"POST {endpoint_label} timed out after {timeout_seconds}s"
            ) from exc
        raise OllamaGenerationError(
            "connection", f"POST {endpoint_label} failed: {exc}"
        ) from exc

    if status != 200:
        raise OllamaGenerationError(
            "http_status", f"POST {endpoint_label} returned status {status}"
        )

    try:
        parsed = json.loads(body)
    except json.JSONDecodeError as exc:
        raise OllamaGenerationError(
            "json_parse", f"POST {endpoint_label} returned invalid JSON: {exc}"
        ) from exc

    if isinstance(parsed, dict):
        parsed["_ollama_response_metadata"] = {
            "http_status": status,
            "raw_body": body,
            "api_endpoint": settings.api_endpoint,
            "response_field": settings.response_field,
        }
    return parsed


_THINK_PATTERN = re.compile(r"</?think>", re.IGNORECASE)


def detect_reasoning_leakage(raw_json: Dict[str, Any], content: str) -> bool:
    """Detect chain-of-thought leakage without stripping or repairing it."""
    message = raw_json.get("message") if isinstance(raw_json.get("message"), dict) else {}
    thinking = message.get("thinking")
    if isinstance(thinking, str) and thinking.strip():
        return True
    if _THINK_PATTERN.search(content):
        return True
    legacy_thinking = raw_json.get("thinking")
    if isinstance(legacy_thinking, str) and legacy_thinking.strip():
        return True
    return False


def validate_chat_response(raw_json: Dict[str, Any]) -> Tuple[str, bool]:
    """Validate *raw_json* (/api/chat body) and return (message.content,
    reasoning_leakage_detected). Fails closed on empty/missing content or
    detected leakage — never strips think-tags and proceeds."""
    message = raw_json.get("message")
    if not isinstance(message, dict):
        raise OllamaGenerationError(
            "empty_response",
            f"missing or invalid 'message' object: {raw_json!r}",
        )

    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise OllamaGenerationError(
            "empty_response",
            f"empty or missing message.content: {raw_json!r}",
        )

    leakage = detect_reasoning_leakage(raw_json, content)
    if leakage:
        raise OllamaGenerationError(
            "think_leak",
            "response contains reasoning leakage; refusing to discard it and proceed",
        )

    return content, leakage


def validate_raw_response(raw_json: Dict[str, Any]) -> str:
    """Backward-compatible wrapper: returns message.content only."""
    content, _ = validate_chat_response(raw_json)
    return content


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


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def resolve_repo_root(start: Optional[pathlib.Path] = None) -> pathlib.Path:
    """Best-effort repo root for default smoke output paths."""
    if start is None:
        start = pathlib.Path(__file__).resolve()
    for parent in [start, *start.parents]:
        if (parent / ".git").is_dir():
            return parent
    return pathlib.Path.cwd()


def default_smoke_output_dir(repo_root: Optional[Union[str, pathlib.Path]] = None) -> pathlib.Path:
    root = pathlib.Path(repo_root) if repo_root is not None else resolve_repo_root()
    return root / SMOKE_OUTPUT_RELATIVE


def select_tasks_official_first_n(
    tasks: Sequence[PublicBenchmarkTask], n: int
) -> List[PublicBenchmarkTask]:
    """Deterministic first-*n* selection in official input order."""
    if n <= 0:
        raise OllamaGenerationError("tasks_load", f"max_tasks must be positive, got {n!r}")
    if len(tasks) < n:
        raise OllamaGenerationError(
            "tasks_load",
            f"input has {len(tasks)} tasks but {n} required for "
            f"{TASK_SELECTION_POLICY_FIRST_N}",
        )
    return list(tasks[:n])


def entry_point_preflight(
    extracted_candidate: Optional[str],
    *,
    entry_point: str,
    prompt: str,
) -> Dict[str, Any]:
    """Record-only AST/entry-point checks before any official evaluator."""
    if not extracted_candidate or not extracted_candidate.strip():
        return {
            "parse_status": "skipped_no_candidate",
            "entry_point_definition_count": 0,
            "entry_point_definition_category": "zero",
            "duplicate_prompt_skeleton_suspected": False,
        }

    try:
        tree = ast.parse(extracted_candidate)
        parse_status = "success"
        parse_error = None
    except SyntaxError as exc:
        return {
            "parse_status": "failed",
            "parse_error": str(exc),
            "entry_point_definition_count": 0,
            "entry_point_definition_category": "zero",
            "duplicate_prompt_skeleton_suspected": False,
        }

    def_count = sum(
        1
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == entry_point
    )
    if def_count == 0:
        category = "zero"
    elif def_count == 1:
        category = "one"
    else:
        category = "multiple"

    prompt_has_skeleton = f"def {entry_point}" in prompt
    duplicate_suspected = prompt_has_skeleton and def_count > 1

    return {
        "parse_status": parse_status,
        "parse_error": parse_error,
        "entry_point_definition_count": def_count,
        "entry_point_definition_category": category,
        "duplicate_prompt_skeleton_suspected": duplicate_suspected,
    }


def _attempt_resume_key(
    attempt: Dict[str, Any],
) -> Tuple[str, str, str, str]:
    meta = attempt.get("metadata") if isinstance(attempt.get("metadata"), dict) else {}
    return (
        str(attempt.get("task_id", "")),
        str(attempt.get("treatment", "")),
        str(meta.get("model_digest", "")),
        str(meta.get("prompt_sha256", "")),
    )


def is_resume_complete(attempt: Dict[str, Any]) -> bool:
    """An attempt is resumable only when raw response was fully saved."""
    return (
        attempt.get("generation_status") == "success"
        or attempt.get("status") == "success"
    ) and isinstance(attempt.get("raw_response"), str) and bool(
        attempt["raw_response"].strip()
    ) and bool(attempt.get("raw_response_sha256"))


def load_completed_attempts(path: Union[str, pathlib.Path]) -> Dict[Tuple[str, str, str, str], Dict[str, Any]]:
    p = pathlib.Path(path)
    if not p.is_file():
        return {}
    completed: Dict[Tuple[str, str, str, str], Dict[str, Any]] = {}
    for line_no, line in enumerate(p.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            rec = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise OllamaGenerationError(
                "tasks_load",
                f"{p}: line {line_no}: invalid JSON in generation_attempts.jsonl: {exc}",
            ) from exc
        if not isinstance(rec, dict):
            continue
        if is_resume_complete(rec):
            completed[_attempt_resume_key(rec)] = rec
    return completed


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
    entry_point: Optional[str],
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
    reasoning_leakage_detected: Optional[bool] = None,
    parse_status: Optional[str] = None,
    entry_point_definition_count: Optional[int] = None,
    entry_point_definition_category: Optional[str] = None,
    duplicate_prompt_skeleton_suspected: Optional[bool] = None,
    ollama_response_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    extracted_candidate = completion
    return {
        "task_id": task_id,
        "entry_point": entry_point,
        "sample_index": 0,
        "treatment": treatment,
        "status": status,
        "generation_status": status,
        "failure_stage": failure_stage,
        "failure_reason": failure_reason,
        "prompt_sha256": metadata.get("prompt_sha256"),
        "raw_response": raw_response,
        "raw_response_sha256": _sha256_or_none(raw_response),
        "completion": completion,
        "extracted_candidate": extracted_candidate,
        "extracted_candidate_sha256": _sha256_or_none(extracted_candidate),
        "completion_sha256": _sha256_or_none(completion),
        "extraction_status": extraction_status,
        "extraction_method": extraction_method,
        "parse_status": parse_status,
        "entry_point_definition_count": entry_point_definition_count,
        "entry_point_definition_category": entry_point_definition_category,
        "duplicate_prompt_skeleton_suspected": duplicate_prompt_skeleton_suspected,
        "reasoning_leakage_detected": reasoning_leakage_detected,
        "generation_latency": elapsed_seconds,
        "total_fenced_blocks": total_fenced_blocks,
        "python_fenced_blocks": python_fenced_blocks,
        "had_markdown_fence": had_markdown_fence,
        "had_surrounding_text": had_surrounding_text,
        "elapsed_seconds": elapsed_seconds,
        "ollama_response_metadata": ollama_response_metadata,
        "metadata": metadata,
    }


def run_attempt(
    task: PublicBenchmarkTask,
    treatment: str,
    *,
    benchmark: str,
    base_url: str,
    timeout_seconds: float,
    settings: OllamaGenerationSettings,
    model_digest: str,
) -> Dict[str, Any]:
    """Run exactly one (task, treatment, sample_index=0) attempt."""
    prompt = build_prompt(task.prompt, treatment)
    metadata = {
        "benchmark": benchmark,
        "treatment": treatment,
        "model": settings.model,
        "model_tag": settings.model,
        "model_digest": model_digest,
        "seed": settings.seed,
        "temperature": settings.temperature,
        "top_p": settings.top_p,
        "top_k": settings.top_k,
        "num_predict": settings.num_predict,
        "api_endpoint": settings.api_endpoint,
        "response_field": settings.response_field,
        "prompt_sha256": sha256_text(prompt),
    }
    start = time.monotonic()

    def _preflight_fields(candidate: Optional[str]) -> Dict[str, Any]:
        pre = entry_point_preflight(
            candidate,
            entry_point=task.entry_point or "",
            prompt=task.prompt,
        )
        return {
            "parse_status": pre["parse_status"],
            "entry_point_definition_count": pre["entry_point_definition_count"],
            "entry_point_definition_category": pre["entry_point_definition_category"],
            "duplicate_prompt_skeleton_suspected": pre["duplicate_prompt_skeleton_suspected"],
        }

    try:
        raw_json = _post_chat(prompt, base_url, timeout_seconds, settings)
    except OllamaGenerationError as exc:
        return _build_attempt(
            task_id=task.task_id, treatment=treatment, entry_point=task.entry_point,
            status="failed", failure_stage="ollama_request", failure_reason=str(exc),
            raw_response=None, completion=None,
            extraction_status=None, extraction_method=None,
            total_fenced_blocks=None, python_fenced_blocks=None,
            had_markdown_fence=None, had_surrounding_text=None,
            elapsed_seconds=time.monotonic() - start, metadata=metadata,
            reasoning_leakage_detected=None,
            **_preflight_fields(None),
        )

    ollama_meta = raw_json.pop("_ollama_response_metadata", None)
    message = raw_json.get("message") if isinstance(raw_json.get("message"), dict) else {}
    raw_response_seen = message.get("content") if isinstance(message.get("content"), str) else None
    leakage_detected = False
    if raw_response_seen is not None:
        leakage_detected = detect_reasoning_leakage(raw_json, raw_response_seen)

    try:
        validated_response, leakage_detected = validate_chat_response(raw_json)
    except OllamaGenerationError as exc:
        return _build_attempt(
            task_id=task.task_id, treatment=treatment, entry_point=task.entry_point,
            status="failed", failure_stage="response_validation", failure_reason=str(exc),
            raw_response=raw_response_seen, completion=None,
            extraction_status=None, extraction_method=None,
            total_fenced_blocks=None, python_fenced_blocks=None,
            had_markdown_fence=None, had_surrounding_text=None,
            elapsed_seconds=time.monotonic() - start, metadata=metadata,
            reasoning_leakage_detected=leakage_detected or None,
            ollama_response_metadata=ollama_meta,
            **_preflight_fields(None),
        )

    analysis = analyze_extraction(validated_response)
    preflight = _preflight_fields(analysis["completion"] if analysis["ok"] else None)
    if not analysis["ok"]:
        return _build_attempt(
            task_id=task.task_id, treatment=treatment, entry_point=task.entry_point,
            status="failed", failure_stage="extraction",
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
            reasoning_leakage_detected=leakage_detected,
            ollama_response_metadata=ollama_meta,
            **preflight,
        )

    return _build_attempt(
        task_id=task.task_id, treatment=treatment, entry_point=task.entry_point,
        status="success", failure_stage=None, failure_reason=None,
        raw_response=validated_response, completion=analysis["completion"],
        extraction_status=analysis["extraction_status"],
        extraction_method=analysis["extraction_method"],
        total_fenced_blocks=analysis["total_fenced_blocks"],
        python_fenced_blocks=analysis["python_fenced_blocks"],
        had_markdown_fence=analysis["had_markdown_fence"],
        had_surrounding_text=analysis["had_surrounding_text"],
        elapsed_seconds=time.monotonic() - start, metadata=metadata,
        reasoning_leakage_detected=leakage_detected,
        ollama_response_metadata=ollama_meta,
        **preflight,
    )


def run_generation_attempts(
    tasks: Sequence[PublicBenchmarkTask],
    *,
    benchmark: str,
    base_url: str,
    timeout_seconds: float,
    settings: OllamaGenerationSettings,
    model_digest: str,
    completed_attempts: Optional[Dict[Tuple[str, str, str, str], Dict[str, Any]]] = None,
    rerun_incomplete: bool = False,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Run every (task, treatment) attempt in fixed order, optionally
    skipping attempts already present in *completed_attempts*."""
    completed_attempts = completed_attempts or {}
    attempts: List[Dict[str, Any]] = []
    resume_stats = {"skipped_complete": 0, "rerun_incomplete": rerun_incomplete}

    for task in tasks:
        for treatment in ALLOWED_TREATMENTS:
            prompt = build_prompt(task.prompt, treatment)
            resume_key = (
                task.task_id,
                treatment,
                model_digest,
                sha256_text(prompt),
            )
            if (
                not rerun_incomplete
                and resume_key in completed_attempts
                and is_resume_complete(completed_attempts[resume_key])
            ):
                attempts.append(completed_attempts[resume_key])
                resume_stats["skipped_complete"] += 1
                continue

            attempts.append(
                run_attempt(
                    task, treatment,
                    benchmark=benchmark,
                    base_url=base_url,
                    timeout_seconds=timeout_seconds,
                    settings=settings,
                    model_digest=model_digest,
                )
            )
    return attempts, resume_stats


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
    model: Optional[str] = None,
    settings: Optional[OllamaGenerationSettings] = None,
    max_tasks: Optional[int] = None,
    resume: bool = False,
    rerun_incomplete: bool = False,
    smoke: bool = False,
    manifest_benchmark: Optional[str] = None,
    started_at: Optional[str] = None,
) -> Dict[str, Any]:
    """Run every (task, treatment) attempt for *tasks_path* against Ollama
    /api/chat. Writes generation_attempts.jsonl, generation_summary.json,
    generation_manifest.json, ab1_raw.jsonl, ab2g_raw.jsonl, ab1.jsonl, and
    ab2g.jsonl to *output_dir*."""
    if benchmark not in ("humaneval", "mbpp"):
        raise OllamaGenerationError(
            "benchmark", f"benchmark must be 'humaneval' or 'mbpp', got {benchmark!r}"
        )

    output_dir = pathlib.Path(output_dir)
    started_at = started_at or _utc_now_iso()

    if settings is None:
        effective_model = model or (DEFAULT_SMOKE_MODEL if smoke else DEFAULT_MODEL_8B)
        settings = OllamaGenerationSettings.for_model(effective_model)
    elif model is not None and model != settings.model:
        raise OllamaGenerationError(
            "benchmark",
            f"conflicting model={model!r} and settings.model={settings.model!r}",
        )

    all_tasks = load_benchmark_tasks(tasks_path, benchmark)
    if not all_tasks:
        raise OllamaGenerationError("tasks_load", f"{tasks_path}: no tasks loaded")

    if max_tasks is not None:
        tasks = select_tasks_official_first_n(all_tasks, max_tasks)
        task_selection_policy = TASK_SELECTION_POLICY_FIRST_N
    else:
        tasks = list(all_tasks)
        task_selection_policy = "full_input"

    provenance = fetch_ollama_provenance(
        base_url,
        timeout_seconds,
        model=settings.model,
        expected_digest_prefix=settings.expected_digest_prefix,
    )
    model_digest = provenance["model_digest"]

    if runner_git_commit is None:
        runner_git_commit = _resolve_runner_git_commit()

    attempts_path = output_dir / "generation_attempts.jsonl"
    completed_attempts = load_completed_attempts(attempts_path) if resume else {}

    attempts, resume_stats = run_generation_attempts(
        tasks,
        benchmark=benchmark,
        base_url=base_url,
        timeout_seconds=timeout_seconds,
        settings=settings,
        model_digest=model_digest,
        completed_attempts=completed_attempts,
        rerun_incomplete=rerun_incomplete,
    )

    _write_completions_jsonl(attempts, attempts_path)

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

    completed_at = _utc_now_iso()
    manifest_benchmark_name = manifest_benchmark or (
        "humaneval_plus" if smoke else benchmark
    )
    manifest: Dict[str, Any] = {
        **provenance,
        "runner_git_commit": runner_git_commit,
        "benchmark": manifest_benchmark_name,
        "benchmark_version": BENCHMARK_VERSION_HUMANEVAL_PLUS if smoke else benchmark,
        "model": settings.model,
        "seed": settings.seed,
        "temperature": settings.temperature,
        "top_p": settings.top_p,
        "top_k": settings.top_k,
        "num_predict": settings.num_predict,
        "prompt_template_version": PROMPT_TEMPLATE_VERSION,
        "timeout_seconds": timeout_seconds,
        "task_ids": [t.task_id for t in tasks],
        "task_count": len(tasks),
        "task_selection_policy": task_selection_policy,
        "treatments": list(ALLOWED_TREATMENTS),
        "started_at": started_at,
        "completed_at": completed_at,
        "resume_enabled": resume,
        "resume_skipped_complete_attempts": resume_stats["skipped_complete"],
        "rerun_incomplete": rerun_incomplete,
    }
    if smoke:
        manifest.update(
            {
                "run_type": RUN_TYPE_SMOKE,
                "analysis_status": ANALYSIS_STATUS_SMOKE_EXCLUDED,
                "official_evalplus_status": OFFICIAL_EVALPLUS_STATUS_SMOKE,
                "official_evalplus_blocker": OFFICIAL_EVALPLUS_BLOCKER,
            }
        )
    _write_json_deterministic(manifest, output_dir / "generation_manifest.json")
    return summary


def run_engineering_smoke_pipeline(
    *,
    tasks_path: Union[str, pathlib.Path],
    repo_root: Optional[Union[str, pathlib.Path]] = None,
    output_dir: Optional[Union[str, pathlib.Path]] = None,
    base_url: str = DEFAULT_BASE_URL,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    runner_git_commit: Optional[str] = None,
    evaluator_git_commit: Optional[str] = None,
    max_tasks: int = SMOKE_TASK_COUNT,
    resume: bool = True,
    rerun_incomplete: bool = False,
    run_ab3: bool = True,
) -> Dict[str, Any]:
    """Isolated 20-task engineering smoke: generation + optional Ab3 derivation.

    Does not write to confirmatory result directories. Does not run official
    EvalPlus scoring."""
    started_at = _utc_now_iso()
    out_dir = pathlib.Path(output_dir) if output_dir is not None else default_smoke_output_dir(repo_root)
    settings = OllamaGenerationSettings.smoke_default()

    all_tasks = load_benchmark_tasks(tasks_path, "humaneval")
    selected_tasks = select_tasks_official_first_n(all_tasks, max_tasks)
    selected_tasks_path = out_dir / "tasks_selected.jsonl"
    _write_completions_jsonl(
        [
            {
                "task_id": t.task_id,
                "prompt": t.prompt,
                "entry_point": t.entry_point,
            }
            for t in selected_tasks
        ],
        selected_tasks_path,
    )

    gen_summary = run_ollama_generation(
        tasks_path=selected_tasks_path,
        benchmark="humaneval",
        output_dir=out_dir,
        base_url=base_url,
        timeout_seconds=timeout_seconds,
        runner_git_commit=runner_git_commit,
        settings=settings,
        max_tasks=max_tasks,
        resume=resume,
        rerun_incomplete=rerun_incomplete,
        smoke=True,
        manifest_benchmark="humaneval_plus",
        started_at=started_at,
    )

    result: Dict[str, Any] = {
        "output_dir": str(out_dir),
        "generation_summary": gen_summary,
        "ab3_ran": False,
    }

    if run_ab3:
        if evaluator_git_commit is None:
            evaluator_git_commit = runner_git_commit or _resolve_runner_git_commit()
        ab3_summary = run_public_benchmark_treatments_from_attempts(
            tasks_path=selected_tasks_path,
            generation_attempts_path=out_dir / "generation_attempts.jsonl",
            benchmark="humaneval",
            artifact_root=out_dir,
            evaluator_git_commit=evaluator_git_commit,
        )
        result["ab3_ran"] = True
        result["ab3_summary"] = {
            "total_tasks": ab3_summary.total_tasks,
            "ab3_target_count": ab3_summary.ab3_target_count,
            "core_changed_count": ab3_summary.core_changed_count,
            "spec_changed_count": ab3_summary.spec_changed_count,
        }

    manifest_path = out_dir / "generation_manifest.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["ab3_from_attempts"] = result["ab3_ran"]
        manifest["completed_at"] = _utc_now_iso()
        _write_json_deterministic(manifest, manifest_path)

    return result


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


def run_treatment_stage_from_attempts(
    *,
    tasks_path: Union[str, pathlib.Path],
    generation_attempts_path: Union[str, pathlib.Path],
    benchmark: str,
    artifact_root: Union[str, pathlib.Path],
    evaluator_git_commit: str,
) -> Dict[str, Any]:
    """Offline Ab3 derivation from generation_attempts.jsonl — Ab1 failure
    never blocks Ab3."""
    summary = run_public_benchmark_treatments_from_attempts(
        tasks_path=tasks_path,
        generation_attempts_path=generation_attempts_path,
        benchmark=benchmark,
        artifact_root=artifact_root,
        evaluator_git_commit=evaluator_git_commit,
    )
    return {"ran": True, "summary": summary}


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
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--timeout-seconds", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument(
        "--model",
        default=None,
        help=f"Ollama model tag (default: {DEFAULT_MODEL_8B}, or smoke model with --smoke).",
    )
    parser.add_argument(
        "--max-tasks",
        type=int,
        default=None,
        help="Deterministic first-N task selection in official input order.",
    )
    parser.add_argument("--resume", action="store_true", help="Skip completed attempts in output dir.")
    parser.add_argument(
        "--rerun-incomplete",
        action="store_true",
        help="When resuming, also rerun failed/incomplete attempts.",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Engineering smoke mode (isolated output, 4B instruct defaults).",
    )
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
        if args.smoke and args.max_tasks is None:
            args.max_tasks = SMOKE_TASK_COUNT
        settings = None
        if args.model is not None:
            settings = OllamaGenerationSettings.for_model(args.model)
        elif args.smoke:
            settings = OllamaGenerationSettings.smoke_default()

        if args.output_dir is not None:
            output_dir = args.output_dir
        elif args.smoke:
            output_dir = str(default_smoke_output_dir())
        else:
            parser.error("--output-dir is required unless --smoke is set")

        run_ollama_generation(
            tasks_path=args.tasks_path,
            benchmark=args.benchmark,
            output_dir=output_dir,
            base_url=args.base_url,
            timeout_seconds=args.timeout_seconds,
            runner_git_commit=args.runner_git_commit,
            model=args.model,
            settings=settings,
            max_tasks=args.max_tasks,
            resume=args.resume,
            rerun_incomplete=args.rerun_incomplete,
            smoke=args.smoke,
        )
        return 0
    except OllamaGenerationError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
