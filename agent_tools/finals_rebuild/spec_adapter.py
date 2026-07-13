"""
Spec Adapter — Commit 3A.

Scope
-----
The Spec Adapter is meant to eventually apply K12-math domain contracts
(calculation skeleton, domain library injection, LaTeX/answer repair) to
Core Adapter output (ab3_full). Commit 3A establishes only the
applicability boundary and no-op behavior: it does NOT call
build_calculation_skeleton(), _inject_domain_libs(), any generate()
fallback, or any RadicalOps/FractionOps/IntegerOps injection. Those are
deferred to Commit 3B and later, enabled rule-by-rule.

No model calls. No code execution. No file I/O.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Set

from agent_tools.finals_rebuild.artifacts import sha256_text
from agent_tools.finals_rebuild.math_spec_rules import (
    RATIONAL_LITERAL_DIVISION_RULE_ID,
    repair_rational_literal_division,
)
from agent_tools.finals_rebuild.math_task_schema import MathOutputContract
from agent_tools.finals_rebuild.trace import TraceStep, TreatmentTrace

# ---------------------------------------------------------------------------
# Rule registry
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SpecRule:
    rule_id: str
    enabled: bool
    safety_classification: str  # see trace.SAFETY_CLASSIFICATIONS
    domain_specific: bool
    reason: str
    fn: Optional[Callable[[str, MathOutputContract], object]] = None
    metadata: Dict[str, str] = field(default_factory=dict)


# Every rule below is disabled by design in Commit 3A.
SPEC_RULE_REGISTRY: Dict[str, SpecRule] = {
    RATIONAL_LITERAL_DIVISION_RULE_ID: SpecRule(
        rule_id=RATIONAL_LITERAL_DIVISION_RULE_ID,
        enabled=False,
        safety_classification="guarded_structural",
        domain_specific=True,
        reason="Disabled by default; only explicit callers may enable the guarded rational literal repair.",
        fn=repair_rational_literal_division,
        metadata={"requires_math_output_contract": "true"},
    ),
    "calculation_skeleton_injection": SpecRule(
        rule_id="calculation_skeleton_injection",
        enabled=False,
        safety_classification="domain_specific",
        domain_specific=True,
        reason=(
            "core.code_generator.build_calculation_skeleton() prepends "
            "PERFECT_UTILS plus dynamically-selected domain helper code. "
            "Deferred to Commit 3B."
        ),
    ),
    "domain_library_injection": SpecRule(
        rule_id="domain_library_injection",
        enabled=False,
        safety_classification="domain_specific",
        domain_specific=True,
        reason=(
            "core.code_generator._inject_domain_libs() injects "
            "RadicalOps/FractionOps/IntegerOps stubs, global aliases, and "
            "skill.json-declared APIs. Deferred to Commit 3B."
        ),
    ),
    "generate_fallback": SpecRule(
        rule_id="generate_fallback",
        enabled=False,
        safety_classification="disabled_semantic_risk",
        domain_specific=True,
        reason=(
            "ASTHealer's generate() fallback fabricates a placeholder "
            "answer when generate() is missing, silently changing the "
            "return contract. Permanently excluded pending a fail-closed "
            "redesign; never simply 'enabled' in a later commit."
        ),
    ),
    "auto_fill_correct_answer": SpecRule(
        rule_id="auto_fill_correct_answer",
        enabled=False,
        safety_classification="domain_specific",
        domain_specific=True,
        reason=(
            "RegexHealer.fix_missing_correct_answer / "
            "fix_shadowed_correct_answer rewrite the math answer contract "
            "(correct_answer assignment). Deferred to Commit 3B."
        ),
    ),
    "domain_ops_injection": SpecRule(
        rule_id="domain_ops_injection",
        enabled=False,
        safety_classification="domain_specific",
        domain_specific=True,
        reason=(
            "RegexHealer.inject_domain_imports / fix_missing_class_prefix "
            "add RadicalOps/FractionOps/IntegerOps imports and call-site "
            "prefixes. Deferred to Commit 3B."
        ),
    ),
    "latex_auto_repair": SpecRule(
        rule_id="latex_auto_repair",
        enabled=False,
        safety_classification="domain_specific",
        domain_specific=True,
        reason=(
            "RegexHealer.fix_latex_hallucinations_in_strings rewrites "
            "LaTeX string content (brackets, trailing operators, squared "
            "terms). Deferred to Commit 3B."
        ),
    ),
    "domain_function_helper_injection": SpecRule(
        rule_id="domain_function_helper_injection",
        enabled=False,
        safety_classification="domain_specific",
        domain_specific=True,
        reason=(
            "DomainFunctionHelper import injection for the Radical "
            "Orchestrator scaffold. Deferred to Commit 3B."
        ),
    ),
}


# ---------------------------------------------------------------------------
# Applicability classifier
# ---------------------------------------------------------------------------

# Observed skill_id naming convention in this project: jh_ (國中/junior
# high) and gh_ (高中/senior high) skill IDs are K12 math skills. Unknown or
# ambiguous skill_ids are NOT treated as applicable — conservative default.
K12_MATH_SKILL_ID_PREFIXES: tuple[str, ...] = ("jh_", "gh_")


def is_k12_math_domain(skill_id: str) -> bool:
    """Minimal, conservative K12-math domain classifier for Commit 3A."""
    if not isinstance(skill_id, str) or not skill_id:
        return False
    return skill_id.startswith(K12_MATH_SKILL_ID_PREFIXES)


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SpecAdapterResult:
    output_code: str
    trace: TreatmentTrace


def run_spec_adapter(
    *,
    pair_id: str,
    skill_id: str,
    input_code: str,
    domain_applicable: Optional[bool] = None,
    math_output_contract: Optional[MathOutputContract] = None,
    enabled_rule_ids: Optional[Set[str]] = None,
) -> SpecAdapterResult:
    """
    Apply only ENABLED rules from SPEC_RULE_REGISTRY to *input_code*, which
    must be the Core Adapter's output.

    domain_applicable: explicit classifier override. When None,
    is_k12_math_domain(skill_id) decides applicability.

    Non-applicable domains return a pure no-op trace (applicable=False,
    applied=False, changed=False, no steps). Applicable domains still
    return changed=False in Commit 3A because every Spec rule is disabled;
    implementation_status reflects this explicitly rather than pretending
    a repair happened.

    The returned trace has run_id="" and created_at_utc="" as placeholders;
    the pipeline binds both once it has resolved the treatment's actual
    run_id and idempotent timestamp.
    """
    input_hash = sha256_text(input_code)
    applicable = (
        domain_applicable
        if domain_applicable is not None
        else is_k12_math_domain(skill_id)
    )

    if not applicable:
        trace = TreatmentTrace(
            pair_id=pair_id,
            run_id="",
            treatment="ab3_full",
            component="spec",
            applicable=False,
            applied=False,
            changed=False,
            input_hash=input_hash,
            output_hash=input_hash,
            implementation_status="not_applicable",
            fail_closed=True,
            failure_reason=None,
            contract_changed=False,
            rules_triggered=[],
            steps=[],
            created_at_utc="",
        )
        return SpecAdapterResult(output_code=input_code, trace=trace)

    code = input_code
    steps: List[TraceStep] = []
    rules_triggered: List[str] = []

    explicitly_enabled = enabled_rule_ids or set()
    failure_reason: Optional[str] = None
    for rule_id, rule in SPEC_RULE_REGISTRY.items():
        before_hash = sha256_text(code)
        enabled = rule.enabled or (rule_id in explicitly_enabled and rule.fn is not None)
        if enabled and rule.fn is not None:
            if math_output_contract is None:
                new_code = code
                after_hash = before_hash
                changed = False
                reason = "missing_math_output_contract"
            else:
                try:
                    repair = rule.fn(code, math_output_contract)
                    new_code = repair.code_after
                    after_hash = repair.after_hash
                    changed = repair.changed
                    reason = repair.reason
                except Exception as exc:
                    new_code = code
                    after_hash = before_hash
                    changed = False
                    reason = f"rule_error:{type(exc).__name__}"
                    failure_reason = reason
            if changed:
                code = new_code
                rules_triggered.append(rule_id)
            steps.append(TraceStep(
                rule_id=rule_id,
                source_component="spec",
                changed=changed,
                before_hash=before_hash,
                after_hash=after_hash,
                reason=reason,
                domain_specific=rule.domain_specific,
                safety_classification=rule.safety_classification,
                enabled=True,
            ))
        else:
            steps.append(TraceStep(
                rule_id=rule_id,
                source_component="spec",
                changed=False,
                before_hash=before_hash,
                after_hash=before_hash,
                reason=rule.reason,
                domain_specific=rule.domain_specific,
                safety_classification=rule.safety_classification,
                enabled=False,
            ))

    output_hash = sha256_text(code)
    changed_overall = output_hash != input_hash
    implementation_status = (
        "implemented" if changed_overall else "implemented_no_safe_rule_triggered"
    )

    trace = TreatmentTrace(
        pair_id=pair_id,
        run_id="",
        treatment="ab3_full",
        component="spec",
        applicable=True,
        applied=True,
        changed=changed_overall,
        input_hash=input_hash,
        output_hash=output_hash,
        implementation_status=implementation_status,
        fail_closed=True,
        failure_reason=failure_reason,
        contract_changed=False,
        rules_triggered=rules_triggered,
        steps=steps,
        created_at_utc="",
    )
    return SpecAdapterResult(output_code=code, trace=trace)
