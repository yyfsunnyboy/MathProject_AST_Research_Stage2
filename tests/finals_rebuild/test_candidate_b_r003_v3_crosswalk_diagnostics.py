from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

import pytest

from scripts import build_candidate_b_r003_v3_crosswalk as crosswalk
from scripts import run_candidate_b_r003_unresolved_diagnostics as runner


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / crosswalk.OUTPUT_RELATIVE


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_crosswalk_preserves_all_legacy_census_fields_and_300_identities():
    result = crosswalk.build_analysis(REPO_ROOT, crosswalk.V3_ATTACHMENT)
    derived = result["crosswalk_rows"]
    legacy = _read_csv(REPO_ROOT / crosswalk.CENSUS)
    assert len(derived) == len(legacy) == 300
    assert len({row["program_id"] for row in derived}) == 300
    assert result["legacy_fields"] == list(legacy[0])
    for before, after in zip(legacy, derived):
        assert {field: after[field] for field in result["legacy_fields"]} == before


def test_v3_counts_gates_and_unresolved_remain_null_pending_review():
    rows = crosswalk.build_analysis(REPO_ROOT, crosswalk.V3_ATTACHMENT)["crosswalk_rows"]
    assert sum(row["v3_primary_failure_layer"] == "L1" for row in rows) == 20
    assert sum(row["v3_primary_failure_layer"] == "L2" for row in rows) == 6
    pending = [row for row in rows if row["v3_classification_status"] == "PENDING_REVIEW"]
    assert len(pending) == 198
    assert all(row["v3_primary_failure_layer"] == "" for row in pending)
    assert all(row["v3_outcome_validity"] == "PENDING_REVIEW" for row in pending)
    assert all(json.loads(row["v3_mechanism_tags"]) == ["needs_human_review"] for row in pending)
    l1 = [row for row in rows if row["v3_primary_failure_layer"] == "L1"]
    l2 = [row for row in rows if row["v3_primary_failure_layer"] == "L2"]
    assert all(row["v3_g3e_entry_point"] == "NOT_ASSESSED" for row in l1)
    assert all(row["v3_g3e_entry_point"] == "FAIL" for row in l2)
    assert all(row["v3_g3s_output_schema"] == "NOT_APPLICABLE" for row in rows)


def test_all_21_adjudication_rows_and_fields_are_preserved_as_legacy_evidence():
    result = crosswalk.build_analysis(REPO_ROOT, crosswalk.V3_ATTACHMENT)
    rows = result["crosswalk_rows"]
    reviewed = [row for row in rows if row["legacy_adjudication_program_id"]]
    assert len(reviewed) == 21
    original = {row["program_id"]: row for row in _read_csv(REPO_ROOT / crosswalk.ADJUDICATION)}
    for row in reviewed:
        source = original[row["program_id"]]
        for field in result["adjudication_fields"]:
            assert row[f"legacy_adjudication_{field}"] == source[field]
    rank21 = next(row for row in reviewed if row["legacy_adjudication_review_rank"] == "21")
    assert rank21["legacy_adjudication_adjudicated_layer"] == "L4"
    assert rank21["v3_primary_failure_layer"] == ""
    assert rank21["v3_classification_status"] == "PENDING_REVIEW"


def test_v3_healer_eligibility_decision_outcome_are_separate_and_evidence_role_is_development():
    rows = crosswalk.build_analysis(REPO_ROOT, crosswalk.V3_ATTACHMENT)["crosswalk_rows"]
    exact = [row for row in rows if row["v3_healer_eligibility"] == "eligible"]
    assert len(exact) == 2
    assert all(row["v3_healer_decision"] == "transformed" for row in exact)
    assert all(row["v3_healer_outcome"] == "unchanged_fail" for row in exact)
    assert sum(row["v3_healer_eligibility"] == "undetermined" for row in rows) == 198
    assert {row["v3_healer_decision"] for row in rows} <= {"transformed", "abstained", "no_trigger"}
    assert {row["v3_healer_outcome"] for row in rows} == {"preserved_pass", "unchanged_fail"}
    assert all(row["v3_evidence_role"] == "development" for row in rows)
    assert all(row["v3_diagnostics_allowed_as_healer_runtime_input"] == "false" for row in rows)


def test_diagnostic_ledger_has_198_hash_only_identities_and_no_source_or_task_values():
    rows = crosswalk.build_analysis(REPO_ROOT, crosswalk.V3_ATTACHMENT)["diagnostic_rows"]
    assert len(rows) == len({row["cell_identity_sha256"] for row in rows}) == 198
    assert all(row["primary_failure_layer"] == "" for row in rows)
    assert all(row["classification_status"] == "PENDING_REVIEW" for row in rows)
    forbidden_fields = {"task_id", "seed", "source", "evaluation_source", "completion"}
    assert not (set(rows[0]) & forbidden_fields)
    hash_fields = {"cell_identity_sha256", "program_id", "task_identity_sha256", "generation_id", "evaluation_source_sha256", "prompt_hash", "evaluator_hash"}
    assert all(len(row[field]) == 64 for row in rows for field in hash_fields)


def test_protocol_order_privacy_allowlist_and_healer_isolation():
    protocol = crosswalk._diagnostic_protocol()
    assert protocol["classification_order"] == ["infrastructure", "G1", "G3e", "G2", "G3s", "G3a", "G4"]
    assert protocol["allowed_result_fields"] == list(runner.RESULT_FIELDS)
    assert protocol["healer_runtime_input"] is False
    assert protocol["diagnostic_results_may_define_or_trigger_healer_rules"] is False
    forbidden = set(protocol["forbidden_result_fields_or_content"])
    assert {"hidden_input", "expected_value", "actual_value", "exception_message", "assertion_message", "traceback"} <= forbidden
    assert not (set(runner.RESULT_FIELDS) & forbidden)


def test_runner_requires_explicit_execution_and_has_no_default_execution(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    parsed = runner.build_parser().parse_args([
        "--manifest", "m", "--manifest-sha256", "h", "--parallel", "1", "--output-dir", "o",
    ])
    assert parsed.execute_frozen_diagnostics is False
    with pytest.raises(runner.DiagnosticRunnerError, match="explicit"):
        runner.run(tmp_path / "m", "h", tmp_path / "o", 1, False)
    assert not (REPO_ROOT / runner.FROZEN_OUTPUT).exists()


def test_duplicate_missing_and_v3_attachment_hash_drift_fail_closed(tmp_path: Path):
    with pytest.raises(crosswalk.CrosswalkError, match="duplicate identity"):
        crosswalk._index_unique([{"id": "x"}, {"id": "x"}], "id", "fixture")
    bad = tmp_path / "v3.md"
    bad.write_text("drift", encoding="utf-8")
    with pytest.raises(crosswalk.CrosswalkError, match="v3 attachment hash drift"):
        crosswalk.build_analysis(REPO_ROOT, bad)


def test_outputs_are_byte_deterministic_hash_locked_and_pre_execution():
    first = crosswalk.build_outputs(REPO_ROOT, crosswalk.V3_ATTACHMENT)
    second = crosswalk.build_outputs(REPO_ROOT, crosswalk.V3_ATTACHMENT)
    assert first == second
    for relative, content in first.items():
        assert (OUTPUT_DIR / relative).read_bytes() == content
    manifest = json.loads(first[Path("manifest.json")])
    assert manifest["counts"] == {"programs": 300, "L1": 20, "L2": 6, "passed": 76, "pending_review_layer_null": 198, "diagnostic_input_cells": 198}
    assert manifest["diagnostics_output_directory_created"] is False
    assert manifest["diagnostic_executions"] == manifest["evalplus_executions"] == manifest["model_calls"] == 0
    assert manifest["healer_rules_modified"] is False
    assert manifest["validation_not_executed"] is True
    for name, digest in manifest["outputs_sha256_excluding_manifest_and_operator_guide"].items():
        assert hashlib.sha256(first[Path(name)]).hexdigest() == digest
    manifest_sha = hashlib.sha256(first[Path("manifest.json")]).hexdigest()
    guide = first[Path("operator_guide_zh.md")].decode("utf-8")
    assert guide.count("scripts/run_candidate_b_r003_unresolved_diagnostics.py") == 1
    assert re.search(r"--manifest-sha256 ([0-9a-f]{64})", guide).group(1) == manifest_sha
