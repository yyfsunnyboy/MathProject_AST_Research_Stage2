"""Snapshot and boundary tests for the isolated Ab2d-local treatment."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from agent_tools.finals_rebuild.ab2d_local_prompt import (
    CORE_SCAFFOLD,
    TASK_LOCAL_PRIMITIVES,
    assemble_ab2d_local_prompt,
    measure_prompt_size,
)
from agent_tools.finals_rebuild.math_answer_contracts import render_answer_contract
from agent_tools.finals_rebuild.math_boundary_pilot import build_ab2d_prompt
from agent_tools.finals_rebuild.math_task_sampler import sample_task_parameters


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tests/finals_rebuild/fixtures/math_generation_tasks_ce115_pilot.jsonl"
SNAPSHOTS = ROOT / "tests/fixtures/ab2d_local_prompt_snapshots.json"
FAMILIES = tuple(TASK_LOCAL_PRIMITIVES)
SEED = 20260714


def _tasks() -> dict[str, dict]:
    rows = [json.loads(line) for line in MANIFEST.read_text(encoding="utf-8").splitlines() if line]
    return {row["skill_id"]: row for row in rows if row["skill_id"] in FAMILIES and row["difficulty_level"] == 1}


def _parts(family: str) -> tuple[dict, dict, str]:
    task = _tasks()[family]
    frozen = sample_task_parameters(task, SEED)["oracle_payload"]
    return task, frozen, render_answer_contract(task, frozen)


def test_snapshots_are_byte_deterministic_and_cover_each_family() -> None:
    snapshots = {row["task_family"]: row for row in json.loads(SNAPSHOTS.read_text(encoding="utf-8"))}
    assert set(snapshots) == set(FAMILIES)
    for family in FAMILIES:
        _, frozen, contract = _parts(family)
        prompt = assemble_ab2d_local_prompt(family, contract, frozen)
        assert prompt == assemble_ab2d_local_prompt(family, contract, frozen)
        assert hashlib.sha256(prompt.encode("utf-8")).hexdigest() == snapshots[family]["sha256"]
        assert prompt.encode("utf-8").decode("utf-8") == prompt


def test_prompt_contains_only_required_sections_and_local_primitive() -> None:
    excluded_full_domain_terms = ("Family Catalogue", "Sub-skill Graph", "Generator Priority", "LiveShow", "F1", "F13", "I1", "I8")
    for family in FAMILIES:
        _, frozen, contract = _parts(family)
        prompt = assemble_ab2d_local_prompt(family, contract, frozen)
        assert CORE_SCAFFOLD in prompt
        assert TASK_LOCAL_PRIMITIVES[family] in prompt
        assert contract.strip() in prompt
        assert json.dumps(frozen, ensure_ascii=False, sort_keys=True) in prompt
        assert not any(term in prompt for term in excluded_full_domain_terms)
    polynomial, frozen, contract = _parts("polynomial_division_quotient_remainder")
    assert "PolynomialOps.div_qr" in assemble_ab2d_local_prompt(polynomial["skill_id"], contract, frozen)
    rpm, frozen, contract = _parts("rpm_circumference_to_kph")
    assert "fractions.Fraction" in assemble_ab2d_local_prompt(rpm["skill_id"], contract, frozen)


def test_local_prompt_is_less_than_half_of_existing_ab2d_full_prompt() -> None:
    for family in FAMILIES:
        task, frozen, contract = _parts(family)
        local = assemble_ab2d_local_prompt(family, contract, frozen)
        full = build_ab2d_prompt(task, {"oracle_payload": frozen})
        local_size, full_size = measure_prompt_size(local), measure_prompt_size(full)
        assert local_size["character_count"] < full_size["character_count"] / 2
        assert local_size["utf8_byte_count"] < full_size["utf8_byte_count"] / 2


def test_measurement_and_unknown_family_fail_closed() -> None:
    assert measure_prompt_size("one two\n三") == {"character_count": 9, "utf8_byte_count": 11, "approx_wordpiece_count": 3}
    with pytest.raises(ValueError, match="unsupported Ab2d-local task family"):
        assemble_ab2d_local_prompt("unknown", "contract", {})
