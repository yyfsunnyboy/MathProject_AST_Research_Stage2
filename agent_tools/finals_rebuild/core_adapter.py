"""
Core Adapter — Commit 3A.

Scope
-----
The Core Adapter is meant to eventually apply generic, non-domain-specific
Python fixups to Scaffold-extracted code (ab3_core). It must never contain
K12-math domain knowledge, and it must never call the legacy Healer classes
directly (RegexHealer, ASTHealer, AntiDuplicationHealer,
UnifiedCleanupHealer) — this module owns its own rule registry instead.

Commit 3A intentionally ships every candidate rule DISABLED. The registry
below documents each rule that was inventoried from the legacy healers,
why it is not safe to enable yet, and its safety classification. No rule
executes in this commit; run_core_adapter() is a deterministic identity
transform that still produces a full, rule-level TreatmentTrace.

No model calls. No code execution. No file I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from agent_tools.finals_rebuild.artifacts import sha256_text
from agent_tools.finals_rebuild.trace import TraceStep, TreatmentTrace

# ---------------------------------------------------------------------------
# Rule registry
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CoreRule:
    rule_id: str
    enabled: bool
    safety_classification: str  # see trace.SAFETY_CLASSIFICATIONS
    domain_specific: bool
    reason: str
    fn: Optional[Callable[[str], str]] = None  # unset while disabled


# Every rule below is disabled by design in Commit 3A. Each entry documents
# the legacy healer method it was inventoried from and the reason it is not
# yet proven safe for the Core boundary (see Commit 3 read-only inventory).
CORE_RULE_REGISTRY: Dict[str, CoreRule] = {
    "xor_to_power": CoreRule(
        rule_id="xor_to_power",
        enabled=False,
        safety_classification="guarded_structural",
        domain_specific=False,
        reason=(
            "ASTHealer.visit_BinOp rewrites '^' (BitXor) to '**' (Pow). "
            "Deferred: could silently break code that legitimately uses "
            "bitwise XOR."
        ),
    ),
    "while_true_bounding": CoreRule(
        rule_id="while_true_bounding",
        enabled=False,
        safety_classification="guarded_structural",
        domain_specific=False,
        reason=(
            "ASTHealer.visit_While rewrites 'while True' into a bounded "
            "for-loop. Changes control flow and can change the return "
            "contract of loops relying on unbounded iteration. Deferred."
        ),
    ),
    "remove_input_calls": CoreRule(
        rule_id="remove_input_calls",
        enabled=False,
        safety_classification="guarded_structural",
        domain_specific=False,
        reason=(
            "RegexHealer.remove_input_calls / ASTHealer input() interception "
            "replace input() with a constant. Changes runtime behavior. "
            "Deferred."
        ),
    ),
    "mismatched_brace_completion": CoreRule(
        rule_id="mismatched_brace_completion",
        enabled=False,
        safety_classification="guarded_structural",
        domain_specific=False,
        reason=(
            "RegexHealer.fix_mismatched_braces uses a last-line heuristic "
            "that can misfire on legitimate code. Not proven safe. Deferred."
        ),
    ),
    "strip_chinese_garbage": CoreRule(
        rule_id="strip_chinese_garbage",
        enabled=False,
        safety_classification="disabled_semantic_risk",
        domain_specific=False,
        reason=(
            "RegexHealer._strip_chinese_garbage can drop whole lines of "
            "code (not just comments) when it misdetects thinking leakage. "
            "Semantic risk. Permanently excluded pending redesign."
        ),
    ),
    "import_removal": CoreRule(
        rule_id="import_removal",
        enabled=False,
        safety_classification="disabled_semantic_risk",
        domain_specific=False,
        reason=(
            "ASTHealer.visit_Import / visit_ImportFrom strip imports via an "
            "allowlist that itself encodes domain assumptions (e.g. 'core' "
            "module trust). Deferred."
        ),
    ),
    "duplicate_definition_removal": CoreRule(
        rule_id="duplicate_definition_removal",
        enabled=False,
        safety_classification="guarded_structural",
        domain_specific=False,
        reason=(
            "RegexHealer.remove_duplicate_class_definitions and "
            "AntiDuplicationHealer.heal keep only the first definition of a "
            "repeated name; not proven safe against legitimate shadowing "
            "patterns. Deferred."
        ),
    ),
    "function_deletion_heuristics": CoreRule(
        rule_id="function_deletion_heuristics",
        enabled=False,
        safety_classification="disabled_semantic_risk",
        domain_specific=False,
        reason=(
            "ASTHealer.visit_FunctionDef deletes functions matching a "
            "CamelCase/keyword heuristic. Can delete legitimate user code. "
            "Permanently excluded pending redesign."
        ),
    ),
    "generate_fallback": CoreRule(
        rule_id="generate_fallback",
        enabled=False,
        safety_classification="disabled_semantic_risk",
        domain_specific=True,
        reason=(
            "ASTHealer.heal injects a fabricated generate() function "
            "returning a placeholder answer when generate() is missing. "
            "This silently changes the return contract and masks "
            "generation failure instead of failing closed. Permanently "
            "excluded from Core; never eligible for Spec either without a "
            "fail-closed redesign."
        ),
    ),
    "signature_rewrite": CoreRule(
        rule_id="signature_rewrite",
        enabled=False,
        safety_classification="disabled_semantic_risk",
        domain_specific=False,
        reason=(
            "Any rewrite of function signatures changes the calling "
            "contract. No such rule is enabled in this commit."
        ),
    ),
    "return_contract_rewrite": CoreRule(
        rule_id="return_contract_rewrite",
        enabled=False,
        safety_classification="disabled_semantic_risk",
        domain_specific=False,
        reason=(
            "Any rewrite of return values/shape changes the evaluation "
            "contract. No such rule is enabled in this commit."
        ),
    ),
}


@dataclass(frozen=True)
class CoreAdapterResult:
    output_code: str
    trace: TreatmentTrace


def run_core_adapter(*, pair_id: str, input_code: str) -> CoreAdapterResult:
    """
    Apply only ENABLED rules from CORE_RULE_REGISTRY to *input_code*.

    Commit 3A: every registry rule is disabled, so this is a deterministic
    identity transform (output_code == input_code). It still produces a
    full TreatmentTrace documenting every candidate rule considered.

    The returned trace has run_id="" and created_at_utc="" as placeholders;
    the pipeline binds both once it has resolved the treatment's actual
    run_id and idempotent timestamp.
    """
    input_hash = sha256_text(input_code)
    code = input_code
    steps: List[TraceStep] = []
    rules_triggered: List[str] = []

    for rule_id, rule in CORE_RULE_REGISTRY.items():
        before_hash = sha256_text(code)
        if rule.enabled and rule.fn is not None:
            new_code = rule.fn(code)
            after_hash = sha256_text(new_code)
            changed = after_hash != before_hash
            if changed:
                code = new_code
                rules_triggered.append(rule_id)
            steps.append(TraceStep(
                rule_id=rule_id,
                source_component="core",
                changed=changed,
                before_hash=before_hash,
                after_hash=after_hash,
                reason=rule.reason,
                domain_specific=rule.domain_specific,
                safety_classification=rule.safety_classification,
                enabled=True,
            ))
        else:
            steps.append(TraceStep(
                rule_id=rule_id,
                source_component="core",
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
        treatment="ab3_core",
        component="core",
        applicable=True,
        applied=True,
        changed=changed_overall,
        input_hash=input_hash,
        output_hash=output_hash,
        implementation_status=implementation_status,
        fail_closed=True,
        failure_reason=None,
        contract_changed=False,
        rules_triggered=rules_triggered,
        steps=steps,
        created_at_utc="",
    )

    return CoreAdapterResult(output_code=code, trace=trace)
