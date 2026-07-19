from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path

import pytest

from scripts import prepare_mbpp_candidate_b_r003_h0_h1_evalplus as preparation
from scripts import run_mbpp_candidate_b_r003_evalplus as evaluator


REPO_ROOT = Path(__file__).resolve().parents[2]
FROZEN_DIR = REPO_ROOT / preparation.OUTPUT_RELATIVE


def _csv_rows(value: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(value.decode("utf-8"))))


def _jsonl_rows(value: bytes) -> list[dict[str, object]]:
    return [json.loads(line) for line in value.decode("utf-8").splitlines() if line]


def test_prepare_is_deterministic_and_complete() -> None:
    first = preparation.build_outputs(REPO_ROOT)
    second = preparation.build_outputs(REPO_ROOT)
    assert first == second
    assert hashlib.sha256(first["manifest.json"]).hexdigest() == evaluator.FROZEN_MANIFEST_SHA256
    raw = _csv_rows(first["candidate_b_raw_generation_ledger.csv"])
    accounts = _csv_rows(first["candidate_b_h0_h1_accounts.csv"])
    eval_rows = _jsonl_rows(first["evalplus_input.jsonl"])
    reuse = _csv_rows(first["candidate_b_h1_unchanged_h0_reuse_ledger.csv"])
    manifest = json.loads(first["manifest.json"])

    assert len(raw) == 300
    assert len({row["generation_id"] for row in raw}) == 300
    assert len({(row["task_id"], row["seed"]) for row in raw}) == 300
    assert len({row["task_id"] for row in raw}) == 60
    assert all(row["status"] == "complete_single_attempt" for row in raw)
    assert all(row["retry_count"] == "0" for row in raw)
    assert all(row["resume"] == "False" for row in raw)
    assert len(accounts) == 600
    assert len({row["evaluation_account_id"] for row in accounts}) == 600
    assert len({row["program_id"] for row in accounts}) == 300
    assert len(eval_rows) == 302
    assert sum(row["healer_account"] == "H0" for row in eval_rows) == 300
    assert sum(row["healer_account"] == "H1" for row in eval_rows) == 2
    assert len(reuse) == 298
    assert manifest["model_calls"] == manifest["evalplus_executions"] == 0
    assert manifest["counts"]["factorial_accounts"] == 1200
    assert manifest["h1_status_counts"] == {
        "abstained": 21, "no_trigger": 277, "transformed": 2,
    }


def test_unchanged_h1_is_byte_identical_to_h0() -> None:
    outputs = preparation.build_outputs(REPO_ROOT)
    accounts = _csv_rows(outputs["candidate_b_h0_h1_accounts.csv"])
    by_program: dict[str, dict[str, dict[str, str]]] = {}
    for row in accounts:
        by_program.setdefault(row["program_id"], {})[row["healer_account"]] = row
    for program_id, arms in by_program.items():
        h0 = arms["H0"]
        h1 = arms["H1"]
        assert h0["generation_id"] == h1["generation_id"]
        assert h0["raw_response_sha256"] == h1["raw_response_sha256"]
        assert h0["pipeline_normalized_source_sha256"] == h1["pipeline_normalized_source_sha256"]
        if h1["source_changed_by_healer"] == "false":
            assert h1["evaluation_source_sha256"] == h0["evaluation_source_sha256"]
            assert h1["h1_byte_identical_to_h0"] == "true"
        else:
            assert h1["evaluation_source_sha256"] != h0["evaluation_source_sha256"]
            assert h1["healer_status"] == "transformed"


def test_operator_guide_contains_unique_wsl_command() -> None:
    outputs = preparation.build_outputs(REPO_ROOT)
    guide = outputs["operator_guide_zh.md"].decode("utf-8")
    assert "/home/yehya/.venvs/ast_evalplus/bin/python" in guide
    assert "scripts/run_mbpp_candidate_b_r003_evalplus.py" in guide
    assert evaluator.FROZEN_MANIFEST_SHA256 in guide
    assert "--parallel 1" in guide
    assert "manual_evalplus_run_001" in guide


def test_evalplus_output_directory_absent() -> None:
    assert not (FROZEN_DIR / "manual_evalplus_run_001").exists()
    assert not (REPO_ROOT / preparation.frozen.VALIDATION_RUN_RELATIVE).exists()


def test_validate_frozen_inputs_accepts_only_exact_assets() -> None:
    receipt = evaluator.validate_frozen_inputs(
        manifest_path=FROZEN_DIR / "manifest.json",
        manifest_sha256=evaluator.FROZEN_MANIFEST_SHA256,
        parallel=1,
    )
    manifest, eval_rows = receipt
    assert manifest["status"] == "prepared_not_executed"
    assert len(eval_rows) == 302
    with pytest.raises(evaluator.EvaluationDriverError, match="parallel"):
        evaluator.validate_frozen_inputs(
            manifest_path=FROZEN_DIR / "manifest.json",
            manifest_sha256=evaluator.FROZEN_MANIFEST_SHA256,
            parallel=2,
        )
    with pytest.raises(evaluator.EvaluationDriverError, match="SHA-256"):
        evaluator.validate_frozen_inputs(
            manifest_path=FROZEN_DIR / "manifest.json",
            manifest_sha256="0" * 64,
            parallel=1,
        )


def test_duplicate_task_seed_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    original = preparation._read_csv

    def duplicate(path: Path) -> list[dict[str, str]]:
        rows = original(path)
        if path.name == "candidate_b_generation_cells.csv":
            rows = rows + [dict(rows[0])]
        return rows

    monkeypatch.setattr(preparation, "_read_csv", duplicate)
    with pytest.raises(preparation.PreparationError, match="cell count|duplicate"):
        preparation.validate_and_materialize(REPO_ROOT)


def test_missing_journal_fails_closed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    names = preparation._journal_names(REPO_ROOT / preparation.R003_RUN_RELATIVE / "j")

    def missing(_path: Path) -> list[str]:
        return names[:-1]

    monkeypatch.setattr(preparation, "_journal_names", missing)
    with pytest.raises(preparation.PreparationError, match="journal count|unexpected or missing"):
        preparation.validate_and_materialize(REPO_ROOT)


def test_unexpected_journal_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    names = preparation._journal_names(REPO_ROOT / preparation.R003_RUN_RELATIVE / "j")

    def extra(_path: Path) -> list[str]:
        return names + ["deadbeef" * 8 + ".json"]

    monkeypatch.setattr(preparation, "_journal_names", extra)
    with pytest.raises(preparation.PreparationError, match="journal count|unexpected or missing"):
        preparation.validate_and_materialize(REPO_ROOT)


def test_empty_response_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    original = preparation._load_journal

    def empty(path: Path) -> dict[str, object]:
        journal = original(path)
        journal["raw_response"] = "   "
        return journal

    monkeypatch.setattr(preparation, "_load_journal", empty)
    with pytest.raises(preparation.PreparationError, match="empty raw response|raw response hash"):
        preparation.validate_and_materialize(REPO_ROOT)


def test_retry_or_resume_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    original = preparation._load_journal

    def resumed(path: Path) -> dict[str, object]:
        journal = original(path)
        journal["resume"] = True
        return journal

    monkeypatch.setattr(preparation, "_load_journal", resumed)
    with pytest.raises(preparation.PreparationError, match="resume"):
        preparation.validate_and_materialize(REPO_ROOT)


def test_r001_r002_contamination_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    original = preparation._load_journal
    mapping = list(csv.DictReader((
        REPO_ROOT / preparation.R003_GOVERNANCE_RELATIVE / "r001_r002_r003_identity_mapping.csv"
    ).open(encoding="utf-8")))
    r002_id = mapping[0]["r002_generation_id"]

    def contaminated(path: Path) -> dict[str, object]:
        journal = original(path)
        journal["generation_id"] = r002_id
        return journal

    monkeypatch.setattr(preparation, "_load_journal", contaminated)
    with pytest.raises(preparation.PreparationError, match="generation_id not in freeze|contamination"):
        preparation.validate_and_materialize(REPO_ROOT)


def test_validation_task_contamination_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    original = preparation._forbid_incident_contamination

    def inject(*, generation_ids, task_ids, repo_root):  # type: ignore[no-untyped-def]
        tainted = set(task_ids) | {"HumanEval/0"}
        return original(generation_ids=generation_ids, task_ids=tainted, repo_root=repo_root)

    monkeypatch.setattr(preparation, "_forbid_incident_contamination", inject)
    with pytest.raises(preparation.PreparationError, match="HumanEval|contamination"):
        preparation.validate_and_materialize(REPO_ROOT)


def test_raw_hash_drift_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    original = preparation._load_journal

    def drift(path: Path) -> dict[str, object]:
        journal = original(path)
        journal["raw_response_sha256"] = "0" * 64
        return journal

    monkeypatch.setattr(preparation, "_load_journal", drift)
    with pytest.raises(preparation.PreparationError, match="raw response hash"):
        preparation.validate_and_materialize(REPO_ROOT)


def test_prepare_check_roundtrip() -> None:
    assert preparation.main(["--check"]) == 0


def test_driver_has_no_generation_resume_or_model_path() -> None:
    source = (REPO_ROOT / "scripts/run_mbpp_candidate_b_r003_evalplus.py").read_text(encoding="utf-8")
    assert "run_attempt" not in source
    assert "commands.add_parser(\"resume\")" not in source
    assert "commands.add_parser(\"retry\")" not in source
    assert "ollama" not in source.lower()
