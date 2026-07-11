"""
Tests for agent_tools/finals_rebuild/artifacts.py

Coverage matrix (15 required cases)
------------------------------------
 1. Same inputs → same pair_id
 2. Timestamp change does NOT affect pair_id
 3. Scaffold prompt hash change DOES change pair_id
 4. Same raw → same raw_id
 5. Different raw → different raw_id
 6. Treatment change → different run_id
 7. Ab2/Ab3-Core/Ab3-Full shared-identity validation passes
 8. Mismatched raw_ab2_hash → shared-identity validation fails
 9. Immutable write – first write succeeds ("written")
10. Immutable write – identical second write returns "unchanged"
11. Immutable write – different content overwrite raises ImmutableWriteError
12. Invalid SHA-256 string is rejected by _require_sha256
13. Path traversal is rejected by immutable_write
14. Metadata JSON round-trip preserves all fields
15. Unknown treatment is rejected
"""

from __future__ import annotations

import os
import sys
import pathlib
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import pytest

from agent_tools.finals_rebuild.artifacts import (
    ALLOWED_TREATMENTS,
    ImmutableWriteError,
    ArtifactMetadata,
    build_pair_id,
    build_raw_id,
    build_run_id,
    immutable_write_bytes,
    immutable_write_text,
    metadata_from_dict,
    metadata_json_round_trip,
    metadata_to_dict,
    sha256_text,
    validate_metadata,
    validate_shared_identity,
    _require_sha256,
    _validate_treatment,
)

# ---------------------------------------------------------------------------
# Fixtures / shared helpers
# ---------------------------------------------------------------------------

_FAKE_HASH_A = "a" * 64
_FAKE_HASH_B = "b" * 64
_FAKE_HASH_C = "c" * 64
_FAKE_HASH_D = "d" * 64
_FAKE_HASH_E = "e" * 64

_BASE_PAIR_KWARGS = dict(
    study_id="study_test",
    model_id="gpt-4o",
    skill_id="algebra_01",
    sample_index=0,
    scaffold_prompt_hash=_FAKE_HASH_A,
    generation_config_hash=_FAKE_HASH_B,
)


def _make_pair_id(**overrides) -> str:
    kwargs = {**_BASE_PAIR_KWARGS, **overrides}
    return build_pair_id(**kwargs)


def _make_valid_meta(
    treatment: str = "ab2",
    pair_id: str | None = None,
    raw_hash: str = _FAKE_HASH_C,
    output_hash: str = _FAKE_HASH_D,
    timestamp: str = "2026-07-11T08:00:00.000000+00:00",
) -> dict:
    pid = pair_id or _make_pair_id()
    raw_id = build_raw_id(pid, raw_hash)
    run_id = build_run_id(pid, treatment, output_hash)

    raw_ab1_hash = sha256_text("bare_raw")
    raw_ab2_hash = raw_hash
    extracted_ab1_hash = sha256_text("bare_extracted")
    extracted_ab2_hash = output_hash

    if treatment == "ab1":
        raw_ab1_hash = raw_hash
        extracted_ab1_hash = output_hash
        raw_id = build_raw_id(pid, raw_ab1_hash)
        run_id = build_run_id(pid, treatment, extracted_ab1_hash)

    return {
        "study_id": "study_test",
        "pair_id": pid,
        "raw_id": raw_id,
        "run_id": run_id,
        "model_id": "gpt-4o",
        "skill_id": "algebra_01",
        "sample_index": 0,
        "seed": 42,
        "prompt_hash": _FAKE_HASH_A,
        "generation_config_hash": _FAKE_HASH_B,
        "source_git_commit": "fbaedacb",
        "timestamp_utc": timestamp,
        "treatment": treatment,
        "raw_ab1_hash": raw_ab1_hash,
        "raw_ab2_hash": raw_ab2_hash,
        "extracted_ab1_hash": extracted_ab1_hash,
        "extracted_ab2_hash": extracted_ab2_hash,
    }


# ---------------------------------------------------------------------------
# Test 1: Same inputs → same pair_id
# ---------------------------------------------------------------------------


def test_pair_id_deterministic():
    pid1 = _make_pair_id()
    pid2 = _make_pair_id()
    assert pid1 == pid2, "pair_id must be deterministic for identical inputs"


# ---------------------------------------------------------------------------
# Test 2: Timestamp change does NOT affect pair_id
# ---------------------------------------------------------------------------


def test_pair_id_ignores_timestamp():
    pid1 = _make_pair_id()
    # Timestamps are not an input to build_pair_id, but we verify calling
    # the function at different conceptual "times" still yields the same result.
    pid2 = build_pair_id(
        study_id="study_test",
        model_id="gpt-4o",
        skill_id="algebra_01",
        sample_index=0,
        scaffold_prompt_hash=_FAKE_HASH_A,
        generation_config_hash=_FAKE_HASH_B,
    )
    assert pid1 == pid2


# ---------------------------------------------------------------------------
# Test 3: Scaffold prompt hash change DOES change pair_id
# ---------------------------------------------------------------------------


def test_pair_id_changes_with_prompt_hash():
    pid1 = _make_pair_id(scaffold_prompt_hash=_FAKE_HASH_A)
    pid2 = _make_pair_id(scaffold_prompt_hash=_FAKE_HASH_B)
    assert pid1 != pid2


# ---------------------------------------------------------------------------
# Test 4: Same raw → same raw_id
# ---------------------------------------------------------------------------


def test_raw_id_deterministic():
    pid = _make_pair_id()
    rid1 = build_raw_id(pid, _FAKE_HASH_C)
    rid2 = build_raw_id(pid, _FAKE_HASH_C)
    assert rid1 == rid2


# ---------------------------------------------------------------------------
# Test 5: Different raw → different raw_id
# ---------------------------------------------------------------------------


def test_raw_id_differs_for_different_raw():
    pid = _make_pair_id()
    rid1 = build_raw_id(pid, _FAKE_HASH_C)
    rid2 = build_raw_id(pid, _FAKE_HASH_D)
    assert rid1 != rid2


# ---------------------------------------------------------------------------
# Test 6: Treatment change → different run_id
# ---------------------------------------------------------------------------


def test_run_id_differs_for_different_treatment():
    pid = _make_pair_id()
    rid_ab2 = build_run_id(pid, "ab2", _FAKE_HASH_C)
    rid_ab3c = build_run_id(pid, "ab3_core", _FAKE_HASH_C)
    assert rid_ab2 != rid_ab3c


# ---------------------------------------------------------------------------
# Test 7: Shared identity validation passes for ab2/ab3_core/ab3_full
# ---------------------------------------------------------------------------


def test_shared_identity_passes():
    pid = _make_pair_id()
    shared_raw_hash = _FAKE_HASH_C
    shared_extracted_hash = _FAKE_HASH_D
    shared_raw_id = build_raw_id(pid, shared_raw_hash)

    def _meta(treatment: str) -> dict:
        run_id = build_run_id(pid, treatment, shared_extracted_hash)
        bare_raw = sha256_text("bare_raw_text")
        bare_extracted = sha256_text("bare_extracted_text")
        return {
            "study_id": "study_test",
            "pair_id": pid,
            "raw_id": shared_raw_id,
            "run_id": run_id,
            "model_id": "gpt-4o",
            "skill_id": "algebra_01",
            "sample_index": 0,
            "seed": 42,
            "prompt_hash": _FAKE_HASH_A,
            "generation_config_hash": _FAKE_HASH_B,
            "source_git_commit": "abc",
            "timestamp_utc": "2026-07-11T00:00:00+00:00",
            "treatment": treatment,
            "raw_ab1_hash": bare_raw,
            "raw_ab2_hash": shared_raw_hash,
            "extracted_ab1_hash": bare_extracted,
            "extracted_ab2_hash": shared_extracted_hash,
        }

    validate_shared_identity(
        ab2_meta=_meta("ab2"),
        ab3_core_meta=_meta("ab3_core"),
        ab3_full_meta=_meta("ab3_full"),
    )


# ---------------------------------------------------------------------------
# Test 8: Mismatched raw_ab2_hash → shared-identity validation fails
# ---------------------------------------------------------------------------


def test_shared_identity_fails_on_raw_hash_mismatch():
    pid = _make_pair_id()
    raw_id_shared = build_raw_id(pid, _FAKE_HASH_C)
    run_id_ab2 = build_run_id(pid, "ab2", _FAKE_HASH_D)
    run_id_ab3c = build_run_id(pid, "ab3_core", _FAKE_HASH_D)
    run_id_ab3f = build_run_id(pid, "ab3_full", _FAKE_HASH_D)

    bare_raw = sha256_text("bare")
    bare_ext = sha256_text("bare_ext")

    def _base(treatment: str, run_id: str, raw_ab2: str) -> dict:
        return {
            "study_id": "study_test",
            "pair_id": pid,
            "raw_id": raw_id_shared,
            "run_id": run_id,
            "model_id": "gpt-4o",
            "skill_id": "algebra_01",
            "sample_index": 0,
            "seed": 0,
            "prompt_hash": _FAKE_HASH_A,
            "generation_config_hash": _FAKE_HASH_B,
            "source_git_commit": "abc",
            "timestamp_utc": "2026-07-11T00:00:00+00:00",
            "treatment": treatment,
            "raw_ab1_hash": bare_raw,
            "raw_ab2_hash": raw_ab2,
            "extracted_ab1_hash": bare_ext,
            "extracted_ab2_hash": _FAKE_HASH_D,
        }

    ab2_meta = _base("ab2", run_id_ab2, _FAKE_HASH_C)
    ab3_core_meta = _base("ab3_core", run_id_ab3c, _FAKE_HASH_C)
    # deliberately different raw_ab2_hash for ab3_full
    ab3_full_meta = _base("ab3_full", run_id_ab3f, _FAKE_HASH_E)

    with pytest.raises(ValueError, match="raw_ab2_hash"):
        validate_shared_identity(ab2_meta, ab3_core_meta, ab3_full_meta)


# ---------------------------------------------------------------------------
# Test 9: Immutable write – first write succeeds ("written")
# ---------------------------------------------------------------------------


def test_immutable_write_first_succeeds(tmp_path):
    target = tmp_path / "sub" / "file.txt"
    result = immutable_write_text(target, "hello", artifact_root=tmp_path)
    assert result == "written"
    assert target.read_text(encoding="utf-8") == "hello"


# ---------------------------------------------------------------------------
# Test 10: Immutable write – identical second write returns "unchanged"
# ---------------------------------------------------------------------------


def test_immutable_write_unchanged_on_same_content(tmp_path):
    target = tmp_path / "file.txt"
    immutable_write_text(target, "hello", artifact_root=tmp_path)
    result = immutable_write_text(target, "hello", artifact_root=tmp_path)
    assert result == "unchanged"


# ---------------------------------------------------------------------------
# Test 11: Immutable write – different content overwrite raises error
# ---------------------------------------------------------------------------


def test_immutable_write_raises_on_different_content(tmp_path):
    target = tmp_path / "file.txt"
    immutable_write_text(target, "hello", artifact_root=tmp_path)
    with pytest.raises(ImmutableWriteError):
        immutable_write_text(target, "world", artifact_root=tmp_path)


# ---------------------------------------------------------------------------
# Test 12: Invalid SHA-256 string is rejected
# ---------------------------------------------------------------------------


def test_invalid_sha256_rejected():
    with pytest.raises(ValueError):
        _require_sha256("not-a-hash", "test_field")

    with pytest.raises(ValueError):
        _require_sha256("a" * 63, "short_hash")

    with pytest.raises(ValueError):
        _require_sha256("G" * 64, "uppercase_hex")


# ---------------------------------------------------------------------------
# Test 13: Path traversal is rejected
# ---------------------------------------------------------------------------


def test_path_traversal_rejected(tmp_path):
    outside = tmp_path.parent / "outside.txt"
    traversal_path = tmp_path / ".." / "outside.txt"
    with pytest.raises(ValueError, match="[Tt]raversal|outside"):
        immutable_write_bytes(
            traversal_path,
            b"bad",
            artifact_root=tmp_path,
        )


# ---------------------------------------------------------------------------
# Test 14: Metadata JSON round-trip preserves all fields
# ---------------------------------------------------------------------------


def test_metadata_json_round_trip():
    pid = _make_pair_id()
    shared_raw_hash = _FAKE_HASH_C
    shared_ext_hash = _FAKE_HASH_D
    raw_id = build_raw_id(pid, shared_raw_hash)
    run_id = build_run_id(pid, "ab2", shared_ext_hash)
    bare_raw = sha256_text("bare_raw")
    bare_ext = sha256_text("bare_ext")

    meta = ArtifactMetadata(
        study_id="study_test",
        pair_id=pid,
        raw_id=raw_id,
        run_id=run_id,
        model_id="gpt-4o",
        skill_id="algebra_01",
        sample_index=0,
        seed=42,
        prompt_hash=_FAKE_HASH_A,
        generation_config_hash=_FAKE_HASH_B,
        source_git_commit="fbaedacb",
        timestamp_utc="2026-07-11T08:00:00+00:00",
        treatment="ab2",
        raw_ab1_hash=bare_raw,
        raw_ab2_hash=shared_raw_hash,
        extracted_ab1_hash=bare_ext,
        extracted_ab2_hash=shared_ext_hash,
        extra={"custom_note": "round_trip_test"},
    )

    restored = metadata_json_round_trip(meta)

    assert restored.study_id == meta.study_id
    assert restored.pair_id == meta.pair_id
    assert restored.raw_id == meta.raw_id
    assert restored.run_id == meta.run_id
    assert restored.model_id == meta.model_id
    assert restored.skill_id == meta.skill_id
    assert restored.sample_index == meta.sample_index
    assert restored.seed == meta.seed
    assert restored.prompt_hash == meta.prompt_hash
    assert restored.generation_config_hash == meta.generation_config_hash
    assert restored.source_git_commit == meta.source_git_commit
    assert restored.timestamp_utc == meta.timestamp_utc
    assert restored.treatment == meta.treatment
    assert restored.raw_ab1_hash == meta.raw_ab1_hash
    assert restored.raw_ab2_hash == meta.raw_ab2_hash
    assert restored.extracted_ab1_hash == meta.extracted_ab1_hash
    assert restored.extracted_ab2_hash == meta.extracted_ab2_hash
    assert restored.extra.get("custom_note") == "round_trip_test"


# ---------------------------------------------------------------------------
# Test 15: Unknown treatment is rejected
# ---------------------------------------------------------------------------


def test_unknown_treatment_rejected():
    with pytest.raises(ValueError, match="treatment"):
        _validate_treatment("ab4_unknown")

    with pytest.raises(ValueError):
        _validate_treatment("")

    with pytest.raises(ValueError):
        build_run_id(_FAKE_HASH_A, "invalid_treatment", _FAKE_HASH_B)
