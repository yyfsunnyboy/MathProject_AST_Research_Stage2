"""
Static evaluator — Commit 4A.

Scope
-----
Produces an EvaluationResult (see evaluation.py) from treatment artifact
code using ONLY static analysis:

  - ast.parse() to determine syntax_pass.
  - A walk over the resulting module body's top-level FunctionDef /
    AsyncFunctionDef nodes to determine discovered_functions.
  - A simple subset check against required_functions to determine
    contract_status.

This module NEVER imports, execs, compiles-for-execution, or spawns a
subprocess against the artifact code. execution_status/test_status are
always "not_run" this commit; see evaluation.py's schema for why those
fields carry an explicit not-evaluated marker instead of False/0.

Fail-closed: any exception raised while inspecting the code (SyntaxError
or otherwise) is caught, recorded as syntax_pass=False with
exception_type/exception_message, and never propagates out of
evaluate_static().
"""

from __future__ import annotations

import ast
from typing import List, Optional, Sequence

from agent_tools.finals_rebuild.artifacts import sha256_json
from agent_tools.finals_rebuild.evaluation import EvaluationResult

# Bumped whenever the static evaluation RULES change (not the schema —
# schema changes don't require a version bump by themselves). Feeds into
# evaluator_config_hash together with the caller's required_functions.
STATIC_EVALUATOR_VERSION = "finals_rebuild.static_evaluator/1.0.0"

_MAX_EXCEPTION_MESSAGE_LEN = 300


def _safe_exception_summary(exc: BaseException) -> str:
    """Return a short, single-line summary of *exc* safe to persist.

    Uses str(exc) — for SyntaxError this is Python's own standard message
    (e.g. "invalid syntax (<unknown>, line 3)"), which may echo a short
    fragment of the offending line but never the full source. Truncated
    defensively regardless.
    """
    text = str(exc).replace("\n", " ").replace("\r", " ").strip()
    if len(text) > _MAX_EXCEPTION_MESSAGE_LEN:
        text = text[:_MAX_EXCEPTION_MESSAGE_LEN] + "…(truncated)"
    return text


def compute_evaluator_config_hash(
    evaluator_version: str, required_functions: Sequence[str]
) -> str:
    """Deterministic hash of the evaluator's own configuration — NOT of
    the code being evaluated. Same (version, required_functions) always
    produces the same hash regardless of treatment/artifact content."""
    return sha256_json({
        "evaluator_version": evaluator_version,
        "required_functions": sorted(required_functions),
    })


def evaluate_static(
    *,
    code: str,
    pair_id: str,
    run_id: str,
    treatment: str,
    artifact_hash: str,
    evaluator_git_commit: str,
    evaluator_version: str = STATIC_EVALUATOR_VERSION,
    required_functions: Optional[Sequence[str]] = None,
) -> EvaluationResult:
    """
    Statically evaluate *code* for one treatment artifact.

    The returned EvaluationResult has created_at_utc="" as a placeholder;
    the pipeline binds it to the treatment's resolved (idempotent)
    timestamp, exactly as it does for TreatmentTrace (see pipeline.py).

    required_functions defaults to empty, which always yields
    contract_status="not_required" — Commit 4A's pipeline does not wire
    up any per-skill required-function source yet.
    """
    req: List[str] = sorted(required_functions) if required_functions else []
    evaluator_config_hash = compute_evaluator_config_hash(evaluator_version, req)

    syntax_pass = False
    discovered: List[str] = []
    exception_type: Optional[str] = None
    exception_message: Optional[str] = None

    try:
        tree = ast.parse(code)
        syntax_pass = True
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                discovered.append(node.name)
    except SyntaxError as exc:
        exception_type = type(exc).__name__
        exception_message = _safe_exception_summary(exc)
    except Exception as exc:  # fail-closed: inspection must never crash the pipeline
        exception_type = type(exc).__name__
        exception_message = _safe_exception_summary(exc)

    if not req:
        contract_status = "not_required"
    elif not syntax_pass:
        contract_status = "fail"
    else:
        discovered_set = set(discovered)
        contract_status = "pass" if all(f in discovered_set for f in req) else "fail"

    return EvaluationResult(
        pair_id=pair_id,
        run_id=run_id,
        treatment=treatment,
        artifact_hash=artifact_hash,
        evaluator_version=evaluator_version,
        evaluator_git_commit=evaluator_git_commit,
        evaluator_config_hash=evaluator_config_hash,
        syntax_pass=syntax_pass,
        contract_status=contract_status,
        required_functions=req,
        discovered_functions=discovered,
        execution_status="not_run",
        execution_success=None,
        test_status="not_run",
        test_pass=None,
        tests_passed=None,
        tests_total=None,
        mcri_code=None,
        mcri_math=None,
        timeout=None,
        exception_type=exception_type,
        exception_message=exception_message,
        fail_closed=True,
        created_at_utc="",
    )
