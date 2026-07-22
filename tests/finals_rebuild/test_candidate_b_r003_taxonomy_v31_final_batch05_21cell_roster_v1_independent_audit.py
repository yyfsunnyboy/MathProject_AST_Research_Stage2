from __future__ import annotations

import csv
import io
import json

from scripts import audit_candidate_b_r003_taxonomy_v31_final_batch05_21cell_roster_v1 as audit


def _rows(data: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(data.decode("utf-8"))))


def test_independent_identity_source_order_and_selection_audit() -> None:
    audit.verify_sources()
    analysis = audit.build_analysis()
    assert len(analysis["findings"]) == 21
    assert all(row["audit_status"] == "AFFIRMED" for row in analysis["findings"])
    assert all(row["matched_fields"] == str(len(audit.COMPARE_FIELDS)) for row in analysis["findings"])
    assert all(row["audit_status"] == "AFFIRMED" for row in analysis["selection"])
    assert analysis["material"] == []


def test_audit_closure_shared_source_and_no_taxonomy() -> None:
    analysis = audit.build_analysis()
    summary = analysis["summary"]
    assert summary["formal_closure"] == "198=177+21"
    assert summary["selection_closure"] == "21=21+0"
    assert summary["remaining_after_selection"] == 0
    assert summary["overlap_with_frozen177"] == 0
    assert summary["duplicate_cells"] == summary["omitted_cells"] == 0
    assert summary["taxonomy_judgments_created"] == 0
    assert len(analysis["shared"]) == 1
    assert analysis["shared"][0]["selection_ranks_json"] == '["5","21"]'


def test_audit_deterministic_byte_rebuild_and_zero_execution() -> None:
    first = audit.build_outputs()
    assert first == audit.build_outputs()
    for name, data in first.items():
        assert (audit.REPO_ROOT / audit.OUTPUT_RELATIVE / name).read_bytes() == data
    assert len(_rows(first["per_cell_roster_findings.csv"])) == 21
    assert _rows(first["material_findings.csv"]) == []
    assert all(value == 0 for value in json.loads(first["execution_counts.json"]).values())
    manifest = json.loads(first["manifest.json"])
    assert manifest["verdict"] == "READY_FOR_FINAL_BATCH05_PROVISIONAL_ADJUDICATION"
    assert manifest["material_findings"] == 0

