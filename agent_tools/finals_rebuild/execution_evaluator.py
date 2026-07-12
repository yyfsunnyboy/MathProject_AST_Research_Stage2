"""
Bounded subprocess execution evaluator — Commit 4B.

*** THIS IS NOT A SECURITY SANDBOX ***

This module runs each artifact in its own subprocess with:
  - the current interpreter in isolated mode (`sys.executable -I`), which
    ignores the user site-packages dir and PYTHON* environment variables;
  - a fresh, disposable temp directory as the working directory;
  - stdin closed (subprocess.DEVNULL);
  - a stripped environment (only PATH/SystemRoot survive, the minimum
    needed for the interpreter itself to start on Windows);
  - stdout/stderr captured and truncated to a bounded length;
  - a wall-clock timeout that kills the subprocess if exceeded.

None of that constitutes a security boundary against a determined
malicious payload: the child process still has full OS-user-level
filesystem/network access for the duration it runs, an AST-only denylist
(see preflight_denylist_violation()) can be bypassed by obfuscation
(string-built imports, `getattr(__builtins__, ...)`, etc.), and there is
no seccomp/container/VM isolation of any kind. Every EvaluationResult this
module produces once execution_status != "not_run" carries
isolation_level="guarded_subprocess_not_security_sandbox" so that
limitation is machine-checkable, not just a comment — see
evaluation.ALLOWED_ISOLATION_LEVELS.

Do not use this module to execute code you do not already trust roughly
as much as you trust the current git worktree.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Optional, Sequence

from agent_tools.finals_rebuild.evaluation import EvaluationResult
from agent_tools.finals_rebuild.static_evaluator import evaluate_static

ISOLATION_LEVEL = "guarded_subprocess_not_security_sandbox"

DEFAULT_TIMEOUT_SECONDS = 3.0
MAX_STDOUT_CHARS = 2000
MAX_STDERR_CHARS = 2000

_WORKER_PATH = Path(__file__).with_name("execution_worker.py")

# ---------------------------------------------------------------------------
# Preflight denylist — AST-only, fail-closed, never a substitute for real
# sandboxing. Rejects the most obviously dangerous imports/calls BEFORE any
# subprocess is spawned.
# ---------------------------------------------------------------------------

_DENYLIST_MODULE_ROOTS: frozenset[str] = frozenset({
    "subprocess", "socket", "requests", "urllib", "http", "ctypes",
    "multiprocessing",
})
_DENYLIST_ATTR_CALLS: frozenset[tuple[str, str]] = frozenset({
    ("os", "system"),
    ("os", "popen"),
})
_DENYLIST_BUILTIN_CALLS: frozenset[str] = frozenset({
    "eval", "exec", "compile", "__import__",
})


def preflight_denylist_violation(code: str) -> Optional[str]:
    """
    Return a short human-readable description of the first denylist hit
    in *code*, or None if none is found (including if *code* itself does
    not even parse — a SyntaxError is not a denylist violation; it is
    reported separately by evaluate_static()/the worker's own failure).

    AST-only: parses *code* but never imports, execs, or compiles it for
    execution.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in _DENYLIST_MODULE_ROOTS:
                    return f"import of denylisted module {alias.name!r}"
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root = node.module.split(".")[0]
                if root in _DENYLIST_MODULE_ROOTS:
                    return f"from-import of denylisted module {node.module!r}"
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in _DENYLIST_BUILTIN_CALLS:
                return f"call to denylisted builtin {func.id}()"
            if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                if (func.value.id, func.attr) in _DENYLIST_ATTR_CALLS:
                    return f"call to denylisted {func.value.id}.{func.attr}()"
    return None


# ---------------------------------------------------------------------------
# Bounded subprocess launcher
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ExecutionOutcome:
    """Execution-only fields; merged into an EvaluationResult by
    evaluate_with_execution()."""

    execution_status: str
    execution_success: bool
    isolation_level: str
    stdout_summary: str
    stderr_summary: str
    return_code: Optional[int]
    duration_ms: float
    timeout: float
    exception_type: Optional[str]
    exception_message: Optional[str]


def _truncate(text: str, limit: int) -> str:
    if text is None:
        return ""
    if len(text) > limit:
        return text[:limit] + "…(truncated)"
    return text


def _minimal_subprocess_env() -> dict:
    """Only what the interpreter itself needs to start; nothing the
    artifact code could use as an ambient side-channel beyond that."""
    env = {}
    for key in ("PATH", "SYSTEMROOT", "SystemRoot"):
        value = os.environ.get(key)
        if value:
            env[key] = value
    return env


def run_bounded_execution(
    *,
    code: str,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> ExecutionOutcome:
    """
    Execute *code* in a bounded subprocess (see module docstring for what
    "bounded" does and does not mean). NEVER imports/execs/compiles *code*
    in THIS (calling) process — only the disposable child process
    (execution_worker.py) ever does that.
    """
    violation = preflight_denylist_violation(code)
    if violation is not None:
        return ExecutionOutcome(
            execution_status="blocked",
            execution_success=False,
            isolation_level=ISOLATION_LEVEL,
            stdout_summary="",
            stderr_summary=_truncate(f"preflight denylist: {violation}", MAX_STDERR_CHARS),
            return_code=None,
            duration_ms=0.0,
            timeout=timeout,
            exception_type="PreflightDenylistViolation",
            exception_message=violation,
        )

    with tempfile.TemporaryDirectory(prefix="finals_rebuild_exec_") as tmp_dir:
        artifact_path = Path(tmp_dir) / "artifact.py"
        artifact_path.write_text(code, encoding="utf-8")

        start = time.monotonic()
        try:
            proc = subprocess.run(
                [sys.executable, "-I", str(_WORKER_PATH), str(artifact_path)],
                cwd=tmp_dir,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=_minimal_subprocess_env(),
                timeout=timeout,
                text=True,
            )
            duration_ms = (time.monotonic() - start) * 1000.0
            status = "success" if proc.returncode == 0 else "failure"
            return ExecutionOutcome(
                execution_status=status,
                execution_success=(status == "success"),
                isolation_level=ISOLATION_LEVEL,
                stdout_summary=_truncate(proc.stdout, MAX_STDOUT_CHARS),
                stderr_summary=_truncate(proc.stderr, MAX_STDERR_CHARS),
                return_code=proc.returncode,
                duration_ms=duration_ms,
                timeout=timeout,
                exception_type=None,
                exception_message=None,
            )
        except subprocess.TimeoutExpired as exc:
            # subprocess.run() already killed the child before re-raising.
            duration_ms = (time.monotonic() - start) * 1000.0
            out = exc.stdout if isinstance(exc.stdout, str) else ""
            err = exc.stderr if isinstance(exc.stderr, str) else ""
            return ExecutionOutcome(
                execution_status="timeout",
                execution_success=False,
                isolation_level=ISOLATION_LEVEL,
                stdout_summary=_truncate(out, MAX_STDOUT_CHARS),
                stderr_summary=_truncate(err, MAX_STDERR_CHARS),
                return_code=None,
                duration_ms=duration_ms,
                timeout=timeout,
                exception_type="TimeoutExpired",
                exception_message=f"execution exceeded {timeout}s timeout",
            )
        except Exception as exc:  # fail-closed: the evaluator must never crash the pipeline
            duration_ms = (time.monotonic() - start) * 1000.0
            return ExecutionOutcome(
                execution_status="error",
                execution_success=False,
                isolation_level=ISOLATION_LEVEL,
                stdout_summary="",
                stderr_summary=_truncate(str(exc), MAX_STDERR_CHARS),
                return_code=None,
                duration_ms=duration_ms,
                timeout=timeout,
                exception_type=type(exc).__name__,
                exception_message=_truncate(str(exc), 300),
            )


# ---------------------------------------------------------------------------
# Combined static + execution evaluation
# ---------------------------------------------------------------------------


def evaluate_with_execution(
    *,
    code: str,
    pair_id: str,
    run_id: str,
    treatment: str,
    artifact_hash: str,
    evaluator_git_commit: str,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    required_functions: Optional[Sequence[str]] = None,
) -> EvaluationResult:
    """
    Static evaluation (evaluate_static — syntax/contract, see
    static_evaluator.py) plus bounded-subprocess execution, merged into a
    single EvaluationResult.

    One treatment's execution failing (or timing out, or being denylist-
    blocked) never raises — the caller always gets back a fully-formed,
    fail-closed EvaluationResult, so evaluating four treatments in a loop
    means one bad treatment can never prevent the other three from being
    evaluated.

    Code that fails to parse (static_result.syntax_pass is False) is
    reported as execution_status="failure" WITHOUT ever spawning a
    subprocess — a syntax error can only ever fail to compile, so
    launching a process to observe that is pure overhead. This is
    distinct from a genuine runtime test failure: it just means the code
    could not be executed at all.
    """
    static_result = evaluate_static(
        code=code,
        pair_id=pair_id,
        run_id=run_id,
        treatment=treatment,
        artifact_hash=artifact_hash,
        evaluator_git_commit=evaluator_git_commit,
        required_functions=required_functions,
    )

    if not static_result.syntax_pass:
        return replace(
            static_result,
            execution_status="failure",
            execution_success=False,
            isolation_level=ISOLATION_LEVEL,
            stdout_summary="",
            stderr_summary="",
            return_code=None,
            duration_ms=0.0,
            timeout=timeout,
            fail_closed=True,
            # exception_type/exception_message intentionally left
            # untouched here — static_result already carries the
            # SyntaxError info from evaluate_static(), which remains the
            # accurate explanation for why execution could not happen.
        )

    outcome = run_bounded_execution(code=code, timeout=timeout)

    merge_kwargs = dict(
        execution_status=outcome.execution_status,
        execution_success=outcome.execution_success,
        isolation_level=outcome.isolation_level,
        stdout_summary=outcome.stdout_summary,
        stderr_summary=outcome.stderr_summary,
        return_code=outcome.return_code,
        duration_ms=outcome.duration_ms,
        timeout=outcome.timeout,
    )
    # Only overwrite exception_type/exception_message when the execution
    # layer itself has something to report (blocked/timeout/error). For
    # plain success/failure, preserve whatever evaluate_static() already
    # recorded (e.g. a SyntaxError that naturally also fails at exec time).
    if outcome.exception_type is not None:
        merge_kwargs["exception_type"] = outcome.exception_type
        merge_kwargs["exception_message"] = outcome.exception_message

    return replace(static_result, **merge_kwargs)
