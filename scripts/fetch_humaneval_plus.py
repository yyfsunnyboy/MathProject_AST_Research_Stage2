#!/usr/bin/env python3
"""Download the official HumanEval+ release asset into data/humaneval_plus/source/."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from agent_tools.finals_rebuild.humaneval_plus_dataset import (  # noqa: E402
    HumanevalPlusDatasetError,
    OFFICIAL_ASSET_NAME,
    fetch_official_source,
    write_json_deterministic,
)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch official HumanEvalPlus.jsonl.gz")
    parser.add_argument(
        "--dest",
        default=str(REPO_ROOT / "data" / "humaneval_plus" / "source" / OFFICIAL_ASSET_NAME),
        help="Destination path for the official gzip asset.",
    )
    parser.add_argument(
        "--expected-sha256",
        default=None,
        help="Optional expected SHA-256 of the downloaded gzip file.",
    )
    parser.add_argument(
        "--write-fetch-metadata",
        action="store_true",
        help="Write fetch_metadata.json beside the source asset.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        result = fetch_official_source(
            args.dest,
            expected_sha256=args.expected_sha256,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        if args.write_fetch_metadata:
            meta_path = pathlib.Path(args.dest).with_name("fetch_metadata.json")
            write_json_deterministic(result, meta_path)
        return 0
    except HumanevalPlusDatasetError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
