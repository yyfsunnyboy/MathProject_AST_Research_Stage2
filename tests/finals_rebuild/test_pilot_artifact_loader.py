"""
Tests for agent_tools/finals_rebuild/pilot_artifact_loader.py
"""

from __future__ import annotations

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from agent_tools.finals_rebuild.artifacts import sha256_text
from agent_tools.finals_rebuild.pilot_artifact_loader import (
    PilotArtifactLoaderError,
    load_generation_attempts_first,
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
    assert ab1[0].source_record_index == 1


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
    assert len(loaded) == 1
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


def test_ambiguous_without_ordinal_or_marker(tmp_path):
    _write_attempts(
        tmp_path,
        [
            _attempt("HumanEval/0", "ab1", "def a():\n    pass\n"),
            _attempt("HumanEval/0", "ab1", "def b():\n    pass\n"),
        ],
    )
    loaded = load_generation_attempts_first(tmp_path, treatments=["ab1"])
    assert loaded[0].first_attempt_selection_status == "ambiguous"
    assert loaded[0].raw_response == "def a():\n    pass\n"


def test_source_file_not_modified(tmp_path):
    path = _write_attempts(
        tmp_path,
        [_attempt("HumanEval/0", "ab1", "def f():\n    return 1\n")],
    )
    before = path.read_text(encoding="utf-8")
    load_generation_attempts_first(tmp_path)
    after = path.read_text(encoding="utf-8")
    assert before == after


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
    by_key = {(s.task_id, s.treatment): s for s in loaded}
    assert by_key[("HumanEval/0", "ab1")].raw_response.endswith("return 1\n")
    assert by_key[("HumanEval/0", "ab2g")].raw_response.endswith("return 2\n")


def test_pilot_flags_fixed(tmp_path):
    _write_attempts(tmp_path, [_attempt("HumanEval/0", "ab1", "def f():\n    pass\n")])
    loaded = load_generation_attempts_first(tmp_path)
    assert loaded[0].pilot_only is True
    assert loaded[0].confirmatory_eligible is False


def test_missing_generation_attempts_fails_closed(tmp_path):
    with pytest.raises(PilotArtifactLoaderError, match="not found"):
        load_generation_attempts_first(tmp_path)
