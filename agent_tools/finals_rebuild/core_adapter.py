"""
Core Adapter — Commit 3A / 3B-1.

Scope
-----
The Core Adapter is meant to eventually apply generic, non-domain-specific
Python fixups to Scaffold-extracted code (ab3_core). It must never contain
K12-math domain knowledge, and it must never call the legacy Healer classes
directly (RegexHealer, ASTHealer, AntiDuplicationHealer,
UnifiedCleanupHealer) — this module owns its own rule registry instead.

Commit 3A shipped every candidate rule DISABLED. Commit 3B-1 enables exactly
one, "core.normalize_fullwidth_python_punctuation" (see below): a
tokenize-based, fail-closed normaliser that only touches fullwidth
punctuation sitting in Python syntax position, never inside strings,
comments, or docstrings. Every other rule remains disabled; the registry
still documents why, and run_core_adapter() still produces a full,
rule-level TreatmentTrace for every candidate rule regardless of whether it
ran.

No model calls. No code execution. No file I/O.
"""

from __future__ import annotations

import ast
import io
import tokenize
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

from agent_tools.finals_rebuild.artifacts import sha256_text
from agent_tools.finals_rebuild.trace import TraceStep, TreatmentTrace

# ---------------------------------------------------------------------------
# core.normalize_fullwidth_python_punctuation
# ---------------------------------------------------------------------------

# Fullwidth punctuation → ASCII equivalent. Deliberately limited to bracket/
# delimiter punctuation that can appear at Python syntax positions; no
# operator glyphs (e.g. fullwidth '>', '=') are included because those were
# not in the approved scope for this rule.
_FULLWIDTH_PUNCT_MAP: Dict[str, str] = {
    "，": ",",  # ，
    "：": ":",  # ：
    "；": ";",  # ；
    "（": "(",  # （
    "）": ")",  # ）
    "［": "[",  # ［
    "］": "]",  # ］
    "｛": "{",  # ｛
    "｝": "}",  # ｝
}


def normalize_fullwidth_python_punctuation(code: str) -> str:
    """
    Replace fullwidth punctuation (，：；（）［］｛｝) with ASCII equivalents,
    but ONLY where they occur in Python syntax position — never inside
    string literals, comments, docstrings, or f-string text segments.

    Implementation
    --------------
    Token-boundary matching does NOT work here: CPython's tokenizer treats
    several of these fullwidth punctuation characters as identifier
    (XID_Continue) characters, so e.g. "f(x，y)" tokenizes '，' as *part of
    the same NAME token* as the surrounding identifier characters, not as
    its own OP/ERRORTOKEN. Splitting punctuation out of a merged NAME token
    would be an unsafe, ambiguous edit.

    Instead this uses tokenize.generate_tokens() only to find the exact
    (row, col) spans of STRING and COMMENT tokens (and FSTRING_MIDDLE/START/
    END on 3.12+, where present) — those spans are masked as "protected".
    Every other character position in the source is then scanned directly:
    any of the 9 mapped characters found outside a protected span is
    replaced. Because none of the 9 characters are ever legal inside a
    normal Python identifier's *meaning* (var/def names are never composed
    of comma/colon/parenthesis/etc glyphs even though the tokenizer's
    XID table happens to tolerate a few of them), this is safe: it reaches
    every syntax-position occurrence including ones tokenize would have
    bundled into a NAME token, while never touching string/comment content.

    Fail-closed
    -----------
    - If tokenizing the input raises anything, the original code is
      returned unchanged.
    - After rewriting, the result is re-parsed with ast.parse(). If that
      fails for any reason (e.g. an unmapped fullwidth character remains,
      such as '＞'), the original code is returned unchanged.
    - If no unprotected mapped character is found, the original code is
      returned unchanged (byte-identical, not just semantically equivalent).
    """
    if not code:
        return code

    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(code).readline))
    except Exception:
        return code

    protected_types = {tokenize.STRING, tokenize.COMMENT}
    for _name in ("FSTRING_START", "FSTRING_MIDDLE", "FSTRING_END"):
        _t = getattr(tokenize, _name, None)
        if _t is not None:
            protected_types.add(_t)

    lines = code.splitlines(keepends=True)
    # protected[row] (1-indexed, matching tokenize) -> list of (start_col, end_col)
    protected: Dict[int, List[Tuple[int, int]]] = {}

    def _mark_protected(start: Tuple[int, int], end: Tuple[int, int]) -> None:
        (start_row, start_col), (end_row, end_col) = start, end
        if start_row == end_row:
            protected.setdefault(start_row, []).append((start_col, end_col))
            return
        # Multi-line span (e.g. a triple-quoted docstring): protect from
        # start_col to end-of-line on the first line, every column on the
        # interior lines, and 0..end_col on the last line.
        protected.setdefault(start_row, []).append(
            (start_col, len(lines[start_row - 1]))
        )
        for row in range(start_row + 1, end_row):
            protected.setdefault(row, []).append((0, len(lines[row - 1])))
        protected.setdefault(end_row, []).append((0, end_col))

    for tok in tokens:
        if tok.type in protected_types:
            _mark_protected(tok.start, tok.end)

    def _is_protected(row: int, col: int) -> bool:
        for start_col, end_col in protected.get(row, ()):
            if start_col <= col < end_col:
                return True
        return False

    new_lines = list(lines)
    changed_any = False
    for row_idx, line in enumerate(lines, start=1):
        chars = list(line)
        line_changed = False
        for col, ch in enumerate(chars):
            if ch in _FULLWIDTH_PUNCT_MAP and not _is_protected(row_idx, col):
                chars[col] = _FULLWIDTH_PUNCT_MAP[ch]
                line_changed = True
        if line_changed:
            new_lines[row_idx - 1] = "".join(chars)
            changed_any = True

    if not changed_any:
        return code

    new_code = "".join(new_lines)

    try:
        ast.parse(new_code)
    except Exception:
        return code

    return new_code


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
    "core.normalize_fullwidth_python_punctuation": CoreRule(
        rule_id="core.normalize_fullwidth_python_punctuation",
        enabled=True,
        safety_classification="safe_format",
        domain_specific=False,
        reason=(
            "Normalises fullwidth punctuation (，：；（）［］｛｝) that "
            "appears in Python syntax position only. tokenize-based: uses "
            "STRING/COMMENT/FSTRING_* token spans to mask string, comment, "
            "and docstring content as protected, then rewrites the 9 "
            "mapped characters only outside those spans. Fails closed to "
            "the original code if tokenizing errors or the rewritten "
            "result does not re-parse with ast.parse()."
        ),
        fn=normalize_fullwidth_python_punctuation,
    ),
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
