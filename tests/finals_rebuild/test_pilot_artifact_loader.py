"""
Tests for agent_tools/finals_rebuild/pilot_artifact_loader.py
"""

from __future__ import annotations

import json
import os
import pathlib
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from agent_tools.finals_rebuild.artifacts import sha256_text
from agent_tools.finals_rebuild.pilot_artifact_loader import (
    FIDELITY_EXTRACTED_ONLY,
    FIDELITY_RAW_RESPONSE,
    SOURCE_FORMAT_GENERATION_ATTEMPTS,
    SOURCE_FORMAT_LEGACY_REPLAY,
    SOURCE_FORMAT_LEGACY_REPLAY_PILOT,
    SOURCE_FORMAT_PUBLIC_BENCHMARK,
    PilotArtifactLoaderError,
    detect_source_format,
    load_generation_attempts_first,
    load_legacy_replay,
    load_legacy_replay_pilot,
    load_public_benchmark,
    load_pilot_samples,
    resolve_repo_root,
)


def _write_attempts(tmp_path, records):
    path = tmp_path / "generation_attempts.jsonl"
    with path.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, sort_keys=True) + "\n")
    return path


def _attempt(
    task_id,
    treatment,
    raw_response,
    *,
    sample_index=0,
    attempt_ordinal=None,
    attempt_kind=None,
    is_first_attempt=None,
):
    rec = {
        "task_id": task_id,
        "treatment": treatment,
        "sample_index": sample_index,
        "status": "success",
        "raw_response": raw_response,
        "raw_response_sha256": sha256_text(raw_response) if raw_response else None,
    }
    if attempt_ordinal is not None:
        rec["attempt_ordinal"] = attempt_ordinal
    if attempt_kind is not None:
        rec["attempt_kind"] = attempt_kind
    if is_first_attempt is not None:
        rec["is_first_attempt"] = is_first_attempt
    return rec


def test_selects_first_jsonl_record_not_last_resume(tmp_path):
    first = _attempt("HumanEval/0", "ab1", "def f():\n    return 1\n", sample_index=0)
    resume = _attempt(
        "HumanEval/0",
        "ab1",
        "def f():\n    return 999\n",
        sample_index=0,
        attempt_kind="resume_retry",
    )
    _write_attempts(tmp_path, [first, resume])

    loaded = load_generation_attempts_first(tmp_path)
    ab1 = [s for s in loaded if s.treatment == "ab1"]
    assert len(ab1) == 1
    assert ab1[0].raw_response == first["raw_response"]
    assert ab1[0].source_fidelity == FIDELITY_RAW_RESPONSE


def test_explicit_ordinal_selects_lowest(tmp_path):
    later = _attempt(
        "HumanEval/0",
        "ab2g",
        "def g():\n    return 2\n",
        attempt_ordinal=2,
    )
    first = _attempt(
        "HumanEval/0",
        "ab2g",
        "def g():\n    return 1\n",
        attempt_ordinal=1,
    )
    _write_attempts(tmp_path, [later, first])

    loaded = load_generation_attempts_first(tmp_path, treatments=["ab2g"])
    assert loaded[0].raw_response == first["raw_response"]
    assert loaded[0].first_attempt_selection_status == "ordinal"


def test_ambiguous_when_conflicting_ordinals(tmp_path):
    _write_attempts(
        tmp_path,
        [
            _attempt("HumanEval/0", "ab1", "def a():\n    pass\n", attempt_ordinal=1),
            _attempt("HumanEval/0", "ab1", "def b():\n    pass\n", attempt_ordinal=1),
        ],
    )
    loaded = load_generation_attempts_first(tmp_path, treatments=["ab1"])
    assert loaded[0].first_attempt_selection_status == "ambiguous"


def test_source_file_not_modified(tmp_path):
    path = _write_attempts(
        tmp_path,
        [_attempt("HumanEval/0", "ab1", "def f():\n    return 1\n")],
    )
    before = path.read_text(encoding="utf-8")
    load_generation_attempts_first(tmp_path)
    assert path.read_text(encoding="utf-8") == before


def test_ab1_and_ab2g_grouped_separately(tmp_path):
    _write_attempts(
        tmp_path,
        [
            _attempt("HumanEval/0", "ab1", "def a():\n    return 1\n"),
            _attempt("HumanEval/0", "ab2g", "def a():\n    return 2\n"),
            _attempt("HumanEval/1", "ab1", "def b():\n    return 3\n"),
            _attempt("HumanEval/1", "ab2g", "def b():\n    return 4\n"),
        ],
    )
    loaded = load_generation_attempts_first(tmp_path)
    assert len(loaded) == 4


def test_public_benchmark_extracted_only_loader(tmp_path):
    evalplus = tmp_path / "public_benchmark" / "humaneval" / "evalplus"
    evalplus.mkdir(parents=True)
    fixture = (
        pathlib.Path(__file__).resolve().parent
        / "fixtures"
        / "pilot_audit"
        / "public_benchmark_ab1.jsonl"
    )
    (evalplus / "ab1.jsonl").write_text(fixture.read_text(encoding="utf-8"), encoding="utf-8")

    loaded = load_public_benchmark(tmp_path, treatments=["ab1"])
    assert len(loaded) == 1
    assert loaded[0].source_fidelity == FIDELITY_EXTRACTED_ONLY
    assert loaded[0].raw_response is None
    assert loaded[0].extracted_code.startswith("def add")


def test_legacy_replay_extracted_only_loader():
    repo = resolve_repo_root()
    fixture_root = repo / "tests" / "finals_rebuild" / "fixtures" / "pilot_audit"
    loaded = load_legacy_replay(fixture_root, treatments=["ab2"], repo_root=repo)
    assert len(loaded) == 1
    assert loaded[0].treatment == "ab2"
    assert loaded[0].source_fidelity == FIDELITY_EXTRACTED_ONLY
    assert "def generate" in loaded[0].extracted_code


def test_legacy_replay_pilot_extracted_only_loader():
    repo = resolve_repo_root()
    fixture_root = repo / "tests" / "finals_rebuild" / "fixtures" / "pilot_audit"
    loaded = load_legacy_replay_pilot(fixture_root, treatments=["ab2"], repo_root=repo)
    assert len(loaded) == 1
    assert loaded[0].treatment == "ab2"
    assert loaded[0].extracted_code is not None


def test_auto_format_detection(tmp_path):
    _write_attempts(tmp_path, [_attempt("HumanEval/0", "ab1", "def f():\n    pass\n")])
    assert detect_source_format(tmp_path) == SOURCE_FORMAT_GENERATION_ATTEMPTS

    pb = tmp_path / "pb"
    evalplus = pb / "public_benchmark" / "humaneval" / "evalplus"
    evalplus.mkdir(parents=True)
    (evalplus / "ab1.jsonl").write_text(
        '{"task_id":"HumanEval/0","completion":"def f():\\n    pass\\n"}\n',
        encoding="utf-8",
    )
    assert detect_source_format(pb) == SOURCE_FORMAT_PUBLIC_BENCHMARK

    legacy = tmp_path / "legacy"
    legacy.mkdir()
    (legacy / "legacy_replay_results.json").write_text("[]", encoding="utf-8")
    assert detect_source_format(legacy) == SOURCE_FORMAT_LEGACY_REPLAY

    pilot = tmp_path / "pilot"
    pilot.mkdir()
    (pilot / "case_results.jsonl").write_text("", encoding="utf-8")
    assert detect_source_format(pilot) == SOURCE_FORMAT_LEGACY_REPLAY_PILOT


def test_unsupported_auto_detection_fails(tmp_path):
    with pytest.raises(PilotArtifactLoaderError, match="cannot auto-detect"):
        detect_source_format(tmp_path)


def test_unknown_treatment_preserved_in_legacy_pilot():
    repo = resolve_repo_root()
    fixture_root = repo / "tests" / "finals_rebuild" / "fixtures" / "pilot_audit"
    case_path = fixture_root / "case_results.jsonl"
    before = case_path.read_text(encoding="utf-8")
    try:
        case_path.write_text(
            json.dumps(
                {
                    "case_id": "unknown_case",
                    "skill_id": "jh_test_skill",
                    "source_ab2_path": "tests/finals_rebuild/fixtures/pilot_audit/legacy_ab2_sample.py",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        loaded = load_legacy_replay_pilot(fixture_root, treatments=["unknown"], repo_root=repo)
        assert loaded == []
        loaded_all = load_legacy_replay_pilot(fixture_root, treatments=["ab2"], repo_root=repo)
        assert loaded_all[0].treatment == "ab2"
    finally:
        case_path.write_text(before, encoding="utf-8")


def test_load_pilot_samples_rejects_ambiguous_auto(tmp_path):
    _write_attempts(tmp_path, [_attempt("HumanEval/0", "ab1", "def f():\n    pass\n")])
    evalplus = tmp_path / "public_benchmark" / "humaneval" / "evalplus"
    evalplus.mkdir(parents=True)
    (evalplus / "ab1.jsonl").write_text(
        '{"task_id":"HumanEval/0","completion":"def f():\\n    pass\\n"}\n',
        encoding="utf-8",
    )
    with pytest.raises(PilotArtifactLoaderError, match="ambiguous"):
        load_pilot_samples(tmp_path, source_format="auto")
