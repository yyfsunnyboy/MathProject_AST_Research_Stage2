"""Offline replay harness for isolated synthetic Math development cases."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from agent_tools.finals_rebuild.artifacts import sha256_text
from agent_tools.finals_rebuild.math_evaluator import MathEvaluationResult, evaluate_math_code
from agent_tools.finals_rebuild.math_task_schema import MathTask
from agent_tools.finals_rebuild.spec_adapter import run_spec_adapter


@dataclass(frozen=True)
class MathDevReplayCase:
    case_id: str
    task: MathTask
    code: str
    enabled_rule_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.case_id, str) or not self.case_id.strip():
            raise ValueError("case_id must be a non-empty string")
        if not isinstance(self.enabled_rule_ids, tuple) or not all(
            isinstance(rule_id, str) and rule_id.strip() for rule_id in self.enabled_rule_ids
        ):
            raise ValueError("enabled_rule_ids must be a tuple of non-empty strings")


@dataclass(frozen=True)
class MathDevReplayResult:
    case_id: str
    code_before: str
    code_after: str
    before_evaluation: MathEvaluationResult
    after_evaluation: MathEvaluationResult
    adapter_trace: object
    changed: bool
    repaired: bool
    failure_reason: str | None


def _adapter_rule_error(trace: object) -> bool:
    if getattr(trace, "failure_reason", None):
        return True
    return any(
        str(getattr(step, "reason", "")).startswith("rule_error:")
        for step in getattr(trace, "steps", ())
    )


def replay_math_dev_case(case: MathDevReplayCase) -> MathDevReplayResult:
    """Replay one supplied synthetic case without model calls or artifacts."""
    before = evaluate_math_code(case.task, case.code)
    adapter = run_spec_adapter(
        pair_id=sha256_text(case.case_id),
        skill_id="jh_math_dev_replay",
        input_code=case.code,
        domain_applicable=True,
        math_output_contract=case.task.output_contract,
        enabled_rule_ids=set(case.enabled_rule_ids),
    )
    after = evaluate_math_code(case.task, adapter.output_code)
    changed = adapter.output_code != case.code
    repaired = (
        before.overall_status != "pass"
        and after.overall_status == "pass"
        and changed
    )

    if _adapter_rule_error(adapter.trace):
        failure_reason = "adapter_rule_error"
    elif before.overall_status == "pass":
        failure_reason = "before_already_passed"
    elif not changed:
        failure_reason = "adapter_no_change"
    elif after.overall_status != "pass":
        failure_reason = "after_still_failed"
    else:
        failure_reason = None

    return MathDevReplayResult(
        case_id=case.case_id,
        code_before=case.code,
        code_after=adapter.output_code,
        before_evaluation=before,
        after_evaluation=after,
        adapter_trace=adapter.trace,
        changed=changed,
        repaired=repaired,
        failure_reason=failure_reason,
    )


def replay_math_dev_cases(
    cases: Sequence[MathDevReplayCase],
) -> tuple[MathDevReplayResult, ...]:
    """Replay cases independently, preserving their input order."""
    return tuple(replay_math_dev_case(case) for case in cases)
