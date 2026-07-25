from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

import scripts.build_deterministic_healer_candidate_inventory_4b9b_v1 as build


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / build.OUTPUT_DIR


def load_ledger() -> list[dict[str, str]]:
    with (OUTPUT / "candidate_ledger.csv").open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_deterministic_rebuild_matches_outputs() -> None:
    expected = build.build_outputs(ROOT)
    assert {path.name for path in OUTPUT.iterdir() if path.is_file()} == set(expected)
    assert all((OUTPUT / name).read_bytes() == data for name, data in expected.items())


def test_complete_unique_error_cohort_and_required_schema() -> None:
    rows = load_ledger()
    assert len(rows) == 372
    assert Counter(row["model"] for row in rows) == {
        "qwen3.5:4b": 148,
        "qwen3.5:9b": 224,
    }
    assert len({(row["model"], row["cell_id"]) for row in rows}) == 372
    assert list(rows[0]) == build.LEDGER_FIELDS
    assert all(len(row["source_sha256"]) == 64 for row in rows)


def test_only_one_rule_is_recommended_and_guards_are_exact() -> None:
    summary = json.loads((OUTPUT / "summary.json").read_text("utf-8"))
    recommendation = summary["recommendation"]
    assert recommendation["candidate_rule"] == (
        "top_level_literal_only_demo_print_quarantine_v0"
    )
    assert recommendation["tasks"] == ["Mbpp/138", "Mbpp/787"]
    assert len(recommendation["candidate_cells"]) == 2
    assert summary["priority_findings"]["2_unique_missing_stdlib_import"] == (
        "0 eligible cells"
    )
    assert summary["zero_execution"] == {
        "EvalPlus_executions": 0,
        "H1_modifications": 0,
        "H2_modifications": 0,
        "candidate_executions": 0,
        "candidate_imports": 0,
        "canonical_solutions_viewed": 0,
        "hidden_tests_viewed": 0,
        "model_calls": 0,
        "rule_implementations": 0,
    }


def test_h1_h2_and_ambiguous_entrypoint_are_not_new_candidates() -> None:
    rows = load_ledger()
    assert not any(
        row["candidate_rule"] == "insert_unique_standard_library_import_v0"
        and row["eligibility"] == "eligible_candidate"
        for row in rows
    )
    ambiguous = [
        row
        for row in rows
        if row["task_id"] == "Mbpp/765"
        and row["program_id"]
        == "eb81f9452bdd4c5d2fece536388915e81997f4d4cde7b0a748cf4bc90075be2d"
    ]
    assert len(ambiguous) == 1
    assert ambiguous[0]["mechanism"] == "entry_point_mismatch_ambiguous"
    assert ambiguous[0]["eligibility"] == "abstain"
    assert all(
        row["eligibility"] != "eligible_candidate"
        for row in rows
        if row["candidate_rule"]
        in {
            "entrypoint_alias_unique_arity_compatible_v0",
            "module_assert_entrypoint_selftest_quarantine_v0",
        }
    )
