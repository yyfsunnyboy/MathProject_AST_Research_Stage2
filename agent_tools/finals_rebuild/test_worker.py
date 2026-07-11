"""
Test-case worker — Commit 4C.

This script is NEVER imported by the main pipeline process. It is only
ever invoked as a standalone subprocess:

    sys.executable -I test_worker.py <artifact_path> <suite_path> <output_path>

by agent_tools/finals_rebuild/test_evaluator.py, which runs it inside a
fresh temp directory with a stripped environment, closed stdin, and an
outer wall-clock timeout — the same "bounded subprocess" principle as
execution_worker.py (Commit 4B).

Behaviour
---------
1. Load the artifact ONCE (exec'd here, in this disposable child process
   — never in the pipeline's own process).
2. For each fixture-described case, call ONLY the named top-level
   function with its JSON-decoded args/kwargs. No eval() of assertion
   expressions, no arbitrary code execution beyond that single call —
   the fixture data (see test_contract.py) is restricted to JSON-
   compatible values, never code or a callable.
3. Each case runs in its own daemon thread with an individual timeout
   (thread.join(timeout)) so one hung/slow case can never block the
   remaining cases from running, and so the worker process itself can
   still exit promptly once every case's timeout budget has elapsed —
   daemon=True means an unfinished thread never keeps the process alive.
   This is a best-effort bound, NOT true preemptive isolation (Python
   cannot forcibly kill a running native thread) — consistent with the
   rest of this evaluator's "bounded subprocess, not a security sandbox"
   positioning (see execution_evaluator.py's module docstring).
4. Write a JSON array of per-case outcomes to <output_path> and exit 0.
   A case failing/erroring/timing out is recorded, never raised — one
   bad case must never prevent the rest from running or being recorded.

*** NOT A SECURITY SANDBOX ***
"""

from __future__ import annotations

import json
import queue
import sys
import threading
import time
from typing import Any, Dict, List


def _load_artifact(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        source = fh.read()
    code_obj = compile(source, path, "exec")
    namespace: Dict[str, Any] = {"__name__": "test_worker_artifact", "__file__": path}
    exec(code_obj, namespace)  # the ONE place artifact code executes
    return namespace


def _compare(actual: Any, expected: Any, mode: str, tolerance: float) -> bool:
    if mode == "exact":
        return actual == expected
    if mode == "numeric_tolerance":
        try:
            return abs(float(actual) - float(expected)) <= tolerance
        except (TypeError, ValueError):
            return False
    if mode == "json_equal":
        try:
            return json.dumps(actual, sort_keys=True) == json.dumps(expected, sort_keys=True)
        except TypeError:
            return False
    return False


def _call_with_timeout(fn, args, kwargs, timeout_seconds):
    """Run fn(*args, **kwargs) in a daemon thread bounded by timeout_seconds.

    Returns (status, value_or_exception):
      ("ok", return_value)
      ("error", exception_instance)
      ("timeout", None)
    """
    result_q: "queue.Queue" = queue.Queue(maxsize=1)

    def _runner():
        try:
            result_q.put(("ok", fn(*args, **kwargs)))
        except Exception as exc:  # noqa: BLE001 — must capture anything the case raises
            result_q.put(("error", exc))

    thread = threading.Thread(target=_runner, daemon=True)
    thread.start()
    thread.join(timeout_seconds)
    if thread.is_alive():
        return ("timeout", None)
    try:
        return result_q.get_nowait()
    except queue.Empty:
        return ("error", RuntimeError("worker thread finished without a result"))


def _run_case(namespace: Dict[str, Any], case: Dict[str, Any], suite_timeout: float, tolerance: float) -> Dict[str, Any]:
    case_id = case["case_id"]
    function_name = case["function_name"]
    args = case.get("args", [])
    kwargs = case.get("kwargs", {})
    expected = case.get("expected")
    comparison_mode = case.get("comparison_mode", "exact")

    start = time.monotonic()
    fn = namespace.get(function_name)
    if fn is None or not callable(fn):
        return {
            "case_id": case_id,
            "status": "error",
            "passed": False,
            "exception_type": "FunctionNotFound",
            "exception_message": f"top-level function {function_name!r} not found in artifact",
            "duration_ms": 0.0,
        }

    status, payload = _call_with_timeout(fn, args, kwargs, suite_timeout)
    duration_ms = (time.monotonic() - start) * 1000.0

    if status == "timeout":
        return {
            "case_id": case_id,
            "status": "timeout",
            "passed": False,
            "exception_type": "TimeoutError",
            "exception_message": f"case exceeded {suite_timeout}s timeout",
            "duration_ms": duration_ms,
        }
    if status == "error":
        exc = payload
        return {
            "case_id": case_id,
            "status": "error",
            "passed": False,
            "exception_type": type(exc).__name__,
            "exception_message": str(exc)[:300],
            "duration_ms": duration_ms,
        }

    actual = payload
    try:
        passed = _compare(actual, expected, comparison_mode, tolerance)
    except Exception as exc:  # noqa: BLE001 — comparison itself must never crash the worker
        return {
            "case_id": case_id,
            "status": "error",
            "passed": False,
            "exception_type": type(exc).__name__,
            "exception_message": str(exc)[:300],
            "duration_ms": duration_ms,
        }
    return {
        "case_id": case_id,
        "status": "passed" if passed else "failed",
        "passed": passed,
        "exception_type": None,
        "exception_message": None,
        "duration_ms": duration_ms,
    }


def main() -> int:
    if len(sys.argv) != 4:
        print(
            "test_worker: expected artifact_path, suite_path, output_path",
            file=sys.stderr,
        )
        return 2

    artifact_path, suite_path, output_path = sys.argv[1], sys.argv[2], sys.argv[3]

    with open(suite_path, "r", encoding="utf-8") as fh:
        suite = json.load(fh)

    cases: List[Dict[str, Any]] = suite.get("cases", [])
    timeout_seconds = suite.get("timeout_seconds", 3.0)
    tolerance = suite.get("numeric_tolerance", 1e-6)

    try:
        namespace = _load_artifact(artifact_path)
    except Exception as exc:
        # Artifact itself failed to load — every case is unrunnable, but
        # this worker still succeeds at reporting that fact.
        results = [
            {
                "case_id": c["case_id"],
                "status": "error",
                "passed": False,
                "exception_type": type(exc).__name__,
                "exception_message": str(exc)[:300],
                "duration_ms": 0.0,
            }
            for c in cases
        ]
        with open(output_path, "w", encoding="utf-8") as fh:
            json.dump(results, fh)
        return 0

    results = [
        _run_case(namespace, case, timeout_seconds, tolerance) for case in cases
    ]
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(results, fh)
    return 0


if __name__ == "__main__":
    sys.exit(main())
