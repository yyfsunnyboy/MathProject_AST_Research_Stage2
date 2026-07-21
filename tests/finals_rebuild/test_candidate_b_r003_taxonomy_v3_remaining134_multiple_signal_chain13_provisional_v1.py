from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "adjudicate_candidate_b_r003_taxonomy_v3_remaining134_multiple_signal_chain13_provisional_v1.py"
SPEC = importlib.util.spec_from_file_location("remaining134_multiple_signal_chain13", SCRIPT)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)


def _rows(raw: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(raw.decode("utf-8").splitlines()))


def test_py_compile_and_import_compatible():
    compile(SCRIPT.read_text(encoding="utf-8"), SCRIPT, "exec")
    assert module.TARGET_CELLS == 13
    assert module.TARGET_CLUSTER == "multiple_signal_chain"
    assert module.STATUS == "AI_ASSISTED_PROVISIONAL_ADJUDICATION_NOT_FORMAL_HUMAN_REVIEW"


def test_frozen_sources_and_census_manifest_sha_verify(monkeypatch):
    module.verify_sources()
    path = next(iter(module.SOURCE_HASHES))
    monkeypatch.setitem(module.SOURCE_HASHES, path, "0" * 64)
    with pytest.raises(module.AdjudicationError, match="hash drift"):
        module.verify_sources()


def test_cluster_selection_roster_closure_and_intersections_zero():
    cluster, roster_by_program, g2_ids, module_exception_ids = module._load_cluster()
    assert len(cluster) == 13
    assert all(row["operational_cluster"] == module.TARGET_CLUSTER for row in cluster)
    cluster_ids = {row["program_id"] for row in cluster}
    assert cluster_ids <= set(roster_by_program)
    assert not (cluster_ids & g2_ids)
    assert not (cluster_ids & module_exception_ids)
    assert set(module.DECISIONS) == cluster_ids


def test_adjudication_rows_have_required_fields_and_status():
    _roster, adjudication = module.build_rows()
    assert len(adjudication) == 13
    assert {row["adjudication_status"] for row in adjudication} == {module.STATUS}
    for row in adjudication:
        for field in module.ADJUDICATION_FIELDS:
            assert field in row
        assert row["operational_cluster"] == module.TARGET_CLUSTER
        assert row["outcome_validity"] == "VALID_MODEL_OUTCOME"
        assert row["healer_eligibility"] == "abstain"
        assert row["confidence"] in {"HIGH", "MEDIUM", "LOW"}
        assert row["ambiguity_status"] in {"UNAMBIGUOUS", "UNRESOLVED"}
        assert int(row["ambiguity_count"]) >= 0
        json.loads(row["provisional_secondary_layers"])
        json.loads(row["mechanism_tags"])
        json.loads(row["failure_chain"])
        json.loads(row["evidence_source_paths"])
        json.loads(row["all_observed_machine_signals"])


def test_roster_rows_have_required_fields():
    roster, _adjudication = module.build_rows()
    assert len(roster) == 13
    for row in roster:
        for field in module.ROSTER_FIELDS:
            assert field in row
        assert row["dataset"] == "MBPP+"
        assert row["condition"] == "Candidate_B/H0"
        json.loads(row["frozen_machine_signals"])


def test_primary_layer_and_summary_counts_sum_to_13():
    outputs = module.build_outputs()
    primary = _rows(outputs[Path("primary_layer_summary.csv")])
    counts = {row["layer"]: int(row["cells"]) for row in primary}
    assert sum(counts.values()) == 13
    assert counts == {"L4": 11, "L5": 1, "UNRESOLVED": 1, "L0": 0, "L1": 0, "L2": 0, "L3": 0}

    secondary = _rows(outputs[Path("secondary_layer_summary.csv")])
    assert all(row["layer"] in module.VALID_SECONDARY_LAYERS for row in secondary)
    assert sum(int(row["cells"]) for row in secondary) == 5
    assert {row["layer"] for row in secondary if int(row["cells"]) > 0} == {"L5"}

    for summary_name, _key in (
        ("outcome_validity_summary.csv", "outcome_validity"),
        ("healer_eligibility_summary.csv", "healer_eligibility"),
        ("confidence_summary.csv", "confidence"),
    ):
        summary = _rows(outputs[Path(summary_name)])
        assert sum(int(row["cells"]) for row in summary) == 13

    crosstab = _rows(outputs[Path("machine_signal_taxonomy_crosstab.csv")])
    assert sum(int(row["cells"]) for row in crosstab) == 13


def test_secondary_layer_schema_is_closed():
    _roster, adjudication = module.build_rows()
    for row in adjudication:
        primary = row["provisional_primary_layer"]
        secondary = json.loads(row["provisional_secondary_layers"])
        assert all(layer in module.VALID_SECONDARY_LAYERS for layer in secondary)
        assert primary not in secondary
        assert "packaging_residue" not in secondary
        assert "UNRESOLVED" not in secondary


def test_healer_candidate_detail_one_row_per_cell_abstain_rule_family_empty():
    outputs = module.build_outputs()
    detail = _rows(outputs[Path("healer_candidate_detail.csv")])
    assert len(detail) == 13
    for row in detail:
        for field in module.HEALER_CANDIDATE_DETAIL_FIELDS:
            assert field in row
        assert row["healer_eligibility"] == "abstain"
        assert row["proposed_rule_family"] == ""
        assert row["counterexample_notes"]


def test_unresolved_detail_covers_low_confidence_cells():
    outputs = module.build_outputs()
    unresolved = _rows(outputs[Path("unresolved_detail.csv")])
    assert len(unresolved) == 1
    assert {row["provisional_primary_layer"] for row in unresolved} == {"UNRESOLVED"}
    assert all(row["confidence"] == "LOW" for row in unresolved)


def test_confidence_distribution():
    _roster, adjudication = module.build_rows()
    assert Counter(row["confidence"] for row in adjudication) == Counter({"HIGH": 12, "LOW": 1})


def test_module_execution_exception_mechanism_count():
    _roster, adjudication = module.build_rows()
    count = sum(
        1 for row in adjudication
        if "module_execution_exception" in json.loads(row["mechanism_tags"])
    )
    assert count == 11


def test_filter_data_cells_l4_primary_l5_secondary_and_failure_chain():
    _roster, adjudication = module.build_rows()
    by_pid = {row["program_id"]: row for row in adjudication}
    for pid in module.FILTER_DATA_PIDS:
        row = by_pid[pid]
        assert row["provisional_primary_layer"] == "L4"
        secondary = json.loads(row["provisional_secondary_layers"])
        assert "L5" in secondary
        mechanisms = json.loads(row["mechanism_tags"])
        assert "unbound_name_stats" in mechanisms
        chain = json.loads(row["failure_chain"])
        assert len(chain) >= 2
        assert chain[0]["stage"] == "causal_mechanism"
        assert chain[-1]["mechanism"] == "strict_inequality_boundary"


def test_pre_freeze_audit_report_present():
    outputs = module.build_outputs()
    audit = _rows(outputs[Path("pre_freeze_adversarial_audit.csv")])
    assert len(audit) >= 10
    check_ids = {row["check_id"] for row in audit}
    assert "PROV-722" in check_ids
    assert "SEC-EMPTY" in check_ids
    assert "MECH-POLICY" in check_ids
    assert "HEAL-ALL" in check_ids
    assert "OUT-VALID" in check_ids
    assert any(row["check_id"] == "MBPP125-001" for row in audit)
    assert any(row["check_id"] == "L5-XOR" for row in audit)
    text = outputs[Path("pre_freeze_adversarial_audit_zh.md")].decode("utf-8")
    assert "REVISION_REQUIRED_BEFORE_FREEZE" in text
    assert "READY_TO_FREEZE_WITHOUT_CHANGE" in text
    assert module.STATUS in text
    assert "ALL_SECONDARY_CONFIRMED_WITH_L5_ON_722" in text


def test_execution_manifest_counts():
    execution = json.loads(module.build_outputs()[Path("execution_manifest.json")])
    assert execution["ai_assisted_adjudication_cells"] == 13
    assert execution["model_calls"] == 0
    assert execution["evalplus_correctness_executions"] == 0
    assert execution["diagnostics_executions"] == 0
    assert execution["healer_executions"] == 0
    assert execution["validation_executions"] == 0
    assert execution["programs_executed"] == 0
    assert execution["status"] == module.STATUS


def test_docs_state_nonformal_status():
    outputs = module.build_outputs()
    for doc in ("methodology_report_zh.md", "adjudication_protocol_zh.md"):
        text = outputs[Path(doc)].decode("utf-8")
        assert module.STATUS in text
    protocol = outputs[Path("adjudication_protocol_zh.md")].decode("utf-8")
    assert "module_execution_exception" in protocol
    provenance = json.loads(outputs[Path("provenance.json")])
    assert provenance["formal_human_adjudication"] is False
    assert provenance["machine_census_manifest_sha256"] == module.MACHINE_CENSUS_MANIFEST_SHA256
    assert provenance["module_exception_manifest_sha256"] == module.MODULE_EXCEPTION_MANIFEST_SHA256


def test_manifest_hashes_and_deterministic_bytes():
    first = module.build_outputs()
    second = module.build_outputs()
    assert first == second
    for data in first.values():
        text = data.decode("utf-8")
        assert all(line == line.rstrip() for line in text.splitlines())
    manifest = json.loads(first[Path("manifest.json")])
    for name, digest in manifest["outputs_sha256_excluding_manifest"].items():
        assert hashlib.sha256(first[Path(name)]).hexdigest() == digest
    assert manifest["cells"] == 13
    assert manifest["machine_census_manifest_sha256"] == module.MACHINE_CENSUS_MANIFEST_SHA256
    assert manifest["primary_layer_counts"] == {"L4": 11, "L5": 1, "UNRESOLVED": 1}
