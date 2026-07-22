from __future__ import annotations

import csv
import io
import json
from collections import Counter

from scripts import audit_candidate_b_r003_taxonomy_v31_batch02_20cell_provisional_v1 as audit


def _rows(data: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(data.decode("utf-8"))))


def test_sha_and_identity_closure() -> None:
    audit.verify_sources()
    analysis = audit.build_analysis()
    findings = analysis["findings"]

    assert len(findings) == 20
    assert len({row["program_id"] for row in findings}) == 20
    assert len({row["cell_identity_sha256"] for row in findings}) == 20
    assert all(len(row["source_sha256"]) == 64 for row in findings)


def test_audit_statistics_rebuild() -> None:
    analysis = audit.build_analysis()
    findings = analysis["findings"]
    summary = analysis["summary"]

    assert Counter(row["audit_status"] for row in findings) == Counter({"AFFIRMED": 18, "MATERIAL": 2})
    assert Counter(row["recommended_primary_layer"] for row in findings) == Counter(
        {"UNRESOLVED": 11, "L5": 5, "L2": 3, "L4": 1}
    )
    assert Counter(row["recommended_confidence"] for row in findings) == Counter(
        {"LOW": 11, "HIGH": 7, "MEDIUM": 2}
    )
    assert Counter(row["recommended_healer_eligibility"] for row in findings) == Counter({"abstain": 20})
    assert summary["ready_to_freeze"] is False


def test_material_findings_are_complete_and_scoped() -> None:
    material = audit.build_analysis()["material"]
    assert len(material) == 2
    assert {row["program_id"] for row in material} == {
        "12179f714d4beea5b64235cf46138bb8095c7170101cacbc268dbb8e53ed2f1d",
        "30f2df90febe8769b5db029b8b00959550855960e64ef7a41e570149744cad4a",
    }
    for row in material:
        assert row["original_primary_layer"] == "L5"
        assert row["recommended_primary_layer"] == "UNRESOLVED"
        assert row["original_confidence"] == "MEDIUM"
        assert row["recommended_confidence"] == "LOW"
        assert row["original_healer_eligibility"] == row["recommended_healer_eligibility"] == "abstain"
        assert row["recommended_unresolved_reason_code"]
        assert row["recommended_evidence_present"]
        assert row["recommended_evidence_missing"]
        assert row["recommended_minimal_future_diagnostic"]


def test_l2_l4_decagonal_unresolved_and_healer_audit() -> None:
    summary = audit.build_analysis()["summary"]
    assert summary["l2_cells_reviewed"] == summary["l2_cells_affirmed"] == 3
    assert summary["l4_cells_reviewed"] == summary["l4_cells_affirmed"] == 1
    assert summary["decagonal_cells_reviewed"] == 3
    assert summary["decagonal_l2_secondary_l5_abstain_affirmed"] == 3
    assert summary["original_unresolved_reviewed"] == summary["original_unresolved_affirmed"] == 9
    assert summary["additional_unresolved_recommended"] == 2
    assert summary["zero_eligible_and_conditional_audit_conclusion"] == "CORRECT_NOT_OVERLY_CONSERVATIVE"


def test_zero_execution_and_deterministic_on_disk_rebuild() -> None:
    first = audit.build_outputs()
    second = audit.build_outputs()
    assert first == second
    for name, data in first.items():
        assert (audit.REPO_ROOT / audit.OUTPUT_RELATIVE / name).read_bytes() == data

    execution = json.loads(first["execution_counts.json"])
    manifest = json.loads(first["manifest.json"])
    provenance = json.loads(first["provenance.json"])
    assert all(value == 0 for value in execution.values())
    assert manifest["fixed_roster_sha256"] == "8742e496ce63a834d6b72237319c8b2419fd749b2e2af971700aaef4055c435d"
    assert manifest["provisional_records_sha256"] == "cb4101111e610faeadc292f8d26dbbb5088848011bf9d4527dbbe029b07252e9"
    assert manifest["verdict"] == "BATCH02_POST_AUDIT_REVISION_REQUIRED"
    assert provenance["independent_reconstruction_precedes_comparison"] is True
    assert provenance["provisional_modified"] is False
    assert provenance["upstream_modified"] is False
    assert len(_rows(first["per_cell_findings.csv"])) == 20
    assert len(_rows(first["material_findings.csv"])) == 2
