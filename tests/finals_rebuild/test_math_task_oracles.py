import json
from pathlib import Path

from agent_tools.finals_rebuild.math_task_oracles import evaluate_math_task_oracle


MANIFEST = Path(__file__).parent / "fixtures" / "math_generation_tasks_ce115_pilot.jsonl"


def _tasks():
    return [json.loads(line) for line in MANIFEST.read_text(encoding="utf-8").splitlines() if line]


def test_manifest_is_four_immutable_oracle_tasks():
    tasks = _tasks()
    assert [task["task_id"] for task in tasks] == [
        "ce115_q07_polynomial_division", "ce115_q20_largest_proper_divisor",
        "ce115_q24_rotation_speed_conversion", "ce115_cr01_training_sequence_threshold",
    ]
    assert all(task["required_entry_point"] == "generate" and task["seed"] == 20260713 for task in tasks)
    assert all(task["required_output_keys"] == ["question_text", "correct_answer", "oracle_payload"] for task in tasks)
    assert all("model" not in task and "treatment" not in task and "prompt" not in task for task in tasks)


def test_polynomial_oracle_exact_and_incorrect_cases():
    payload = _tasks()[0]["oracle_payload"]
    assert evaluate_math_task_oracle("polynomial_division_exact", payload, {"quotient_coefficients": [4, -11], "remainder": 17})["is_correct"]
    assert not evaluate_math_task_oracle("polynomial_division_exact", payload, {"quotient_coefficients": [4, -11], "remainder": 0})["is_correct"]


def test_divisor_oracle_and_invalid_payload():
    payload = _tasks()[1]["oracle_payload"]
    assert evaluate_math_task_oracle("largest_proper_divisor_logic", payload, {"claims": [False, False]})["is_correct"]
    assert not evaluate_math_task_oracle("largest_proper_divisor_logic", payload, {"claims": [True, False]})["is_correct"]
    assert evaluate_math_task_oracle("largest_proper_divisor_logic", {"largest_proper_divisors": {}, "claims": []}, None)["error"]


def test_unit_conversion_oracle_exact_fraction():
    payload = _tasks()[2]["oracle_payload"]
    assert evaluate_math_task_oracle("rpm_circumference_kph", payload, {"coefficient": "3/25", "unit": "km/h"})["is_correct"]
    assert not evaluate_math_task_oracle("rpm_circumference_kph", payload, {"coefficient": "0.12", "unit": "km/h"})["is_correct"]


def test_sequence_oracle_strict_threshold_and_multipart_answer():
    payload = _tasks()[3]["oracle_payload"]
    expected = {"specified_session_laps": 9, "first_exceed_week": 17, "first_exceed_day": "Thursday"}
    assert evaluate_math_task_oracle("alternating_sequence_threshold", payload, expected)["is_correct"]
    assert not evaluate_math_task_oracle("alternating_sequence_threshold", payload, {**expected, "first_exceed_day": "Tuesday"})["is_correct"]
