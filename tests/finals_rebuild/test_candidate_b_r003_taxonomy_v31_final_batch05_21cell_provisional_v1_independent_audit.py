from __future__ import annotations

import csv
import io
import json

from scripts import audit_candidate_b_r003_taxonomy_v31_final_batch05_21cell_provisional_v1 as audit


def _rows(data: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(data.decode("utf-8"))))


def test_upstream_sha_identity_and_set_closure() -> None:
    audit.verify_sources()
    analysis = audit.build_analysis()
    summary = analysis["summary"]
    assert summary["unique_program_id"] == 21
    assert summary["unique_cell_identity"] == 21
    assert summary["unique_source_sha256"] == 20
    assert summary["legal_shared_source_ranks"] == [5, 21]
    assert summary["overlap_with_frozen177"] == 0
    assert summary["set_closure"] == "198=177+21"
    assert summary["unadjudicated_remaining"] == 0


def test_independent_per_cell_findings_and_single_material_difference() -> None:
    analysis = audit.build_analysis()
    findings = analysis["findings"]
    assert len(findings) == 21
    assert sum(row["audit_status"] == "AFFIRMED" for row in findings) == 20
    assert sum(row["audit_status"] == "MATERIAL" for row in findings) == 1
    material_cell = next(row for row in findings if row["audit_status"] == "MATERIAL")
    assert material_cell["batch_rank"] == "17"
    assert json.loads(material_cell["field_differences_json"]) == ["mechanism_tags_json"]
    assert len(analysis["differences"]) == len(analysis["material"]) == 1
    assert analysis["non_material"] == []
    difference = analysis["differences"][0]
    assert difference["field_name"] == "mechanism_tags_json"
    assert "algorithm_reconstruction_required" not in difference["recommended_value"]


def test_layer_unresolved_rank11_healer_chain_and_mechanism_audits() -> None:
    analysis = audit.build_analysis()
    summary = analysis["summary"]
    assert summary["independent_primary_distribution"] == {"L5": 10, "UNRESOLVED": 11}
    assert summary["unresolved_ranks"] == [1, 2, 3, 4, 5, 7, 9, 14, 15, 20, 21]
    assert summary["rank11_primary"] == "L5"
    assert summary["rank11_outcome"] == "VALID_MODEL_OUTCOME"
    assert summary["rank11_diagnostic_only_infrastructure_node"] == "AFFIRMED"
    assert all(row["audit_status"] == "AFFIRMED" for row in analysis["healer_audit"])
    assert all(row["independent_disposition"] == "abstain" for row in analysis["healer_audit"])
    assert all(row["audit_status"] == "AFFIRMED" for row in analysis["chain_audit"])
    assert len(analysis["unresolved_audit"]) == 11
    mechanism = {row["mechanism_tag"]: row for row in analysis["mechanism_audit"]}
    assert mechanism["algorithm_reconstruction_required"]["audit_status"] == "MATERIAL"
    assert mechanism["algorithm_reconstruction_required"]["provisional_count"] == "10"
    assert mechanism["algorithm_reconstruction_required"]["independent_supported_count"] == "9"
    for tag in ("public_examples_non_discriminating", "plus_failure_not_localized", "diagnostic_execution_required", "algorithmic_error", "semantic_goal_drift"):
        assert mechanism[tag]["audit_status"] == "AFFIRMED"


def test_deterministic_byte_rebuild_and_zero_execution() -> None:
    first = audit.build_outputs()
    assert first == audit.build_outputs()
    for name, data in first.items():
        assert (audit.REPO_ROOT / audit.OUTPUT_RELATIVE / name).read_bytes() == data
    assert len(_rows(first["per_cell_audit_findings.csv"])) == 21
    assert len(_rows(first["field_level_difference_ledger.csv"])) == 1
    assert len(_rows(first["material_findings.csv"])) == 1
    assert _rows(first["non_material_findings.csv"]) == []
    assert all(value == 0 for value in json.loads(first["execution_counts.json"]).values())
    manifest = json.loads(first["manifest.json"])
    assert manifest["verdict"] == "FINAL_BATCH05_PROVISIONAL_V2_REVISION_REQUIRED"
    assert manifest["affirmed"] == 20 and manifest["non_material"] == 0 and manifest["material"] == 1

