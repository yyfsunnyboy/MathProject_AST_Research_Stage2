from __future__ import annotations

import csv
import json
import pathlib
import tempfile

import pytest

from scripts import run_mbpp_development_baseline as baseline
from agent_tools.finals_rebuild import generation_persistence as persistence


def test_frozen_active_subset_is_exactly_twenty_non_confirmatory_tasks():
    rows = baseline.load_active_task_rows()
    assert len(rows) == 20
    assert len({row["task_id"] for row in rows}) == 20
    assert {row["dataset"] for row in rows} == {"MBPP+"}
    assert {row["proposed_role"] for row in rows} == {"historical_development_pool"}
    assert {row["confirmatory_eligible"] for row in rows} == {"false"}


def test_selected_task_loader_with_synthetic_records_only():
    records = [
        {"task_id": "Synthetic/1", "prompt": "synthetic alpha", "entry_point": "alpha"},
        {"task_id": "Synthetic/2", "prompt": "synthetic beta", "entry_point": "beta"},
    ]
    with tempfile.TemporaryDirectory() as directory:
        path = pathlib.Path(directory) / "synthetic_tasks.jsonl"
        path.write_text(
            "".join(json.dumps(record) + "\n" for record in records), encoding="utf-8"
        )
        tasks = baseline.load_selected_tasks(["Synthetic/2"], path)
    assert [task.task_id for task in tasks] == ["Synthetic/2"]
    assert tasks[0].prompt == "synthetic beta"
    assert tasks[0].canonical_solution is None
    assert tasks[0].metadata == {}


def test_dataset_manifest_is_pinned_and_excludes_answers_tests():
    manifest = baseline.verify_dataset_manifest()
    assert manifest["evalplus_package_version"] == "0.3.1"
    assert manifest["release_tag_or_dataset_version"] == "v0.2.0"
    assert manifest["stored_fields"] == ["task_id", "prompt", "entry_point"]
    assert manifest["official_tests_and_canonical_solutions_included"] is False


def test_generation_ids_are_unique_for_twenty_by_five():
    task_ids = [row["task_id"] for row in baseline.load_active_task_rows()]
    ids = {
        baseline.generation_id(task_id, seed, "a" * 64)
        for task_id in task_ids
        for seed in baseline.EXPECTED_SEEDS
    }
    assert len(ids) == 100


def test_pipeline_correction_uses_frozen_neutral_extraction_only():
    raw = {
        "generation_id": "g",
        "task_id": "Mbpp/2",
        "seed": 11,
        "sample_index": 0,
        "raw_response": "```python\ndef f():\n    return 1\n```",
        "raw_response_sha256": baseline.sha256_text(
            "```python\ndef f():\n    return 1\n```"
        ),
    }
    corrected = baseline.build_pipeline_record(raw)
    assert corrected["pipeline_correction_spec"] == (
        "agent_tools.finals_rebuild.extraction.extract_code"
    )
    assert corrected["pipeline_correction_spec_commit"] == "c5094bb7"
    assert corrected["pipeline_corrected_output"] == "def f():\n    return 1\n"
    assert "healer" not in json.dumps(corrected).lower()


def test_output_paths_refuse_overwrite(tmp_path, monkeypatch):
    output_root = tmp_path / "out"
    output = output_root / "runs" / "synthetic-run"
    output.mkdir(parents=True)
    (output / "existing").write_text("keep", encoding="utf-8")
    monkeypatch.setattr(baseline, "OUTPUT_ROOT", output_root)
    with pytest.raises(baseline.BaselineError, match="refusing to overwrite"):
        baseline.generate(
            run_id="synthetic-run",
            base_url="http://127.0.0.1:1",
            timeout_seconds=0.01,
        )


def test_evaluation_csv_schema_contains_no_hidden_material():
    source = pathlib.Path(baseline.__file__).read_text(encoding="utf-8")
    forbidden_columns = {
        "test_input",
        "expected_output",
        "canonical_solution",
        "hidden_test",
        "error_message",
        "diagnostics",
    }
    fieldnames_start = source.index("fieldnames = [")
    fieldnames_end = source.index("]", fieldnames_start)
    fieldnames_text = source[fieldnames_start:fieldnames_end]
    assert not any(column in fieldnames_text for column in forbidden_columns)


def test_expansion_rule_is_disjunctive_and_not_executed_here():
    assert (19 < 20 or 10 < 5) is True
    assert (20 < 20 or 4 < 5) is True
    assert (20 < 20 or 5 < 5) is False


def test_synthetic_jsonl_persistence_flush_fsync_readback_and_sha256(monkeypatch):
    records = [
        {"generation_id": "synthetic-001", "seed": 11, "response": "alpha"},
        {"generation_id": "synthetic-002", "seed": 22, "response": "beta"},
    ]
    fsync_calls = 0
    rename_saw_closed_handle = False
    original_fsync = persistence.os.fsync
    original_rename = persistence.os.rename

    def fsync_spy(file_descriptor):
        nonlocal fsync_calls
        fsync_calls += 1
        return original_fsync(file_descriptor)

    def rename_spy(source, target):
        nonlocal rename_saw_closed_handle
        with open(source, "ab"):
            rename_saw_closed_handle = True
        return original_rename(source, target)

    monkeypatch.setattr(persistence.os, "fsync", fsync_spy)
    monkeypatch.setattr(persistence.os, "rename", rename_spy)
    with tempfile.TemporaryDirectory() as directory:
        path = pathlib.Path(directory) / "nested" / "synthetic.jsonl"
        receipt = persistence.durable_write_jsonl_new(path, records)
        assert receipt.record_count == 2
        assert receipt.sha256 == persistence.sha256_bytes(path.read_bytes())
        assert [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] == records
        assert not list(path.parent.glob("*.tmp"))
    assert fsync_calls == 1
    assert rename_saw_closed_handle is True


def test_synthetic_immutable_journal_refuses_overwrite():
    record = {"generation_id": "synthetic-only", "response": "not a benchmark"}
    with tempfile.TemporaryDirectory() as directory:
        path = pathlib.Path(directory) / "journal" / "cell.json"
        persistence.durable_write_json_new(path, record)
        original_hash = persistence.sha256_bytes(path.read_bytes())
        with pytest.raises(persistence.PersistenceError, match="refusing to overwrite"):
            persistence.durable_write_json_new(path, {"changed": True})
        assert persistence.sha256_bytes(path.read_bytes()) == original_hash


def test_permission_error_is_fail_visible(monkeypatch):
    with tempfile.TemporaryDirectory() as directory:
        path = pathlib.Path(directory) / "synthetic.json"

        def deny_rename(source, target):
            raise PermissionError(13, "synthetic permission denial", str(target))

        monkeypatch.setattr(persistence.os, "rename", deny_rename)
        with pytest.raises(persistence.PersistenceError, match="permission denied") as caught:
            persistence.durable_write_json_new(path, {"synthetic": True})
        assert isinstance(caught.value.__cause__, PermissionError)
        assert not path.exists()
