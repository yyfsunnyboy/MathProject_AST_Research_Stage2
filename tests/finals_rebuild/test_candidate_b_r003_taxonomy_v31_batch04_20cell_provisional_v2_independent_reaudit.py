from __future__ import annotations

import csv
import io
import json
from collections import Counter

from scripts import reaudit_candidate_b_r003_taxonomy_v31_batch04_20cell_provisional_v2 as reaudit


def _rows(data: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(data.decode("utf-8"))))


def test_sha_identity_source_and_complete_delta_closure() -> None:
    reaudit.verify_sources()
    analysis = reaudit.build_analysis()
    assert len(analysis["findings"]) == 20
    assert Counter(r["change_status"] for r in analysis["findings"]) == Counter(
        {"UNCHANGED_AFFIRMED": 19, "APPROVED_CHANGE_AFFIRMED": 1}
    )
    assert analysis["summary"]["identity_source_closure"] == 20
    assert analysis["summary"]["unique_source_sha256"] == 19
    assert analysis["summary"]["legal_shared_source_ranks"] == ["5", "12"]


def test_one_independent_approved_change_verification() -> None:
    analysis = reaudit.build_analysis()
    assert len(analysis["approved"]) == len(analysis["differences"]) == 1
    assert {r["program_id"] for r in analysis["approved"]} == reaudit.TARGET_IDS
    assert analysis["approved"][0]["batch_rank"] == "10"
    assert all(
        r["verification_status"] == "AFFIRMED"
        and r["preserved_fields_status"] == "ALL_NON_MECHANISM_FIELDS_EQUAL"
        for r in analysis["approved"]
    )
    assert all(
        reaudit.NEW_TAG in r["v2_mechanisms_json"] and reaudit.OLD_TAG not in r["v2_mechanisms_json"]
        for r in analysis["approved"]
    )
    assert "semantic_goal_drift" in analysis["approved"][0]["v2_mechanisms_json"]


def test_derivatives_statistics_and_no_issues() -> None:
    summary = reaudit.build_analysis()["summary"]
    stats = summary["rebuilt_statistics"]
    assert summary["affirmed"] == 20
    assert summary["non_material"] == summary["material"] == summary["unauthorized_differences"] == 0
    assert summary["first_audit_material_fully_corrected"] is True
    assert stats["primary"] == {"L4": 1, "L5": 10, "UNRESOLVED": 9}
    assert stats["secondary"] == {"L5": 1, "empty": 19}
    assert stats["confidence"] == {"HIGH": 11, "LOW": 9}
    assert stats["outcome"] == {"VALID_MODEL_OUTCOME": 20}
    assert stats["healer"] == {"eligible": 0, "conditional": 0, "abstain": 20}
    assert stats["mechanisms"][reaudit.NEW_TAG] == 1
    assert reaudit.OLD_TAG not in stats["mechanisms"]
    assert stats["mechanisms"]["semantic_goal_drift"] == 3


def test_zero_execution_and_deterministic_on_disk_rebuild() -> None:
    first = reaudit.build_outputs()
    assert first == reaudit.build_outputs()
    for name, data in first.items():
        assert (reaudit.REPO_ROOT / reaudit.OUTPUT_RELATIVE / name).read_bytes() == data
    assert len(_rows(first["per_cell_v2_reaudit_findings.csv"])) == 20
    assert len(_rows(first["material_findings.csv"])) == len(_rows(first["non_material_findings.csv"])) == 0
    assert all(value == 0 for value in json.loads(first["execution_counts.json"]).values())
    assert json.loads(first["manifest.json"])["verdict"] == "READY_TO_FREEZE_BATCH04_PROVISIONAL_V2"
