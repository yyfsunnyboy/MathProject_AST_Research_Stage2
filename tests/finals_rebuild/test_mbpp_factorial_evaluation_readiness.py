from __future__ import annotations

import csv
import hashlib
import io
import json

from scripts import build_mbpp_factorial_evaluation_readiness as readiness


def _rows(value: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(value.decode("utf-8"))))


def test_formal_accounts_and_common_pipeline_order() -> None:
    outputs = readiness.build_outputs()
    spec = json.loads(outputs["factorial_accounting_spec.json"])
    assert spec["factorial_arms"] == ["P0_H0", "P0_H1", "P1_H0", "P1_H1"]
    assert spec["normalization"]["order"] == "generation -> frozen Pipeline normalization -> H0/H1 fork"
    assert spec["normalization"]["same_version_for_p0_and_p1"] is True
    assert spec["normalization"]["extraction_fence_stripping_plain_text_normalization_are_healer"] is False


def test_same_healer_version_order_guards_and_no_regeneration() -> None:
    spec = json.loads(readiness.build_outputs()["factorial_accounting_spec.json"])
    accounts = spec["healer_accounts"]
    assert accounts["same_healer_version_for_p0_and_p1"] is True
    assert accounts["same_rule_order_for_p0_and_p1"] is True
    assert accounts["same_guards_and_abstention_for_p0_and_p1"] is True
    assert accounts["model_regeneration_for_healer"] is False
    assert accounts["evaluator_used_for_trigger_selection_or_acceptance"] is False


def test_rule_triggers_are_split_by_p0_and_scaffold_conditions() -> None:
    rows = _rows(readiness.build_outputs()["healer_factorial_trigger_ledger.csv"])
    assert len(rows) == 6
    assert all(row["same_rule_version_required"] == "true" for row in rows)
    assert all(row["development_only"] == "true" for row in rows)
    entry = next(row for row in rows if row["rule_id"] == "entrypoint_alias_unique_arity_compatible_v0")
    assert (entry["p0_trigger_cells"], entry["p0_trigger_unique_tasks"]) == ("40", "16")
    assert (entry["scaffold_trigger_cells"], entry["scaffold_trigger_unique_tasks"]) == ("2", "1")
    assert entry["expected_repairable_signature"] == "entrypoint_unique_arity_compatible_candidate"


def test_pipeline_and_healer_accounts_are_separate() -> None:
    outputs = readiness.build_outputs()
    rows = _rows(outputs["healer_factorial_trigger_ledger.csv"])
    packaging = next(row for row in rows if row["rule_id"] == "format_packaging_extraction")
    assert packaging["recommended_status"] == "scaffold_or_pipeline_only"
    assert packaging["expected_repairable_signature"] == "none_currently"
    manifest = json.loads(outputs["factorial_readiness_manifest.json"])
    assert manifest["healer_implemented_or_frozen"] is False


def test_prospective_plan_is_not_activated_or_populated() -> None:
    plan = json.loads(readiness.build_outputs()["prospective_2x2_validation_plan.json"])
    assert plan["status"] == readiness.PLAN_STATUS
    assert plan["validation_task_ids"] == []
    assert plan["validation_task_content_read"] is False
    assert plan["planned_identity_count"] is None
    assert plan["activation_gate"]["formal_execution_allowed_now"] is False
    assert plan["generation_design"]["generation_count_per_identity"] == 2
    assert plan["generation_design"]["evaluation_accounts_per_identity"] == 4
    assert plan["generation_design"]["healer_causes_additional_generation"] is False


def test_h0_h1_share_generation_and_pipeline_identity() -> None:
    spec = json.loads(readiness.build_outputs()["factorial_accounting_spec.json"])
    identity = spec["identity_invariants"]
    assert identity["h0_h1_share_generation_id"] is True
    assert identity["h0_h1_share_raw_sha256"] is True
    assert identity["h0_h1_share_pipeline_input_and_normalized_sha256"] is True
    assert identity["exactly_one_model_attempt_per_prompt_arm_identity"] is True


def test_raw_packaging_ablation_is_separate() -> None:
    spec = json.loads(readiness.build_outputs()["factorial_accounting_spec.json"])
    ablation = spec["raw_deployment_packaging_ablation"]
    assert ablation["allowed_as_separate_optional_account"] is True
    assert ablation["part_of_formal_factorial"] is False
    assert ablation["may_not_replace_pipeline_or_healer_accounts"] is True


def test_manifest_is_development_only_and_has_no_calls() -> None:
    manifest = json.loads(readiness.build_outputs()["factorial_readiness_manifest.json"])
    assert manifest["development_only"] is True
    assert manifest["development_counts"] == {"programs": 600, "task_seed_identities": 300, "tasks": 60}
    assert manifest["model_calls"] == manifest["evalplus_executions"] == 0
    assert manifest["validation_tasks_read_or_selected"] == 0
    assert manifest["candidate_b_or_final_p1_frozen"] is False


def test_deterministic_bytes_and_hashes() -> None:
    first = readiness.build_outputs()
    second = readiness.build_outputs()
    assert first == second
    manifest = json.loads(first["factorial_readiness_manifest.json"])
    for name, expected in manifest["output_sha256_excluding_manifest"].items():
        assert hashlib.sha256(first[name]).hexdigest() == expected


def test_frozen_bytes_match_builder() -> None:
    readiness.write_outputs(check=True)
