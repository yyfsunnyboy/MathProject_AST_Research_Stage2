"""
Tests for agent_tools/finals_rebuild/pilot_audit.py
"""

from __future__ import annotations

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from agent_tools.finals_rebuild.artifacts import sha256_text
from agent_tools.finals_rebuild.pilot_artifact_loader import (
    FIDELITY_EXTRACTED_ONLY,
    FIDELITY_RAW_RESPONSE,
    SOURCE_FORMAT_GENERATION_ATTEMPTS,
    SOURCE_FORMAT_PUBLIC_BENCHMARK,
    PilotLoadedSample,
)
from agent_tools.finals_rebuild.pilot_audit import (
    REPAIR_PATH_TIER1,
    REPAIR_PATH_TIER1_EXPLORATORY,
    STAGE1_FULL,
    STAGE1_PARTIAL,
    PilotAuditError,
    analyze_extracted_code,
    analyze_raw_response,
    assess_stage1_eligibility,
    audit_sample,
    build_summary,
    classify_taxonomy,
    run_pilot_audit,
)


def _sample(
    *,
    task_id="HumanEval/0",
    treatment="ab1",
    raw_response="def f():\n    return 1\n",
    extracted_code=None,
    entry_point="f",
    source_fidelity=FIDELITY_RAW_RESPONSE,
    source_type=SOURCE_FORMAT_GENERATION_ATTEMPTS,
    skill_id=None,
):
    return PilotLoadedSample(
        source_id=f"{task_id}|{treatment}|0",
        source_type=source_type,
        source_fidelity=source_fidelity,
        dataset="humaneval",
        model_tag=None,
        task_id=task_id,
        treatment=treatment,
        attempt_kind="first_attempt",
        first_attempt_selection_status="only_record",
        raw_response=raw_response,
        extracted_code=extracted_code,
        raw_response_sha256=sha256_text(raw_response) if raw_response else None,
        source_artifact_path="generation_attempts.jsonl",
        source_record_index=1,
        entry_point=entry_point,
        skill_id=skill_id,
    )


def _extracted_sample(**kwargs):
    defaults = {
        "raw_response": None,
        "extracted_code": "def f():\n    return 1\n",
        "source_fidelity": FIDELITY_EXTRACTED_ONLY,
        "source_type": SOURCE_FORMAT_PUBLIC_BENCHMARK,
    }
    defaults.update(kwargs)
    return _sample(**defaults)


def test_ab1_tier1_audit_row():
    row = audit_sample(_sample(treatment="ab1"), repair_path=REPAIR_PATH_TIER1)
    assert row["treatment"] == "ab1"
    assert row["repair_path"] == REPAIR_PATH_TIER1
    assert row["pilot_only"] is True
    assert row["confirmatory_eligible"] is False
    assert row["stage1_mode"] == STAGE1_FULL
    assert row["extraction_replay_available"] is True


def test_ab2g_tier1_audit_row():
    row = audit_sample(_sample(treatment="ab2g"), repair_path=REPAIR_PATH_TIER1)
    assert row["treatment"] == "ab2g"
    assert row["repair_path"] == REPAIR_PATH_TIER1


def test_repair_path_selector_mapping():
    assert audit_sample(_sample(), repair_path=REPAIR_PATH_TIER1)["repair_path_mapping_status"] == "stable"
    exploratory = audit_sample(_sample(), repair_path=REPAIR_PATH_TIER1_EXPLORATORY)
    assert exploratory["repair_path"] == REPAIR_PATH_TIER1_EXPLORATORY
    assert exploratory["repair_path_mapping_status"] == "provisional"


def test_no_trigger_when_no_rule_hits():
    row = audit_sample(_sample(), repair_path=REPAIR_PATH_TIER1)
    assert row["triggered"] is False
    assert row["triggered_rules"] == []


def test_triggered_when_fullwidth_rule_hits():
    code = "def f（x，y）:\n    return x + y\n"
    row = audit_sample(
        _sample(raw_response=f"```python\n{code}```", entry_point="f"),
        repair_path=REPAIR_PATH_TIER1,
    )
    assert row["triggered"] is True
    assert "core.normalize_fullwidth_python_punctuation" in row["triggered_rules"]


def test_changed_false_when_hash_same():
    raw = "def f():\n    return 1\n"
    row = audit_sample(_sample(raw_response=raw), repair_path=REPAIR_PATH_TIER1)
    assert row["before_sha256"] == row["after_sha256"]
    assert row["changed"] is False


def test_changed_true_when_hash_differs():
    raw = "def f（）:\n    return 1\n"
    row = audit_sample(
        _sample(raw_response=raw, entry_point="f"),
        repair_path=REPAIR_PATH_TIER1,
    )
    assert row["before_sha256"] != row["after_sha256"]
    assert row["changed"] is True


def test_empty_response_taxonomy():
    analysis = analyze_raw_response("", entry_point="f")
    assert analysis.taxonomy_primary == "generation_catastrophic"


def test_no_candidate_taxonomy():
    analysis = analyze_raw_response("```python\n```", entry_point="f")
    assert analysis.taxonomy_primary == "no_code_candidate"


def test_ambiguous_taxonomy():
    raw = "```python\nA\n```\n```python\nB\n```"
    analysis = analyze_raw_response(raw, entry_point="f")
    assert analysis.taxonomy_primary == "ambiguous_candidates"


def test_syntax_failure_taxonomy():
    analysis = analyze_raw_response("def broken(:\n    pass\n", entry_point="broken")
    assert analysis.taxonomy_primary == "syntax_or_format"


def test_missing_entry_point_taxonomy():
    analysis = analyze_raw_response("x = 1\n", entry_point="missing_fn")
    assert analysis.taxonomy_primary == "missing_entry_point"


def test_multiple_entry_point_taxonomy():
    raw = "def f():\n    return 1\n\ndef f():\n    return 2\n"
    analysis = analyze_raw_response(raw, entry_point="f")
    assert analysis.taxonomy_primary == "duplicate_or_multiple_entry_point"


def test_parse_success_single_entry_point_taxonomy_none():
    raw = "def f():\n    return 1\n"
    analysis = analyze_raw_response(raw, entry_point="f")
    assert analysis.taxonomy_primary == "none"


def test_exploratory_spec_no_op_on_humaneval():
    before = "def f():\n    return 1\n"
    tier1 = audit_sample(_sample(raw_response=before), repair_path=REPAIR_PATH_TIER1)
    exploratory = audit_sample(
        _sample(raw_response=before),
        repair_path=REPAIR_PATH_TIER1_EXPLORATORY,
    )
    assert exploratory["after_sha256"] == tier1["after_sha256"]
    assert exploratory["triggered"] is False
    spec_traces = [t for t in exploratory["trace"] if t.get("component") == "spec"]
    assert len(spec_traces) == 1
    assert spec_traces[0]["implementation_status"] == "not_applicable"


def test_partial_stage1_extracted_only():
    row = audit_sample(_extracted_sample(), repair_path=REPAIR_PATH_TIER1)
    assert row["stage1_mode"] == STAGE1_PARTIAL
    assert row["extraction_replay_available"] is False
    assert row["raw_response_available"] is False
    assert row["extraction_status_before"] == "not_replayed"


def test_assess_stage1_eligibility():
    eligible, mode, reason = assess_stage1_eligibility(_sample())
    assert eligible is True
    assert mode == STAGE1_FULL
    assert reason is None

    eligible, mode, reason = assess_stage1_eligibility(_extracted_sample())
    assert eligible is True
    assert mode == STAGE1_PARTIAL

    empty = _sample(raw_response=None, extracted_code=None)
    eligible, mode, reason = assess_stage1_eligibility(empty)
    assert eligible is False
    assert reason == "missing_raw_response_and_extracted_code"


def test_extracted_only_taxonomy_not_catastrophic():
    analysis = analyze_extracted_code("def f():\n    return 1\n", entry_point="f")
    assert analysis.taxonomy_primary == "none"


def test_does_not_import_ollama_client():
    import agent_tools.finals_rebuild.pilot_audit as pilot_audit

    text = open(pilot_audit.__file__, encoding="utf-8").read()
    assert "ollama_generation_runner" not in text
    assert "urllib" not in text


def test_summary_full_vs_partial_separation():
    rows = [
        audit_sample(_sample(task_id="HumanEval/0", treatment="ab1"), repair_path=REPAIR_PATH_TIER1),
        audit_sample(_extracted_sample(task_id="HumanEval/1", treatment="ab1"), repair_path=REPAIR_PATH_TIER1),
    ]
    summary = build_summary(rows, source_bundle_id="test_bundle")
    block = summary["by_source_treatment_repair_path"]["test_bundle__ab1__tier1"]
    assert block["N_loaded"] == 2
    assert block["N_full_stage1"] == 1
    assert block["N_partial_stage1"] == 1
    assert block["N_stage1_eligible"] == 2
    for forbidden in ("rescue", "regression", "net_gain", "pass@1"):
        assert forbidden not in block


def test_run_pilot_audit_writes_outputs(tmp_path):
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    raw = "def add(a, b):\n    return a + b\n"
    rec = {
        "task_id": "HumanEval/0",
        "treatment": "ab1",
        "sample_index": 0,
        "status": "success",
        "entry_point": "add",
        "raw_response": raw,
        "raw_response_sha256": sha256_text(raw),
    }
    (artifacts / "generation_attempts.jsonl").write_text(
        json.dumps(rec) + "\n", encoding="utf-8"
    )
    (artifacts / "tasks_selected.jsonl").write_text(
        json.dumps(
            {"task_id": "HumanEval/0", "prompt": "def add(a,b):\n", "entry_point": "add"}
        )
        + "\n",
        encoding="utf-8",
    )

    out = tmp_path / "out"
    result = run_pilot_audit(
        artifacts_root=artifacts,
        output_dir=out,
        treatments=["ab1"],
        repair_paths=["tier1"],
    )
    assert result["unique_samples"] == 1
    assert (out / "sample_results.jsonl").is_file()
    assert (out / "summary.json").is_file()
    sample_row = json.loads((out / "sample_results.jsonl").read_text(encoding="utf-8").strip())
    assert sample_row["source_type"] == SOURCE_FORMAT_GENERATION_ATTEMPTS
    assert sample_row["stage1_eligible"] is True


def test_output_dir_refuses_overwrite_without_flag(tmp_path):
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    raw = "def f():\n    return 1\n"
    (artifacts / "generation_attempts.jsonl").write_text(
        json.dumps(
            {
                "task_id": "HumanEval/0",
                "treatment": "ab1",
                "sample_index": 0,
                "status": "success",
                "raw_response": raw,
                "raw_response_sha256": sha256_text(raw),
            }
        )
        + "\n",
        encoding="utf-8",
    )
    out = tmp_path / "out"
    out.mkdir()
    (out / "existing.txt").write_text("x", encoding="utf-8")
    with pytest.raises(PilotAuditError, match="non-empty"):
        run_pilot_audit(
            artifacts_root=artifacts,
            output_dir=out,
            treatments=["ab1"],
            repair_paths=["tier1"],
            overwrite=False,
        )


def test_classify_taxonomy_precedence():
    assert (
        classify_taxonomy(
            raw_response="",
            extraction_status="empty",
            extracted_code=None,
            parse_status="skipped_no_candidate",
            entry_point_count=0,
            artifact_hints={"infrastructure_failure": True},
        )
        == "infrastructure_failure"
    )
