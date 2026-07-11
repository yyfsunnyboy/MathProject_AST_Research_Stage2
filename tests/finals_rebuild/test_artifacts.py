"""
Tests for agent_tools/finals_rebuild/artifacts.py

Coverage
--------
Group 1 – pair_id determinism
  A  pair_id is deterministic for identical inputs
  B  pair_id reflects bare_prompt_hash   (P0-new)
  C  pair_id reflects scaffold_prompt_hash
  D  pair_id changes with model_revision  (P0-new)
  E  pair_id excludes timestamp

Group 2 – raw_id determinism
  F  raw_id is deterministic
  G  different raw content → different raw_id
  H  Ab1 and Scaffold use distinct raw_role  (P0-new)

Group 3 – run_id determinism
  I  treatment change → different run_id
  J  ab3_core output change → run_id changes  (P0-new)
  K  ab3_full and ab3_core same input, different output → different run_id  (P0-new)

Group 4 – validation guards
  L  sample_index=True rejected  (P0-new)
  M  seed=True rejected  (P0-new)
  N  seed negative rejected  (P0-new)
  O  invalid SHA-256 rejected
  P  unknown treatment rejected
  Q  naive timestamp rejected  (P0-new)
  R  non-UTC offset rejected  (P0-new)

Group 5 – PairMetadata partial validation  (P0-new)
  S  draft stage allows null raw/extracted hashes
  T  complete stage fails when any hash is missing

Group 6 – ArtifactPaths  (P0-new)
  U  init rejects '..' in study_id
  V  init rejects '..' in pair_id
  W  each treatment has a distinct run_metadata_json path
  X  pair_metadata_json and run_metadata_json paths do not collide

Group 7 – shared run identity
  Y  shared run identity passes for ab2/ab3_core/ab3_full
  Z  shared run identity fails on input_artifact_hash mismatch

Group 8 – immutable write
  AA first write returns "written"
  AB same content returns "unchanged"
  AC different content raises ImmutableWriteError
  AD path traversal in immutable_write rejected
  AE same content preserves mtime  (P0-new)
  AF exclusive-create fallback: content is never corrupted  (P0-new)

Group 9 – JSON round-trip
  AG PairMetadata round-trip preserves all fields
  AH RunMetadata round-trip preserves all fields
  AI stable JSON serialisation independent of dict key order  (P0-new)
"""

from __future__ import annotations

import os
import sys
import time
import pathlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import pytest

from agent_tools.finals_rebuild.artifacts import (
    ALLOWED_TREATMENTS,
    ALLOWED_RAW_ROLES,
    ImmutableWriteError,
    PairMetadata,
    RunMetadata,
    ArtifactPaths,
    build_pair_id,
    build_raw_id,
    build_run_id,
    immutable_write_bytes,
    immutable_write_text,
    pair_metadata_from_dict,
    pair_metadata_json_round_trip,
    pair_metadata_to_dict,
    run_metadata_from_dict,
    run_metadata_json_round_trip,
    run_metadata_to_dict,
    sha256_text,
    sha256_json,
    validate_pair_metadata,
    validate_run_metadata,
    validate_shared_run_identity,
    _require_sha256,
    _require_optional_seed,
    _require_nonneg_int,
    _validate_treatment,
    _validate_utc_timestamp,
)

# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

_H_A = "a" * 64
_H_B = "b" * 64
_H_C = "c" * 64
_H_D = "d" * 64
_H_E = "e" * 64
_H_F = "f" * 64

_TIMESTAMP = "2026-07-11T08:00:00+00:00"

_BASE_PAIR_KWARGS: dict = dict(
    study_id="study_test",
    model_id="gpt-4o",
    model_revision="2024-08-06",
    skill_id="algebra_01",
    sample_index=0,
    seed=42,
    bare_prompt_hash=_H_A,
    scaffold_prompt_hash=_H_B,
    generation_config_hash=_H_C,
)

# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _make_pair_id(**overrides) -> str:
    kwargs = {**_BASE_PAIR_KWARGS, **overrides}
    return build_pair_id(**kwargs)


def _make_complete_pair_meta(**pair_id_overrides) -> PairMetadata:
    """Return a fully-populated PairMetadata that passes stage='complete'."""
    pkw = {**_BASE_PAIR_KWARGS, **pair_id_overrides}
    pid = build_pair_id(**pkw)
    raw_ab1_hash = sha256_text("ab1_raw_content")
    raw_ab2_hash = sha256_text("ab2_raw_content")
    raw_ab1_id = build_raw_id(pid, "ab1_raw", raw_ab1_hash)
    raw_ab2_id = build_raw_id(pid, "scaffold_raw", raw_ab2_hash)
    ext_ab1 = sha256_text("ab1_extracted")
    ext_ab2 = sha256_text("ab2_extracted")
    return PairMetadata(
        study_id=pkw["study_id"],
        pair_id=pid,
        model_id=pkw["model_id"],
        model_revision=pkw["model_revision"],
        skill_id=pkw["skill_id"],
        sample_index=pkw["sample_index"],
        seed=pkw["seed"],
        bare_prompt_hash=pkw["bare_prompt_hash"],
        scaffold_prompt_hash=pkw["scaffold_prompt_hash"],
        generation_config_hash=pkw["generation_config_hash"],
        source_git_commit="eeab937",
        created_at_utc=_TIMESTAMP,
        raw_ab1_id=raw_ab1_id,
        raw_ab2_id=raw_ab2_id,
        raw_ab1_hash=raw_ab1_hash,
        raw_ab2_hash=raw_ab2_hash,
        extracted_ab1_hash=ext_ab1,
        extracted_ab2_hash=ext_ab2,
    )


def _make_draft_pair_meta() -> PairMetadata:
    """Return a PairMetadata with all nullable fields set to None."""
    pid = _make_pair_id()
    return PairMetadata(
        study_id="study_test",
        pair_id=pid,
        model_id="gpt-4o",
        model_revision="2024-08-06",
        skill_id="algebra_01",
        sample_index=0,
        seed=42,
        bare_prompt_hash=_H_A,
        scaffold_prompt_hash=_H_B,
        generation_config_hash=_H_C,
        source_git_commit="eeab937",
        created_at_utc=_TIMESTAMP,
    )


def _make_run_meta(
    treatment: str,
    pair_id: str,
    input_hash: str,
    output_hash: str,
) -> RunMetadata:
    run_id = build_run_id(pair_id, treatment, output_hash)
    return RunMetadata(
        study_id="study_test",
        pair_id=pair_id,
        treatment=treatment,
        run_id=run_id,
        input_artifact_hash=input_hash,
        output_artifact_hash=output_hash,
        source_git_commit="eeab937",
        created_at_utc=_TIMESTAMP,
    )


# ============================================================
# Group 1: pair_id determinism
# ============================================================


def test_A_pair_id_is_deterministic():
    pid1 = _make_pair_id()
    pid2 = _make_pair_id()
    assert pid1 == pid2


def test_B_pair_id_reflects_bare_prompt_hash():
    pid1 = _make_pair_id(bare_prompt_hash=_H_A)
    pid2 = _make_pair_id(bare_prompt_hash=_H_D)
    assert pid1 != pid2


def test_C_pair_id_reflects_scaffold_prompt_hash():
    pid1 = _make_pair_id(scaffold_prompt_hash=_H_B)
    pid2 = _make_pair_id(scaffold_prompt_hash=_H_E)
    assert pid1 != pid2


def test_D_pair_id_changes_with_model_revision():
    pid1 = _make_pair_id(model_revision="2024-08-06")
    pid2 = _make_pair_id(model_revision="2025-01-01")
    assert pid1 != pid2


def test_E_pair_id_excludes_timestamp():
    """Calling build_pair_id at two different conceptual times yields the
    same result because timestamp is not an input."""
    pid1 = build_pair_id(**_BASE_PAIR_KWARGS)
    pid2 = build_pair_id(**_BASE_PAIR_KWARGS)
    assert pid1 == pid2


# ============================================================
# Group 2: raw_id determinism
# ============================================================


def test_F_raw_id_is_deterministic():
    pid = _make_pair_id()
    assert build_raw_id(pid, "ab1_raw", _H_C) == build_raw_id(pid, "ab1_raw", _H_C)


def test_G_different_raw_content_gives_different_raw_id():
    pid = _make_pair_id()
    rid1 = build_raw_id(pid, "ab1_raw", _H_C)
    rid2 = build_raw_id(pid, "ab1_raw", _H_D)
    assert rid1 != rid2


def test_H_ab1_and_scaffold_use_distinct_raw_role():
    """Same pair_id and same raw content still produce different raw_ids
    because the raw_role differs."""
    pid = _make_pair_id()
    same_hash = _H_C
    rid_ab1 = build_raw_id(pid, "ab1_raw", same_hash)
    rid_scaf = build_raw_id(pid, "scaffold_raw", same_hash)
    assert rid_ab1 != rid_scaf


# ============================================================
# Group 3: run_id determinism
# ============================================================


def test_I_run_id_changes_with_treatment():
    pid = _make_pair_id()
    rid_ab2 = build_run_id(pid, "ab2", _H_C)
    rid_ab3c = build_run_id(pid, "ab3_core", _H_C)
    assert rid_ab2 != rid_ab3c


def test_J_run_id_changes_with_ab3_core_output():
    pid = _make_pair_id()
    rid1 = build_run_id(pid, "ab3_core", _H_C)
    rid2 = build_run_id(pid, "ab3_core", _H_D)
    assert rid1 != rid2


def test_K_ab3_full_and_ab3_core_differ_on_different_output():
    """Same input_artifact_hash, different output → different run_id."""
    pid = _make_pair_id()
    # Simulate ab3_core and ab3_full each producing a different output
    rid_core = build_run_id(pid, "ab3_core", _H_C)
    rid_full = build_run_id(pid, "ab3_full", _H_D)
    assert rid_core != rid_full
    # Even if outputs were accidentally equal, treatments differ
    rid_core2 = build_run_id(pid, "ab3_core", _H_E)
    rid_full2 = build_run_id(pid, "ab3_full", _H_E)
    assert rid_core2 != rid_full2


# ============================================================
# Group 4: validation guards
# ============================================================


def test_L_sample_index_bool_rejected():
    with pytest.raises(ValueError):
        _require_nonneg_int(True, "sample_index")
    with pytest.raises(ValueError):
        build_pair_id(**{**_BASE_PAIR_KWARGS, "sample_index": True})


def test_M_seed_bool_rejected():
    with pytest.raises(ValueError):
        _require_optional_seed(True, "seed")
    with pytest.raises(ValueError):
        build_pair_id(**{**_BASE_PAIR_KWARGS, "seed": True})


def test_N_seed_negative_rejected():
    with pytest.raises(ValueError):
        _require_optional_seed(-1, "seed")
    with pytest.raises(ValueError):
        build_pair_id(**{**_BASE_PAIR_KWARGS, "seed": -1})


def test_O_invalid_sha256_rejected():
    with pytest.raises(ValueError):
        _require_sha256("not-a-hash", "field")
    with pytest.raises(ValueError):
        _require_sha256("a" * 63, "short")
    with pytest.raises(ValueError):
        _require_sha256("G" * 64, "uppercase")


def test_P_unknown_treatment_rejected():
    with pytest.raises(ValueError):
        _validate_treatment("ab4_unknown")
    with pytest.raises(ValueError):
        _validate_treatment("")
    with pytest.raises(ValueError):
        build_run_id(_H_A, "bad_treatment", _H_B)


def test_Q_naive_timestamp_rejected():
    with pytest.raises(ValueError):
        _validate_utc_timestamp("2026-07-11T08:00:00", "ts")


def test_R_non_utc_offset_rejected():
    with pytest.raises(ValueError):
        _validate_utc_timestamp("2026-07-11T08:00:00+08:00", "ts")
    with pytest.raises(ValueError):
        _validate_utc_timestamp("2026-07-11T08:00:00-05:00", "ts")
    # Valid UTC offsets must pass
    _validate_utc_timestamp("2026-07-11T08:00:00+00:00", "ts")
    _validate_utc_timestamp("2026-07-11T08:00:00Z", "ts")


# ============================================================
# Group 5: PairMetadata partial validation
# ============================================================


def test_S_draft_allows_null_hashes():
    meta = _make_draft_pair_meta()
    validate_pair_metadata(meta, stage="draft")  # must not raise


def test_T_complete_fails_on_missing_hash():
    meta = _make_draft_pair_meta()
    with pytest.raises(ValueError, match="complete"):
        validate_pair_metadata(meta, stage="complete")


# ============================================================
# Group 6: ArtifactPaths
# ============================================================


def test_U_artifact_paths_rejects_dotdot_in_study_id(tmp_path):
    with pytest.raises(ValueError):
        ArtifactPaths(root=tmp_path, study_id="..", pair_id="valid_pair")


def test_V_artifact_paths_rejects_dotdot_in_pair_id(tmp_path):
    with pytest.raises(ValueError):
        ArtifactPaths(root=tmp_path, study_id="valid_study", pair_id="..")


def test_W_each_treatment_has_distinct_run_metadata_path(tmp_path):
    ap = ArtifactPaths(root=tmp_path, study_id="s", pair_id="p")
    paths = [str(ap.run_metadata_json(t)) for t in sorted(ALLOWED_TREATMENTS)]
    assert len(paths) == len(set(paths)), "run_metadata_json paths must be distinct"


def test_X_pair_metadata_and_run_metadata_no_collision(tmp_path):
    ap = ArtifactPaths(root=tmp_path, study_id="s", pair_id="p")
    pair_path = str(ap.pair_metadata_json)
    run_paths = [str(ap.run_metadata_json(t)) for t in sorted(ALLOWED_TREATMENTS)]
    assert pair_path not in run_paths
    assert all(pair_path != rp for rp in run_paths)


# ============================================================
# Group 7: shared run identity
# ============================================================


def test_Y_shared_run_identity_passes():
    pid = _make_pair_id()
    shared_input = _H_C
    ab2 = _make_run_meta("ab2", pid, shared_input, _H_D)
    ab3c = _make_run_meta("ab3_core", pid, shared_input, _H_E)
    ab3f = _make_run_meta("ab3_full", pid, shared_input, _H_F)
    validate_shared_run_identity(ab2, ab3c, ab3f)  # must not raise


def test_Z_shared_run_identity_fails_on_input_hash_mismatch():
    pid = _make_pair_id()
    ab2 = _make_run_meta("ab2", pid, _H_C, _H_D)
    ab3c = _make_run_meta("ab3_core", pid, _H_C, _H_E)
    # ab3_full uses a different input_artifact_hash
    ab3f = _make_run_meta("ab3_full", pid, _H_F, _H_F)
    with pytest.raises(ValueError, match="input_artifact_hash"):
        validate_shared_run_identity(ab2, ab3c, ab3f)


# ============================================================
# Group 8: immutable write
# ============================================================


def test_AA_first_write_returns_written(tmp_path):
    target = tmp_path / "sub" / "file.txt"
    result = immutable_write_text(target, "hello", artifact_root=tmp_path)
    assert result == "written"
    assert target.read_text(encoding="utf-8") == "hello"


def test_AB_same_content_returns_unchanged(tmp_path):
    target = tmp_path / "file.txt"
    immutable_write_text(target, "hello", artifact_root=tmp_path)
    result = immutable_write_text(target, "hello", artifact_root=tmp_path)
    assert result == "unchanged"


def test_AC_different_content_raises(tmp_path):
    target = tmp_path / "file.txt"
    immutable_write_text(target, "hello", artifact_root=tmp_path)
    with pytest.raises(ImmutableWriteError):
        immutable_write_text(target, "world", artifact_root=tmp_path)


def test_AD_immutable_write_path_traversal_rejected(tmp_path):
    traversal = tmp_path / ".." / "escaped.txt"
    with pytest.raises(ValueError, match="[Tt]raversal|outside"):
        immutable_write_bytes(traversal, b"bad", artifact_root=tmp_path)


def test_AE_same_content_preserves_mtime(tmp_path):
    target = tmp_path / "file.txt"
    immutable_write_text(target, "stable", artifact_root=tmp_path)
    mtime_before = target.stat().st_mtime_ns
    time.sleep(0.05)
    result = immutable_write_text(target, "stable", artifact_root=tmp_path)
    mtime_after = target.stat().st_mtime_ns
    assert result == "unchanged"
    assert mtime_before == mtime_after, "mtime must not change on unchanged write"


def test_AF_exclusive_create_fallback_no_corruption(tmp_path):
    """
    Verify the exclusive-create pattern:
    - FileExistsError is handled by reading and comparing.
    - Content is never silently overwritten or corrupted.
    """
    target = tmp_path / "artifact.bin"
    data = b"original_content"

    r1 = immutable_write_bytes(target, data, artifact_root=tmp_path)
    assert r1 == "written"
    assert target.read_bytes() == data

    r2 = immutable_write_bytes(target, data, artifact_root=tmp_path)
    assert r2 == "unchanged"
    assert target.read_bytes() == data  # not corrupted

    with pytest.raises(ImmutableWriteError):
        immutable_write_bytes(target, b"tampered", artifact_root=tmp_path)
    assert target.read_bytes() == data  # original preserved


# ============================================================
# Group 9: JSON round-trip
# ============================================================


def test_AG_pair_metadata_json_round_trip():
    meta = _make_complete_pair_meta()
    meta_extra = PairMetadata(
        **{f: getattr(meta, f) for f in (
            "study_id", "pair_id", "model_id", "model_revision",
            "skill_id", "sample_index", "seed",
            "bare_prompt_hash", "scaffold_prompt_hash",
            "generation_config_hash", "source_git_commit",
            "created_at_utc", "raw_ab1_id", "raw_ab2_id",
            "raw_ab1_hash", "raw_ab2_hash",
            "extracted_ab1_hash", "extracted_ab2_hash",
        )},
        extra={"custom_note": "round_trip"},
    )
    restored = pair_metadata_json_round_trip(meta_extra)
    assert restored.study_id == meta_extra.study_id
    assert restored.pair_id == meta_extra.pair_id
    assert restored.model_id == meta_extra.model_id
    assert restored.model_revision == meta_extra.model_revision
    assert restored.skill_id == meta_extra.skill_id
    assert restored.sample_index == meta_extra.sample_index
    assert restored.seed == meta_extra.seed
    assert restored.bare_prompt_hash == meta_extra.bare_prompt_hash
    assert restored.scaffold_prompt_hash == meta_extra.scaffold_prompt_hash
    assert restored.generation_config_hash == meta_extra.generation_config_hash
    assert restored.source_git_commit == meta_extra.source_git_commit
    assert restored.created_at_utc == meta_extra.created_at_utc
    assert restored.raw_ab1_id == meta_extra.raw_ab1_id
    assert restored.raw_ab2_id == meta_extra.raw_ab2_id
    assert restored.raw_ab1_hash == meta_extra.raw_ab1_hash
    assert restored.raw_ab2_hash == meta_extra.raw_ab2_hash
    assert restored.extracted_ab1_hash == meta_extra.extracted_ab1_hash
    assert restored.extracted_ab2_hash == meta_extra.extracted_ab2_hash
    assert restored.extra.get("custom_note") == "round_trip"


def test_AH_run_metadata_json_round_trip():
    pid = _make_pair_id()
    meta = RunMetadata(
        study_id="study_test",
        pair_id=pid,
        treatment="ab3_core",
        run_id=build_run_id(pid, "ab3_core", _H_D),
        input_artifact_hash=_H_C,
        output_artifact_hash=_H_D,
        source_git_commit="eeab937",
        created_at_utc=_TIMESTAMP,
        trace_hash=_H_E,
        evaluation_hash=None,
        extra={"note": "test"},
    )
    restored = run_metadata_json_round_trip(meta)
    assert restored.study_id == meta.study_id
    assert restored.pair_id == meta.pair_id
    assert restored.treatment == meta.treatment
    assert restored.run_id == meta.run_id
    assert restored.input_artifact_hash == meta.input_artifact_hash
    assert restored.output_artifact_hash == meta.output_artifact_hash
    assert restored.source_git_commit == meta.source_git_commit
    assert restored.created_at_utc == meta.created_at_utc
    assert restored.trace_hash == meta.trace_hash
    assert restored.evaluation_hash is None
    assert restored.extra.get("note") == "test"


def test_AI_stable_json_serialization():
    """sha256_json must produce the same hash regardless of dict key order."""
    obj_a = {"b": 2, "a": 1, "c": 3}
    obj_b = {"a": 1, "c": 3, "b": 2}
    obj_c = {"c": 3, "b": 2, "a": 1}
    h1 = sha256_json(obj_a)
    h2 = sha256_json(obj_b)
    h3 = sha256_json(obj_c)
    assert h1 == h2 == h3
    # Changing a value must change the hash
    obj_d = {"a": 1, "b": 99, "c": 3}
    assert sha256_json(obj_a) != sha256_json(obj_d)


# ---------------------------------------------------------------------------
# Group 10 – RunMetadata.extra reserved-key protection (Fix 2)
# ---------------------------------------------------------------------------


def _make_run_meta_with_extra(pid: str, extra: dict) -> RunMetadata:
    """Build a RunMetadata with the given extra dict (skipping validation)."""
    run_id = build_run_id(pid, "ab2", _H_C)
    return RunMetadata(
        study_id="study_test",
        pair_id=pid,
        treatment="ab2",
        run_id=run_id,
        input_artifact_hash=_H_C,
        output_artifact_hash=_H_C,
        source_git_commit="abc123",
        created_at_utc=_TIMESTAMP,
        extra=extra,
    )


def test_AJ_extra_with_study_id_rejected_in_validate():
    """extra containing 'study_id' must be rejected by validate_run_metadata."""
    pid = _make_pair_id()
    meta = _make_run_meta_with_extra(pid, {"study_id": "injected"})
    with pytest.raises(ValueError, match="study_id"):
        validate_run_metadata(meta)


def test_AK_extra_with_treatment_rejected_in_validate():
    """extra containing 'treatment' must be rejected by validate_run_metadata."""
    pid = _make_pair_id()
    meta = _make_run_meta_with_extra(pid, {"treatment": "ab3_full"})
    with pytest.raises(ValueError, match="treatment"):
        validate_run_metadata(meta)


def test_AL_extra_with_run_id_rejected_in_validate():
    """extra containing 'run_id' must be rejected by validate_run_metadata."""
    pid = _make_pair_id()
    meta = _make_run_meta_with_extra(pid, {"run_id": "b" * 64})
    with pytest.raises(ValueError, match="run_id"):
        validate_run_metadata(meta)


def test_AM_extra_with_created_at_utc_rejected_in_validate():
    """extra containing 'created_at_utc' must be rejected."""
    pid = _make_pair_id()
    meta = _make_run_meta_with_extra(pid, {"created_at_utc": "2099-01-01T00:00:00Z"})
    with pytest.raises(ValueError, match="created_at_utc"):
        validate_run_metadata(meta)


def test_AN_run_metadata_to_dict_raises_on_conflicting_extra():
    """run_metadata_to_dict must also reject extra keys that shadow official fields."""
    pid = _make_pair_id()
    meta = _make_run_meta_with_extra(pid, {"pair_id": "injected"})
    with pytest.raises(ValueError):
        run_metadata_to_dict(meta)


def test_AO_valid_extra_fields_round_trip():
    """Non-conflicting extra keys must survive a full JSON round-trip."""
    pid = _make_pair_id()
    run_id = build_run_id(pid, "ab2", _H_C)
    meta = RunMetadata(
        study_id="study_test",
        pair_id=pid,
        treatment="ab2",
        run_id=run_id,
        input_artifact_hash=_H_C,
        output_artifact_hash=_H_C,
        source_git_commit="abc123",
        created_at_utc=_TIMESTAMP,
        extra={
            "treatment_applied": False,
            "implementation_status": "pass_through",
            "changed": False,
        },
    )
    validate_run_metadata(meta)   # must not raise
    restored = run_metadata_json_round_trip(meta)
    assert restored.extra.get("treatment_applied") is False
    assert restored.extra.get("implementation_status") == "pass_through"
    assert restored.extra.get("changed") is False
