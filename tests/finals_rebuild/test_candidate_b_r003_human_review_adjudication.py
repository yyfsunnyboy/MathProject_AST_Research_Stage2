from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path

import pytest

from scripts import adjudicate_candidate_b_r003_human_review as adjudication


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / adjudication.OUTPUT_RELATIVE


def test_exact_21_queue_boundary_and_no_source_emission():
    result = adjudication.build_analysis(REPO_ROOT)
    rows = result["rows"]
    queue_ids = {row["program_id"] for row in result["queue"]}
    assert len(rows) == len(queue_ids) == 21
    assert {row["program_id"] for row in rows} == queue_ids
    assert {int(row["review_rank"]) for row in rows} == set(range(1, 22))
    assert all(row["source_reviewed"] == "true" for row in rows)
    assert all(row["full_source_emitted"] == "false" for row in rows)
    assert "source" not in adjudication.FIELDS
    assert "evaluation_source" not in adjudication.FIELDS
    assert "raw_response" not in adjudication.FIELDS


def test_adjudication_counts_and_conservative_abstention():
    rows = adjudication.build_analysis(REPO_ROOT)["rows"]
    assert sum(row["repairability_tier"] == "ELIGIBLE_EXACT" for row in rows) == 2
    assert sum(row["repairability_tier"] == "CANDIDATE_REVIEW" for row in rows) == 1
    assert sum(row["repairability_tier"] == "INELIGIBLE" for row in rows) == 13
    assert sum(row["repairability_tier"] == "UNRESOLVED" for row in rows) == 5
    assert sum(row["abstain"] == "true" for row in rows) == 19
    assert {int(row["review_rank"]) for row in rows if row["repairability_tier"] == "ELIGIBLE_EXACT"} == {14, 15}
    assert {int(row["review_rank"]) for row in rows if row["repairability_tier"] == "CANDIDATE_REVIEW"} == {6}


def test_layer_validity_and_special_l1_l2_decisions():
    rows = {int(row["review_rank"]): row for row in adjudication.build_analysis(REPO_ROOT)["rows"]}
    assert rows[21]["adjudicated_layer"] == "L4"
    assert rows[21]["layer_subtype_reasonable"] == "false"
    assert rows[21]["repairability_tier"] == "INELIGIBLE"
    assert all(rows[rank]["outcome_validity"] == "PENDING_REVIEW" for rank in range(16, 21))
    assert all(rows[rank]["repairability_tier"] == "INELIGIBLE" for rank in (1, 2, 3, 4, 5, 7, 8, 9))
    assert rows[6]["unique_transformation"] == "true"
    assert rows[10]["adjudicated_subtype"] == "REQUIRED_FUNCTION_MISSING_AMBIGUOUS_ENTRYPOINT"
    assert all(rows[rank]["rule_family"] == "SIGNATURE_WRAPPER_REJECTED" for rank in (11, 12, 13))


def test_no_safe_new_cross_task_rule_family():
    rows = adjudication.build_analysis(REPO_ROOT)["rows"]
    families = adjudication._family_rows(rows)
    assert all(row["safe_cross_task_family"] == "false" for row in families)
    assert not any(
        row["new_or_existing"] == "new_candidate"
        and int(row["unique_tasks"]) >= 2
        for row in families
    )
    alias = next(row for row in families if row["rule_family"] == "EXISTING_UNIQUE_ENTRYPOINT_ALIAS_V0")
    assert int(alias["supported_cells"]) == 2
    assert int(alias["unique_tasks"]) == 1
    assert alias["formal_observation"] == "2 fail_to_fail; 0 rescue"


def test_minimal_diagnostics_do_not_include_hidden_values():
    diagnostics = adjudication._diagnostic_rows()
    assert len(diagnostics) >= 7
    combined = json.dumps(diagnostics, ensure_ascii=False).lower()
    assert "不得記錄測試輸入" in combined
    assert "不得記錄 return value" in combined
    assert not any(row["field"] in {"test_input", "expected_output", "actual_output"} for row in diagnostics)


def test_duplicate_missing_and_hash_drift_fail_closed(tmp_path: Path):
    original = REPO_ROOT / adjudication.SOURCE_DIR / "human_review_queue.csv"
    rows = list(csv.DictReader(io.StringIO(original.read_text(encoding="utf-8"))))
    assert len({row["program_id"] for row in rows}) == 21
    with pytest.raises(adjudication.AdjudicationError, match="duplicate identity"):
        adjudication._index_unique([{"id": "x"}, {"id": "x"}], "id", "fixture")
    with pytest.raises(adjudication.AdjudicationError, match="missing or unexpected"):
        adjudication._load_selected_h0_sources(REPO_ROOT, {"not-a-real-program"})
    with pytest.raises(adjudication.AdjudicationError, match="hash drift"):
        old = adjudication.SOURCE_HASHES[str(adjudication.SOURCE_DIR / "manifest.json").replace("\\", "/")]
        key = str(adjudication.SOURCE_DIR / "manifest.json").replace("\\", "/")
        adjudication.SOURCE_HASHES[key] = hashlib.sha256(b"drift").hexdigest()
        try:
            adjudication._verify_sources(REPO_ROOT)
        finally:
            adjudication.SOURCE_HASHES[key] = old


def test_outputs_are_byte_deterministic_and_hash_locked():
    first = adjudication.build_outputs(REPO_ROOT)
    second = adjudication.build_outputs(REPO_ROOT)
    assert first == second
    for relative, content in first.items():
        assert (OUTPUT_DIR / relative).read_bytes() == content
    manifest = json.loads(first[Path("manifest.json")])
    assert manifest["reviewed_cells"] == 21
    assert manifest["safe_new_rule_families_crossing_two_tasks"] == 0
    assert manifest["model_calls"] == manifest["evalplus_executions"] == 0
    assert manifest["healer_rules_modified"] is False
    assert manifest["validation_not_executed"] is True
    for name, digest in manifest["outputs_sha256_excluding_manifest"].items():
        assert hashlib.sha256(first[Path(name)]).hexdigest() == digest
