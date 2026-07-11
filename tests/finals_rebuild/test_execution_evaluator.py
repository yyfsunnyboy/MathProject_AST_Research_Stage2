"""
Tests for agent_tools/finals_rebuild/execution_evaluator.py
"""

from __future__ import annotations

import inspect
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from agent_tools.finals_rebuild.evaluation import validate_evaluation_result
from agent_tools.finals_rebuild.execution_evaluator import (
    ISOLATION_LEVEL,
    MAX_STDERR_CHARS,
    MAX_STDOUT_CHARS,
    evaluate_with_execution,
    preflight_denylist_violation,
    run_bounded_execution,
)

_PAIR_ID = "a" * 64
_RUN_ID = "b" * 64
_HASH = "c" * 64


# ---------------------------------------------------------------------------
# 1. Normal program → success
# ---------------------------------------------------------------------------


def test_1_normal_program_success():
    outcome = run_bounded_execution(code="def generate():\n    return 1\n")
    assert outcome.execution_status == "success"
    assert outcome.execution_success is True
    assert outcome.return_code == 0
    assert outcome.isolation_level == ISOLATION_LEVEL


# ---------------------------------------------------------------------------
# 2. Raises exception → failure
# ---------------------------------------------------------------------------


def test_2_top_level_exception_failure():
    outcome = run_bounded_execution(code="raise ValueError('boom')\n")
    assert outcome.execution_status == "failure"
    assert outcome.execution_success is False
    assert outcome.return_code != 0
    assert "ValueError" in outcome.stderr_summary


# ---------------------------------------------------------------------------
# 3. Infinite loop → timeout
# ---------------------------------------------------------------------------


def test_3_infinite_loop_timeout():
    outcome = run_bounded_execution(
        code="while True:\n    pass\n", timeout=1.0
    )
    assert outcome.execution_status == "timeout"
    assert outcome.execution_success is False
    assert outcome.exception_type == "TimeoutExpired"
    assert outcome.timeout == 1.0


# ---------------------------------------------------------------------------
# 4. subprocess/socket/eval → blocked
# ---------------------------------------------------------------------------


def test_4a_subprocess_import_blocked():
    outcome = run_bounded_execution(code="import subprocess\n")
    assert outcome.execution_status == "blocked"
    assert outcome.execution_success is False
    assert outcome.return_code is None  # subprocess never spawned


def test_4b_socket_import_blocked():
    outcome = run_bounded_execution(code="import socket\n")
    assert outcome.execution_status == "blocked"


def test_4c_eval_call_blocked():
    outcome = run_bounded_execution(code="eval('1+1')\n")
    assert outcome.execution_status == "blocked"


def test_4d_requests_urllib_http_ctypes_multiprocessing_blocked():
    for code in (
        "import requests\n",
        "import urllib\n",
        "import http.client\n",
        "import ctypes\n",
        "import multiprocessing\n",
        "os.system('echo hi')\n",
        "os.popen('echo hi')\n",
        "exec('1')\n",
        "compile('1', '<s>', 'eval')\n",
        "__import__('os')\n",
    ):
        outcome = run_bounded_execution(code=f"import os\n{code}" if "os." in code else code)
        assert outcome.execution_status == "blocked", f"expected blocked for: {code!r}"


def test_denylist_violation_never_spawns_subprocess():
    violation = preflight_denylist_violation("import socket\n")
    assert violation is not None
    assert "socket" in violation


def test_no_violation_for_safe_code():
    assert preflight_denylist_violation("def f():\n    return 1\n") is None


def test_no_violation_reported_for_syntax_errors():
    """A SyntaxError is not a denylist violation — it's reported
    separately (as execution_status='failure' once actually run)."""
    assert preflight_denylist_violation("def f(:\n") is None


# ---------------------------------------------------------------------------
# 5. Never executed in the main process
# ---------------------------------------------------------------------------


def test_5_main_process_never_execs_artifact(tmp_path):
    """
    Prove the artifact code runs in a genuinely different OS process, not
    inside the (calling) test/pipeline process: have the artifact print
    its own os.getpid() and compare against this process's pid. A real
    subprocess is not a sandbox (it has ordinary filesystem access, as
    demonstrated separately) — the distinguishing fact this test checks
    is *which process* the code executed in.
    """
    sentinel = tmp_path / "pid.txt"
    code = (
        f"import os, pathlib\n"
        f"pathlib.Path(r'{sentinel}').write_text(str(os.getpid()))\n"
    )
    outcome = run_bounded_execution(code=code)
    assert outcome.execution_status == "success"
    assert sentinel.exists()
    child_pid = int(sentinel.read_text().strip())
    assert child_pid != os.getpid()


def test_no_exec_eval_compile_calls_in_execution_evaluator_source():
    import ast as _ast
    import agent_tools.finals_rebuild.execution_evaluator as mod

    source = inspect.getsource(mod)
    tree = _ast.parse(source)
    forbidden_calls = {"exec", "eval", "compile", "__import__"}
    for node in _ast.walk(tree):
        if isinstance(node, _ast.Call) and isinstance(node.func, _ast.Name):
            assert node.func.id not in forbidden_calls, (
                f"execution_evaluator.py must not call {node.func.id}()"
            )


# ---------------------------------------------------------------------------
# 6. stdout/stderr length limits
# ---------------------------------------------------------------------------


def test_6_stdout_is_truncated():
    code = "print('x' * 10000)\n"
    outcome = run_bounded_execution(code=code)
    assert outcome.execution_status == "success"
    assert len(outcome.stdout_summary) <= MAX_STDOUT_CHARS + len("…(truncated)")


def test_6_stderr_is_truncated():
    code = "import sys\nsys.stderr.write('e' * 10000)\n"
    outcome = run_bounded_execution(code=code)
    assert len(outcome.stderr_summary) <= MAX_STDERR_CHARS + len("…(truncated)")


# ---------------------------------------------------------------------------
# 7/8. Independent per-treatment results; one failure doesn't block others
# ---------------------------------------------------------------------------


def test_7_and_8_independent_results_one_failure_does_not_block_others():
    codes = {
        "ab1": "def generate():\n    return 1\n",           # success
        "ab2": "raise ValueError('boom')\n",                  # failure
        "ab3_core": "while True:\n    pass\n",                # timeout
        "ab3_full": "import socket\n",                        # blocked
    }
    results = {}
    for treatment, code in codes.items():
        results[treatment] = evaluate_with_execution(
            code=code,
            pair_id=_PAIR_ID,
            run_id=_RUN_ID,
            treatment=treatment,
            artifact_hash=_HASH,
            evaluator_git_commit="deadbeef",
            timeout=1.0,
        )

    assert results["ab1"].execution_status == "success"
    assert results["ab2"].execution_status == "failure"
    assert results["ab3_core"].execution_status == "timeout"
    assert results["ab3_full"].execution_status == "blocked"

    # Each is independently valid — a failure in one never corrupted another.
    import dataclasses
    for treatment, result in results.items():
        finalized = dataclasses.replace(
            result, created_at_utc="2026-07-11T09:00:00+00:00"
        )
        validate_evaluation_result(finalized)


# ---------------------------------------------------------------------------
# not-a-sandbox transparency
# ---------------------------------------------------------------------------


def test_isolation_level_constant_matches_schema_allowlist():
    from agent_tools.finals_rebuild.evaluation import ALLOWED_ISOLATION_LEVELS
    assert ISOLATION_LEVEL in ALLOWED_ISOLATION_LEVELS
    assert ISOLATION_LEVEL == "guarded_subprocess_not_security_sandbox"


def test_module_docstring_disclaims_security_sandbox():
    import agent_tools.finals_rebuild.execution_evaluator as mod
    doc = mod.__doc__ or ""
    assert "NOT A SECURITY SANDBOX" in doc


# ---------------------------------------------------------------------------
# evaluate_with_execution merges static + execution correctly
# ---------------------------------------------------------------------------


def test_merge_preserves_static_syntax_pass_on_success():
    result = evaluate_with_execution(
        code="def generate():\n    return 1\n",
        pair_id=_PAIR_ID,
        run_id=_RUN_ID,
        treatment="ab1",
        artifact_hash=_HASH,
        evaluator_git_commit="deadbeef",
    )
    assert result.syntax_pass is True
    assert result.execution_status == "success"


def test_merge_blocked_does_not_report_syntax_failure():
    result = evaluate_with_execution(
        code="import socket\n",
        pair_id=_PAIR_ID,
        run_id=_RUN_ID,
        treatment="ab1",
        artifact_hash=_HASH,
        evaluator_git_commit="deadbeef",
    )
    assert result.syntax_pass is True  # it DOES parse; it's just denylisted
    assert result.execution_status == "blocked"
    assert result.exception_type == "PreflightDenylistViolation"


def test_evaluate_with_execution_never_raises_on_bad_code():
    """Fail-closed: even wildly broken input must return a valid result,
    never propagate an exception up to the caller."""
    for code in ("", "def f(:\n", "🔥" * 50, "while True: pass"):
        result = evaluate_with_execution(
            code=code,
            pair_id=_PAIR_ID,
            run_id=_RUN_ID,
            treatment="ab1",
            artifact_hash=_HASH,
            evaluator_git_commit="deadbeef",
            timeout=1.0,
        )
        assert result is not None


# ---------------------------------------------------------------------------
# Fix 2: syntax failure skips run_bounded_execution entirely
# ---------------------------------------------------------------------------


def test_5_syntax_error_never_calls_subprocess_run(monkeypatch):
    calls = []
    import subprocess as _subprocess

    original_run = _subprocess.run

    def spy_run(*args, **kwargs):
        calls.append((args, kwargs))
        return original_run(*args, **kwargs)

    monkeypatch.setattr(_subprocess, "run", spy_run)

    result = evaluate_with_execution(
        code="def f(:\n",
        pair_id=_PAIR_ID,
        run_id=_RUN_ID,
        treatment="ab1",
        artifact_hash=_HASH,
        evaluator_git_commit="deadbeef",
    )
    assert result.syntax_pass is False
    assert calls == [], "subprocess.run must never be called for syntax-invalid code"


def test_6_syntax_error_execution_status_and_success():
    result = evaluate_with_execution(
        code="def f(:\n",
        pair_id=_PAIR_ID,
        run_id=_RUN_ID,
        treatment="ab1",
        artifact_hash=_HASH,
        evaluator_git_commit="deadbeef",
    )
    assert result.execution_status == "failure"
    assert result.execution_success is False
    assert result.return_code is None
    assert result.duration_ms == 0.0
    assert result.isolation_level == ISOLATION_LEVEL
    assert result.fail_closed is True
    # exception_type/message preserved from the static SyntaxError, not
    # overwritten by the (never-run) execution layer.
    assert result.exception_type == "SyntaxError"
    assert result.exception_message is not None


def test_syntax_error_result_validates(tmp_path=None):
    import dataclasses
    result = evaluate_with_execution(
        code="def f(:\n",
        pair_id=_PAIR_ID,
        run_id=_RUN_ID,
        treatment="ab1",
        artifact_hash=_HASH,
        evaluator_git_commit="deadbeef",
    )
    finalized = dataclasses.replace(
        result, created_at_utc="2026-07-11T09:00:00+00:00"
    )
    validate_evaluation_result(finalized)


def test_run_bounded_execution_not_called_for_syntax_error(monkeypatch):
    """Direct check on the orchestrator: run_bounded_execution itself
    must never be invoked when static evaluation already failed to
    parse."""
    import agent_tools.finals_rebuild.execution_evaluator as mod

    calls = []
    monkeypatch.setattr(
        mod, "run_bounded_execution", lambda **kw: calls.append(kw) or None
    )
    mod.evaluate_with_execution(
        code="def f(:\n",
        pair_id=_PAIR_ID,
        run_id=_RUN_ID,
        treatment="ab1",
        artifact_hash=_HASH,
        evaluator_git_commit="deadbeef",
    )
    assert calls == []
