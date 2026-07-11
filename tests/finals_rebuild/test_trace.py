"""
Tests for agent_tools/finals_rebuild/trace.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import pytest

from agent_tools.finals_rebuild.artifacts import sha256_text
from agent_tools.finals_rebuild.trace import (
    TraceStep,
    TraceValidationError,
    TreatmentTrace,
    compute_trace_hash,
    treatment_trace_from_dict,
    treatment_trace_json_round_trip,
    treatment_trace_to_dict,
    validate_trace_step,
    validate_treatment_trace,
)

_PAIR_ID = "a" * 64
_RUN_ID = "b" * 64
_HASH = sha256_text("some code")
_TS = "2026-07-11T09:00:00+00:00"


def _step(**overrides) -> TraceStep:
    base = dict(
        rule_id="dummy_rule",
        source_component="core",
        changed=False,
        before_hash=_HASH,
        after_hash=_HASH,
        reason="test reason",
        domain_specific=False,
        safety_classification="guarded_structural",
        enabled=False,
    )
    base.update(overrides)
    return TraceStep(**base)


def _trace(**overrides) -> TreatmentTrace:
    base = dict(
        pair_id=_PAIR_ID,
        run_id=_RUN_ID,
        treatment="ab3_core",
        component="core",
        applicable=True,
        applied=True,
        changed=False,
        input_hash=_HASH,
        output_hash=_HASH,
        implementation_status="implemented_no_safe_rule_triggered",
        fail_closed=True,
        failure_reason=None,
        contract_changed=False,
        rules_triggered=[],
        steps=[_step()],
        created_at_utc=_TS,
    )
    base.update(overrides)
    return TreatmentTrace(**base)


# ---------------------------------------------------------------------------
# TraceStep validation
# ---------------------------------------------------------------------------


def test_valid_step_passes():
    validate_trace_step(_step())


def test_disabled_semantic_risk_rule_cannot_be_enabled():
    with pytest.raises(TraceValidationError, match="disabled_semantic_risk"):
        validate_trace_step(_step(
            enabled=True, safety_classification="disabled_semantic_risk",
            changed=True, after_hash="c" * 64,
        ))


def test_disabled_step_cannot_report_changed():
    with pytest.raises(TraceValidationError, match="disabled rule"):
        validate_trace_step(_step(enabled=False, changed=True, after_hash="c" * 64))


def test_invalid_safety_classification_rejected():
    with pytest.raises(TraceValidationError, match="safety_classification"):
        validate_trace_step(_step(safety_classification="not_a_real_category"))


def test_bad_hash_format_rejected():
    with pytest.raises(TraceValidationError, match="before_hash"):
        validate_trace_step(_step(before_hash="not-a-hash"))


# ---------------------------------------------------------------------------
# TreatmentTrace validation
# ---------------------------------------------------------------------------


def test_valid_trace_passes():
    validate_treatment_trace(_trace())


def test_treatment_component_mismatch_rejected():
    with pytest.raises(TraceValidationError, match="component"):
        validate_treatment_trace(_trace(treatment="ab3_core", component="spec"))


def test_spec_component_requires_ab3_full_treatment():
    trace = _trace(
        treatment="ab3_full", component="spec",
        steps=[_step(source_component="spec")],
    )
    validate_treatment_trace(trace)


def test_unknown_treatment_rejected():
    with pytest.raises(TraceValidationError, match="treatment"):
        validate_treatment_trace(_trace(treatment="ab1"))


def test_step_source_component_must_match_trace_component():
    with pytest.raises(TraceValidationError, match="source_component"):
        validate_treatment_trace(_trace(steps=[_step(source_component="spec")]))


def test_rules_triggered_must_match_enabled_changed_steps():
    with pytest.raises(TraceValidationError, match="rules_triggered"):
        validate_treatment_trace(_trace(rules_triggered=["dummy_rule"]))


def test_core_component_rejects_enabled_domain_specific_step():
    hot_step = _step(
        rule_id="hot", enabled=True, domain_specific=True,
        safety_classification="domain_specific",
        after_hash="c" * 64, changed=True,
    )
    with pytest.raises(TraceValidationError, match="domain_specific"):
        validate_treatment_trace(
            _trace(steps=[hot_step], rules_triggered=["hot"])
        )


def test_applicable_false_requires_pure_no_op():
    trace = TreatmentTrace(
        pair_id=_PAIR_ID,
        run_id=_RUN_ID,
        treatment="ab3_full",
        component="spec",
        applicable=False,
        applied=False,
        changed=False,
        input_hash=_HASH,
        output_hash=_HASH,
        implementation_status="not_applicable",
        fail_closed=True,
        failure_reason=None,
        contract_changed=False,
        rules_triggered=[],
        steps=[],
        created_at_utc=_TS,
    )
    validate_treatment_trace(trace)


def test_applicable_false_but_applied_true_rejected():
    trace = TreatmentTrace(
        pair_id=_PAIR_ID, run_id=_RUN_ID, treatment="ab3_full", component="spec",
        applicable=False, applied=True, changed=False,
        input_hash=_HASH, output_hash=_HASH,
        implementation_status="not_applicable", fail_closed=True,
        failure_reason=None, contract_changed=False,
        rules_triggered=[], steps=[], created_at_utc=_TS,
    )
    with pytest.raises(TraceValidationError, match="applicable=False"):
        validate_treatment_trace(trace)


def test_changed_true_requires_hash_mismatch():
    with pytest.raises(TraceValidationError, match="changed=True"):
        validate_treatment_trace(_trace(changed=True))


def test_hash_mismatch_requires_changed_true():
    with pytest.raises(TraceValidationError, match="input_hash != output_hash"):
        validate_treatment_trace(_trace(output_hash="c" * 64))


def test_bad_created_at_utc_rejected():
    with pytest.raises(TraceValidationError, match="created_at_utc"):
        validate_treatment_trace(_trace(created_at_utc="not-a-date"))


def test_bad_implementation_status_rejected():
    with pytest.raises(TraceValidationError, match="implementation_status"):
        validate_treatment_trace(_trace(implementation_status="totally_made_up"))


# ---------------------------------------------------------------------------
# JSON round-trip
# ---------------------------------------------------------------------------


def test_json_round_trip_preserves_content():
    trace = _trace()
    round_tripped = treatment_trace_json_round_trip(trace)
    assert treatment_trace_to_dict(trace) == treatment_trace_to_dict(round_tripped)


def test_from_dict_to_dict_inverse():
    trace = _trace()
    d = treatment_trace_to_dict(trace)
    restored = treatment_trace_from_dict(d)
    assert restored == trace


# ---------------------------------------------------------------------------
# compute_trace_hash determinism
# ---------------------------------------------------------------------------


def test_compute_trace_hash_is_deterministic():
    trace = _trace()
    assert compute_trace_hash(trace) == compute_trace_hash(trace)


def test_compute_trace_hash_changes_with_content():
    trace_a = _trace()
    trace_b = _trace(changed=True, output_hash="c" * 64)
    assert compute_trace_hash(trace_a) != compute_trace_hash(trace_b)


def test_compute_trace_hash_is_valid_sha256():
    import re
    h = compute_trace_hash(_trace())
    assert re.match(r"^[0-9a-f]{64}$", h)
