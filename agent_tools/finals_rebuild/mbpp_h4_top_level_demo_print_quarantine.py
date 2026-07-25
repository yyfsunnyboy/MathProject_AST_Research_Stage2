"""H4: post-H2 stage-aware demo-print quarantine.

Fixed cumulative order: H1 -> H2 -> H3 -> H4. This module's stage contract is
different from the pre-existing, independently frozen
``top_level_literal_only_demo_print_quarantine_v0`` evidence
(``mbpp_top_level_demo_print_quarantine.py``), whose own preregistration
records ``composition_order: "demo_print_then_H2"`` -- i.e. that rule was
validated as running *before* H2, on a source where the self-test assert was
still top-level.

Running the same top-level-assert-seeking guard *after* H2 is a stage
interface collision, not a safety property: H2 already relocates any
top-level assert that would satisfy H4's own selftest guards into
``if __name__ == "__main__":`` before H4 ever sees the source, so a
naive post-H2 reapplication of the old guard set abstains on every cell by
construction, independent of any actual demo-print content.

H4 instead requires **structural H2 provenance**: it only acts when (a) the
H2 stage itself reports ``changed=True`` for this cell, and (b) the resulting
source contains an ``if __name__ == "__main__":`` guard whose sole body
statement is, by AST structural comparison (``ast.dump``, no position
attributes), the exact same Assert that was top-level in H2's *input*
source. Absent that structural proof, H4 abstains -- an arbitrary
pre-existing ``__main__`` guard never triggers it.

When provenance is confirmed, H4 looks at H2's *pre-transform* source to find
the top-level ``print`` statement (if any) that was adjacent to that same
assert, re-validates it against the pre-existing literal/argument-safety
guards, and -- if every guard holds -- merges that print into the same
guard H2 created, directly after the assert. The print is moved, never
deleted; statement order and content are preserved. The transform is
idempotent: once merged, the print is no longer top-level in H4's own
input source, so ``print_still_top_level_in_h4_input`` fails on any
re-application and the rule abstains without further change.

Content-safety helpers (literal detection, print-argument safety, assert
fingerprinting, main-guard shape, function-segment hashing) are imported
unmodified from ``mbpp_top_level_demo_print_quarantine.py`` rather than
duplicated, since that module's guard logic is itself frozen development
evidence and must not be forked.
"""

from __future__ import annotations

import ast
import hashlib
from dataclasses import asdict, dataclass
from typing import Any, Iterable

from agent_tools.finals_rebuild.mbpp_top_level_demo_print_quarantine import (
    _function_segment_hashes,
    _is_main_guard,
    _print_is_safe,
    _unclassified_top_level_call_count,
    assert_fingerprint,
)

RULE_ID = "top_level_demo_print_quarantine_v0"
RULE_STATUS = "development_candidate_not_frozen"


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _dump(node: ast.AST) -> str:
    return ast.dump(node, annotate_fields=True, include_attributes=False)


@dataclass(frozen=True)
class DemoPrintDecision:
    rule_id: str
    rule_status: str
    triggered: bool
    transformed: bool
    abstained: bool
    reason: str
    guard_results: dict[str, bool]
    source_sha256: str
    output_sha256: str
    output_source: str
    claim: str

    def record(self) -> dict[str, Any]:
        return asdict(self)


def _decision(
    source: str,
    *,
    triggered: bool,
    transformed: bool,
    reason: str,
    guard_results: dict[str, bool],
    output_source: str | None = None,
) -> DemoPrintDecision:
    output = source if output_source is None else output_source
    return DemoPrintDecision(
        rule_id=RULE_ID,
        rule_status=RULE_STATUS,
        triggered=triggered,
        transformed=transformed,
        abstained=not transformed,
        reason=reason,
        guard_results=dict(sorted(guard_results.items())),
        source_sha256=_sha256_text(source),
        output_sha256=_sha256_text(output),
        output_source=output,
        claim="post_h2_demo_print_merged_into_h2_created_guard_no_correctness_claim",
    )


def _find_h2_created_guard(
    h2_input_tree: ast.Module, h4_input_tree: ast.Module
) -> ast.If | None:
    """Return the unique __main__ guard in h4_input_tree whose sole body
    statement structurally matches (ast.dump) a top-level Assert that
    existed in h2_input_tree, or None if no such unambiguous match exists.
    """
    pre_asserts = [n for n in h2_input_tree.body if isinstance(n, ast.Assert)]
    if len(pre_asserts) != 1:
        return None
    pre_dump = _dump(pre_asserts[0])

    candidate: ast.If | None = None
    for node in h4_input_tree.body:
        if not _is_main_guard(node):
            continue
        if len(node.body) == 1 and isinstance(node.body[0], ast.Assert):
            if _dump(node.body[0]) == pre_dump:
                if candidate is not None:
                    return None
                candidate = node
    return candidate


def _merge_print_into_guard(
    source: str, guard_node: ast.If, print_stmt: ast.Expr
) -> str | None:
    if print_stmt.end_lineno is None or guard_node.body[0].end_lineno is None:
        return None
    lines = source.splitlines(keepends=True)
    print_start = print_stmt.lineno - 1
    print_end = print_stmt.end_lineno
    if print_start < 0 or print_end > len(lines):
        return None
    first_line = lines[print_start]
    if first_line[: print_stmt.col_offset].strip():
        return None

    print_lines = lines[print_start:print_end]
    assert_stmt = guard_node.body[0]
    assert_end = assert_stmt.end_lineno

    removed = print_end - print_start
    remaining = lines[:print_start] + lines[print_end:]
    if print_end <= assert_stmt.lineno:
        assert_end -= removed

    if assert_end < 0 or assert_end > len(remaining):
        return None

    indent = "    "
    guarded_print_lines = [indent + line for line in print_lines]
    output_lines = remaining[:assert_end] + guarded_print_lines + remaining[assert_end:]
    return "".join(output_lines)


def quarantine_post_h2_top_level_demo_print(
    *,
    h2_input_source: str,
    h4_input_source: str,
    h2_changed: bool,
    entry_point: str,
    extraction_unambiguous: bool | None,
    source_complete: bool | None,
    public_assert_fingerprints: Iterable[str],
) -> DemoPrintDecision:
    """Apply H4 only under confirmed post-H2 structural provenance.

    ``h2_input_source`` is the source H2 was given (H1's output_source).
    ``h4_input_source`` is the source H4 must rewrite (H3's output_source,
    i.e. post-H1-H2-H3). ``h2_changed`` is H2's own StageRecord.changed
    signal for this exact cell -- H4 never re-derives whether H2 "should
    have" transformed; without h2_changed=True there is no provenance to
    confirm and H4 abstains regardless of any __main__ guard present.
    """
    guards = {
        "extraction_unambiguous": extraction_unambiguous is True,
        "source_complete": source_complete is True,
        "h2_reported_changed": h2_changed is True,
        "h2_input_parseable": False,
        "h4_input_parseable": False,
        "h2_guard_provenance_confirmed": False,
        "exactly_one_h2_input_top_level_print": False,
        "print_adjacent_to_h2_input_assert": False,
        "assert_matches_public_selftest": False,
        "print_still_top_level_in_h4_input": False,
        "print_arguments_safe": False,
        "builtin_print_unshadowed": False,
        "no_other_unclassified_top_level_calls": False,
        "output_parseable": False,
        "function_segments_unchanged": False,
        "print_removed_from_top_level": False,
    }

    if not isinstance(h4_input_source, str) or not h4_input_source.strip():
        return _decision(
            h4_input_source if isinstance(h4_input_source, str) else "",
            triggered=False,
            transformed=False,
            reason="empty_or_invalid_source",
            guard_results=guards,
        )
    if not isinstance(entry_point, str) or not entry_point.isidentifier():
        return _decision(
            h4_input_source,
            triggered=False,
            transformed=False,
            reason="invalid_entry_point",
            guard_results=guards,
        )
    if extraction_unambiguous is not True:
        return _decision(
            h4_input_source,
            triggered=False,
            transformed=False,
            reason="extraction_ambiguous_or_unknown",
            guard_results=guards,
        )
    if source_complete is not True:
        return _decision(
            h4_input_source,
            triggered=False,
            transformed=False,
            reason="source_truncated_or_completion_unknown",
            guard_results=guards,
        )
    if h2_changed is not True:
        return _decision(
            h4_input_source,
            triggered=False,
            transformed=False,
            reason="h2_did_not_transform_no_provenance",
            guard_results=guards,
        )
    if not isinstance(h2_input_source, str) or not h2_input_source.strip():
        return _decision(
            h4_input_source,
            triggered=False,
            transformed=False,
            reason="missing_h2_input_source_for_provenance",
            guard_results=guards,
        )

    try:
        h2_input_tree = ast.parse(h2_input_source)
    except SyntaxError:
        return _decision(
            h4_input_source,
            triggered=False,
            transformed=False,
            reason="h2_input_source_unparseable",
            guard_results=guards,
        )
    guards["h2_input_parseable"] = True

    try:
        h4_input_tree = ast.parse(h4_input_source)
    except SyntaxError:
        return _decision(
            h4_input_source,
            triggered=False,
            transformed=False,
            reason="h4_input_source_unparseable",
            guard_results=guards,
        )
    guards["h4_input_parseable"] = True

    guard_node = _find_h2_created_guard(h2_input_tree, h4_input_tree)
    if guard_node is None:
        return _decision(
            h4_input_source,
            triggered=False,
            transformed=False,
            reason="h2_guard_provenance_not_confirmed",
            guard_results=guards,
        )
    guards["h2_guard_provenance_confirmed"] = True

    pre_assertion = [n for n in h2_input_tree.body if isinstance(n, ast.Assert)][0]
    pre_prints = [
        n
        for n in h2_input_tree.body
        if isinstance(n, ast.Expr)
        and isinstance(n.value, ast.Call)
        and isinstance(n.value.func, ast.Name)
        and n.value.func.id == "print"
    ]
    triggered = bool(pre_prints)
    guards["exactly_one_h2_input_top_level_print"] = len(pre_prints) == 1
    common = {"triggered": triggered, "transformed": False, "guard_results": guards}
    if len(pre_prints) != 1:
        reason = (
            "no_h2_input_top_level_print"
            if not pre_prints
            else "h2_input_top_level_print_count_not_one"
        )
        return _decision(h4_input_source, reason=reason, **common)

    pre_print = pre_prints[0]
    print_index = h2_input_tree.body.index(pre_print)
    assert_index = h2_input_tree.body.index(pre_assertion)
    guards["print_adjacent_to_h2_input_assert"] = abs(print_index - assert_index) == 1
    if not guards["print_adjacent_to_h2_input_assert"]:
        return _decision(h4_input_source, reason="print_not_adjacent_to_h2_input_assert", **common)

    fp_set = {v for v in public_assert_fingerprints if isinstance(v, str)}
    guards["assert_matches_public_selftest"] = assert_fingerprint(pre_assertion) in fp_set
    if not guards["assert_matches_public_selftest"]:
        return _decision(h4_input_source, reason="adjacent_assert_not_in_public_prompt", **common)

    pre_print_dump = _dump(pre_print)
    h4_top_level_prints = [
        n
        for n in h4_input_tree.body
        if isinstance(n, ast.Expr)
        and isinstance(n.value, ast.Call)
        and isinstance(n.value.func, ast.Name)
        and n.value.func.id == "print"
        and _dump(n) == pre_print_dump
    ]
    guards["print_still_top_level_in_h4_input"] = len(h4_top_level_prints) == 1
    if not guards["print_still_top_level_in_h4_input"]:
        return _decision(h4_input_source, reason="print_not_found_top_level_in_h4_input", **common)
    target_print = h4_top_level_prints[0]

    guards["print_arguments_safe"] = _print_is_safe(target_print.value, entry_point)
    if not guards["print_arguments_safe"]:
        return _decision(
            h4_input_source,
            reason="print_arguments_not_literal_or_entrypoint_literal_call",
            **common,
        )

    module_bound_print = any(
        (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and node.name == "print"
        )
        or (
            isinstance(node, (ast.Import, ast.ImportFrom))
            and any((a.asname or a.name.split(".")[-1]) == "print" for a in node.names)
        )
        or (
            isinstance(node, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "print" for t in node.targets)
        )
        for node in h4_input_tree.body
    )
    guards["builtin_print_unshadowed"] = not module_bound_print
    if not guards["builtin_print_unshadowed"]:
        return _decision(h4_input_source, reason="print_name_shadowed", **common)

    other_calls = _unclassified_top_level_call_count(h4_input_tree, target_print, guard_node)
    guards["no_other_unclassified_top_level_calls"] = other_calls == 0
    if not guards["no_other_unclassified_top_level_calls"]:
        return _decision(h4_input_source, reason="other_unclassified_top_level_call_present", **common)

    output = _merge_print_into_guard(h4_input_source, guard_node, target_print)
    if output is None:
        return _decision(h4_input_source, reason="source_rewrite_boundary_ambiguous", **common)

    try:
        output_tree = ast.parse(output)
    except SyntaxError:
        return _decision(h4_input_source, reason="output_unparseable", **common)
    guards["output_parseable"] = True

    guards["function_segments_unchanged"] = _function_segment_hashes(
        h4_input_source, h4_input_tree
    ) == _function_segment_hashes(output, output_tree)
    if not guards["function_segments_unchanged"]:
        return _decision(h4_input_source, reason="function_content_change_detected", **common)

    output_top_level_prints = [
        n
        for n in output_tree.body
        if isinstance(n, ast.Expr)
        and isinstance(n.value, ast.Call)
        and isinstance(n.value.func, ast.Name)
        and n.value.func.id == "print"
    ]
    guards["print_removed_from_top_level"] = len(output_top_level_prints) == 0
    if not guards["print_removed_from_top_level"]:
        return _decision(h4_input_source, reason="print_still_top_level", **common)

    return _decision(
        h4_input_source,
        triggered=True,
        transformed=True,
        reason="transformed_demo_print_merged_into_h2_guard",
        guard_results=guards,
        output_source=output,
    )


__all__ = [
    "DemoPrintDecision",
    "RULE_ID",
    "RULE_STATUS",
    "quarantine_post_h2_top_level_demo_print",
]
