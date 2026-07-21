from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import pytest

from scripts import (
    adjudicate_candidate_b_r003_taxonomy_v3_remaining121_output_contract_shape20_provisional_v1 as adj,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / adj.OUTPUT_RELATIVE


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def materialized() -> Path:
    if OUTPUT_DIR.exists():
        return OUTPUT_DIR
    return adj.write_outputs(REPO_ROOT)


@pytest.mark.parametrize("relative,expected", list(adj.SOURCE_HASHES.items()))
def test_frozen_sources_are_hash_pinned(relative: Path, expected: str):
    path = relative if relative.is_absolute() else REPO_ROOT / relative
    assert _digest(path) == expected


def test_fixed_roster_and_processed77_intersection(materialized: Path):
    roster = _rows(REPO_ROOT / adj.NEXT_BATCH_ROSTER)
    assert len(roster) == adj.TARGET_CELLS
    assert len({row["program_id"] for row in roster}) == adj.TARGET_CELLS
    assert len({row["evaluation_source_sha256"] for row in roster}) == adj.TARGET_UNIQUE_SOURCES
    assert len({row["task_id"] for row in roster}) == adj.TARGET_UNIQUE_TASKS
    assert _digest(REPO_ROOT / adj.NEXT_BATCH_ROSTER) == adj.NEXT_BATCH_ROSTER_SHA256
    processed = adj._processed77(REPO_ROOT)
    assert len(processed) == 77
    assert not ({row["program_id"] for row in roster} & processed)


def test_adjudication_rows_complete(materialized: Path):
    rows = _rows(materialized / "ai_provisional_adjudication.csv")
    assert len(rows) == 20
    for row in rows:
        for field in adj.ADJUDICATION_FIELDS:
            assert field in row
        assert row["adjudication_status"] == adj.STATUS
        assert row["observed_machine_signal"] == adj.TARGET_CLUSTER
        assert row["primary_layer"] in adj.VALID_PRIMARY_LAYERS
        assert row["outcome_validity"] == "VALID_MODEL_OUTCOME"
        assert row["healer_eligibility"] in adj.VALID_HEALER
        assert row["confidence"] in adj.VALID_CONFIDENCE
        chain = json.loads(row["failure_chain"])
        assert isinstance(chain, list) and len(chain) >= 2
        assert json.loads(row["secondary_layers"]) is not None
        assert json.loads(row["mechanism_tags"]) is not None
        assert json.loads(row["allowed_evidence"])
        assert json.loads(row["evidence_citations"])
        assert row["source_sha256"] in row["adjudication_identity"]
        if row["primary_layer"] == "UNRESOLVED":
            assert row["healer_eligibility"] == "abstain"
            assert row["abstain_reason"]


def test_roster_closure_audit(materialized: Path):
    closure = _rows(materialized / "roster_closure_audit.csv")
    assert len(closure) == 20
    assert all(row["in_fixed_roster"] == "true" for row in closure)
    assert all(row["in_processed77"] == "false" for row in closure)
    assert all(row["source_sha_verified"] == "true" for row in closure)


def test_evidence_citation_audit_traceable(materialized: Path):
    citations = _rows(materialized / "evidence_citation_audit.csv")
    assert len(citations) == 80  # 20 cells * 4 citations
    kinds = {row["citation_kind"] for row in citations}
    assert kinds == {"public_prompt", "candidate_source", "machine_census", "fixed_roster"}


def test_summary_distributions(materialized: Path):
    summary = json.loads((materialized / "adjudication_summary.json").read_text(encoding="utf-8"))
    rows = _rows(materialized / "ai_provisional_adjudication.csv")
    primary = Counter(row["primary_layer"] for row in rows)
    assert summary["primary_layer_distribution"] == dict(sorted(primary.items()))
    assert summary["cells"] == 20
    assert summary["unique_task_id"] == 13
    assert summary["unique_source_sha256"] == 20
    assert summary["ai_assisted_adjudication_cells"] == 20
    assert summary["unresolved_cells"] == primary.get("UNRESOLVED", 0)


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
        assert doc["ai_assisted_adjudication_cells"] == 20
    assert execution["candidate_executions"] == 0
    assert manifest["frozen"] is False


def test_decisions_cover_exact_roster():
    roster_ids = {row["program_id"] for row in _rows(REPO_ROOT / adj.NEXT_BATCH_ROSTER)}
    assert set(adj.DECISIONS) == roster_ids


def test_deterministic_rebuild_bytes_match(materialized: Path):
    rebuilt = adj.build_outputs(REPO_ROOT)
    for relative, data in rebuilt.items():
        assert data == (materialized / relative).read_bytes()


def test_py_compile():
    compile(
        (REPO_ROOT / adj.ANALYZER).read_text(encoding="utf-8"),
        adj.ANALYZER,
        "exec",
    )
