#!/usr/bin/env python3
"""Merge and verify Validation20 cross-machine per-model results.

Never regenerates candidates. Never re-runs EvalPlus. Fail-closed on hash,
roster, schema, or model-identity mismatches.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import freeze_mbpp_validation20_scaffold_healer_v3 as freeze  # noqa: E402


class MergeError(RuntimeError):
    """Fail-closed merge violation."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise MergeError(message)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_model_bundle(*, model_tag: str, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    _require(model_tag in freeze.ALLOWED_MODEL_TAGS, f"unsupported model: {model_tag}")
    _require("2b" not in model_tag.lower(), "2B results forbidden")
    spec = freeze.MODEL_SPECS[model_tag]
    model_manifest = _read_json(repo_root / freeze.model_dir(model_tag) / "model_manifest.json")
    cells = _read_csv(repo_root / freeze.model_dir(model_tag) / "generation_cells.csv")
    _require(len(cells) == 400, f"{model_tag}: generation cells != 400")
    _require(model_manifest["model"]["tag"] == model_tag, "model manifest tag drift")

    run_dir = repo_root / spec["run_output_relative"]
    eval_dir = repo_root / spec["evalplus_output_relative"]
    raw_ledger = run_dir / "raw_candidate_sha_ledger.csv"
    deriv_manifest = run_dir / "derivatives" / "derivatives_manifest.json"
    exec_manifest = eval_dir / "execution_manifest.json"
    cell_ledger = eval_dir / "cell_level_ledger.csv"

    missing = [
        path.as_posix()
        for path in (raw_ledger, deriv_manifest, exec_manifest, cell_ledger)
        if not path.is_file()
    ]
    complete = not missing
    report: dict[str, Any] = {
        "model_tag": model_tag,
        "operator_role": spec["operator_role"],
        "complete": complete,
        "missing_artifacts": missing,
        "identity_status": model_manifest["model"]["identity_status"],
        "model_digest_pinned": model_manifest["model"].get("digest"),
    }
    if not complete:
        return report

    raw_rows = _read_csv(raw_ledger)
    eval_rows = _read_csv(cell_ledger)
    execution = _read_json(exec_manifest)
    _require(len(raw_rows) == 400, f"{model_tag}: raw ledger != 400")
    _require(len(eval_rows) == 1200, f"{model_tag}: eval ledger != 1200")
    _require(execution["model_tag"] == model_tag, "execution manifest model drift")
    _require(execution["dataset_hash"] == freeze.DATASET_HASH, "dataset hash drift")
    _require(execution["evalplus_version"] == freeze.EVALPLUS_VERSION, "evalplus version drift")
    _require(
        _sha256_bytes(cell_ledger.read_bytes()) == execution["results_sha256"],
        "cell ledger SHA mismatch vs execution_manifest",
    )

    # Missing-cell / stage pairing checks.
    by_generation: dict[str, set[str]] = {}
    for row in eval_rows:
        _require(row["model_tag"] == model_tag, "foreign model row in eval ledger")
        by_generation.setdefault(row["generation_id"], set()).add(row["stage"])
    _require(len(by_generation) == 400, "eval generation coverage drift")
    for generation_id, stages in by_generation.items():
        _require(stages == set(freeze.STAGES), f"incomplete stages for {generation_id}")

    report.update(
        {
            "raw_candidates": len(raw_rows),
            "eval_cells": len(eval_rows),
            "execution_manifest_sha256": _sha256_bytes(exec_manifest.read_bytes()),
            "cell_ledger_sha256": execution["results_sha256"],
            "evalplus_executed": True,
        }
    )
    return report


def merge_all(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    reports = {
        tag: verify_model_bundle(model_tag=tag, repo_root=repo_root)
        for tag in freeze.ALLOWED_MODEL_TAGS
    }
    complete_models = [tag for tag, row in reports.items() if row["complete"]]
    incomplete_models = [tag for tag, row in reports.items() if not row["complete"]]
    merged = {
        "status": (
            "cross_machine_merge_complete"
            if len(complete_models) == 3
            else "cross_machine_merge_partial"
        ),
        "plan_id": freeze.PLAN_ID,
        "expected_models": list(freeze.ALLOWED_MODEL_TAGS),
        "complete_models": complete_models,
        "incomplete_models": incomplete_models,
        "per_model": reports,
        "totals_if_complete": {
            "immutable_candidates": 1200,
            "evalplus_cells": 3600,
            "primary_comparison_rows_raw_vs_post_healer": 2400,
            "pipeline_attribution_rows": 1200,
        },
        "model_calls": 0,
        "candidate_program_executed": False,
        "evalplus_executed_by_this_merge_tool": False,
        "note": (
            "Merge verifies independently produced per-model bundles; "
            "it never re-executes EvalPlus or regenerates candidates."
        ),
    }
    out = repo_root / freeze.ARTIFACT_RELATIVE / "cross_machine_merge_report.json"
    out.write_text(json.dumps(merged, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    merged["report_path"] = out.relative_to(repo_root).as_posix()
    return merged


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model",
        choices=freeze.ALLOWED_MODEL_TAGS,
        help="Verify one model bundle only.",
    )
    parser.add_argument(
        "--merge-all",
        action="store_true",
        help="Verify all three model bundles and write merge report.",
    )
    args = parser.parse_args(argv)
    if args.model:
        print(json.dumps(verify_model_bundle(model_tag=args.model), indent=2, sort_keys=True))
        return 0
    if args.merge_all:
        print(json.dumps(merge_all(), indent=2, sort_keys=True))
        return 0
    raise SystemExit("specify --model or --merge-all")


if __name__ == "__main__":
    raise SystemExit(main())
