from __future__ import annotations

import csv
import io
import json

from scripts import adjudicate_candidate_b_r003_taxonomy_v31_final_batch05_21cell_provisional_v1 as adjudication


def _rows(data: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(data.decode("utf-8"))))


def test_baseline_identity_source_and_set_closure() -> None:
    adjudication.verify_sources()
    analysis = adjudication.build_analysis()
    records = analysis["records"]
    assert len(records) == 21
    assert [row["batch_rank"] for row in records] == [str(i) for i in range(1, 22)]
    assert len({row["program_id"] for row in records}) == 21
    assert len({row["cell_identity_sha256"] for row in records}) == 21
    assert len({row["source_sha256"] for row in records}) == 20
    assert analysis["summary"]["legal_shared_source_ranks"] == [5, 21]
    assert analysis["summary"]["overlap_with_frozen177"] == 0
    assert analysis["summary"]["set_closure"] == "198=177+21"
    assert analysis["summary"]["remaining_adjudicated_after_batch05"] == 0


def test_each_record_has_complete_traceable_adjudication() -> None:
    records = adjudication.build_analysis()["records"]
    allowed_primary = {"L0", "L1", "L2", "L3", "L4", "L5", "UNRESOLVED"}
    for row in records:
        assert row["primary_layer"] in allowed_primary
        assert row["confidence"] in {"HIGH", "MEDIUM", "LOW"}
        assert row["outcome_validity"] == "VALID_MODEL_OUTCOME"
        assert row["healer_eligibility"] in {"eligible", "conditional", "abstain"}
        assert row["review_status"] == "PROVISIONALLY_ADJUDICATED"
        assert row["classification_status"] == "ADJUDICATED"
        assert row["mechanism_tags_json"] and json.loads(row["mechanism_tags_json"])
        assert row["failure_chain"] and len(json.loads(row["failure_chain"])) >= 2
        assert row["evidence_present"] and row["reason"] and row["evidence_citations"]
        assert row["public_evidence"] and row["source_structure_locator"]
        if row["primary_layer"] == "UNRESOLVED":
            assert row["unresolved_reason_code"]
            assert row["evidence_missing"] and row["competing_explanations"]
            assert row["minimal_future_diagnostic"]


def test_rebuilt_distributions_and_healer_safety() -> None:
    analysis = adjudication.build_analysis()
    summary = analysis["summary"]
    assert summary["primary_distribution"] == {"L5": 10, "UNRESOLVED": 11}
    assert summary["secondary_distribution"] == {"empty": 21}
    assert summary["confidence_distribution"] == {"HIGH": 10, "LOW": 11}
    assert summary["outcome_validity_distribution"] == {"VALID_MODEL_OUTCOME": 21}
    assert summary["healer_distribution"] == {"abstain": 21}
    assert summary["unresolved_ranks"] == [1, 2, 3, 4, 5, 7, 9, 14, 15, 20, 21]
    assert all(row["healer_eligibility"] == "abstain" for row in analysis["records"])
    assert len(analysis["gaps"]) == 11
    assert len(analysis["chains"]) == 21


def test_deterministic_byte_rebuild_and_zero_execution() -> None:
    first = adjudication.build_outputs()
    assert first == adjudication.build_outputs()
    for name, data in first.items():
        assert (adjudication.REPO_ROOT / adjudication.OUTPUT_RELATIVE / name).read_bytes() == data
    assert len(_rows(first["adjudication_records.csv"])) == 21
    assert len(_rows(first["failure_chain_ledger.csv"])) == 21
    assert all(value == 0 for value in json.loads(first["execution_counts.json"]).values())
    manifest = json.loads(first["manifest.json"])
    assert manifest["verdict"] == "READY_FOR_FINAL_BATCH05_PROVISIONAL_INDEPENDENT_AUDIT"
    assert manifest["remaining_after_adjudication"] == 0

