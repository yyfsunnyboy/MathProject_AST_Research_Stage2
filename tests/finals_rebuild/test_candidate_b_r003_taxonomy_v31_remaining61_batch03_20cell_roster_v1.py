from __future__ import annotations

import csv
import io
import json

from scripts import prepare_candidate_b_r003_taxonomy_v31_remaining61_batch03_20cell_roster_v1 as roster


def _rows(data: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(data.decode("utf-8"))))


def test_source_sha_and_population_closure() -> None:
    roster.verify_sources()
    analysis = roster.build_analysis()
    summary = analysis["summary"]
    assert summary["formal_closure"] == "198=137+20+41"
    assert summary["selection_closure"] == "61=20+41"
    assert summary["duplicate_identities"] == summary["omitted_identities"] == 0


def test_fixed_order_roster_identity_and_overlap() -> None:
    analysis = roster.build_analysis()
    selected = analysis["roster"]
    assert len(selected) == 20
    assert [row["selection_rank"] for row in selected] == [str(i) for i in range(1, 21)]
    assert [row["remaining61_rank"] for row in selected] == [str(i) for i in range(1, 21)]
    assert len({row["program_id"] for row in selected}) == 20
    assert len({row["cell_identity_sha256"] for row in selected}) == 20
    assert all(row["selection_rule"] == roster.SELECTION_RULE for row in selected)
    assert all(row["selection_rule_citation"] for row in selected)
    summary = analysis["summary"]
    assert summary["overlap_with_frozen117"] == 0
    assert summary["overlap_with_batch01"] == 0
    assert summary["overlap_with_batch02"] == 0


def test_selection_ledger_partitions_remaining61() -> None:
    ledger = roster.build_analysis()["ledger"]
    assert len(ledger) == 61
    assert sum(row["selection_disposition"] == "BATCH03_SELECTED" for row in ledger) == 20
    deferred = [row for row in ledger if row["selection_disposition"] == "PLANNED_REMAINING_AFTER_BATCH03"]
    assert len(deferred) == 41
    assert [row["after_batch03_remaining_rank"] for row in deferred] == [str(i) for i in range(1, 42)]


def test_zero_execution_and_deterministic_on_disk_rebuild() -> None:
    first = roster.build_outputs()
    assert first == roster.build_outputs()
    for name, data in first.items():
        assert (roster.REPO_ROOT / roster.OUTPUT_RELATIVE / name).read_bytes() == data
    assert len(_rows(first["batch03_roster.csv"])) == 20
    assert len(_rows(first["selection_ledger.csv"])) == 61
    assert all(value == 0 for value in json.loads(first["execution_counts.json"]).values())
    manifest = json.loads(first["manifest.json"])
    assert manifest["verdict"] == "READY_FOR_BATCH03_ROSTER_AUDIT"
    assert manifest["batch02_frozen_records_sha256"] == "dc6d4a4fa0f0027eb87e3af48b3567c72443255fcda2e2779acf7fe0fbf70f04"
    assert manifest["batch02_frozen_manifest_sha256"] == "41f8f76edf2669ee37494a03cf9d05ec0464bb7379d6ada58a6e2921fbeafee6"
