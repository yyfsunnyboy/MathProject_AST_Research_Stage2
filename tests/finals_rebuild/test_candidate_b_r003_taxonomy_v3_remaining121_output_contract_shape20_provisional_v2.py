from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import pytest

from scripts import (
    adjudicate_candidate_b_r003_taxonomy_v3_remaining121_output_contract_shape20_provisional_v2 as v2,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / v2.OUTPUT_RELATIVE
V1_DIR = REPO_ROOT / v2.V1_DIR


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def materialized() -> Path:
    if OUTPUT_DIR.exists():
        return OUTPUT_DIR
    return v2.write_outputs(REPO_ROOT)


@pytest.mark.parametrize("relative,expected", list(v2.SOURCE_HASHES.items()))
def test_frozen_sources_are_hash_pinned(relative: Path, expected: str):
    path = relative if relative.is_absolute() else REPO_ROOT / relative
    assert _digest(path) == expected


def test_v1_remains_byte_identical(materialized: Path):
    assert _digest(V1_DIR / "manifest.json") == v2.V1_MANIFEST_SHA256
    assert _digest(V1_DIR / "ai_provisional_adjudication.csv") == v2.V1_CSV_SHA256
    assert _digest(V1_DIR / "evidence_citation_audit.csv") == v2.V1_CITATION_SHA256
    assert _digest(V1_DIR / "roster_closure_audit.csv") == v2.V1_CLOSURE_SHA256


def test_exactly_four_cell_field_changes(materialized: Path):
    delta = _rows(materialized / "revision_delta_v1_to_v2.csv")
    assert len(delta) == 4
    assert {row["change_id"] for row in delta} == {
        "H237-44",
        "H237R-44",
        "H237-22",
        "H237R-22",
    }
    assert {row["field"] for row in delta} == {"healer_eligibility", "abstain_reason"}
    assert {row["program_id"] for row in delta} == {
        "70f586aba6f3965fb1463303753ecf4040872364230be73de4b4e51b340b8fb9",
        "af469fe5ae58e9b111c2a5b1d78741fe0dfb9ed0d54b43f939e23ae28c87bcea",
    }


def test_v2_only_changes_mbpp237_healer_fields(materialized: Path):
    v1_rows = {row["program_id"]: row for row in _rows(V1_DIR / "ai_provisional_adjudication.csv")}
    v2_rows = {row["program_id"]: row for row in _rows(materialized / "ai_provisional_adjudication.csv")}
    assert set(v1_rows) == set(v2_rows)
    changed_pids = {
        "70f586aba6f3965fb1463303753ecf4040872364230be73de4b4e51b340b8fb9",
        "af469fe5ae58e9b111c2a5b1d78741fe0dfb9ed0d54b43f939e23ae28c87bcea",
    }
    for program_id, v1 in v1_rows.items():
        v2_row = v2_rows[program_id]
        for field in v2.IMMUTABLE_FIELDS:
            assert v2_row[field] == v1[field]
        if program_id in changed_pids:
            assert v1["healer_eligibility"] == "conditional"
            assert v2_row["healer_eligibility"] == "abstain"
            assert v2_row["abstain_reason"] == v2.MBPP237_ABSTAIN_REASON
            assert v2_row["primary_layer"] == "L5"
        else:
            assert v2_row["healer_eligibility"] == v1["healer_eligibility"]
            assert v2_row["abstain_reason"] == v1["abstain_reason"]


def test_expected_distributions(materialized: Path):
    rows = _rows(materialized / "ai_provisional_adjudication.csv")
    primary = Counter(row["primary_layer"] for row in rows)
    healer = Counter(row["healer_eligibility"] for row in rows)
    confidence = Counter(row["confidence"] for row in rows)
    assert primary == {"UNRESOLVED": 12, "L5": 7, "L2": 1}
    assert healer == {"abstain": 20}
    assert confidence == {"HIGH": 8, "LOW": 12}
    assert all(row["outcome_validity"] == "VALID_MODEL_OUTCOME" for row in rows)
    assert all(json.loads(row["secondary_layers"]) == [] for row in rows)
    assert len({row["task_id"] for row in rows}) == 13
    assert len({row["source_sha256"] for row in rows}) == 20


def test_processed77_intersection_zero(materialized: Path):
    rows = _rows(materialized / "ai_provisional_adjudication.csv")
    processed = v2._processed77(REPO_ROOT)
    assert len(processed) == 77
    assert not ({row["program_id"] for row in rows} & processed)


def test_clarification_does_not_rewrite_preaudit(materialized: Path):
    text = (materialized / "pre_audit_sufficiency_clarification_zh.md").read_text(encoding="utf-8")
    assert "sufficient" in text
    assert "UNRESOLVED" in text
    assert "不得再描述為「相對於 pre-audit **新增 7 格 UNRESOLVED**」" in text or "新增 7 格" in text
    pre_audit = (
        REPO_ROOT
        / "artifacts/public_benchmark_governance/"
        / "candidate_b_r003_taxonomy_v3_remaining121_output_contract_shape20_pre_adjudication_audit_v1"
        / "manifest.json"
    )
    # Pre-audit still present and unchanged relative to post-audit pin path existence.
    assert pre_audit.is_file()


def test_execution_counts_zero(materialized: Path):
    execution = json.loads((materialized / "execution_counts.json").read_text(encoding="utf-8"))
    manifest = json.loads((materialized / "manifest.json").read_text(encoding="utf-8"))
    provenance = json.loads((materialized / "provenance.json").read_text(encoding="utf-8"))
    for doc in (execution, manifest, provenance):
        assert doc["model_calls"] == 0
        assert doc["evalplus_correctness_executions"] == 0
        assert doc["diagnostics_executions"] == 0
        assert doc["healer_executions"] == 0
        assert doc["validation_executions"] == 0
        assert doc["programs_executed"] == 0
    assert execution["candidate_executions"] == 0
    assert manifest["frozen"] is False
    assert manifest["v1_overwritten"] is False
    assert provenance["v1_overwritten"] is False


def test_deterministic_rebuild_bytes_match(materialized: Path):
    rebuilt = v2.build_outputs(REPO_ROOT)
    for relative, data in rebuilt.items():
        assert data == (materialized / relative).read_bytes()


def test_py_compile():
    compile(
        (REPO_ROOT / v2.ANALYZER).read_text(encoding="utf-8"),
        v2.ANALYZER,
        "exec",
    )
