"""
Test-case worker — Commit 4C (revised: per-case subprocess isolation).

This script is NEVER imported by the main pipeline process. It is only
ever invoked as a standalone subprocess, ONCE PER TEST CASE:

    sys.executable -I test_worker.py <artifact_path> <case_path> <output_path>

by agent_tools/finals_rebuild/test_evaluator.py, which spawns a fresh
process for EVERY case (never one process shared across a whole suite)
inside a fresh temp directory with a stripped environment, closed stdin,
and a per-case wall-clock timeout.

Why per-case subprocess instead of a per-case thread
------------------------------------------------------
A thread that "times out" (thread.join(timeout) returning while the
thread is still alive) does NOT stop the thread — it keeps running,
consuming CPU, and can still mutate any module-level state the artifact
defines, which the NEXT case (sharing that same process/namespace) would
then silently observe. That is real cross-case contamination, not just a
latency problem.

A fresh subprocess per case has no such next case to contaminate: the
whole process — its threads, its module globals, everything — is killed
by the parent (test_evaluator.py's subprocess.run(timeout=...), which
calls proc.kill() on timeout) the moment the case's budget is exceeded.
Nothing survives to leak into another case, because there IS no shared
process. Loading the artifact fresh every single case (this process only
ever handles ONE case) is what removes the possibility of one case's
mutation being observed by another in the first place.

Behaviour
---------
1. Load the artifact (exec'd here, in this disposable child process —
   never in the pipeline's own process, never shared with another case).
2. Call ONLY the named top-level function with its JSON-decoded args/
   kwargs. No eval() of assertion expressions, no arbitrary code
   execution beyond that single call — fixture data (test_contract.py)
   is restricted to JSON-compatible values, never code or a callable.
3. Compare the result via the case's comparison_mode.
4. Write ONE JSON result object to <output_path> and exit 0. Any
   exception (missing function, runtime error, comparison failure) is
   caught and recorded here, never left to propagate uncaught — but a
   genuine timeout is enforced from OUTSIDE this process (the parent
   kills it), not by anything in this script.

*** NOT A SECURITY SANDBOX ***
"""

from __future__ import annotations

import json
import sys
import time
from typing import Any, Dict


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


def _run_case(namespace: Dict[str, Any], case: Dict[str, Any], tolerance: float) -> Dict[str, Any]:
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

    try:
        actual = fn(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001 — must capture anything the case raises
        duration_ms = (time.monotonic() - start) * 1000.0
        return {
            "case_id": case_id,
            "status": "error",
            "passed": False,
            "exception_type": type(exc).__name__,
            "exception_message": str(exc)[:300],
            "duration_ms": duration_ms,
        }
    duration_ms = (time.monotonic() - start) * 1000.0

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
            "test_worker: expected artifact_path, case_path, output_path",
            file=sys.stderr,
        )
        return 2

    artifact_path, case_path, output_path = sys.argv[1], sys.argv[2], sys.argv[3]

    with open(case_path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    case: Dict[str, Any] = payload["case"]
    tolerance = payload.get("numeric_tolerance", 1e-6)

    try:
        namespace = _load_artifact(artifact_path)
    except Exception as exc:
        # Artifact itself failed to load — this one case is unrunnable,
        # but this worker still succeeds at reporting that fact.
        result = {
            "case_id": case["case_id"],
            "status": "error",
            "passed": False,
            "exception_type": type(exc).__name__,
            "exception_message": str(exc)[:300],
            "duration_ms": 0.0,
        }
        with open(output_path, "w", encoding="utf-8") as fh:
            json.dump(result, fh)
        return 0

    result = _run_case(namespace, case, tolerance)
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh)
    return 0


if __name__ == "__main__":
    sys.exit(main())
