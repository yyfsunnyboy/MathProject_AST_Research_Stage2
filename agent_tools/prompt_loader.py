"""Dependency-light reusable skill prompt loader for production evaluation paths."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_prompt_from_skill(skill_name: str, ablation_target: str = "Ab3", task_metadata: dict[str, Any] | None = None,
                           frozen_payload: dict[str, Any] | None = None) -> str | None:
    path = (PROJECT_ROOT / "agent_skills" / skill_name / "experiments" / "ab1_bare_prompt.md"
            if ablation_target == "Ab1" else PROJECT_ROOT / "agent_skills" / skill_name / "SKILL.md")
    if not path.is_file():
        return None
    full_text = path.read_text(encoding="utf-8")
    if ablation_target == "Ab1" or path.name != "SKILL.md":
        return full_text
    if task_metadata is not None:
        reusable = [match.group(1).strip() for match in re.finditer(r"=== REUSABLE_START ===(.*?)=== REUSABLE_END ===", full_text, re.DOTALL)]
        base_rules = "\n\n".join(reusable) if reusable else full_text.split("=== SKILL_END_PROMPT ===")[0]
        from agent_tools.finals_rebuild.math_answer_contracts import render_answer_contract
        return f"{base_rules}\n{render_answer_contract(task_metadata, frozen_payload)}"
    base_rules = full_text.split("=== SKILL_END_PROMPT ===")[0]
    benchmark_path = path.with_name("prompt_benchmark.md")
    if benchmark_path.is_file():
        benchmark = benchmark_path.read_text(encoding="utf-8").strip()
    else:
        match = re.search(r"\[\[MODE:BENCHMARK\]\](.*?)\[\[END_MODE:BENCHMARK\]\]", full_text, re.DOTALL)
        if not match:
            raise ValueError(f"no benchmark prompt is available for {path}")
        benchmark = match.group(1).strip()
    return f"{base_rules}\n=== SKILL_END_PROMPT ===\n\n{benchmark}"
