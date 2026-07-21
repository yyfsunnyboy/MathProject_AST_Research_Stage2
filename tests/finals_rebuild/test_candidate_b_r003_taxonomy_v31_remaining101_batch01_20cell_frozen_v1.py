from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import pytest

from scripts import (
    freeze_candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_v1 as freezer,
)
from scripts import (
    adjudicate_candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_provisional_v2 as provisional_v2,
)


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


def test_upstream_revisions_byte_stable(materialized):
    assert _digest(REPO_ROOT / freezer.V1_RECORDS) == freezer.V1_RECORDS_SHA256
    assert _digest(REPO_ROOT / freezer.V1_ROSTER) == freezer.V1_ROSTER_SHA256
    assert _digest(REPO_ROOT / freezer.V1_MANIFEST) == freezer.V1_MANIFEST_SHA256
    assert _digest(REPO_ROOT / freezer.V2_RECORDS) == freezer.V2_RECORDS_SHA256
    assert _digest(REPO_ROOT / freezer.V2_ROSTER) == freezer.V2_ROSTER_SHA256
    assert _digest(REPO_ROOT / freezer.V2_MANIFEST) == freezer.V2_MANIFEST_SHA256
    assert _digest(REPO_ROOT / freezer.AUDIT_MANIFEST) == freezer.AUDIT_MANIFEST_SHA256
    assert _digest(REPO_ROOT / freezer.REAUDIT_MANIFEST) == freezer.REAUDIT_MANIFEST_SHA256
    assert _digest(REPO_ROOT / freezer.NEXT20) == freezer.NEXT20_SHA256
    assert _digest(REPO_ROOT / freezer.REMAINING101) == freezer.REMAINING101_SHA256
    assert _digest(REPO_ROOT / freezer.CENSUS_MANIFEST) == freezer.CENSUS_MANIFEST_SHA256
    assert _digest(REPO_ROOT / freezer.PRIOR_PROGRESS_MANIFEST) == freezer.PRIOR_PROGRESS_MANIFEST_SHA256


def test_frozen_payload_matches_provisional_v2_bytes(materialized):
    freeze_dir, _progress = materialized
    frozen = _rows(freeze_dir / "frozen_adjudication.csv")
    projected = [{field: row[field] for field in provisional_v2.RECORD_FIELDS} for row in frozen]
    projected_bytes = freezer._csv_bytes(provisional_v2.RECORD_FIELDS, projected)
    assert projected_bytes == (REPO_ROOT / freezer.V2_RECORDS).read_bytes()
    assert _digest(freeze_dir / "frozen_unresolved_evidence_gaps.csv") == freezer.V2_GAPS_SHA256
    assert _digest(freeze_dir / "frozen_roster.csv") == freezer.V2_ROSTER_SHA256


def test_identity_closure_and_statistics(materialized):
    freeze_dir, progress_dir = materialized
    frozen = _rows(freeze_dir / "frozen_adjudication.csv")
    next20 = _rows(REPO_ROOT / freezer.NEXT20)
    assert len(frozen) == 20
    assert [row["program_id"] for row in frozen] == [row["program_id"] for row in next20]
    assert len({row["program_id"] for row in frozen}) == 20
    assert len({row["source_sha256"] for row in frozen}) == 20
    primary = Counter(row["primary_layer"] for row in frozen)
    healer = Counter(row["healer_eligibility"] for row in frozen)
    confidence = Counter(row["confidence"] for row in frozen)
    outcome = Counter(row["outcome_validity"] for row in frozen)
    secondary = Counter(row["secondary_layer"] or "(empty)" for row in frozen)
    assert primary == {"L5": 9, "UNRESOLVED": 11}
    assert healer == {"abstain": 20}
    assert confidence == {"HIGH": 9, "LOW": 11}
    assert outcome == {"VALID_MODEL_OUTCOME": 20}
    assert secondary == {"(empty)": 20}
    assert primary.get("L2", 0) == 0
    for row in frozen:
        assert row["freeze_status"] == freezer.STATUS
        assert row["freeze_basis_verdict"] == freezer.FREEZE_BASIS_VERDICT
        assert row["frozen_from_revision"] == freezer.V2_DIR.name

    freeze_manifest = json.loads((freeze_dir / "manifest.json").read_text(encoding="utf-8"))
    progress_manifest = json.loads((progress_dir / "manifest.json").read_text(encoding="utf-8"))
    assert freeze_manifest["freeze_basis_verdict"] == freezer.FREEZE_BASIS_VERDICT
    assert freeze_manifest["newly_frozen"] == 20
    assert freeze_manifest["previously_frozen"] == 97
    assert freeze_manifest["total_frozen"] == 117
    assert freeze_manifest["remaining"] == 81
    assert freeze_manifest["no_new_adjudication"] is True
    assert progress_manifest["total_frozen"] == 117
    assert progress_manifest["remaining"] == 81
    assert progress_manifest["overwrites_prior_census"] is False
    assert progress_manifest["next_batch_started"] is False
    assert progress_manifest["batch01_roster_sha256"] == freezer.NEXT20_SHA256


def test_execution_counts_zero(materialized):
    freeze_dir, progress_dir = materialized
    for directory in (freeze_dir, progress_dir):
        execution = json.loads((directory / "execution_counts.json").read_text(encoding="utf-8"))
        for key in (
            "model_calls",
            "candidate_executions",
            "candidate_imports",
            "public_test_executions",
            "hidden_test_executions",
            "evalplus_correctness_executions",
            "diagnostics_executions",
            "validation_executions",
            "healer_executions",
            "programs_executed",
        ):
            assert execution[key] == 0
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


def test_manifest_provenance_closure(materialized):
    freeze_dir, progress_dir = materialized
    freeze_manifest = json.loads((freeze_dir / "manifest.json").read_text(encoding="utf-8"))
    provenance = json.loads((freeze_dir / "provenance.json").read_text(encoding="utf-8"))
    progress_prov = json.loads((progress_dir / "provenance.json").read_text(encoding="utf-8"))
    assert freeze_manifest["provisional_v2_records_sha256"] == freezer.V2_RECORDS_SHA256
    assert freeze_manifest["reaudit_v2_manifest_sha256"] == freezer.REAUDIT_MANIFEST_SHA256
    assert provenance["freeze_basis_verdict"] == freezer.FREEZE_BASIS_VERDICT
    assert provenance["taxonomy_v31_reference_sha256"] == "93908ec8e4721f0039acc779fb948988b6c25e712c29890bd98aa7c21a8422a0"
    assert provenance["audit_v1_manifest_sha256"] == freezer.AUDIT_MANIFEST_SHA256
    assert provenance["provisional_v1_records_sha256"] == freezer.V1_RECORDS_SHA256
    assert provenance["no_model_or_candidate_execution"] is True
    assert progress_prov["immutable_new_revision"] is True
    outputs = freeze_manifest["outputs_sha256_excluding_manifest"]
    for name, digest in outputs.items():
        assert _digest(freeze_dir / name) == digest


def test_py_compile():
    compile(
        (REPO_ROOT / freezer.ANALYZER).read_text(encoding="utf-8"),
        freezer.ANALYZER,
        "exec",
    )
