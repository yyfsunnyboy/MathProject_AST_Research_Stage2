"""
Tests for agent_tools/finals_rebuild/humaneval_plus_dataset.py
"""

from __future__ import annotations

import gzip
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from agent_tools.finals_rebuild.benchmarks_adapter import load_benchmark_tasks
from agent_tools.finals_rebuild.humaneval_plus_dataset import (
    EXPECTED_TASK_COUNT,
    HumanevalPlusDatasetError,
    load_source_records,
    prepare_tasks_file,
    prepare_tasks_from_source,
    sha256_file,
    verify_source_sha256,
    write_tasks_jsonl,
)


def _write_source_gzip(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _sample_records(n: int):
    return [
        {
            "task_id": f"HumanEval/{i}",
            "prompt": f"def f{i}():\n    \"\"\"doc {i}\"\"\"\n",
            "entry_point": f"f{i}",
            "canonical_solution": "    return 1\n",
            "test": "def check(candidate): pass",
        }
        for i in range(n)
    ]


def test_prepare_requires_exactly_164_tasks():
    with pytest.raises(HumanevalPlusDatasetError, match="expected exactly 164"):
        prepare_tasks_from_source(_sample_records(2))


def test_prepare_preserves_order_and_unique_task_ids(tmp_path):
    records = _sample_records(EXPECTED_TASK_COUNT)
    tasks = prepare_tasks_from_source(records)
    assert [t["task_id"] for t in tasks] == [f"HumanEval/{i}" for i in range(EXPECTED_TASK_COUNT)]
    assert len({t["task_id"] for t in tasks}) == EXPECTED_TASK_COUNT


def test_prepare_fails_on_duplicate_task_id():
    records = _sample_records(EXPECTED_TASK_COUNT)
    records[1]["task_id"] = records[0]["task_id"]
    with pytest.raises(HumanevalPlusDatasetError, match="duplicate task_id"):
        prepare_tasks_from_source(records)


def test_prepare_fails_on_missing_prompt():
    records = _sample_records(EXPECTED_TASK_COUNT)
    records[5]["prompt"] = ""
    with pytest.raises(HumanevalPlusDatasetError, match="missing or empty prompt"):
        prepare_tasks_from_source(records)


def test_prepare_fails_on_missing_entry_point():
    records = _sample_records(EXPECTED_TASK_COUNT)
    records[5]["entry_point"] = "   "
    with pytest.raises(HumanevalPlusDatasetError, match="missing or empty entry_point"):
        prepare_tasks_from_source(records)


def test_output_schema_exact_and_no_tests_or_solution(tmp_path):
    records = _sample_records(EXPECTED_TASK_COUNT)
    tasks = prepare_tasks_from_source(records)
    out = tmp_path / "tasks.jsonl"
    write_tasks_jsonl(tasks, out)
    loaded = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert set(loaded[0].keys()) == {"task_id", "prompt", "entry_point"}
    assert "canonical_solution" not in loaded[0]
    assert "test" not in loaded[0]


def test_utf8_prompt_preserved(tmp_path):
    records = _sample_records(EXPECTED_TASK_COUNT)
    records[0]["prompt"] = 'def f0():\n    """中文註解 → ok"""\n'
    tasks = prepare_tasks_from_source(records)
    out = tmp_path / "tasks.jsonl"
    write_tasks_jsonl(tasks, out)
    loaded = json.loads(out.read_text(encoding="utf-8").splitlines()[0])
    assert "中文註解 → ok" in loaded["prompt"]


def test_source_sha_mismatch_fails_closed(tmp_path):
    src = tmp_path / "source.jsonl.gz"
    _write_source_gzip(src, _sample_records(EXPECTED_TASK_COUNT))
    with pytest.raises(HumanevalPlusDatasetError, match="SHA256 mismatch"):
        verify_source_sha256(src, "0" * 64)


def test_prepare_tasks_file_offline_roundtrip(tmp_path):
    src = tmp_path / "HumanEvalPlus.jsonl.gz"
    records = _sample_records(EXPECTED_TASK_COUNT)
    _write_source_gzip(src, records)
    tasks_out = tmp_path / "tasks.jsonl"
    manifest_out = tmp_path / "dataset_manifest.json"
    manifest = prepare_tasks_file(
        source_path=src,
        tasks_path=tasks_out,
        manifest_path=manifest_out,
        creation_script="tests/prepare_fixture.py",
        expected_source_sha256=sha256_file(src),
    )
    assert manifest["task_count"] == EXPECTED_TASK_COUNT
    loaded = load_benchmark_tasks(tasks_out, "humaneval")
    assert len(loaded) == EXPECTED_TASK_COUNT
    assert loaded[0].task_id == "HumanEval/0"
    assert loaded[19].task_id == "HumanEval/19"
    assert loaded[-1].task_id == "HumanEval/163"
    assert loaded[0].canonical_solution is None


def test_load_source_records_rejects_invalid_json(tmp_path):
    bad = tmp_path / "bad.jsonl"
    bad.write_text("{not json}\n", encoding="utf-8")
    with pytest.raises(HumanevalPlusDatasetError, match="invalid JSON"):
        load_source_records(bad)


def test_manifest_notes_no_humaneval_fallback(tmp_path):
    src = tmp_path / "HumanEvalPlus.jsonl.gz"
    _write_source_gzip(src, _sample_records(EXPECTED_TASK_COUNT))
    manifest_out = tmp_path / "dataset_manifest.json"
    prepare_tasks_file(
        source_path=src,
        tasks_path=tmp_path / "tasks.jsonl",
        manifest_path=manifest_out,
        creation_script="tests/prepare_fixture.py",
    )
    manifest = json.loads(manifest_out.read_text(encoding="utf-8"))
    assert any("No fallback to original HumanEval" in note for note in manifest["notes"])
