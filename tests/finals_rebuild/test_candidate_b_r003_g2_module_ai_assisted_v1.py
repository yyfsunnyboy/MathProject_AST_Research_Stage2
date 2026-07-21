from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "adjudicate_candidate_b_r003_g2_module_ai_assisted_v1.py"
SPEC = importlib.util.spec_from_file_location("g2_ai_assisted", SCRIPT)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)


def _rows(raw: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(raw.decode("utf-8").splitlines()))


def test_all_15_frozen_source_hashes_verify_and_drift_fails_closed(monkeypatch):
    module.verify_sources()
    assert len(module.SOURCE_HASHES) == 15
    path = next(iter(module.SOURCE_HASHES))
    monkeypatch.setitem(module.SOURCE_HASHES, path, "0" * 64)
    with pytest.raises(module.AdjudicationError, match="hash drift"):
        module.verify_sources()


def test_scope_identity_order_and_diagnostic_distribution():
    rows = module.build_rows()
    assert len(rows) == 27
    assert len({row["program_id"] for row in rows}) == 27
    assert len({row["cell_identity_sha256"] for row in rows}) == 27
    assert [row["program_id"] for row in rows] == sorted(row["program_id"] for row in rows)
    assert [row["review_rank"] for row in rows] == list(range(1, 28))
    assert Counter(row["diagnostic_exception_class"] for row in rows) == Counter({"AssertionError": 25, "PatternError": 1, "ValueError": 1})
    assert {row["diagnostic_phase"] for row in rows} == {"G2_module"}


def test_each_packet_contains_required_public_and_source_evidence():
    rows = module.build_rows()
    for row in rows:
        assert row["public_task_contract"].strip()
        assert row["required_entry_point"]
        assert f"def {row['required_entry_point']}" in row["required_function_source"]
        assert row["module_level_executable_statements"].strip()
        assert row["diagnostic_source_context_numbered"].strip()
        assert row["imports"].startswith("[")
        assert row["api_calls"].startswith("[")
        assert row["evidence_references"]


def test_proposals_are_explicitly_nonformal_and_researcher_fields_blank():
    rows = module.build_rows()
    assert {row["adjudication_status"] for row in rows} == {module.STATUS}
    for row in rows:
        assert row["researcher_review_status"] == ""
        assert row["researcher_notes"] == ""
        assert row["researcher_id"] == ""
        assert row["reviewed_at_utc"] == ""


def test_layer_and_unresolved_summary():
    outputs = module.build_outputs()
    rows = _rows(outputs[Path("layer_summary.csv")])
    counts = {row["layer"]: int(row["cells"]) for row in rows}
    assert counts == {"L0": 0, "L1": 0, "L2": 2, "L3": 0, "L4": 25, "L5": 0, "UNRESOLVED": 0}


def test_assertion_cells_are_not_batch_assigned_one_layer():
    rows = module.build_rows()
    assertion_rows = [row for row in rows if row["diagnostic_exception_class"] == "AssertionError"]
    assert len(assertion_rows) == 25
    assert Counter(row["proposed_primary_failure_layer"] for row in assertion_rows) == Counter({"L4": 23, "L2": 2})
    assert len({row["rationale"] for row in assertion_rows}) >= 20


def test_pattern_and_value_cases_are_runtime_not_domain_api():
    rows = module.build_rows()
    special = {row["diagnostic_exception_class"]: row for row in rows if row["diagnostic_exception_class"] != "AssertionError"}
    assert special["PatternError"]["proposed_primary_failure_layer"] == "L4"
    assert "stdlib_regex_pattern_construction" in json.loads(special["PatternError"]["mechanism_tags"])
    assert special["ValueError"]["proposed_primary_failure_layer"] == "L4"
    assert "text_parsing_control_flow_failure" in json.loads(special["ValueError"]["mechanism_tags"])
    assert special["PatternError"]["proposed_healer_eligibility"] == "abstain"
    assert special["ValueError"]["proposed_healer_eligibility"] == "abstain"


def test_decagonal_numeric_contract_cases_are_individually_l2():
    rows = module.build_rows()
    l2 = [row for row in rows if row["proposed_primary_failure_layer"] == "L2"]
    assert len(l2) == 2
    assert {row["task_id"] for row in l2} == {"Mbpp/279"}
    assert all(row["g3s_observation"] == "FAIL" for row in l2)
    assert all("schema_mismatch" in json.loads(row["mechanism_tags"]) for row in l2)
    assert all(row["proposed_healer_eligibility"] == "abstain" for row in l2)


def test_healer_summary_is_conditional_not_presumed_safe():
    outputs = module.build_outputs()
    summary = _rows(outputs[Path("healer_eligibility_summary.csv")])
    assert {row["proposed_healer_eligibility"]: int(row["cells"]) for row in summary} == {"eligible": 0, "conditional": 23, "abstain": 4}
    rows = module.build_rows()
    assert {row["proposed_healer_decision"] for row in rows} == {"not_run"}
    assert not any(row["proposed_healer_eligibility"] == "eligible" for row in rows)


def test_forbidden_correctness_and_hidden_evidence_are_not_exported():
    outputs = module.build_outputs()
    rows = _rows(outputs[Path("ai_assisted_provisional_adjudication.csv")])
    forbidden_fields = {"hidden_expected", "hidden_actual", "correctness_result", "exception_message", "traceback"}
    assert forbidden_fields.isdisjoint(rows[0])
    for row in rows:
        refs = row["evidence_references"].lower()
        assert "evalplus_results" not in refs
        assert "paired_cell_results" not in refs
        assert row["g4_observation"] == "PUBLIC_CONTRACT_OBSERVATION_ONLY_NOT_FORMAL_CORRECTNESS"


def test_original_reviewer_and_prior_provisional_files_are_not_dependencies():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "reviewer_A_blank.csv" not in source
    assert "reviewer_B_blank.csv" not in source
    assert "provisional_recommendations.csv" not in source
    provenance = json.loads(module.build_outputs()[Path("provenance.json")])
    assert provenance["original_reviewer_worksheets_modified"] is False
    assert provenance["existing_provisional_recommendations_read"] is False


def test_no_experimental_executions_or_false_human_review_claims():
    execution = json.loads(module.build_outputs()[Path("execution_manifest.json")])
    assert execution["researcher_reviews_completed"] == 0
    assert execution["model_calls"] == 0
    assert execution["evalplus_correctness_executions"] == 0
    assert execution["diagnostics_executions"] == 0
    assert execution["healer_executions"] == 0
    assert execution["validation_executions"] == 0
    assert execution["new_correctness_tests"] == 0
    provenance = json.loads(module.build_outputs()[Path("provenance.json")])
    assert provenance["formal_human_adjudication"] is False
    assert provenance["two_human_blind_review_claimed"] is False
    assert provenance["cohens_kappa_computed"] is False


def test_report_presents_every_cell_and_full_evidence_sections():
    outputs = module.build_outputs()
    report = outputs[Path("ai_assisted_review_report_zh.md")].decode("utf-8")
    for row in module.build_rows():
        assert row["program_id"] in report
        assert row["required_function_source"] in report
        assert row["module_level_executable_statements"] in report
    assert module.STATUS in report
    assert "Cohen’s kappa" in report


def test_manifest_hashes_and_deterministic_bytes():
    first = module.build_outputs()
    second = module.build_outputs()
    assert first == second
    for data in first.values():
        text = data.decode("utf-8")
        assert all(line == line.rstrip() for line in text.splitlines())
    manifest = json.loads(first[Path("manifest.json")])
    for name, digest in manifest["outputs_sha256_excluding_manifest"].items():
        assert hashlib.sha256(first[Path(name)]).hexdigest() == digest
    assert manifest["researcher_reviews_completed"] == 0
