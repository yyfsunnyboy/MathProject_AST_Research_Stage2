from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import pytest

from scripts import (
    audit_candidate_b_r003_taxonomy_v3_remaining121_output_contract_shape20_pre_adjudication_v1 as audit,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / audit.OUTPUT_RELATIVE


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def materialized() -> Path:
    if OUTPUT_DIR.exists():
        return OUTPUT_DIR
    return audit.write_outputs(REPO_ROOT)


@pytest.mark.parametrize("relative,expected", list(audit.SOURCE_HASHES.items()))
def test_frozen_sources_are_hash_pinned(relative: Path, expected: str):
    path = relative if relative.is_absolute() else REPO_ROOT / relative
    assert _digest(path) == expected


def test_fixed_roster_closure(materialized: Path):
    roster = _rows(REPO_ROOT / audit.NEXT_BATCH_ROSTER)
    assert len(roster) == audit.TARGET_CELLS
    assert len({row["program_id"] for row in roster}) == audit.TARGET_CELLS
    assert len({row["evaluation_source_sha256"] for row in roster}) == audit.TARGET_UNIQUE_SOURCES
    assert len({row["task_id"] for row in roster}) == audit.TARGET_UNIQUE_TASKS
    assert _digest(REPO_ROOT / audit.NEXT_BATCH_ROSTER) == audit.NEXT_BATCH_ROSTER_SHA256


def test_processed77_intersection_zero(materialized: Path):
    roster_ids = {row["program_id"] for row in _rows(REPO_ROOT / audit.NEXT_BATCH_ROSTER)}
    processed = audit._processed77(REPO_ROOT)
    assert len(processed) == 77
    assert not (roster_ids & processed)


def test_audit_has_20_rows_and_no_formal_adjudication(materialized: Path):
    audit_rows = _rows(materialized / "pre_adjudication_adversarial_audit.csv")
    assert len(audit_rows) == 20
    assert not (materialized / "ai_provisional_adjudication.csv").exists()
    manifest = json.loads((materialized / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["formal_adjudication_emitted"] is False


def test_evidence_sufficiency_distribution(materialized: Path):
    audit_rows = _rows(materialized / "pre_adjudication_adversarial_audit.csv")
    counter = Counter(row["evidence_sufficiency"] for row in audit_rows)
    assert counter.get("insufficient", 0) == 0
    assert counter.get("conditional", 0) + counter.get("sufficient", 0) == 20


def test_return_type_coverage(materialized: Path):
    audit_rows = _rows(materialized / "pre_adjudication_adversarial_audit.csv")
    assert audit.EXPECTED_RETURN_TYPES <= {row["return_type_bucket"] for row in audit_rows}


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
    assert execution["candidate_executions"] == 0
    assert execution["programs_executed"] == 0


def test_proposed_protocol_mentions_required_fields(materialized: Path):
    text = (materialized / "proposed_adjudication_protocol_zh.md").read_text(encoding="utf-8")
    for field in audit.PROTOCOL_ADJUDICATION_FIELDS:
        assert f"`{field}`" in text
    assert audit.ADJUDICATION_STATUS in text


def test_deterministic_rebuild_bytes_match(materialized: Path):
    rebuilt = audit.build_outputs(REPO_ROOT)
    for relative, data in rebuilt.items():
        assert data == (materialized / relative).read_bytes()


def test_py_compile():
    compile(
        (REPO_ROOT / audit.ANALYZER).read_text(encoding="utf-8"),
        audit.ANALYZER,
        "exec",
    )


def test_audit_verdict_ready(materialized: Path):
    provenance = json.loads((materialized / "provenance.json").read_text(encoding="utf-8"))
    assert provenance["audit_verdict"] == "READY_FOR_20_CELL_AI_ASSISTED_PROVISIONAL_ADJUDICATION"
