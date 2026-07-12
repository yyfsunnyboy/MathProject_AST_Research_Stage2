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
from agent_tools.finals_rebuild.spec_adapter import run_spec_adapter
from agent_tools.finals_rebuild.static_evaluator import evaluate_static
from agent_tools.finals_rebuild.trace import (
    TreatmentTrace,
    treatment_trace_to_dict,
    validate_treatment_trace,
)

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
