"""
EvaluationResult schema for the finals-rebuild paired ablation study.

Scope
-----
Commit 4A: static evaluation only (syntax + contract inspection). No code
execution, no test cases, no MCRI computation, no subprocess, no import of
generated artifacts. Every field belonging to a later evaluation stage
(execution, tests, MCRI) is deliberately populated with an explicit
"not evaluated yet" marker (None / "not_run") rather than a misleading
False/0 — those are meaningfully different: False means "checked and it
failed"; None/"not_run" means "not checked at all".

This module only defines the schema, its validation, and JSON round-trip
helpers — see static_evaluator.py for the module that actually produces
EvaluationResult values.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from agent_tools.finals_rebuild.artifacts import ALLOWED_TREATMENTS, sha256_text

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CONTRACT_STATUSES: frozenset[str] = frozenset({"pass", "fail", "not_required"})

# "blocked" (Commit 4B: AST preflight denylist rejected the code before any
# subprocess was spawned) joins the set introduced in Commit 4A.
EXECUTION_STATUSES: frozenset[str] = frozenset({
    "not_run", "success", "failure", "timeout", "blocked", "error",
})
TEST_STATUSES: frozenset[str] = frozenset({
    "not_run", "passed", "failed", "error",
})

# execution_status -> required execution_success value. Enforced exactly
# (not just "must be a bool") so a caller can never report e.g.
# execution_status="failure", execution_success=True.
EXECUTION_SUCCESS_BY_STATUS: Dict[str, bool] = {
    "success": True,
    "failure": False,
    "timeout": False,
    "blocked": False,
    "error": False,
}

# Commit 4B ships exactly one isolation level: a bounded subprocess, NOT a
# security sandbox. See execution_evaluator.py's module docstring for what
# that does and does not guarantee.
ALLOWED_ISOLATION_LEVELS: frozenset[str] = frozenset({
    "guarded_subprocess_not_security_sandbox",
})

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ISO8601_UTC_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|\+00:00)$"
)


class EvaluationValidationError(ValueError):
    """Raised when an EvaluationResult fails validation."""


# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EvaluationResult:
    """One evaluator run against one treatment artifact.

    execution_status/test_status carry an explicit "not_run" sentinel;
    their corresponding value fields (execution_success, isolation_level,
    stdout_summary, stderr_summary, return_code, duration_ms, test_pass,
    tests_passed, tests_total, mcri_code, mcri_math) must be None while
    that sentinel is set — never False or 0.

    isolation_level, when set, always reports what kind of execution
    boundary was actually used (Commit 4B: a bounded subprocess, NOT a
    security sandbox — see execution_evaluator.py). It is never omitted
    or left implicit once execution_status != "not_run".
    """

    pair_id: str
    run_id: str
    treatment: str
    artifact_hash: str
    evaluator_version: str
    evaluator_git_commit: str
    evaluator_config_hash: str
    syntax_pass: bool
    contract_status: str
    required_functions: List[str] = field(default_factory=list)
    discovered_functions: List[str] = field(default_factory=list)
    execution_status: str = "not_run"
    execution_success: Optional[bool] = None
    isolation_level: Optional[str] = None
    stdout_summary: Optional[str] = None
    stderr_summary: Optional[str] = None
    return_code: Optional[int] = None
    duration_ms: Optional[float] = None
    test_status: str = "not_run"
    test_pass: Optional[bool] = None
    tests_passed: Optional[int] = None
    tests_total: Optional[int] = None
    mcri_code: Optional[float] = None
    mcri_math: Optional[float] = None
    timeout: Optional[float] = None
    exception_type: Optional[str] = None
    exception_message: Optional[str] = None
    fail_closed: bool = True
    created_at_utc: str = ""


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_evaluation_result(result: EvaluationResult) -> None:
    """Validate *result*; raises EvaluationValidationError on any defect."""
    if not isinstance(result.pair_id, str) or not _SHA256_RE.match(result.pair_id):
        raise EvaluationValidationError(
            f"pair_id must be a 64-char lowercase hex SHA-256, got {result.pair_id!r}"
        )
    if not isinstance(result.run_id, str) or not _SHA256_RE.match(result.run_id):
        raise EvaluationValidationError(
            f"run_id must be a 64-char lowercase hex SHA-256, got {result.run_id!r}"
        )
    if result.treatment not in ALLOWED_TREATMENTS:
        raise EvaluationValidationError(
            f"treatment must be one of {sorted(ALLOWED_TREATMENTS)}, "
            f"got {result.treatment!r}"
        )
    if not isinstance(result.artifact_hash, str) or not _SHA256_RE.match(
        result.artifact_hash
    ):
        raise EvaluationValidationError(
            f"artifact_hash must be a 64-char lowercase hex SHA-256, "
            f"got {result.artifact_hash!r}"
        )
    if not isinstance(result.evaluator_version, str) or not result.evaluator_version.strip():
        raise EvaluationValidationError("evaluator_version must be a non-empty string")
    if not isinstance(result.evaluator_git_commit, str) or not result.evaluator_git_commit.strip():
        raise EvaluationValidationError("evaluator_git_commit must be a non-empty string")
    if not isinstance(result.evaluator_config_hash, str) or not _SHA256_RE.match(
        result.evaluator_config_hash
    ):
        raise EvaluationValidationError(
            f"evaluator_config_hash must be a 64-char lowercase hex SHA-256, "
            f"got {result.evaluator_config_hash!r}"
        )

    if not isinstance(result.syntax_pass, bool):
        raise EvaluationValidationError("syntax_pass must be a bool")

    if result.contract_status not in CONTRACT_STATUSES:
        raise EvaluationValidationError(
            f"contract_status must be one of {sorted(CONTRACT_STATUSES)}, "
            f"got {result.contract_status!r}"
        )

    for list_field in ("required_functions", "discovered_functions"):
        value = getattr(result, list_field)
        if not isinstance(value, list) or not all(
            isinstance(item, str) and item for item in value
        ):
            raise EvaluationValidationError(
                f"{list_field} must be a list of non-empty strings"
            )

    if result.execution_status not in EXECUTION_STATUSES:
        raise EvaluationValidationError(
            f"execution_status must be one of {sorted(EXECUTION_STATUSES)}, "
            f"got {result.execution_status!r}"
        )
    if result.execution_status == "not_run":
        for fname in (
            "execution_success", "isolation_level", "stdout_summary",
            "stderr_summary", "return_code", "duration_ms",
        ):
            if getattr(result, fname) is not None:
                raise EvaluationValidationError(
                    f"execution_status='not_run' requires {fname}=None"
                )
    else:
        expected_success = EXECUTION_SUCCESS_BY_STATUS[result.execution_status]
        if result.execution_success is not expected_success:
            raise EvaluationValidationError(
                f"execution_status={result.execution_status!r} requires "
                f"execution_success={expected_success!r}, "
                f"got {result.execution_success!r}"
            )
        if result.isolation_level not in ALLOWED_ISOLATION_LEVELS:
            raise EvaluationValidationError(
                f"isolation_level must be one of {sorted(ALLOWED_ISOLATION_LEVELS)} "
                f"once execution_status != 'not_run', got {result.isolation_level!r}"
            )
        for fname in ("stdout_summary", "stderr_summary"):
            value = getattr(result, fname)
            if value is not None and not isinstance(value, str):
                raise EvaluationValidationError(f"{fname} must be None or a string")
        if result.return_code is not None and (
            isinstance(result.return_code, bool) or not isinstance(result.return_code, int)
        ):
            raise EvaluationValidationError("return_code must be None or an int")
        if result.duration_ms is not None and (
            isinstance(result.duration_ms, bool)
            or not isinstance(result.duration_ms, (int, float))
            or result.duration_ms < 0
        ):
            raise EvaluationValidationError(
                "duration_ms must be None or a non-negative number"
            )

    if result.test_status not in TEST_STATUSES:
        raise EvaluationValidationError(
            f"test_status must be one of {sorted(TEST_STATUSES)}, "
            f"got {result.test_status!r}"
        )
    if result.test_status == "not_run":
        for fname in ("test_pass", "tests_passed", "tests_total", "mcri_code", "mcri_math"):
            if getattr(result, fname) is not None:
                raise EvaluationValidationError(
                    f"test_status='not_run' requires {fname}=None"
                )
    else:
        if not isinstance(result.test_pass, bool):
            raise EvaluationValidationError(
                "test_pass must be a bool once test_status != 'not_run'"
            )
        for fname in ("tests_passed", "tests_total"):
            value = getattr(result, fname)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise EvaluationValidationError(
                    f"{fname} must be a non-negative int once test_status != 'not_run'"
                )
        if result.tests_passed > result.tests_total:
            raise EvaluationValidationError("tests_passed cannot exceed tests_total")
        for fname in ("mcri_code", "mcri_math"):
            value = getattr(result, fname)
            if value is not None and (
                isinstance(value, bool) or not isinstance(value, (int, float))
            ):
                raise EvaluationValidationError(f"{fname} must be None or numeric")

    if result.timeout is not None and (
        isinstance(result.timeout, bool)
        or not isinstance(result.timeout, (int, float))
        or result.timeout <= 0
    ):
        raise EvaluationValidationError("timeout must be None or a positive number")

    if result.exception_type is not None and (
        not isinstance(result.exception_type, str) or not result.exception_type.strip()
    ):
        raise EvaluationValidationError(
            "exception_type must be None or a non-empty string"
        )
    if result.exception_message is not None and not isinstance(
        result.exception_message, str
    ):
        raise EvaluationValidationError("exception_message must be None or a string")

    if not result.syntax_pass and result.exception_type is None:
        raise EvaluationValidationError(
            "syntax_pass=False requires exception_type to be recorded"
        )

    if not isinstance(result.fail_closed, bool):
        raise EvaluationValidationError("fail_closed must be a bool")

    if not isinstance(result.created_at_utc, str) or not _ISO8601_UTC_RE.match(
        result.created_at_utc
    ):
        raise EvaluationValidationError(
            f"created_at_utc must be UTC ISO-8601 with Z or +00:00 offset, "
            f"got {result.created_at_utc!r}"
        )


# ---------------------------------------------------------------------------
# JSON round-trip helpers
# ---------------------------------------------------------------------------


def evaluation_result_to_dict(result: EvaluationResult) -> Dict[str, Any]:
    return {
        "pair_id": result.pair_id,
        "run_id": result.run_id,
        "treatment": result.treatment,
        "artifact_hash": result.artifact_hash,
        "evaluator_version": result.evaluator_version,
        "evaluator_git_commit": result.evaluator_git_commit,
        "evaluator_config_hash": result.evaluator_config_hash,
        "syntax_pass": result.syntax_pass,
        "contract_status": result.contract_status,
        "required_functions": list(result.required_functions),
        "discovered_functions": list(result.discovered_functions),
        "execution_status": result.execution_status,
        "execution_success": result.execution_success,
        "isolation_level": result.isolation_level,
        "stdout_summary": result.stdout_summary,
        "stderr_summary": result.stderr_summary,
        "return_code": result.return_code,
        "duration_ms": result.duration_ms,
        "test_status": result.test_status,
        "test_pass": result.test_pass,
        "tests_passed": result.tests_passed,
        "tests_total": result.tests_total,
        "mcri_code": result.mcri_code,
        "mcri_math": result.mcri_math,
        "timeout": result.timeout,
        "exception_type": result.exception_type,
        "exception_message": result.exception_message,
        "fail_closed": result.fail_closed,
        "created_at_utc": result.created_at_utc,
    }


def evaluation_result_from_dict(d: Dict[str, Any]) -> EvaluationResult:
    return EvaluationResult(
        pair_id=d["pair_id"],
        run_id=d["run_id"],
        treatment=d["treatment"],
        artifact_hash=d["artifact_hash"],
        evaluator_version=d["evaluator_version"],
        evaluator_git_commit=d["evaluator_git_commit"],
        evaluator_config_hash=d["evaluator_config_hash"],
        syntax_pass=d["syntax_pass"],
        contract_status=d["contract_status"],
        required_functions=list(d.get("required_functions", [])),
        discovered_functions=list(d.get("discovered_functions", [])),
        execution_status=d.get("execution_status", "not_run"),
        execution_success=d.get("execution_success"),
        isolation_level=d.get("isolation_level"),
        stdout_summary=d.get("stdout_summary"),
        stderr_summary=d.get("stderr_summary"),
        return_code=d.get("return_code"),
        duration_ms=d.get("duration_ms"),
        test_status=d.get("test_status", "not_run"),
        test_pass=d.get("test_pass"),
        tests_passed=d.get("tests_passed"),
        tests_total=d.get("tests_total"),
        mcri_code=d.get("mcri_code"),
        mcri_math=d.get("mcri_math"),
        timeout=d.get("timeout"),
        exception_type=d.get("exception_type"),
        exception_message=d.get("exception_message"),
        fail_closed=d.get("fail_closed", True),
        created_at_utc=d["created_at_utc"],
    )


def evaluation_result_json_round_trip(result: EvaluationResult) -> EvaluationResult:
    """Serialise to JSON string and back; used for round-trip tests."""
    raw_json = json.dumps(
        evaluation_result_to_dict(result),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return evaluation_result_from_dict(json.loads(raw_json))


def compute_evaluation_hash(result: EvaluationResult) -> str:
    """SHA-256 of the exact bytes that :func:`immutable_write_json` will
    write for this result (sort_keys=True, indent=2, ensure_ascii=True,
    plus a trailing newline) — kept identical to the artifacts.py
    serialisation so RunMetadata.evaluation_hash is guaranteed to equal
    the on-disk file hash.
    """
    serialised = (
        json.dumps(
            evaluation_result_to_dict(result),
            sort_keys=True,
            indent=2,
            ensure_ascii=True,
        )
        + "\n"
    )
    return sha256_text(serialised)
