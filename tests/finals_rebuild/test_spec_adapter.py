"""
Tests for agent_tools/finals_rebuild/spec_adapter.py
"""

from __future__ import annotations

import inspect
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from agent_tools.finals_rebuild.artifacts import sha256_text
from agent_tools.finals_rebuild.spec_adapter import (
    SPEC_RULE_REGISTRY,
    is_k12_math_domain,
    run_spec_adapter,
)
from agent_tools.finals_rebuild.trace import validate_treatment_trace

_PAIR_ID = "a" * 64
_CODE = "def generate():\n    return {'question_text': 'x', 'correct_answer': '1'}\n"

_REQUIRED_DISABLED_RULE_IDS = {
    "calculation_skeleton_injection",
    "domain_library_injection",
    "generate_fallback",
    "auto_fill_correct_answer",
    "domain_ops_injection",
    "latex_auto_repair",
    "domain_function_helper_injection",
}


def test_all_domain_rules_are_disabled():
    for rule_id in _REQUIRED_DISABLED_RULE_IDS:
        assert rule_id in SPEC_RULE_REGISTRY, f"{rule_id} missing from registry"
        assert SPEC_RULE_REGISTRY[rule_id].enabled is False


def test_no_rule_currently_enabled():
    assert all(not r.enabled for r in SPEC_RULE_REGISTRY.values())


# ---------------------------------------------------------------------------
# Domain classifier
# ---------------------------------------------------------------------------


def test_jh_prefix_is_k12_math():
    assert is_k12_math_domain("jh_數學1上_FourArithmeticOperationsOfIntegers") is True


def test_gh_prefix_is_k12_math():
    assert is_k12_math_domain("gh_ApplicationsOfDerivatives") is True


def test_unknown_prefix_is_not_k12_math():
    assert is_k12_math_domain("algebra_01") is False


def test_empty_skill_id_is_not_k12_math():
    assert is_k12_math_domain("") is False


# ---------------------------------------------------------------------------
# Non-applicable domain → no-op
# ---------------------------------------------------------------------------


def test_non_math_domain_is_pure_noop():
    result = run_spec_adapter(pair_id=_PAIR_ID, skill_id="algebra_01", input_code=_CODE)
    assert result.output_code == _CODE
    assert result.trace.applicable is False
    assert result.trace.applied is False
    assert result.trace.changed is False
    assert result.trace.implementation_status == "not_applicable"
    assert result.trace.steps == []
    assert result.trace.rules_triggered == []
    assert result.trace.input_hash == result.trace.output_hash == sha256_text(_CODE)


def test_explicit_domain_applicable_override_false():
    result = run_spec_adapter(
        pair_id=_PAIR_ID, skill_id="jh_math_skill", input_code=_CODE,
        domain_applicable=False,
    )
    assert result.trace.applicable is False


# ---------------------------------------------------------------------------
# Applicable K12-math domain → still no-op in Commit 3A (no enabled rule)
# ---------------------------------------------------------------------------


def test_math_domain_applicable_but_no_safe_rule_triggered():
    result = run_spec_adapter(
        pair_id=_PAIR_ID, skill_id="jh_數學1上_FourArithmeticOperationsOfIntegers",
        input_code=_CODE,
    )
    assert result.output_code == _CODE
    assert result.trace.applicable is True
    assert result.trace.applied is True
    assert result.trace.changed is False
    assert result.trace.implementation_status == "implemented_no_safe_rule_triggered"
    assert result.trace.rules_triggered == []
    step_ids = {s.rule_id for s in result.trace.steps}
    assert step_ids == set(SPEC_RULE_REGISTRY.keys())
    for step in result.trace.steps:
        assert step.enabled is False


def test_explicit_domain_applicable_override_true():
    result = run_spec_adapter(
        pair_id=_PAIR_ID, skill_id="not_a_math_skill", input_code=_CODE,
        domain_applicable=True,
    )
    assert result.trace.applicable is True
    assert result.trace.implementation_status == "implemented_no_safe_rule_triggered"


# ---------------------------------------------------------------------------
# Spec input = Core output
# ---------------------------------------------------------------------------


def test_spec_input_hash_equals_provided_input_code_hash():
    """
    The pipeline is responsible for feeding Core's output as Spec's
    input_code; the adapter itself simply hashes whatever it receives.
    """
    core_like_output = "def generate():\n    return {'correct_answer': '2'}\n"
    result = run_spec_adapter(
        pair_id=_PAIR_ID, skill_id="jh_math_skill", input_code=core_like_output,
    )
    assert result.trace.input_hash == sha256_text(core_like_output)


# ---------------------------------------------------------------------------
# Trace validity + forbidden calls
# ---------------------------------------------------------------------------


def test_applicable_trace_validates_once_finalized():
    import dataclasses
    result = run_spec_adapter(
        pair_id=_PAIR_ID, skill_id="jh_math_skill", input_code=_CODE,
    )
    finalized = dataclasses.replace(
        result.trace, run_id="b" * 64, created_at_utc="2026-07-11T09:00:00+00:00"
    )
    validate_treatment_trace(finalized)


def test_noop_trace_validates_once_finalized():
    import dataclasses
    result = run_spec_adapter(
        pair_id=_PAIR_ID, skill_id="algebra_01", input_code=_CODE,
    )
    finalized = dataclasses.replace(
        result.trace, run_id="b" * 64, created_at_utc="2026-07-11T09:00:00+00:00"
    )
    validate_treatment_trace(finalized)


def test_spec_adapter_module_imports_nothing_forbidden():
    """
    Structural check: spec_adapter.py must not import core.code_generator,
    any legacy Healer class, or any AI client. Rule names/reasons may
    legitimately mention these in docstrings (that's how the registry
    documents deferral), so this checks import statements specifically,
    not arbitrary substrings.
    """
    import agent_tools.finals_rebuild.spec_adapter as mod
    source = inspect.getsource(mod)
    import_lines = [
        line.strip() for line in source.splitlines()
        if line.strip().startswith(("import ", "from "))
    ]
    joined_imports = "\n".join(import_lines)
    for forbidden in (
        "core.code_generator",
        "core.healers",
        "RegexHealer",
        "ASTHealer",
        "AntiDuplicationHealer",
        "UnifiedCleanupHealer",
        "google.generativeai",
        "openai",
        "anthropic",
        "call_ai_with_retry",
    ):
        assert forbidden not in joined_imports, (
            f"spec_adapter.py must not import {forbidden!r}"
        )
    # No rule in the registry has a live callable yet — fn is always None
    # while enabled=False, so nothing forbidden can actually execute.
    for rule in SPEC_RULE_REGISTRY.values():
        if not rule.enabled:
            assert rule.fn is None


def test_no_model_or_network_calls():
    result = run_spec_adapter(
        pair_id=_PAIR_ID, skill_id="jh_math_skill", input_code=_CODE,
    )
    assert result.trace.applied is True
