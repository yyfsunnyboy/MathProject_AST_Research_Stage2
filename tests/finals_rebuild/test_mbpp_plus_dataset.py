from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts import prepare_mbpp_plus_tasks as exporter

TASKS_PATH = REPO_ROOT / "data/mbpp_plus/tasks.jsonl"
MANIFEST_PATH = REPO_ROOT / "data/mbpp_plus/dataset_manifest.json"


def _records() -> list[dict[str, str]]:
    return [
        json.loads(line)
        for line in TASKS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _manifest() -> dict[str, object]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def test_tasks_have_exact_safe_fields_and_valid_unique_ids():
    records = _records()
    task_ids = [record["task_id"] for record in records]

    assert len(records) == 378
    assert len(task_ids) == len(set(task_ids))
    assert all(re.fullmatch(r"Mbpp/[0-9]+", task_id) for task_id in task_ids)
    assert all(tuple(record) == exporter.TASK_FIELDS for record in records)
    assert all(isinstance(record["prompt"], str) and record["prompt"].strip() for record in records)
    assert all(
        isinstance(record["entry_point"], str) and record["entry_point"].strip()
        for record in records
    )
    assert all(not (set(record) & exporter.FORBIDDEN_FIELDS) for record in records)


def test_manifest_pins_official_evalplus_provenance_and_no_fallback():
    manifest = _manifest()

    assert manifest["dataset_name"] == "MBPP+"
    assert manifest["task_count"] == 378
    assert manifest["evalplus_package_version"] == "0.3.1"
    assert manifest["release_tag_or_dataset_version"] == "v0.2.0"
    assert manifest["environment_variable"] == "MBPP_PLUS_VERSION=v0.2.0"
    assert manifest["source_loader"] == "evalplus.data.get_mbpp_plus"
    assert manifest["fallback_policy"] == "forbidden_original_mbpp"
    assert manifest["official_tests_and_canonical_solutions_included"] is False


def test_manifest_hashes_match_exported_bytes_and_official_order():
    records = _records()
    manifest = _manifest()
    task_ids = [record["task_id"] for record in records]

    assert hashlib.sha256(TASKS_PATH.read_bytes()).hexdigest() == manifest["tasks_sha256"]
    assert exporter.task_ids_sha256(task_ids) == manifest["task_ids_sha256"]
    assert manifest["task_order_policy"] == "official_loader_order"
    assert manifest["first_task_id"] == task_ids[0]
    assert manifest["last_task_id"] == task_ids[-1]


def test_task_serialization_is_byte_deterministic():
    records = _records()
    loader_order_mapping = {
        record["task_id"]: {
            "task_id": record["task_id"],
            "prompt": record["prompt"],
            "entry_point": record["entry_point"],
        }
        for record in records
    }

    first = exporter.render_tasks_jsonl(loader_order_mapping)
    second = exporter.render_tasks_jsonl(loader_order_mapping)
    assert first == second == TASKS_PATH.read_bytes()
