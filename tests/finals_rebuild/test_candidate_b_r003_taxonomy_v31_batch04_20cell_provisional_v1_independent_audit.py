from __future__ import annotations

import csv
import io
import json
from collections import Counter

from scripts import audit_candidate_b_r003_taxonomy_v31_batch04_20cell_provisional_v1 as audit


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
    shared = [row for row in analysis["findings"] if row["batch_rank"] in {"5", "12"}]
    assert len({row["source_sha256"] for row in shared}) == 1
    assert len({row["cell_identity_sha256"] for row in shared}) == 2
    assert {row["independent_primary"] for row in shared} == {"UNRESOLVED"}


def test_finding_counts_and_one_material_mechanism_direction() -> None:
    analysis = audit.build_analysis()
    assert Counter(row["audit_status"] for row in analysis["findings"]) == Counter({"AFFIRMED": 19, "MATERIAL": 1})
    assert {row["program_id"] for row in analysis["material"]} == audit.MATERIAL_IDS
    assert len(analysis["differences"]) == len(analysis["material"]) == 1
    assert analysis["material"][0]["field_name"] == "mechanism_tags_json"
    assert analysis["material"][0]["batch_rank"] == "10"
    assert "frequency_one_instead_of_distinct_value" in analysis["material"][0]["recommended_value"]
    assert "dedupe_instead_of_unique_occurrence" in analysis["material"][0]["provisional_value"]


def test_focused_audits_and_inferred_statistics() -> None:
    analysis = audit.build_analysis()
    summary = analysis["summary"]
    assert len(analysis["unresolved"]) == 9
    assert all(row["audit_status"] == "AFFIRMED" for row in analysis["unresolved"])
    assert len(analysis["healer"]) == 20
    assert all(row["independent_healer"] == row["provisional_healer"] == "abstain" for row in analysis["healer"])
    rank14 = next(row for row in analysis["findings"] if row["batch_rank"] == "14")
    assert rank14["independent_primary"] == rank14["provisional_primary"] == "L4"
    assert rank14["independent_secondary"] == rank14["provisional_secondary"] == "L5"
    assert rank14["audit_status"] == "AFFIRMED"
    assert summary["inferred_primary_distribution"] == {"L4": 1, "L5": 10, "UNRESOLVED": 9}
    assert summary["inferred_secondary_distribution"] == {"L5": 1, "empty": 19}
    assert summary["inferred_confidence_distribution"] == {"HIGH": 11, "LOW": 9}
    assert summary["inferred_healer_distribution"] == {"eligible": 0, "conditional": 0, "abstain": 20}
    assert summary["rank14_secondary_l5_affirmed"] is True


def test_zero_execution_and_deterministic_on_disk_rebuild() -> None:
    first = audit.build_outputs()
    assert first == audit.build_outputs()
    for name, data in first.items():
        assert (audit.REPO_ROOT / audit.OUTPUT_RELATIVE / name).read_bytes() == data
    assert len(_rows(first["per_cell_audit_findings.csv"])) == 20
    assert len(_rows(first["material_findings.csv"])) == 1
    assert len(_rows(first["non_material_findings.csv"])) == 0
    assert len(_rows(first["unresolved_audit.csv"])) == 9
    assert all(value == 0 for value in json.loads(first["execution_counts.json"]).values())
    assert json.loads(first["manifest.json"])["verdict"] == "BATCH04_PROVISIONAL_V2_REVISION_REQUIRED"
