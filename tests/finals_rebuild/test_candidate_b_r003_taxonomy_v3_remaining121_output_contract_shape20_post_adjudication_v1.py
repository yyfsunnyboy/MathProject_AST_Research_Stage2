from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pytest

from scripts import (
    audit_candidate_b_r003_taxonomy_v3_remaining121_output_contract_shape20_post_adjudication_v1 as audit,
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


def test_roster_and_processed77(materialized: Path):
    roster = _rows(REPO_ROOT / audit.NEXT_BATCH_ROSTER)
    assert len(roster) == 20
    assert len({row["program_id"] for row in roster}) == 20
    assert len({row["evaluation_source_sha256"] for row in roster}) == 20
    assert len({row["task_id"] for row in roster}) == 13
    processed = audit._processed77(REPO_ROOT)
    assert len(processed) == 77
    assert not ({row["program_id"] for row in roster} & processed)


def test_every_cell_audited_once(materialized: Path):
    rows = _rows(materialized / "post_adjudication_adversarial_audit.csv")
    assert len(rows) == 20
    assert len({row["program_id"] for row in rows}) == 20
    verdicts = {row["cell_audit_verdict"] for row in rows}
    assert verdicts <= {"accept", "change_required"}
    assert sum(row["cell_audit_verdict"] == "accept" for row in rows) == 18
    assert sum(row["cell_audit_verdict"] == "change_required" for row in rows) == 2


def test_unresolved_reconciliation(materialized: Path):
    recon = _rows(materialized / "pre_post_sufficiency_reconciliation.csv")
    unresolved = _rows(materialized / "unresolved12_audit.csv")
    assert len(recon) == 12
    assert len(unresolved) == 12
    assert sum(row["pre_audit_sufficiency"] == "sufficient" for row in unresolved) == 11
    assert sum(row["pre_audit_sufficiency"] == "conditional" for row in unresolved) == 1


def test_mbpp237_requires_abstain(materialized: Path):
    rows = _rows(materialized / "mbpp237_healer_eligibility_audit.csv")
    assert len(rows) == 2
    assert len({row["source_sha256"] for row in rows}) == 2
    assert all(row["recommended_healer"] == "abstain" for row in rows)
    assert all(row["generic_healer_candidate"] == "false" for row in rows)
    assert all(row["audit_verdict"] == "change_required" for row in rows)


def test_mbpp603_accept(materialized: Path):
    rows = _rows(materialized / "mbpp603_contract_audit.csv")
    assert len(rows) == 1
    assert rows[0]["l2_supported"] == "true"
    assert rows[0]["list_wrap_eligible"] == "false"
    assert rows[0]["audit_verdict"] == "accept"


def test_proposed_changes_match_report(materialized: Path):
    changes = _rows(materialized / "proposed_changes.csv")
    text = (materialized / "post_adjudication_adversarial_audit_zh.md").read_text(encoding="utf-8")
    assert len(changes) >= 3
    assert any(row["task_id"] == "Mbpp/237" and row["proposed_value"] == "abstain" for row in changes)
    assert "REVISION_REQUIRED" in text or "REVISION_REQUIRED_BEFORE_FREEZE" in text
    assert str(len(changes)) in text or f"數量：{len(changes)}" in text


def test_provisional_not_modified(materialized: Path):
    assert _digest(REPO_ROOT / audit.PROVISIONAL_CSV) == audit.PROVISIONAL_CSV_SHA256
    assert _digest(REPO_ROOT / audit.PROVISIONAL_MANIFEST) == audit.PROVISIONAL_MANIFEST_SHA256
    provenance = json.loads((materialized / "provenance.json").read_text(encoding="utf-8"))
    assert provenance["provisional_modified"] is False
    assert provenance["freeze_authorized"] is False


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
    assert manifest["audit_verdict"] == "REVISION_REQUIRED_BEFORE_FREEZE"


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
