from __future__ import annotations

import csv
import io
import json

from scripts import prepare_candidate_b_r003_taxonomy_v31_final_batch05_21cell_roster_v1 as roster


def _rows(data: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(data.decode("utf-8"))))


def test_authoritative_population_and_frozen_batch_closure() -> None:
    roster.verify_sources()
    analysis = roster.build_analysis()
    assert analysis["summary"]["formal_closure"] == "198=177+21"
    assert analysis["summary"]["selection_closure"] == "21=21+0"
    assert analysis["summary"]["overlap_with_frozen177"] == 0
    assert analysis["summary"]["duplicate_cells"] == analysis["summary"]["omitted_cells"] == 0


def test_all_remaining_identity_order_source_and_static_evidence() -> None:
    analysis = roster.build_analysis()
    rows = analysis["roster"]
    assert len(rows) == 21
    assert [row["selection_rank"] for row in rows] == [str(i) for i in range(1, 22)]
    assert [row["after_batch04_remaining_rank"] for row in rows] == [str(i) for i in range(1, 22)]
    assert len({row["program_id"] for row in rows}) == 21
    assert len({row["cell_identity_sha256"] for row in rows}) == 21
    assert len({row["source_sha256"] for row in rows}) == 20
    assert all(row["selection_reason"] == roster.SELECTION_REASON for row in rows)
    assert len(analysis["evidence"]) == 21
    assert all(row["program_readable_nonempty"] == "true" for row in analysis["evidence"])
    assert len(analysis["shared"]) == 1
    assert analysis["shared"][0]["selection_ranks_json"] == '["5","21"]'


def test_deterministic_byte_rebuild_and_zero_execution() -> None:
    first = roster.build_outputs()
    assert first == roster.build_outputs()
    for name, data in first.items():
        assert (roster.REPO_ROOT / roster.OUTPUT_RELATIVE / name).read_bytes() == data
    assert len(_rows(first["batch05_roster.csv"])) == 21
    assert len(_rows(first["selection_ledger.csv"])) == 21
    assert all(value == 0 for value in json.loads(first["execution_counts.json"]).values())
    manifest = json.loads(first["manifest.json"])
    assert manifest["batch05_cells"] == 21
    assert manifest["remaining_after_selection"] == 0
    assert manifest["batch04_remaining21_sha256"] == "48647e94065311f5f8376fb9e3e3299b96b8a95176d97a890be90919ff2ed07b"

