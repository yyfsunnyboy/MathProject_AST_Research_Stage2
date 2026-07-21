from __future__ import annotations

import copy
import csv
import hashlib
import json
from pathlib import Path

import pytest

from scripts import prepare_candidate_b_r003_taxonomy_v3_formal_classification as analyzer


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / analyzer.OUTPUT_RELATIVE


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.parametrize("relative,expected", list(analyzer.SOURCE_HASHES.items()))
def test_every_frozen_source_is_hash_pinned_and_drift_fails_closed(relative: Path, expected: str):
    path = relative if relative.is_absolute() else REPO_ROOT / relative
    assert _digest(path) == expected
    with pytest.raises(analyzer.PreparationError, match="hash drift"):
        analyzer._verify_one(path, "0" * 64)


def test_formal_receipt_and_results_identity_are_verified():
    tables = analyzer.load_tables(REPO_ROOT)
    receipt = tables["formal_receipt"]
    assert receipt["status"] == "r002_v3_formal_complete"
    assert receipt["cells"] == 198
    assert receipt["results_sha256"] == analyzer.SOURCE_HASHES[analyzer.FORMAL_RESULTS]
    assert receipt["source_manifest_sha256"] == analyzer.SOURCE_HASHES[analyzer.DIAGNOSTICS_SOURCE_MANIFEST]
    assert receipt["healer_runtime_input"] is False


def test_preparation_is_exactly_198_unique_programs_and_cells():
    analysis = analyzer.build_analysis(REPO_ROOT)
    rows = analysis["preparation"]
    assert len(rows) == 198
    assert len({row["program_id"] for row in rows}) == 198
    assert len({row["cell_identity_sha256"] for row in rows}) == 198
    assert sum(row["review_queue_disposition"] == "HUMAN_REVIEW_QUEUE" for row in rows) == 196
    assert sum(row["diagnostic_evidence_validity"] == "INVALID_INFRASTRUCTURE" for row in rows) == 2


def test_two_infrastructure_cells_are_fixed_unclassified_and_never_l4():
    rows = analyzer.build_analysis(REPO_ROOT)["preparation"]
    infrastructure = [row for row in rows if row["diagnostic_evidence_validity"] == "INVALID_INFRASTRUCTURE"]
    assert {(row["program_id"], row["cell_identity_sha256"]) for row in infrastructure} == analyzer.EXPECTED_INFRASTRUCTURE
    for row in infrastructure:
        assert row["classification_status"] == "PENDING_REVIEW"
        assert row["primary_failure_layer"] == ""
        assert row["outcome_validity"] == "INVALID_INFRASTRUCTURE"
        assert row["reviewer_required"] == "true"
        assert row["healer_eligibility"] == "undetermined"
        assert row["healer_decision"] == "not_run"
        assert row["healer_outcome"] == "not_assessed"
        assert row["machine_proposal"] == "ABSTAIN_DIAGNOSTIC_INFRASTRUCTURE"
        assert "L4" not in row["primary_failure_layer"]


def test_machine_preparation_assigns_no_primary_layer_or_formal_adjudication():
    rows = analyzer.build_analysis(REPO_ROOT)["preparation"]
    assert all(row["classification_status"] == "PENDING_REVIEW" for row in rows)
    assert all(row["primary_failure_layer"] == "" for row in rows)
    assert all(row["formal_adjudication_status"] == "NOT_COMPLETED" for row in rows)
    assert all(row["formal_adjudicated_primary_layer"] == "" for row in rows)
    assert all(row["machine_proposal_status"] == "PREPARATION_ONLY_NOT_FORMAL_ADJUDICATION" for row in rows)


def test_phase_and_exception_are_not_direct_layer_mappings():
    rows = analyzer.build_analysis(REPO_ROOT)["preparation"]
    raised = [row for row in rows if row["termination"] == "raised"]
    assert len(raised) == 75
    assert all(row["g2_execution"] == "FAIL" for row in raised)
    assert all(row["primary_failure_layer"] == "" for row in raised)
    assert all(row["machine_proposal"] == "REVIEW_RUNTIME_ROOT_CAUSE_AND_EARLIEST_GATE" for row in raised)
    assert len({row["diagnostic_exception_class"] for row in raised}) > 1


def test_completed_returned_is_not_correctness_pass_or_automatic_l5():
    rows = analyzer.build_analysis(REPO_ROOT)["preparation"]
    completed = [row for row in rows if row["diagnostic_phase"] == "completed"]
    assert len(completed) == 121
    assert all(row["g2_execution"] == "PASS" and row["g4_correctness"] == "FAIL" for row in completed)
    assert all(row["primary_failure_layer"] == "" for row in completed)
    assert all(row["machine_proposal"] == "REVIEW_OUTPUT_CONTRACT_OR_SEMANTIC" for row in completed)
    assert not any(row["machine_proposal"] == "L5" for row in completed)


def test_base_plus_failure_is_preserved_as_observation_not_semantic_label():
    rows = analyzer.build_analysis(REPO_ROOT)["preparation"]
    patterns = {(row["evalplus_base_status"], row["evalplus_plus_status"]) for row in rows}
    assert patterns == {("fail", "fail"), ("pass", "fail")}
    assert all(row["primary_failure_layer"] == "" for row in rows)


@pytest.mark.parametrize(
    "mutation,match",
    [
        (lambda t: t["diagnostics"].append(dict(t["diagnostics"][0])), "row count"),
        (lambda t: t["diagnostics"].pop(), "row count"),
        (lambda t: t["diagnostics"][0].__setitem__("evaluation_source_sha256", "0" * 64), "source hash drift"),
        (lambda t: t["diagnostics"][0].__setitem__("task_identity_sha256", "0" * 64), "task identity drift"),
        (lambda t: t["diagnostics"][0].__setitem__("evaluator_hash", "0" * 64), "evaluator hash drift"),
        (lambda t: t["diagnostics"][0].__setitem__("protocol_sha256", "0" * 64), "protocol hash drift"),
    ],
)
def test_duplicate_missing_source_task_evaluator_protocol_drift_fail_closed(mutation, match: str):
    tables = analyzer.load_tables(REPO_ROOT)
    mutation(tables)
    with pytest.raises(analyzer.PreparationError, match=match):
        analyzer.analyze_tables(tables)


def test_identity_join_audit_is_complete_and_never_uses_row_order():
    audit = analyzer.build_analysis(REPO_ROOT)["audit"]
    assert audit["diagnostics_rows"] == 198
    assert audit["usable_diagnostics"] == 196
    assert audit["infrastructure_invalid"] == 2
    assert audit["human_review_queue"] == 196
    assert audit["formal_adjudications_completed"] == 0
    assert all(value == 198 for value in audit["join_counts"].values())
    assert audit["row_order_used_for_join"] is False
    assert audit["task_name_only_used_for_join"] is False
    assert audit["seed_only_used_for_join"] is False


def test_taxonomy_schema_enums_and_required_fields_are_frozen():
    schema = json.loads((OUTPUT_DIR / "proposed_classification_schema.json").read_bytes())
    required = {
        "program_id",
        "cell_identity_sha256",
        "task_identity_sha256",
        "diagnostic_evidence_validity",
        "classification_status",
        "primary_failure_layer",
        "secondary_failure_layers",
        "g1_parse",
        "g2_execution",
        "g3_contract",
        "g4_correctness",
        "outcome_validity",
        "failure_chain",
        "mechanism_tags",
        "evidence_references",
        "confidence",
        "reviewer_required",
        "healer_eligibility",
        "healer_decision",
        "healer_outcome",
    }
    assert required <= set(schema["fields"])
    assert schema["primary_layer_enum"] == [None, "L0", "L1", "L2", "L3", "L4", "L5"]
    assert schema["formal_adjudication_completed"] is False
    assert schema["invariants"]["machine_proposal_is_not_formal_adjudication"] is True


def test_outputs_contain_no_forbidden_payload_fields_or_source_content():
    rows = _rows(OUTPUT_DIR / "classification_preparation.csv")
    forbidden = {
        "source",
        "hidden_input",
        "expected",
        "actual",
        "exception_message",
        "assertion_message",
        "traceback",
        "stdout",
        "stderr",
    }
    assert not (set(rows[0]) & forbidden)
    assert "evaluation_source_sha256" in rows[0]
    assert all(row["diagnostics_allowed_as_healer_runtime_input"] == "false" for row in rows)
    assert all(row["healer_decision"] == "not_run" for row in rows)
    assert all(row["healer_outcome"] == "not_assessed" for row in rows)


def test_runner_revision_and_taxonomy_version_are_not_conflated():
    rows = _rows(OUTPUT_DIR / "classification_preparation.csv")
    assert {row["diagnostics_runner_revision"] for row in rows} == {"r002_v3"}
    assert {row["taxonomy_version"] for row in rows} == {analyzer.TAXONOMY_VERSION}
    assert analyzer.TAXONOMY_VERSION != analyzer.DIAGNOSTICS_RUNNER_REVISION


def test_machine_proposal_summary_covers_all_cells_without_layers():
    rows = _rows(OUTPUT_DIR / "machine_proposal_summary.csv")
    assert sum(int(row["cells"]) for row in rows) == 198
    assert all(row["formal_adjudication_completed"] == "false" for row in rows)
    assert all(row["primary_layer_assigned"] == "false" for row in rows)


def test_outputs_are_deterministic_and_manifest_hash_locks_every_output():
    first = analyzer.build_outputs(REPO_ROOT)
    second = analyzer.build_outputs(REPO_ROOT)
    assert first == second
    for relative, content in first.items():
        assert (OUTPUT_DIR / relative).read_bytes() == content
    manifest = json.loads(first[Path("manifest.json")])
    assert manifest["programs"] == 198
    assert manifest["usable_diagnostics"] == 196
    assert manifest["infrastructure_invalid_unclassified"] == 2
    assert manifest["formal_adjudications_completed"] == 0
    for name, digest in manifest["outputs_sha256_excluding_manifest"].items():
        assert hashlib.sha256(first[Path(name)]).hexdigest() == digest


def test_execution_manifest_records_zero_new_executions():
    manifest = json.loads((OUTPUT_DIR / "execution_manifest.json").read_bytes())
    assert manifest["programs_prepared"] == 198
    assert manifest["human_review_queue"] == 196
    assert manifest["infrastructure_unclassified"] == 2
    assert manifest["formal_adjudications_completed"] == 0
    for field in (
        "model_calls",
        "evalplus_correctness_executions",
        "formal_diagnostics_executions",
        "partial_diagnostics_executions",
        "healer_executions",
        "validation_executions",
    ):
        assert manifest[field] == 0
    assert manifest["diagnostics_allowed_as_healer_runtime_input"] is False
