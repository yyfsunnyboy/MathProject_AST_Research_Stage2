"""
Public benchmark treatment runner — wires existing Ab1/Ab2g completions
into the deterministic Core/Spec adapters.

Scope
-----
For each (task_id, sample_index) pair already covered by an existing Ab1
(Bare) and Ab2g (Generic Safety-and-Format Scaffold) completion, this
module produces:

    Ab1       = the existing Bare completion (untouched, never adapted)
    Ab2g      = the existing Scaffold completion (untouched, never adapted)
    Ab3-Core  = run_core_adapter() applied ONCE to that same Ab2g completion
    Ab3-Full  = run_spec_adapter() applied ONCE to Ab3-Core's own output
                (never to the raw Ab2g completion directly)

No model calls. No network calls. No semantic healer. No EvalPlus
execution. No official test running. No pass@1/McNemar/MCRI computation.
HumanEval+/MBPP+ tests are never converted into this repo's own
TestSuite — see benchmarks_adapter.py's own module docstring for why.

test_status is always "not_run" and test_pass is always None: this module
only ever reports syntax/bounded-execution operational outcome, never a
fabricated functional-correctness verdict.
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass, field, replace
from typing import Any, Dict, List, Sequence, Union

from agent_tools.finals_rebuild.artifacts import (
    RunMetadata,
    build_run_id,
    sha256_text,
    validate_run_metadata,
    validate_treatment_chain_identity,
)
from agent_tools.finals_rebuild.benchmarks_adapter import (
    BenchmarkCompletion,
    PublicBenchmarkTask,
    find_missing_task_ids,
    load_benchmark_completions,
    load_benchmark_tasks,
    validate_completion_identity,
    write_evalplus_completion_jsonl,
)
from agent_tools.finals_rebuild.core_adapter import run_core_adapter
from agent_tools.finals_rebuild.evaluation import (
    EvaluationResult,
    evaluation_result_to_dict,
    validate_evaluation_result,
)
from agent_tools.finals_rebuild.execution_evaluator import evaluate_with_execution
from agent_tools.finals_rebuild.extraction import extract_code
from agent_tools.finals_rebuild.spec_adapter import run_spec_adapter
from agent_tools.finals_rebuild.static_evaluator import evaluate_static
from agent_tools.finals_rebuild.trace import (
    TreatmentTrace,
    treatment_trace_to_dict,
    validate_treatment_trace,
)
from typing import Optional, Tuple

# Fixed, non-current placeholder timestamp — required only to satisfy the
# UTC ISO-8601 format validators on TreatmentTrace/EvaluationResult/
# RunMetadata. Never derived from datetime.now(); never varies between
# runs, which is what keeps output byte-reproducible for identical input.
_FIXED_CREATED_AT_UTC = "2000-01-01T00:00:00+00:00"
_FIXED_SOURCE_GIT_COMMIT = "public_benchmark_runner"

# artifacts.ALLOWED_TREATMENTS uses "ab2" (not "ab2g") as its label; these
# are the treatment labels handed to the static/execution evaluator and to
# RunMetadata/TreatmentTrace, which only recognise artifacts.py's set.
_EVAL_TREATMENT_AB2G = "ab2"
_EVAL_TREATMENT_AB3_CORE = "ab3_core"
_EVAL_TREATMENT_AB3_FULL = "ab3_full"
_EVAL_TREATMENT_AB1 = "ab1"


class PublicBenchmarkRunnerError(ValueError):
    """Raised on any invariant violation in this module; fails closed."""


# ---------------------------------------------------------------------------
# Pair identity
# ---------------------------------------------------------------------------


def build_public_benchmark_pair_id(
    benchmark: str, task_id: str, sample_index: int
) -> str:
    """Deterministic pair_id for one public-benchmark (task_id,
    sample_index) pair. Independent of artifacts.build_pair_id (which
    requires bare/scaffold prompt hashes that do not exist here)."""
    payload = "\x00".join(
        ("public_benchmark", benchmark, task_id, str(sample_index))
    )
    return sha256_text(payload)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PublicBenchmarkTreatmentResult:
    """One (task_id, sample_index) pair's full four-treatment outcome."""

    benchmark: str
    task_id: str
    sample_index: int
    ab1_completion: str
    ab2g_completion: str
    ab3_core_completion: str
    ab3_full_completion: str
    ab1_hash: str
    ab2g_hash: str
    ab3_core_hash: str
    ab3_full_hash: str
    core_changed: bool
    spec_changed: bool
    core_fix_count: int
    spec_fix_count: int
    core_trace: Dict[str, Any]
    spec_trace: Dict[str, Any]
    ab1_static: Dict[str, Any]
    ab2g_static: Dict[str, Any]
    ab3_core_static: Dict[str, Any]
    ab3_full_static: Dict[str, Any]
    ab1_execution: Dict[str, Any]
    ab2g_execution: Dict[str, Any]
    ab3_core_execution: Dict[str, Any]
    ab3_full_execution: Dict[str, Any]
    test_status: str = "not_run"


@dataclass(frozen=True)
class PublicBenchmarkRunSummary:
    """Aggregate counts across every processed pair. No pass@1, no
    McNemar, no MCRI — only structural change counts and syntax/execution
    operational rescue/regression counts."""

    benchmark: str
    total_pairs: int
    core_changed_count: int
    spec_changed_count: int
    core_unchanged_count: int
    spec_unchanged_count: int
    syntax_rescued_by_core: int
    syntax_regressed_by_core: int
    execution_rescued_by_core: int
    execution_regressed_by_core: int
    syntax_rescued_by_full: int
    syntax_regressed_by_full: int
    execution_rescued_by_full: int
    execution_regressed_by_full: int
    not_test_assessable_count: int


# ---------------------------------------------------------------------------
# Rescue/regression helpers (pure)
# ---------------------------------------------------------------------------


def _syntax_pass(evaluation: EvaluationResult) -> bool:
    return evaluation.syntax_pass is True


def _execution_pass(evaluation: EvaluationResult) -> bool:
    return evaluation.execution_success is True


def _rescued(baseline: bool, outcome: bool) -> bool:
    return (not baseline) and outcome


def _regressed(baseline: bool, outcome: bool) -> bool:
    return baseline and (not outcome)


# ---------------------------------------------------------------------------
# Single-pair processing
# ---------------------------------------------------------------------------


def _finalize_trace(trace: TreatmentTrace, pair_id: str, treatment: str, output_hash: str) -> TreatmentTrace:
    run_id = build_run_id(pair_id, treatment, output_hash)
    finalized = replace(trace, run_id=run_id, created_at_utc=_FIXED_CREATED_AT_UTC)
    try:
        validate_treatment_trace(finalized)
    except Exception as exc:
        raise PublicBenchmarkRunnerError(
            f"adapter trace failed validation for treatment={treatment!r}: {exc}"
        ) from exc
    return finalized


def _evaluate(
    *,
    code: str,
    pair_id: str,
    run_id: str,
    treatment: str,
    artifact_hash: str,
    evaluator_git_commit: str,
) -> tuple[EvaluationResult, EvaluationResult]:
    """Return (static_result, execution_result), both schema-validated and
    with a fixed, non-current created_at_utc."""
    static_raw = evaluate_static(
        code=code,
        pair_id=pair_id,
        run_id=run_id,
        treatment=treatment,
        artifact_hash=artifact_hash,
        evaluator_git_commit=evaluator_git_commit,
    )
    static_result = replace(static_raw, created_at_utc=_FIXED_CREATED_AT_UTC)

    execution_raw = evaluate_with_execution(
        code=code,
        pair_id=pair_id,
        run_id=run_id,
        treatment=treatment,
        artifact_hash=artifact_hash,
        evaluator_git_commit=evaluator_git_commit,
    )
    execution_result = replace(execution_raw, created_at_utc=_FIXED_CREATED_AT_UTC)

    for label, ev in (("static", static_result), ("execution", execution_result)):
        try:
            validate_evaluation_result(ev)
        except Exception as exc:
            raise PublicBenchmarkRunnerError(
                f"{label} evaluation failed schema validation "
                f"(treatment={treatment!r}): {exc}"
            ) from exc

    return static_result, execution_result


def _process_pair(
    *,
    benchmark: str,
    task_id: str,
    sample_index: int,
    ab1_completion: BenchmarkCompletion,
    ab2g_completion: BenchmarkCompletion,
    evaluator_git_commit: str,
) -> tuple[PublicBenchmarkTreatmentResult, BenchmarkCompletion, BenchmarkCompletion]:
    pair_id = build_public_benchmark_pair_id(benchmark, task_id, sample_index)

    ab1_code = ab1_completion.completion
    ab2g_code = ab2g_completion.completion
    ab1_hash = sha256_text(ab1_code)
    ab2g_hash = sha256_text(ab2g_code)

    # --- Core (Ab2g completion -> Core, once) -------------------------------
    core_result = run_core_adapter(pair_id=pair_id, input_code=ab2g_code)
    ab3_core_code = core_result.output_code
    ab3_core_hash = sha256_text(ab3_core_code)
    core_trace = _finalize_trace(
        core_result.trace, pair_id, _EVAL_TREATMENT_AB3_CORE, ab3_core_hash
    )

    # --- Spec (Core's own output -> Spec, once; never the raw Ab2g) --------
    spec_result = run_spec_adapter(
        pair_id=pair_id, skill_id=task_id, input_code=ab3_core_code
    )
    ab3_full_code = spec_result.output_code
    ab3_full_hash = sha256_text(ab3_full_code)
    spec_trace = _finalize_trace(
        spec_result.trace, pair_id, _EVAL_TREATMENT_AB3_FULL, ab3_full_hash
    )

    # --- Chain-identity check: reuses the same validator the paired
    # pipeline uses, rather than re-deriving the invariant by hand. ---------
    ab2g_run = RunMetadata(
        study_id="public_benchmark", pair_id=pair_id, treatment=_EVAL_TREATMENT_AB2G,
        run_id=build_run_id(pair_id, _EVAL_TREATMENT_AB2G, ab2g_hash),
        input_artifact_hash=ab2g_hash, output_artifact_hash=ab2g_hash,
        source_git_commit=_FIXED_SOURCE_GIT_COMMIT, created_at_utc=_FIXED_CREATED_AT_UTC,
    )
    ab3_core_run = RunMetadata(
        study_id="public_benchmark", pair_id=pair_id, treatment=_EVAL_TREATMENT_AB3_CORE,
        run_id=core_trace.run_id,
        input_artifact_hash=ab2g_hash, output_artifact_hash=ab3_core_hash,
        source_git_commit=_FIXED_SOURCE_GIT_COMMIT, created_at_utc=_FIXED_CREATED_AT_UTC,
    )
    ab3_full_run = RunMetadata(
        study_id="public_benchmark", pair_id=pair_id, treatment=_EVAL_TREATMENT_AB3_FULL,
        run_id=spec_trace.run_id,
        input_artifact_hash=ab3_core_hash, output_artifact_hash=ab3_full_hash,
        source_git_commit=_FIXED_SOURCE_GIT_COMMIT, created_at_utc=_FIXED_CREATED_AT_UTC,
    )
    for run_meta in (ab2g_run, ab3_core_run, ab3_full_run):
        validate_run_metadata(run_meta)
    try:
        validate_treatment_chain_identity(ab2g_run, ab3_core_run, ab3_full_run)
    except Exception as exc:
        raise PublicBenchmarkRunnerError(
            f"treatment chain identity failed for task_id={task_id!r} "
            f"sample_index={sample_index!r}: {exc}"
        ) from exc

    # Ab3-Core/Ab3-Full completions must structurally declare source_treatment
    # "ab2g" — BenchmarkCompletion.__post_init__ fails closed otherwise.
    ab3_core_completion = BenchmarkCompletion(
        benchmark=benchmark, task_id=task_id, sample_index=sample_index,
        treatment="ab3_core", completion=ab3_core_code, source_treatment="ab2g",
    )
    ab3_full_completion = BenchmarkCompletion(
        benchmark=benchmark, task_id=task_id, sample_index=sample_index,
        treatment="ab3_full", completion=ab3_full_code, source_treatment="ab2g",
    )

    # --- Evaluation: static + bounded execution for all four treatments ----
    ab1_run_id = build_run_id(pair_id, _EVAL_TREATMENT_AB1, ab1_hash)
    ab1_static, ab1_execution = _evaluate(
        code=ab1_code, pair_id=pair_id, run_id=ab1_run_id,
        treatment=_EVAL_TREATMENT_AB1, artifact_hash=ab1_hash,
        evaluator_git_commit=evaluator_git_commit,
    )
    ab2g_static, ab2g_execution = _evaluate(
        code=ab2g_code, pair_id=pair_id, run_id=ab2g_run.run_id,
        treatment=_EVAL_TREATMENT_AB2G, artifact_hash=ab2g_hash,
        evaluator_git_commit=evaluator_git_commit,
    )
    ab3_core_static, ab3_core_execution = _evaluate(
        code=ab3_core_code, pair_id=pair_id, run_id=ab3_core_run.run_id,
        treatment=_EVAL_TREATMENT_AB3_CORE, artifact_hash=ab3_core_hash,
        evaluator_git_commit=evaluator_git_commit,
    )
    ab3_full_static, ab3_full_execution = _evaluate(
        code=ab3_full_code, pair_id=pair_id, run_id=ab3_full_run.run_id,
        treatment=_EVAL_TREATMENT_AB3_FULL, artifact_hash=ab3_full_hash,
        evaluator_git_commit=evaluator_git_commit,
    )

    result = PublicBenchmarkTreatmentResult(
        benchmark=benchmark,
        task_id=task_id,
        sample_index=sample_index,
        ab1_completion=ab1_code,
        ab2g_completion=ab2g_code,
        ab3_core_completion=ab3_core_code,
        ab3_full_completion=ab3_full_code,
        ab1_hash=ab1_hash,
        ab2g_hash=ab2g_hash,
        ab3_core_hash=ab3_core_hash,
        ab3_full_hash=ab3_full_hash,
        core_changed=core_trace.changed,
        spec_changed=spec_trace.changed,
        core_fix_count=len(core_trace.rules_triggered),
        spec_fix_count=len(spec_trace.rules_triggered),
        core_trace=treatment_trace_to_dict(core_trace),
        spec_trace=treatment_trace_to_dict(spec_trace),
        ab1_static=evaluation_result_to_dict(ab1_static),
        ab2g_static=evaluation_result_to_dict(ab2g_static),
        ab3_core_static=evaluation_result_to_dict(ab3_core_static),
        ab3_full_static=evaluation_result_to_dict(ab3_full_static),
        ab1_execution=evaluation_result_to_dict(ab1_execution),
        ab2g_execution=evaluation_result_to_dict(ab2g_execution),
        ab3_core_execution=evaluation_result_to_dict(ab3_core_execution),
        ab3_full_execution=evaluation_result_to_dict(ab3_full_execution),
        test_status="not_run",
    )
    return result, ab3_core_completion, ab3_full_completion


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


def _build_summary(
    benchmark: str, results: Sequence[PublicBenchmarkTreatmentResult]
) -> PublicBenchmarkRunSummary:
    total = len(results)
    core_changed_count = sum(1 for r in results if r.core_changed)
    spec_changed_count = sum(1 for r in results if r.spec_changed)

    syntax_rescued_by_core = 0
    syntax_regressed_by_core = 0
    execution_rescued_by_core = 0
    execution_regressed_by_core = 0
    syntax_rescued_by_full = 0
    syntax_regressed_by_full = 0
    execution_rescued_by_full = 0
    execution_regressed_by_full = 0
    not_test_assessable_count = 0

    for r in results:
        ab2g_ev = EvaluationResult(**r.ab2g_execution)
        core_ev = EvaluationResult(**r.ab3_core_execution)
        full_ev = EvaluationResult(**r.ab3_full_execution)

        base_syntax = _syntax_pass(ab2g_ev)
        base_exec = _execution_pass(ab2g_ev)
        core_syntax = _syntax_pass(core_ev)
        core_exec = _execution_pass(core_ev)
        full_syntax = _syntax_pass(full_ev)
        full_exec = _execution_pass(full_ev)

        if _rescued(base_syntax, core_syntax):
            syntax_rescued_by_core += 1
        if _regressed(base_syntax, core_syntax):
            syntax_regressed_by_core += 1
        if _rescued(base_exec, core_exec):
            execution_rescued_by_core += 1
        if _regressed(base_exec, core_exec):
            execution_regressed_by_core += 1

        if _rescued(base_syntax, full_syntax):
            syntax_rescued_by_full += 1
        if _regressed(base_syntax, full_syntax):
            syntax_regressed_by_full += 1
        if _rescued(base_exec, full_exec):
            execution_rescued_by_full += 1
        if _regressed(base_exec, full_exec):
            execution_regressed_by_full += 1

        if r.test_status != "completed":
            not_test_assessable_count += 1

    return PublicBenchmarkRunSummary(
        benchmark=benchmark,
        total_pairs=total,
        core_changed_count=core_changed_count,
        spec_changed_count=spec_changed_count,
        core_unchanged_count=total - core_changed_count,
        spec_unchanged_count=total - spec_changed_count,
        syntax_rescued_by_core=syntax_rescued_by_core,
        syntax_regressed_by_core=syntax_regressed_by_core,
        execution_rescued_by_core=execution_rescued_by_core,
        execution_regressed_by_core=execution_regressed_by_core,
        syntax_rescued_by_full=syntax_rescued_by_full,
        syntax_regressed_by_full=syntax_regressed_by_full,
        execution_rescued_by_full=execution_rescued_by_full,
        execution_regressed_by_full=execution_regressed_by_full,
        not_test_assessable_count=not_test_assessable_count,
    )


def _summary_to_dict(summary: PublicBenchmarkRunSummary) -> Dict[str, Any]:
    return {
        "benchmark": summary.benchmark,
        "total_pairs": summary.total_pairs,
        "core_changed_count": summary.core_changed_count,
        "spec_changed_count": summary.spec_changed_count,
        "core_unchanged_count": summary.core_unchanged_count,
        "spec_unchanged_count": summary.spec_unchanged_count,
        "syntax_rescued_by_core": summary.syntax_rescued_by_core,
        "syntax_regressed_by_core": summary.syntax_regressed_by_core,
        "execution_rescued_by_core": summary.execution_rescued_by_core,
        "execution_regressed_by_core": summary.execution_regressed_by_core,
        "syntax_rescued_by_full": summary.syntax_rescued_by_full,
        "syntax_regressed_by_full": summary.syntax_regressed_by_full,
        "execution_rescued_by_full": summary.execution_rescued_by_full,
        "execution_regressed_by_full": summary.execution_regressed_by_full,
        "not_test_assessable_count": summary.not_test_assessable_count,
    }


def _result_to_dict(result: PublicBenchmarkTreatmentResult) -> Dict[str, Any]:
    return {
        "benchmark": result.benchmark,
        "task_id": result.task_id,
        "sample_index": result.sample_index,
        "ab1_completion": result.ab1_completion,
        "ab2g_completion": result.ab2g_completion,
        "ab3_core_completion": result.ab3_core_completion,
        "ab3_full_completion": result.ab3_full_completion,
        "ab1_hash": result.ab1_hash,
        "ab2g_hash": result.ab2g_hash,
        "ab3_core_hash": result.ab3_core_hash,
        "ab3_full_hash": result.ab3_full_hash,
        "core_changed": result.core_changed,
        "spec_changed": result.spec_changed,
        "core_fix_count": result.core_fix_count,
        "spec_fix_count": result.spec_fix_count,
        "core_trace": result.core_trace,
        "spec_trace": result.spec_trace,
        "ab1_static": result.ab1_static,
        "ab2g_static": result.ab2g_static,
        "ab3_core_static": result.ab3_core_static,
        "ab3_full_static": result.ab3_full_static,
        "ab1_execution": result.ab1_execution,
        "ab2g_execution": result.ab2g_execution,
        "ab3_core_execution": result.ab3_core_execution,
        "ab3_full_execution": result.ab3_full_execution,
        "test_status": result.test_status,
    }


# ---------------------------------------------------------------------------
# JSON writing
# ---------------------------------------------------------------------------


def _write_json_deterministic(obj: Any, path: pathlib.Path) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        serialised = (
            json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
        )
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(serialised)
    except OSError as exc:
        raise PublicBenchmarkRunnerError(
            f"failed to write output file {path}: {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


def run_public_benchmark_treatments(
    *,
    tasks_path: Union[str, pathlib.Path],
    ab1_completions_path: Union[str, pathlib.Path],
    ab2g_completions_path: Union[str, pathlib.Path],
    benchmark: str,
    artifact_root: Union[str, pathlib.Path],
    evaluator_git_commit: str,
) -> PublicBenchmarkRunSummary:
    """
    Run the full Ab1/Ab2g/Ab3-Core/Ab3-Full treatment comparison over
    every (task_id, sample_index) pair covered by *ab1_completions_path*
    and *ab2g_completions_path*.

    Ab3-Core/Ab3-Full are never regenerated by a model — they are always
    the deterministic output of run_core_adapter()/run_spec_adapter()
    applied to the existing Ab2g completion (Core once, then Spec once on
    Core's own output). Ab1 is never fed to either adapter. Ab2g's own
    completion text is never mutated (only read).

    Fails closed (raises PublicBenchmarkRunnerError, or a propagated
    BenchmarkAdapterError/TraceValidationError/EvaluationValidationError/
    ValueError from an underlying validator) on: Ab1/Ab2g identity-set
    mismatch, an unknown task_id, a task with no completion, a mismatched
    benchmark, duplicate (task_id, sample_index) identity, an invalid
    adapter trace, a failed chain-identity check, or an unwritable
    artifact_root. Never silently skips a pair or falls back to the
    intersection of the two completion sets.
    """
    tasks: List[PublicBenchmarkTask] = load_benchmark_tasks(tasks_path, benchmark)
    ab1_completions: List[BenchmarkCompletion] = load_benchmark_completions(
        ab1_completions_path, benchmark, "ab1"
    )
    ab2g_completions: List[BenchmarkCompletion] = load_benchmark_completions(
        ab2g_completions_path, benchmark, "ab2g"
    )

    validate_completion_identity(tasks, ab1_completions)
    validate_completion_identity(tasks, ab2g_completions)

    missing_for_ab1 = find_missing_task_ids(tasks, ab1_completions)
    if missing_for_ab1:
        raise PublicBenchmarkRunnerError(
            f"tasks missing an Ab1 completion: {missing_for_ab1}"
        )
    missing_for_ab2g = find_missing_task_ids(tasks, ab2g_completions)
    if missing_for_ab2g:
        raise PublicBenchmarkRunnerError(
            f"tasks missing an Ab2g completion: {missing_for_ab2g}"
        )

    ab1_keys = {(c.task_id, c.sample_index) for c in ab1_completions}
    ab2g_keys = {(c.task_id, c.sample_index) for c in ab2g_completions}
    if ab1_keys != ab2g_keys:
        only_ab1 = sorted(ab1_keys - ab2g_keys)
        only_ab2g = sorted(ab2g_keys - ab1_keys)
        raise PublicBenchmarkRunnerError(
            "Ab1/Ab2g identity sets do not match exactly: "
            f"only_in_ab1={only_ab1}, only_in_ab2g={only_ab2g}"
        )

    ab1_by_key: Dict[tuple[str, int], BenchmarkCompletion] = {
        (c.task_id, c.sample_index): c for c in ab1_completions
    }

    results: List[PublicBenchmarkTreatmentResult] = []
    ab3_core_completions: List[BenchmarkCompletion] = []
    ab3_full_completions: List[BenchmarkCompletion] = []
    seen_identity: set[tuple[str, int]] = set()

    for ab2g_completion in ab2g_completions:
        key = (ab2g_completion.task_id, ab2g_completion.sample_index)
        if key in seen_identity:
            raise PublicBenchmarkRunnerError(f"duplicate identity: {key!r}")
        seen_identity.add(key)

        ab1_completion = ab1_by_key[key]
        if ab1_completion.benchmark != benchmark or ab2g_completion.benchmark != benchmark:
            raise PublicBenchmarkRunnerError(
                f"benchmark mismatch for {key!r}: "
                f"ab1={ab1_completion.benchmark!r}, ab2g={ab2g_completion.benchmark!r}, "
                f"expected={benchmark!r}"
            )

        result, ab3_core_completion, ab3_full_completion = _process_pair(
            benchmark=benchmark,
            task_id=ab2g_completion.task_id,
            sample_index=ab2g_completion.sample_index,
            ab1_completion=ab1_completion,
            ab2g_completion=ab2g_completion,
            evaluator_git_commit=evaluator_git_commit,
        )
        results.append(result)
        ab3_core_completions.append(ab3_core_completion)
        ab3_full_completions.append(ab3_full_completion)

    summary = _build_summary(benchmark, results)

    out_root = pathlib.Path(artifact_root) / "public_benchmark" / benchmark
    _write_json_deterministic(
        [_result_to_dict(r) for r in results], out_root / "results.json"
    )
    _write_json_deterministic(_summary_to_dict(summary), out_root / "summary.json")

    evalplus_dir = out_root / "evalplus"
    write_evalplus_completion_jsonl(ab1_completions, evalplus_dir / "ab1.jsonl")
    write_evalplus_completion_jsonl(ab2g_completions, evalplus_dir / "ab2g.jsonl")
    write_evalplus_completion_jsonl(ab3_core_completions, evalplus_dir / "ab3_core.jsonl")
    write_evalplus_completion_jsonl(ab3_full_completions, evalplus_dir / "ab3_full.jsonl")

    return summary


# =============================================================================
# Raw-response-driven Ab3 pipeline
# =============================================================================
#
# The entrypoint above (run_public_benchmark_treatments) requires a
# successfully-*extracted* Ab1 AND Ab2g completion for every task, because
# it consumes ab1.jsonl/ab2g.jsonl (extraction-success-only files written by
# ollama_generation_runner.py). That makes Ab3 availability accidentally
# depend on Ab1 extraction succeeding, and on Ab2g extraction succeeding —
# neither of which the research design intends.
#
# The functions below instead read
# agent_tools.finals_rebuild.ollama_generation_runner's
# generation_attempts.jsonl schema directly (task_id, sample_index,
# treatment, status, raw_response, raw_response_sha256, extraction_status,
# completion, ...) and gate Ab3 on exactly one condition: does the Ab2g
# attempt have a non-empty raw_response? Ab1's outcome never affects
# whether Ab3 runs, and Ab1 is never fed to Core/Spec. Core/Spec always
# receive Ab2g's *raw* model response (not the extracted completion) — the
# scaffold's own instructions are what ask the model for clean code;
# whether that request was honored is exactly what Core/Spec + a
# post-hoc extract_code() call are being used to observe. extraction.py is
# never modified and never re-implemented here: `extract_code()` is called
# as-is after Core and again after Spec, and the ambiguity/emptiness rule
# it applies is authoritative — this module never selects a "first" or
# "last" block among multiple candidates.
#
# This module does not import agent_tools.finals_rebuild.
# ollama_generation_runner (that module already imports
# run_public_benchmark_treatments from here — importing back would create
# a cycle); it only depends on the plain JSON schema that module writes.


class _Ab3RawPipelineError(PublicBenchmarkRunnerError):
    """Raised on any invariant violation specific to the raw-response Ab3
    pipeline; fails closed like PublicBenchmarkRunnerError."""


@dataclass(frozen=True)
class RawAb3TaskResult:
    """One task's Ab1 (informational only) + Ab2g-raw-driven Ab3 outcome.

    Ab1 fields are populated only if an Ab1 attempt exists for this task;
    a missing Ab1 attempt never blocks the rest of this record (all Ab1
    fields become None). All Ab3 fields are None whenever
    has_ab3_target is False. test_status/test_pass are always fixed —
    this module never runs the official benchmark tests."""

    benchmark: str
    task_id: str
    sample_index: int

    ab1_status: Optional[str]
    ab1_completion: Optional[str]
    ab1_extraction_status: Optional[str]

    ab2g_generation_status: str
    ab2g_raw_response_hash: Optional[str]
    ab2g_extraction_status: Optional[str]
    ab2g_completion: Optional[str]

    ab3_core_raw_output: Optional[str]
    ab3_core_raw_hash: Optional[str]
    ab3_core_extraction_status: Optional[str]
    ab3_core_completion: Optional[str]
    ab3_core_static: Optional[Dict[str, Any]]
    ab3_core_execution: Optional[Dict[str, Any]]
    core_trace: Optional[Dict[str, Any]]

    ab3_full_raw_output: Optional[str]
    ab3_full_raw_hash: Optional[str]
    ab3_full_extraction_status: Optional[str]
    ab3_full_completion: Optional[str]
    ab3_full_static: Optional[Dict[str, Any]]
    ab3_full_execution: Optional[Dict[str, Any]]
    spec_trace: Optional[Dict[str, Any]]

    has_ab3_target: bool
    test_status: str = "not_run"
    test_pass: Optional[bool] = None


@dataclass(frozen=True)
class RawAb3RunSummary:
    """Aggregate counts across every processed task. No pass@1 — only
    availability/extraction/structural-change/operational-rescue counts."""

    benchmark: str
    total_tasks: int
    ab1_available_count: int
    ab1_missing_count: int
    ab2g_raw_available_count: int
    ab2g_raw_missing_count: int
    ab2g_extraction_success_count: int
    ab2g_extraction_failure_count: int
    ab3_target_count: int
    ab3_core_extraction_success_count: int
    ab3_core_extraction_failure_count: int
    ab3_full_extraction_success_count: int
    ab3_full_extraction_failure_count: int
    core_changed_count: int
    spec_changed_count: int
    syntax_rescued_by_core: int
    execution_rescued_by_core: int
    syntax_rescued_by_full: int
    execution_rescued_by_full: int
    not_test_assessable_count: int


def load_generation_attempts(
    path: Union[str, pathlib.Path]
) -> List[Dict[str, Any]]:
    """Load agent_tools.finals_rebuild.ollama_generation_runner's
    generation_attempts.jsonl (or any file sharing its per-attempt schema:
    task_id, sample_index, treatment, status, at minimum). Fails closed on
    missing file, invalid JSON, a non-object line, or a missing required
    field. Never guesses a default for a missing field."""
    p = pathlib.Path(path)
    if not p.is_file():
        raise _Ab3RawPipelineError(f"generation attempts file not found: {p}")

    records: List[Dict[str, Any]] = []
    text = p.read_text(encoding="utf-8")
    for line_no, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            obj = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise _Ab3RawPipelineError(
                f"{p}: line {line_no}: invalid JSON: {exc}"
            ) from exc
        if not isinstance(obj, dict):
            raise _Ab3RawPipelineError(
                f"{p}: line {line_no}: expected a JSON object"
            )
        for key in ("task_id", "sample_index", "treatment", "status"):
            if key not in obj:
                raise _Ab3RawPipelineError(
                    f"{p}: line {line_no}: missing required field {key!r}"
                )
        records.append(obj)
    return records


def _extract_for_raw_pipeline(raw_text: str) -> Tuple[Optional[str], str]:
    """Call extraction.extract_code() as-is (no local disambiguation, no
    "first"/"last" fence selection) and return (completion_or_None,
    extraction_status)."""
    result = extract_code(raw_text)
    ok = (
        result.extraction_status == "extracted"
        and bool(result.extracted_code)
        and bool(result.extracted_code.strip())
    )
    return (result.extracted_code if ok else None), result.extraction_status


def _process_raw_ab3_task(
    *,
    benchmark: str,
    task_id: str,
    sample_index: int,
    ab1_attempt: Optional[Dict[str, Any]],
    ab2g_attempt: Dict[str, Any],
    evaluator_git_commit: str,
) -> RawAb3TaskResult:
    pair_id = build_public_benchmark_pair_id(benchmark, task_id, sample_index)

    ab1_status = ab1_attempt.get("status") if ab1_attempt else None
    ab1_completion = ab1_attempt.get("completion") if ab1_attempt else None
    ab1_extraction_status = ab1_attempt.get("extraction_status") if ab1_attempt else None

    ab2g_generation_status = ab2g_attempt["status"]
    ab2g_raw_response = ab2g_attempt.get("raw_response")
    ab2g_raw_response_hash = ab2g_attempt.get("raw_response_sha256")
    ab2g_extraction_status = ab2g_attempt.get("extraction_status")
    ab2g_completion = ab2g_attempt.get("completion")

    has_ab3_target = bool(
        isinstance(ab2g_raw_response, str) and ab2g_raw_response.strip()
    )

    if not has_ab3_target:
        return RawAb3TaskResult(
            benchmark=benchmark, task_id=task_id, sample_index=sample_index,
            ab1_status=ab1_status, ab1_completion=ab1_completion,
            ab1_extraction_status=ab1_extraction_status,
            ab2g_generation_status=ab2g_generation_status,
            ab2g_raw_response_hash=ab2g_raw_response_hash,
            ab2g_extraction_status=ab2g_extraction_status,
            ab2g_completion=ab2g_completion,
            ab3_core_raw_output=None, ab3_core_raw_hash=None,
            ab3_core_extraction_status=None, ab3_core_completion=None,
            ab3_core_static=None, ab3_core_execution=None, core_trace=None,
            ab3_full_raw_output=None, ab3_full_raw_hash=None,
            ab3_full_extraction_status=None, ab3_full_completion=None,
            ab3_full_static=None, ab3_full_execution=None, spec_trace=None,
            has_ab3_target=False,
        )

    computed_ab2g_hash = sha256_text(ab2g_raw_response)
    if ab2g_raw_response_hash is not None and ab2g_raw_response_hash != computed_ab2g_hash:
        raise _Ab3RawPipelineError(
            f"task_id={task_id!r}: ab2g raw_response_sha256 {ab2g_raw_response_hash!r} "
            f"does not match sha256(raw_response)={computed_ab2g_hash!r}"
        )
    ab2g_raw_response_hash = computed_ab2g_hash

    # --- Core: Ab2g's RAW response (never the extracted completion, never
    # Ab1) -> Core, once. -----------------------------------------------
    core_result = run_core_adapter(pair_id=pair_id, input_code=ab2g_raw_response)
    ab3_core_raw_output = core_result.output_code
    ab3_core_raw_hash = sha256_text(ab3_core_raw_output)
    core_trace = _finalize_trace(
        core_result.trace, pair_id, _EVAL_TREATMENT_AB3_CORE, ab3_core_raw_hash
    )
    if core_trace.input_hash != ab2g_raw_response_hash:
        raise _Ab3RawPipelineError(
            f"task_id={task_id!r}: Core input_hash does not equal Ab2g raw_response hash"
        )

    ab3_core_completion, ab3_core_extraction_status = _extract_for_raw_pipeline(
        ab3_core_raw_output
    )
    if ab3_core_completion is not None:
        ab3_core_static_res, ab3_core_execution_res = _evaluate(
            code=ab3_core_completion, pair_id=pair_id, run_id=core_trace.run_id,
            treatment=_EVAL_TREATMENT_AB3_CORE, artifact_hash=ab3_core_raw_hash,
            evaluator_git_commit=evaluator_git_commit,
        )
        ab3_core_static = evaluation_result_to_dict(ab3_core_static_res)
        ab3_core_execution = evaluation_result_to_dict(ab3_core_execution_res)
    else:
        ab3_core_static = None
        ab3_core_execution = None

    # --- Full: Core's own RAW output (never Ab2g's raw directly) -> Spec,
    # once. ----------------------------------------------------------------
    spec_result = run_spec_adapter(
        pair_id=pair_id, skill_id=task_id, input_code=ab3_core_raw_output
    )
    ab3_full_raw_output = spec_result.output_code
    ab3_full_raw_hash = sha256_text(ab3_full_raw_output)
    spec_trace = _finalize_trace(
        spec_result.trace, pair_id, _EVAL_TREATMENT_AB3_FULL, ab3_full_raw_hash
    )
    if spec_trace.input_hash != ab3_core_raw_hash:
        raise _Ab3RawPipelineError(
            f"task_id={task_id!r}: Full input_hash does not equal Core raw output hash"
        )

    ab3_full_completion, ab3_full_extraction_status = _extract_for_raw_pipeline(
        ab3_full_raw_output
    )
    if ab3_full_completion is not None:
        ab3_full_static_res, ab3_full_execution_res = _evaluate(
            code=ab3_full_completion, pair_id=pair_id, run_id=spec_trace.run_id,
            treatment=_EVAL_TREATMENT_AB3_FULL, artifact_hash=ab3_full_raw_hash,
            evaluator_git_commit=evaluator_git_commit,
        )
        ab3_full_static = evaluation_result_to_dict(ab3_full_static_res)
        ab3_full_execution = evaluation_result_to_dict(ab3_full_execution_res)
    else:
        ab3_full_static = None
        ab3_full_execution = None

    # --- Chain-identity check over the RAW hashes (Ab1 never participates). --
    ab2g_run = RunMetadata(
        study_id="public_benchmark_raw", pair_id=pair_id, treatment=_EVAL_TREATMENT_AB2G,
        run_id=build_run_id(pair_id, _EVAL_TREATMENT_AB2G, ab2g_raw_response_hash),
        input_artifact_hash=ab2g_raw_response_hash, output_artifact_hash=ab2g_raw_response_hash,
        source_git_commit=_FIXED_SOURCE_GIT_COMMIT, created_at_utc=_FIXED_CREATED_AT_UTC,
    )
    ab3_core_run = RunMetadata(
        study_id="public_benchmark_raw", pair_id=pair_id, treatment=_EVAL_TREATMENT_AB3_CORE,
        run_id=core_trace.run_id,
        input_artifact_hash=ab2g_raw_response_hash, output_artifact_hash=ab3_core_raw_hash,
        source_git_commit=_FIXED_SOURCE_GIT_COMMIT, created_at_utc=_FIXED_CREATED_AT_UTC,
    )
    ab3_full_run = RunMetadata(
        study_id="public_benchmark_raw", pair_id=pair_id, treatment=_EVAL_TREATMENT_AB3_FULL,
        run_id=spec_trace.run_id,
        input_artifact_hash=ab3_core_raw_hash, output_artifact_hash=ab3_full_raw_hash,
        source_git_commit=_FIXED_SOURCE_GIT_COMMIT, created_at_utc=_FIXED_CREATED_AT_UTC,
    )
    for run_meta in (ab2g_run, ab3_core_run, ab3_full_run):
        validate_run_metadata(run_meta)
    try:
        validate_treatment_chain_identity(ab2g_run, ab3_core_run, ab3_full_run)
    except Exception as exc:
        raise _Ab3RawPipelineError(
            f"raw Ab3 treatment chain identity failed for task_id={task_id!r} "
            f"sample_index={sample_index!r}: {exc}"
        ) from exc

    return RawAb3TaskResult(
        benchmark=benchmark, task_id=task_id, sample_index=sample_index,
        ab1_status=ab1_status, ab1_completion=ab1_completion,
        ab1_extraction_status=ab1_extraction_status,
        ab2g_generation_status=ab2g_generation_status,
        ab2g_raw_response_hash=ab2g_raw_response_hash,
        ab2g_extraction_status=ab2g_extraction_status,
        ab2g_completion=ab2g_completion,
        ab3_core_raw_output=ab3_core_raw_output, ab3_core_raw_hash=ab3_core_raw_hash,
        ab3_core_extraction_status=ab3_core_extraction_status,
        ab3_core_completion=ab3_core_completion,
        ab3_core_static=ab3_core_static, ab3_core_execution=ab3_core_execution,
        core_trace=treatment_trace_to_dict(core_trace),
        ab3_full_raw_output=ab3_full_raw_output, ab3_full_raw_hash=ab3_full_raw_hash,
        ab3_full_extraction_status=ab3_full_extraction_status,
        ab3_full_completion=ab3_full_completion,
        ab3_full_static=ab3_full_static, ab3_full_execution=ab3_full_execution,
        spec_trace=treatment_trace_to_dict(spec_trace),
        has_ab3_target=True,
    )


def _build_raw_ab3_summary(
    benchmark: str, results: Sequence[RawAb3TaskResult]
) -> RawAb3RunSummary:
    total = len(results)

    def _static_pass(d: Optional[Dict[str, Any]]) -> bool:
        return d is not None and d.get("syntax_pass") is True

    def _exec_pass(d: Optional[Dict[str, Any]]) -> bool:
        return d is not None and d.get("execution_success") is True

    syntax_rescued_by_core = 0
    execution_rescued_by_core = 0
    syntax_rescued_by_full = 0
    execution_rescued_by_full = 0
    not_test_assessable_count = 0
    core_changed_count = 0
    spec_changed_count = 0

    for r in results:
        # Baseline: Ab2g's raw response did not itself yield an assessable
        # extracted completion. Core/Full "rescuing" it means they produced
        # a completion that Ab2g's own raw response could not.
        base_ok = r.ab2g_extraction_status == "extracted"

        if r.core_trace is not None and r.core_trace.get("changed"):
            core_changed_count += 1
        if r.spec_trace is not None and r.spec_trace.get("changed"):
            spec_changed_count += 1

        if (not base_ok) and _static_pass(r.ab3_core_static):
            syntax_rescued_by_core += 1
        if (not base_ok) and _exec_pass(r.ab3_core_execution):
            execution_rescued_by_core += 1
        if (not base_ok) and _static_pass(r.ab3_full_static):
            syntax_rescued_by_full += 1
        if (not base_ok) and _exec_pass(r.ab3_full_execution):
            execution_rescued_by_full += 1

        if r.ab3_core_completion is None and r.ab3_full_completion is None:
            not_test_assessable_count += 1

    return RawAb3RunSummary(
        benchmark=benchmark,
        total_tasks=total,
        ab1_available_count=sum(1 for r in results if r.ab1_status is not None),
        ab1_missing_count=sum(1 for r in results if r.ab1_status is None),
        ab2g_raw_available_count=sum(1 for r in results if r.has_ab3_target),
        ab2g_raw_missing_count=sum(1 for r in results if not r.has_ab3_target),
        ab2g_extraction_success_count=sum(
            1 for r in results if r.ab2g_extraction_status == "extracted"
        ),
        ab2g_extraction_failure_count=sum(
            1 for r in results
            if r.ab2g_extraction_status is not None and r.ab2g_extraction_status != "extracted"
        ),
        ab3_target_count=sum(1 for r in results if r.has_ab3_target),
        ab3_core_extraction_success_count=sum(
            1 for r in results if r.ab3_core_extraction_status == "extracted"
        ),
        ab3_core_extraction_failure_count=sum(
            1 for r in results
            if r.ab3_core_extraction_status is not None and r.ab3_core_extraction_status != "extracted"
        ),
        ab3_full_extraction_success_count=sum(
            1 for r in results if r.ab3_full_extraction_status == "extracted"
        ),
        ab3_full_extraction_failure_count=sum(
            1 for r in results
            if r.ab3_full_extraction_status is not None and r.ab3_full_extraction_status != "extracted"
        ),
        core_changed_count=core_changed_count,
        spec_changed_count=spec_changed_count,
        syntax_rescued_by_core=syntax_rescued_by_core,
        execution_rescued_by_core=execution_rescued_by_core,
        syntax_rescued_by_full=syntax_rescued_by_full,
        execution_rescued_by_full=execution_rescued_by_full,
        not_test_assessable_count=not_test_assessable_count,
    )


def _raw_result_to_dict(result: RawAb3TaskResult) -> Dict[str, Any]:
    return {
        "benchmark": result.benchmark,
        "task_id": result.task_id,
        "sample_index": result.sample_index,
        "ab1_status": result.ab1_status,
        "ab1_completion": result.ab1_completion,
        "ab1_extraction_status": result.ab1_extraction_status,
        "ab2g_generation_status": result.ab2g_generation_status,
        "ab2g_raw_response_hash": result.ab2g_raw_response_hash,
        "ab2g_extraction_status": result.ab2g_extraction_status,
        "ab2g_completion": result.ab2g_completion,
        "ab3_core_raw_output": result.ab3_core_raw_output,
        "ab3_core_raw_hash": result.ab3_core_raw_hash,
        "ab3_core_extraction_status": result.ab3_core_extraction_status,
        "ab3_core_completion": result.ab3_core_completion,
        "ab3_core_static": result.ab3_core_static,
        "ab3_core_execution": result.ab3_core_execution,
        "core_trace": result.core_trace,
        "ab3_full_raw_output": result.ab3_full_raw_output,
        "ab3_full_raw_hash": result.ab3_full_raw_hash,
        "ab3_full_extraction_status": result.ab3_full_extraction_status,
        "ab3_full_completion": result.ab3_full_completion,
        "ab3_full_static": result.ab3_full_static,
        "ab3_full_execution": result.ab3_full_execution,
        "spec_trace": result.spec_trace,
        "has_ab3_target": result.has_ab3_target,
        "test_status": result.test_status,
        "test_pass": result.test_pass,
    }


def _raw_summary_to_dict(summary: RawAb3RunSummary) -> Dict[str, Any]:
    return {
        "benchmark": summary.benchmark,
        "total_tasks": summary.total_tasks,
        "ab1_available_count": summary.ab1_available_count,
        "ab1_missing_count": summary.ab1_missing_count,
        "ab2g_raw_available_count": summary.ab2g_raw_available_count,
        "ab2g_raw_missing_count": summary.ab2g_raw_missing_count,
        "ab2g_extraction_success_count": summary.ab2g_extraction_success_count,
        "ab2g_extraction_failure_count": summary.ab2g_extraction_failure_count,
        "ab3_target_count": summary.ab3_target_count,
        "ab3_core_extraction_success_count": summary.ab3_core_extraction_success_count,
        "ab3_core_extraction_failure_count": summary.ab3_core_extraction_failure_count,
        "ab3_full_extraction_success_count": summary.ab3_full_extraction_success_count,
        "ab3_full_extraction_failure_count": summary.ab3_full_extraction_failure_count,
        "core_changed_count": summary.core_changed_count,
        "spec_changed_count": summary.spec_changed_count,
        "syntax_rescued_by_core": summary.syntax_rescued_by_core,
        "execution_rescued_by_core": summary.execution_rescued_by_core,
        "syntax_rescued_by_full": summary.syntax_rescued_by_full,
        "execution_rescued_by_full": summary.execution_rescued_by_full,
        "not_test_assessable_count": summary.not_test_assessable_count,
    }


def _write_jsonl_allow_empty(
    records: Sequence[Dict[str, Any]], path: pathlib.Path
) -> None:
    """Write *records* as JSONL, one per line, creating the file even when
    *records* is empty — a treatment with zero extractable completions
    still gets a valid, empty file rather than none at all, and never a
    fabricated/padded row."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")


def run_public_benchmark_treatments_from_attempts(
    *,
    tasks_path: Union[str, pathlib.Path],
    generation_attempts_path: Union[str, pathlib.Path],
    benchmark: str,
    artifact_root: Union[str, pathlib.Path],
    evaluator_git_commit: str,
) -> RawAb3RunSummary:
    """
    Run Ab3-Core/Ab3-Full for every task in *tasks_path*, gated only on
    whether that task's Ab2g attempt (from *generation_attempts_path*, the
    schema ollama_generation_runner.py's generation_attempts.jsonl writes)
    has a non-empty raw_response — never on Ab2g extraction success, and
    never on Ab1 at all. Ab1 is recorded for reference only and never fed
    to Core/Spec. Core/Spec always consume the raw model response (Ab2g's
    raw -> Core; Core's own raw output -> Spec), and extract_code() is
    re-run, unmodified and with no first/last-block disambiguation, after
    each stage to decide whether that stage's output is assessable.

    Fails closed (raises PublicBenchmarkRunnerError/_Ab3RawPipelineError)
    on: a task with no Ab2g attempt at all, a duplicate (task_id,
    sample_index, treatment) attempt row, an attempt referencing an
    unknown task_id, an Ab2g raw_response_sha256 mismatch, a chain-identity
    failure, or an unwritable artifact_root. Never fabricates a missing
    completion and never silently skips a task.
    """
    tasks: List[PublicBenchmarkTask] = load_benchmark_tasks(tasks_path, benchmark)
    attempts = load_generation_attempts(generation_attempts_path)

    known_task_ids = {t.task_id for t in tasks}
    seen_keys: set[tuple[str, int, str]] = set()
    by_key: Dict[tuple[str, int, str], Dict[str, Any]] = {}
    for a in attempts:
        if a["task_id"] not in known_task_ids:
            raise _Ab3RawPipelineError(
                f"generation attempt references unknown task_id {a['task_id']!r}"
            )
        key = (a["task_id"], a["sample_index"], a["treatment"])
        if key in seen_keys:
            raise _Ab3RawPipelineError(f"duplicate generation attempt for {key!r}")
        seen_keys.add(key)
        by_key[key] = a

    results: List[RawAb3TaskResult] = []
    for task in tasks:
        sample_index = 0
        ab2g_key = (task.task_id, sample_index, "ab2g")
        if ab2g_key not in by_key:
            raise _Ab3RawPipelineError(
                f"task_id={task.task_id!r}: no Ab2g generation attempt found "
                f"(sample_index={sample_index!r})"
            )
        ab1_attempt = by_key.get((task.task_id, sample_index, "ab1"))
        ab2g_attempt = by_key[ab2g_key]

        results.append(
            _process_raw_ab3_task(
                benchmark=benchmark, task_id=task.task_id, sample_index=sample_index,
                ab1_attempt=ab1_attempt, ab2g_attempt=ab2g_attempt,
                evaluator_git_commit=evaluator_git_commit,
            )
        )

    summary = _build_raw_ab3_summary(benchmark, results)

    out_root = pathlib.Path(artifact_root) / "public_benchmark_raw" / benchmark
    _write_json_deterministic(
        [_raw_result_to_dict(r) for r in results], out_root / "results.json"
    )
    _write_json_deterministic(_raw_summary_to_dict(summary), out_root / "summary.json")

    evalplus_dir = out_root / "evalplus"
    _write_jsonl_allow_empty(
        [{"task_id": r.task_id, "completion": r.ab1_completion} for r in results if r.ab1_completion],
        evalplus_dir / "ab1.jsonl",
    )
    _write_jsonl_allow_empty(
        [{"task_id": r.task_id, "completion": r.ab2g_completion} for r in results if r.ab2g_completion],
        evalplus_dir / "ab2g.jsonl",
    )
    _write_jsonl_allow_empty(
        [{"task_id": r.task_id, "completion": r.ab3_core_completion} for r in results if r.ab3_core_completion],
        evalplus_dir / "ab3_core.jsonl",
    )
    _write_jsonl_allow_empty(
        [{"task_id": r.task_id, "completion": r.ab3_full_completion} for r in results if r.ab3_full_completion],
        evalplus_dir / "ab3_full.jsonl",
    )

    return summary
