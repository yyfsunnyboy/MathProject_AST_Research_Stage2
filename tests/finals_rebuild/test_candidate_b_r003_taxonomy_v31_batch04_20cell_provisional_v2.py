from __future__ import annotations

import csv
import io
import json
from collections import Counter

from scripts import adjudicate_candidate_b_r003_taxonomy_v31_batch04_20cell_provisional_v2 as revision


def _rows(data: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(data.decode("utf-8"))))


def test_sha_identity_order_and_source_closure() -> None:
    revision.verify_sources()
    analysis = revision.build_analysis()
    assert len(analysis["records"]) == 20
    assert [r["program_id"] for r in analysis["records"]] == [r["program_id"] for r in analysis["roster"]]
    assert [r["cell_identity_sha256"] for r in analysis["records"]] == [
        r["cell_identity_sha256"] for r in analysis["roster"]
    ]
    assert [r["source_sha256"] for r in analysis["records"]] == [r["source_sha256"] for r in analysis["roster"]]
    assert len({r["source_sha256"] for r in analysis["records"]}) == 19
    shared = [r for r in analysis["records"] if r["batch_rank"] in {"5", "12"}]
    assert len({r["source_sha256"] for r in shared}) == 1
    assert len({r["cell_identity_sha256"] for r in shared}) == 2


def test_only_one_approved_mechanism_change_and_nineteen_equal() -> None:
    analysis = revision.build_analysis()
    changed = {old["program_id"] for old, new in zip(analysis["v1"], analysis["records"]) if old != new}
    assert changed == revision.TARGET_IDS
    assert len(analysis["differences"]) == 1
    assert analysis["differences"][0]["batch_rank"] == "10"
    assert sum(old == new for old, new in zip(analysis["v1"], analysis["records"])) == 19
    for old, new in zip(analysis["v1"], analysis["records"]):
        diffs = [field for field in revision.RECORD_FIELDS if old[field] != new[field]]
        assert diffs == (["mechanism_tags_json"] if old["program_id"] in revision.TARGET_IDS else [])
        if old["program_id"] in revision.TARGET_IDS:
            assert new["primary_layer"] == "L5"
            assert new["confidence"] == "HIGH"
            assert new["outcome_validity"] == "VALID_MODEL_OUTCOME"
            assert new["healer_eligibility"] == "abstain"


def test_expected_statistics_and_mechanism_counts() -> None:
    analysis = revision.build_analysis()
    records = analysis["records"]
    mechanisms = Counter(r["mechanism_tag"] for r in analysis["mechanisms"])
    assert Counter(r["primary_layer"] for r in records) == Counter({"L5": 10, "UNRESOLVED": 9, "L4": 1})
    assert Counter(r["secondary_layer"] or "empty" for r in records) == Counter({"empty": 19, "L5": 1})
    assert Counter(r["confidence"] for r in records) == Counter({"HIGH": 11, "LOW": 9})
    assert Counter(r["outcome_validity"] for r in records) == Counter({"VALID_MODEL_OUTCOME": 20})
    assert Counter(r["healer_eligibility"] for r in records) == Counter({"abstain": 20})
    assert mechanisms[revision.OLD_TAG] == 0
    assert mechanisms[revision.NEW_TAG] == 1
    assert mechanisms["semantic_goal_drift"] == 3


def test_zero_execution_copied_ledgers_and_deterministic_rebuild() -> None:
    first = revision.build_outputs()
    assert first == revision.build_outputs()
    for name, data in first.items():
        assert (revision.REPO_ROOT / revision.OUTPUT_RELATIVE / name).read_bytes() == data
    assert first["per_cell_evidence_ledger.csv"] == (revision.REPO_ROOT / revision.V1_EVIDENCE).read_bytes()
    assert first["unresolved_evidence_gaps.csv"] == (revision.REPO_ROOT / revision.V1_GAPS).read_bytes()
    assert first["conditional_diagnostic_queue.csv"] == (
        revision.REPO_ROOT / revision.V1_CONDITIONAL
    ).read_bytes()
    assert len(_rows(first["approved_difference_ledger.csv"])) == 1
    assert all(value == 0 for value in json.loads(first["execution_counts.json"]).values())
    manifest = json.loads(first["manifest.json"])
    assert manifest["verdict"] == "READY_FOR_BATCH04_PROVISIONAL_V2_INDEPENDENT_REAUDIT"
    assert manifest["material_findings_adopted"] == 1
    assert manifest["unauthorized_differences"] == 0
