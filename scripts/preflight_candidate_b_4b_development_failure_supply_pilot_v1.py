#!/usr/bin/env python3
"""Zero-model preflight for the 4B development failure-supply pilot.

Does not call Ollama generation, does not execute candidate code, does not
run EvalPlus, and does not modify Healer.
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

from scripts import freeze_candidate_b_4b_development_failure_supply_pilot_v1 as freeze  # noqa: E402

FROZEN_MANIFEST_RELATIVE = freeze.OUTPUT_RELATIVE / "manifest.json"


class PilotPreflightError(RuntimeError):
    """Fail-closed preflight violation."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PilotPreflightError(message)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def compute_manifest_sha256(repo_root: Path) -> str:
    return _sha256_bytes((repo_root / FROZEN_MANIFEST_RELATIVE).read_bytes())


def assert_output_isolation(repo_root: Path, manifest: dict[str, Any]) -> None:
    pilot_dir = repo_root / freeze.RUN_OUTPUT_RELATIVE
    for relative in manifest["parity_with_9b"]["isolated_from_9b_output_dirs"]:
        other = repo_root / relative
        _require(
            other.resolve() != pilot_dir.resolve(),
            f"pilot output collides with isolated path: {relative}",
        )
        _require(
            freeze.RUN_OUTPUT_RELATIVE.as_posix() not in relative,
            f"isolation list malformed: {relative}",
        )


def assert_development_only(cells: list[dict[str, str]], manifest: dict[str, Any]) -> None:
    _require(len(cells) == freeze.EXPECTED_CELL_COUNT, "cell count != 200")
    _require(
        len({row["task_id"] for row in cells}) == freeze.EXPECTED_TASK_COUNT,
        "task count != 20",
    )
    _require(
        sorted({row["task_id"] for row in cells}) == sorted(freeze.ACTIVE_TASK_IDS),
        "task list drift vs frozen active20",
    )
    _require(
        all(row["development_only"] == "true" for row in cells),
        "non-development cell present",
    )
    seeds = sorted({int(row["seed"]) for row in cells})
    _require(seeds == list(freeze.SEEDS), f"seed drift: {seeds}")
    conditions = sorted({row["condition_id"] for row in cells})
    _require(
        conditions == ["Ab1_H0", "Ab2g_H1"],
        f"condition drift: {conditions}",
    )
    policy = manifest["split_policy"]
    _require(
        list(policy["forbidden_roles"]) == list(freeze.FORBIDDEN_ROLES),
        "forbidden role list drift",
    )
    _require(policy["forbid_validation"] is True, "validation not forbidden")
    _require(policy["forbid_confirmatory"] is True, "confirmatory not forbidden")
    _require(policy["forbid_sealed_reserve"] is True, "sealed_reserve not forbidden")
    _require(
        policy["forbid_humaneval_plus_external"] is True,
        "HumanEval+ external not forbidden",
    )
    _require(
        policy["allowed_role"] == "historical_development_pool",
        "allowed role drift",
    )


def assert_model_identity(manifest: dict[str, Any]) -> None:
    model = manifest["model"]
    _require(model["tag"] == freeze.MODEL_TAG, "model tag drift")
    _require(model["digest"] == freeze.MODEL_DIGEST, "model digest drift")
    _require(model["quantization"] == freeze.MODEL_QUANTIZATION, "quantization drift")
    _require(
        model["public_benchmark_general_execution_allowed"] is False,
        "general 4B public execution must remain disabled",
    )
    _require(model["pilot_execution_waiver"] == freeze.PILOT_WAIVER, "waiver drift")
    _require(
        len(model["digest"]) == 64 and all(c in "0123456789abcdef" for c in model["digest"]),
        "digest must be full 64-hex, not guessed short form",
    )


def assert_resume_policy(manifest: dict[str, Any]) -> None:
    policy = manifest["resume_policy"]
    _require(policy["overwrite_forbidden"] is True, "overwrite must be forbidden")
    required = {
        "cell_identity",
        "model_tag",
        "model_digest",
        "composed_prompt_sha256",
        "condition_id",
        "seed",
        "completion_flag=success",
    }
    _require(
        set(policy["resume_skip_requires_exact_match_of"]) == required,
        "resume match fields drift",
    )
    _require(policy["any_identity_mismatch"] == "fail_closed", "resume must fail closed")


def zero_model_preflight(
    *,
    repo_root: Path = REPO_ROOT,
    manifest_path: Path | None = None,
    manifest_sha256: str | None = None,
    require_output_absent: bool = True,
) -> dict[str, Any]:
    rebuilt = freeze.build_outputs(repo_root)
    expected_manifest = rebuilt["manifest.json"]
    expected_sha = _sha256_bytes(expected_manifest)
    path = manifest_path or (repo_root / FROZEN_MANIFEST_RELATIVE)
    _require(path.is_file(), f"missing manifest: {path.as_posix()}")
    actual = path.read_bytes()
    _require(actual == expected_manifest, "manifest bytes drift vs deterministic rebuild")
    actual_sha = _sha256_bytes(actual)
    if manifest_sha256 is not None:
        _require(
            actual_sha == manifest_sha256,
            f"manifest SHA mismatch: expected {manifest_sha256}, got {actual_sha}",
        )
    manifest = json.loads(actual.decode("utf-8"))
    cells = _read_csv(repo_root / freeze.OUTPUT_RELATIVE / "generation_cells.csv")
    assert_development_only(cells, manifest)
    assert_model_identity(manifest)
    assert_resume_policy(manifest)
    assert_output_isolation(repo_root, manifest)

    out_dir = repo_root / freeze.RUN_OUTPUT_RELATIVE
    if require_output_absent:
        _require(
            not out_dir.exists() or not any(out_dir.iterdir()),
            f"output directory already present; resume/overwrite forbidden until "
            f"exact identity match path is used: {out_dir.as_posix()}",
        )

    for name, payload in rebuilt.items():
        artifact = repo_root / freeze.OUTPUT_RELATIVE / name
        _require(artifact.is_file(), f"missing artifact: {artifact.as_posix()}")
        _require(
            artifact.read_bytes() == payload,
            f"artifact drift: {artifact.as_posix()}",
        )

    receipt = {
        "status": "zero_model_preflight_passed",
        "run_id": freeze.RUN_ID,
        "manifest_path": path.as_posix(),
        "manifest_sha256": actual_sha,
        "expected_manifest_sha256": expected_sha,
        "cell_count": len(cells),
        "task_count": len({row["task_id"] for row in cells}),
        "condition_count": len({row["condition_id"] for row in cells}),
        "model_tag": freeze.MODEL_TAG,
        "model_digest": freeze.MODEL_DIGEST,
        "model_calls": 0,
        "ollama_generation_calls": 0,
        "candidate_code_executions": 0,
        "evalplus_executions": 0,
        "healer_modifications": 0,
        "output_directory": freeze.RUN_OUTPUT_RELATIVE.as_posix(),
        "require_output_absent": require_output_absent,
        "development_only_verified": True,
    }
    _require(actual_sha == expected_sha, "internal SHA inconsistency")
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest-sha256",
        default=None,
        help="Optional exact manifest SHA-256 pin.",
    )
    parser.add_argument(
        "--allow-existing-output",
        action="store_true",
        help="Allow preflight when output dir exists (still does not generate).",
    )
    args = parser.parse_args(argv)
    receipt = zero_model_preflight(
        manifest_sha256=args.manifest_sha256,
        require_output_absent=not args.allow_existing_output,
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
