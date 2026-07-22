from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import pytest

from scripts import freeze_candidate_b_r003_taxonomy_v31_batch02_20cell_v1 as freezer


REPO_ROOT = Path(__file__).resolve().parents[2]
FREEZE_DIR = REPO_ROOT / freezer.FREEZE_OUTPUT
PROGRESS_DIR = REPO_ROOT / freezer.PROGRESS_OUTPUT


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def materialized() -> tuple[Path, Path]:
    if FREEZE_DIR.exists() and PROGRESS_DIR.exists():
        return FREEZE_DIR, PROGRESS_DIR
    return freezer.write_outputs(REPO_ROOT)


@pytest.mark.parametrize("relative,expected", list(freezer.SOURCE_HASHES.items()))
def test_frozen_sources_hash_pinned(relative: Path, expected: str):
    path = relative if relative.is_absolute() else REPO_ROOT / relative
    assert _digest(path) == expected


def test_upstream_frozen117_and_v2_chain_byte_stable(materialized):
    assert _digest(REPO_ROOT / freezer.BATCH01_FROZEN_RECORDS) == freezer.BATCH01_FROZEN_RECORDS_SHA256
    assert _digest(REPO_ROOT / freezer.BATCH01_FROZEN_MANIFEST) == freezer.BATCH01_FROZEN_MANIFEST_SHA256
    assert _digest(REPO_ROOT / freezer.PROGRESS_V2_MANIFEST) == freezer.PROGRESS_V2_MANIFEST_SHA256
    assert _digest(REPO_ROOT / freezer.V2_RECORDS) == freezer.V2_RECORDS_SHA256
    assert _digest(REPO_ROOT / freezer.V2_MANIFEST) == freezer.V2_MANIFEST_SHA256
    assert _digest(REPO_ROOT / freezer.REAUDIT_MANIFEST) == freezer.REAUDIT_MANIFEST_SHA256
    assert _digest(REPO_ROOT / freezer.REAUDIT_FINDINGS) == freezer.REAUDIT_FINDINGS_SHA256
    assert _digest(REPO_ROOT / freezer.ROSTER) == freezer.ROSTER_SHA256
    assert _digest(REPO_ROOT / freezer.V1_RECORDS) == freezer.V1_RECORDS_SHA256
    assert _digest(REPO_ROOT / freezer.AUDIT_MANIFEST) == freezer.AUDIT_MANIFEST_SHA256


def test_frozen_records_byte_identical_to_v2(materialized):
    freeze_dir, _progress = materialized
    frozen = freeze_dir / "frozen_adjudication.csv"
    assert frozen.read_bytes() == (REPO_ROOT / freezer.V2_RECORDS).read_bytes()
    assert _digest(frozen) == freezer.V2_RECORDS_SHA256
    assert _digest(freeze_dir / "frozen_roster.csv") == freezer.V2_ROSTER_SHA256
    assert _digest(freeze_dir / "frozen_unresolved_evidence_gaps.csv") == freezer.V2_GAPS_SHA256


def test_identity_statistics_and_progress_closure(materialized):
    freeze_dir, progress_dir = materialized
    frozen = _rows(freeze_dir / "frozen_adjudication.csv")
    roster = _rows(REPO_ROOT / freezer.ROSTER)
    batch01 = _rows(REPO_ROOT / freezer.BATCH01_FROZEN_RECORDS)
    assert len(frozen) == 20
    assert [row["program_id"] for row in frozen] == [row["program_id"] for row in roster]
    assert [row["cell_identity_sha256"] for row in frozen] == [row["cell_identity_sha256"] for row in roster]
    assert [row["source_sha256"] for row in frozen] == [row["source_sha256"] for row in roster]
    assert len({row["program_id"] for row in frozen}) == 20
    assert len({row["cell_identity_sha256"] for row in frozen}) == 20
    assert len({row["source_sha256"] for row in frozen}) == 19
    assert not ({row["program_id"] for row in frozen} & {row["program_id"] for row in batch01})

    primary = Counter(row["primary_layer"] for row in frozen)
    secondary = Counter(row["secondary_layer"] or "empty" for row in frozen)
    confidence = Counter(row["confidence"] for row in frozen)
    outcome = Counter(row["outcome_validity"] for row in frozen)
    healer = Counter(row["healer_eligibility"] for row in frozen)
    assert primary == {"L2": 3, "L4": 1, "L5": 5, "UNRESOLVED": 11}
    assert secondary == {"L5": 4, "empty": 16}
    assert confidence == {"HIGH": 7, "MEDIUM": 2, "LOW": 11}
    assert outcome == {"VALID_MODEL_OUTCOME": 20}
    assert healer == {"abstain": 20}

    freeze_manifest = json.loads((freeze_dir / "manifest.json").read_text(encoding="utf-8"))
    progress_manifest = json.loads((progress_dir / "manifest.json").read_text(encoding="utf-8"))
    assert freeze_manifest["freeze_basis_verdict"] == freezer.FREEZE_BASIS_VERDICT
    assert freeze_manifest["newly_frozen"] == 20
    assert freeze_manifest["previously_frozen"] == 117
    assert freeze_manifest["total_frozen"] == 137
    assert freeze_manifest["remaining"] == 61
    assert freeze_manifest["unauthorized_adjudication_differences"] == 0
    assert freeze_manifest["remaining61_roster_created"] is False
    assert freeze_manifest["batch03_started"] is False
    assert progress_manifest["total_frozen"] == 137
    assert progress_manifest["remaining"] == 61
    assert progress_manifest["overwrites_prior_census"] is False
    assert progress_manifest["batch03_started"] is False
    assert freezer.FORMAL_POPULATION == 137 + 61
    assert freezer.REMAINING81_CELLS - 20 == 61


def test_execution_counts_zero(materialized):
    freeze_dir, progress_dir = materialized
    for directory in (freeze_dir, progress_dir):
        execution = json.loads((directory / "execution_counts.json").read_text(encoding="utf-8"))
        assert all(value == 0 for value in execution.values())
        manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        for key in (
            "model_calls",
            "candidate_executions",
            "evalplus_correctness_executions",
            "diagnostics_executions",
            "validation_executions",
            "healer_executions",
            "programs_executed",
        ):
            assert manifest[key] == 0


def test_deterministic_rebuild(materialized):
    freeze_dir, progress_dir = materialized
    rebuilt = freezer.build_outputs(REPO_ROOT)
    for relative, data in rebuilt["freeze"].items():
        assert data == (freeze_dir / relative).read_bytes()
    for relative, data in rebuilt["progress"].items():
        assert data == (progress_dir / relative).read_bytes()


def test_manifest_provenance_and_sha_ledger(materialized):
    freeze_dir, _progress = materialized
    freeze_manifest = json.loads((freeze_dir / "manifest.json").read_text(encoding="utf-8"))
    provenance = json.loads((freeze_dir / "provenance.json").read_text(encoding="utf-8"))
    ledger = json.loads((freeze_dir / "sha_ledger.json").read_text(encoding="utf-8"))
    assert freeze_manifest["provisional_v2_records_sha256"] == freezer.V2_RECORDS_SHA256
    assert freeze_manifest["reaudit_manifest_sha256"] == freezer.REAUDIT_MANIFEST_SHA256
    assert freeze_manifest["frozen_records_byte_identical_to_v2"] is True
    assert provenance["provenance_chain"] == [
        "roster",
        "provisional_v1",
        "audit",
        "provisional_v2",
        "reaudit",
        "frozen",
    ]
    assert ledger["roster_sha256"] == freezer.ROSTER_SHA256
    assert ledger["provisional_v2_records_sha256"] == freezer.V2_RECORDS_SHA256
    assert ledger["reaudit_findings_sha256"] == freezer.REAUDIT_FINDINGS_SHA256
    for name, digest in freeze_manifest["outputs_sha256_excluding_manifest"].items():
        assert _digest(freeze_dir / name) == digest


def test_py_compile():
    compile(
        (REPO_ROOT / freezer.ANALYZER).read_text(encoding="utf-8"),
        freezer.ANALYZER,
        "exec",
    )
