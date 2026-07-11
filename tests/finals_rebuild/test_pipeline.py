"""
Tests for agent_tools/finals_rebuild/pipeline.py

Coverage (test IDs map to the 20-test checklist in the task spec)
------------------------------------------------------------------
 1  Ab2/Ab3-Core/Ab3-Full share same raw_scaffold_id
 2  three treatments share same extracted scaffold hash
 3  scaffold extraction called only once
 4  Pipeline API cannot accept three separate scaffold raws
 5  Ab1 and Scaffold raw IDs are different
 6  pass-through output hashes same; run_ids differ
 7  bare prompt hash mismatch → fail-closed
 7  scaffold prompt hash mismatch → fail-closed
 8  pair_id mismatch → fail-closed
14  second run same input is idempotent (unchanged)
15  second run different raw raises ImmutableWriteError
16  RunMetadata output_artifact_hash matches actual treatment file
17  treatment_applied=False for all treatments
18  implementation_status="pass_through" for all treatments
19  no healer_trace file produced
20  no model/network calls
"""

from __future__ import annotations

import dataclasses
import inspect
import json
import os
import sys
import pathlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import pytest

from agent_tools.finals_rebuild.artifacts import (
    ALLOWED_TREATMENTS,
    ImmutableWriteError,
    PairMetadata,
    build_pair_id,
    pair_metadata_from_dict,
    pair_metadata_to_dict,
    sha256_text,
    sha256_bytes,
)
from agent_tools.finals_rebuild.core_adapter import run_core_adapter
from agent_tools.finals_rebuild.extraction import extract_code as _orig_extract_code
from agent_tools.finals_rebuild.trace import compute_trace_hash, validate_treatment_trace
from agent_tools.finals_rebuild.pipeline import (
    ExistingMetadataMismatchError,
    PairedPipelineInput,
    PairedPipelineResult,
    PipelineError,
    TreatmentOutput,
    run_paired_pipeline,
)

# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

_GEN_CONFIG_HASH = "c" * 64
_BARE_PROMPT = "Solve this bare math problem: 2 + 2."
_SCAFFOLD_PROMPT = "Solve this problem step-by-step with hints: 2 + 2."
_RAW_AB1 = "```python\ndef solve_ab1():\n    return 4\n```"
_RAW_SCAFFOLD = "```python\ndef solve_scaffold():\n    return 4\n```"

# ---------------------------------------------------------------------------
# Factory helper
# ---------------------------------------------------------------------------


def _make_input(
    tmp_path: pathlib.Path,
    bare_prompt: str = _BARE_PROMPT,
    scaffold_prompt: str = _SCAFFOLD_PROMPT,
    raw_ab1: str = _RAW_AB1,
    raw_scaffold: str = _RAW_SCAFFOLD,
    skill_id: str = "algebra_01",
) -> PairedPipelineInput:
    """Build a fully-consistent PairedPipelineInput for tests.

    skill_id defaults to a non-K12-math id ("algebra_01") so the Spec
    Adapter's default behaviour in most tests is a no-op; pass a
    jh_/gh_-prefixed skill_id to exercise the applicable-domain path.
    """
    bare_hash = sha256_text(bare_prompt)
    scaffold_hash = sha256_text(scaffold_prompt)
    pair_id = build_pair_id(
        study_id="test_study",
        model_id="test_model",
        model_revision="v1",
        skill_id=skill_id,
        sample_index=0,
        seed=0,
        bare_prompt_hash=bare_hash,
        scaffold_prompt_hash=scaffold_hash,
        generation_config_hash=_GEN_CONFIG_HASH,
    )
    meta = PairMetadata(
        study_id="test_study",
        pair_id=pair_id,
        model_id="test_model",
        model_revision="v1",
        skill_id=skill_id,
        sample_index=0,
        seed=0,
        bare_prompt_hash=bare_hash,
        scaffold_prompt_hash=scaffold_hash,
        generation_config_hash=_GEN_CONFIG_HASH,
        source_git_commit="2d8a0fb",
        created_at_utc="2026-07-11T08:00:00+00:00",
    )
    return PairedPipelineInput(
        pair_metadata=meta,
        bare_prompt_text=bare_prompt,
        scaffold_prompt_text=scaffold_prompt,
        raw_ab1_response=raw_ab1,
        raw_scaffold_response=raw_scaffold,
        artifact_root=tmp_path,
    )


# ============================================================
# Test 1: Ab2/Ab3-Core/Ab3-Full share same raw_scaffold_id
# ============================================================


def test_shared_treatments_use_same_raw_scaffold_id(tmp_path):
    inp = _make_input(tmp_path)
    result = run_paired_pipeline(inp)

    raw_scaffold_id = result.raw_scaffold_id
    assert raw_scaffold_id is not None

    # Verify pair_metadata.json stores this raw_ab2_id
    stored = json.loads(result.artifact_paths.pair_metadata_json.read_text())
    assert stored["raw_ab2_id"] == raw_scaffold_id


# ============================================================
# Test 2: three treatments share same extracted hash
# ============================================================


def test_shared_treatments_use_same_extracted_hash(tmp_path):
    inp = _make_input(tmp_path)
    result = run_paired_pipeline(inp)

    expected = result.extracted_scaffold_hash
    assert (
        result.treatment_outputs["ab2"].run_metadata.input_artifact_hash
        == result.treatment_outputs["ab3_core"].run_metadata.input_artifact_hash
        == result.treatment_outputs["ab3_full"].run_metadata.input_artifact_hash
        == expected
    )


# ============================================================
# Test 3: scaffold extraction called only once
# ============================================================


def test_scaffold_extraction_called_once(tmp_path, monkeypatch):
    call_log: list = []

    def spy_extract(text: str):
        call_log.append(text)
        return _orig_extract_code(text)

    monkeypatch.setattr(
        "agent_tools.finals_rebuild.pipeline.extract_code",
        spy_extract,
    )

    inp = _make_input(tmp_path)
    run_paired_pipeline(inp)

    scaffold_calls = [t for t in call_log if t == inp.raw_scaffold_response]
    assert len(scaffold_calls) == 1, (
        f"scaffold must be extracted exactly once, got {len(scaffold_calls)}"
    )
    # Ab1 raw is also extracted once
    ab1_calls = [t for t in call_log if t == inp.raw_ab1_response]
    assert len(ab1_calls) == 1


# ============================================================
# Test 4: Pipeline API enforces single scaffold raw
# ============================================================


def test_pipeline_input_has_single_scaffold_field():
    """
    PairedPipelineInput has exactly one scaffold raw field.
    There are no separate ab2_raw, ab3_core_raw, or ab3_full_raw.
    """
    field_names = {f.name for f in dataclasses.fields(PairedPipelineInput)}
    assert "raw_scaffold_response" in field_names
    for forbidden in ("raw_ab2_response", "raw_ab3_core_response",
                      "raw_ab3_full_response"):
        assert forbidden not in field_names, (
            f"Field {forbidden!r} must not exist in PairedPipelineInput"
        )


# ============================================================
# Test 5: Ab1 and Scaffold raw IDs are different
# ============================================================


def test_ab1_and_scaffold_raw_ids_differ(tmp_path):
    inp = _make_input(tmp_path)
    result = run_paired_pipeline(inp)
    assert result.raw_ab1_id != result.raw_scaffold_id


# ============================================================
# Test 6: pass-through – same output hash, different run_id
# ============================================================


def test_passthrough_same_output_hash_different_run_id(tmp_path):
    # Use identical raw for ab1 and scaffold to force ab1 output = scaffold output
    same_raw = "```python\ndef f():\n    return 1\n```"
    inp = _make_input(tmp_path, raw_ab1=same_raw, raw_scaffold=same_raw)
    result = run_paired_pipeline(inp)

    ab2 = result.treatment_outputs["ab2"]
    ab3c = result.treatment_outputs["ab3_core"]
    ab3f = result.treatment_outputs["ab3_full"]

    # All three share the same output hash (same extracted code)
    assert ab2.output_hash == ab3c.output_hash == ab3f.output_hash

    # But run_ids must differ (treatment is different)
    run_ids = {ab2.run_id, ab3c.run_id, ab3f.run_id}
    assert len(run_ids) == 3, "each treatment must have a unique run_id"


# ============================================================
# Test 7: prompt hash mismatches → fail-closed
# ============================================================


def test_bare_prompt_hash_mismatch_fails(tmp_path):
    inp = _make_input(tmp_path)
    bad = PairedPipelineInput(
        pair_metadata=inp.pair_metadata,
        bare_prompt_text="WRONG BARE PROMPT TEXT",
        scaffold_prompt_text=inp.scaffold_prompt_text,
        raw_ab1_response=inp.raw_ab1_response,
        raw_scaffold_response=inp.raw_scaffold_response,
        artifact_root=tmp_path,
    )
    with pytest.raises(PipelineError, match="bare_prompt"):
        run_paired_pipeline(bad)


def test_scaffold_prompt_hash_mismatch_fails(tmp_path):
    inp = _make_input(tmp_path)
    bad = PairedPipelineInput(
        pair_metadata=inp.pair_metadata,
        bare_prompt_text=inp.bare_prompt_text,
        scaffold_prompt_text="WRONG SCAFFOLD PROMPT TEXT",
        raw_ab1_response=inp.raw_ab1_response,
        raw_scaffold_response=inp.raw_scaffold_response,
        artifact_root=tmp_path,
    )
    with pytest.raises(PipelineError, match="scaffold_prompt"):
        run_paired_pipeline(bad)


# ============================================================
# Test 8: pair_id mismatch → fail-closed
# ============================================================


def test_pair_id_mismatch_fails(tmp_path):
    inp = _make_input(tmp_path)
    # Tamper the pair_id while keeping all other fields the same
    d = pair_metadata_to_dict(inp.pair_metadata)
    d["pair_id"] = "a" * 64  # valid SHA-256 format but wrong value
    bad_meta = pair_metadata_from_dict(d)
    bad = PairedPipelineInput(
        pair_metadata=bad_meta,
        bare_prompt_text=inp.bare_prompt_text,
        scaffold_prompt_text=inp.scaffold_prompt_text,
        raw_ab1_response=inp.raw_ab1_response,
        raw_scaffold_response=inp.raw_scaffold_response,
        artifact_root=tmp_path,
    )
    with pytest.raises(PipelineError, match="pair_id"):
        run_paired_pipeline(bad)


# ============================================================
# Test 14: second run same input is idempotent
# ============================================================


def test_second_run_same_input_is_idempotent(tmp_path):
    inp = _make_input(tmp_path)
    result1 = run_paired_pipeline(inp)
    result2 = run_paired_pipeline(inp)  # must not raise

    assert result1.pair_id == result2.pair_id
    assert result1.raw_scaffold_id == result2.raw_scaffold_id
    assert result1.extracted_scaffold_hash == result2.extracted_scaffold_hash
    assert result1.validation_status == result2.validation_status == "complete"


# ============================================================
# Test 15: second run different raw → rejected
# ============================================================


def test_second_run_different_raw_raises(tmp_path):
    inp = _make_input(tmp_path)
    run_paired_pipeline(inp)

    different_scaffold = "```python\ndef completely_different():\n    return 999\n```"
    inp2 = PairedPipelineInput(
        pair_metadata=inp.pair_metadata,
        bare_prompt_text=inp.bare_prompt_text,
        scaffold_prompt_text=inp.scaffold_prompt_text,
        raw_ab1_response=inp.raw_ab1_response,
        raw_scaffold_response=different_scaffold,
        artifact_root=tmp_path,
    )
    # With strict ID validation, a different scaffold raw produces a different
    # run_id for ab2/ab3_core/ab3_full → ExistingMetadataMismatchError.
    # If for any reason the validation order changes, ImmutableWriteError is
    # also an acceptable fail-closed signal.
    with pytest.raises((ExistingMetadataMismatchError, ImmutableWriteError)):
        run_paired_pipeline(inp2)


# ============================================================
# Test 16: RunMetadata output_artifact_hash matches actual file
# ============================================================


def test_run_metadata_output_hash_matches_file(tmp_path):
    inp = _make_input(tmp_path)
    result = run_paired_pipeline(inp)
    ap = result.artifact_paths

    for treatment, to in result.treatment_outputs.items():
        actual_bytes = ap.treatment_file(treatment).read_bytes()
        actual_hash = sha256_bytes(actual_bytes)
        assert actual_hash == to.run_metadata.output_artifact_hash, (
            f"{treatment}: file hash {actual_hash!r} "
            f"≠ metadata hash {to.run_metadata.output_artifact_hash!r}"
        )


# ============================================================
# Test 17: treatment_applied=False for all treatments
# ============================================================


def test_treatment_applied_is_false(tmp_path):
    """
    Ab1/Ab2 remain pure pass-through (treatment_applied=False). Ab3-Core
    always runs the Core Adapter (treatment_applied=True, even though
    Commit 3A has no enabled rule so changed=False). Ab3-Full's
    treatment_applied reflects Spec applicability for this skill_id; the
    fixture's "algebra_01" skill_id is not K12-math, so Spec is a no-op.
    """
    inp = _make_input(tmp_path)
    result = run_paired_pipeline(inp)

    for treatment in ("ab1", "ab2"):
        to = result.treatment_outputs[treatment]
        assert to.treatment_applied is False, (
            f"{treatment}: treatment_applied must be False in pass-through"
        )
        assert to.changed is False, (
            f"{treatment}: changed must be False in pass-through"
        )

    core_to = result.treatment_outputs["ab3_core"]
    assert core_to.treatment_applied is True
    assert core_to.changed is False  # no rule enabled in Commit 3A

    full_to = result.treatment_outputs["ab3_full"]
    assert full_to.treatment_applied is False  # non-K12-math skill_id → no-op
    assert full_to.changed is False


# ============================================================
# Test 18: implementation_status="pass_through" for all treatments
# ============================================================


def test_implementation_status_is_pass_through(tmp_path):
    inp = _make_input(tmp_path)
    result = run_paired_pipeline(inp)

    for treatment in ("ab1", "ab2"):
        to = result.treatment_outputs[treatment]
        assert to.implementation_status == "pass_through", (
            f"{treatment}: expected 'pass_through', "
            f"got {to.implementation_status!r}"
        )

    # Core Adapter ran (no enabled rule triggered in Commit 3A).
    assert (
        result.treatment_outputs["ab3_core"].implementation_status
        == "implemented_no_safe_rule_triggered"
    )
    # Spec Adapter is a no-op for this fixture's non-K12-math skill_id.
    assert (
        result.treatment_outputs["ab3_full"].implementation_status
        == "not_applicable"
    )


# ============================================================
# Test 19: no healer_trace file produced
# ============================================================


def test_no_healer_trace_produced(tmp_path):
    inp = _make_input(tmp_path)
    result = run_paired_pipeline(inp)
    assert not result.artifact_paths.healer_trace.exists(), (
        "healer_trace.json must not be created during pass-through"
    )


# ============================================================
# Test 20: no model / network calls
# ============================================================


def test_no_model_or_network_calls(tmp_path):
    """
    Structural check: pipeline module must not import AI client packages.
    Functional check: runs to completion without any API key or network.
    """
    import agent_tools.finals_rebuild.pipeline as pipe_mod

    source = inspect.getsource(pipe_mod)
    for forbidden in (
        "google.generativeai",
        "openai",
        "anthropic",
        "call_ai_with_retry",
        "ASTHealer",
        "RegexHealer",
        "heal_minimal",
    ):
        assert forbidden not in source, (
            f"pipeline.py must not reference {forbidden!r}"
        )

    # Functional: completes without network
    inp = _make_input(tmp_path)
    result = run_paired_pipeline(inp)
    assert result.validation_status == "complete"


# ============================================================
# Additional: artifact layout verification
# ============================================================


def test_all_expected_artifacts_are_written(tmp_path):
    inp = _make_input(tmp_path)
    result = run_paired_pipeline(inp)
    ap = result.artifact_paths

    assert ap.pair_metadata_json.exists()
    assert ap.prompt_ab1.exists()
    assert ap.prompt_ab2.exists()
    assert ap.raw_ab1.exists()
    assert ap.raw_ab2.exists()
    assert ap.extracted_ab1.exists()
    assert ap.extracted_ab2.exists()
    for treatment in ALLOWED_TREATMENTS:
        assert ap.treatment_file(treatment).exists(), (
            f"treatment file missing: {treatment}"
        )
        assert ap.run_metadata_json(treatment).exists(), (
            f"run metadata missing: {treatment}"
        )


def test_extracted_ab1_content_matches_hash(tmp_path):
    inp = _make_input(tmp_path)
    result = run_paired_pipeline(inp)
    ap = result.artifact_paths

    ab1_bytes = ap.extracted_ab1.read_bytes()
    assert sha256_bytes(ab1_bytes) == result.extracted_ab1_hash


def test_extracted_scaffold_is_shared_by_three_treatments(tmp_path):
    """
    extracted_ab2.py content must equal the treatment output for
    ab2, ab3_core, and ab3_full in pass-through mode.
    """
    inp = _make_input(tmp_path)
    result = run_paired_pipeline(inp)
    ap = result.artifact_paths

    scaffold_content = ap.extracted_ab2.read_bytes()
    scaffold_hash = sha256_bytes(scaffold_content)

    for treatment in ("ab2", "ab3_core", "ab3_full"):
        to = result.treatment_outputs[treatment]
        assert to.output_hash == scaffold_hash, (
            f"{treatment}: output_hash should match extracted_scaffold"
        )


def test_run_metadata_json_files_are_valid(tmp_path):
    """run metadata JSON for each treatment must be parseable and consistent."""
    inp = _make_input(tmp_path)
    result = run_paired_pipeline(inp)
    ap = result.artifact_paths

    expected_status = {
        "ab1": "pass_through",
        "ab2": "pass_through",
        "ab3_core": "implemented_no_safe_rule_triggered",
        "ab3_full": "not_applicable",  # non-K12-math skill_id in this fixture
    }
    expected_applied = {
        "ab1": False,
        "ab2": False,
        "ab3_core": True,
        "ab3_full": False,
    }
    for treatment in ALLOWED_TREATMENTS:
        raw_json = ap.run_metadata_json(treatment).read_text(encoding="utf-8")
        stored = json.loads(raw_json)
        assert stored["treatment"] == treatment
        assert stored["pair_id"] == result.pair_id
        assert stored["treatment_applied"] is expected_applied[treatment]
        assert stored["implementation_status"] == expected_status[treatment]


# ============================================================
# Fix 1: ExistingMetadataMismatchError on tampered metadata
# ============================================================


def test_existing_metadata_pair_id_mismatch_raises(tmp_path):
    """If existing run metadata has wrong pair_id, pipeline fails closed."""
    inp = _make_input(tmp_path)
    result = run_paired_pipeline(inp)

    meta_path = result.artifact_paths.run_metadata_json("ab1")
    stored = json.loads(meta_path.read_text())
    stored["pair_id"] = "a" * 64   # tampered (valid SHA-256 format, wrong value)
    meta_path.write_text(json.dumps(stored, sort_keys=True, indent=2) + "\n")

    with pytest.raises(ExistingMetadataMismatchError, match="pair_id"):
        run_paired_pipeline(inp)


def test_existing_metadata_run_id_mismatch_raises(tmp_path):
    """If existing run metadata has wrong run_id, pipeline fails closed."""
    inp = _make_input(tmp_path)
    result = run_paired_pipeline(inp)

    meta_path = result.artifact_paths.run_metadata_json("ab1")
    stored = json.loads(meta_path.read_text())
    stored["run_id"] = "b" * 64   # tampered
    meta_path.write_text(json.dumps(stored, sort_keys=True, indent=2) + "\n")

    with pytest.raises(ExistingMetadataMismatchError, match="run_id"):
        run_paired_pipeline(inp)


def test_existing_metadata_corrupt_json_raises(tmp_path):
    """If existing run metadata contains invalid JSON, pipeline fails closed."""
    inp = _make_input(tmp_path)
    result = run_paired_pipeline(inp)

    meta_path = result.artifact_paths.run_metadata_json("ab1")
    meta_path.write_text("{ not valid json at all }")

    with pytest.raises(ExistingMetadataMismatchError):
        run_paired_pipeline(inp)


# ============================================================
# Fix 3: pipeline fails closed on empty fenced extraction
# ============================================================


def test_pipeline_fails_on_empty_fenced_ab1(tmp_path):
    """If ab1 raw contains an empty python fence, pipeline must fail closed."""
    empty_raw = "```python\n```"
    inp = _make_input(tmp_path, raw_ab1=empty_raw)
    with pytest.raises(PipelineError):
        run_paired_pipeline(inp)


def test_pipeline_fails_on_empty_fenced_scaffold(tmp_path):
    """If scaffold raw contains an empty python fence, pipeline must fail closed."""
    empty_raw = "```python\n   \n```"
    inp = _make_input(tmp_path, raw_scaffold=empty_raw)
    with pytest.raises(PipelineError):
        run_paired_pipeline(inp)


# ============================================================
# Commit 3A: Core → Spec adapter chain
# ============================================================


def test_ab2_does_not_invoke_core_or_spec(tmp_path, monkeypatch):
    calls = []
    import agent_tools.finals_rebuild.pipeline as pipe_mod

    orig_core = pipe_mod.run_core_adapter
    orig_spec = pipe_mod.run_spec_adapter

    def spy_core(**kwargs):
        calls.append("core")
        return orig_core(**kwargs)

    def spy_spec(**kwargs):
        calls.append("spec")
        return orig_spec(**kwargs)

    monkeypatch.setattr(pipe_mod, "run_core_adapter", spy_core)
    monkeypatch.setattr(pipe_mod, "run_spec_adapter", spy_spec)

    inp = _make_input(tmp_path)
    result = run_paired_pipeline(inp)

    # Ab2 is untouched pass-through content, identical to extracted scaffold.
    ab2_code = result.artifact_paths.extracted_ab2.read_text(encoding="utf-8")
    assert result.treatment_outputs["ab2"].output_code == ab2_code
    assert result.treatment_outputs["ab2"].trace is None

    # Core/Spec run exactly once each (for ab3_core / ab3_full), never twice
    # and never on behalf of ab2.
    assert calls == ["core", "spec"]


def test_core_input_hash_equals_scaffold_extracted_hash(tmp_path):
    inp = _make_input(tmp_path)
    result = run_paired_pipeline(inp)
    core_trace = result.treatment_outputs["ab3_core"].trace
    assert core_trace.input_hash == result.extracted_scaffold_hash


def test_spec_input_hash_equals_core_output_hash(tmp_path):
    inp = _make_input(tmp_path)
    result = run_paired_pipeline(inp)
    core_trace = result.treatment_outputs["ab3_core"].trace
    spec_trace = result.treatment_outputs["ab3_full"].trace
    assert spec_trace.input_hash == core_trace.output_hash


def test_core_runs_exactly_once(tmp_path, monkeypatch):
    import agent_tools.finals_rebuild.pipeline as pipe_mod

    call_count = {"n": 0}
    orig_core = pipe_mod.run_core_adapter

    def spy_core(**kwargs):
        call_count["n"] += 1
        return orig_core(**kwargs)

    monkeypatch.setattr(pipe_mod, "run_core_adapter", spy_core)
    inp = _make_input(tmp_path)
    run_paired_pipeline(inp)
    assert call_count["n"] == 1


def test_spec_runs_exactly_once(tmp_path, monkeypatch):
    import agent_tools.finals_rebuild.pipeline as pipe_mod

    call_count = {"n": 0}
    orig_spec = pipe_mod.run_spec_adapter

    def spy_spec(**kwargs):
        call_count["n"] += 1
        return orig_spec(**kwargs)

    monkeypatch.setattr(pipe_mod, "run_spec_adapter", spy_spec)
    inp = _make_input(tmp_path)
    run_paired_pipeline(inp)
    assert call_count["n"] == 1


def test_core_trace_has_no_enabled_domain_specific_step(tmp_path):
    inp = _make_input(tmp_path, skill_id="jh_數學1上_FourArithmeticOperationsOfIntegers")
    result = run_paired_pipeline(inp)
    core_trace = result.treatment_outputs["ab3_core"].trace
    for step in core_trace.steps:
        assert not (step.enabled and step.domain_specific)


def test_only_one_known_safe_core_rule_is_enabled_all_spec_disabled(tmp_path):
    """
    Commit 3B-1: exactly one Core rule (the safe_format punctuation
    normaliser) is enabled; every other Core rule and every Spec rule
    remains disabled.
    """
    inp = _make_input(tmp_path, skill_id="jh_數學1上_FourArithmeticOperationsOfIntegers")
    result = run_paired_pipeline(inp)

    core_trace = result.treatment_outputs["ab3_core"].trace
    enabled_core_steps = [s for s in core_trace.steps if s.enabled]
    assert len(enabled_core_steps) == 1
    assert enabled_core_steps[0].rule_id == "core.normalize_fullwidth_python_punctuation"
    assert enabled_core_steps[0].safety_classification == "safe_format"
    assert enabled_core_steps[0].domain_specific is False

    spec_trace = result.treatment_outputs["ab3_full"].trace
    for step in spec_trace.steps:
        assert step.enabled is False, (
            f"ab3_full: rule {step.rule_id!r} must be disabled"
        )


def test_pipeline_never_calls_regex_or_ast_healer_directly(tmp_path):
    """
    Structural check: pipeline.py must not import or call the legacy
    Healer classes/methods it is explicitly forbidden from touching.
    """
    import agent_tools.finals_rebuild.pipeline as pipe_mod
    source = inspect.getsource(pipe_mod)
    for forbidden in (
        "RegexHealer",
        "ASTHealer",
        "AntiDuplicationHealer",
        "UnifiedCleanupHealer",
        "heal_minimal",
        "heal_unified",
        ".heal(",
        "semantic_heal",
        "google.generativeai",
        "openai",
        "anthropic",
        "call_ai_with_retry",
    ):
        assert forbidden not in source, f"pipeline.py must not contain {forbidden!r}"


def test_no_generate_fallback_in_output(tmp_path):
    inp = _make_input(tmp_path, skill_id="jh_數學1上_FourArithmeticOperationsOfIntegers")
    result = run_paired_pipeline(inp)
    for treatment in ("ab3_core", "ab3_full"):
        code = result.treatment_outputs[treatment].output_code
        assert "Fallback due to missing generate() wrapper" not in code
        assert "\\text{Failed}" not in code


def test_non_math_domain_spec_is_applicable_false_changed_false(tmp_path):
    inp = _make_input(tmp_path, skill_id="algebra_01")
    result = run_paired_pipeline(inp)
    spec_trace = result.treatment_outputs["ab3_full"].trace
    assert spec_trace.applicable is False
    assert spec_trace.changed is False
    assert spec_trace.implementation_status == "not_applicable"


def test_k12_math_domain_spec_has_no_safe_rule_yet(tmp_path):
    inp = _make_input(tmp_path, skill_id="gh_ApplicationsOfDerivatives")
    result = run_paired_pipeline(inp)
    spec_trace = result.treatment_outputs["ab3_full"].trace
    assert spec_trace.applicable is True
    assert spec_trace.changed is False
    assert spec_trace.implementation_status == "implemented_no_safe_rule_triggered"


def test_trace_hashes_match_actual_artifact_bytes(tmp_path):
    inp = _make_input(tmp_path, skill_id="jh_math_skill")
    result = run_paired_pipeline(inp)
    ap = result.artifact_paths
    for treatment in ("ab3_core", "ab3_full"):
        trace_bytes = ap.trace_json(treatment).read_bytes()
        actual_hash = sha256_bytes(trace_bytes)
        assert actual_hash == result.treatment_outputs[treatment].run_metadata.trace_hash


def test_core_adapter_trace_hash_consistent_when_rule_actually_fires():
    """
    Requirement 8 (trace hash matches actual output) exercised on a case
    where the Commit 3B-1 punctuation rule actually changes the code, at
    the adapter level.

    NOTE: a full pipeline-level version of this test is intentionally
    NOT included here. Running raw scaffold text containing fullwidth
    punctuation through run_paired_pipeline() surfaces a pre-existing
    invariant bug in artifacts.validate_shared_run_identity(), which
    assumes ab2 / ab3_core / ab3_full always share the same
    input_artifact_hash. That assumption silently held throughout Commit
    3A only because no Core rule ever changed anything; now that Spec's
    input (Core's output) can genuinely diverge from ab2/ab3_core's input
    once Core makes a real edit, that shared-identity check fails.
    artifacts.py is outside this commit's allowed file list, so this is
    reported as a follow-up rather than patched here.
    """
    import dataclasses

    code = "def solve_scaffold(x)：\n    return x\n"
    result = run_core_adapter(pair_id="a" * 64, input_code=code)
    assert result.trace.changed is True

    finalized = dataclasses.replace(
        result.trace, run_id="b" * 64, created_at_utc="2026-07-11T09:00:00+00:00"
    )
    validate_treatment_trace(finalized)
    trace_hash = compute_trace_hash(finalized)
    # Recomputing from the same (now-finalized) trace object must be stable.
    assert trace_hash == compute_trace_hash(finalized)
    assert finalized.output_hash == sha256_text(result.output_code)


def test_run_metadata_trace_hash_matches_trace_json(tmp_path):
    inp = _make_input(tmp_path, skill_id="jh_math_skill")
    result = run_paired_pipeline(inp)
    ap = result.artifact_paths
    for treatment in ("ab3_core", "ab3_full"):
        stored_meta = json.loads(ap.run_metadata_json(treatment).read_text(encoding="utf-8"))
        trace_bytes = ap.trace_json(treatment).read_bytes()
        assert stored_meta["trace_hash"] == sha256_bytes(trace_bytes)


def test_ab1_and_ab2_have_no_trace_json(tmp_path):
    inp = _make_input(tmp_path, skill_id="jh_math_skill")
    result = run_paired_pipeline(inp)
    ap = result.artifact_paths
    for treatment in ("ab1", "ab2"):
        assert not ap.trace_json(treatment).exists()


def test_second_run_same_input_trace_json_is_idempotent(tmp_path):
    inp = _make_input(tmp_path, skill_id="jh_math_skill")
    result1 = run_paired_pipeline(inp)
    trace_bytes_1 = {
        t: result1.artifact_paths.trace_json(t).read_bytes()
        for t in ("ab3_core", "ab3_full")
    }
    result2 = run_paired_pipeline(inp)  # must not raise
    trace_bytes_2 = {
        t: result2.artifact_paths.trace_json(t).read_bytes()
        for t in ("ab3_core", "ab3_full")
    }
    assert trace_bytes_1 == trace_bytes_2


def test_core_and_spec_run_ids_differ_and_bind_own_output(tmp_path):
    inp = _make_input(tmp_path, skill_id="jh_math_skill")
    result = run_paired_pipeline(inp)
    core_to = result.treatment_outputs["ab3_core"]
    full_to = result.treatment_outputs["ab3_full"]
    assert core_to.run_id != full_to.run_id
    assert core_to.trace.run_id == core_to.run_id
    assert full_to.trace.run_id == full_to.run_id
    assert core_to.trace.output_hash == core_to.output_hash
    assert full_to.trace.output_hash == full_to.output_hash


def test_all_87_plus_new_tests_still_pass_smoke(tmp_path):
    """
    Smoke test: a full pipeline run with a K12-math skill_id completes and
    produces a fully self-consistent artifact tree (existing invariants +
    Commit 3A additions all hold simultaneously).
    """
    inp = _make_input(tmp_path, skill_id="jh_math_skill")
    result = run_paired_pipeline(inp)
    assert result.validation_status == "complete"
    ap = result.artifact_paths
    for treatment in ALLOWED_TREATMENTS:
        assert ap.treatment_file(treatment).exists()
        assert ap.run_metadata_json(treatment).exists()
    assert ap.trace_json("ab3_core").exists()
    assert ap.trace_json("ab3_full").exists()
