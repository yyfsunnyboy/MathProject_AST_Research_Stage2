from __future__ import annotations

import csv
import io
import json

from scripts import adjudicate_candidate_b_r003_taxonomy_v31_final_batch05_21cell_provisional_v2 as v2


def _rows(data: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(data.decode("utf-8"))))


def test_upstream_sha_and_single_approved_difference() -> None:
    v2.verify_sources()
    analysis = v2.build_analysis()
    assert analysis["summary"]["v1_to_v2_changed_records"] == 1
    assert analysis["summary"]["v1_to_v2_changed_fields"] == 1
    assert analysis["summary"]["changed_ranks"] == [17]
    assert analysis["summary"]["approved_differences_adopted"] == 1
    assert analysis["summary"]["unauthorized_differences"] == 0
    assert analysis["summary"]["unchanged_records"] == 20
    assert len(analysis["difference_ledger"]) == 1
    assert analysis["difference_ledger"][0]["field_name"] == "mechanism_tags_json"


def test_rank17_only_removes_unsupported_tag_and_preserves_other_fields() -> None:
    _, before = v2._read_csv_with_fields(v2.REPO_ROOT, v2.V1_RECORDS)
    after = v2.build_analysis()["records"]
    target_before = before[16]
    target_after = after[16]
    before_tags = {tag["tag"] for tag in json.loads(target_before["mechanism_tags_json"])}
    after_tags = {tag["tag"] for tag in json.loads(target_after["mechanism_tags_json"])}
    assert before_tags == {"end_index_off_by_one", "wrong_boundary_condition", "algorithm_reconstruction_required"}
    assert after_tags == {"end_index_off_by_one", "wrong_boundary_condition"}
    for field in target_before:
        if field != "mechanism_tags_json":
            assert target_before[field] == target_after[field]
    assert target_after["primary_layer"] == "L5"
    assert target_after["confidence"] == "HIGH"
    assert target_after["outcome_validity"] == "VALID_MODEL_OUTCOME"
    assert target_after["healer_eligibility"] == "abstain"
    assert target_after["failure_chain"] == target_before["failure_chain"]
    for index in range(21):
        if index != 16:
            assert before[index] == after[index]


def test_v2_statistics_identity_set_and_mechanism_rebuild() -> None:
    analysis = v2.build_analysis()
    summary = analysis["summary"]
    assert summary["primary_distribution"] == {"L5": 10, "UNRESOLVED": 11}
    assert summary["secondary_distribution"] == {"empty": 21}
    assert summary["confidence_distribution"] == {"HIGH": 10, "LOW": 11}
    assert summary["outcome_validity_distribution"] == {"VALID_MODEL_OUTCOME": 21}
    assert summary["healer_distribution"] == {"eligible": 0, "conditional": 0, "abstain": 21}
    assert summary["algorithm_reconstruction_required_v1"] == 10
    assert summary["algorithm_reconstruction_required_v2"] == 9
    assert summary["unique_program_id"] == summary["unique_cell_identity"] == 21
    assert summary["unique_source_sha256"] == 20
    assert summary["legal_shared_source_ranks"] == [5, 21]
    assert summary["overlap_with_frozen177"] == 0
    assert summary["set_closure"] == "198=177+21"
    assert summary["unadjudicated_remaining"] == 0


def test_deterministic_byte_rebuild_and_zero_execution() -> None:
    first = v2.build_outputs()
    assert first == v2.build_outputs()
    for name, data in first.items():
        assert (v2.REPO_ROOT / v2.OUTPUT_RELATIVE / name).read_bytes() == data
    assert len(_rows(first["adjudication_records.csv"])) == 21
    assert len(_rows(first["approved_difference_ledger.csv"])) == 1
    assert all(value == 0 for value in json.loads(first["execution_counts.json"]).values())
    manifest = json.loads(first["manifest.json"])
    assert manifest["verdict"] == "READY_FOR_FINAL_BATCH05_PROVISIONAL_V2_INDEPENDENT_REAUDIT"
    assert manifest["changed_records"] == manifest["changed_fields"] == 1
    assert manifest["unauthorized_differences"] == 0

