"""
Fixture test-case evaluator — Commit 4C (revised: per-case subprocess
isolation, see the "case isolation" fix below).

Runs a TestSuite (see test_contract.py) against one treatment's artifact
code by spawning ONE FRESH SUBPROCESS PER TEST CASE — never a single
shared subprocess for the whole suite. The worker (test_worker.py) loads
the artifact fresh in each subprocess, then calls ONLY the top-level
function named by that ONE TestCase — never arbitrary code, never eval()
of an assertion expression.

*** NOT A SECURITY SANDBOX *** — same caveat as execution_evaluator.py;
this reuses that module's preflight denylist and minimal-subprocess-env
helpers rather than duplicating them.

Only ever called by the pipeline when execution already succeeded
(syntax_pass and execution_status=="success"); the preflight denylist
check here is still applied independently as defense-in-depth for any
direct caller that bypasses that gate.

Case isolation (fix)
---------------------
The original Commit 4C implementation ran all cases inside ONE
subprocess, each bounded by a daemon thread with thread.join(timeout).
That is not a real timeout boundary: a thread that "times out" keeps
running — burning CPU and free to mutate module-level state the artifact
defines — and the NEXT case, sharing that same process, could silently
observe whatever the hung case left behind.

Now every case gets its OWN subprocess (see _run_one_case_subprocess()).
A case's timeout is enforced by subprocess.Popen.communicate(timeout=...)
+ proc.kill() on TimeoutExpired — this terminates the ENTIRE process, not
just a Python-level construct within it, so nothing survives to leak into
another case. Every case also gets a completely fresh artifact exec (each
subprocess only ever handles one case), which independently rules out
global-state contamination between cases even before considering timeout
at all.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent_tools.finals_rebuild.execution_evaluator import (
    _minimal_subprocess_env,
    _truncate,
    preflight_denylist_violation,
)
from agent_tools.finals_rebuild.test_contract import (
    TestCase,
    TestSuite,
    compute_test_suite_hash,
    test_case_to_dict,
    validate_test_suite,
)

_WORKER_PATH = Path(__file__).with_name("test_worker.py")

_CASE_STATUSES: frozenset[str] = frozenset({"passed", "failed", "error", "timeout"})

_MAX_CASE_MESSAGE_CHARS = 500


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


@dataclass(frozen=True)
class _CaseSubprocessResult:
    """Internal — carries diagnostic info (pid, confirmed termination)
    alongside the outcome, so tests can independently verify a timed-out
    case's process was actually killed. Never exposed through the public
    TestSuiteOutcome/test_results.json schema."""

    outcome: TestCaseOutcome
    pid: Optional[int]
    terminated: bool  # True once proc.poll() confirms the process has exited


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


def _run_one_case_subprocess(
    *,
    code: str,
    case: TestCase,
    tolerance: float,
    timeout: float,
) -> _CaseSubprocessResult:
    """
    Spawn a FRESH subprocess for exactly this one case. Never imports/
    execs/compiles *code* in THIS (calling) process — only the disposable
    child process (test_worker.py) ever does that, and it only ever
    handles this single case before exiting.
    """
    with tempfile.TemporaryDirectory(prefix="finals_rebuild_test_case_") as tmp_dir:
        artifact_path = Path(tmp_dir) / "artifact.py"
        artifact_path.write_text(code, encoding="utf-8")
        case_path = Path(tmp_dir) / "case.json"
        case_path.write_text(
            json.dumps({
                "case": test_case_to_dict(case),
                "numeric_tolerance": tolerance,
            }),
            encoding="utf-8",
        )
        output_path = Path(tmp_dir) / "result.json"

        proc = subprocess.Popen(
            [
                sys.executable, "-I", str(_WORKER_PATH),
                str(artifact_path), str(case_path), str(output_path),
            ],
            cwd=tmp_dir,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=_minimal_subprocess_env(),
            text=True,
        )
        pid = proc.pid
        start = time.monotonic()

        try:
            proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            # Kill the ENTIRE process — this is what actually stops
            # whatever the case was doing (CPU work, global mutation),
            # unlike a thread timing out while continuing to run.
            proc.kill()
            proc.communicate()
            duration_ms = (time.monotonic() - start) * 1000.0
            terminated = proc.poll() is not None
            return _CaseSubprocessResult(
                outcome=TestCaseOutcome(
                    case_id=case.case_id,
                    status="timeout",
                    passed=False,
                    exception_type="TimeoutExpired",
                    exception_message=_truncate(
                        f"case exceeded {timeout}s timeout (pid={pid})",
                        _MAX_CASE_MESSAGE_CHARS,
                    ),
                    duration_ms=duration_ms,
                ),
                pid=pid,
                terminated=terminated,
            )
        except Exception as exc:  # fail-closed: infra failure must never crash the pipeline
            try:
                proc.kill()
                proc.communicate()
            except Exception:
                pass
            return _CaseSubprocessResult(
                outcome=TestCaseOutcome(
                    case_id=case.case_id,
                    status="error",
                    passed=False,
                    exception_type=type(exc).__name__,
                    exception_message=_truncate(str(exc), _MAX_CASE_MESSAGE_CHARS),
                    duration_ms=0.0,
                ),
                pid=pid,
                terminated=proc.poll() is not None,
            )

        terminated = proc.poll() is not None  # communicate() already returned -> exited

        try:
            raw = json.loads(output_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return _CaseSubprocessResult(
                outcome=TestCaseOutcome(
                    case_id=case.case_id,
                    status="error",
                    passed=False,
                    exception_type=type(exc).__name__,
                    exception_message=_truncate(
                        f"failed to read worker output: {exc}", _MAX_CASE_MESSAGE_CHARS
                    ),
                    duration_ms=0.0,
                ),
                pid=pid,
                terminated=terminated,
            )

        status = raw.get("status")
        if status not in _CASE_STATUSES:
            return _CaseSubprocessResult(
                outcome=TestCaseOutcome(
                    case_id=case.case_id,
                    status="error",
                    passed=False,
                    exception_type="InvalidWorkerStatus",
                    exception_message=f"worker reported unrecognised status {status!r}",
                    duration_ms=0.0,
                ),
                pid=pid,
                terminated=terminated,
            )

        return _CaseSubprocessResult(
            outcome=TestCaseOutcome(
                case_id=raw.get("case_id", case.case_id),
                status=status,
                passed=bool(raw.get("passed", False)),
                exception_type=raw.get("exception_type"),
                exception_message=raw.get("exception_message"),
                duration_ms=float(raw.get("duration_ms", 0.0)),
            ),
            pid=pid,
            terminated=terminated,
        )


def run_test_suite(*, code: str, suite: TestSuite) -> TestSuiteOutcome:
    """
    Run every case in *suite* against *code*, each in its own subprocess.

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

    case_outcomes: List[TestCaseOutcome] = []
    for case in suite.cases:
        result = _run_one_case_subprocess(
            code=code,
            case=case,
            tolerance=suite.numeric_tolerance,
            timeout=suite.timeout_seconds,
        )
        case_outcomes.append(result.outcome)

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
