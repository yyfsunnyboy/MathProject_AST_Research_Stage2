"""
TreatmentTrace / TraceStep schema for the Core and Spec adapters.

Purpose
-------
Rule-level trace of what the Core Adapter (ab3_core) and Spec Adapter
(ab3_full) did to a given piece of code. Every candidate rule — enabled or
not — appears as one TraceStep so the disabled/enabled boundary is fully
auditable from the artifact alone.

Never stores model chain-of-thought or any model output text. Every value
here is derived from code hashes, rule metadata, and booleans.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from agent_tools.finals_rebuild.artifacts import sha256_text

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SAFETY_CLASSIFICATIONS: frozenset[str] = frozenset({
    "safe_format",
    "guarded_structural",
    "domain_specific",
    "disabled_semantic_risk",
})

COMPONENTS: frozenset[str] = frozenset({"core", "spec"})

TREATMENT_COMPONENT: Dict[str, str] = {
    "ab3_core": "core",
    "ab3_full": "spec",
}

IMPLEMENTATION_STATUSES: frozenset[str] = frozenset({
    "implemented",
    "implemented_no_safe_rule_triggered",
    "not_applicable",
})

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ISO8601_UTC_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|\+00:00)$"
)


class TraceValidationError(ValueError):
    """Raised when a TraceStep or TreatmentTrace fails validation."""


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TraceStep:
    """One candidate rule's outcome for one adapter invocation.

    Emitted for every registry rule, whether or not it ran, so the
    disabled/enabled boundary is visible directly in the artifact.
    """

    rule_id: str
    source_component: str  # "core" | "spec"
    changed: bool
    before_hash: str
    after_hash: str
    reason: str
    domain_specific: bool
    safety_classification: str
    enabled: bool


@dataclass(frozen=True)
class TreatmentTrace:
    """Rule-level trace for one treatment execution (ab3_core or ab3_full)."""

    pair_id: str
    run_id: str
    treatment: str  # "ab3_core" | "ab3_full"
    component: str  # "core" | "spec"
    applicable: bool
    applied: bool
    changed: bool
    input_hash: str
    output_hash: str
    implementation_status: str
    fail_closed: bool
    failure_reason: Optional[str]
    contract_changed: bool
    rules_triggered: List[str] = field(default_factory=list)
    steps: List[TraceStep] = field(default_factory=list)
    created_at_utc: str = ""


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_trace_step(step: TraceStep) -> None:
    """Validate *step* in isolation (no knowledge of its parent trace)."""
    if not isinstance(step.rule_id, str) or not step.rule_id.strip():
        raise TraceValidationError("rule_id must be a non-empty string")
    if step.source_component not in COMPONENTS:
        raise TraceValidationError(
            f"source_component must be one of {sorted(COMPONENTS)}, "
            f"got {step.source_component!r}"
        )
    if not isinstance(step.before_hash, str) or not _SHA256_RE.match(step.before_hash):
        raise TraceValidationError(
            f"before_hash must be a 64-char lowercase hex SHA-256, "
            f"got {step.before_hash!r}"
        )
    if not isinstance(step.after_hash, str) or not _SHA256_RE.match(step.after_hash):
        raise TraceValidationError(
            f"after_hash must be a 64-char lowercase hex SHA-256, "
            f"got {step.after_hash!r}"
        )
    if step.safety_classification not in SAFETY_CLASSIFICATIONS:
        raise TraceValidationError(
            f"safety_classification must be one of "
            f"{sorted(SAFETY_CLASSIFICATIONS)}, got {step.safety_classification!r}"
        )
    for flag_name in ("changed", "domain_specific", "enabled"):
        if not isinstance(getattr(step, flag_name), bool):
            raise TraceValidationError(f"{flag_name} must be a bool")
    if not isinstance(step.reason, str) or not step.reason.strip():
        raise TraceValidationError("reason must be a non-empty string")

    # Hard safety invariant: a rule classified as semantically risky can
    # never be marked enabled, regardless of what the adapter passed in.
    if step.enabled and step.safety_classification == "disabled_semantic_risk":
        raise TraceValidationError(
            f"rule {step.rule_id!r}: safety_classification="
            f"'disabled_semantic_risk' rules must never be enabled"
        )
    if not step.enabled and step.changed:
        raise TraceValidationError(
            f"rule {step.rule_id!r}: a disabled rule cannot report changed=True"
        )


def validate_treatment_trace(trace: TreatmentTrace) -> None:
    """Validate *trace* and all of its steps; raises TraceValidationError."""
    if not isinstance(trace.pair_id, str) or not _SHA256_RE.match(trace.pair_id):
        raise TraceValidationError(
            f"pair_id must be a 64-char lowercase hex SHA-256, got {trace.pair_id!r}"
        )
    if not isinstance(trace.run_id, str) or not _SHA256_RE.match(trace.run_id):
        raise TraceValidationError(
            f"run_id must be a 64-char lowercase hex SHA-256, got {trace.run_id!r}"
        )
    if trace.treatment not in TREATMENT_COMPONENT:
        raise TraceValidationError(
            f"treatment must be one of {sorted(TREATMENT_COMPONENT)}, "
            f"got {trace.treatment!r}"
        )
    if trace.component not in COMPONENTS:
        raise TraceValidationError(
            f"component must be one of {sorted(COMPONENTS)}, got {trace.component!r}"
        )
    expected_component = TREATMENT_COMPONENT[trace.treatment]
    if trace.component != expected_component:
        raise TraceValidationError(
            f"treatment {trace.treatment!r} must have component "
            f"{expected_component!r}, got {trace.component!r}"
        )

    for flag_name in ("applicable", "applied", "changed", "fail_closed", "contract_changed"):
        if not isinstance(getattr(trace, flag_name), bool):
            raise TraceValidationError(f"{flag_name} must be a bool")

    if not isinstance(trace.input_hash, str) or not _SHA256_RE.match(trace.input_hash):
        raise TraceValidationError(
            f"input_hash must be a 64-char lowercase hex SHA-256, "
            f"got {trace.input_hash!r}"
        )
    if not isinstance(trace.output_hash, str) or not _SHA256_RE.match(trace.output_hash):
        raise TraceValidationError(
            f"output_hash must be a 64-char lowercase hex SHA-256, "
            f"got {trace.output_hash!r}"
        )
    if trace.implementation_status not in IMPLEMENTATION_STATUSES:
        raise TraceValidationError(
            f"implementation_status must be one of "
            f"{sorted(IMPLEMENTATION_STATUSES)}, got {trace.implementation_status!r}"
        )
    if trace.failure_reason is not None and not isinstance(trace.failure_reason, str):
        raise TraceValidationError("failure_reason must be None or a string")

    if not isinstance(trace.rules_triggered, list):
        raise TraceValidationError("rules_triggered must be a list")
    for rule_id in trace.rules_triggered:
        if not isinstance(rule_id, str) or not rule_id.strip():
            raise TraceValidationError(
                "rules_triggered entries must be non-empty strings"
            )

    if not isinstance(trace.steps, list):
        raise TraceValidationError("steps must be a list")
    step_rule_ids: set[str] = set()
    for step in trace.steps:
        validate_trace_step(step)
        if step.source_component != trace.component:
            raise TraceValidationError(
                f"step {step.rule_id!r}: source_component "
                f"{step.source_component!r} must match trace component "
                f"{trace.component!r}"
            )
        step_rule_ids.add(step.rule_id)

    for rule_id in trace.rules_triggered:
        if rule_id not in step_rule_ids:
            raise TraceValidationError(
                f"rules_triggered contains {rule_id!r} which has no matching step"
            )

    # A rule can only end up in rules_triggered if its step is enabled+changed.
    triggered_steps = {
        step.rule_id for step in trace.steps if step.enabled and step.changed
    }
    if set(trace.rules_triggered) != triggered_steps:
        raise TraceValidationError(
            f"rules_triggered {sorted(trace.rules_triggered)} must exactly match "
            f"enabled+changed steps {sorted(triggered_steps)}"
        )

    # Core must never carry an enabled domain-specific step.
    if trace.component == "core":
        for step in trace.steps:
            if step.enabled and step.domain_specific:
                raise TraceValidationError(
                    f"core component must not have an enabled domain_specific "
                    f"step (rule_id={step.rule_id!r})"
                )

    # Non-applicable trace must be a pure no-op.
    if not trace.applicable:
        if trace.applied or trace.changed or trace.rules_triggered or trace.steps:
            raise TraceValidationError(
                "applicable=False requires applied=False, changed=False, "
                "no rules_triggered, and no steps"
            )
        if trace.input_hash != trace.output_hash:
            raise TraceValidationError(
                "applicable=False requires input_hash == output_hash"
            )
        if trace.implementation_status != "not_applicable":
            raise TraceValidationError(
                "applicable=False requires implementation_status='not_applicable'"
            )

    # changed=True requires input_hash != output_hash, and vice versa.
    if trace.changed and trace.input_hash == trace.output_hash:
        raise TraceValidationError(
            "changed=True requires input_hash != output_hash"
        )
    if not trace.changed and trace.input_hash != trace.output_hash:
        raise TraceValidationError(
            "input_hash != output_hash requires changed=True"
        )

    if not isinstance(trace.created_at_utc, str) or not _ISO8601_UTC_RE.match(
        trace.created_at_utc
    ):
        raise TraceValidationError(
            f"created_at_utc must be UTC ISO-8601 with Z or +00:00 offset, "
            f"got {trace.created_at_utc!r}"
        )


# ---------------------------------------------------------------------------
# JSON round-trip helpers
# ---------------------------------------------------------------------------


def trace_step_to_dict(step: TraceStep) -> Dict[str, Any]:
    return {
        "rule_id": step.rule_id,
        "source_component": step.source_component,
        "changed": step.changed,
        "before_hash": step.before_hash,
        "after_hash": step.after_hash,
        "reason": step.reason,
        "domain_specific": step.domain_specific,
        "safety_classification": step.safety_classification,
        "enabled": step.enabled,
    }


def trace_step_from_dict(d: Dict[str, Any]) -> TraceStep:
    return TraceStep(
        rule_id=d["rule_id"],
        source_component=d["source_component"],
        changed=d["changed"],
        before_hash=d["before_hash"],
        after_hash=d["after_hash"],
        reason=d["reason"],
        domain_specific=d["domain_specific"],
        safety_classification=d["safety_classification"],
        enabled=d["enabled"],
    )


def treatment_trace_to_dict(trace: TreatmentTrace) -> Dict[str, Any]:
    return {
        "pair_id": trace.pair_id,
        "run_id": trace.run_id,
        "treatment": trace.treatment,
        "component": trace.component,
        "applicable": trace.applicable,
        "applied": trace.applied,
        "changed": trace.changed,
        "input_hash": trace.input_hash,
        "output_hash": trace.output_hash,
        "implementation_status": trace.implementation_status,
        "fail_closed": trace.fail_closed,
        "failure_reason": trace.failure_reason,
        "contract_changed": trace.contract_changed,
        "rules_triggered": list(trace.rules_triggered),
        "steps": [trace_step_to_dict(s) for s in trace.steps],
        "created_at_utc": trace.created_at_utc,
    }


def treatment_trace_from_dict(d: Dict[str, Any]) -> TreatmentTrace:
    return TreatmentTrace(
        pair_id=d["pair_id"],
        run_id=d["run_id"],
        treatment=d["treatment"],
        component=d["component"],
        applicable=d["applicable"],
        applied=d["applied"],
        changed=d["changed"],
        input_hash=d["input_hash"],
        output_hash=d["output_hash"],
        implementation_status=d["implementation_status"],
        fail_closed=d["fail_closed"],
        failure_reason=d.get("failure_reason"),
        contract_changed=d["contract_changed"],
        rules_triggered=list(d.get("rules_triggered", [])),
        steps=[trace_step_from_dict(s) for s in d.get("steps", [])],
        created_at_utc=d["created_at_utc"],
    )


def treatment_trace_json_round_trip(trace: TreatmentTrace) -> TreatmentTrace:
    """Serialise to JSON string and back; used for round-trip tests."""
    raw_json = json.dumps(
        treatment_trace_to_dict(trace),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return treatment_trace_from_dict(json.loads(raw_json))


def compute_trace_hash(trace: TreatmentTrace) -> str:
    """SHA-256 of the exact bytes that :func:`immutable_write_json` will
    write for this trace (sort_keys=True, indent=2, ensure_ascii=True, plus
    a trailing newline) — kept identical to the artifacts.py serialisation
    so RunMetadata.trace_hash is guaranteed to equal the on-disk file hash.
    """
    serialised = (
        json.dumps(
            treatment_trace_to_dict(trace),
            sort_keys=True,
            indent=2,
            ensure_ascii=True,
        )
        + "\n"
    )
    return sha256_text(serialised)
