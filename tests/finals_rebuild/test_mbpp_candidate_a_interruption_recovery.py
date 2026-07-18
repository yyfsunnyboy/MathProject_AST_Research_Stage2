from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts import analyze_mbpp_candidate_a_expansion as analyzer
from scripts import freeze_mbpp_candidate_a_expansion_protocol as original
from scripts import freeze_mbpp_candidate_a_interruption_recovery as recovery
from scripts import run_mbpp_candidate_a_expansion as driver


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / recovery.OUTPUT_RELATIVE


def _r001_hashes() -> dict[str, str]:
    root = REPO_ROOT / recovery.CA_R001_RELATIVE
    return {
        relative: hashlib.sha256((root / relative).read_bytes()).hexdigest()
        for relative in recovery.CA_R001_EXPECTED_FILES
    }


def test_r001_incident_is_permanently_invalidated_and_evidence_only():
    incident = recovery.inspect_incident(REPO_ROOT)

    assert incident["status"] == "permanently_invalidated_operator_interrupt"
    assert incident["journal_count"] == 2
    assert incident["planned_cells"] == 200
    assert incident["valid_generation_for_formal_analysis"] == 0
    assert not any(incident["reuse_policy"].values())
    assert incident["unpersisted_in_flight_request"] == {
        "formal_cell_credit": 0,
        "known_to_exist": False,
        "possible": True,
        "reason": (
            "Ctrl+C may have occurred during a later run_attempt or after a response but before "
            "journal persistence; the disk evidence cannot prove or exclude such a request."
        ),
        "recoverable_from_disk": False,
    }


def test_two_r001_journals_have_exact_identity_completeness_and_hashes():
    rows = recovery.inspect_incident(REPO_ROOT)["journal_records"]

    assert [(row["task_id"], row["seed"]) for row in rows] == [
        ("Mbpp/748", 11),
        ("Mbpp/748", 22),
    ]
    assert [row["generation_id"] for row in rows] == [
        "151d77fae8ffac7c760a91767c4f6c67bd039776bd906879ffcd099a9015f8be",
        "29fc8cf9ec16041ef35778656dbc6a7d531817363e19c04e856343a5d29796b6",
    ]
    assert [row["raw_response_sha256"] for row in rows] == [
        "20e2451a476ccce4dd7ee9475a1b163807833908c828adf4aacea50e611075b3",
        "f00328582f9cda58fd1c96df51c5c815603d85441517ef8f950d66248bd707d0",
    ]
    assert all(row["journal_status_field"] is None for row in rows)
    assert all(
        row["derived_status"] == "complete_saved_first_attempt_incident_evidence_only"
        for row in rows
    )
    assert all(row["transport_complete"] for row in rows)
    assert all(row["model_generation_complete"] for row in rows)
    assert all(row["generation_complete"] for row in rows)
    assert all(row["response_fully_saved"] for row in rows)
    assert all(row["formal_analysis_eligible"] is False for row in rows)
    assert [row["model_done_reason"] for row in rows] == ["length", "stop"]


def test_r001_artifact_hashes_are_immutable_across_rebuild():
    before = _r001_hashes()
    recovery.frozen_outputs(REPO_ROOT)
    after = _r001_hashes()

    assert before == after
    assert before == {
        relative: metadata["sha256"]
        for relative, metadata in recovery.CA_R001_EXPECTED_FILES.items()
    }


def test_p0_r001_remains_complete_valid_and_generation_rerun_is_rejected(monkeypatch):
    p0 = recovery.inspect_p0(REPO_ROOT)

    assert p0["status"] == "valid_complete_generation_do_not_rerun"
    assert p0["planned_cells"] == 200
    assert p0["raw_generation_records"] == 200
    assert p0["pipeline_records"] == 200
    assert p0["journal_records"] == 200
    assert p0["unique_task_seed_identities"] == 200
    assert p0["retry_count_sum"] == 0
    assert p0["protocol_violation_count"] == 0
    assert p0["rerun_allowed"] is False

    called = False

    def forbidden(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("model call forbidden")

    monkeypatch.setattr(driver, "fetch_ollama_provenance", forbidden)
    with pytest.raises(driver.ExpansionRunError, match="P0 r001"):
        driver.generate(
            treatment="p0",
            run_id=recovery.P0_RUN_ID,
            base_url="http://127.0.0.1:1",
            timeout_seconds=600.0,
        )
    assert called is False


def test_driver_and_analyzer_reject_invalidated_candidate_r001():
    with pytest.raises(driver.ExpansionRunError, match="run ID"):
        driver.resolve_run_dir("candidate_a", recovery.CA_R001_RUN_ID)
    with pytest.raises(analyzer.ProspectiveAnalysisError, match="recovery plan"):
        analyzer.build_analysis(recovery.P0_RUN_ID, recovery.CA_R001_RUN_ID)


def test_r002_is_full_200_cell_fresh_plan_with_all_invariants_preserved():
    old = json.loads((REPO_ROOT / recovery.ORIGINAL_CA_PLAN).read_text(encoding="utf-8"))
    new = recovery.build_r002_plan(REPO_ROOT)

    assert new["run_id"] == new["logical_run_id"] == recovery.CA_R002_RUN_ID
    assert new["physical_storage_directory"] == recovery.CA_R002_RELATIVE.as_posix()
    assert new["invalidated_predecessor_run_id"] == recovery.CA_R001_RUN_ID
    assert new["predecessor_cells_reused"] == 0
    assert new["full_regeneration_required"] is True
    assert len(new["cells"]) == new["expected_cells"] == 200
    assert len({(cell["task_id"], cell["seed"]) for cell in new["cells"]}) == 200
    assert len({cell["planned_cell_id"] for cell in new["cells"]}) == 200
    assert {cell["planned_cell_id"] for cell in new["cells"]}.isdisjoint(
        {cell["planned_cell_id"] for cell in old["cells"]}
    )
    for field in (
        "task_ids",
        "seeds",
        "model",
        "model_digest",
        "quantization",
        "generation_parameters",
        "ollama_request_timeout_seconds",
        "candidate_exact_text_utf8",
        "candidate_exact_text_sha256",
        "separator_exact_text_utf8",
        "separator_sha256",
    ):
        assert new[field] == old[field]
    assert new["candidate_exact_text_sha256"] == original.CANDIDATE_SHA256
    assert new["generation_parameters"]["thinking"] is False
    assert not any(
        new[key] for key in ("retry", "resume", "selective_retry", "overwrite", "healer")
    )


def test_recovery_pairing_uses_unchanged_p0_and_complete_r002_identities():
    p0 = json.loads((REPO_ROOT / recovery.ORIGINAL_P0_PLAN).read_text(encoding="utf-8"))
    candidate = recovery.build_r002_plan(REPO_ROOT)
    paired = recovery.build_paired_plan(REPO_ROOT)
    p0_keys = [(cell["task_id"], cell["seed"]) for cell in p0["cells"]]
    candidate_keys = [(cell["task_id"], cell["seed"]) for cell in candidate["cells"]]

    assert p0_keys == candidate_keys
    assert len(set(p0_keys)) == 200
    assert paired["p0_run_id"] == recovery.P0_RUN_ID
    assert paired["candidate_run_id"] == recovery.CA_R002_RUN_ID
    assert paired["invalidated_candidate_run_id"] == recovery.CA_R001_RUN_ID
    assert paired["invalidated_candidate_cells_included"] == 0


def test_recovery_short_path_preflight_passes_and_r002_is_not_created():
    mapping = recovery.build_storage_mapping(REPO_ROOT)

    assert mapping["windows_path_budget_chars"] == 240
    assert mapping["invalidated_run"]["reuse_allowed"] is False
    assert all(run["within_budget"] for run in mapping["runs"])
    assert max(run["longest_windows_path_length"] for run in mapping["runs"]) == 166
    assert mapping["paired_analysis"]["within_budget"] is True
    assert mapping["r002_directory_created_by_freezer"] is False
    assert not (REPO_ROOT / recovery.CA_R002_RELATIVE).exists()
    assert not (REPO_ROOT / recovery.PAIRED_R002_RELATIVE).exists()


def test_updated_driver_preflight_targets_r002_without_model_call(monkeypatch):
    called = False

    def forbidden(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("model call forbidden")

    monkeypatch.setattr(driver, "fetch_ollama_provenance", forbidden)
    result = driver.preflight()
    plan = driver.load_frozen_plan("candidate_a")

    assert result["status"] == "preflight_ok_no_model_call"
    assert result["candidate_a_cells"] == 200
    assert plan["run_id"] == recovery.CA_R002_RUN_ID
    assert called is False


def test_recovery_outputs_are_byte_deterministic_and_manifest_complete():
    first = recovery.frozen_outputs(REPO_ROOT)
    second = recovery.frozen_outputs(REPO_ROOT)

    assert first == second
    assert len(first) == 6
    for relative, expected in first.items():
        assert (OUTPUT_DIR / relative).read_bytes() == expected
    manifest = json.loads(first[Path("milestone_2e_r_manifest.json")])
    assert manifest["incident"] == {
        "artifacts_modified_moved_or_deleted": False,
        "journal_evidence_count": 2,
        "run_id": recovery.CA_R001_RUN_ID,
        "status": recovery.INCIDENT_STATUS,
        "valid_generation_for_formal_analysis": 0,
    }
    assert manifest["replacement"]["run_id"] == recovery.CA_R002_RUN_ID
    assert manifest["replacement"]["planned_cells"] == 200
    assert manifest["replacement"]["predecessor_cells_reused"] == 0
    assert manifest["paired_analysis"]["candidate_r001_cells_included"] == 0
    assert not any(manifest["prohibited_actions_attestation"].values())
    for name, metadata in manifest["outputs"].items():
        content = first[Path(name)]
        assert hashlib.sha256(content).hexdigest() == metadata["sha256"]
        assert len(content) == metadata["size_bytes"]


def test_recovery_operator_guide_has_only_r002_candidate_generation():
    guide = (OUTPUT_DIR / "operator_guide_recovery_zh.md").read_text(encoding="utf-8")

    assert recovery.INCIDENT_STATUS in guide
    assert "formal valid generation=0" in guide
    assert "不得再次執行P0 generation" in guide
    assert guide.count("run_mbpp_candidate_a_expansion.py generate") == 1
    assert recovery.CA_R002_RUN_ID in guide
    assert recovery.CA_R001_RUN_ID in guide
    assert f"--run-id {recovery.CA_R001_RUN_ID} --base-url" not in guide
    assert "Candidate A r001貢獻0格" in guide
