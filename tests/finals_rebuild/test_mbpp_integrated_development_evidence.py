from __future__ import annotations

import csv
import hashlib
import io
import json

from scripts import build_mbpp_integrated_development_evidence as integrated


def _rows(value: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(value.decode("utf-8"))))


def test_60_tasks_300_identities_and_600_programs() -> None:
    outputs = integrated.build_outputs()
    rows = _rows(outputs["integrated_development_cell_ledger.csv"])
    assert len(rows) == 300
    assert len({row["task_id"] for row in rows}) == 60
    assert len({(row["task_id"], row["seed"]) for row in rows}) == 300
    assert sum(int(row["program_count_represented"]) for row in rows) == 600
    assert all(row["pipeline_is_healer"] == "false" for row in rows)


def test_development_layers_and_treatment_accounts_are_separate() -> None:
    outputs = integrated.build_outputs()
    rows = _rows(outputs["integrated_development_cell_ledger.csv"])
    assert sum(row["development_layer"] == "discovery_development" for row in rows) == 100
    assert sum(row["development_layer"] == "expansion_development" for row in rows) == 200
    manifest = json.loads(outputs["milestone_2g_manifest.json"])
    assert manifest["treatment_program_counts"] == {
        "candidate_a": 200,
        "p0_official_prompt_only": 300,
        "scaffold_v0": 100,
    }


def test_signature_census_has_cells_and_unique_tasks() -> None:
    rows = {row["signature"]: row for row in _rows(integrated.build_outputs()["integrated_failure_signature_census.csv"])}
    assert set(rows) >= {
        "format_or_packaging_extraction_failure",
        "generation_length_termination",
        "syntax_parse_failure",
        "entrypoint_unique_arity_compatible_candidate",
        "generic_evaluator_failure_unknown",
        "import_or_dependency_failure_uniquely_evidenced",
    }
    assert all("cell_support" in row and "unique_task_support" in row for row in rows.values())
    assert rows["import_or_dependency_failure_uniquely_evidenced"]["cell_support"] == "0"


def test_candidate_b_is_one_draft_not_frozen_and_not_retested() -> None:
    outputs = integrated.build_outputs()
    rows = _rows(outputs["scaffold_candidate_evidence.csv"])
    assert {row["candidate_id"] for row in rows} == {"candidate_b_concise_complete_draft"}
    assert {row["status"] for row in rows} == {"candidate_not_frozen"}
    assert {row["exact_text_draft_utf8"] for row in rows} == {integrated.CANDIDATE_B_TEXT}
    assert all(row["same_40_task_retest_allowed"] == "false" for row in rows)
    assert all(row["official_v1_frozen"] == "false" for row in rows)


def test_candidate_a_length_and_compile_evidence_counts() -> None:
    manifest = json.loads(integrated.build_outputs()["milestone_2g_manifest.json"])
    assert manifest["candidate_a_evidence"] == {
        "syntax_cells": 19,
        "syntax_tasks": 10,
        "truncation_cells": 18,
        "truncation_syntax_overlap_cells": 15,
        "truncation_tasks": 8,
    }


def test_only_one_narrow_healer_rule_is_eligible_and_evaluator_blind() -> None:
    rows = _rows(integrated.build_outputs()["healer_candidate_rule_ledger.csv"])
    eligible = [row for row in rows if row["recommended_status"] == "eligible_for_implementation"]
    assert len(eligible) == 1
    assert eligible[0]["rule_id"] == "entrypoint_alias_unique_arity_compatible_v0"
    assert int(eligible[0]["unique_task_support"]) >= 2
    assert int(eligible[0]["cell_support"]) >= int(eligible[0]["unique_task_support"])
    assert eligible[0]["verified_rule"] == "false"
    assert eligible[0]["evaluator_result_used_to_accept_repair"] == "false"
    unknown = next(row for row in rows if row["rule_id"] == "generic_unknown_failure")
    assert unknown["recommended_status"] == "nonrepairable"


def test_sufficiency_decision_does_not_activate_remaining_56() -> None:
    decision = json.loads(integrated.build_outputs()["development_sufficiency_decision.json"])
    assert decision["decision"] == integrated.DECISION
    assert decision["remaining_historical_development_tasks"] == 56
    assert decision["activate_remaining_56_now"] is False
    assert decision["candidate_a_same_40_task_retest_allowed"] is False
    assert decision["model_calls"] == decision["evalplus_executions"] == 0


def test_source_scope_excludes_forbidden_roles() -> None:
    manifest = json.loads(integrated.build_outputs()["milestone_2g_manifest.json"])
    assert manifest["forbidden_roles_read"] == []
    forbidden = ("validation", "confirmatory", "sealed", "excluded")
    assert not any(any(word in path.lower() for word in forbidden) for path in manifest["source_artifact_sha256"])
    assert manifest["remaining_tasks_selected_or_read"] == 0


def test_deterministic_bytes_and_manifest_hashes() -> None:
    first = integrated.build_outputs()
    second = integrated.build_outputs()
    assert first == second
    manifest = json.loads(first["milestone_2g_manifest.json"])
    for name, expected in manifest["output_sha256_excluding_manifest"].items():
        assert hashlib.sha256(first[name]).hexdigest() == expected


def test_frozen_output_bytes_match_builder() -> None:
    integrated.write_outputs(check=True)
