from __future__ import annotations

import csv
import io
import json
from collections import Counter

from scripts import adjudicate_candidate_b_r003_taxonomy_v31_batch02_20cell_provisional_v1 as adjudication


def _rows(data: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(data.decode("utf-8"))))


def test_source_roster_and_identity_closure() -> None:
    adjudication.verify_sources()
    analysis = adjudication.build_analysis()
    records = analysis["records"]
    roster = analysis["roster"]

    assert len(records) == len(roster) == 20
    assert [row["program_id"] for row in records] == [row["program_id"] for row in roster]
    assert [row["cell_identity_sha256"] for row in records] == [row["cell_identity_sha256"] for row in roster]
    assert [row["source_sha256"] for row in records] == [row["source_sha256"] for row in roster]
    assert len({row["program_id"] for row in records}) == 20
    assert len({row["cell_identity_sha256"] for row in records}) == 20
    assert all(len(row["source_sha256"]) == 64 for row in records)


def test_statistics_rebuild_from_records() -> None:
    analysis = adjudication.build_analysis()
    records = analysis["records"]
    summary = analysis["summary"]

    assert dict(sorted(Counter(row["primary_layer"] for row in records).items())) == summary["primary_layer_distribution"]
    assert dict(sorted(Counter(row["secondary_layer"] or "(empty)" for row in records).items())) == summary["secondary_layer_distribution"]
    assert dict(sorted(Counter(row["confidence"] for row in records).items())) == summary["confidence_distribution"]
    assert dict(sorted(Counter(row["outcome_validity"] for row in records).items())) == summary["outcome_validity_distribution"]
    assert Counter(row["healer_eligibility"] for row in records) == Counter({"abstain": 20})
    assert summary["primary_layer_distribution"] == {"L2": 3, "L4": 1, "L5": 7, "UNRESOLVED": 9}
    assert summary["confidence_distribution"] == {"HIGH": 7, "LOW": 9, "MEDIUM": 4}
    assert summary["outcome_validity_distribution"] == {"VALID_MODEL_OUTCOME": 20}
    assert summary["healer_eligibility_distribution"] == {"eligible": 0, "conditional": 0, "abstain": 20}


def test_l2_and_eligibility_are_evidence_constrained() -> None:
    records = adjudication.build_analysis()["records"]
    eligible = [row for row in records if row["healer_eligibility"] == "eligible"]

    assert eligible == []
    decagonal = next(
        row for row in records
        if row["program_id"] == "3162f7ce0a2214cadadba6f4903b5961215cda0f2d6eb3ea126a92f69e605640"
    )
    assert decagonal["primary_layer"] == "L2"
    assert decagonal["secondary_layer"] == "L5"
    assert decagonal["healer_eligibility"] == "abstain"
    assert all("never promoted directly" in row["planning_signal_note"] for row in records)
    assert all(row["healer_eligibility"] == "abstain" for row in records if row["secondary_layer"] == "L5")


def test_every_unresolved_cell_has_complete_gap() -> None:
    analysis = adjudication.build_analysis()
    unresolved = [row for row in analysis["records"] if row["primary_layer"] == "UNRESOLVED"]
    gaps = analysis["gaps"]

    assert len(unresolved) == len(gaps) == 9
    assert {row["program_id"] for row in unresolved} == {row["program_id"] for row in gaps}
    assert all(row["unresolved_reason_code"] for row in gaps)
    assert all(row["evidence_present"] for row in gaps)
    assert all(row["evidence_missing"] for row in gaps)
    assert all(row["minimal_future_diagnostic"] for row in gaps)
    assert all(row["healer_eligibility"] == "abstain" for row in gaps)


def test_outputs_are_zero_execution_and_deterministic() -> None:
    first = adjudication.build_outputs()
    second = adjudication.build_outputs()
    assert first == second
    for name, data in first.items():
        assert (adjudication.REPO_ROOT / adjudication.OUTPUT_RELATIVE / name).read_bytes() == data

    manifest = json.loads(first["manifest.json"])
    provenance = json.loads(first["provenance.json"])
    execution = json.loads(first["execution_counts.json"])
    records = _rows(first["adjudication_records.csv"])

    assert len(records) == 20
    assert manifest["fixed_roster_sha256"] == "8742e496ce63a834d6b72237319c8b2419fd749b2e2af971700aaef4055c435d"
    assert manifest["verdict"] == "READY_FOR_BATCH02_PROVISIONAL_V1_AUDIT"
    assert provenance["new_runtime_observations"] == 0
    assert provenance["upstream_modified"] is False
    assert all(value == 0 for value in execution.values())
    for key in execution:
        assert manifest[key] == 0
        assert provenance[key] == 0
