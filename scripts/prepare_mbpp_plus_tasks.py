#!/usr/bin/env python3
"""Export model-visible MBPP+ task fields from the official EvalPlus loader."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import platform
import sys
from collections.abc import Mapping
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

EXPECTED_EVALPLUS_VERSION = "0.3.1"
EXPECTED_DATASET_VERSION = "v0.2.0"
EXPECTED_ENVIRONMENT = f"MBPP_PLUS_VERSION={EXPECTED_DATASET_VERSION}"
EXPECTED_TASK_COUNT = 378
TASK_FIELDS = ("task_id", "prompt", "entry_point")
FORBIDDEN_FIELDS = frozenset(
    {
        "canonical_solution",
        "solution",
        "code",
        "test",
        "tests",
        "test_list",
        "base_input",
        "plus_input",
        "contract",
        "oracle",
        "expected_output",
        "reference_answer",
    }
)


class MbppPlusExportError(RuntimeError):
    """Fail-closed error for MBPP+ metadata export."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def task_ids_sha256(task_ids: list[str]) -> str:
    return sha256_bytes(("\n".join(task_ids) + "\n").encode("utf-8"))


def build_task_records(dataset: Mapping[str, Mapping[str, Any]]) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    seen: set[str] = set()
    for mapping_task_id, problem in dataset.items():
        task_id = problem.get("task_id")
        prompt = problem.get("prompt")
        entry_point = problem.get("entry_point")
        if task_id != mapping_task_id:
            raise MbppPlusExportError(
                f"loader key/task_id mismatch: {mapping_task_id!r} != {task_id!r}"
            )
        if not isinstance(task_id, str) or not task_id.startswith("Mbpp/"):
            raise MbppPlusExportError(f"invalid MBPP+ task_id: {task_id!r}")
        suffix = task_id.removeprefix("Mbpp/")
        if not suffix.isdigit():
            raise MbppPlusExportError(f"non-numeric MBPP+ task_id: {task_id!r}")
        if task_id in seen:
            raise MbppPlusExportError(f"duplicate MBPP+ task_id: {task_id}")
        if not isinstance(prompt, str) or not prompt.strip():
            raise MbppPlusExportError(f"{task_id}: missing non-empty official prompt")
        if not isinstance(entry_point, str) or not entry_point.strip():
            raise MbppPlusExportError(f"{task_id}: missing non-empty official entry_point")
        seen.add(task_id)
        records.append(
            {"task_id": task_id, "prompt": prompt, "entry_point": entry_point}
        )
    if len(records) != EXPECTED_TASK_COUNT:
        raise MbppPlusExportError(
            f"expected {EXPECTED_TASK_COUNT} official MBPP+ tasks, got {len(records)}"
        )
    return records


def render_tasks_jsonl(dataset: Mapping[str, Mapping[str, Any]]) -> bytes:
    records = build_task_records(dataset)
    lines = [
        json.dumps(record, ensure_ascii=False, separators=(",", ":"))
        for record in records
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def build_manifest(
    *,
    records: list[dict[str, str]],
    tasks_bytes: bytes,
    dataset_hash: str,
    created_at_utc: str,
    python_version: str,
) -> dict[str, Any]:
    task_ids = [record["task_id"] for record in records]
    return {
        "created_at_utc": created_at_utc,
        "creation_script": "scripts/prepare_mbpp_plus_tasks.py",
        "dataset_name": "MBPP+",
        "dataset_role": "official_task_prompts_and_evalplus_tests",
        "environment_variable": EXPECTED_ENVIRONMENT,
        "evalplus_dataset_hash": dataset_hash,
        "evalplus_package_version": EXPECTED_EVALPLUS_VERSION,
        "fallback_policy": "forbidden_original_mbpp",
        "first_task_id": task_ids[0],
        "last_task_id": task_ids[-1],
        "notes": [
            "Exported through evalplus.data.get_mbpp_plus via the repository EvalPlus bridge",
            "No fallback to original non-Plus MBPP is allowed",
            "Official tests, canonical solutions, contracts, inputs, and expected outputs are not stored",
            "Only task_id, prompt, and entry_point are model-visible in tasks.jsonl",
        ],
        "official_tests_and_canonical_solutions_included": False,
        "release_tag_or_dataset_version": EXPECTED_DATASET_VERSION,
        "source_loader": "evalplus.data.get_mbpp_plus",
        "source_prompt_field": "prompt",
        "source_repository": "https://github.com/evalplus/evalplus",
        "stored_fields": list(TASK_FIELDS),
        "task_count": len(records),
        "task_ids_sha256": task_ids_sha256(task_ids),
        "task_order_policy": "official_loader_order",
        "tasks_file": "data/mbpp_plus/tasks.jsonl",
        "tasks_sha256": sha256_bytes(tasks_bytes),
        "wsl_python_version": python_version,
    }


def export_mbpp_plus(
    *,
    tasks_path: pathlib.Path,
    manifest_path: pathlib.Path,
    created_at_utc: str,
) -> dict[str, Any]:
    if os.environ.get("MBPP_PLUS_VERSION") != EXPECTED_DATASET_VERSION:
        raise MbppPlusExportError(
            f"environment must contain {EXPECTED_ENVIRONMENT}"
        )

    from agent_tools.finals_rebuild.evalplus_bridge import (  # noqa: PLC0415
        get_evalplus_version,
        load_evalplus_dataset,
    )

    evalplus_version = get_evalplus_version()
    if evalplus_version != EXPECTED_EVALPLUS_VERSION:
        raise MbppPlusExportError(
            f"expected evalplus {EXPECTED_EVALPLUS_VERSION}, got {evalplus_version}"
        )
    dataset, dataset_hash = load_evalplus_dataset("mbpp", None)
    records = build_task_records(dataset)
    tasks_bytes = render_tasks_jsonl(dataset)
    manifest = build_manifest(
        records=records,
        tasks_bytes=tasks_bytes,
        dataset_hash=dataset_hash,
        created_at_utc=created_at_utc,
        python_version=platform.python_version(),
    )

    tasks_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    tasks_path.write_bytes(tasks_bytes)
    manifest_path.write_bytes(
        (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
            "utf-8"
        )
    )
    return manifest


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tasks-out",
        type=pathlib.Path,
        default=REPO_ROOT / "data/mbpp_plus/tasks.jsonl",
    )
    parser.add_argument(
        "--manifest-out",
        type=pathlib.Path,
        default=REPO_ROOT / "data/mbpp_plus/dataset_manifest.json",
    )
    parser.add_argument("--created-at-utc", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    created_at_utc = args.created_at_utc or dt.datetime.now(dt.timezone.utc).isoformat()
    manifest = export_mbpp_plus(
        tasks_path=args.tasks_out,
        manifest_path=args.manifest_out,
        created_at_utc=created_at_utc,
    )
    print(
        json.dumps(
            {
                "dataset_hash": manifest["evalplus_dataset_hash"],
                "evalplus_package_version": manifest["evalplus_package_version"],
                "first_task_id": manifest["first_task_id"],
                "last_task_id": manifest["last_task_id"],
                "task_count": manifest["task_count"],
                "tasks_sha256": manifest["tasks_sha256"],
                "wsl_python_version": manifest["wsl_python_version"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
