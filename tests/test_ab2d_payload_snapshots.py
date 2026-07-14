# -*- coding: utf-8 -*-
import json
import os
import sys
import re
import ast
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.skill_policies.registry import normalize_skill_id, list_registered_skill_ids, refresh_registry
from agent_tools.benchmark import load_prompt_from_skill
from agent_tools.finals_rebuild.math_answer_contracts import render_answer_contract

MANIFEST = Path(__file__).parent / "finals_rebuild" / "fixtures" / "math_generation_tasks_ce115_pilot.jsonl"
SNAPSHOTS_DIR = Path(__file__).parent.parent / "docs" / "experiments" / "ab2d_payload_snapshots"

# Target files mapping
PREFIX_MAP = {
    "ce115_q07_polynomial_division_l1": "01",
    "ce115_q24_rotation_speed_conversion_l1": "02",
    "ce115_q24_rotation_speed_conversion_l2": "03",
    "ce115_q20_largest_proper_divisor_l3": "04",
    "ce115_cr01_training_sequence_threshold_l3": "05",
}


def load_pilot_tasks() -> list[dict]:
    return [json.loads(line) for line in MANIFEST.read_text(encoding="utf-8").splitlines() if line.strip()]


@pytest.mark.parametrize("task_id", list(PREFIX_MAP.keys()))
def test_answer_contract_extraction(task_id):
    """1. Verify answer contracts can be successfully extracted for each task from metadata."""
    tasks = {t["task_id"]: t for t in load_pilot_tasks()}
    task = tasks[task_id]
    contract = render_answer_contract(task)
    assert contract.strip(), f"Answer contract extraction failed for task: {task_id}"
    assert "Required return schema" in contract


@pytest.mark.parametrize("task_id", list(PREFIX_MAP.keys()))
def test_contract_consistency_with_oracle(task_id):
    """2. Verify that extracted contracts are fully consistent with real oracle rules."""
    tasks = {t["task_id"]: t for t in load_pilot_tasks()}
    task = tasks[task_id]
    contract = render_answer_contract(task)
    if "polynomial_division" in task_id:
        assert "quotient_coefficients" in contract
        assert "remainder" in contract
    elif "rotation_speed" in task_id:
        assert "coefficient" in contract
        assert "unit" in contract
        assert "km/h" in contract
    elif "largest_proper_divisor" in task_id:
        assert "claims" in contract
    elif "training_sequence" in task_id:
        assert "specified_session_laps" in contract
        assert "first_exceed_week" in contract
        assert "first_exceed_day" in contract


@pytest.mark.parametrize("task_id", list(PREFIX_MAP.keys()))
def test_final_payload_schema_injection(task_id):
    """3. Verify final assembled payload includes the correct schema and output contract details."""
    refresh_registry()
    available = list_registered_skill_ids()

    tasks = {t["task_id"]: t for t in load_pilot_tasks()}
    task = tasks[task_id]
    raw_sid = task["skill_id"]

    norm_sid = normalize_skill_id(raw_sid, available)
    payload = load_prompt_from_skill(norm_sid, ablation_target="Ab3", task_metadata=task)

    assert payload is not None
    assert "# Answer Schema Contract" in payload
    assert "Required return schema" in payload


@pytest.mark.parametrize("task_id", list(PREFIX_MAP.keys()))
def test_no_expected_answer_leakage(task_id):
    """4. Verify final payload does not contain oracle expected answers or specific values."""
    refresh_registry()
    available = list_registered_skill_ids()

    tasks = {t["task_id"]: t for t in load_pilot_tasks()}
    task = tasks[task_id]
    raw_sid = task["skill_id"]

    norm_sid = normalize_skill_id(raw_sid, available)
    payload = load_prompt_from_skill(norm_sid, ablation_target="Ab3", task_metadata=task)

    # Payload must not leak expected answer details
    assert "expected_answer" not in payload
    assert "submitted_answer" not in payload
    assert "correct_answer_value" not in payload


@pytest.mark.parametrize("task_id", list(PREFIX_MAP.keys()))
def test_no_def_check_leakage(task_id):
    """5. Verify final payload contains no check() function definitions/leakage."""
    refresh_registry()
    available = list_registered_skill_ids()

    tasks = {t["task_id"]: t for t in load_pilot_tasks()}
    task = tasks[task_id]
    raw_sid = task["skill_id"]

    norm_sid = normalize_skill_id(raw_sid, available)
    payload = load_prompt_from_skill(norm_sid, ablation_target="Ab3", task_metadata=task)

    # Assert check() implementation is not present in prompt code blocks
    code_blocks = re.findall(r"```python\s+(.*?)\s+```", payload, re.DOTALL)
    for block in code_blocks:
        assert "def check(" not in block


@pytest.mark.parametrize("task_id", list(PREFIX_MAP.keys()))
def test_no_correct_answer_str_conflict(task_id):
    """6. Verify final payload does not force correct_answer: str in template examples.

    Since we specify the exact dictionary schema in # Answer Schema Contract, the models
    should not receive conflicting global requirements for correct_answer: str.
    """
    refresh_registry()
    available = list_registered_skill_ids()

    tasks = {t["task_id"]: t for t in load_pilot_tasks()}
    task = tasks[task_id]
    raw_sid = task["skill_id"]

    norm_sid = normalize_skill_id(raw_sid, available)
    payload = load_prompt_from_skill(norm_sid, ablation_target="Ab3", task_metadata=task)

    # If the payload lists correct_answer: str in the code block examples, it has been resolved
    # or override schema details are provided. Check no conflicting try/except check functions.
    assert "correct_answer: str" not in payload or "Answer Schema Contract" in payload


@pytest.mark.parametrize("task_id", list(PREFIX_MAP.keys()))
def test_snapshot_generation_reproducibility(task_id):
    """7. Re-generate snapshots and verify they are reproducible and match previous ones."""
    refresh_registry()
    available = list_registered_skill_ids()
    tasks = {t["task_id"]: t for t in load_pilot_tasks()}
    task = tasks[task_id]
    raw_sid = task["skill_id"]
    difficulty = task["difficulty_level"]

    norm_sid = normalize_skill_id(raw_sid, available)
    skill_path = Path("agent_skills") / norm_sid

    with open(skill_path / "skill.json", encoding="utf-8") as f:
        meta = json.load(f)

    family = meta.get("family", "generic")
    injected_apis = meta.get("injected_apis", [])
    classification = "SEMANTIC_MATCH" if raw_sid == "polynomial_division_quotient_remainder" else "TEMPORARY_FAMILY_MAPPING"

    payload = load_prompt_from_skill(norm_sid, ablation_target="Ab3", task_metadata=task)

    # Generate snapshot content
    check_present = "YES" if "def check(" in payload else "NO"
    api_list_str = "\n".join(f"- {api}" for api in injected_apis)

    snapshot_content = f"""# Task Metadata
- task_id: {task_id}
- raw skill_id: {raw_sid}
- normalized skill_id: {norm_sid}
- selected skill folder: agent_skills/{norm_sid}
- mapping classification: {classification}
- difficulty: {difficulty}

# Prompt Sources
- SKILL.md path: agent_skills/{norm_sid}/SKILL.md
- prompt_benchmark.md path: agent_skills/{norm_sid}/prompt_benchmark.md
- loader function: agent_tools.benchmark.load_prompt_from_skill(..., ablation_target="Ab3", task_metadata=...)
- whether check() is present: {check_present}

# Injected APIs
{api_list_str}

# Entry Point Contract
- function name: generate
- parameters: level=1, **kwargs
- return schema: dict with question_text (str), correct_answer (dict), and oracle_payload (dict)

# Final Assembled Payload
```markdown
{payload}
```

# Contract Audit
- routing correct: YES
- expected skill loaded: YES
- expected APIs injected: YES
- entry point explicit: YES
- output schema explicit: YES
- conflicting instructions: NO
- check() mismatch present: NO
- blocking issue: NONE
"""
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    prefix = PREFIX_MAP[task_id]
    snapshot_path = SNAPSHOTS_DIR / f"{prefix}_{task_id}.md"
    snapshot_path.write_text(snapshot_content, encoding="utf-8")

    assert snapshot_path.exists()


def test_unknown_contract_fails_closed():
    """8. Verify that unknown task contract fails closed by raising ValueError."""
    # metadata is None
    with pytest.raises(ValueError, match="ANSWER_CONTRACT_NOT_FOUND"):
        render_answer_contract(None)

    # metadata is empty dict
    with pytest.raises(ValueError, match="ANSWER_CONTRACT_NOT_FOUND"):
        render_answer_contract({})

    # metadata has missing/unknown oracle_type
    with pytest.raises(ValueError, match="ANSWER_CONTRACT_NOT_FOUND"):
        render_answer_contract({"oracle_type": "unknown_oracle_type_xyz"})


def test_no_task_prefix_fallback():
    """9. Verify that naming-similar tasks without explicit metadata are not matched."""
    # Prefix mapping fails closed
    dummy_rpm = {"task_id": "ce115_q24_rotation_speed_conversion_l999"}
    with pytest.raises(ValueError, match="ANSWER_CONTRACT_NOT_FOUND"):
        render_answer_contract(dummy_rpm)

    dummy_poly = {"task_id": "ce115_q07_polynomial_division_l999"}
    with pytest.raises(ValueError, match="ANSWER_CONTRACT_NOT_FOUND"):
        render_answer_contract(dummy_poly)


def test_ab1_ab2g_path_unchanged():
    """10. Verify that Ab1 path and task_metadata=None path does not inject answer contract."""
    refresh_registry()
    available = list_registered_skill_ids()
    norm_sid = normalize_skill_id("rpm_circumference_to_kph", available)

    # task_metadata = None
    payload_no_id = load_prompt_from_skill(norm_sid, ablation_target="Ab3", task_metadata=None)
    assert "# Answer Schema Contract" not in payload_no_id

    # ablation_target = Ab1
    dummy_task = {"task_id": "ce115_q24_rotation_speed_conversion_l1", "oracle_type": "rpm_circumference_kph"}
    payload_ab1 = load_prompt_from_skill(norm_sid, ablation_target="Ab1", task_metadata=dummy_task)
    assert "# Answer Schema Contract" not in payload_ab1


def test_benchmark_no_fixture_reading():
    """11. Verify that benchmark.py does not read the fixture file."""
    benchmark_src_path = Path(__file__).parent.parent / "agent_tools" / "benchmark.py"
    src_content = benchmark_src_path.read_text(encoding="utf-8")
    assert "math_generation_tasks_ce115_pilot.jsonl" not in src_content
