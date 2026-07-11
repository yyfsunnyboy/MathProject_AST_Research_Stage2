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
from agent_tools.finals_rebuild.evaluation import (
    compute_evaluation_hash,
    evaluation_result_to_dict,
    validate_evaluation_result,
)
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

# Deliberately DIFFERENT from PairMetadata.source_git_commit ("2d8a0fb" in
# _make_input below) — proves evaluator_git_commit is an independent fact,
# not silently aliased to source_git_commit.
_EVALUATOR_GIT_COMMIT = "e3d2e1b"

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
    evaluator_git_commit: str = _EVALUATOR_GIT_COMMIT,
) -> PairedPipelineInput:
    """Build a fully-consistent PairedPipelineInput for tests.

    skill_id defaults to a non-K12-math id ("algebra_01") so the Spec
    Adapter's default behaviour in most tests is a no-op; pass a
    jh_/gh_-prefixed skill_id to exercise the applicable-domain path.

    evaluator_git_commit defaults to a value distinct from
    PairMetadata.source_git_commit ("2d8a0fb" below), proving the pipeline
    keeps them as independent facts rather than aliasing one to the other.
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
        evaluator_git_commit=evaluator_git_commit,
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
        evaluator_git_commit=inp.evaluator_git_commit,
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
        evaluator_git_commit=inp.evaluator_git_commit,
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
        evaluator_git_commit=inp.evaluator_git_commit,
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
        evaluator_git_commit=inp.evaluator_git_commit,
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


# ============================================================
# Treatment chain identity — full pipeline, Core actually changed
#
# Restores/extends the paired invariants that a stale
# validate_shared_run_identity() (fixed in artifacts.py:
# validate_treatment_chain_identity()) used to reject whenever Core
# Adapter made a real edit. These run the FULL pipeline, not just the
# adapter in isolation.
# ============================================================


def _make_input_with_fullwidth_scaffold(tmp_path, skill_id="jh_math_skill"):
    """Scaffold raw whose def-line trailing colon is fullwidth '：', which
    the Commit 3B-1 punctuation rule will normalize — i.e. this forces
    Core Adapter to have changed=True."""
    raw_with_fullwidth = "```python\ndef solve_scaffold(x)：\n    return x\n```"
    return _make_input(
        tmp_path, skill_id=skill_id, raw_scaffold=raw_with_fullwidth
    )


def test_1_fullwidth_scaffold_makes_core_actually_changed(tmp_path):
    inp = _make_input_with_fullwidth_scaffold(tmp_path)
    result = run_paired_pipeline(inp)
    core_trace = result.treatment_outputs["ab3_core"].trace
    assert core_trace.changed is True


def test_2_full_pipeline_succeeds_when_core_changes_code(tmp_path):
    inp = _make_input_with_fullwidth_scaffold(tmp_path)
    result = run_paired_pipeline(inp)  # must not raise
    assert result.validation_status == "complete"


def test_3_ab2_input_equals_extracted_scaffold_hash(tmp_path):
    inp = _make_input_with_fullwidth_scaffold(tmp_path)
    result = run_paired_pipeline(inp)
    ab2_meta = result.treatment_outputs["ab2"].run_metadata
    assert ab2_meta.input_artifact_hash == result.extracted_scaffold_hash


def test_4_ab3_core_input_equals_extracted_scaffold_hash(tmp_path):
    inp = _make_input_with_fullwidth_scaffold(tmp_path)
    result = run_paired_pipeline(inp)
    ab3c_meta = result.treatment_outputs["ab3_core"].run_metadata
    assert ab3c_meta.input_artifact_hash == result.extracted_scaffold_hash


def test_5_ab3_full_input_equals_ab3_core_output(tmp_path):
    inp = _make_input_with_fullwidth_scaffold(tmp_path)
    result = run_paired_pipeline(inp)
    ab3c_meta = result.treatment_outputs["ab3_core"].run_metadata
    ab3f_meta = result.treatment_outputs["ab3_full"].run_metadata
    assert ab3f_meta.input_artifact_hash == ab3c_meta.output_artifact_hash


def test_6_ab3_core_output_differs_from_ab2_output_when_core_changed(tmp_path):
    inp = _make_input_with_fullwidth_scaffold(tmp_path)
    result = run_paired_pipeline(inp)
    ab2_out = result.treatment_outputs["ab2"].output_hash
    ab3c_out = result.treatment_outputs["ab3_core"].output_hash
    assert ab3c_out != ab2_out


def test_7_spec_noop_means_ab3_full_output_equals_ab3_core_output(tmp_path):
    """Spec Adapter has zero enabled rules in this commit, so whenever it
    runs (applicable or not), its output must equal whatever it was
    handed — Core's output — byte for byte."""
    inp = _make_input_with_fullwidth_scaffold(tmp_path)
    result = run_paired_pipeline(inp)
    ab3c_out = result.treatment_outputs["ab3_core"].output_hash
    ab3f_out = result.treatment_outputs["ab3_full"].output_hash
    assert ab3f_out == ab3c_out


def test_8_each_run_id_binds_its_own_output_hash(tmp_path):
    from agent_tools.finals_rebuild.artifacts import build_run_id

    inp = _make_input_with_fullwidth_scaffold(tmp_path)
    result = run_paired_pipeline(inp)
    for treatment in ("ab2", "ab3_core", "ab3_full"):
        meta = result.treatment_outputs[treatment].run_metadata
        expected_run_id = build_run_id(
            meta.pair_id, treatment, meta.output_artifact_hash
        )
        assert meta.run_id == expected_run_id
    run_ids = {
        result.treatment_outputs[t].run_metadata.run_id
        for t in ("ab2", "ab3_core", "ab3_full")
    }
    assert len(run_ids) == 3  # all distinct, since output hashes differ


def test_9_tampered_ab3_full_input_hash_fails_chain_validation(tmp_path):
    """
    Direct unit-level counterpart of the pipeline invariant: feeding the
    real validator a deliberately wrong ab3_full.input_artifact_hash (not
    equal to ab3_core's output) must raise, proving validation is not
    silently satisfied by construction.
    """
    from agent_tools.finals_rebuild.artifacts import (
        RunMetadata,
        build_run_id,
        validate_treatment_chain_identity,
    )

    inp = _make_input_with_fullwidth_scaffold(tmp_path)
    result = run_paired_pipeline(inp)
    ab2_meta = result.treatment_outputs["ab2"].run_metadata
    ab3c_meta = result.treatment_outputs["ab3_core"].run_metadata
    ab3f_meta = result.treatment_outputs["ab3_full"].run_metadata

    wrong_input_hash = "9" * 64
    assert wrong_input_hash != ab3c_meta.output_artifact_hash
    tampered_ab3f = dataclasses.replace(
        ab3f_meta,
        input_artifact_hash=wrong_input_hash,
        run_id=build_run_id(
            ab3f_meta.pair_id, "ab3_full", ab3f_meta.output_artifact_hash
        ),
    )
    with pytest.raises(ValueError, match="ab3_core.output_artifact_hash"):
        validate_treatment_chain_identity(ab2_meta, ab3c_meta, tampered_ab3f)


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


# ============================================================
# Commit 4A: static evaluation.json for all four treatments
# ============================================================


def test_9_all_four_treatments_produce_evaluation_json(tmp_path):
    inp = _make_input(tmp_path, skill_id="jh_math_skill")
    result = run_paired_pipeline(inp)
    ap = result.artifact_paths
    for treatment in ALLOWED_TREATMENTS:
        assert ap.run_evaluation_json(treatment).exists()


def test_10_evaluation_pair_id_and_run_id_match_run_metadata(tmp_path):
    inp = _make_input(tmp_path, skill_id="jh_math_skill")
    result = run_paired_pipeline(inp)
    ap = result.artifact_paths
    for treatment in ALLOWED_TREATMENTS:
        eval_json = json.loads(
            ap.run_evaluation_json(treatment).read_text(encoding="utf-8")
        )
        run_meta = result.treatment_outputs[treatment].run_metadata
        assert eval_json["pair_id"] == run_meta.pair_id
        assert eval_json["run_id"] == run_meta.run_id
        assert eval_json["treatment"] == treatment


def test_11_evaluation_artifact_hash_matches_actual_treatment_file(tmp_path):
    inp = _make_input(tmp_path, skill_id="jh_math_skill")
    result = run_paired_pipeline(inp)
    ap = result.artifact_paths
    for treatment in ALLOWED_TREATMENTS:
        eval_json = json.loads(
            ap.run_evaluation_json(treatment).read_text(encoding="utf-8")
        )
        actual_bytes = ap.treatment_file(treatment).read_bytes()
        assert eval_json["artifact_hash"] == sha256_bytes(actual_bytes)


def test_12_evaluation_json_immutable_rerun_unchanged(tmp_path):
    inp = _make_input(tmp_path, skill_id="jh_math_skill")
    result1 = run_paired_pipeline(inp)
    eval_bytes_1 = {
        t: result1.artifact_paths.run_evaluation_json(t).read_bytes()
        for t in ALLOWED_TREATMENTS
    }
    result2 = run_paired_pipeline(inp)  # must not raise
    eval_bytes_2 = {
        t: result2.artifact_paths.run_evaluation_json(t).read_bytes()
        for t in ALLOWED_TREATMENTS
    }
    assert eval_bytes_1 == eval_bytes_2


def test_13_evaluation_json_cannot_be_silently_overwritten(tmp_path):
    inp = _make_input(tmp_path, skill_id="jh_math_skill")
    result = run_paired_pipeline(inp)
    eval_path = result.artifact_paths.run_evaluation_json("ab1")
    eval_path.write_text('{"tampered": true}', encoding="utf-8")

    # Re-running must fail closed rather than silently accept different
    # content at the same immutable path. The pipeline reuses an existing
    # evaluation.json on idempotent re-runs (bounded execution is not
    # deterministic — see _read_existing_evaluation in pipeline.py), so
    # tampered/incomplete content is caught by that consistency check
    # (ExistingMetadataMismatchError) before immutable_write_json would
    # even be reached; either fail-closed signal is acceptable.
    with pytest.raises((ImmutableWriteError, ExistingMetadataMismatchError)):
        run_paired_pipeline(inp)


# ============================================================
# Fix: evaluation reuse validation (evaluator_git_commit /
# evaluator_config_hash / isolation_level / missing fields)
# ============================================================


def _tamper_evaluation_field(eval_path, field_name, new_value):
    stored = json.loads(eval_path.read_text(encoding="utf-8"))
    stored[field_name] = new_value
    eval_path.write_text(json.dumps(stored, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _delete_evaluation_field(eval_path, field_name):
    stored = json.loads(eval_path.read_text(encoding="utf-8"))
    del stored[field_name]
    eval_path.write_text(json.dumps(stored, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def test_reuse_rejects_different_evaluator_git_commit(tmp_path):
    inp = _make_input(tmp_path, skill_id="jh_math_skill")
    result = run_paired_pipeline(inp)
    eval_path = result.artifact_paths.run_evaluation_json("ab1")
    _tamper_evaluation_field(eval_path, "evaluator_git_commit", "totally-different-commit")

    with pytest.raises(ExistingMetadataMismatchError, match="evaluator_git_commit"):
        run_paired_pipeline(inp)


def test_reuse_rejects_different_evaluator_config_hash(tmp_path):
    inp = _make_input(tmp_path, skill_id="jh_math_skill")
    result = run_paired_pipeline(inp)
    eval_path = result.artifact_paths.run_evaluation_json("ab1")
    _tamper_evaluation_field(eval_path, "evaluator_config_hash", "f" * 64)

    with pytest.raises(ExistingMetadataMismatchError, match="evaluator_config_hash"):
        run_paired_pipeline(inp)


def test_reuse_rejects_different_isolation_level(tmp_path):
    inp = _make_input(tmp_path, skill_id="jh_math_skill")
    result = run_paired_pipeline(inp)
    eval_path = result.artifact_paths.run_evaluation_json("ab1")
    _tamper_evaluation_field(eval_path, "isolation_level", "some_other_isolation_level")

    with pytest.raises(ExistingMetadataMismatchError, match="isolation_level"):
        run_paired_pipeline(inp)


def test_reuse_rejects_missing_required_field(tmp_path):
    inp = _make_input(tmp_path, skill_id="jh_math_skill")
    result = run_paired_pipeline(inp)
    eval_path = result.artifact_paths.run_evaluation_json("ab1")
    _delete_evaluation_field(eval_path, "evaluator_config_hash")

    with pytest.raises(ExistingMetadataMismatchError, match="evaluator_config_hash"):
        run_paired_pipeline(inp)


def test_reuse_never_falls_back_to_none_and_reexecute_on_mismatch(tmp_path):
    """
    A mismatch must always be an explicit, fail-closed error — never a
    silent None-return that triggers a fresh execution and a subsequent
    ImmutableWriteError from writing conflicting content to the same
    already-tampered path in a confusing way. Confirms the specific
    exception type/message, not just "some exception".
    """
    inp = _make_input(tmp_path, skill_id="jh_math_skill")
    result = run_paired_pipeline(inp)
    eval_path = result.artifact_paths.run_evaluation_json("ab2")
    _tamper_evaluation_field(eval_path, "pair_id", "1" * 64)

    with pytest.raises(ExistingMetadataMismatchError, match="pair_id"):
        run_paired_pipeline(inp)


def test_identical_evaluation_reuses_cleanly(tmp_path):
    """Fully identical evaluation.json content (an untouched idempotent
    re-run) must reuse without error and without any field changing."""
    inp = _make_input(tmp_path, skill_id="jh_math_skill")
    result1 = run_paired_pipeline(inp)
    result2 = run_paired_pipeline(inp)  # must not raise

    for treatment in ALLOWED_TREATMENTS:
        ev1 = result1.treatment_outputs[treatment].evaluation
        ev2 = result2.treatment_outputs[treatment].evaluation
        assert ev1 == ev2


def test_14_full_pipeline_passes_when_core_actually_changed_with_evaluation(tmp_path):
    """
    Restores the paired invariant across the FULL evaluation feature: a
    scaffold raw that makes Core Adapter actually change code must still
    produce a fully self-consistent evaluation.json for all four
    treatments, with RunMetadata.evaluation_hash matching on-disk bytes.
    """
    raw_with_fullwidth = "```python\ndef solve_scaffold(x)：\n    return x\n```"
    inp = _make_input(
        tmp_path, skill_id="jh_math_skill", raw_scaffold=raw_with_fullwidth
    )
    result = run_paired_pipeline(inp)
    assert result.validation_status == "complete"

    core_trace = result.treatment_outputs["ab3_core"].trace
    assert core_trace.changed is True

    ap = result.artifact_paths
    # ab1/ab2 are pass-through: they still contain the raw fullwidth colon,
    # so their static evaluation correctly reports syntax_pass=False. Only
    # ab3_core/ab3_full (post-Core-Adapter) have valid Python.
    expected_syntax_pass = {
        "ab1": True,  # ab1's raw has no fullwidth punctuation
        "ab2": False,
        "ab3_core": True,
        "ab3_full": True,
    }
    for treatment in ALLOWED_TREATMENTS:
        to = result.treatment_outputs[treatment]
        assert to.evaluation is not None
        validate_evaluation_result(to.evaluation)
        assert to.evaluation.syntax_pass is expected_syntax_pass[treatment], (
            f"{treatment}: expected syntax_pass={expected_syntax_pass[treatment]}, "
            f"got {to.evaluation.syntax_pass}"
        )

        eval_bytes = ap.run_evaluation_json(treatment).read_bytes()
        assert sha256_bytes(eval_bytes) == to.run_metadata.evaluation_hash
        assert sha256_bytes(eval_bytes) == compute_evaluation_hash(to.evaluation)


def test_run_metadata_never_rewritten_to_add_evaluation_hash(tmp_path):
    """
    RunMetadata is written exactly once per treatment (immutable_write_json
    returns "written" the first time), and evaluation_hash is already
    correct on that first write — this test asserts the run metadata file
    is not touched a second time by evaluation.json's own write.
    """
    inp = _make_input(tmp_path, skill_id="jh_math_skill")
    result = run_paired_pipeline(inp)
    ap = result.artifact_paths
    run_meta_bytes_after_first_run = {
        t: ap.run_metadata_json(t).read_bytes() for t in ALLOWED_TREATMENTS
    }

    # Second (idempotent) run must not alter any run metadata file, and
    # every RunMetadata.evaluation_hash must already be non-None (i.e. it
    # was correct on the very first write, never patched in afterward).
    result2 = run_paired_pipeline(inp)
    for treatment in ALLOWED_TREATMENTS:
        assert (
            ap.run_metadata_json(treatment).read_bytes()
            == run_meta_bytes_after_first_run[treatment]
        )
        assert result2.treatment_outputs[treatment].run_metadata.evaluation_hash is not None


def test_evaluation_result_test_and_mcri_fields_are_not_run(tmp_path):
    """
    Commit 4B adds real execution (execution_status is now "success" for
    ordinary code), but test_status/mcri_* remain "not_run"/None — no
    test cases are run and no MCRI is computed this commit.
    """
    inp = _make_input(tmp_path, skill_id="jh_math_skill")
    result = run_paired_pipeline(inp)
    for treatment in ALLOWED_TREATMENTS:
        ev = result.treatment_outputs[treatment].evaluation
        assert ev.test_status == "not_run"
        assert ev.test_pass is None
        assert ev.tests_passed is None
        assert ev.tests_total is None
        assert ev.mcri_code is None
        assert ev.mcri_math is None


# ============================================================
# Commit 4B: bounded execution evaluator, full pipeline
# ============================================================


def test_evaluator_git_commit_differs_from_source_git_commit(tmp_path):
    inp = _make_input(tmp_path, skill_id="jh_math_skill")
    assert inp.pair_metadata.source_git_commit != inp.evaluator_git_commit

    result = run_paired_pipeline(inp)
    for treatment in ALLOWED_TREATMENTS:
        ev = result.treatment_outputs[treatment].evaluation
        assert ev.evaluator_git_commit == inp.evaluator_git_commit
        assert ev.evaluator_git_commit != inp.pair_metadata.source_git_commit
        # RunMetadata.source_git_commit is unaffected — still the
        # generation commit, never silently swapped for the evaluator's.
        run_meta = result.treatment_outputs[treatment].run_metadata
        assert run_meta.source_git_commit == inp.pair_metadata.source_git_commit


def test_all_four_treatments_get_independent_execution_results(tmp_path):
    inp = _make_input(tmp_path, skill_id="jh_math_skill")
    result = run_paired_pipeline(inp)
    statuses = {
        t: result.treatment_outputs[t].evaluation.execution_status
        for t in ALLOWED_TREATMENTS
    }
    # All four ran independently and successfully for this well-formed
    # fixture (each is valid, side-effect-free Python).
    assert all(status == "success" for status in statuses.values())
    assert len(statuses) == 4


def test_one_treatment_execution_failure_does_not_block_others(tmp_path):
    """
    ab1's raw response is swapped for code that raises at module level;
    ab2/ab3_core/ab3_full must still be fully evaluated (not skipped, not
    aborted) even though ab1's execution genuinely fails.
    """
    raising_ab1 = "```python\nraise ValueError('boom')\n```"
    inp = _make_input(tmp_path, skill_id="jh_math_skill", raw_ab1=raising_ab1)
    result = run_paired_pipeline(inp)  # must not raise

    assert result.treatment_outputs["ab1"].evaluation.execution_status == "failure"
    for treatment in ("ab2", "ab3_core", "ab3_full"):
        ev = result.treatment_outputs[treatment].evaluation
        assert ev.execution_status == "success"
        assert ev.execution_success is True
