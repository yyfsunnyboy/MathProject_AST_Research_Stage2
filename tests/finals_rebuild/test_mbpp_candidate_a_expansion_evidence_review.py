from __future__ import annotations

import csv
import hashlib
import io
import json

from scripts import build_mbpp_candidate_a_expansion_evidence_review as review


def _csv_rows(value: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(value.decode("utf-8"))))


def test_complete_paired_200_cells_and_transitions() -> None:
    outputs = review.build_outputs()
    rows = _csv_rows(outputs["expansion_cell_evidence.csv"])
    assert len(rows) == 200
    assert len({(row["task_id"], row["seed"]) for row in rows}) == 200
    counts = {name: sum(row["pipeline_transition"] == name for row in rows) for name in review.EXPECTED_TRANSITIONS}
    assert counts == review.EXPECTED_TRANSITIONS
    assert sum(row["p0_pipeline_status"] == "pass" for row in rows) == 38
    assert sum(row["candidate_pipeline_status"] == "pass" for row in rows) == 53


def test_protocol_identity_hash_and_r001_exclusion() -> None:
    outputs = review.build_outputs()
    manifest = json.loads(outputs["milestone_2f_manifest.json"])
    assert manifest["candidate_exact_text_sha256"] == review.EXPECTED_CANDIDATE_HASH
    assert manifest["invalidated_candidate_r001_formal_cells"] == 0
    assert manifest["journal_inventories"]["p0_r001"]["count"] == 200
    assert manifest["journal_inventories"]["candidate_r002"]["count"] == 200
    assert manifest["model_calls"] == manifest["evalplus_executions"] == 0


def test_exact_22_noncompliant_and_concepts_separated() -> None:
    outputs = review.build_outputs()
    rows = _csv_rows(outputs["candidate_a_format_noncompliance.csv"])
    assert len(rows) == 22
    assert all(row["strict_output_compliance"] == "false" for row in rows)
    assert all(row["generation_protocol_compliance"] == "true" for row in rows)
    assert all(row["extraction_status"] == "extracted" for row in rows)
    assert all(row["reasoning_leakage"] == "false" for row in rows)
    assert all(row["reproducible_diagnostic"] for row in rows)


def test_rescues_regressions_common_passes_and_task_profiles() -> None:
    outputs = review.build_outputs()
    cells = _csv_rows(outputs["expansion_cell_evidence.csv"])
    assert sum(row["transition_evidence_class"] == "paired_rescue" for row in cells) == 30
    assert sum(row["transition_evidence_class"].startswith("paired_regression") for row in cells) == 15
    assert sum(row["transition_evidence_class"] == "common_pipeline_pass" for row in cells) == 23
    summaries = {row["task_id"]: row for row in _csv_rows(outputs["rescue_regression_task_summary.csv"])}
    assert summaries["Mbpp/6"]["fail_to_pass"] == "5"
    assert summaries["Mbpp/14"]["pass_to_fail"] == "4"
    assert summaries["Mbpp/607"]["pass_to_fail"] == "4"
    regression_tasks = {row["task_id"] for row in cells if row["pipeline_transition"] == "pass_to_fail"}
    assert regression_tasks == {"Mbpp/432", "Mbpp/572", "Mbpp/14", "Mbpp/722", "Mbpp/607", "Mbpp/786"}


def test_failure_census_is_evidence_limited() -> None:
    outputs = review.build_outputs()
    rows = _csv_rows(outputs["candidate_a_failure_census.csv"])
    assert len(rows) == 147
    assert all(row["pipeline_status"] == "fail" for row in rows)
    assert all(row["candidate_label_caveat"] == "candidate_label_not_validated_repair_rule" for row in rows)
    for row in rows:
        if row["failure_category"] == "unknown":
            assert row["evaluator_blind_healer_candidate"] == "false"
            assert row["must_not_auto_repair"] == "true"
            assert row["review_status"] == "manual_review_required"


def test_preregistered_promotion_decision_is_not_relaxed() -> None:
    manifest = json.loads(review.build_outputs()["milestone_2f_manifest.json"])
    assert manifest["exact_mcnemar_two_sided_p"] == 0.035697803555194696
    assert manifest["net_gain_cells"] == 15
    assert manifest["net_gain_percentage_points"] == 7.5
    assert manifest["gates"] == {
        "correctness_improvement_condition": True,
        "format_gate": False,
        "full_promotion": False,
        "pipeline_correctness_safety_gate": True,
        "protocol_gate": True,
    }
    assert manifest["format"]["strict_python_only"] == {"count": 178, "rate": 0.89}


def test_deterministic_bytes_and_manifest_hashes() -> None:
    first = review.build_outputs()
    second = review.build_outputs()
    assert first == second
    manifest = json.loads(first["milestone_2f_manifest.json"])
    for name, expected in manifest["output_sha256_excluding_manifest"].items():
        assert hashlib.sha256(first[name]).hexdigest() == expected


def test_frozen_outputs_match_builder() -> None:
    review.write_outputs(check=True)
