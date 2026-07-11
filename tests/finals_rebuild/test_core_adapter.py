"""
Tests for agent_tools/finals_rebuild/core_adapter.py
"""

from __future__ import annotations

import inspect
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from agent_tools.finals_rebuild.artifacts import sha256_text
from agent_tools.finals_rebuild.core_adapter import (
    CORE_RULE_REGISTRY,
    run_core_adapter,
)
from agent_tools.finals_rebuild.trace import validate_treatment_trace

_PAIR_ID = "a" * 64
_CODE = "def generate():\n    return {'question_text': 'x', 'correct_answer': '1'}\n"

_REQUIRED_DISABLED_RULE_IDS = {
    "xor_to_power",
    "while_true_bounding",
    "remove_input_calls",
    "mismatched_brace_completion",
    "strip_chinese_garbage",
    "import_removal",
    "duplicate_definition_removal",
    "function_deletion_heuristics",
    "generate_fallback",
    "signature_rewrite",
    "return_contract_rewrite",
}


def test_all_mandated_high_risk_rules_are_disabled():
    for rule_id in _REQUIRED_DISABLED_RULE_IDS:
        assert rule_id in CORE_RULE_REGISTRY, f"{rule_id} missing from registry"
        assert CORE_RULE_REGISTRY[rule_id].enabled is False, (
            f"{rule_id} must be disabled in Commit 3A"
        )


def test_no_rule_is_domain_specific_and_enabled():
    for rule in CORE_RULE_REGISTRY.values():
        if rule.enabled:
            assert rule.domain_specific is False


def test_no_rule_currently_enabled():
    """Commit 3A is entirely conservative: nothing is enabled."""
    assert all(not r.enabled for r in CORE_RULE_REGISTRY.values())


def test_output_is_deterministic():
    r1 = run_core_adapter(pair_id=_PAIR_ID, input_code=_CODE)
    r2 = run_core_adapter(pair_id=_PAIR_ID, input_code=_CODE)
    assert r1.output_code == r2.output_code
    assert r1.trace.output_hash == r2.trace.output_hash


def test_output_equals_input_when_no_rule_triggers():
    result = run_core_adapter(pair_id=_PAIR_ID, input_code=_CODE)
    assert result.output_code == _CODE
    assert result.trace.changed is False
    assert result.trace.implementation_status == "implemented_no_safe_rule_triggered"
    assert result.trace.applied is True
    assert result.trace.applicable is True


def test_input_hash_matches_scaffold_extracted_hash():
    result = run_core_adapter(pair_id=_PAIR_ID, input_code=_CODE)
    assert result.trace.input_hash == sha256_text(_CODE)


def test_trace_has_no_enabled_domain_specific_steps():
    result = run_core_adapter(pair_id=_PAIR_ID, input_code=_CODE)
    for step in result.trace.steps:
        assert not (step.enabled and step.domain_specific)


def test_rules_triggered_is_empty():
    result = run_core_adapter(pair_id=_PAIR_ID, input_code=_CODE)
    assert result.trace.rules_triggered == []


def test_every_registry_rule_produces_a_step():
    result = run_core_adapter(pair_id=_PAIR_ID, input_code=_CODE)
    step_ids = {s.rule_id for s in result.trace.steps}
    assert step_ids == set(CORE_RULE_REGISTRY.keys())


def test_trace_component_and_treatment_are_core():
    result = run_core_adapter(pair_id=_PAIR_ID, input_code=_CODE)
    assert result.trace.treatment == "ab3_core"
    assert result.trace.component == "core"


def test_trace_run_id_and_created_at_are_placeholders():
    """
    run_id/created_at_utc are bound by the pipeline, not the adapter —
    the adapter cannot know either in advance.
    """
    result = run_core_adapter(pair_id=_PAIR_ID, input_code=_CODE)
    assert result.trace.run_id == ""
    assert result.trace.created_at_utc == ""


def test_finalized_trace_validates(monkeypatch):
    """Once run_id/created_at_utc are bound (as the pipeline does), the
    trace must pass full schema validation."""
    import dataclasses
    result = run_core_adapter(pair_id=_PAIR_ID, input_code=_CODE)
    finalized = dataclasses.replace(
        result.trace, run_id="b" * 64, created_at_utc="2026-07-11T09:00:00+00:00"
    )
    validate_treatment_trace(finalized)


def test_core_adapter_module_does_not_call_legacy_healers():
    """
    Structural check: core_adapter.py must not import or reference the
    legacy Healer classes/methods it is explicitly forbidden from calling.
    """
    import agent_tools.finals_rebuild.core_adapter as mod
    source = inspect.getsource(mod)
    for forbidden in (
        "RegexHealer.heal(",
        "RegexHealer.heal_minimal(",
        "RegexHealer()",
        "ASTHealer.heal(",
        "ASTHealer.semantic_heal(",
        "ASTHealer()",
        "AntiDuplicationHealer.heal(",
        "AntiDuplicationHealer()",
        "UnifiedCleanupHealer.heal(",
        "UnifiedCleanupHealer()",
        "import RegexHealer",
        "import ASTHealer",
        "import AntiDuplicationHealer",
        "import UnifiedCleanupHealer",
        "google.generativeai",
        "openai",
        "anthropic",
        "call_ai_with_retry",
    ):
        assert forbidden not in source, f"core_adapter.py must not contain {forbidden!r}"


def test_no_model_or_network_calls():
    """Functional check: adapter runs to completion with no external I/O."""
    result = run_core_adapter(pair_id=_PAIR_ID, input_code=_CODE)
    assert result.trace.applied is True
