#!/usr/bin/env python3
"""Zero-model / zero-candidate-execution preflight for Validation20 generation."""

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


class PreflightError(RuntimeError):
    """Fail-closed preflight violation."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PreflightError(message)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def resolve_model_tag(model: str) -> str:
    _require(model in freeze.ALLOWED_MODEL_TAGS, f"unsupported --model: {model}")
    return model


def assert_output_isolation(repo_root: Path, model_tag: str) -> None:
    spec = freeze.MODEL_SPECS[model_tag]
    run_dir = (repo_root / spec["run_output_relative"]).resolve()
    for relative in freeze.FORBIDDEN_OUTPUT_COLLISION_RELATIVES:
        other = (repo_root / relative).resolve()
        _require(other != run_dir, f"output collides with forbidden path: {relative}")
    for peer_tag in freeze.ALLOWED_MODEL_TAGS:
        if peer_tag == model_tag:
            continue
        peer = (repo_root / freeze.MODEL_SPECS[peer_tag]["run_output_relative"]).resolve()
        _require(peer != run_dir, f"output collides with peer model {peer_tag}")


def assert_cells(cells: list[dict[str, str]], model_tag: str) -> None:
    _require(len(cells) == 400, f"{model_tag}: cell count != 400")
    _require(all(row["model_tag"] == model_tag for row in cells), "foreign model cell present")
    _require(all(row["validation_only"] == "true" for row in cells), "non-validation cell")
    _require(
        all(row["forbid_development_substitute"] == "true" for row in cells),
        "development substitute not forbidden",
    )
    _require(
        sorted({row["task_id"] for row in cells}) == sorted(freeze.VALIDATION_TASK_IDS),
        "task roster drift",
    )
    _require(
        sorted({int(row["seed"]) for row in cells}) == list(freeze.SEEDS),
        "seed drift",
    )
    expected_conditions = [row["prompt_condition"] for row in freeze.PROMPT_CONDITIONS]
    _require(
        sorted({row["prompt_condition"] for row in cells}) == sorted(expected_conditions),
        "prompt condition drift",
    )


def assert_model_identity_for_preflight(manifest: dict[str, Any], *, require_verified: bool) -> None:
    model = manifest["model"]
    _require(model["tag"] in freeze.ALLOWED_MODEL_TAGS, "model tag not in allowed set")
    _require("2b" not in model["tag"].lower(), "2B models are forbidden")
    _require(model["machine_verified_identity_required_before_generate"] is True, "identity gate missing")
    if require_verified:
        _require(
            model["identity_status"] == "machine_verified_on_build_host"
            or model["identity_status"] == "machine_verified_on_execution_host",
            f"model identity not machine-verified: {model['tag']}",
        )
        digest = model.get("digest")
        _require(isinstance(digest, str) and len(digest) == 64, "digest must be full 64-hex")
        _require(all(c in "0123456789abcdef" for c in digest), "digest must be lowercase hex")
        _require(model.get("quantization_level"), "quantization_level missing")
        _require(model.get("parameter_size"), "parameter_size missing")
        _require(model.get("family"), "family missing")
        _require(model.get("format"), "format missing")


def zero_model_preflight(
    *,
    model: str,
    repo_root: Path = REPO_ROOT,
    require_verified_identity: bool = False,
    require_output_absent: bool = True,
) -> dict[str, Any]:
    model_tag = resolve_model_tag(model)
    rebuilt = freeze.build_outputs(repo_root)
    model_manifest_rel = (freeze.model_dir(model_tag) / "model_manifest.json").as_posix()
    cells_rel = (freeze.model_dir(model_tag) / "generation_cells.csv").as_posix()
    expected_manifest = rebuilt[model_manifest_rel]
    expected_cells = rebuilt[cells_rel]

    manifest_path = repo_root / model_manifest_rel
    cells_path = repo_root / cells_rel
    _require(manifest_path.is_file(), f"missing model manifest: {model_manifest_rel}")
    _require(cells_path.is_file(), f"missing generation cells: {cells_rel}")
    actual_manifest = manifest_path.read_bytes()
    actual_cells = cells_path.read_bytes()
    _require(actual_manifest == expected_manifest, "model manifest drift vs freeze rebuild")
    _require(actual_cells == expected_cells, "generation_cells drift vs freeze rebuild")

    master_rel = (freeze.ARTIFACT_RELATIVE / "master_manifest.json").as_posix()
    _require(
        (repo_root / master_rel).read_bytes() == rebuilt[master_rel],
        "master_manifest drift",
    )

    manifest = json.loads(actual_manifest.decode("utf-8"))
    cells = _read_csv(cells_path)
    assert_cells(cells, model_tag)
    assert_model_identity_for_preflight(
        manifest, require_verified=require_verified_identity
    )
    assert_output_isolation(repo_root, model_tag)

    run_dir = repo_root / freeze.MODEL_SPECS[model_tag]["run_output_relative"]
    if require_output_absent:
        _require(
            not run_dir.exists() or not any(run_dir.iterdir()),
            f"generation output already present: {run_dir.as_posix()}",
        )

    eval_dir = repo_root / freeze.MODEL_SPECS[model_tag]["evalplus_output_relative"]
    _require(
        not eval_dir.exists(),
        f"EvalPlus output must remain absent during generation preflight: {eval_dir.as_posix()}",
    )

    return {
        "status": "zero_model_preflight_passed",
        "plan_id": freeze.PLAN_ID,
        "model_tag": model_tag,
        "model_key": freeze.MODEL_SPECS[model_tag]["model_key"],
        "manifest_path": model_manifest_rel,
        "manifest_sha256": _sha256_bytes(actual_manifest),
        "cell_count": len(cells),
        "identity_status": manifest["model"]["identity_status"],
        "require_verified_identity": require_verified_identity,
        "model_calls": 0,
        "ollama_generation_calls": 0,
        "candidate_program_executed": False,
        "candidate_program_imported": False,
        "candidate_program_compiled": False,
        "evalplus_executed": False,
        "healer_modifications": 0,
        "output_directory": freeze.MODEL_SPECS[model_tag]["run_output_relative"].as_posix(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, choices=freeze.ALLOWED_MODEL_TAGS)
    parser.add_argument(
        "--require-verified-identity",
        action="store_true",
        help="Fail if model digest/quantization/family are not machine-verified.",
    )
    parser.add_argument(
        "--allow-existing-output",
        action="store_true",
        help="Allow preflight when generation output dir exists.",
    )
    args = parser.parse_args(argv)
    receipt = zero_model_preflight(
        model=args.model,
        require_verified_identity=args.require_verified_identity,
        require_output_absent=not args.allow_existing_output,
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
