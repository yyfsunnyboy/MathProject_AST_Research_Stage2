from __future__ import annotations

import csv
import hashlib
import io
import json

from scripts import prepare_candidate_b_r003_taxonomy_v31_remaining81_batch02_20cell_roster_v1 as roster


def _rows(data: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(data.decode("utf-8"))))


def test_sources_and_population_closure() -> None:
    roster.verify_sources()
    analysis = roster.build_analysis()
    summary = analysis["summary"]

    assert summary["formal_population"] == 198
    assert summary["frozen_cells"] == 117
    assert summary["remaining_before_batch02_selection"] == 81
    assert summary["batch02_cells"] == 20
    assert summary["remaining_after_batch02_selection"] == 61
    assert summary["unique_frozen_program_id"] == 117
    assert summary["unique_frozen_cell_identity"] == 117


def test_frozen117_funnel_and_paired_outcomes() -> None:
    summary = roster.build_analysis()["summary"]

    assert summary["primary_layer_distribution"] == {
        "L2": 3,
        "L4": 68,
        "L5": 17,
        "UNRESOLVED": 29,
    }
    assert summary["healer_eligibility_distribution"] == {
        "eligible": 0,
        "conditional": 23,
        "abstain": 94,
    }
    assert summary["transformed"] == 0
    assert summary["verified_rescue"] == 0
    assert summary["regression"] == 0
    assert summary["execution_accounts_counted_as_cells"] == 0
    assert summary["duplicate_seed_rows_counted"] == 0
    assert summary["legacy_154_case_forensic_rows_counted"] == 0


def test_batch02_uses_fixed_remaining_order_and_is_disjoint() -> None:
    analysis = roster.build_analysis()
    batch02 = analysis["batch02_rows"]
    remaining61 = analysis["remaining61_rows"]
    frozen = analysis["audit_rows"]

    assert len(batch02) == 20
    assert len(remaining61) == 61
    assert [int(row["batch_rank"]) for row in batch02] == list(range(1, 21))
    assert [int(row["source_roster_rank"]) for row in batch02] == [
        1, 2, 3, 5, 6, 8, 10, 11, 13, 14, 15, 16, 17, 18, 19, 20, 22, 23, 24, 25
    ]
    batch_ids = {row["program_id"] for row in batch02}
    assert batch_ids.isdisjoint({row["program_id"] for row in frozen})
    assert len(batch_ids) == 20
    assert len({row["cell_identity_sha256"] for row in batch02}) == 20
    assert all(len(row["source_sha256"]) == 64 for row in batch02)


def test_outputs_are_deterministic_and_self_consistent() -> None:
    first = roster.build_outputs()
    second = roster.build_outputs()
    assert first == second

    manifest = json.loads(first["manifest.json"])
    provenance = json.loads(first["provenance.json"])
    batch02 = _rows(first["batch02_roster.csv"])
    remaining61 = _rows(first["remaining61_roster.csv"])

    digest = hashlib.sha256(first["batch02_roster.csv"]).hexdigest()
    assert manifest["status"] == "READY_FOR_BATCH02_20CELL_ADJUDICATION"
    assert manifest["batch02_roster_sha256"] == digest
    assert provenance["batch02_roster_sha256"] == digest
    assert len(batch02) == 20
    assert len(remaining61) == 61
    assert provenance["no_adjudication"] is True
    assert provenance["model_calls"] == 0
    assert provenance["candidate_executions"] == 0
    assert provenance["diagnostics_executions"] == 0
    assert provenance["healer_executions"] == 0
