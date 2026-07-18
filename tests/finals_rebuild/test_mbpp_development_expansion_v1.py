from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
from pathlib import Path

from scripts import freeze_mbpp_development_expansion_v1 as expansion


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / expansion.OUTPUT_RELATIVE


def _source_hashes() -> dict[str, str]:
    return {
        label: hashlib.sha256((REPO_ROOT / path).read_bytes()).hexdigest()
        for label, path in expansion.SOURCE_PATHS.items()
    }


def test_20_plus_40_equals_60_unique_tasks_and_preserves_discovery():
    result = expansion.build_expansion(REPO_ROOT)
    rows = result["overlay_rows"]
    discovery = [row for row in rows if row["development_layer"] == "discovery_development"]
    added = [row for row in rows if row["development_layer"] == "expansion_development"]

    assert len(discovery) == 20
    assert len(added) == 40
    assert len(rows) == 60
    assert len({(row["dataset"], row["task_id"]) for row in rows}) == 60
    assert all(row["original_active_development_subset"] == "true" for row in discovery)
    assert all(row["original_active_development_subset"] == "false" for row in added)


def test_300_unique_future_task_seed_identities_per_treatment():
    identities = expansion.build_expansion(REPO_ROOT)["identities"]

    assert len(identities) == 300
    assert len({(row["task_id"], row["seed"]) for row in identities}) == 300
    assert {row["seed"] for row in identities} == {11, 22, 33, 44, 55}


def test_added_tasks_come_only_from_remaining_historical_pool_and_zero_overlap():
    result = expansion.build_expansion(REPO_ROOT)
    rows = result["overlay_rows"]
    added_ids = {
        row["task_id"] for row in rows if row["development_layer"] == "expansion_development"
    }
    frozen = expansion._read_csv_fields(
        REPO_ROOT / expansion.FROZEN_SPLIT,
        expansion.ALLOWED_FROZEN_FIELDS,
        expansion.ALLOWED_FROZEN_FIELDS,
    )
    historical = {
        row["task_id"]
        for row in frozen
        if row["dataset"] == "MBPP+"
        and row["proposed_role"] == "historical_development_pool"
    }
    active = {
        row["task_id"]
        for row in frozen
        if row["dataset"] == "MBPP+"
        and row["active_development_generation_subset"] == "true"
    }
    forbidden_roles = {
        "validation",
        "internal_confirmatory_candidate",
        "external_confirmatory_candidate",
        "excluded_historical",
        "sealed_reserve",
    }
    forbidden = {
        (row["dataset"], row["task_id"])
        for row in frozen
        if row["proposed_role"] in forbidden_roles
    }

    assert len(historical) == 116
    assert len(active) == 20
    assert len(historical - active) == 96
    assert added_ids <= historical - active
    assert not ({(row["dataset"], row["task_id"]) for row in rows} & forbidden)
    assert result["forbidden_overlap_count"] == 0


def test_selection_hash_preimage_and_order_are_exact_and_have_no_override():
    result = expansion.build_expansion(REPO_ROOT)
    records = result["selection_records"]
    selected = records[:40]

    assert expansion.SELECTION_SEED == "20260718"
    assert expansion.SELECTION_SALT == (
        "MathProject_AST_Research_Stage2|MBPP+|development_expansion_v1"
    )
    assert len(records) == 96
    assert [row["selection_rank_within_remaining_pool"] for row in records] == list(
        range(1, 97)
    )
    assert [(row["selection_hash"], row["task_id"]) for row in records] == sorted(
        (row["selection_hash"], row["task_id"]) for row in records
    )
    assert all(row["selected"] for row in selected)
    assert not any(row["selected"] for row in records[40:])
    assert result["selected_expansion_task_ids"] == [row["task_id"] for row in selected]


def test_builder_uses_only_governance_allowlists_and_no_sensitive_source_paths():
    assert not (
        expansion.FORBIDDEN_SELECTION_FIELDS & expansion.ALLOWED_FROZEN_FIELDS
    )
    assert not (
        expansion.FORBIDDEN_SELECTION_FIELDS & expansion.ALLOWED_CONTAMINATION_FIELDS
    )
    assert set(expansion.SOURCE_PATHS) == {
        "frozen_split.csv",
        "frozen_split_summary.md",
        "contamination_manifest.csv",
        "milestone_2c_manifest.json",
        "scaffold_v1_candidates.json",
    }
    assert all(
        "tasks.jsonl" not in path.as_posix()
        and "raw_generations" not in path.as_posix()
        and "evaluation_results" not in path.as_posix()
        for path in expansion.SOURCE_PATHS.values()
    )
    source = (REPO_ROOT / "scripts/freeze_mbpp_development_expansion_v1.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(source)
    path_literals = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    assert not any("data/mbpp_plus/tasks.jsonl" in value for value in path_literals)


def test_original_frozen_sources_and_candidate_a_remain_byte_identical():
    before = _source_hashes()
    result = expansion.build_expansion(REPO_ROOT)
    after = _source_hashes()

    assert before == after == expansion.EXPECTED_SOURCE_HASHES
    assert result["candidate_a"]["status"] == "candidate_only_not_frozen"
    assert result["candidate_a"]["exact_text_sha256"] == (
        expansion.EXPECTED_CANDIDATE_A_TEXT_SHA256
    )
    assert result["candidate_a"]["generation_plan_created"] is False


def test_outputs_are_byte_deterministic_and_manifest_is_complete():
    first = expansion.build_outputs(REPO_ROOT)
    second = expansion.build_outputs(REPO_ROOT)

    assert first == second
    for relative, expected in first.items():
        assert (OUTPUT_DIR / relative).read_bytes() == expected
    manifest = json.loads(first[Path("development_expansion_manifest.json")])
    assert manifest["counts"] == {
        "discovery_development": 20,
        "expansion_development": 40,
        "historical_development_pool": 116,
        "remaining_historical_candidates": 96,
        "total_development": 60,
        "unique_task_seed_identities_per_future_treatment": 300,
    }
    assert len(manifest["development_tasks"]) == 60
    assert len(manifest["future_task_seed_identities"]) == 300
    assert manifest["zero_overlap"]["verified_total_forbidden_overlap"] == 0
    assert manifest["selection"]["manual_override_allowed"] is False
    assert manifest["source_frozen_split"]["modified"] is False
    for name, metadata in manifest["outputs"].items():
        content = first[Path(name)]
        assert hashlib.sha256(content).hexdigest() == metadata["sha256"]
        assert len(content) == metadata["size_bytes"]


def test_committed_csv_schema_has_no_sensitive_fields():
    rows = list(
        csv.DictReader(
            io.StringIO(
                (OUTPUT_DIR / "development_expansion_manifest.csv").read_text(
                    encoding="utf-8"
                )
            )
        )
    )
    assert len(rows) == 60
    assert tuple(rows[0]) == expansion.CSV_FIELDS
    assert not (expansion.FORBIDDEN_SELECTION_FIELDS & set(rows[0]))
