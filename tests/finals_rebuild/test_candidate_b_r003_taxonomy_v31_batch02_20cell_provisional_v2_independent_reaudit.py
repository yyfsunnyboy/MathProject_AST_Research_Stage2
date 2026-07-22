from __future__ import annotations

import csv
import io
import json
from collections import Counter

from scripts import reaudit_candidate_b_r003_taxonomy_v31_batch02_20cell_provisional_v2 as reaudit


def _rows(data: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(data.decode("utf-8"))))


def test_sha_identity_and_exact_change_closure() -> None:
    reaudit.verify_sources()
    analysis = reaudit.build_analysis()
    findings = analysis["findings"]
    assert len(findings) == 20
    assert Counter(r["finding_status"] for r in findings) == Counter({"UNCHANGED_AFFIRMED": 18, "AUDIT_CHANGE_AFFIRMED": 2})
    assert {r["program_id"] for r in findings if r["finding_status"] == "AUDIT_CHANGE_AFFIRMED"} == reaudit.TARGET_IDS
    assert all(r["identity_status"] == r["source_sha_status"] == "MATCH" for r in findings)


def test_two_changes_fully_implement_audit_and_eighteen_are_equal() -> None:
    analysis = reaudit.build_analysis()
    assert analysis["summary"]["audit_change_affirmed"] == 2
    assert analysis["summary"]["unchanged_affirmed"] == 18
    assert analysis["summary"]["unauthorized_differences"] == 0
    for row in analysis["findings"]:
        if row["program_id"] in reaudit.TARGET_IDS:
            assert row["audit_implementation_status"] == "COMPLETE"
            assert row["evidence_gap_status"] == "COMPLETE"
            assert row["citation_status"] == "COMPLETE"
            assert set(json.loads(row["changed_fields_json"])) == reaudit.EXPECTED_CHANGED_FIELDS
        else:
            assert json.loads(row["changed_fields_json"]) == []


def test_rebuilt_statistics_and_no_material_findings() -> None:
    summary = reaudit.build_analysis()["summary"]
    assert summary["primary_layer_distribution"] == {"L2": 3, "L4": 1, "L5": 5, "UNRESOLVED": 11}
    assert summary["secondary_layer_distribution"] == {"L5": 4, "empty": 16}
    assert summary["confidence_distribution"] == {"HIGH": 7, "LOW": 11, "MEDIUM": 2}
    assert summary["outcome_validity_distribution"] == {"VALID_MODEL_OUTCOME": 20}
    assert summary["healer_eligibility_distribution"] == {"eligible": 0, "conditional": 0, "abstain": 20}
    assert summary["unique_program_id"] == 20
    assert summary["unique_cell_identity"] == 20
    assert summary["unique_source_sha256"] == 19
    assert summary["material_findings"] == 0


def test_zero_execution_and_deterministic_rebuild() -> None:
    first = reaudit.build_outputs()
    assert first == reaudit.build_outputs()
    for name, data in first.items():
        assert (reaudit.REPO_ROOT / reaudit.OUTPUT_RELATIVE / name).read_bytes() == data
    assert len(_rows(first["per_cell_change_findings.csv"])) == 20
    assert len(_rows(first["material_findings.csv"])) == 0
    assert all(value == 0 for value in json.loads(first["execution_counts.json"]).values())
    manifest = json.loads(first["manifest.json"])
    assert manifest["verdict"] == "READY_TO_FREEZE_BATCH02_PROVISIONAL_V2"
    assert manifest["audit_approved_differences"] == 2
    assert manifest["unauthorized_differences"] == 0
