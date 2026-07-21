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
SCRIPT = ROOT / "scripts" / "adjudicate_candidate_b_r003_taxonomy_v3_remaining171_module_exception_provisional_v1.py"
SPEC = importlib.util.spec_from_file_location("remaining171_module_exception", SCRIPT)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)


def _rows(raw: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(raw.decode("utf-8").splitlines()))


def test_py_compile_and_import_compatible():
    compile(SCRIPT.read_text(encoding="utf-8"), SCRIPT, "exec")
    assert module.TARGET_CELLS == 37
    assert module.STATUS == "AI_ASSISTED_PROVISIONAL_ADJUDICATION_NOT_FORMAL_HUMAN_REVIEW"


def test_frozen_sources_and_census_manifest_sha_verify(monkeypatch):
    module.verify_sources()
    path = next(iter(module.SOURCE_HASHES))
    monkeypatch.setitem(module.SOURCE_HASHES, path, "0" * 64)
    with pytest.raises(module.AdjudicationError, match="hash drift"):
        module.verify_sources()


def test_cluster_selection_roster_closure_and_g2_intersection_zero():
    cluster, roster_by_program, g2_ids = module._load_cluster()
    assert len(cluster) == 37
    assert all(row["operational_cluster"] == module.TARGET_CLUSTER for row in cluster)
    cluster_ids = {row["program_id"] for row in cluster}
    assert cluster_ids <= set(roster_by_program)
    assert not (cluster_ids & g2_ids)
    assert set(module.DECISIONS) == cluster_ids


def test_adjudication_rows_have_required_fields_and_status():
    _roster, adjudication = module.build_rows()
    assert len(adjudication) == 37
    assert {row["adjudication_status"] for row in adjudication} == {module.STATUS}
    for row in adjudication:
        for field in module.ADJUDICATION_FIELDS:
            assert field in row
        assert row["operational_cluster"] == module.TARGET_CLUSTER
        assert row["outcome_validity"] == "VALID_MODEL_OUTCOME"
        assert row["healer_eligibility"] == "abstain"
        json.loads(row["provisional_secondary_layers"])
        json.loads(row["mechanism_tags"])
        json.loads(row["failure_chain"])
        json.loads(row["evidence_source_paths"])


def test_primary_layer_and_summary_counts_sum_to_37():
    outputs = module.build_outputs()
    primary = _rows(outputs[Path("primary_layer_summary.csv")])
    counts = {row["layer"]: int(row["cells"]) for row in primary}
    assert sum(counts.values()) == 37
    assert counts == {"L4": 32, "UNRESOLVED": 5, "L0": 0, "L1": 0, "L2": 0, "L3": 0, "L5": 0}

    secondary = _rows(outputs[Path("secondary_layer_summary.csv")])
    assert all(row["layer"] in module.VALID_SECONDARY_LAYERS for row in secondary)
    assert sum(int(row["cells"]) for row in secondary) == 8

    for summary_name, key in (
        ("outcome_validity_summary.csv", "outcome_validity"),
        ("healer_eligibility_summary.csv", "healer_eligibility"),
        ("confidence_summary.csv", "confidence"),
    ):
        summary = _rows(outputs[Path(summary_name)])
        assert sum(int(row["cells"]) for row in summary) == 37

    crosstab = _rows(outputs[Path("machine_signal_taxonomy_crosstab.csv")])
    assert sum(int(row["cells"]) for row in crosstab) == 37


def test_secondary_layer_schema_is_closed():
    _roster, adjudication = module.build_rows()
    for row in adjudication:
        primary = row["provisional_primary_layer"]
        secondary = json.loads(row["provisional_secondary_layers"])
        assert all(layer in module.VALID_SECONDARY_LAYERS for layer in secondary)
        assert primary not in secondary
        assert "packaging_residue" not in secondary
        assert "UNRESOLVED" not in secondary


def test_pre_freeze_audit_report_present():
    outputs = module.build_outputs()
    audit = _rows(outputs[Path("pre_freeze_adversarial_audit.csv")])
    assert len(audit) >= 10
    assert any(row["check_id"] == "SEC-001" for row in audit)
    assert any(row["check_id"] == "L2-001" for row in audit)
    text = outputs[Path("pre_freeze_adversarial_audit_zh.md")].decode("utf-8")
    assert "REVISION_REQUIRED_BEFORE_FREEZE" in text
    assert "READY_TO_FREEZE_WITHOUT_CHANGE" in text


def test_unresolved_detail_covers_low_confidence_cells():
    outputs = module.build_outputs()
    unresolved = _rows(outputs[Path("unresolved_detail.csv")])
    assert len(unresolved) == 5
    assert {row["provisional_primary_layer"] for row in unresolved} == {"UNRESOLVED"}
    assert all(row["confidence"] == "LOW" for row in unresolved)


def test_execution_manifest_counts():
    execution = json.loads(module.build_outputs()[Path("execution_manifest.json")])
    assert execution["ai_assisted_adjudication_cells"] == 37
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
    provenance = json.loads(outputs[Path("provenance.json")])
    assert provenance["formal_human_adjudication"] is False
    assert provenance["machine_census_manifest_sha256"] == module.MACHINE_CENSUS_MANIFEST_SHA256


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
    assert manifest["cells"] == 37
    assert manifest["machine_census_manifest_sha256"] == module.MACHINE_CENSUS_MANIFEST_SHA256
