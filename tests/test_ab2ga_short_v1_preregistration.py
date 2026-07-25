from __future__ import annotations

import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path

import scripts.build_ab2ga_short_v1_preregistration as build


ROOT = Path(__file__).resolve().parents[1]


def test_deterministic_rebuild_matches_frozen_artifacts() -> None:
    expected = build.build_outputs(ROOT)
    actual_dir = ROOT / build.ARTIFACT_DIR
    assert {path.name for path in actual_dir.iterdir() if path.is_file()} == set(expected)
    assert all((actual_dir / name).read_bytes() == data for name, data in expected.items())


def test_base_is_bitwise_unchanged_and_increment_is_unique_suffix() -> None:
    artifact_dir = ROOT / build.ARTIFACT_DIR
    base = artifact_dir.joinpath("frozen_ab2g_base.txt").read_bytes()
    increment = artifact_dir.joinpath("frozen_incremental_block.txt").read_bytes()
    source = (ROOT / build.BASE_PATH).read_bytes()
    spec = json.loads(artifact_dir.joinpath("scaffold_spec.json").read_text("utf-8"))
    assert base == source
    assert hashlib.sha256(base).hexdigest() == build.BASE_SHA256
    assert increment.decode("utf-8") == build.INCREMENTAL_BLOCK
    composite = base + build.INCREMENTAL_SEPARATOR.encode() + increment
    assert composite.startswith(base)
    assert hashlib.sha256(composite).hexdigest() == spec["composition"]["composite_scaffold_sha256"]


def test_exact_200_cell_paired_distribution_and_complete_prompts() -> None:
    artifact_dir = ROOT / build.ARTIFACT_DIR
    with artifact_dir.joinpath("cell_plan.csv").open(newline="", encoding="utf-8") as handle:
        cells = list(csv.DictReader(handle))
    prompts = [
        json.loads(line)
        for line in artifact_dir.joinpath("complete_prompt_manifest.jsonl")
        .read_text("utf-8")
        .splitlines()
    ]
    assert len(cells) == len(prompts) == 200
    assert len({row["cell_identity"] for row in cells}) == 200
    assert Counter(row["model_tag"] for row in cells) == {
        "qwen3.5:4b": 100,
        "qwen3.5:9b": 100,
    }
    assert all(
        hashlib.sha256(row["complete_prompt"].encode()).hexdigest()
        == row["complete_prompt_sha256"]
        for row in prompts
    )
    identities = {(row["task_id"], row["seed"]) for row in cells if row["model_tag"] == "qwen3.5:4b"}
    assert identities == {
        (row["task_id"], row["seed"])
        for row in cells
        if row["model_tag"] == "qwen3.5:9b"
    }
    assert all(row["execution_state"] == "preregistered_not_executed" for row in cells)


def test_preregistration_fixes_roles_metrics_and_zero_execution() -> None:
    prereg = json.loads(
        (ROOT / build.ARTIFACT_DIR / "preregistration.json").read_text("utf-8")
    )
    assert prereg["research_role"] == "development_condition_transfer_increment"
    assert prereg["confirmatory_claim_for_unseen_tasks"] is False
    assert prereg["h1"]["sha256"] == build.H1_SHA256
    assert prereg["h2"]["sha256"] == build.H2_SHA256
    assert prereg["h2"]["current_status"] == "development_candidate_not_frozen"
    assert set(prereg["execution_state"].values()) == {0}
    required = {
        "Base pass",
        "Plus pass",
        "strict pass",
        "extractability",
        "parseability",
        "executability",
        "eligible",
        "transformed",
        "abstained",
        "blocker removed",
        "verified rescue",
        "partial repair",
        "regression",
        "preserved pass",
        "failure layer",
        "failure chain",
        "per-cell paired transition",
    }
    assert set(prereg["metrics"]) == required
