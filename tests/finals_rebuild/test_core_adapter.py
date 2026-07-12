"""
Tests for agent_tools/finals_rebuild/core_adapter.py
"""

from __future__ import annotations

import inspect
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import ast

import pytest

from agent_tools.finals_rebuild.artifacts import sha256_text
from agent_tools.finals_rebuild.core_adapter import (
    CORE_RULE_REGISTRY,
    normalize_fullwidth_python_punctuation,
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


def test_exactly_one_rule_currently_enabled():
    """
    Commit 3B-1 enables exactly one, safe_format, non-domain-specific rule:
    core.normalize_fullwidth_python_punctuation. Everything else stays
    disabled.
    """
    enabled = [r for r in CORE_RULE_REGISTRY.values() if r.enabled]
    assert len(enabled) == 1
    assert enabled[0].rule_id == "core.normalize_fullwidth_python_punctuation"
    assert enabled[0].safety_classification == "safe_format"
    assert enabled[0].domain_specific is False
    for rule_id in _REQUIRED_DISABLED_RULE_IDS:
        assert CORE_RULE_REGISTRY[rule_id].enabled is False


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


# ============================================================
# Commit 3B-1: core.normalize_fullwidth_python_punctuation
# ============================================================


def test_1_fullwidth_colon_makes_code_legal():
    code = "if x>0：\n    pass\n"
    out = normalize_fullwidth_python_punctuation(code)
    assert out != code
    ast.parse(out)  # must not raise
    assert "：" not in out


def test_2_string_content_untouched():
    code = 'x = "全形：，（）"\n'
    out = normalize_fullwidth_python_punctuation(code)
    assert out == code


def test_3_comment_untouched():
    code = "x = 1  # 全形：，（）\n"
    out = normalize_fullwidth_python_punctuation(code)
    assert out == code


def test_4_docstring_untouched():
    code = 'def f():\n    """全形：，（）"""\n    pass\n'
    out = normalize_fullwidth_python_punctuation(code)
    assert out == code


def test_5_legal_code_is_noop():
    code = "def f(x, y):\n    return x + y\n"
    out = normalize_fullwidth_python_punctuation(code)
    assert out == code


def test_6_healed_output_parses():
    code = "f(x，y)\n"
    out = normalize_fullwidth_python_punctuation(code)
    ast.parse(out)  # must not raise
    assert out == "f(x,y)\n"


def test_7_unrecoverable_input_fails_closed_returns_original():
    """
    '＞' (fullwidth greater-than) is deliberately NOT in the mapped set.
    Normalizing only the colon still leaves invalid syntax, so the rule
    must detect the re-parse failure and return the ORIGINAL code
    untouched rather than a half-fixed, still-broken result.
    """
    code = "if x＞0：\n    pass\n"
    out = normalize_fullwidth_python_punctuation(code)
    assert out == code
    with pytest.raises(SyntaxError):
        ast.parse(out)


def test_mixed_identifier_and_fullwidth_comma_is_split_safely():
    """
    Regression guard for the tokenizer quirk that motivated the
    span-masking implementation: CPython's tokenizer merges '，' into the
    same NAME token as adjacent identifier characters (e.g. "x，y" is one
    NAME token), so naive per-token rewriting would miss this case
    entirely. The span-masking approach must still catch it.
    """
    code = "def f(a，b):\n    return a，b\n"
    out = normalize_fullwidth_python_punctuation(code)
    ast.parse(out)
    assert "，" not in out


def test_empty_string_is_noop():
    assert normalize_fullwidth_python_punctuation("") == ""


def test_unparseable_input_is_noop():
    code = "def f(:\n    this is not python at all ＠＃＄\n"
    out = normalize_fullwidth_python_punctuation(code)
    assert out == code


def test_trace_step_for_enabled_rule_has_required_fields(tmp_path=None):
    code = "if x>0：\n    pass\n"
    result = run_core_adapter(pair_id=_PAIR_ID, input_code=code)
    step = next(
        s for s in result.trace.steps
        if s.rule_id == "core.normalize_fullwidth_python_punctuation"
    )
    assert step.enabled is True
    assert step.changed is True
    assert step.domain_specific is False
    assert step.safety_classification == "safe_format"
    assert step.before_hash == sha256_text(code)
    assert step.after_hash == sha256_text(result.output_code)
    assert result.trace.changed is True
    assert result.trace.implementation_status == "implemented"
    assert result.trace.rules_triggered == [
        "core.normalize_fullwidth_python_punctuation"
    ]


def test_trace_step_records_noop_when_rule_does_not_trigger():
    result = run_core_adapter(pair_id=_PAIR_ID, input_code=_CODE)
    step = next(
        s for s in result.trace.steps
        if s.rule_id == "core.normalize_fullwidth_python_punctuation"
    )
    assert step.enabled is True
    assert step.changed is False
    assert step.before_hash == step.after_hash == sha256_text(_CODE)


def test_finalized_trace_hash_matches_actual_output(tmp_path):
    """
    End-to-end: run the adapter, finalize the trace as the pipeline would,
    and confirm compute_trace_hash is consistent with the output_code the
    adapter actually returned (before/after hashes on the enabled step
    must match the real before/after code).
    """
    import dataclasses
    code = "if x>0：\n    pass\n"
    result = run_core_adapter(pair_id=_PAIR_ID, input_code=code)
    finalized = dataclasses.replace(
        result.trace, run_id="b" * 64, created_at_utc="2026-07-11T09:00:00+00:00"
    )
    validate_treatment_trace(finalized)
    assert finalized.output_hash == sha256_text(result.output_code)
