from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

import pytest

from scripts import analyze_candidate_b_r003_failure_census as census


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / census.OUTPUT_RELATIVE


def test_complete_300_program_76_pass_224_fail_and_60x5_identity():
    result = census.build_analysis(REPO_ROOT, census.TAXONOMY_PATH)
    rows = result["rows"]
    assert len(rows) == len({row["program_id"] for row in rows}) == 300
    assert sum(row["final_status"] == "PASSED" for row in rows) == 76
    assert sum(row["final_status"] == "FAILED" for row in rows) == 224
    assert len({row["task_id"] for row in rows}) == 60
    assert {row["seed"] for row in rows} == {"11", "22", "33", "44", "55"}
    assert all(row["included"] == "true" for row in rows)


def test_adapter_never_defaults_aggregate_failures_to_l5_and_na_gates_are_filled():
    rows = census.build_analysis(REPO_ROOT, census.TAXONOMY_PATH)["rows"]
    assert not any(row["primary_failure_layer"] == "L5" for row in rows)
    unresolved = [row for row in rows if row["primary_failure_layer"] == "UNRESOLVED"]
    assert unresolved
    assert all(row["outcome_validity"] == "PENDING_REVIEW" for row in unresolved)
    assert all(row["g3a_required_api"] == "NOT_APPLICABLE" for row in rows)
    assert all(row["g3c_canonical_form"] == "NOT_APPLICABLE" for row in rows)


def test_negative_controls_and_repairability_boundaries():
    rows = census.build_analysis(REPO_ROOT, census.TAXONOMY_PATH)["rows"]
    controls = [row for row in rows if row["negative_control"] == "true"]
    assert len(controls) == 76
    assert all(row["primary_failure_layer"] == "PASSED" for row in controls)
    assert all(row["repairability_tier"] == "INELIGIBLE" for row in controls)
    assert all(row["healer_eligible"] == "false" for row in controls)
    assert all(row["primary_failure_layer"] != "L5" or row["healer_eligible"] == "false" for row in rows)


def test_static_classifiers_keep_missing_import_as_review_not_proven_l4():
    classified = census._classify(
        source="def target(x):\n    return math.sqrt(x)\n", passed=False,
        entry="target", arities=(1,), generation_truncated=False, raw_strict=True,
    )
    assert classified["primary_failure_layer"] == "UNRESOLVED"
    assert classified["failure_subtype"] == "L4_MISSING_STDLIB_IMPORT_CANDIDATE"
    assert classified["repairability_tier"] == "CANDIDATE_REVIEW"
    assert classified["outcome_validity"] == "PENDING_REVIEW"


def test_exact_alias_and_ambiguous_alias_guards():
    exact = census._classify(source="def other(x):\n    return x\n", passed=False, entry="target", arities=(1,), generation_truncated=False, raw_strict=True)
    ambiguous = census._classify(source="def a(x):\n    return x\ndef b(x):\n    return x\n", passed=False, entry="target", arities=(1,), generation_truncated=False, raw_strict=True)
    assert exact["repairability_tier"] == "ELIGIBLE_EXACT"
    assert exact["healer_eligible"] is True
    assert ambiguous["repairability_tier"] == "CANDIDATE_REVIEW"
    assert ambiguous["healer_eligible"] is False


def test_nested_function_return_does_not_satisfy_outer_return_contract():
    tree = ast.parse("def target(x):\n    def inner():\n        return x\n")
    function = tree.body[0]
    assert isinstance(function, ast.FunctionDef)
    assert census._function_has_value_return(function) is False


def test_duplicate_missing_hash_and_taxonomy_drift_fail_closed(tmp_path: Path):
    with pytest.raises(census.CensusError, match="duplicate"):
        census._index_unique([{"id": "x"}, {"id": "x"}], "id", "fixture")
    with pytest.raises(census.CensusError, match="missing or unexpected"):
        census._require_exact_keys({"a"}, {"a", "b"}, "fixture")
    with pytest.raises(census.CensusError, match="hash drift"):
        census._verify_bytes(b"drift", hashlib.sha256(b"expected").hexdigest(), "fixture")
    bad_taxonomy = tmp_path / "taxonomy.md"
    bad_taxonomy.write_text("drift", encoding="utf-8")
    with pytest.raises(census.CensusError, match="taxonomy v2 attachment"):
        census.build_analysis(REPO_ROOT, bad_taxonomy)


def test_review_queue_is_representative_and_contains_no_source():
    result = census.build_analysis(REPO_ROOT, census.TAXONOMY_PATH)
    queue = result["review_rows"]
    assert queue
    assert all(row["source_in_queue"] == "false" for row in queue)
    assert all(row["selection_basis"] == "feature_stratum_then_program_id_not_task_or_answer" for row in queue)
    assert len({row["program_id"] for row in queue}) == len(queue)


def test_outputs_are_byte_deterministic_and_manifest_hashes_match():
    first = census.build_outputs(REPO_ROOT, census.TAXONOMY_PATH)
    second = census.build_outputs(REPO_ROOT, census.TAXONOMY_PATH)
    assert first == second
    for relative, content in first.items():
        assert (OUTPUT_DIR / relative).read_bytes() == content
    manifest = json.loads(first[Path("manifest.json")])
    for name, digest in manifest["outputs_sha256_excluding_manifest"].items():
        assert hashlib.sha256(first[Path(name)]).hexdigest() == digest
    assert manifest["model_calls"] == manifest["evalplus_executions"] == 0
    assert manifest["healer_rules_modified"] is False
    assert manifest["validation_not_executed"] is True
