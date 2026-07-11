"""
Fixed-fixture pilot runner for the finals-rebuild ablation study.

Validates the complete reporting chain for all four treatment stages:
  ab1 (Bare) → ab2 (Scaffold) → ab3_core (Scaffold + Core)
             → ab3_full (Scaffold + Core + Spec)

Design
------
The pilot runner is a thin wrapper around run_paired_pipeline():
  1. Loads fixture records from a JSON file.
  2. Converts each fixture into a PairedPipelineInput (with TestSuite).
  3. Calls run_paired_pipeline() which handles Core/Spec adapters,
     execution evaluation, and test evaluation internally.
  4. Reads evaluation results from TreatmentOutput.evaluation and
     TreatmentOutput.changed to compute per-fixture and aggregate stats.
  5. Writes pilot_results.json (per-fixture) and pilot_summary.json.

No model calls.  No new Healer rules.  No MCRI computation.
MCRI fields are reserved as null for a future commit.

Statistics
----------
core_changed   : count of fixtures where ab3_core code ≠ ab2 code.
core_rescued   : count where ab2.test_pass != True AND ab3_core.test_pass == True.
core_regression: count where ab2.test_pass == True AND ab3_core.test_pass != True.
spec_changed   : count where ab3_full code ≠ ab3_core code.
spec_rescued   : count where ab3_core.test_pass != True AND ab3_full.test_pass == True.
spec_regression: count where ab3_core.test_pass == True AND ab3_full.test_pass != True.

Fixture JSON schema
-------------------
Each fixture record is a JSON object with keys::

    case_id, description, study_id, skill_id, model_id, model_revision,
    sample_index, seed, generation_config, created_at_utc,
    source_git_commit, bare_prompt, scaffold_prompt,
    raw_ab1_response, raw_scaffold_response, test_suite

test_suite::

    {
      "suite_id": "...",
      "timeout_seconds": 3.0,
      "numeric_tolerance": 1e-6,
      "cases": [
        {
          "case_id": "...",
          "function_name": "...",
          "args": [...],
          "kwargs": {},
          "expected": ...,
          "comparison_mode": "exact"
        }
      ]
    }
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from agent_tools.finals_rebuild.artifacts import (
    PairMetadata,
    build_pair_id,
    sha256_json,
    sha256_text,
)
from agent_tools.finals_rebuild.pipeline import (
    PairedPipelineInput,
    PipelineError,
    run_paired_pipeline,
)
from agent_tools.finals_rebuild.test_contract import (
    TestCase,
    TestSuite,
)

# ---------------------------------------------------------------------------
# Fixture → pipeline conversion helpers
# ---------------------------------------------------------------------------


def _build_test_suite(ts_data: Dict[str, Any]) -> TestSuite:
    """Convert a fixture's test_suite dict to a TestSuite dataclass."""
    cases = [
        TestCase(
            case_id=tc["case_id"],
            function_name=tc["function_name"],
            args=tc.get("args", []),
            kwargs=tc.get("kwargs", {}),
            expected=tc.get("expected"),
            comparison_mode=tc.get("comparison_mode", "exact"),
        )
        for tc in ts_data["cases"]
    ]
    return TestSuite(
        suite_id=ts_data["suite_id"],
        cases=cases,
        timeout_seconds=float(ts_data.get("timeout_seconds", 3.0)),
        numeric_tolerance=float(ts_data.get("numeric_tolerance", 1e-6)),
    )


def _build_pair_metadata(
    fx: Dict[str, Any],
    source_git_commit: str,
) -> PairMetadata:
    """Build a fully-consistent PairMetadata from a fixture dict."""
    bare_hash = sha256_text(fx["bare_prompt"])
    scaffold_hash = sha256_text(fx["scaffold_prompt"])
    gen_config_hash = sha256_json(fx.get("generation_config", {}))
    pair_id = build_pair_id(
        study_id=fx["study_id"],
        model_id=fx["model_id"],
        model_revision=fx["model_revision"],
        skill_id=fx["skill_id"],
        sample_index=fx["sample_index"],
        seed=fx.get("seed"),
        bare_prompt_hash=bare_hash,
        scaffold_prompt_hash=scaffold_hash,
        generation_config_hash=gen_config_hash,
    )
    return PairMetadata(
        study_id=fx["study_id"],
        pair_id=pair_id,
        model_id=fx["model_id"],
        model_revision=fx["model_revision"],
        skill_id=fx["skill_id"],
        sample_index=fx["sample_index"],
        seed=fx.get("seed"),
        bare_prompt_hash=bare_hash,
        scaffold_prompt_hash=scaffold_hash,
        generation_config_hash=gen_config_hash,
        source_git_commit=fx.get("source_git_commit", source_git_commit),
        created_at_utc=fx["created_at_utc"],
    )


# ---------------------------------------------------------------------------
# Per-fixture result
# ---------------------------------------------------------------------------


@dataclass
class TreatmentPilotResult:
    """Evaluation summary for one treatment in one fixture."""

    treatment: str
    output_code_hash: str
    changed: bool
    syntax_pass: bool
    execution_success: Optional[bool]
    test_pass: Optional[bool]
    tests_passed: Optional[int]
    tests_total: Optional[int]
    execution_status: str
    test_status: str
    exception_summary: Optional[str]


@dataclass
class FixturePilotResult:
    """Full pilot result for one fixture case."""

    case_id: str
    pair_id: str
    pipeline_error: Optional[str]
    treatments: Dict[str, TreatmentPilotResult]
    # Cross-treatment comparison flags
    core_changed: bool = False
    core_rescued: bool = False
    core_regression: bool = False
    spec_changed: bool = False
    spec_rescued: bool = False
    spec_regression: bool = False


# ---------------------------------------------------------------------------
# Per-treatment summary
# ---------------------------------------------------------------------------


@dataclass
class TreatmentSummary:
    syntax_pass_count: int = 0
    execution_success_count: int = 0
    test_pass_count: int = 0


# ---------------------------------------------------------------------------
# Aggregate summary
# ---------------------------------------------------------------------------


@dataclass
class PilotSummary:
    """Aggregate statistics across all fixture cases.

    ``syntax_pass_count``, ``execution_success_count``, ``test_pass_count``
    are totals summed across ALL four treatment stages (n * 4 opportunities).

    ``by_treatment`` breaks out per-stage counts (each is 0..n).

    ``core_changed`` / ``core_rescued`` / ``core_regression`` and their
    ``spec_*`` counterparts are per-fixture counts (0..n).

    ``mcri`` is reserved for a future commit; always null in this pilot.
    """

    n: int = 0
    syntax_pass_count: int = 0
    execution_success_count: int = 0
    test_pass_count: int = 0
    by_treatment: Dict[str, TreatmentSummary] = field(
        default_factory=lambda: {
            t: TreatmentSummary()
            for t in ("ab1", "ab2", "ab3_core", "ab3_full")
        }
    )
    core_changed: int = 0
    core_rescued: int = 0
    core_regression: int = 0
    spec_changed: int = 0
    spec_rescued: int = 0
    spec_regression: int = 0
    mcri: Optional[float] = None


# ---------------------------------------------------------------------------
# Rescue / regression helpers
# ---------------------------------------------------------------------------


def _is_rescued(before_test_pass: Optional[bool], after_test_pass: Optional[bool]) -> bool:
    """True iff the previous stage did NOT pass and the current stage DOES pass."""
    return before_test_pass != True and after_test_pass == True


def _is_regression(
    before_test_pass: Optional[bool], after_test_pass: Optional[bool]
) -> bool:
    """True iff the previous stage DID pass and the current stage does NOT pass."""
    return before_test_pass == True and after_test_pass != True


# ---------------------------------------------------------------------------
# Per-fixture runner
# ---------------------------------------------------------------------------


def _run_fixture(
    fx: Dict[str, Any],
    artifact_root: pathlib.Path,
    evaluator_git_commit: str,
    source_git_commit: str,
) -> FixturePilotResult:
    """Run one fixture through the full pipeline + evaluation chain."""
    meta = _build_pair_metadata(fx, source_git_commit)
    test_suite = _build_test_suite(fx["test_suite"])

    pipeline_input = PairedPipelineInput(
        pair_metadata=meta,
        bare_prompt_text=fx["bare_prompt"],
        scaffold_prompt_text=fx["scaffold_prompt"],
        raw_ab1_response=fx["raw_ab1_response"],
        raw_scaffold_response=fx["raw_scaffold_response"],
        artifact_root=artifact_root,
        evaluator_git_commit=evaluator_git_commit,
        test_suite=test_suite,
    )

    # Pipeline handles Core/Spec adapters, execution eval, and test eval.
    try:
        pipeline_result = run_paired_pipeline(pipeline_input)
    except PipelineError as exc:
        # Fail-open for the pilot: record the error so the summary can still
        # be produced for the remaining fixtures.
        empty_tr = TreatmentPilotResult(
            treatment="",
            output_code_hash="",
            changed=False,
            syntax_pass=False,
            execution_success=None,
            test_pass=None,
            tests_passed=None,
            tests_total=None,
            execution_status="not_run",
            test_status="not_run",
            exception_summary=str(exc),
        )
        return FixturePilotResult(
            case_id=fx["case_id"],
            pair_id=meta.pair_id,
            pipeline_error=str(exc),
            treatments={t: empty_tr for t in ("ab1", "ab2", "ab3_core", "ab3_full")},
        )

    treatments: Dict[str, TreatmentPilotResult] = {}
    for treatment, to in pipeline_result.treatment_outputs.items():
        ev = to.evaluation
        exc_summary: Optional[str] = None
        if ev is not None and ev.exception_type:
            exc_summary = (
                f"{ev.exception_type}: {ev.exception_message}"
                if ev.exception_message
                else ev.exception_type
            )
        treatments[treatment] = TreatmentPilotResult(
            treatment=treatment,
            output_code_hash=to.output_hash,
            changed=to.changed,
            syntax_pass=(ev.syntax_pass if ev is not None else False),
            execution_success=(ev.execution_success if ev is not None else None),
            test_pass=(ev.test_pass if ev is not None else None),
            tests_passed=(ev.tests_passed if ev is not None else None),
            tests_total=(ev.tests_total if ev is not None else None),
            execution_status=(ev.execution_status if ev is not None else "not_run"),
            test_status=(ev.test_status if ev is not None else "not_run"),
            exception_summary=exc_summary,
        )

    ab2_tp = treatments["ab2"].test_pass
    ab3c_tp = treatments["ab3_core"].test_pass
    ab3f_tp = treatments["ab3_full"].test_pass

    return FixturePilotResult(
        case_id=fx["case_id"],
        pair_id=pipeline_result.pair_id,
        pipeline_error=None,
        treatments=treatments,
        core_changed=treatments["ab3_core"].changed,
        core_rescued=_is_rescued(ab2_tp, ab3c_tp),
        core_regression=_is_regression(ab2_tp, ab3c_tp),
        spec_changed=treatments["ab3_full"].changed,
        spec_rescued=_is_rescued(ab3c_tp, ab3f_tp),
        spec_regression=_is_regression(ab3c_tp, ab3f_tp),
    )


# ---------------------------------------------------------------------------
# Summary computation
# ---------------------------------------------------------------------------


def _compute_summary(results: List[FixturePilotResult]) -> PilotSummary:
    s = PilotSummary(n=len(results))
    for r in results:
        for treatment, tr in r.treatments.items():
            ts = s.by_treatment[treatment]
            if tr.syntax_pass:
                ts.syntax_pass_count += 1
                s.syntax_pass_count += 1
            if tr.execution_success is True:
                ts.execution_success_count += 1
                s.execution_success_count += 1
            if tr.test_pass is True:
                ts.test_pass_count += 1
                s.test_pass_count += 1
        if r.core_changed:
            s.core_changed += 1
        if r.core_rescued:
            s.core_rescued += 1
        if r.core_regression:
            s.core_regression += 1
        if r.spec_changed:
            s.spec_changed += 1
        if r.spec_rescued:
            s.spec_rescued += 1
        if r.spec_regression:
            s.spec_regression += 1
    return s


# ---------------------------------------------------------------------------
# JSON serialisation helpers
# ---------------------------------------------------------------------------


def _serialise_treatment(tr: TreatmentPilotResult) -> Dict[str, Any]:
    return {
        "treatment": tr.treatment,
        "output_code_hash": tr.output_code_hash,
        "changed": tr.changed,
        "syntax_pass": tr.syntax_pass,
        "execution_success": tr.execution_success,
        "test_pass": tr.test_pass,
        "tests_passed": tr.tests_passed,
        "tests_total": tr.tests_total,
        "execution_status": tr.execution_status,
        "test_status": tr.test_status,
        "exception_summary": tr.exception_summary,
    }


def _serialise_fixture_result(r: FixturePilotResult) -> Dict[str, Any]:
    return {
        "case_id": r.case_id,
        "pair_id": r.pair_id,
        "pipeline_error": r.pipeline_error,
        "core_changed": r.core_changed,
        "core_rescued": r.core_rescued,
        "core_regression": r.core_regression,
        "spec_changed": r.spec_changed,
        "spec_rescued": r.spec_rescued,
        "spec_regression": r.spec_regression,
        "treatments": {
            t: _serialise_treatment(tr) for t, tr in r.treatments.items()
        },
    }


def _serialise_summary(s: PilotSummary) -> Dict[str, Any]:
    return {
        "n": s.n,
        "syntax_pass_count": s.syntax_pass_count,
        "execution_success_count": s.execution_success_count,
        "test_pass_count": s.test_pass_count,
        "by_treatment": {
            t: {
                "syntax_pass_count": ts.syntax_pass_count,
                "execution_success_count": ts.execution_success_count,
                "test_pass_count": ts.test_pass_count,
            }
            for t, ts in s.by_treatment.items()
        },
        "core_changed": s.core_changed,
        "core_rescued": s.core_rescued,
        "core_regression": s.core_regression,
        "spec_changed": s.spec_changed,
        "spec_rescued": s.spec_rescued,
        "spec_regression": s.spec_regression,
        "mcri": s.mcri,
    }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run_pilot(
    fixtures_path: pathlib.Path,
    artifact_root: pathlib.Path,
    output_dir: pathlib.Path,
    evaluator_git_commit: str = "pilot_evaluator_stub",
    source_git_commit: str = "pilot_stub",
) -> PilotSummary:
    """
    Load fixtures, run each through the full pipeline + evaluation chain,
    and write summary outputs.

    Parameters
    ----------
    fixtures_path
        Path to a JSON file containing a list of fixture records (see the
        module docstring for the fixture schema).
    artifact_root
        Root directory under which per-pair artifact directories are created
        (passed as ``PairedPipelineInput.artifact_root``).  A dedicated
        subdirectory per run is recommended so successive pilot runs do not
        conflict on immutable artifacts.
    output_dir
        Directory where ``pilot_results.json`` and ``pilot_summary.json``
        are written (created if absent).
    evaluator_git_commit
        Fixed commit identifier for the evaluator — deliberately separate
        from the artifact source_git_commit; passed to
        ``PairedPipelineInput.evaluator_git_commit``.
    source_git_commit
        Fallback ``source_git_commit`` for fixtures that do not provide one.

    Returns
    -------
    PilotSummary
        The aggregate statistics object (also serialised to
        ``output_dir/pilot_summary.json``).
    """
    fixtures_path = pathlib.Path(fixtures_path)
    artifact_root = pathlib.Path(artifact_root)
    output_dir = pathlib.Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with fixtures_path.open(encoding="utf-8") as fh:
        fixtures: List[Dict[str, Any]] = json.load(fh)

    results: List[FixturePilotResult] = []
    for fx in fixtures:
        result = _run_fixture(fx, artifact_root, evaluator_git_commit, source_git_commit)
        results.append(result)

    summary = _compute_summary(results)

    (output_dir / "pilot_results.json").write_text(
        json.dumps(
            [_serialise_fixture_result(r) for r in results],
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (output_dir / "pilot_summary.json").write_text(
        json.dumps(_serialise_summary(summary), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return summary
