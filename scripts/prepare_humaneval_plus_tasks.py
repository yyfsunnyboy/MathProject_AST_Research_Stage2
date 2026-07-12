#!/usr/bin/env python3
"""Offline conversion of official HumanEvalPlus.jsonl.gz to runner tasks.jsonl."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from agent_tools.finals_rebuild.humaneval_plus_dataset import (  # noqa: E402
    EXPECTED_TASK_COUNT,
    HumanevalPlusDatasetError,
    OFFICIAL_ASSET_NAME,
    prepare_tasks_file,
)


def build_arg_parser() -> argparse.ArgumentParser:
    data_root = REPO_ROOT / "data" / "humaneval_plus"
    parser = argparse.ArgumentParser(
        description="Prepare HumanEval+ tasks.jsonl from official source asset."
    )
    parser.add_argument(
        "--source",
        default=str(data_root / "source" / OFFICIAL_ASSET_NAME),
        help="Path to official HumanEvalPlus.jsonl.gz",
    )
    parser.add_argument(
        "--tasks-out",
        default=str(data_root / "tasks.jsonl"),
        help="Output runner tasks JSONL path.",
    )
    parser.add_argument(
        "--manifest-out",
        default=str(data_root / "dataset_manifest.json"),
        help="Output dataset manifest JSON path.",
    )
    parser.add_argument(
        "--expected-source-sha256",
        default=None,
        help="Optional fail-closed SHA-256 check for the source gzip file.",
    )
    parser.add_argument(
        "--downloaded-at-utc",
        default=None,
        help="Optional downloaded_at_utc to record in manifest.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        manifest = prepare_tasks_file(
            source_path=args.source,
            tasks_path=args.tasks_out,
            manifest_path=args.manifest_out,
            creation_script="scripts/prepare_humaneval_plus_tasks.py",
            expected_source_sha256=args.expected_source_sha256,
            downloaded_at_utc=args.downloaded_at_utc,
        )
        tasks_path = pathlib.Path(args.tasks_out)
        lines = [
            json.loads(line)
            for line in tasks_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        print(
            json.dumps(
                {
                    "task_count": len(lines),
                    "first_task_id": lines[0]["task_id"],
                    "twentieth_task_id": lines[19]["task_id"],
                    "last_task_id": lines[-1]["task_id"],
                    "tasks_sha256": manifest["tasks_sha256"],
                    "source_sha256": manifest["source_sha256"],
                },
                indent=2,
                sort_keys=True,
            )
        )
        if len(lines) != EXPECTED_TASK_COUNT:
            raise HumanevalPlusDatasetError(
                f"post-write validation failed: expected {EXPECTED_TASK_COUNT}, got {len(lines)}"
            )
        return 0
    except HumanevalPlusDatasetError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
