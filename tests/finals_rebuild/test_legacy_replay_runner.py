"""
Tests for agent_tools/finals_rebuild/legacy_replay_runner.py
"""

from __future__ import annotations

import inspect
import json
import os
import sys
import tempfile
import pathlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import pytest

from agent_tools.finals_rebuild.artifacts import sha256_text
from agent_tools.finals_rebuild.evaluation import EvaluationResult
from agent_tools.finals_rebuild.legacy_replay_runner import (
    LegacyReplayError,
    OPERATIONAL_REGRESSION,
    OPERATIONAL_RESCUED,
    OPERATIONAL_UNCHANGED_FAIL,
    OPERATIONAL_UNCHANGED_PASS,
    build_legacy_pair_id,
    classify_operational,
    run_legacy_replay,
)

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
_MANIFEST = os.path.join(
    _ROOT, "tests", "finals_rebuild", "fixtures", "legacy_replay_manifest.json"
)
_EVALUATOR_GIT_COMMIT = "e3d2e1b"

_FIXED_TS = "2000-01-01T00:00:00+00:00"


def _make_eval(*, syntax_pass, execution_success, treatment="ab2"):
    return EvaluationResult(
        pair_id="a" * 64,
        run_id="b" * 64,
        treatment=treatment,
        artifact_hash="c" * 64,
        evaluator_version="v1",
        evaluator_git_commit=_EVALUATOR_GIT_COMMIT,
        evaluator_config_hash="d" * 64,
        syntax_pass=syntax_pass,
        contract_status="not_required",
        execution_status=(
            "success" if execution_success else ("failure" if syntax_pass else "failure")
        ),
        execution_success=execution_success,
        isolation_level="guarded_subprocess_not_security_sandbox",
        stdout_summary="",
        stderr_summary="",
        return_code=0 if execution_success else 1,
        duration_ms=1.0,
        created_at_utc=_FIXED_TS,
        exception_type=None if syntax_pass else "SyntaxError",
    )


# ============================================================
# 1. All 7 loaded
# ============================================================


def test_all_7_entries_loaded(tmp_path):
    result = run_legacy_replay(
        manifest_path=_MANIFEST,
        project_root=_ROOT,
        artifact_root=tmp_path / "artifacts",
        output_dir=tmp_path / "out",
        evaluator_git_commit=_EVALUATOR_GIT_COMMIT,
    )
    assert len(result["results"]) == 7
    assert result["summary"]["total"] == 7


# ============================================================
# 2 & 3. Only run_core_adapter is called; Spec adapter never invoked
# ============================================================


def test_only_core_adapter_invoked_never_spec(tmp_path, monkeypatch):
    import agent_tools.finals_rebuild.legacy_replay_runner as mod

    calls = []
    orig_core = mod.run_core_adapter

    def spy_core(**kwargs):
        calls.append("core")
        return orig_core(**kwargs)

    monkeypatch.setattr(mod, "run_core_adapter", spy_core)

    src = inspect.getsource(mod)
    assert "run_spec_adapter" not in src
    assert "spec_adapter" not in src.lower()

    run_legacy_replay(
        manifest_path=_MANIFEST,
        project_root=_ROOT,
        artifact_root=tmp_path / "artifacts",
        output_dir=tmp_path / "out",
        evaluator_git_commit=_EVALUATOR_GIT_COMMIT,
    )
    assert len(calls) == 7


# ============================================================
# 4 & 5. before/after both get static evaluation + bounded execution
# ============================================================


def test_before_after_both_evaluated_statically_and_executed(tmp_path):
    result = run_legacy_replay(
        manifest_path=_MANIFEST,
        project_root=_ROOT,
        artifact_root=tmp_path / "artifacts",
        output_dir=tmp_path / "out",
        evaluator_git_commit=_EVALUATOR_GIT_COMMIT,
    )
    for r in result["results"]:
        before = r["before_evaluation"]
        after = r["after_evaluation"]
        # Static evaluation ran (syntax_pass is a real bool, not missing).
        assert isinstance(before["syntax_pass"], bool)
        assert isinstance(after["syntax_pass"], bool)
        # Bounded execution ran whenever syntax passed (execution_status
        # is not the speculative "not_run" sentinel from Commit 4A).
        assert before["execution_status"] != "not_run"
        assert after["execution_status"] != "not_run"


# ============================================================
# 6. test_pass is None
# ============================================================


def test_test_pass_is_always_none(tmp_path):
    result = run_legacy_replay(
        manifest_path=_MANIFEST,
        project_root=_ROOT,
        artifact_root=tmp_path / "artifacts",
        output_dir=tmp_path / "out",
        evaluator_git_commit=_EVALUATOR_GIT_COMMIT,
    )
    for r in result["results"]:
        assert r["test_status"] == "not_run"
        assert r["before_evaluation"]["test_pass"] is None
        assert r["after_evaluation"]["test_pass"] is None
        assert r["before_evaluation"]["tests_passed"] is None
        assert r["after_evaluation"]["tests_total"] is None


# ============================================================
# 7-10. Operational classification
# ============================================================


def test_classify_rescued():
    before = _make_eval(syntax_pass=False, execution_success=False)
    after = _make_eval(syntax_pass=True, execution_success=True, treatment="ab3_core")
    assert classify_operational(before, after) == OPERATIONAL_RESCUED


def test_classify_regression():
    before = _make_eval(syntax_pass=True, execution_success=True)
    after = _make_eval(syntax_pass=False, execution_success=False, treatment="ab3_core")
    assert classify_operational(before, after) == OPERATIONAL_REGRESSION


def test_classify_unchanged_pass():
    before = _make_eval(syntax_pass=True, execution_success=True)
    after = _make_eval(syntax_pass=True, execution_success=True, treatment="ab3_core")
    assert classify_operational(before, after) == OPERATIONAL_UNCHANGED_PASS


def test_classify_unchanged_fail():
    before = _make_eval(syntax_pass=False, execution_success=False)
    after = _make_eval(syntax_pass=False, execution_success=False, treatment="ab3_core")
    assert classify_operational(before, after) == OPERATIONAL_UNCHANGED_FAIL


def test_classify_none_execution_success_never_counts_as_pass():
    before = EvaluationResult(
        pair_id="a" * 64, run_id="b" * 64, treatment="ab2", artifact_hash="c" * 64,
        evaluator_version="v1", evaluator_git_commit=_EVALUATOR_GIT_COMMIT,
        evaluator_config_hash="d" * 64, syntax_pass=True, contract_status="not_required",
        execution_status="not_run", execution_success=None, created_at_utc=_FIXED_TS,
    )
    after = _make_eval(syntax_pass=True, execution_success=True, treatment="ab3_core")
    # before has execution_success=None -> must NOT be treated as pass.
    assert classify_operational(before, after) == OPERATIONAL_RESCUED


# ============================================================
# 11. net gain
# ============================================================


def test_operational_net_gain_definition():
    result = run_legacy_replay(
        manifest_path=_MANIFEST,
        project_root=_ROOT,
        artifact_root=tempfile.mkdtemp(),
        output_dir=tempfile.mkdtemp(),
        evaluator_git_commit=_EVALUATOR_GIT_COMMIT,
    )
    s = result["summary"]
    assert s["operational_net_gain"] == (
        s["operational_rescued"] - s["operational_regression"]
    )


# ============================================================
# 12. Same input reruns identically
# ============================================================


def test_rerun_is_fully_deterministic(tmp_path):
    out1 = tmp_path / "out1"
    out2 = tmp_path / "out2"
    r1 = run_legacy_replay(
        manifest_path=_MANIFEST, project_root=_ROOT,
        artifact_root=tmp_path / "art1", output_dir=out1,
        evaluator_git_commit=_EVALUATOR_GIT_COMMIT,
    )
    r2 = run_legacy_replay(
        manifest_path=_MANIFEST, project_root=_ROOT,
        artifact_root=tmp_path / "art2", output_dir=out2,
        evaluator_git_commit=_EVALUATOR_GIT_COMMIT,
    )
    # duration_ms/stdout_summary reflect real bounded-subprocess execution
    # timing and are NOT required to be reproducible (see
    # execution_evaluator.py's own docstring on this). The task's
    # reproducibility contract only covers the fields below plus summary
    # counts and JSON key ordering.
    assert r1["summary"] == r2["summary"]
    for res1, res2 in zip(r1["results"], r2["results"]):
        for key in (
            "pair_id", "skill_id", "sample_index", "source_path",
            "source_hash", "before_code_hash", "after_code_hash",
            "changed", "core_fix_count", "operational_classification",
            "test_status",
        ):
            assert res1[key] == res2[key], f"{key} differs between reruns"
        assert res1["trace"] == res2["trace"]

    summary1 = json.loads((out1 / "legacy_replay_summary.json").read_text(encoding="utf-8"))
    summary2 = json.loads((out2 / "legacy_replay_summary.json").read_text(encoding="utf-8"))
    assert summary1 == summary2
    assert list(json.loads((out1 / "legacy_replay_summary.json").read_text(encoding="utf-8")).keys()) == \
        sorted(summary1.keys())


def test_output_json_has_no_current_time_or_uuid(tmp_path):
    result = run_legacy_replay(
        manifest_path=_MANIFEST, project_root=_ROOT,
        artifact_root=tmp_path / "art", output_dir=tmp_path / "out",
        evaluator_git_commit=_EVALUATOR_GIT_COMMIT,
    )
    for r in result["results"]:
        assert r["trace"]["created_at_utc"] == _FIXED_TS
        assert r["before_evaluation"]["created_at_utc"] == _FIXED_TS
        assert r["after_evaluation"]["created_at_utc"] == _FIXED_TS


def test_output_json_uses_relative_source_paths(tmp_path):
    result = run_legacy_replay(
        manifest_path=_MANIFEST, project_root=_ROOT,
        artifact_root=tmp_path / "art", output_dir=tmp_path / "out",
        evaluator_git_commit=_EVALUATOR_GIT_COMMIT,
    )
    for r in result["results"]:
        assert not pathlib.Path(r["source_path"]).is_absolute()
        assert str(tmp_path) not in r["source_path"]


# ============================================================
# 13. source hash mismatch -> fail closed
# ============================================================


def _write_manifest(tmpdir: pathlib.Path, entries: list) -> pathlib.Path:
    manifest_path = tmpdir / "manifest.json"
    manifest_path.write_text(json.dumps(entries), encoding="utf-8")
    return manifest_path


def _write_legacy_source(tmpdir: pathlib.Path, name: str, code_body: str) -> pathlib.Path:
    p = tmpdir / name
    p.write_text(
        "# Advanced Healer: OFF\n# [AI GENERATED CODE]\n" + code_body,
        encoding="utf-8",
    )
    return p


def _entry(sample_id, skill_id, model_id, sample_index, path, source_hash):
    return {
        "sample_id": sample_id,
        "skill_id": skill_id,
        "model_id": model_id,
        "sample_index": sample_index,
        "source_ab2_path": path,
        "source_kind": "legacy_extracted_code",
        "is_original_raw": False,
        "legacy_replay": True,
        "healer_status": "unknown",
        "source_file_hash": source_hash,
    }


def test_source_hash_mismatch_fails_closed(tmp_path):
    from agent_tools.finals_rebuild.legacy_migration import compute_source_hash

    entries = []
    for i in range(7):
        src = _write_legacy_source(
            tmp_path, f"s{i}.py", f"def generate_{i}():\n    return {i}\n"
        )
        correct_hash = compute_source_hash(src)
        # Entry 0 deliberately declares the wrong hash; the rest are correct
        # so the "expected exactly 7" check passes and the hash check is
        # what actually fires.
        declared_hash = "0" * 64 if i == 0 else correct_hash
        entries.append(_entry(f"s{i}", "skill_a", "model_a", i, f"s{i}.py", declared_hash))
    manifest = _write_manifest(tmp_path, entries)

    with pytest.raises(LegacyReplayError, match="source_file_hash mismatch"):
        run_legacy_replay(
            manifest_path=manifest, project_root=tmp_path,
            artifact_root=tmp_path / "art", output_dir=tmp_path / "out",
            evaluator_git_commit=_EVALUATOR_GIT_COMMIT,
        )


# ============================================================
# 14. source missing -> fail closed
# ============================================================


def test_source_missing_fails_closed(tmp_path):
    entry = _entry("s1", "skill_a", "model_a", 0, "missing.py", "0" * 64)
    manifest = _write_manifest(tmp_path, [entry])

    with pytest.raises(LegacyReplayError):
        run_legacy_replay(
            manifest_path=manifest, project_root=tmp_path,
            artifact_root=tmp_path / "art", output_dir=tmp_path / "out",
            evaluator_git_commit=_EVALUATOR_GIT_COMMIT,
        )


def test_manifest_missing_fails_closed(tmp_path):
    with pytest.raises(LegacyReplayError, match="manifest not found"):
        run_legacy_replay(
            manifest_path=tmp_path / "does_not_exist.json", project_root=tmp_path,
            artifact_root=tmp_path / "art", output_dir=tmp_path / "out",
            evaluator_git_commit=_EVALUATOR_GIT_COMMIT,
        )


# ============================================================
# 15. migration result not 7 -> fail closed
# ============================================================


def test_migration_non_7_fails_closed(tmp_path):
    from agent_tools.finals_rebuild.legacy_migration import compute_source_hash

    src = _write_legacy_source(tmp_path, "s1.py", "def generate():\n    return 1\n")
    entry = _entry("s1", "skill_a", "model_a", 0, "s1.py", compute_source_hash(src))
    manifest = _write_manifest(tmp_path, [entry])  # only 1 entry, not 7

    with pytest.raises(LegacyReplayError, match="expected exactly 7"):
        run_legacy_replay(
            manifest_path=manifest, project_root=tmp_path,
            artifact_root=tmp_path / "art", output_dir=tmp_path / "out",
            evaluator_git_commit=_EVALUATOR_GIT_COMMIT,
        )


# ============================================================
# 16. No fake functional-correctness output
# ============================================================


def test_no_fake_functional_correctness_output(tmp_path):
    result = run_legacy_replay(
        manifest_path=_MANIFEST, project_root=_ROOT,
        artifact_root=tmp_path / "art", output_dir=tmp_path / "out",
        evaluator_git_commit=_EVALUATOR_GIT_COMMIT,
    )
    results_json = json.loads((tmp_path / "out" / "legacy_replay_results.json").read_text(encoding="utf-8"))
    summary_json = json.loads((tmp_path / "out" / "legacy_replay_summary.json").read_text(encoding="utf-8"))

    forbidden_keys = ("pass_at_1", "pass_rate", "accuracy", "score", "percentage")
    blob = json.dumps(results_json) + json.dumps(summary_json)
    for key in forbidden_keys:
        assert key not in blob

    for r in result["results"]:
        assert r["test_status"] == "not_run"
        assert r["before_evaluation"]["test_pass"] is None
        assert r["after_evaluation"]["test_pass"] is None


# ============================================================
# Additional: pair_id determinism, duplicate identity fail closed
# ============================================================


def test_build_legacy_pair_id_is_deterministic():
    pid1 = build_legacy_pair_id("s1", "skill_a", "model_a", 0, "h" * 64)
    pid2 = build_legacy_pair_id("s1", "skill_a", "model_a", 0, "h" * 64)
    assert pid1 == pid2


def test_build_legacy_pair_id_changes_with_sample_id():
    pid1 = build_legacy_pair_id("s1", "skill_a", "model_a", 0, "h" * 64)
    pid2 = build_legacy_pair_id("s2", "skill_a", "model_a", 0, "h" * 64)
    assert pid1 != pid2


def test_no_model_or_network_calls_structural():
    import agent_tools.finals_rebuild.legacy_replay_runner as mod

    src = inspect.getsource(mod)
    for forbidden in (
        "openai", "anthropic", "google.generativeai", "call_ai_with_retry",
        "semantic_heal", "run_spec_adapter",
    ):
        assert forbidden not in src, f"forbidden reference {forbidden!r} found"
    # No TestSuite import/usage (the docstring only *mentions* TestSuite by
    # name to explain what this module deliberately does NOT create).
    assert "import TestSuite" not in src
    assert "TestSuite(" not in src


def test_summary_json_keys_present(tmp_path):
    run_legacy_replay(
        manifest_path=_MANIFEST, project_root=_ROOT,
        artifact_root=tmp_path / "art", output_dir=tmp_path / "out",
        evaluator_git_commit=_EVALUATOR_GIT_COMMIT,
    )
    summary = json.loads((tmp_path / "out" / "legacy_replay_summary.json").read_text(encoding="utf-8"))
    expected_keys = {
        "total", "changed_count", "unchanged_count",
        "operational_rescued", "operational_regression",
        "operational_unchanged_pass", "operational_unchanged_fail",
        "operational_net_gain", "not_test_assessable_count",
    }
    assert set(summary.keys()) == expected_keys
