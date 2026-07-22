from __future__ import annotations

import csv
import io
import json

from scripts import audit_candidate_b_r003_taxonomy_v31_remaining61_batch03_20cell_roster_v1 as audit


def _rows(data: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(data.decode("utf-8"))))


def test_sha_and_independent_remaining61_rebuild() -> None:
    audit.verify_sources()
    summary = audit.build_analysis()["summary"]
    assert summary["remaining61_rows_rebuilt"] == 61
    assert summary["remaining61_rows_field_equal"] == 61
    assert summary["remaining61_order_equal"] is True


def test_batch03_per_cell_and_fixed_order_affirmed() -> None:
    analysis = audit.build_analysis()
    assert len(analysis["per_cell"]) == 20
    assert all(row["audit_status"] == "AFFIRMED" for row in analysis["per_cell"])
    assert all(row["matched_fields"] == str(len(audit.COMPARE_FIELDS)) for row in analysis["per_cell"])
    assert [row["selection_rank"] for row in analysis["per_cell"]] == [str(i) for i in range(1, 21)]
    assert all(row["audit_status"] == "AFFIRMED" for row in analysis["order_findings"])
    assert analysis["summary"]["content_or_error_directed_selection_detected"] is False


def test_closure_overlap_duplicates_omissions_and_material() -> None:
    summary = audit.build_analysis()["summary"]
    assert summary["formal_closure"] == "198=137+20+41"
    assert summary["selection_closure"] == "61=20+41"
    assert summary["unique_program_id"] == summary["unique_cell_identity"] == 20
    assert summary["overlap_frozen117"] == summary["overlap_batch01"] == summary["overlap_batch02"] == 0
    assert summary["duplicates"] == summary["omissions"] == summary["material_findings"] == 0


def test_zero_execution_and_deterministic_on_disk_rebuild() -> None:
    first = audit.build_outputs()
    assert first == audit.build_outputs()
    for name, data in first.items():
        assert (audit.REPO_ROOT / audit.OUTPUT_RELATIVE / name).read_bytes() == data
    assert len(_rows(first["per_cell_roster_findings.csv"])) == 20
    assert len(_rows(first["material_findings.csv"])) == 0
    assert all(value == 0 for value in json.loads(first["execution_counts.json"]).values())
    manifest = json.loads(first["manifest.json"])
    assert manifest["verdict"] == "READY_FOR_BATCH03_PROVISIONAL_ADJUDICATION"
    assert manifest["batch03_roster_sha256"] == "6f772918bb5c16eb1c9ad88e086e936b4e1d12e7e378924cc13a22a812ac1f74"
    assert manifest["batch03_manifest_sha256"] == "42552f07b842b7317e94f162bf6345d2d35761bcd6c4972451344cba3393001c"
