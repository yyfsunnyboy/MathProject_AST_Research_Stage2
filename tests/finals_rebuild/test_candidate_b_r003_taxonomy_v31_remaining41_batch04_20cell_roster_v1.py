from __future__ import annotations

import csv
import io
import json

from scripts import prepare_candidate_b_r003_taxonomy_v31_remaining41_batch04_20cell_roster_v1 as roster


def _rows(data: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(data.decode("utf-8"))))


def test_source_sha_and_population_closure() -> None:
    roster.verify_sources()
    analysis = roster.build_analysis()
    summary = analysis["summary"]
    assert summary["formal_closure"] == "198=157+20+21"
    assert summary["selection_closure"] == "41=20+21"
    assert summary["duplicate_identities"] == summary["omitted_identities"] == 0
    assert summary["programs_readable_nonempty"] == 20


def test_fixed_order_roster_identity_and_overlap() -> None:
    analysis = roster.build_analysis()
    selected = analysis["roster"]
    assert len(selected) == 20
    assert [row["selection_rank"] for row in selected] == [str(i) for i in range(1, 21)]
    assert [row["remaining41_rank"] for row in selected] == [str(i) for i in range(1, 21)]
    assert [row["remaining61_rank"] for row in selected] == [str(i) for i in range(21, 41)]
    assert len({row["program_id"] for row in selected}) == 20
    assert len({row["cell_identity_sha256"] for row in selected}) == 20
    assert len({row["source_sha256"] for row in selected}) == 19
    assert all(row["selection_rule"] == roster.SELECTION_RULE for row in selected)
    summary = analysis["summary"]
    assert summary["overlap_with_frozen157"] == 0
    assert summary["overlap_with_batch01"] == summary["overlap_with_batch02"] == summary["overlap_with_batch03"] == 0
    assert summary["legal_shared_source_groups"] == 1


def test_selection_ledger_and_remaining21_partition() -> None:
    analysis = roster.build_analysis()
    ledger = analysis["ledger"]
    remaining21 = analysis["remaining21"]
    assert len(ledger) == 41
    assert sum(row["selection_disposition"] == "BATCH04_SELECTED" for row in ledger) == 20
    deferred = [row for row in ledger if row["selection_disposition"] == "PLANNED_REMAINING_AFTER_BATCH04"]
    assert len(deferred) == len(remaining21) == 21
    assert [row["after_batch04_remaining_rank"] for row in remaining21] == [str(i) for i in range(1, 22)]


def test_zero_execution_and_deterministic_on_disk_rebuild() -> None:
    first = roster.build_outputs()
    assert first == roster.build_outputs()
    for name, data in first.items():
        assert (roster.REPO_ROOT / roster.OUTPUT_RELATIVE / name).read_bytes() == data
    assert len(_rows(first["batch04_roster.csv"])) == 20
    assert len(_rows(first["selection_ledger.csv"])) == 41
    assert len(_rows(first["remaining21_roster.csv"])) == 21
    assert all(value == 0 for value in json.loads(first["execution_counts.json"]).values())
    manifest = json.loads(first["manifest.json"])
    assert manifest["verdict"] == "READY_FOR_BATCH04_ROSTER_AUDIT"
    assert manifest["frozen_cells"] == 157
    assert manifest["remaining_after_selection"] == 21
