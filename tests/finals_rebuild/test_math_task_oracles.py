import json
from pathlib import Path

from agent_tools.finals_rebuild.math_task_oracles import evaluate_math_task_oracle


MANIFEST = Path(__file__).parent / "fixtures" / "math_generation_tasks_ce115_pilot.jsonl"


def _tasks():
    return [json.loads(line) for line in MANIFEST.read_text(encoding="utf-8").splitlines() if line]


def test_manifest_is_twelve_immutable_oracle_tasks():
    tasks = _tasks()
    assert len(tasks) == 12 and len({task["task_id"] for task in tasks}) == 12
    assert {task["difficulty_level"] for task in tasks} == {1, 2, 3}
    assert all(task["required_entry_point"] == "generate" and task["seed"] == 20260713 for task in tasks)
    assert all(task["required_output_keys"] == ["question_text", "correct_answer", "oracle_payload"] for task in tasks)
    assert all("model" not in task and "treatment" not in task and "prompt" not in task for task in tasks)
    assert all("oracle_payload" not in task for task in tasks)
    for task in tasks:
        randomization = task["randomization_contract"]
        assert randomization["seeded"] is True
        assert randomization["local_rng_required"] is True
        assert randomization["same_seed_reproducible"] is True
        assert randomization["different_seed_variability_expected"] is True
        assert all(task["k12_constraints"].values())
        for value in task["parameter_ranges"].values():
            if "min" in value:
                assert value["min"] <= value["max"]
    q24 = next(task for task in tasks if task["skill_id"] == "rpm_circumference_to_kph")["parameter_ranges"]["circumference_cm"]
    assert q24["step"] > 0
    assert next(task for task in tasks if task["skill_id"] == "alternating_training_progression_threshold")["parameter_ranges"]["track_length_m"]["allowed_values"]


def test_polynomial_oracle_exact_and_incorrect_cases():
    payload = {"dividend_coefficients": [2, 1, -3], "divisor_root": 1}
    assert evaluate_math_task_oracle("polynomial_division_exact", payload, {"quotient_coefficients": [2, 3], "remainder": 0})["is_correct"]
    assert not evaluate_math_task_oracle("polynomial_division_exact", payload, {"quotient_coefficients": [2, 3], "remainder": 1})["is_correct"]


def test_divisor_oracle_and_invalid_payload():
    payload = {"largest_proper_divisors": {"A": 6, "B": 15}, "claims": [{"subject": "A", "candidate_factor": 2, "asks_necessity": True}, {"subject": "B", "candidate_factor": 4, "asks_necessity": True}]}
    assert evaluate_math_task_oracle("largest_proper_divisor_logic", payload, {"claims": [True, False]})["is_correct"]
    assert not evaluate_math_task_oracle("largest_proper_divisor_logic", payload, {"claims": [False, False]})["is_correct"]
    assert evaluate_math_task_oracle("largest_proper_divisor_logic", {"largest_proper_divisors": {}, "claims": []}, None)["error"]


def test_unit_conversion_oracle_exact_fraction():
    payload = {"circumference_cm": 150, "rpm_symbol": "rpm", "requested_unit": "km/h"}
    assert evaluate_math_task_oracle("rpm_circumference_kph", payload, {"coefficient": "9/100", "unit": "km/h"})["is_correct"]
    assert not evaluate_math_task_oracle("rpm_circumference_kph", payload, {"coefficient": "0.12", "unit": "km/h"})["is_correct"]


def test_sequence_oracle_strict_threshold_and_multipart_answer():
    payload = {"track_length_m": 200, "initial_first_day_laps": 3, "same_week_increment_laps": 1, "threshold_km": 2, "specified_week": 3, "specified_day": "Thursday", "day_labels": ["Monday", "Thursday"]}
    expected = {"specified_session_laps": 6, "first_exceed_week": 8, "first_exceed_day": "Thursday"}
    assert evaluate_math_task_oracle("alternating_sequence_threshold", payload, expected)["is_correct"]
    assert not evaluate_math_task_oracle("alternating_sequence_threshold", payload, {**expected, "first_exceed_day": "Tuesday"})["is_correct"]
