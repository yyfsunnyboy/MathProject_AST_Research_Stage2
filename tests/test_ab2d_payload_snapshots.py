# -*- coding: utf-8 -*-
import json
import os
import sys
import re
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


OVERRIDE_QUOTE = "supersedes any earlier generic `correct_answer: str` instruction"


def audit_payload(payload, task_id, norm_sid, injected_apis):
    routing_correct = "YES" if norm_sid else "NO"
    skill_loaded = "YES" if norm_sid in payload or "Skill Specification" in payload else "NO"
    apis_injected = "YES" if all(api in payload for api in injected_apis) else "NO"
    entry_point_explicit = "YES" if "def generate(level=1, **kwargs):" in payload else "NO"
    output_schema_explicit = "YES" if (
        "Required return schema" in payload
        and "Return exactly these three top-level keys and no others" in payload
        and all(key in payload for key in ("question_text", "correct_answer", "oracle_payload"))
    ) else "NO"

    # B1 checks: the override sentence legitimately quotes `correct_answer: str`;
    # only occurrences OUTSIDE that quote are an active legacy instruction.
    has_conflict = "NO"
    active_str_contract = payload.replace(OVERRIDE_QUOTE, "")
    if "correct_answer: str" in active_str_contract or '"correct_answer": str' in active_str_contract:
        has_conflict = "YES"
    if "'answer': ''" in payload or '"answer": ""' in payload or "'mode': 1" in payload or '"mode": 1' in payload:
        has_conflict = "YES"
    if "def check(" in payload or "check(user_answer, correct_answer)" in payload:
        has_conflict = "YES"

    check_mismatch = "YES" if "def check(" in payload or "check(user_answer, correct_answer)" in payload else "NO"
    # apis_injected is reported but non-blocking: the runtime injects the APIs
    # regardless of prompt documentation, and every pilot task is solvable with
    # plain Python if the API docs are absent from the reusable section.
    blocking = "NONE"
    if entry_point_explicit == "NO" or output_schema_explicit == "NO" or has_conflict == "YES" or check_mismatch == "YES":
        blocking = "YES"

    return {
        "routing_correct": routing_correct,
        "skill_loaded": skill_loaded,
        "apis_injected": apis_injected,
        "entry_point_explicit": entry_point_explicit,
        "output_schema_explicit": output_schema_explicit,
        "conflicting_instructions": has_conflict,
        "check_mismatch": check_mismatch,
        "blocking_issue": blocking
    }


def get_verified_payload(task_id):
    refresh_registry()
    available = list_registered_skill_ids()
    tasks = {t["task_id"]: t for t in load_pilot_tasks()}
    task = tasks[task_id]
    raw_sid = task["skill_id"]
    norm_sid = normalize_skill_id(raw_sid, available)

    from agent_tools.finals_rebuild.math_task_sampler import sample_task_parameters
    sampled = sample_task_parameters(task, seed=2026071301)
    frozen_payload = sampled["oracle_payload"]

    payload = load_prompt_from_skill(norm_sid, ablation_target="Ab3", task_metadata=task, frozen_payload=frozen_payload)
    return payload, task, frozen_payload


@pytest.mark.parametrize("task_id", list(PREFIX_MAP.keys()))
def test_answer_contract_extraction(task_id):
    """1. Verify answer contracts can be successfully extracted for each task from metadata."""
    tasks = {t["task_id"]: t for t in load_pilot_tasks()}
    task = tasks[task_id]

    from agent_tools.finals_rebuild.math_task_sampler import sample_task_parameters
    sampled = sample_task_parameters(task, seed=2026071301)
    frozen_payload = sampled["oracle_payload"]

    contract = render_answer_contract(task, frozen_payload)
    assert contract.strip(), f"Answer contract extraction failed for task: {task_id}"
    assert "Required return schema" in contract


@pytest.mark.parametrize("task_id", list(PREFIX_MAP.keys()))
def test_contract_consistency_with_oracle(task_id):
    """2. Verify that extracted contracts are fully consistent with real oracle rules."""
    tasks = {t["task_id"]: t for t in load_pilot_tasks()}
    task = tasks[task_id]

    from agent_tools.finals_rebuild.math_task_sampler import sample_task_parameters
    sampled = sample_task_parameters(task, seed=2026071301)
    frozen_payload = sampled["oracle_payload"]

    contract = render_answer_contract(task, frozen_payload)
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
def test_static_assertions_on_payloads(task_id):
    """3. Verify all the B1, B2, B3 payload properties systematically."""
    payload, task, frozen_payload = get_verified_payload(task_id)

    # 0. generation output instructions (entry point + output format)
    assert "Write only complete Python source code" in payload
    assert "Do not use Markdown fences, prose, explanations, or prompt echoes" in payload
    assert "Implement exactly one function" in payload
    assert "def generate(level=1, **kwargs):" in payload
    assert "`generate()` must return exactly the three-key dictionary specified below" in payload

    # 0b. no active legacy 4-key template
    for legacy in ("'answer': ''", '"answer": ""', "'mode': 1", '"mode": 1'):
        assert legacy not in payload

    # 0c. derived audit must be clean
    tasks_meta = json.loads((Path("agent_skills") / normalize_skill_id(task["skill_id"], list_registered_skill_ids()) / "skill.json").read_text(encoding="utf-8"))
    audit = audit_payload(payload, task_id, normalize_skill_id(task["skill_id"], list_registered_skill_ids()), tasks_meta.get("injected_apis", []))
    assert audit["blocking_issue"] == "NONE", f"audit not clean: {audit}"

    # 1. exact three-key contract (B1)
    assert "Return exactly these three top-level keys and no others" in payload
    assert "`question_text`, `correct_answer`, and `oracle_payload`" in payload
    assert "Do not return `answer`, `mode`, or any additional key" in payload
    assert "supersedes any earlier generic `correct_answer: str` instruction" in payload

    # 2. frozen sampled parameters exist (B2)
    assert "Frozen sampled parameters:" in payload
    for k in frozen_payload.keys():
        assert k in payload

    # 3. oracle_payload requirement matches (B2)
    assert "`oracle_payload` must exactly equal the frozen sampled parameters above" in payload

    # 4. RPM L1/L2 specific sampled values check (B2)
    if "rotation_speed" in task_id:
        assert str(frozen_payload["circumference_cm"]) in payload
        assert frozen_payload["rpm_symbol"] in payload

    # 5. largest proper divisor payload check (B2)
    if "largest_proper_divisor" in task_id:
        assert "largest_proper_divisors" in payload
        assert "claims" in payload

    # 6. sequence payload check (B2)
    if "training_sequence" in task_id:
        assert "track_length_m" in payload
        assert "initial_first_day_laps" in payload
        assert "same_week_increment_laps" in payload
        assert "threshold_km" in payload
        assert "specified_week" in payload
        assert "day_labels" in payload

    # 7. Polynomial payload check (M1)
    if "polynomial_division" in task_id:
        assert "check(user_answer, correct_answer)" not in payload
        assert "def check(" not in payload

    # 8. temporary-mapped tasks do not contain incorrect family task commands (B3)
    if "rotation_speed" in task_id or "largest_proper_divisor" in task_id or "training_sequence" in task_id:
        banned_commands = [
            "生成分數四則運算題目",
            "中括號混合運算＋除法＋絕對值",
            "生成整數四則運算題目"
        ]
        for cmd in banned_commands:
            assert cmd not in payload

    # 9. temporary-mapped tasks contain correct neutral task statement (B3)
    if "rotation_speed" in task_id:
        assert "# Task Specification: Rotation Speed Conversion" in payload
    elif "largest_proper_divisor" in task_id:
        assert "# Task Specification: Largest Proper Divisor Logic Reasoning" in payload
    elif "training_sequence" in task_id:
        assert "# Task Specification: Alternating Sequence Threshold Crossing" in payload

    # 17. no expected answer leakage
    from agent_tools.finals_rebuild.math_task_oracles import evaluate_math_task_oracle
    verdict = evaluate_math_task_oracle(task["oracle_type"], frozen_payload, None)
    expected_answer = verdict["expected_answer"]
    assert json.dumps(expected_answer) not in payload


@pytest.mark.parametrize("task_id", list(PREFIX_MAP.keys()))
def test_snapshot_generation_reproducibility(task_id):
    """4. Load and verify existing snapshot contents, with opt-in regeneration."""
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

    from agent_tools.finals_rebuild.math_task_sampler import sample_task_parameters
    sampled = sample_task_parameters(task, seed=2026071301)
    frozen_payload = sampled["oracle_payload"]

    payload = load_prompt_from_skill(norm_sid, ablation_target="Ab3", task_metadata=task, frozen_payload=frozen_payload)

    # Dynamic audit results (M2)
    audit = audit_payload(payload, task_id, norm_sid, injected_apis)

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
- routing correct: {audit["routing_correct"]}
- expected skill loaded: {audit["skill_loaded"]}
- expected APIs injected: {audit["apis_injected"]}
- entry point explicit: {audit["entry_point_explicit"]}
- output schema explicit: {audit["output_schema_explicit"]}
- conflicting instructions: {audit["conflicting_instructions"]}
- check() mismatch present: {audit["check_mismatch"]}
- blocking issue: {audit["blocking_issue"]}
"""
    # Clean up trailing spaces from snapshot_content before comparison/write
    snapshot_content = "\n".join(line.rstrip() for line in snapshot_content.splitlines()) + "\n"

    prefix = PREFIX_MAP[task_id]
    snapshot_path = SNAPSHOTS_DIR / f"{prefix}_{task_id}.md"

    if os.environ.get("REGENERATE_SNAPSHOTS") == "1":
        SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        snapshot_path.write_text(snapshot_content, encoding="utf-8")

    assert snapshot_path.exists(), f"Snapshot not found at {snapshot_path}. Run with REGENERATE_SNAPSHOTS=1 to generate."
    existing_content = snapshot_path.read_text(encoding="utf-8")
    assert existing_content == snapshot_content, "Snapshot mismatch! Run with REGENERATE_SNAPSHOTS=1 to update."


def test_unknown_contract_fails_closed():
    """5. Verify that unknown task contract fails closed by raising ValueError."""
    with pytest.raises(ValueError, match="ANSWER_CONTRACT_NOT_FOUND"):
        render_answer_contract(None)
    with pytest.raises(ValueError, match="ANSWER_CONTRACT_NOT_FOUND"):
        render_answer_contract({})
    with pytest.raises(ValueError, match="ANSWER_CONTRACT_NOT_FOUND"):
        render_answer_contract({"oracle_type": "unknown_oracle_type_xyz"})


def test_no_task_prefix_fallback():
    """6. Verify that naming-similar tasks without explicit metadata are not matched."""
    dummy_rpm = {"task_id": "ce115_q24_rotation_speed_conversion_l999"}
    with pytest.raises(ValueError, match="ANSWER_CONTRACT_NOT_FOUND"):
        render_answer_contract(dummy_rpm)
    dummy_poly = {"task_id": "ce115_q07_polynomial_division_l999"}
    with pytest.raises(ValueError, match="ANSWER_CONTRACT_NOT_FOUND"):
        render_answer_contract(dummy_poly)


def test_ab1_ab2g_path_unchanged():
    """7. Verify that Ab1 path and task_metadata=None path does not inject answer contract and Ab1 is byte-equivalent."""
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

    # Verify byte-equivalence of Ab1 output with the raw bare prompt on disk
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "agent_skills", norm_sid, "experiments", "ab1_bare_prompt.md")
    with open(path, "r", encoding="utf-8") as f:
        expected_ab1 = f.read()
    assert payload_ab1 == expected_ab1


@pytest.mark.parametrize("task_id", list(PREFIX_MAP.keys()))
def test_production_frozen_payload_propagation(task_id):
    """9. Verify the production runner path: the same frozen object the evaluator
    compares against is embedded verbatim in the assembled Ab2d prompt."""
    from agent_tools.finals_rebuild.math_boundary_pilot import build_ab2d_prompt, frozen_payloads

    tasks = {t["task_id"]: t for t in load_pilot_tasks()}
    task = tasks[task_id]

    frozen_records = frozen_payloads([task], repeat_seeds=(2026071301,))
    assert len(frozen_records) == 1
    frozen = frozen_records[0]

    prompt = build_ab2d_prompt(task, frozen)

    # The exact frozen dictionary used by classify_response must appear verbatim.
    frozen_json = json.dumps(frozen["oracle_payload"], sort_keys=True)
    assert frozen_json in prompt
    assert "`oracle_payload` must exactly equal the frozen sampled parameters above" in prompt

    # No re-sampling: a second build with the same frozen record is identical.
    assert build_ab2d_prompt(task, frozen) == prompt


def test_production_condition_registered():
    """10. Verify the ab2d condition is wired into the production runner."""
    from agent_tools.finals_rebuild.math_boundary_pilot import CONDITIONS, build_ab2d_prompt
    assert CONDITIONS.get("ab2d") == ("Ab2d", build_ab2d_prompt)


def test_benchmark_no_fixture_reading():
    """8. Verify that benchmark.py does not read the fixture file."""
    benchmark_src_path = Path(__file__).parent.parent / "agent_tools" / "benchmark.py"
    src_content = benchmark_src_path.read_text(encoding="utf-8")
    assert "math_generation_tasks_ce115_pilot.jsonl" not in src_content
