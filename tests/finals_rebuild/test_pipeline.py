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
from agent_tools.finals_rebuild.extraction import extract_code as _orig_extract_code
from agent_tools.finals_rebuild.pipeline import (
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
) -> PairedPipelineInput:
    """Build a fully-consistent PairedPipelineInput for tests."""
    bare_hash = sha256_text(bare_prompt)
    scaffold_hash = sha256_text(scaffold_prompt)
    pair_id = build_pair_id(
        study_id="test_study",
        model_id="test_model",
        model_revision="v1",
        skill_id="algebra_01",
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
        skill_id="algebra_01",
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
    with pytest.raises(ImmutableWriteError):
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
    inp = _make_input(tmp_path)
    result = run_paired_pipeline(inp)

    for treatment, to in result.treatment_outputs.items():
        assert to.treatment_applied is False, (
            f"{treatment}: treatment_applied must be False in pass-through"
        )
        assert to.changed is False, (
            f"{treatment}: changed must be False in pass-through"
        )


# ============================================================
# Test 18: implementation_status="pass_through" for all treatments
# ============================================================


def test_implementation_status_is_pass_through(tmp_path):
    inp = _make_input(tmp_path)
    result = run_paired_pipeline(inp)

    for treatment, to in result.treatment_outputs.items():
        assert to.implementation_status == "pass_through", (
            f"{treatment}: expected 'pass_through', "
            f"got {to.implementation_status!r}"
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

    for treatment in ALLOWED_TREATMENTS:
        raw_json = ap.run_metadata_json(treatment).read_text(encoding="utf-8")
        stored = json.loads(raw_json)
        assert stored["treatment"] == treatment
        assert stored["pair_id"] == result.pair_id
        assert stored["treatment_applied"] is False
        assert stored["implementation_status"] == "pass_through"
