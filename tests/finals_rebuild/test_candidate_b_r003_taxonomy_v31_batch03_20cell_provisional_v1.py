from __future__ import annotations

import csv
import io
import json
from collections import Counter

from scripts import adjudicate_candidate_b_r003_taxonomy_v31_batch03_20cell_provisional_v1 as adjudication


def _rows(data: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(data.decode("utf-8"))))


def test_sha_identity_order_and_source_closure() -> None:
    adjudication.verify_sources()
    analysis = adjudication.build_analysis()
    roster = adjudication._read_csv(adjudication.REPO_ROOT, adjudication.ROSTER)
    records = analysis["records"]
    assert len(records) == 20
    assert [r["program_id"] for r in records] == [r["program_id"] for r in roster]
    assert [r["cell_identity_sha256"] for r in records] == [r["cell_identity_sha256"] for r in roster]
    assert [r["source_sha256"] for r in records] == [r["source_sha256"] for r in roster]


def test_complete_schema_dispositions_and_evidence_guards() -> None:
    records = adjudication.build_analysis()["records"]
    assert all(set(row) == set(adjudication.RECORD_FIELDS) for row in records)
    assert all(row["primary_layer"] in {"L0", "L1", "L2", "L3", "L4", "L5", "UNRESOLVED"} for row in records)
    assert all(row["healer_eligibility"] in {"eligible", "conditional", "abstain"} for row in records)
    assert all(row["failure_chain"] and row["reason"] and row["evidence_present"] and row["evidence_citations"] for row in records)
    assert all(row["eligibility_reason"] for row in records if row["healer_eligibility"] == "abstain")
    assert all(row["unresolved_reason_code"] and row["evidence_missing"] and row["minimal_future_diagnostic"] for row in records if row["primary_layer"] == "UNRESOLVED")


def test_statistics_rebuild_and_ledgers() -> None:
    analysis = adjudication.build_analysis()
    records = analysis["records"]
    assert Counter(r["primary_layer"] for r in records) == Counter({"L5": 12, "UNRESOLVED": 7, "L2": 1})
    assert Counter(r["secondary_layer"] or "empty" for r in records) == Counter({"empty": 19, "L5": 1})
    assert Counter(r["confidence"] for r in records) == Counter({"HIGH": 13, "LOW": 7})
    assert Counter(r["outcome_validity"] for r in records) == Counter({"VALID_MODEL_OUTCOME": 20})
    assert Counter(r["healer_eligibility"] for r in records) == Counter({"abstain": 20})
    assert len(analysis["evidence"]) == 20
    assert len(analysis["gaps"]) == 7
    assert analysis["conditional"] == []


def test_zero_execution_and_deterministic_on_disk_rebuild() -> None:
    first = adjudication.build_outputs()
    assert first == adjudication.build_outputs()
    for name, data in first.items():
        assert (adjudication.REPO_ROOT / adjudication.OUTPUT_RELATIVE / name).read_bytes() == data
    assert len(_rows(first["adjudication_records.csv"])) == 20
    assert len(_rows(first["per_cell_evidence_ledger.csv"])) == 20
    assert len(_rows(first["conditional_diagnostic_queue.csv"])) == 0
    assert len(_rows(first["unresolved_evidence_gaps.csv"])) == 7
    assert all(value == 0 for value in json.loads(first["execution_counts.json"]).values())
    assert json.loads(first["manifest.json"])["verdict"] == "READY_FOR_BATCH03_PROVISIONAL_AUDIT"
