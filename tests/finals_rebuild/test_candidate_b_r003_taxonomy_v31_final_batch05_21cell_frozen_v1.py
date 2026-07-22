from __future__ import annotations

import csv
import io
import json

from scripts import freeze_candidate_b_r003_taxonomy_v31_final_batch05_21cell_v1 as freeze


def _rows(data: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(data.decode("utf-8"))))


def test_freeze_authorization_records_identity_and_statistics() -> None:
    freeze.verify_sources()
    payload = freeze.build_payload()
    summary = payload["freeze_summary"]
    assert summary["freeze_authorized"] is True
    assert summary["reaudit_affirmed"] == 21
    assert summary["reaudit_non_material"] == summary["reaudit_material"] == 0
    assert payload["records_bytes"] == (freeze.REPO_ROOT / freeze.V2_RECORDS).read_bytes()
    assert summary["statistics"]["primary"] == {"L5": 10, "UNRESOLVED": 11}
    assert summary["statistics"]["secondary"] == {"empty": 21}
    assert summary["statistics"]["confidence"] == {"HIGH": 10, "LOW": 11}
    assert summary["statistics"]["outcome"] == {"VALID_MODEL_OUTCOME": 21}
    assert summary["statistics"]["healer"] == {"eligible": 0, "conditional": 0, "abstain": 21}
    assert summary["statistics"]["mechanisms"]["algorithm_reconstruction_required"] == 9
    assert summary["unique_program_id"] == summary["unique_cell_identity"] == 21
    assert summary["unique_source_sha256"] == 20
    assert summary["rank5_rank21_legal_shared_source"] is True
    assert summary["intersection_with_frozen177"] == 0


def test_complete_198_identity_order_overlap_and_omission_closure() -> None:
    payload = freeze.build_payload()
    rows = payload["cumulative"]
    summary = payload["closure_summary"]
    assert len(rows) == 198
    assert [row["freeze_order"] for row in rows] == [str(i) for i in range(1, 199)]
    assert len({row["program_id"] for row in rows}) == 198
    assert len({row["cell_identity_sha256"] for row in rows}) == 198
    assert sum(row["membership"] == "final_batch05_newly_frozen" for row in rows) == 21
    assert rows[:177] == freeze._read_csv(freeze.REPO_ROOT, freeze.FROZEN177)
    assert [row["program_id"] for row in rows[177:]] == [row["program_id"] for row in freeze._read_csv(freeze.REPO_ROOT, freeze.V2_RECORDS)]
    assert summary["reconciliation"] == "198=177+21"
    assert summary["total_frozen"] == 198 and summary["unfrozen_remaining"] == 0
    assert summary["duplicate_programs"] == summary["duplicate_cells"] == 0
    assert summary["omitted_programs"] == summary["omitted_cells"] == 0
    assert summary["overlap_frozen177_batch05"] == 0


def test_deterministic_frozen_and_closure_byte_rebuild() -> None:
    first = freeze.build_outputs()
    assert first == freeze.build_outputs()
    for bundle, relative in (("freeze", freeze.FREEZE_OUTPUT), ("closure", freeze.CLOSURE_OUTPUT)):
        for name, data in first[bundle].items():
            assert (freeze.REPO_ROOT / relative / name).read_bytes() == data
    assert first["freeze"]["frozen_adjudication_records.csv"] == (freeze.REPO_ROOT / freeze.V2_RECORDS).read_bytes()
    assert len(_rows(first["closure"]["complete_cumulative_frozen_identity_ledger.csv"])) == 198


def test_manifests_and_zero_execution() -> None:
    outputs = freeze.build_outputs()
    for bundle in ("freeze", "closure"):
        counts = json.loads(outputs[bundle]["execution_counts.json"])
        assert all(value == 0 for value in counts.values())
        manifest = json.loads(outputs[bundle]["manifest.json"])
        assert manifest["verdict"] == "FINAL_BATCH05_FROZEN_198_CELL_TAXONOMY_CLOSED"
        assert all(value == 0 for key, value in manifest.items() if key.endswith("executions") or key in {"model_calls", "programs_executed"})
    freeze_manifest = json.loads(outputs["freeze"]["manifest.json"])
    closure_manifest = json.loads(outputs["closure"]["manifest.json"])
    assert freeze_manifest["frozen_records_byte_identical_to_v2"] is True
    assert freeze_manifest["total_frozen"] == 198 and freeze_manifest["remaining"] == 0
    assert closure_manifest["formal_population"] == closure_manifest["total_frozen"] == 198
    assert closure_manifest["remaining"] == 0

