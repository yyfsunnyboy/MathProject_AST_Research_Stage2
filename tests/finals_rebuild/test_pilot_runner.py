"""
Tests for the fixed-fixture pilot runner (pilot_runner.py).

All tests use a fresh tmp_path (pytest fixture) for both the artifact root
and the output directory — no test shares state with another.  The pilot
cases JSON is read from the checked-in fixtures file; every test expects
exactly 7 cases.

No model calls, no network calls, no MCRI computation.
"""

from __future__ import annotations

import json
import os
import sys
import pathlib
from typing import Any, Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import pytest

from agent_tools.finals_rebuild.pilot_runner import (
    PilotSummary,
    run_pilot,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FIXTURES_PATH = pathlib.Path(__file__).parent / "fixtures" / "pilot_cases.json"
_N_FIXTURES = 7

# Reuse the same evaluator commit stub for all tests — distinct from the
# production git HEAD so results are never confused with real evaluations.
_EVAL_COMMIT = "test_pilot_eval_stub"


def _pilot(tmp_path: pathlib.Path) -> PilotSummary:
    """Run the pilot and return the summary object."""
    return run_pilot(
        fixtures_path=FIXTURES_PATH,
        artifact_root=tmp_path / "artifacts",
        output_dir=tmp_path / "output",
        evaluator_git_commit=_EVAL_COMMIT,
    )


def _load_results(tmp_path: pathlib.Path) -> List[Dict[str, Any]]:
    return json.loads((tmp_path / "output" / "pilot_results.json").read_text(encoding="utf-8"))


def _load_summary(tmp_path: pathlib.Path) -> Dict[str, Any]:
    return json.loads((tmp_path / "output" / "pilot_summary.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Fixture sanity
# ---------------------------------------------------------------------------


def test_fixtures_file_exists():
    """The pilot_cases.json file must exist and be valid JSON."""
    assert FIXTURES_PATH.exists(), f"fixtures file not found: {FIXTURES_PATH}"
    data = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert len(data) == _N_FIXTURES


def test_fixtures_case_ids_unique():
    """Every fixture must have a distinct case_id."""
    data = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
    ids = [fx["case_id"] for fx in data]
    assert len(ids) == len(set(ids))


def test_fixtures_required_fields():
    """Every fixture must have all required fields."""
    required = {
        "case_id", "study_id", "skill_id", "model_id", "model_revision",
        "sample_index", "seed", "created_at_utc", "source_git_commit",
        "bare_prompt", "scaffold_prompt",
        "raw_ab1_response", "raw_scaffold_response",
        "test_suite",
    }
    data = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
    for fx in data:
        missing = required - set(fx)
        assert not missing, f"case {fx.get('case_id')!r} missing fields: {missing}"


# ---------------------------------------------------------------------------
# Completion
# ---------------------------------------------------------------------------


def test_all_fixtures_complete(tmp_path):
    """All 7 fixtures run to completion; output files are written."""
    summary = _pilot(tmp_path)
    assert summary.n == _N_FIXTURES

    results_path = tmp_path / "output" / "pilot_results.json"
    summary_path = tmp_path / "output" / "pilot_summary.json"
    assert results_path.exists()
    assert summary_path.exists()

    results = _load_results(tmp_path)
    assert len(results) == _N_FIXTURES

    # Every fixture result must have entries for all four treatments.
    for r in results:
        assert set(r["treatments"]) == {"ab1", "ab2", "ab3_core", "ab3_full"}


def test_no_pipeline_errors(tmp_path):
    """None of the 7 fixture cases should trigger a PipelineError."""
    _pilot(tmp_path)
    results = _load_results(tmp_path)
    for r in results:
        assert r["pipeline_error"] is None, (
            f"case {r['case_id']!r} had a pipeline error: {r['pipeline_error']}"
        )


# ---------------------------------------------------------------------------
# Core rescued / changed / regression
# ---------------------------------------------------------------------------


def test_core_rescued_count(tmp_path):
    """Exactly one fixture (core_rescues_fullwidth) should be core_rescued."""
    summary = _pilot(tmp_path)
    assert summary.core_rescued == 1


def test_core_changed_count(tmp_path):
    """Exactly one fixture (core_rescues_fullwidth) should have core_changed."""
    summary = _pilot(tmp_path)
    assert summary.core_changed == 1


def test_core_regression_zero(tmp_path):
    """No fixture should produce a core_regression in the pilot suite."""
    summary = _pilot(tmp_path)
    assert summary.core_regression == 0


def test_core_rescues_fullwidth_case(tmp_path):
    """The core_rescues_fullwidth case: ab2 fails syntax, ab3_core passes."""
    _pilot(tmp_path)
    results = _load_results(tmp_path)
    case = next(r for r in results if r["case_id"] == "core_rescues_fullwidth")

    # ab2 must fail (full-width punctuation → syntax error)
    ab2 = case["treatments"]["ab2"]
    assert ab2["syntax_pass"] is False, "ab2 must fail syntax on full-width code"
    assert ab2["test_pass"] is None, "ab2 test must not run when syntax fails"

    # ab3_core must be rescued by Core Healer
    ab3c = case["treatments"]["ab3_core"]
    assert ab3c["syntax_pass"] is True, "ab3_core must pass syntax after Core Healer"
    assert ab3c["test_pass"] is True, "ab3_core must pass tests after Core Healer"
    assert ab3c["changed"] is True, "ab3_core must report changed=True"

    # Flags
    assert case["core_changed"] is True
    assert case["core_rescued"] is True
    assert case["core_regression"] is False


def test_core_noop_not_rescued(tmp_path):
    """The core_noop case: clean code, Core makes no change, not counted as rescued."""
    _pilot(tmp_path)
    results = _load_results(tmp_path)
    case = next(r for r in results if r["case_id"] == "core_noop")

    assert case["core_changed"] is False
    assert case["core_rescued"] is False
    assert case["core_regression"] is False

    ab3c = case["treatments"]["ab3_core"]
    assert ab3c["changed"] is False
    # Both ab2 and ab3_core should pass tests on clean code
    assert case["treatments"]["ab2"]["test_pass"] is True
    assert ab3c["test_pass"] is True


# ---------------------------------------------------------------------------
# Spec is no-op
# ---------------------------------------------------------------------------


def test_spec_changed_zero(tmp_path):
    """Spec Adapter is currently disabled; spec_changed must be 0 for all fixtures."""
    summary = _pilot(tmp_path)
    assert summary.spec_changed == 0


def test_spec_rescued_zero(tmp_path):
    """Spec Adapter is currently disabled; spec_rescued must be 0."""
    summary = _pilot(tmp_path)
    assert summary.spec_rescued == 0


def test_spec_regression_zero(tmp_path):
    """Spec Adapter is currently disabled; spec_regression must be 0."""
    summary = _pilot(tmp_path)
    assert summary.spec_regression == 0


def test_spec_noop_case(tmp_path):
    """The spec_noop fixture verifies ab3_full == ab3_core (no Spec change)."""
    _pilot(tmp_path)
    results = _load_results(tmp_path)
    case = next(r for r in results if r["case_id"] == "spec_noop")

    assert case["spec_changed"] is False
    assert case["spec_rescued"] is False
    ab3c = case["treatments"]["ab3_core"]
    ab3f = case["treatments"]["ab3_full"]
    # Output hashes must be identical when Spec is no-op
    assert ab3c["output_code_hash"] == ab3f["output_code_hash"]
    assert ab3f["test_pass"] is True


# ---------------------------------------------------------------------------
# Individual treatment behaviour
# ---------------------------------------------------------------------------


def test_syntax_fail_ab1_case(tmp_path):
    """syntax_fail_ab1: ab1 fails syntax, scaffold treatments pass."""
    _pilot(tmp_path)
    results = _load_results(tmp_path)
    case = next(r for r in results if r["case_id"] == "syntax_fail_ab1")

    assert case["treatments"]["ab1"]["syntax_pass"] is False
    assert case["treatments"]["ab2"]["syntax_pass"] is True
    assert case["treatments"]["ab2"]["test_pass"] is True
    assert case["treatments"]["ab3_core"]["syntax_pass"] is True
    assert case["treatments"]["ab3_full"]["syntax_pass"] is True


def test_execution_fail_case(tmp_path):
    """execution_fail: syntax passes, but execution fails for all treatments."""
    _pilot(tmp_path)
    results = _load_results(tmp_path)
    case = next(r for r in results if r["case_id"] == "execution_fail")

    for treatment in ("ab1", "ab2", "ab3_core", "ab3_full"):
        tr = case["treatments"][treatment]
        assert tr["syntax_pass"] is True, f"{treatment} must pass syntax"
        assert tr["execution_success"] is False, f"{treatment} must fail execution"
        assert tr["test_pass"] is None, f"{treatment} test must not run"


def test_test_fail_case(tmp_path):
    """test_fail: execution succeeds but wrong answer → test_pass=False."""
    _pilot(tmp_path)
    results = _load_results(tmp_path)
    case = next(r for r in results if r["case_id"] == "test_fail")

    for treatment in ("ab1", "ab2", "ab3_core", "ab3_full"):
        tr = case["treatments"][treatment]
        assert tr["syntax_pass"] is True
        assert tr["execution_success"] is True
        assert tr["test_pass"] is False, f"{treatment} must fail test with wrong answer"


def test_success_all_case(tmp_path):
    """success_all: all four treatments must pass syntax, exec, and tests."""
    _pilot(tmp_path)
    results = _load_results(tmp_path)
    case = next(r for r in results if r["case_id"] == "success_all")

    for treatment in ("ab1", "ab2", "ab3_core", "ab3_full"):
        tr = case["treatments"][treatment]
        assert tr["syntax_pass"] is True
        assert tr["execution_success"] is True
        assert tr["test_pass"] is True


# ---------------------------------------------------------------------------
# Summary consistency
# ---------------------------------------------------------------------------


def test_summary_consistent_with_per_fixture_results(tmp_path):
    """pilot_summary.json must be consistent with pilot_results.json."""
    _pilot(tmp_path)
    results = _load_results(tmp_path)
    summary = _load_summary(tmp_path)

    assert summary["n"] == len(results)
    assert summary["core_rescued"] == sum(1 for r in results if r["core_rescued"])
    assert summary["core_regression"] == sum(1 for r in results if r["core_regression"])
    assert summary["core_changed"] == sum(1 for r in results if r["core_changed"])
    assert summary["spec_changed"] == sum(1 for r in results if r["spec_changed"])
    assert summary["spec_rescued"] == sum(1 for r in results if r["spec_rescued"])
    assert summary["spec_regression"] == sum(1 for r in results if r["spec_regression"])

    # Verify per-treatment counts in by_treatment section.
    for treatment in ("ab1", "ab2", "ab3_core", "ab3_full"):
        expected_syntax = sum(
            1 for r in results if r["treatments"][treatment]["syntax_pass"]
        )
        expected_exec = sum(
            1 for r in results
            if r["treatments"][treatment]["execution_success"] is True
        )
        expected_test = sum(
            1 for r in results
            if r["treatments"][treatment]["test_pass"] is True
        )
        bt = summary["by_treatment"][treatment]
        assert bt["syntax_pass_count"] == expected_syntax, treatment
        assert bt["execution_success_count"] == expected_exec, treatment
        assert bt["test_pass_count"] == expected_test, treatment

    # Total counts must equal sum across all treatments
    total_syntax = sum(
        summary["by_treatment"][t]["syntax_pass_count"]
        for t in ("ab1", "ab2", "ab3_core", "ab3_full")
    )
    assert summary["syntax_pass_count"] == total_syntax


def test_summary_mcri_is_null(tmp_path):
    """MCRI is reserved for a future commit; must be null in pilot summary."""
    _pilot(tmp_path)
    summary = _load_summary(tmp_path)
    assert summary["mcri"] is None


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_pilot_is_deterministic(tmp_path):
    """Running the pilot twice with separate artifact roots gives the same summary."""
    s1 = run_pilot(
        fixtures_path=FIXTURES_PATH,
        artifact_root=tmp_path / "run1" / "artifacts",
        output_dir=tmp_path / "run1" / "output",
        evaluator_git_commit=_EVAL_COMMIT,
    )
    s2 = run_pilot(
        fixtures_path=FIXTURES_PATH,
        artifact_root=tmp_path / "run2" / "artifacts",
        output_dir=tmp_path / "run2" / "output",
        evaluator_git_commit=_EVAL_COMMIT,
    )
    assert s1.n == s2.n
    assert s1.core_changed == s2.core_changed
    assert s1.core_rescued == s2.core_rescued
    assert s1.core_regression == s2.core_regression
    assert s1.spec_changed == s2.spec_changed
    assert s1.spec_rescued == s2.spec_rescued
    assert s1.spec_regression == s2.spec_regression
    assert s1.syntax_pass_count == s2.syntax_pass_count
    assert s1.execution_success_count == s2.execution_success_count
    assert s1.test_pass_count == s2.test_pass_count


# ---------------------------------------------------------------------------
# No model or network access
# ---------------------------------------------------------------------------


def test_no_ai_client_imports():
    """pilot_runner.py must not import any AI client library."""
    import importlib
    import inspect

    import agent_tools.finals_rebuild.pilot_runner as pr_mod

    source = inspect.getsource(pr_mod)
    forbidden = [
        "google.generativeai",
        "openai",
        "anthropic",
        "call_ai_with_retry",
        "requests",
    ]
    for lib in forbidden:
        assert lib not in source, f"pilot_runner.py must not reference {lib!r}"
