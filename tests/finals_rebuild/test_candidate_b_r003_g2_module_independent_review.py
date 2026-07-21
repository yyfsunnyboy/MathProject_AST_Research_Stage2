from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "prepare_candidate_b_r003_g2_module_independent_review.py"
SPEC = importlib.util.spec_from_file_location("g2_module_review", SCRIPT)
assert SPEC and SPEC.loader
review = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = review
SPEC.loader.exec_module(review)


def _rows(raw: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(raw.decode("utf-8").splitlines()))


def _analysis():
    review.verify_sources()
    return review.build_analysis()


def test_all_frozen_sources_are_hash_pinned_and_drift_fails_closed(monkeypatch):
    review.verify_sources()
    key = next(iter(review.SOURCE_HASHES))
    monkeypatch.setitem(review.SOURCE_HASHES, key, "0" * 64)
    with pytest.raises(review.ReviewPreparationError, match="source hash drift"):
        review.verify_sources()


def test_exact_g2_module_scope_and_fixed_identity_order():
    analysis = _analysis()
    packets = analysis["packets"]
    assert len(packets) == 27
    assert len({row["program_id"] for row in packets}) == 27
    assert len({row["cell_identity_sha256"] for row in packets}) == 27
    assert [row["program_id"] for row in packets] == sorted(row["program_id"] for row in packets)
    assert {row["diagnostic_phase"] for row in packets} == {"G2_module"}
    prepared = _rows((ROOT / review.PREPARATION_CSV).read_bytes())
    proposals = {row["program_id"]: row["machine_proposal"] for row in prepared}
    assert {proposals[row["program_id"]] for row in packets} == {"REVIEW_RUNTIME_ROOT_CAUSE_AND_EARLIEST_GATE"}


def test_packet_evidence_groups_and_public_assert_relations():
    packets = _analysis()["packets"]
    location_counts = {}
    relation_counts = {}
    for row in packets:
        location_counts[row["failure_location_kind"]] = location_counts.get(row["failure_location_kind"], 0) + 1
        relation_counts[row["public_assert_relation"]] = relation_counts.get(row["public_assert_relation"], 0) + 1
        assert row["static_entry_point_present"] == "true"
        assert row["static_signature_compatible"] == "true"
        assert "THIRD_PARTY" not in row["import_classification"]
        assert row["generation_truncated"] == "false"
    assert location_counts == {
        "TOP_LEVEL_ASSERT_EXECUTION": 25,
        "FUNCTION_RAISE_EXPOSED_BY_MODULE_ASSERT": 1,
        "FUNCTION_REGEX_PATTERN_ERROR_EXPOSED_BY_MODULE_ASSERT": 1,
    }
    assert relation_counts == {"PUBLIC_CONTRACT_ASSERT_AST_EXACT": 25, "REQUIRED_ENTRY_ASSERT_VARIANT_NOT_CONTRACT_EXACT": 2}


def test_reviewer_worksheets_are_independent_and_decisions_blank():
    outputs = review.build_outputs()
    reviewer_a = _rows(outputs[Path("reviewer_A_blank.csv")])
    reviewer_b = _rows(outputs[Path("reviewer_B_blank.csv")])
    assert len(reviewer_a) == len(reviewer_b) == 27
    for left, right in zip(reviewer_a, reviewer_b, strict=True):
        assert left["worksheet_role"] == "REVIEWER_A_INDEPENDENT"
        assert right["worksheet_role"] == "REVIEWER_B_INDEPENDENT_BLINDED"
        left_evidence = {k: v for k, v in left.items() if k != "worksheet_role"}
        right_evidence = {k: v for k, v in right.items() if k != "worksheet_role"}
        assert left_evidence == right_evidence
        for field in review.REVIEW_DECISION_FIELDS:
            assert left[field] == ""
            assert right[field] == ""
    assert "provisional_primary_failure_layer" not in reviewer_a[0]
    assert "provisional_primary_failure_layer" not in reviewer_b[0]


def test_disagreement_sheet_is_blank_and_not_preadjudicated():
    rows = _rows(review.build_outputs()[Path("disagreement_adjudication_blank.csv")])
    assert len(rows) == 27
    for row in rows:
        assert row["reviewer_a_decision"] == ""
        assert row["reviewer_b_decision"] == ""
        assert row["disagreement_fields"] == ""
        assert row["adjudication_decision"] == ""
        assert row["adjudicator_id"] == ""
        assert row["adjudicated_at_utc"] == ""


def test_provisional_recommendations_are_never_formal_adjudications():
    rows = _rows(review.build_outputs()[Path("provisional_recommendations.csv")])
    assert len(rows) == 27
    assert {row["provisional_status"] for row in rows} == {
        "AI_ASSISTED_PROVISIONAL_NOT_FORMAL_ADJUDICATION"
    }
    assert {row["provisional_needs_second_review"] for row in rows} == {"true"}
    assert {row["provisional_healer_decision"] for row in rows} == {"not_run"}
    assert {row["provisional_healer_outcome"] for row in rows} == {"not_assessed"}
    assert sum(row["provisional_primary_failure_layer"] == "L4" for row in rows) == 2
    assert sum(row["provisional_primary_failure_layer"] == "" for row in rows) == 25
    assert all("ADJUDICATED" not in row["provisional_status"].replace("NOT_FORMAL_ADJUDICATION", "") for row in rows)


def test_special_05_and_07_are_individually_recommended_from_public_evidence():
    rows = _rows(review.build_outputs()[Path("provisional_recommendations.csv")])
    by_number = {row["review_rank"].zfill(2): row for row in rows}
    case_05 = by_number["05"]
    case_07 = by_number["07"]
    assert case_05["provisional_failure_subtype"] == "STDLIB_TEXT_PARSING_CONTROL_FLOW_RAISE"
    assert case_05["provisional_healer_eligibility"] == "noneligible"
    assert "no-match" in case_05["provisional_uncertainty_notes"]
    assert case_07["provisional_failure_subtype"] == "STDLIB_REGEX_PATTERN_CONSTRUCTION_ERROR"
    assert case_07["provisional_healer_eligibility"] == "noneligible"
    assert "semantic" in case_07["provisional_uncertainty_notes"]


def test_assert_cases_remain_per_cell_and_variant_cases_are_not_declared_safe():
    analysis = _analysis()
    packets = analysis["packets"]
    provisional = {row["program_id"]: row for row in analysis["provisional"]}
    assert_cases = [row for row in packets if row["failure_location_kind"] == "TOP_LEVEL_ASSERT_EXECUTION"]
    assert len(assert_cases) == 25
    variant_ids = [row["program_id"] for row in assert_cases if row["public_assert_relation"] == "REQUIRED_ENTRY_ASSERT_VARIANT_NOT_CONTRACT_EXACT"]
    assert len(variant_ids) == 2
    for program_id in variant_ids:
        row = provisional[program_id]
        assert row["provisional_confidence"] == "LOW"
        assert row["provisional_healer_eligibility"] == "undetermined"
        assert "根因不唯一" in row["provisional_uncertainty_notes"]
    assert all("CANDIDATE_ONLY" in provisional[row["program_id"]]["assert_removal_rule_assessment"] for row in assert_cases)


def test_outputs_exclude_forbidden_payloads_and_raw_source():
    outputs = review.build_outputs()
    forbidden_fields = {
        "source",
        "hidden_input",
        "hidden_inputs",
        "expected",
        "actual",
        "exception_message",
        "message",
        "traceback",
    }
    for name in (
        "review_packets.csv",
        "reviewer_A_blank.csv",
        "reviewer_B_blank.csv",
        "provisional_recommendations.csv",
    ):
        rows = _rows(outputs[Path(name)])
        assert forbidden_fields.isdisjoint(rows[0])
        text = outputs[Path(name)].decode("utf-8").lower()
        assert "traceback (most recent call last)" not in text
        assert "\ndef " not in text
    packets = _rows(outputs[Path("review_packets.csv")])
    assert all(len(row["source_context_sha256"]) == 64 for row in packets)
    assert all(row["minimal_source_evidence_summary"] for row in packets)


def test_execution_receipt_records_zero_executions_and_no_runtime_input():
    outputs = review.build_outputs()
    execution = json.loads(outputs[Path("execution_manifest.json")])
    assert execution["model_calls"] == 0
    assert execution["evalplus_correctness_executions"] == 0
    assert execution["diagnostics_executions"] == 0
    assert execution["healer_executions"] == 0
    assert execution["validation_executions"] == 0
    assert execution["healer_runtime_input"] is False
    assert execution["formal_adjudications_completed"] == 0


def test_manifest_hashes_cover_every_generated_output():
    outputs = review.build_outputs()
    manifest = json.loads(outputs[Path("manifest.json")])
    for name, digest in manifest["outputs_sha256_excluding_manifest"].items():
        assert hashlib.sha256(outputs[Path(name)]).hexdigest() == digest
    assert set(manifest["outputs_sha256_excluding_manifest"]) == {path.as_posix() for path in outputs if path != Path("manifest.json")}


def test_build_is_byte_deterministic():
    first = review.build_outputs()
    second = review.build_outputs()
    assert first == second


@pytest.mark.parametrize("mutation", ["duplicate", "missing", "source_hash"])
def test_identity_and_source_drift_fail_closed(monkeypatch, mutation):
    original_loader = review.preparation.load_tables

    def broken_loader(repo=ROOT):
        tables = original_loader(repo)
        tables = {name: [dict(row) for row in rows] if isinstance(rows, list) else rows for name, rows in tables.items()}
        diagnostics = tables["diagnostics"]
        target_index = next(i for i, row in enumerate(diagnostics) if row["phase"] == "G2_module")
        if mutation == "duplicate":
            diagnostics.append(dict(diagnostics[target_index]))
        elif mutation == "missing":
            diagnostics.pop(target_index)
        else:
            journals = tables["journal"]
            target_program = diagnostics[target_index]["program_id"]
            target = next(row for row in journals if row["program_id"] == target_program)
            target["evaluation_source"] += "\n# synthetic hash drift"
        return tables

    monkeypatch.setattr(review.preparation, "load_tables", broken_loader)
    with pytest.raises((review.ReviewPreparationError, review.preparation.PreparationError)):
        review.build_analysis()
