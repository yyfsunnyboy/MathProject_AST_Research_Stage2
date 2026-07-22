from __future__ import annotations

import csv
import io
import json

from scripts import audit_candidate_b_r003_taxonomy_v31_remaining41_batch04_20cell_roster_v1 as audit


def _rows(data: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(data.decode("utf-8"))))


def test_sha_and_independent_remaining41_rebuild() -> None:
    audit.verify_sources()
    summary = audit.build_analysis()["summary"]
    assert summary["remaining41_rows_rebuilt"] == 41
    assert summary["remaining41_rows_field_equal"] == 41
    assert summary["remaining41_order_equal"] is True


def test_batch04_per_cell_and_fixed_order_affirmed() -> None:
    analysis = audit.build_analysis()
    assert len(analysis["per_cell"]) == 20
    assert all(row["audit_status"] == "AFFIRMED" for row in analysis["per_cell"])
    assert all(row["matched_fields"] == str(len(audit.COMPARE_FIELDS)) for row in analysis["per_cell"])
    assert all(row["program_readable_status"] == "MATCH" for row in analysis["per_cell"])
    assert [row["selection_rank"] for row in analysis["per_cell"]] == [str(i) for i in range(1, 21)]
    assert all(row["audit_status"] == "AFFIRMED" for row in analysis["order_findings"])
    assert analysis["summary"]["content_or_error_directed_selection_detected"] is False
    assert analysis["summary"]["identity_source_order_affirmed"] == "20/20"


def test_closure_overlap_shared_source_and_material() -> None:
    analysis = audit.build_analysis()
    summary = analysis["summary"]
    assert summary["formal_closure"] == "198=157+20+21"
    assert summary["selection_closure"] == "41=20+21"
    assert summary["unique_program_id"] == summary["unique_cell_identity"] == 20
    assert summary["unique_source_sha256"] == 19
    assert summary["legal_shared_source_groups"] == 1
    assert summary["overlap_frozen157"] == summary["duplicates"] == summary["omissions"] == 0
    assert summary["material_findings"] == 0
    assert analysis["shared_findings"][0]["legality_status"] == "AFFIRMED"
    assert analysis["shared_findings"][0]["selection_ranks_json"] == '["5","12"]'


def test_zero_execution_and_deterministic_on_disk_rebuild() -> None:
    first = audit.build_outputs()
    assert first == audit.build_outputs()
    for name, data in first.items():
        assert (audit.REPO_ROOT / audit.OUTPUT_RELATIVE / name).read_bytes() == data
    assert len(_rows(first["per_cell_roster_findings.csv"])) == 20
    assert len(_rows(first["material_findings.csv"])) == 0
    assert all(value == 0 for value in json.loads(first["execution_counts.json"]).values())
    manifest = json.loads(first["manifest.json"])
    assert manifest["verdict"] == "READY_FOR_BATCH04_PROVISIONAL_ADJUDICATION"
    assert manifest["batch04_roster_sha256"] == "0c77a58de44149c17c2dd33ed310c2ef4e6b81b357874eb9ab21157e59b2ecae"
    assert manifest["batch04_manifest_sha256"] == "9de720aba72fa5acb134b93785201aacde0482ef817b71ac6ba3739afbe10719"
