from __future__ import annotations

import csv
import io
import json
from collections import Counter

from scripts import audit_candidate_b_r003_taxonomy_v31_batch03_20cell_provisional_v1 as audit


def _rows(data: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(data.decode("utf-8"))))


def test_sha_taxonomy_identity_and_source_closure() -> None:
    audit.verify_sources()
    analysis = audit.build_analysis()
    assert len(analysis["findings"]) == 20
    assert all(row["source_sha256"] for row in analysis["findings"])
    assert analysis["summary"]["identity_source_closure"] == 20
    assert analysis["summary"]["unique_program_id"] == 20
    assert analysis["summary"]["unique_cell_identity"] == 20
    assert analysis["summary"]["unique_source_sha256"] == 19


def test_finding_counts_and_two_material_mechanism_directions() -> None:
    analysis = audit.build_analysis()
    assert Counter(row["audit_status"] for row in analysis["findings"]) == Counter({"AFFIRMED": 18, "MATERIAL": 2})
    assert {row["program_id"] for row in analysis["material"]} == audit.MATERIAL_IDS
    assert len(analysis["differences"]) == len(analysis["material"]) == 2
    assert all(row["field_name"] == "mechanism_tags_json" for row in analysis["material"])
    assert all("frequency_one_instead_of_distinct_value" in row["recommended_value"] for row in analysis["material"])


def test_focused_audits_and_inferred_statistics() -> None:
    analysis = audit.build_analysis()
    summary = analysis["summary"]
    assert len(analysis["unresolved"]) == 7
    assert all(row["audit_status"] == "AFFIRMED" for row in analysis["unresolved"])
    assert len(analysis["healer"]) == 20
    assert all(row["independent_healer"] == row["provisional_healer"] == "abstain" for row in analysis["healer"])
    assert summary["inferred_primary_distribution"] == {"L2": 1, "L5": 12, "UNRESOLVED": 7}
    assert summary["inferred_secondary_distribution"] == {"L5": 1, "empty": 19}
    assert summary["inferred_confidence_distribution"] == {"HIGH": 13, "LOW": 7}
    assert summary["inferred_healer_distribution"] == {"eligible": 0, "conditional": 0, "abstain": 20}


def test_zero_execution_and_deterministic_on_disk_rebuild() -> None:
    first = audit.build_outputs()
    assert first == audit.build_outputs()
    for name, data in first.items():
        assert (audit.REPO_ROOT / audit.OUTPUT_RELATIVE / name).read_bytes() == data
    assert len(_rows(first["per_cell_audit_findings.csv"])) == 20
    assert len(_rows(first["material_findings.csv"])) == 2
    assert len(_rows(first["non_material_findings.csv"])) == 0
    assert all(value == 0 for value in json.loads(first["execution_counts.json"]).values())
    assert json.loads(first["manifest.json"])["verdict"] == "BATCH03_PROVISIONAL_REVISION_REQUIRED"
