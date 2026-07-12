"""
Tests for agent_tools/finals_rebuild/evalplus_bridge.py

All EvalPlus package/API and subprocess interactions are mocked — this
suite never invokes the real evalplus package (not installed, and not
runnable on native Windows anyway; see the module's own platform guard).
"""

from __future__ import annotations

import inspect
import json
import os
import subprocess
import sys
import types
import pathlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import pytest

import agent_tools.finals_rebuild.evalplus_bridge as bridge
from agent_tools.finals_rebuild.evalplus_bridge import (
    EvalPlusBridgeError,
    build_arg_parser,
    filter_samples_by_task_ids,
    is_native_windows,
    load_completion_samples,
    main,
    parse_task_ids,
    run_evalplus_bridge,
)

_HUMANEVAL_DATASET = {
    "HumanEval/0": {"prompt": "def add(a, b):\n"},
    "HumanEval/1": {"prompt": "def double(x):\n"},
}


def _write_samples(tmp_path, records):
    path = tmp_path / "samples.jsonl"
    with open(path, "w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec) + "\n")
    return path


def _fake_evalplus_module(version="0.1.0"):
    mod = types.ModuleType("evalplus")
    mod.__version__ = version
    return mod


def _fake_evalplus_data_module(dataset=_HUMANEVAL_DATASET, dataset_hash="fixedhash123"):
    mod = types.ModuleType("evalplus.data")
    mod.get_human_eval_plus = lambda: dict(dataset)
    mod.get_human_eval_plus_hash = lambda: dataset_hash
    mod.get_mbpp_plus = lambda: dict(dataset)
    mod.get_mbpp_plus_hash = lambda: dataset_hash
    return mod


def _install_fake_evalplus(monkeypatch, dataset=_HUMANEVAL_DATASET, dataset_hash="fixedhash123", version="0.1.0"):
    fake_evalplus = _fake_evalplus_module(version)
    fake_data = _fake_evalplus_data_module(dataset, dataset_hash)
    monkeypatch.setitem(sys.modules, "evalplus", fake_evalplus)
    monkeypatch.setitem(sys.modules, "evalplus.data", fake_data)


def _make_completed_process(returncode=0, stdout="ok", stderr=""):
    return subprocess.CompletedProcess(args=["fake"], returncode=returncode, stdout=stdout, stderr=stderr)


def _write_official_result(samples_path: pathlib.Path, eval_mapping: dict):
    result_path = samples_path.with_name(samples_path.stem + "_eval_results.json")
    result_path.write_text(json.dumps({"eval": eval_mapping}), encoding="utf-8")
    return result_path


# ============================================================
# 1. CLI parser
# ============================================================


def test_cli_parser_basic():
    parser = build_arg_parser()
    args = parser.parse_args([
        "--benchmark", "humaneval",
        "--samples", "s.jsonl",
        "--output-dir", "out",
    ])
    assert args.benchmark == "humaneval"
    assert args.samples == "s.jsonl"
    assert args.output_dir == "out"
    assert args.task_ids is None
    assert args.dataset_version is None


# ============================================================
# 2 & 3. --task-ids comma parsing, dedupe preserving order
# ============================================================


def test_task_ids_comma_parsing():
    assert parse_task_ids("HumanEval/0,HumanEval/1") == ["HumanEval/0", "HumanEval/1"]


def test_task_ids_dedupe_preserves_order():
    assert parse_task_ids("HumanEval/1,HumanEval/0,HumanEval/1") == ["HumanEval/1", "HumanEval/0"]


def test_task_ids_strips_whitespace():
    assert parse_task_ids(" HumanEval/0 , HumanEval/1 ") == ["HumanEval/0", "HumanEval/1"]


# ============================================================
# 4. empty task list fail closed
# ============================================================


def test_empty_task_ids_string_fails_closed():
    with pytest.raises(EvalPlusBridgeError):
        parse_task_ids("")


def test_task_ids_with_empty_entry_fails_closed():
    with pytest.raises(EvalPlusBridgeError):
        parse_task_ids("HumanEval/0,,HumanEval/1")


# ============================================================
# 5. nonexistent task fail closed
# ============================================================


def test_nonexistent_task_id_fails_closed():
    samples = [{"task_id": "HumanEval/0", "completion": "x"}]
    with pytest.raises(EvalPlusBridgeError, match="not present"):
        filter_samples_by_task_ids(samples, ["HumanEval/999"])


# ============================================================
# 6. filtering to 0 samples fail closed
# ============================================================


def test_filter_to_zero_samples_fails_closed():
    samples = [{"task_id": "HumanEval/0", "completion": "x"}]
    with pytest.raises(EvalPlusBridgeError):
        filter_samples_by_task_ids(samples, [])


def test_filter_none_means_no_filter():
    samples = [{"task_id": "HumanEval/0", "completion": "x"}]
    assert filter_samples_by_task_ids(samples, None) == samples


# ============================================================
# 7. duplicate task sample in n=1 mode fail closed
# ============================================================


def test_duplicate_task_id_in_samples_fails_closed(tmp_path):
    path = _write_samples(tmp_path, [
        {"task_id": "HumanEval/0", "completion": "a"},
        {"task_id": "HumanEval/0", "completion": "b"},
    ])
    with pytest.raises(EvalPlusBridgeError, match="more than once"):
        load_completion_samples(path)


# ============================================================
# 8. empty completion fail closed
# ============================================================


def test_empty_completion_fails_closed(tmp_path):
    path = _write_samples(tmp_path, [{"task_id": "HumanEval/0", "completion": "   "}])
    with pytest.raises(EvalPlusBridgeError, match="completion"):
        load_completion_samples(path)


def test_empty_task_id_fails_closed(tmp_path):
    path = _write_samples(tmp_path, [{"task_id": "", "completion": "x"}])
    with pytest.raises(EvalPlusBridgeError):
        load_completion_samples(path)


# ============================================================
# 9. native Windows preflight blocks
# ============================================================


def test_windows_preflight_blocks(monkeypatch, tmp_path):
    monkeypatch.setattr(bridge, "is_native_windows", lambda: True)
    samples_path = _write_samples(tmp_path, [{"task_id": "HumanEval/0", "completion": "x"}])
    with pytest.raises(EvalPlusBridgeError, match="not supported in this native Windows"):
        run_evalplus_bridge(
            benchmark="humaneval", samples_path=samples_path,
            output_dir=tmp_path / "out",
        )
    failure = json.loads((tmp_path / "out" / "failure.json").read_text(encoding="utf-8"))
    assert failure["status"] == "failed_preflight"
    assert not (tmp_path / "out" / "evalplus_summary.json").exists()


# ============================================================
# 10. Linux runtime not falsely blocked
# ============================================================


def test_linux_runtime_not_blocked(monkeypatch):
    monkeypatch.setattr(bridge.os, "name", "posix")
    monkeypatch.setattr(bridge.sys, "platform", "linux")
    assert is_native_windows() is False


def test_windows_native_detected():
    import agent_tools.finals_rebuild.evalplus_bridge as mod
    # This test runs on the actual dev machine (native Windows) with no
    # monkeypatching, confirming the real runtime is correctly detected.
    assert mod.is_native_windows() is True


# ============================================================
# 11. EvalPlus import failure fail closed
# ============================================================


def test_evalplus_import_failure_fails_closed(monkeypatch, tmp_path):
    monkeypatch.setattr(bridge, "is_native_windows", lambda: False)
    monkeypatch.delitem(sys.modules, "evalplus", raising=False)

    def _raise_import(*a, **k):
        raise ImportError("no evalplus installed")

    monkeypatch.setattr(bridge, "get_evalplus_version", lambda: (_ for _ in ()).throw(
        EvalPlusBridgeError("evalplus_import", "failed to import evalplus: no evalplus installed")
    ))

    samples_path = _write_samples(tmp_path, [{"task_id": "HumanEval/0", "completion": "x"}])
    with pytest.raises(EvalPlusBridgeError, match="import"):
        run_evalplus_bridge(
            benchmark="humaneval", samples_path=samples_path, output_dir=tmp_path / "out",
        )
    failure = json.loads((tmp_path / "out" / "failure.json").read_text(encoding="utf-8"))
    assert failure["status"] == "failed_preflight"


# ============================================================
# 12. version cannot be determined fail closed
# ============================================================


def test_version_undeterminable_fails_closed(monkeypatch, tmp_path):
    monkeypatch.setattr(bridge, "is_native_windows", lambda: False)
    fake_evalplus = types.ModuleType("evalplus")  # no __version__ attribute
    monkeypatch.setitem(sys.modules, "evalplus", fake_evalplus)
    monkeypatch.setattr(
        "importlib.metadata.version",
        lambda name: (_ for _ in ()).throw(Exception("not found")),
    )
    with pytest.raises(EvalPlusBridgeError, match="version"):
        bridge.get_evalplus_version()


# ============================================================
# 13. dataset loader failure fail closed
# ============================================================


def test_dataset_loader_failure_fails_closed(monkeypatch, tmp_path):
    monkeypatch.setattr(bridge, "is_native_windows", lambda: False)
    _install_fake_evalplus(monkeypatch)
    fake_data = sys.modules["evalplus.data"]
    fake_data.get_human_eval_plus = lambda: (_ for _ in ()).throw(RuntimeError("network fetch failed"))

    with pytest.raises(EvalPlusBridgeError, match="dataset loader"):
        bridge.load_evalplus_dataset("humaneval", "fixedhash123")


# ============================================================
# 14. empty dataset fail closed
# ============================================================


def test_empty_dataset_fails_closed(monkeypatch):
    monkeypatch.setattr(bridge, "is_native_windows", lambda: False)
    _install_fake_evalplus(monkeypatch, dataset={})
    with pytest.raises(EvalPlusBridgeError, match="no tasks"):
        bridge.load_evalplus_dataset("humaneval", "fixedhash123")


# ============================================================
# 15. sample task not in dataset fail closed
# ============================================================


def test_sample_task_not_in_dataset_fails_closed():
    with pytest.raises(EvalPlusBridgeError, match="not present in the official"):
        bridge.verify_dataset_covers_samples(["HumanEval/0"], ["HumanEval/999"])


# ============================================================
# 16. no fallback to original HumanEval
# ============================================================


def test_no_fallback_when_loader_missing(monkeypatch):
    monkeypatch.setattr(bridge, "is_native_windows", lambda: False)
    fake_evalplus = _fake_evalplus_module()
    fake_data = types.ModuleType("evalplus.data")  # no get_human_eval_plus at all
    monkeypatch.setitem(sys.modules, "evalplus", fake_evalplus)
    monkeypatch.setitem(sys.modules, "evalplus.data", fake_data)
    with pytest.raises(EvalPlusBridgeError, match="refusing to fall back"):
        bridge.load_evalplus_dataset("humaneval", "v1")


def test_no_fallback_module_source_never_references_jsonl_gz():
    # The module docstring legitimately *mentions* HumanEval.jsonl.gz and
    # openai_humaneval by name to disclaim them (documenting what this
    # module refuses to do) — check import statements specifically, since
    # that's what would indicate an actual fallback usage.
    src = inspect.getsource(bridge)
    import_lines = "\n".join(
        line.strip() for line in src.splitlines()
        if line.strip().startswith(("import ", "from "))
    )
    assert "datasets" not in import_lines
    assert "gzip" not in import_lines


# ============================================================
# 17. subprocess non-zero exit fail closed
# ============================================================


def test_subprocess_nonzero_exit_fails_closed(monkeypatch, tmp_path):
    monkeypatch.setattr(bridge, "is_native_windows", lambda: False)
    _install_fake_evalplus(monkeypatch)
    monkeypatch.setattr(
        bridge, "_invoke_evalplus_cli",
        lambda **kw: _make_completed_process(returncode=1, stdout="", stderr="boom"),
    )
    samples_path = _write_samples(tmp_path, [{"task_id": "HumanEval/0", "completion": "x"}])
    with pytest.raises(EvalPlusBridgeError, match="return code"):
        run_evalplus_bridge(
            benchmark="humaneval", samples_path=samples_path, output_dir=tmp_path / "out",
            dataset_version="fixedhash123",
        )
    assert (tmp_path / "out" / "stderr.txt").read_text(encoding="utf-8") == "boom"
    failure = json.loads((tmp_path / "out" / "failure.json").read_text(encoding="utf-8"))
    assert failure["status"] == "failed_execution"


# ============================================================
# 18. subprocess timeout fail closed
# ============================================================


def test_subprocess_timeout_fails_closed(monkeypatch, tmp_path):
    monkeypatch.setattr(bridge, "is_native_windows", lambda: False)
    _install_fake_evalplus(monkeypatch)

    def _raise_timeout(**kw):
        raise EvalPlusBridgeError("subprocess", "official EvalPlus CLI timed out after 1.0s")

    monkeypatch.setattr(bridge, "_invoke_evalplus_cli", _raise_timeout)
    samples_path = _write_samples(tmp_path, [{"task_id": "HumanEval/0", "completion": "x"}])
    with pytest.raises(EvalPlusBridgeError, match="timed out"):
        run_evalplus_bridge(
            benchmark="humaneval", samples_path=samples_path, output_dir=tmp_path / "out",
            dataset_version="fixedhash123",
        )


# ============================================================
# 19. official result file missing fail closed
# ============================================================


def test_official_result_file_missing_fails_closed(monkeypatch, tmp_path):
    monkeypatch.setattr(bridge, "is_native_windows", lambda: False)
    _install_fake_evalplus(monkeypatch)
    monkeypatch.setattr(bridge, "_invoke_evalplus_cli", lambda **kw: _make_completed_process())
    samples_path = _write_samples(tmp_path, [{"task_id": "HumanEval/0", "completion": "x"}])
    # Deliberately do NOT write the *_eval_results.json file.
    with pytest.raises(EvalPlusBridgeError, match="not found"):
        run_evalplus_bridge(
            benchmark="humaneval", samples_path=samples_path, output_dir=tmp_path / "out",
            dataset_version="fixedhash123",
        )


# ============================================================
# 20. official result parse failure fail closed
# ============================================================


def test_official_result_parse_failure_fails_closed(monkeypatch, tmp_path):
    monkeypatch.setattr(bridge, "is_native_windows", lambda: False)
    _install_fake_evalplus(monkeypatch)
    monkeypatch.setattr(bridge, "_invoke_evalplus_cli", lambda **kw: _make_completed_process())
    samples_path = _write_samples(tmp_path, [{"task_id": "HumanEval/0", "completion": "x"}])
    result_path = samples_path.with_name(samples_path.stem + "_eval_results.json")
    result_path.write_text("{ not valid json", encoding="utf-8")
    with pytest.raises(EvalPlusBridgeError, match="failed to parse"):
        run_evalplus_bridge(
            benchmark="humaneval", samples_path=samples_path, output_dir=tmp_path / "out",
            dataset_version="fixedhash123",
        )


def test_official_result_missing_eval_key_fails_closed(tmp_path):
    result_path = tmp_path / "x_eval_results.json"
    result_path.write_text(json.dumps({"not_eval": {}}), encoding="utf-8")
    with pytest.raises(EvalPlusBridgeError, match="'eval'"):
        bridge._parse_official_result_file(result_path)


# ============================================================
# 21. manifest contains version/hash/task count; full success path
# ============================================================


def test_manifest_contains_version_hash_task_count(monkeypatch, tmp_path):
    monkeypatch.setattr(bridge, "is_native_windows", lambda: False)
    _install_fake_evalplus(monkeypatch)
    samples_path = _write_samples(tmp_path, [
        {"task_id": "HumanEval/0", "completion": "def add(a, b):\n    return a + b\n"},
    ])
    monkeypatch.setattr(bridge, "_invoke_evalplus_cli", lambda **kw: _make_completed_process())
    _write_official_result(samples_path, {"HumanEval/0": [{"plus_status": "pass"}]})

    summary = run_evalplus_bridge(
        benchmark="humaneval", samples_path=samples_path, output_dir=tmp_path / "out",
        dataset_version=None,  # resolved via get_human_eval_plus_hash()
    )
    manifest = json.loads((tmp_path / "out" / "evalplus_manifest.json").read_text(encoding="utf-8"))
    assert manifest["evalplus_version"] == "0.1.0"
    assert manifest["dataset_version"] == "fixedhash123"
    assert manifest["dataset_task_count"] == len(_HUMANEVAL_DATASET)
    assert manifest["samples_sha256"] == bridge.compute_samples_sha256(samples_path)
    assert manifest["status"] == "success"
    assert summary["status"] == "success"


# ============================================================
# 22. summary never fabricates pass@1
# ============================================================


def test_summary_pass_at_1_comes_from_official_result(monkeypatch, tmp_path):
    monkeypatch.setattr(bridge, "is_native_windows", lambda: False)
    _install_fake_evalplus(monkeypatch)
    samples_path = _write_samples(tmp_path, [
        {"task_id": "HumanEval/0", "completion": "def add(a, b):\n    return a + b\n"},
        {"task_id": "HumanEval/1", "completion": "def double(x):\n    return x * 2\n"},
    ])
    monkeypatch.setattr(bridge, "_invoke_evalplus_cli", lambda **kw: _make_completed_process())
    _write_official_result(samples_path, {
        "HumanEval/0": [{"plus_status": "pass"}],
        "HumanEval/1": [{"plus_status": "fail", "error_type": "AssertionError", "error_message": "boom"}],
    })
    summary = run_evalplus_bridge(
        benchmark="humaneval", samples_path=samples_path, output_dir=tmp_path / "out",
        dataset_version="fixedhash123",
    )
    assert summary["total"] == 2
    assert summary["passed"] == 1
    assert summary["failed"] == 1
    assert summary["pass_at_1"] == 0.5

    results = json.loads((tmp_path / "out" / "evalplus_results.json").read_text(encoding="utf-8"))
    r1 = next(r for r in results if r["task_id"] == "HumanEval/1")
    assert r1["passed"] is False
    assert r1["error_type"] == "AssertionError"


# ============================================================
# 23 & 24. completion never concatenated with prompt / never modified
# ============================================================


def test_completion_not_concatenated_or_modified(tmp_path):
    original = "    return a + b\n"
    path = _write_samples(tmp_path, [{"task_id": "HumanEval/0", "completion": original}])
    samples = load_completion_samples(path)
    assert samples[0]["completion"] == original
    assert "def " not in samples[0]["completion"]


# ============================================================
# 25. failure never produces a success summary
# ============================================================


def test_failure_never_produces_success_summary(monkeypatch, tmp_path):
    monkeypatch.setattr(bridge, "is_native_windows", lambda: True)
    samples_path = _write_samples(tmp_path, [{"task_id": "HumanEval/0", "completion": "x"}])
    with pytest.raises(EvalPlusBridgeError):
        run_evalplus_bridge(
            benchmark="humaneval", samples_path=samples_path, output_dir=tmp_path / "out",
        )
    assert not (tmp_path / "out" / "evalplus_summary.json").exists()
    assert not (tmp_path / "out" / "evalplus_results.json").exists()


# ============================================================
# 26. stdout/stderr saved
# ============================================================


def test_stdout_stderr_saved_on_success(monkeypatch, tmp_path):
    monkeypatch.setattr(bridge, "is_native_windows", lambda: False)
    _install_fake_evalplus(monkeypatch)
    samples_path = _write_samples(tmp_path, [{"task_id": "HumanEval/0", "completion": "x"}])
    monkeypatch.setattr(
        bridge, "_invoke_evalplus_cli",
        lambda **kw: _make_completed_process(stdout="hello stdout", stderr="hello stderr"),
    )
    _write_official_result(samples_path, {"HumanEval/0": [{"plus_status": "pass"}]})
    run_evalplus_bridge(
        benchmark="humaneval", samples_path=samples_path, output_dir=tmp_path / "out",
        dataset_version="fixedhash123",
    )
    assert (tmp_path / "out" / "stdout.txt").read_text(encoding="utf-8") == "hello stdout"
    assert (tmp_path / "out" / "stderr.txt").read_text(encoding="utf-8") == "hello stderr"


def test_stdout_stderr_saved_on_windows_guard_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(bridge, "is_native_windows", lambda: True)
    samples_path = _write_samples(tmp_path, [{"task_id": "HumanEval/0", "completion": "x"}])
    with pytest.raises(EvalPlusBridgeError):
        run_evalplus_bridge(
            benchmark="humaneval", samples_path=samples_path, output_dir=tmp_path / "out",
        )
    assert (tmp_path / "out" / "stdout.txt").exists()
    assert (tmp_path / "out" / "stderr.txt").exists()


# ============================================================
# 27. output deterministic across reruns
# ============================================================


def test_output_deterministic_across_reruns(monkeypatch, tmp_path):
    monkeypatch.setattr(bridge, "is_native_windows", lambda: False)
    _install_fake_evalplus(monkeypatch)
    samples_path = _write_samples(tmp_path, [
        {"task_id": "HumanEval/0", "completion": "def add(a, b):\n    return a + b\n"},
    ])
    monkeypatch.setattr(bridge, "_invoke_evalplus_cli", lambda **kw: _make_completed_process())
    _write_official_result(samples_path, {"HumanEval/0": [{"plus_status": "pass"}]})

    out1 = tmp_path / "out1"
    out2 = tmp_path / "out2"
    run_evalplus_bridge(benchmark="humaneval", samples_path=samples_path, output_dir=out1, dataset_version="fixedhash123")
    run_evalplus_bridge(benchmark="humaneval", samples_path=samples_path, output_dir=out2, dataset_version="fixedhash123")

    for name in ("evalplus_results.json", "evalplus_summary.json"):
        assert (out1 / name).read_bytes() == (out2 / name).read_bytes()

    manifest1 = json.loads((out1 / "evalplus_manifest.json").read_text(encoding="utf-8"))
    manifest2 = json.loads((out2 / "evalplus_manifest.json").read_text(encoding="utf-8"))
    for key in ("benchmark", "samples_sha256", "evalplus_version", "dataset_version",
                "dataset_task_count", "evaluated_task_ids", "sample_count", "status"):
        assert manifest1[key] == manifest2[key]


# ============================================================
# 28. never calls a model
# ============================================================


def test_no_model_calls_structural():
    src = inspect.getsource(bridge)
    for forbidden in ("openai", "anthropic", "google.generativeai", "call_ai_with_retry"):
        assert forbidden not in src


# ============================================================
# 29. never calls Core/Spec adapter
# ============================================================


def test_no_core_or_spec_adapter_calls_structural():
    src = inspect.getsource(bridge)
    for forbidden in ("run_core_adapter", "run_spec_adapter", "core_adapter", "spec_adapter"):
        assert forbidden not in src


# ============================================================
# 30. never uses the repo's own TestSuite
# ============================================================


def test_no_own_testsuite_structural():
    # The module docstring legitimately *mentions* TestSuite/test_contract
    # by name to disclaim them; check import statements specifically.
    src = inspect.getsource(bridge)
    import_lines = "\n".join(
        line.strip() for line in src.splitlines()
        if line.strip().startswith(("import ", "from "))
    )
    assert "test_contract" not in import_lines
    assert "TestSuite" not in import_lines


# ============================================================
# Additional: --shell=True never used; args are a list
# ============================================================


def test_subprocess_never_uses_shell_true(monkeypatch):
    # Functional check: intercept the real subprocess.run() call and
    # assert shell was never requested and cmd is a list, not a string.
    captured = {}
    orig_run = subprocess.run

    def spy_run(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["shell"] = kwargs.get("shell", False)
        return _make_completed_process()

    monkeypatch.setattr(bridge.subprocess, "run", spy_run)
    bridge._invoke_evalplus_cli(
        benchmark="humaneval", samples_path=pathlib.Path("s.jsonl"), timeout_seconds=5.0
    )
    assert captured["shell"] is False
    assert isinstance(captured["cmd"], list)


def test_main_returns_nonzero_on_windows(monkeypatch, tmp_path):
    monkeypatch.setattr(bridge, "is_native_windows", lambda: True)
    samples_path = _write_samples(tmp_path, [{"task_id": "HumanEval/0", "completion": "x"}])
    exit_code = main([
        "--benchmark", "humaneval",
        "--samples", str(samples_path),
        "--output-dir", str(tmp_path / "out"),
    ])
    assert exit_code == 1
