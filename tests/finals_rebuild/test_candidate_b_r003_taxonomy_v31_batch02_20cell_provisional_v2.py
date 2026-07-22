from __future__ import annotations

import csv
import io
import json
from collections import Counter

from scripts import adjudicate_candidate_b_r003_taxonomy_v31_batch02_20cell_provisional_v2 as revision


def _rows(data: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(data.decode("utf-8"))))


def test_baseline_sha_and_identity_closure() -> None:
    revision.verify_sources()
    analysis = revision.build_analysis()
    records = analysis["records"]

    assert len(records) == 20
    assert len({row["program_id"] for row in records}) == 20
    assert len({row["cell_identity_sha256"] for row in records}) == 20
    assert [row["program_id"] for row in records] == [row["program_id"] for row in analysis["roster"]]
    assert [row["source_sha256"] for row in records] == [row["source_sha256"] for row in analysis["roster"]]


def test_only_two_audit_approved_rows_change() -> None:
    analysis = revision.build_analysis()
    changed_ids = set()
    for v1, v2 in zip(analysis["v1"], analysis["records"]):
        if v1 != v2:
            changed_ids.add(v1["program_id"])
        else:
            assert v1["program_id"] not in revision.TARGET_IDS

    assert changed_ids == revision.TARGET_IDS
    assert len(analysis["deltas"]) == 2
    assert analysis["summary"]["unchanged_v1_cells"] == 18
    assert analysis["summary"]["audit_approved_revised_cells"] == 2


def test_two_revisions_match_audit_exactly() -> None:
    analysis = revision.build_analysis()
    revised = {row["program_id"]: row for row in analysis["records"] if row["program_id"] in revision.TARGET_IDS}
    assert set(revised) == revision.TARGET_IDS
    required_mechanisms = {
        "negative_number_boundary": "SUSPECTED",
        "public_examples_non_discriminating": "CONFIRMED",
        "plus_failure_not_localized": "CONFIRMED",
        "diagnostic_execution_required": "SUPPORTED",
        "return_shape_mismatch": "REJECTED",
    }
    for row in revised.values():
        assert row["primary_layer"] == "UNRESOLVED"
        assert row["secondary_layer"] == ""
        assert row["confidence"] == "LOW"
        assert row["healer_eligibility"] == "abstain"
        assert row["outcome_validity"] == "VALID_MODEL_OUTCOME"
        assert {item["tag"]: item["strength"] for item in json.loads(row["mechanism_tags_json"])} == required_mechanisms
        assert row["unresolved_reason_code"]
        assert row["evidence_present"]
        assert row["evidence_missing"]
        assert row["minimal_future_diagnostic"]


def test_v2_statistics_rebuild_from_records() -> None:
    analysis = revision.build_analysis()
    records = analysis["records"]
    summary = analysis["summary"]

    assert Counter(row["primary_layer"] for row in records) == Counter({"UNRESOLVED": 11, "L5": 5, "L2": 3, "L4": 1})
    assert Counter(row["confidence"] for row in records) == Counter({"LOW": 11, "HIGH": 7, "MEDIUM": 2})
    assert Counter(row["outcome_validity"] for row in records) == Counter({"VALID_MODEL_OUTCOME": 20})
    assert Counter(row["healer_eligibility"] for row in records) == Counter({"abstain": 20})
    assert summary["primary_layer_distribution"] == {"L2": 3, "L4": 1, "L5": 5, "UNRESOLVED": 11}
    assert summary["confidence_distribution"] == {"HIGH": 7, "LOW": 11, "MEDIUM": 2}
    assert summary["healer_eligibility_distribution"] == {"eligible": 0, "conditional": 0, "abstain": 20}
    assert len(analysis["gaps"]) == 11


def test_zero_execution_and_deterministic_on_disk_rebuild() -> None:
    first = revision.build_outputs()
    second = revision.build_outputs()
    assert first == second
    for name, data in first.items():
        assert (revision.REPO_ROOT / revision.OUTPUT_RELATIVE / name).read_bytes() == data

    execution = json.loads(first["execution_counts.json"])
    manifest = json.loads(first["manifest.json"])
    provenance = json.loads(first["provenance.json"])
    assert all(value == 0 for value in execution.values())
    assert manifest["verdict"] == "READY_FOR_BATCH02_PROVISIONAL_V2_REAUDIT"
    assert manifest["fixed_roster_sha256"] == "8742e496ce63a834d6b72237319c8b2419fd749b2e2af971700aaef4055c435d"
    assert manifest["provisional_v1_records_sha256"] == "cb4101111e610faeadc292f8d26dbbb5088848011bf9d4527dbbe029b07252e9"
    assert manifest["audit_material_findings_sha256"] == "47160a3054e2bd634a1530f4f25e663209164d5d45c7f618fb02af1cb3182e9c"
    assert provenance["upstream_modified"] is False
    assert provenance["new_runtime_observations"] == 0
    assert len(_rows(first["audit_approved_changes.csv"])) == 2
