"""Regression coverage for Gemini diagnostic response classification."""
from __future__ import annotations

import json
from pathlib import Path

from agent_tools.finals_rebuild.math_boundary_pilot import classify_response


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "docs/experiments/results/gemini_ab1_ab2d_l1_seed_20260714_diagnostic.jsonl"
FAMILY = "alternating_training_progression_threshold"
TASK = {"skill_id": FAMILY, "oracle_type": "alternating_sequence_threshold"}


def _frozen() -> dict:
    return {
        "oracle_payload": {
            "day_labels": ["Monday", "Thursday"],
            "initial_first_day_laps": 7,
            "same_week_increment_laps": 1,
            "specified_day": "Thursday",
            "specified_week": 3,
            "threshold_km": 5,
            "track_length_m": 400,
        }
    }


def _valid_source() -> str:
    return '''def generate(level=1, **kwargs):
    return {
        "question_text": "Training schedule.",
        "correct_answer": {
            "specified_session_laps": 10,
            "first_exceed_week": 6,
            "first_exceed_day": "Thursday",
        },
        "oracle_payload": {
            "day_labels": ["Monday", "Thursday"],
            "initial_first_day_laps": 7,
            "same_week_increment_laps": 1,
            "specified_day": "Thursday",
            "specified_week": 3,
            "threshold_km": 5,
            "track_length_m": 400,
        },
    }
'''


def test_frozen_alternating_raw_outputs_are_not_false_parse_minor() -> None:
    rows = [json.loads(line) for line in RESULT.read_text(encoding="utf-8").splitlines() if line]
    alternating = [row for row in rows if row["task_family"] == FAMILY]
    assert {row["prompt_condition"] for row in alternating} == {"Ab1", "Ab2d"}
    for row in alternating:
        outcome, candidate, details = classify_response(row["raw_first_attempt_output"], _frozen(), TASK)
        assert outcome == "extraction_failure"
        assert candidate is None
        assert details["extraction_status"] == "no_generate_source"


def test_pure_python_source_is_unchanged_and_evaluable() -> None:
    source = _valid_source()
    outcome, candidate, _ = classify_response(source, _frozen(), TASK)
    assert outcome == "passed"
    assert candidate == source.strip()


def test_fenced_python_source_is_evaluable() -> None:
    source = _valid_source()
    outcome, candidate, _ = classify_response(f"```python\n{source}```", _frozen(), TASK)
    assert outcome == "passed"
    assert candidate == source


def test_valid_module_import_prelude_is_preserved_for_generate() -> None:
    source = "import math\n\n" + _valid_source()
    outcome, candidate, _ = classify_response(source, _frozen(), TASK)
    assert outcome == "passed"
    assert candidate == source.strip()


def test_leading_prose_is_removed_only_before_generate_source() -> None:
    source = _valid_source()
    outcome, candidate, _ = classify_response(f"Here is the generator:\n\n{source}", _frozen(), TASK)
    assert outcome == "passed"
    assert candidate == source.strip()


def test_prose_only_does_not_become_candidate_source() -> None:
    outcome, candidate, details = classify_response("Here is an explanation without code.", _frozen(), TASK)
    assert outcome == "extraction_failure"
    assert candidate is None
    assert details["extraction_status"] == "no_generate_source"
