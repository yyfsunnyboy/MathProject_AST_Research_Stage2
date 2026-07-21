from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import pytest

from scripts import (
    freeze_candidate_b_r003_taxonomy_v3_remaining121_output_contract_shape20_v1 as freezer,
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


def test_upstream_revisions_unmodified(materialized):
    assert _digest(REPO_ROOT / freezer.V1_MANIFEST) == freezer.V1_MANIFEST_SHA256
    assert _digest(REPO_ROOT / freezer.V1_CSV) == freezer.V1_CSV_SHA256
    assert _digest(REPO_ROOT / freezer.V2_MANIFEST) == freezer.V2_MANIFEST_SHA256
    assert _digest(REPO_ROOT / freezer.V2_CSV) == freezer.V2_CSV_SHA256
    assert _digest(REPO_ROOT / freezer.FINAL_AUDIT_MANIFEST) == freezer.FINAL_AUDIT_MANIFEST_SHA256


def test_frozen_roster_matches_v2(materialized):
    freeze_dir, _progress = materialized
    frozen = _rows(freeze_dir / "frozen_adjudication.csv")
    v2 = _rows(REPO_ROOT / freezer.V2_CSV)
    assert len(frozen) == 20
    assert [row["program_id"] for row in frozen] == [row["program_id"] for row in v2]
    for f_row, v_row in zip(frozen, v2, strict=True):
        assert f_row["primary_layer"] == v_row["primary_layer"]
        assert f_row["healer_eligibility"] == v_row["healer_eligibility"]
        assert f_row["outcome_validity"] == v_row["outcome_validity"]
        assert f_row["confidence"] == v_row["confidence"]
        assert f_row["source_sha256"] == v_row["source_sha256"]
        assert f_row["freeze_status"] == freezer.STATUS


def test_statistics_and_progress(materialized):
    freeze_dir, progress_dir = materialized
    frozen = _rows(freeze_dir / "frozen_adjudication.csv")
    primary = Counter(row["primary_layer"] for row in frozen)
    healer = Counter(row["healer_eligibility"] for row in frozen)
    assert primary == {"UNRESOLVED": 12, "L5": 7, "L2": 1}
    assert healer == {"abstain": 20}
    freeze_manifest = json.loads((freeze_dir / "manifest.json").read_text(encoding="utf-8"))
    progress_manifest = json.loads((progress_dir / "manifest.json").read_text(encoding="utf-8"))
    assert freeze_manifest["total_frozen"] == 97
    assert freeze_manifest["remaining"] == 101
    assert freeze_manifest["newly_frozen"] == 20
    assert freeze_manifest["previously_frozen"] == 77
    assert progress_manifest["total_frozen"] == 97
    assert progress_manifest["remaining"] == 101
    assert progress_manifest["overwrites_prior_census"] is False


def test_processed77_intersection_zero(materialized):
    freeze_dir, _progress = materialized
    frozen_ids = {row["program_id"] for row in _rows(freeze_dir / "frozen_adjudication.csv")}
    processed = freezer._processed77(REPO_ROOT)
    assert len(processed) == 77
    assert not (frozen_ids & processed)


def test_execution_counts_zero(materialized):
    freeze_dir, progress_dir = materialized
    for directory in (freeze_dir, progress_dir):
        execution = json.loads((directory / "execution_counts.json").read_text(encoding="utf-8"))
        for key in (
            "model_calls",
            "candidate_executions",
            "evalplus_correctness_executions",
            "diagnostics_executions",
            "validation_executions",
            "healer_executions",
            "programs_executed",
        ):
            assert execution[key] == 0


def test_deterministic_rebuild(materialized):
    freeze_dir, progress_dir = materialized
    rebuilt = freezer.build_outputs(REPO_ROOT)
    for relative, data in rebuilt["freeze"].items():
        assert data == (freeze_dir / relative).read_bytes()
    for relative, data in rebuilt["progress"].items():
        assert data == (progress_dir / relative).read_bytes()


def test_py_compile():
    compile(
        (REPO_ROOT / freezer.ANALYZER).read_text(encoding="utf-8"),
        freezer.ANALYZER,
        "exec",
    )
