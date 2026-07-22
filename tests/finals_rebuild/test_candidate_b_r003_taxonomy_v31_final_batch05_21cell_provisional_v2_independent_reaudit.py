from __future__ import annotations

import csv
import io
import json

from scripts import reaudit_candidate_b_r003_taxonomy_v31_final_batch05_21cell_provisional_v2 as reaudit


def _rows(data: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(data.decode("utf-8"))))


def test_sha_identity_and_set_closure() -> None:
    reaudit.verify_sources()
    analysis = reaudit.build_analysis()
    summary = analysis["summary"]
    assert summary["unique_program_id"] == summary["unique_cell_identity"] == 21
    assert summary["unique_source_sha256"] == 20
    assert summary["legal_shared_source_ranks"] == [5, 21]
    assert summary["overlap_with_frozen177"] == 0
    assert summary["set_closure"] == "198=177+21"
    assert summary["unadjudicated_remaining"] == 0


def test_single_approved_v1_v2_difference_and_per_cell_affirmation() -> None:
    analysis = reaudit.build_analysis()
    summary = analysis["summary"]
    assert summary["v1_to_v2_changed_records"] == 1
    assert summary["v1_to_v2_changed_fields"] == 1
    assert summary["approved_changes_affirmed"] == 1
    assert summary["unauthorized_differences"] == 0
    assert summary["rank17_nonmechanism_fields_unchanged"] is True
    assert summary["unchanged_records"] == 20
    assert len(analysis["difference_verification"]) == 1
    difference = analysis["difference_verification"][0]
    assert difference["batch_rank"] == "17"
    assert difference["field_name"] == "mechanism_tags_json"
    assert difference["reaudit_status"] == "AFFIRMED"
    assert len(analysis["findings"]) == 21
    assert all(row["reaudit_status"] == "AFFIRMED" for row in analysis["findings"])
    assert analysis["material"] == analysis["non_material"] == []


def test_statistics_mechanisms_chains_unresolved_and_healer() -> None:
    analysis = reaudit.build_analysis()
    summary = analysis["summary"]
    assert summary["primary_distribution"] == {"L5": 10, "UNRESOLVED": 11}
    assert summary["secondary_distribution"] == {"empty": 21}
    assert summary["confidence_distribution"] == {"HIGH": 10, "LOW": 11}
    assert summary["outcome_validity_distribution"] == {"VALID_MODEL_OUTCOME": 21}
    assert summary["healer_distribution"] == {"eligible": 0, "conditional": 0, "abstain": 21}
    assert summary["algorithm_reconstruction_required"] == 9
    assert summary["failure_chains_affirmed"] == 21
    assert summary["unresolved_evidence_affirmed"] == 11
    assert len(analysis["mechanism_findings"]) == len(summary["mechanism_distribution"])
    assert all(row["reaudit_status"] == "AFFIRMED" for row in analysis["mechanism_findings"])
    assert all(row["reaudit_status"] == "AFFIRMED" for row in analysis["chain_findings"])
    assert len(analysis["unresolved_findings"]) == 11
    assert all(row["reaudit_status"] == "AFFIRMED" for row in analysis["unresolved_findings"])


def test_deterministic_byte_rebuild_and_zero_execution() -> None:
    first = reaudit.build_outputs()
    assert first == reaudit.build_outputs()
    for name, data in first.items():
        assert (reaudit.REPO_ROOT / reaudit.OUTPUT_RELATIVE / name).read_bytes() == data
    assert len(_rows(first["per_cell_v2_reaudit_findings.csv"])) == 21
    assert len(_rows(first["field_level_difference_verification.csv"])) == 1
    assert _rows(first["material_findings.csv"]) == []
    assert _rows(first["non_material_findings.csv"]) == []
    assert all(value == 0 for value in json.loads(first["execution_counts.json"]).values())
    manifest = json.loads(first["manifest.json"])
    assert manifest["verdict"] == "READY_TO_FREEZE_FINAL_BATCH05_PROVISIONAL_V2"
    assert manifest["affirmed"] == 21
    assert manifest["non_material"] == manifest["material"] == 0

