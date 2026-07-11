"""
Fixture test-case evaluator — Commit 4C.

Runs a TestSuite (see test_contract.py) against one treatment's artifact
code inside ONE bounded subprocess per treatment: the worker
(test_worker.py) loads the artifact once, then calls ONLY the top-level
function named by each TestCase — never arbitrary code, never eval() of
an assertion expression.

*** NOT A SECURITY SANDBOX *** — same caveat as execution_evaluator.py;
this reuses that module's preflight denylist and minimal-subprocess-env
helpers rather than duplicating them.

Only ever called by the pipeline when execution already succeeded
(syntax_pass and execution_status=="success"); the preflight denylist
check here is still applied independently as defense-in-depth for any
direct caller that bypasses that gate.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent_tools.finals_rebuild.execution_evaluator import (
    _minimal_subprocess_env,
    preflight_denylist_violation,
)
from agent_tools.finals_rebuild.test_contract import (
    TestSuite,
    compute_test_suite_hash,
    test_suite_to_dict,
    validate_test_suite,
)

_WORKER_PATH = Path(__file__).with_name("test_worker.py")

_CASE_STATUSES: frozenset[str] = frozenset({"passed", "failed", "error", "timeout"})


@dataclass(frozen=True)
class TestCaseOutcome:
    case_id: str
    status: str  # "passed" | "failed" | "error" | "timeout"
    passed: bool
    exception_type: Optional[str]
    exception_message: Optional[str]
    duration_ms: float


@dataclass(frozen=True)
class TestSuiteOutcome:
    suite_hash: str
    test_pass: bool
    tests_passed: int
    tests_total: int
    cases: List[TestCaseOutcome] = field(default_factory=list)


def _all_cases_as(suite: TestSuite, *, status: str, exception_type: str, exception_message: str) -> List[TestCaseOutcome]:
    return [
        TestCaseOutcome(
            case_id=c.case_id,
            status=status,
            passed=False,
            exception_type=exception_type,
            exception_message=exception_message,
            duration_ms=0.0,
        )
        for c in suite.cases
    ]


def run_test_suite(*, code: str, suite: TestSuite) -> TestSuiteOutcome:
    """
    Run every case in *suite* against *code*.

    One case failing/erroring/timing out never stops the rest from
    running — every case is always recorded, even when the whole worker
    infrastructure fails (denylist block, subprocess crash/timeout,
    unreadable output): in every one of those situations every case is
    reported as a fail-closed "error"/"timeout" outcome rather than the
    caller getting an exception or a partial result set.
    """
    validate_test_suite(suite)
    suite_hash = compute_test_suite_hash(suite)

    violation = preflight_denylist_violation(code)
    if violation is not None:
        cases = _all_cases_as(
            suite,
            status="error",
            exception_type="PreflightDenylistViolation",
            exception_message=violation,
        )
        return TestSuiteOutcome(
            suite_hash=suite_hash, test_pass=False,
            tests_passed=0, tests_total=len(suite.cases), cases=cases,
        )

    with tempfile.TemporaryDirectory(prefix="finals_rebuild_test_") as tmp_dir:
        artifact_path = Path(tmp_dir) / "artifact.py"
        artifact_path.write_text(code, encoding="utf-8")
        suite_path = Path(tmp_dir) / "suite.json"
        suite_path.write_text(
            json.dumps(test_suite_to_dict(suite)), encoding="utf-8"
        )
        output_path = Path(tmp_dir) / "results.json"

        # Each case gets its own timeout_seconds budget (enforced inside
        # the worker via a per-case daemon thread); this outer bound must
        # be generous enough to let every case reach its own limit even
        # in the worst case where all of them individually time out.
        outer_timeout = suite.timeout_seconds * max(1, len(suite.cases)) + 5.0

        try:
            subprocess.run(
                [
                    sys.executable, "-I", str(_WORKER_PATH),
                    str(artifact_path), str(suite_path), str(output_path),
                ],
                cwd=tmp_dir,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=_minimal_subprocess_env(),
                timeout=outer_timeout,
                text=True,
            )
        except subprocess.TimeoutExpired:
            cases = _all_cases_as(
                suite, status="timeout",
                exception_type="WorkerTimeoutExpired",
                exception_message=f"test worker exceeded outer timeout {outer_timeout}s",
            )
            return TestSuiteOutcome(
                suite_hash=suite_hash, test_pass=False,
                tests_passed=0, tests_total=len(suite.cases), cases=cases,
            )
        except Exception as exc:  # fail-closed: infra failure must never crash the pipeline
            cases = _all_cases_as(
                suite, status="error",
                exception_type=type(exc).__name__,
                exception_message=str(exc)[:300],
            )
            return TestSuiteOutcome(
                suite_hash=suite_hash, test_pass=False,
                tests_passed=0, tests_total=len(suite.cases), cases=cases,
            )

        try:
            raw_results = json.loads(output_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            cases = _all_cases_as(
                suite, status="error",
                exception_type=type(exc).__name__,
                exception_message=f"failed to read worker output: {exc}",
            )
            return TestSuiteOutcome(
                suite_hash=suite_hash, test_pass=False,
                tests_passed=0, tests_total=len(suite.cases), cases=cases,
            )

    results_by_id: Dict[str, Any] = {
        r["case_id"]: r for r in raw_results if isinstance(r, dict) and "case_id" in r
    }
    case_outcomes: List[TestCaseOutcome] = []
    for c in suite.cases:
        r = results_by_id.get(c.case_id)
        if r is None:
            case_outcomes.append(TestCaseOutcome(
                case_id=c.case_id, status="error", passed=False,
                exception_type="MissingResult",
                exception_message="worker did not report a result for this case",
                duration_ms=0.0,
            ))
            continue
        status = r.get("status")
        if status not in _CASE_STATUSES:
            case_outcomes.append(TestCaseOutcome(
                case_id=c.case_id, status="error", passed=False,
                exception_type="InvalidWorkerStatus",
                exception_message=f"worker reported unrecognised status {status!r}",
                duration_ms=0.0,
            ))
            continue
        case_outcomes.append(TestCaseOutcome(
            case_id=r["case_id"],
            status=status,
            passed=bool(r.get("passed", False)),
            exception_type=r.get("exception_type"),
            exception_message=r.get("exception_message"),
            duration_ms=float(r.get("duration_ms", 0.0)),
        ))

    tests_passed = sum(1 for c in case_outcomes if c.passed)
    tests_total = len(case_outcomes)
    return TestSuiteOutcome(
        suite_hash=suite_hash,
        test_pass=(tests_total > 0 and tests_passed == tests_total),
        tests_passed=tests_passed,
        tests_total=tests_total,
        cases=case_outcomes,
    )


def test_results_to_dict(
    outcome: TestSuiteOutcome,
    *,
    pair_id: str,
    run_id: str,
    artifact_hash: str,
) -> Dict[str, Any]:
    """Content for runs/<treatment>/test_results.json — bound to
    pair_id/run_id/artifact_hash/test_suite_hash as required."""
    return {
        "pair_id": pair_id,
        "run_id": run_id,
        "artifact_hash": artifact_hash,
        "test_suite_hash": outcome.suite_hash,
        "test_pass": outcome.test_pass,
        "tests_passed": outcome.tests_passed,
        "tests_total": outcome.tests_total,
        "cases": [
            {
                "case_id": c.case_id,
                "status": c.status,
                "passed": c.passed,
                "exception_type": c.exception_type,
                "exception_message": c.exception_message,
                "duration_ms": c.duration_ms,
            }
            for c in outcome.cases
        ],
    }
