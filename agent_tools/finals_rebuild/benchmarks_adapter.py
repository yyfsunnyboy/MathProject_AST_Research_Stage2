"""
Public benchmark adapter — HumanEval+/MBPP+ task and completion loading.

Scope
-----
This module is a minimal intermediary layer between locally-stored
HumanEval+/MBPP+ task JSON/JSONL files, existing Ab1/Ab2g completions, and
the official EvalPlus completion JSONL format. It does not:

- run EvalPlus
- call any model
- generate Ab3-Core/Ab3-Full (those are deterministic re-derivations of an
  existing Ab2g raw code, produced by core_adapter.py/spec_adapter.py; this
  module never regenerates them)
- call semantic_heal or any LLM repair
- convert HumanEval+/MBPP+ tests into this repo's own TestSuite
- rewrite EvalPlus's own test/evaluation logic
- judge test_pass

No model calls. No code execution. No file I/O beyond reading the given
task/completion files and writing the output completion JSONL.
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Union

ALLOWED_BENCHMARKS: frozenset[str] = frozenset({"humaneval", "mbpp"})

ALLOWED_TREATMENTS: frozenset[str] = frozenset(
    {"ab1", "ab2g", "ab3_core", "ab3_full"}
)

# treatment -> required source_treatment (None means "must be None")
_SOURCE_TREATMENT_BY_TREATMENT: Dict[str, Optional[str]] = {
    "ab1": None,
    "ab2g": None,
    "ab3_core": "ab2g",
    "ab3_full": "ab2g",
}


class BenchmarkAdapterError(ValueError):
    """Raised on any invariant violation in this module; fails closed."""


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PublicBenchmarkTask:
    """One HumanEval+/MBPP+ task, as loaded from a local task file.

    No test cases are stored here — HumanEval+/MBPP+ correctness is judged
    exclusively by the official EvalPlus tooling downstream, never by a
    self-made TestSuite.
    """

    benchmark: str
    task_id: str
    prompt: str
    entry_point: Optional[str]
    canonical_solution: Optional[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.benchmark not in ALLOWED_BENCHMARKS:
            raise BenchmarkAdapterError(
                f"benchmark must be one of {sorted(ALLOWED_BENCHMARKS)}, "
                f"got {self.benchmark!r}"
            )
        if not isinstance(self.task_id, str) or not self.task_id.strip():
            raise BenchmarkAdapterError("task_id must be a non-empty string")
        if not isinstance(self.prompt, str) or not self.prompt.strip():
            raise BenchmarkAdapterError("prompt must be a non-empty string")
        if self.benchmark == "humaneval":
            if not isinstance(self.entry_point, str) or not self.entry_point.strip():
                raise BenchmarkAdapterError(
                    f"humaneval task {self.task_id!r} requires a non-empty entry_point"
                )
        if self.entry_point is not None and not isinstance(self.entry_point, str):
            raise BenchmarkAdapterError("entry_point must be None or a string")
        if self.canonical_solution is not None and not isinstance(
            self.canonical_solution, str
        ):
            raise BenchmarkAdapterError(
                "canonical_solution must be None or a string"
            )


@dataclass(frozen=True)
class BenchmarkCompletion:
    """One sampled completion for one (benchmark, task_id, sample_index)."""

    benchmark: str
    task_id: str
    sample_index: int
    treatment: str
    completion: str
    source_treatment: Optional[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.benchmark not in ALLOWED_BENCHMARKS:
            raise BenchmarkAdapterError(
                f"benchmark must be one of {sorted(ALLOWED_BENCHMARKS)}, "
                f"got {self.benchmark!r}"
            )
        if not isinstance(self.task_id, str) or not self.task_id.strip():
            raise BenchmarkAdapterError("task_id must be a non-empty string")
        if isinstance(self.sample_index, bool) or not isinstance(
            self.sample_index, int
        ) or self.sample_index < 0:
            raise BenchmarkAdapterError(
                f"sample_index must be a non-negative integer, "
                f"got {self.sample_index!r}"
            )
        if self.treatment not in ALLOWED_TREATMENTS:
            raise BenchmarkAdapterError(
                f"treatment must be one of {sorted(ALLOWED_TREATMENTS)}, "
                f"got {self.treatment!r}"
            )
        expected_source = _SOURCE_TREATMENT_BY_TREATMENT[self.treatment]
        if self.source_treatment != expected_source:
            raise BenchmarkAdapterError(
                f"treatment {self.treatment!r} requires source_treatment="
                f"{expected_source!r}, got {self.source_treatment!r}"
            )
        if not isinstance(self.completion, str) or not self.completion.strip():
            raise BenchmarkAdapterError(
                f"completion for task_id={self.task_id!r} "
                f"sample_index={self.sample_index!r} must be a non-empty string"
            )


# ---------------------------------------------------------------------------
# File loading helpers
# ---------------------------------------------------------------------------


def _load_records(path: Union[str, pathlib.Path]) -> List[Dict[str, Any]]:
    """Load a list of JSON objects from a .json (list) or .jsonl file."""
    p = pathlib.Path(path)
    suffix = p.suffix.lower()
    text = p.read_text(encoding="utf-8")

    if suffix == ".jsonl":
        records: List[Dict[str, Any]] = []
        for line_no, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                obj = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise BenchmarkAdapterError(
                    f"{p}: line {line_no}: invalid JSON: {exc}"
                ) from exc
            if not isinstance(obj, dict):
                raise BenchmarkAdapterError(
                    f"{p}: line {line_no}: expected a JSON object, got {type(obj).__name__}"
                )
            records.append(obj)
        return records

    if suffix == ".json":
        try:
            obj = json.loads(text)
        except json.JSONDecodeError as exc:
            raise BenchmarkAdapterError(f"{p}: invalid JSON: {exc}") from exc
        if isinstance(obj, list):
            for i, item in enumerate(obj):
                if not isinstance(item, dict):
                    raise BenchmarkAdapterError(
                        f"{p}: item {i} expected a JSON object, got {type(item).__name__}"
                    )
            return obj
        if isinstance(obj, dict):
            return [obj]
        raise BenchmarkAdapterError(
            f"{p}: expected a JSON object or list of objects, got {type(obj).__name__}"
        )

    raise BenchmarkAdapterError(
        f"{p}: unsupported file extension {p.suffix!r}; expected .json or .jsonl"
    )


# ---------------------------------------------------------------------------
# Task loading
# ---------------------------------------------------------------------------


def load_benchmark_tasks(
    path: Union[str, pathlib.Path],
    benchmark: str,
) -> List[PublicBenchmarkTask]:
    """Load HumanEval+/MBPP+ tasks from a local .json/.jsonl file.

    Preserves original record order. Fails closed on: unsupported
    *benchmark*, duplicate task_id, or missing required fields. Never
    downloads a dataset and never silently falls back to a different
    benchmark than requested.
    """
    if benchmark not in ALLOWED_BENCHMARKS:
        raise BenchmarkAdapterError(
            f"benchmark must be one of {sorted(ALLOWED_BENCHMARKS)}, "
            f"got {benchmark!r}"
        )

    records = _load_records(path)
    tasks: List[PublicBenchmarkTask] = []
    seen_task_ids: set[str] = set()

    for i, rec in enumerate(records):
        task_id = rec.get("task_id")
        if not isinstance(task_id, str) or not task_id.strip():
            raise BenchmarkAdapterError(
                f"{path}: record {i}: missing or invalid required field 'task_id'"
            )
        if task_id in seen_task_ids:
            raise BenchmarkAdapterError(
                f"{path}: duplicate task_id {task_id!r}"
            )
        seen_task_ids.add(task_id)

        if benchmark == "humaneval":
            prompt = rec.get("prompt")
            if not isinstance(prompt, str) or not prompt.strip():
                raise BenchmarkAdapterError(
                    f"{path}: task_id={task_id!r}: missing or invalid required field 'prompt'"
                )
            entry_point = rec.get("entry_point")
            if not isinstance(entry_point, str) or not entry_point.strip():
                raise BenchmarkAdapterError(
                    f"{path}: task_id={task_id!r}: humaneval requires a non-empty 'entry_point'"
                )
            canonical_solution = rec.get("canonical_solution")
        else:  # mbpp
            prompt = rec.get("prompt", rec.get("text"))
            if not isinstance(prompt, str) or not prompt.strip():
                raise BenchmarkAdapterError(
                    f"{path}: task_id={task_id!r}: missing or invalid 'prompt'/'text' field"
                )
            entry_point = rec.get("entry_point")
            canonical_solution = rec.get("canonical_solution", rec.get("code"))

        metadata = {
            k: v
            for k, v in rec.items()
            if k not in ("task_id", "prompt", "text", "entry_point",
                         "canonical_solution", "code")
        }

        tasks.append(
            PublicBenchmarkTask(
                benchmark=benchmark,
                task_id=task_id,
                prompt=prompt,
                entry_point=entry_point,
                canonical_solution=canonical_solution,
                metadata=metadata,
            )
        )

    return tasks


# ---------------------------------------------------------------------------
# Completion loading
# ---------------------------------------------------------------------------


def load_benchmark_completions(
    path: Union[str, pathlib.Path],
    benchmark: str,
    treatment: str,
) -> List[BenchmarkCompletion]:
    """Load existing Ab1/Ab2g/Ab3-Core/Ab3-Full completions from a local
    .json/.jsonl file.

    sample_index defaults to 0 only when a given task_id has exactly one
    record in the file; if a task_id repeats without explicit sample_index
    values, this fails closed rather than guessing. Fails closed on
    duplicate (task_id, sample_index) or empty completion text. Never
    prepends the prompt or re-adds a function signature to the completion.
    """
    if benchmark not in ALLOWED_BENCHMARKS:
        raise BenchmarkAdapterError(
            f"benchmark must be one of {sorted(ALLOWED_BENCHMARKS)}, "
            f"got {benchmark!r}"
        )
    if treatment not in ALLOWED_TREATMENTS:
        raise BenchmarkAdapterError(
            f"treatment must be one of {sorted(ALLOWED_TREATMENTS)}, "
            f"got {treatment!r}"
        )
    source_treatment = _SOURCE_TREATMENT_BY_TREATMENT[treatment]

    records = _load_records(path)

    # First pass: count records per task_id to know whether a missing
    # sample_index may default to 0.
    task_id_counts: Dict[str, int] = {}
    for rec in records:
        tid = rec.get("task_id")
        if isinstance(tid, str):
            task_id_counts[tid] = task_id_counts.get(tid, 0) + 1

    completions: List[BenchmarkCompletion] = []
    seen_keys: set[tuple[str, int]] = set()

    for i, rec in enumerate(records):
        task_id = rec.get("task_id")
        if not isinstance(task_id, str) or not task_id.strip():
            raise BenchmarkAdapterError(
                f"{path}: record {i}: missing or invalid required field 'task_id'"
            )

        completion = rec.get("completion")
        if not isinstance(completion, str) or not completion.strip():
            raise BenchmarkAdapterError(
                f"{path}: task_id={task_id!r}: 'completion' must be a non-empty string"
            )

        raw_sample_index = rec.get("sample_index")
        if raw_sample_index is None:
            if task_id_counts[task_id] != 1:
                raise BenchmarkAdapterError(
                    f"{path}: task_id={task_id!r}: 'sample_index' is required "
                    f"when a task_id has more than one record"
                )
            sample_index = 0
        else:
            if isinstance(raw_sample_index, bool) or not isinstance(
                raw_sample_index, int
            ) or raw_sample_index < 0:
                raise BenchmarkAdapterError(
                    f"{path}: task_id={task_id!r}: 'sample_index' must be a "
                    f"non-negative integer, got {raw_sample_index!r}"
                )
            sample_index = raw_sample_index

        key = (task_id, sample_index)
        if key in seen_keys:
            raise BenchmarkAdapterError(
                f"{path}: duplicate (task_id, sample_index) pair {key!r}"
            )
        seen_keys.add(key)

        metadata = {
            k: v
            for k, v in rec.items()
            if k not in ("task_id", "completion", "sample_index")
        }

        completions.append(
            BenchmarkCompletion(
                benchmark=benchmark,
                task_id=task_id,
                sample_index=sample_index,
                treatment=treatment,
                completion=completion,
                source_treatment=source_treatment,
                metadata=metadata,
            )
        )

    return completions


# ---------------------------------------------------------------------------
# Outer code fence stripping
# ---------------------------------------------------------------------------


def strip_outer_code_fence(completion: str) -> str:
    """Remove a single outermost ```python/``` (or bare ```) fence, if
    present, preserving all inner content byte-for-byte.

    Does not attempt any syntax or AST repair, and does not rewrite program
    logic. If the text is not wrapped in a single outer fence, it is
    returned unchanged.
    """
    text = completion
    stripped = text.strip("\n")
    lines = stripped.splitlines()
    if len(lines) < 2:
        return completion

    first_line = lines[0].strip()
    last_line = lines[-1].strip()

    if not first_line.startswith("```"):
        return completion
    if last_line != "```":
        return completion

    inner_lines = lines[1:-1]
    return "\n".join(inner_lines)


# ---------------------------------------------------------------------------
# Identity validation
# ---------------------------------------------------------------------------


def validate_completion_identity(
    tasks: Sequence[PublicBenchmarkTask],
    completions: Sequence[BenchmarkCompletion],
) -> None:
    """Assert every completion's task_id exists among *tasks*.

    Fails closed on any completion referencing an unknown task_id. Does not
    require every task to have a completion (use find_missing_task_ids for
    that) — it only ever rejects unknown/orphaned completions, never
    silently drops them.
    """
    known_task_ids = {t.task_id for t in tasks}
    for c in completions:
        if c.task_id not in known_task_ids:
            raise BenchmarkAdapterError(
                f"completion references unknown task_id {c.task_id!r} "
                f"(sample_index={c.sample_index!r})"
            )


def find_missing_task_ids(
    tasks: Sequence[PublicBenchmarkTask],
    completions: Sequence[BenchmarkCompletion],
) -> List[str]:
    """Return task_ids from *tasks* that have no corresponding completion,
    preserving the original task order."""
    completed_task_ids = {c.task_id for c in completions}
    return [t.task_id for t in tasks if t.task_id not in completed_task_ids]


# ---------------------------------------------------------------------------
# EvalPlus completion JSONL output
# ---------------------------------------------------------------------------


def write_evalplus_completion_jsonl(
    completions: Sequence[BenchmarkCompletion],
    output_path: Union[str, pathlib.Path],
) -> None:
    """Write *completions* as an EvalPlus-compatible completion JSONL file.

    Each line is exactly ``{"task_id": ..., "completion": ...}`` — no
    test_pass/score/syntax_pass/execution_success or any other fabricated
    EvalPlus result field. All completions in *completions* must share one
    benchmark and one treatment (fails closed otherwise). Fails closed on
    duplicate (task_id, sample_index) or empty completion. Input order is
    preserved; repeated task_ids (sample_index > 0) are allowed and emitted
    as separate lines without ID rewriting.
    """
    if not completions:
        raise BenchmarkAdapterError("completions must not be empty")

    benchmarks = {c.benchmark for c in completions}
    if len(benchmarks) != 1:
        raise BenchmarkAdapterError(
            f"all completions must share one benchmark, got {sorted(benchmarks)}"
        )

    treatments = {c.treatment for c in completions}
    if len(treatments) != 1:
        raise BenchmarkAdapterError(
            f"all completions must share one treatment, got {sorted(treatments)}"
        )

    seen_keys: set[tuple[str, int]] = set()
    for c in completions:
        key = (c.task_id, c.sample_index)
        if key in seen_keys:
            raise BenchmarkAdapterError(
                f"duplicate (task_id, sample_index) pair {key!r}"
            )
        seen_keys.add(key)
        if not c.completion.strip():
            raise BenchmarkAdapterError(
                f"completion for task_id={c.task_id!r} "
                f"sample_index={c.sample_index!r} must be a non-empty string"
            )

    out_path = pathlib.Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        for c in completions:
            line = json.dumps(
                {"task_id": c.task_id, "completion": c.completion},
                ensure_ascii=False,
            )
            fh.write(line + "\n")
