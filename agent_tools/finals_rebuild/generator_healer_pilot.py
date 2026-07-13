"""Read-only before/after pilot using the Tier 1 Core adapter only."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from agent_tools.finals_rebuild.core_adapter import run_core_adapter
from agent_tools.finals_rebuild.generator_evaluator import GeneratorEvaluationResult, evaluate_generator_code
from agent_tools.finals_rebuild.generator_integration_pilot import GeneratorPilotCase, _observed


@dataclass(frozen=True)
class GeneratorHealerPilotResult:
    case: GeneratorPilotCase
    source_sha256: str
    healer_changed: bool
    healer_rules_triggered: tuple[str, ...]
    healer_failure_reason: str | None
    before_evaluation: GeneratorEvaluationResult
    after_evaluation: GeneratorEvaluationResult
    before_category: str
    after_category: str
    outcome: str


@dataclass(frozen=True)
class GeneratorHealerPilotSummary:
    total: int; before_passed: int; after_passed: int; rescued: int; preserved_pass: int; regressed: int; changed_but_not_rescued: int; unchanged_failure: int; healer_error: int; changed_cases: int


def _outcome(before: GeneratorEvaluationResult, after: GeneratorEvaluationResult, changed: bool, error: str | None) -> str:
    if error: return "healer_error"
    if not before.success and after.success: return "rescued"
    if before.success and after.success: return "preserved_pass"
    if before.success and not after.success: return "regressed"
    return "changed_but_not_rescued" if changed else "unchanged_failure"


def run_generator_healer_pilot_case(case: GeneratorPilotCase, *, repo_root: str | Path, timeout_seconds: float = 2.0) -> GeneratorHealerPilotResult:
    root=Path(repo_root).resolve(); path=(root / case.source_file).resolve()
    source=path.read_bytes(); code=source.decode("utf-8")
    before=evaluate_generator_code(code, timeout_seconds=timeout_seconds)
    try:
        core=run_core_adapter(pair_id=hashlib.sha256(case.case_id.encode()).hexdigest(), input_code=code)
        after=evaluate_generator_code(core.output_code, timeout_seconds=timeout_seconds)
        changed=core.output_code != code
        rules=tuple(core.trace.rules_triggered)
        error=core.trace.failure_reason
    except Exception as exc:
        after=before; changed=False; rules=(); error=f"core_adapter_error:{type(exc).__name__}"
    return GeneratorHealerPilotResult(case, hashlib.sha256(source).hexdigest(), changed, rules, error, before, after, _observed(before), _observed(after), _outcome(before, after, changed, error))


def run_generator_healer_pilot(cases: Sequence[GeneratorPilotCase], *, repo_root: str | Path, timeout_seconds: float = 2.0) -> tuple[GeneratorHealerPilotResult, ...]:
    return tuple(run_generator_healer_pilot_case(case, repo_root=repo_root, timeout_seconds=timeout_seconds) for case in cases)


def summarize_generator_healer_pilot(results: Sequence[GeneratorHealerPilotResult]) -> GeneratorHealerPilotSummary:
    outcomes={name: sum(result.outcome == name for result in results) for name in ("rescued","preserved_pass","regressed","changed_but_not_rescued","unchanged_failure","healer_error")}
    return GeneratorHealerPilotSummary(len(results), sum(r.before_evaluation.success for r in results), sum(r.after_evaluation.success for r in results), outcomes["rescued"], outcomes["preserved_pass"], outcomes["regressed"], outcomes["changed_but_not_rescued"], outcomes["unchanged_failure"], outcomes["healer_error"], sum(r.healer_changed for r in results))
