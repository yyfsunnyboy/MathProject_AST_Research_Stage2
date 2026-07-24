"""Guarded H2 quarantine for one module-level entry-point self-test assert.

The rule is deliberately independent from the existing H1 healer.  It never
uses task IDs, expected answers, evaluator outcomes, or candidate execution.
Its only claim is that a narrowly recognized self-test assert is moved behind
``if __name__ == "__main__":`` so it no longer runs during module import.
"""

from __future__ import annotations

import ast
import hashlib
from dataclasses import asdict, dataclass
from typing import Any

RULE_ID = "module_assert_entrypoint_selftest_quarantine_v0"
RULE_STATUS = "development_candidate_not_frozen"


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class H2Decision:
    rule_id: str
    rule_status: str
    triggered: bool
    transformed: bool
    abstained: bool
    reason: str
    module_assert_count: int
    entrypoint_status: str
    guard_results: dict[str, bool]
    source_sha256: str
    output_sha256: str
    output_source: str
    claim: str

    def record(self) -> dict[str, Any]:
        """Return the serializable decision record, including output source."""
        return asdict(self)


def _decision(
    source: str,
    *,
    triggered: bool,
    transformed: bool,
    reason: str,
    module_assert_count: int,
    entrypoint_status: str,
    guard_results: dict[str, bool],
    output_source: str | None = None,
) -> H2Decision:
    output = source if output_source is None else output_source
    return H2Decision(
        rule_id=RULE_ID,
        rule_status=RULE_STATUS,
        triggered=triggered,
        transformed=transformed,
        abstained=not transformed,
        reason=reason,
        module_assert_count=module_assert_count,
        entrypoint_status=entrypoint_status,
        guard_results=dict(sorted(guard_results.items())),
        source_sha256=_sha256_text(source),
        output_sha256=_sha256_text(output),
        output_source=output,
        claim="module_load_assert_quarantined_only_no_pass_claim",
    )


def _entrypoint_status(tree: ast.Module, entry_point: str) -> tuple[str, int]:
    count = sum(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == entry_point
        for node in tree.body
    )
    if count == 1:
        return "unique", count
    if count == 0:
        return "missing", count
    return "multiple", count


def _is_literal(node: ast.AST) -> bool:
    if isinstance(node, ast.Constant):
        return True
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return all(_is_literal(item) for item in node.elts)
    if isinstance(node, ast.Dict):
        return all(
            key is not None and _is_literal(key) for key in node.keys
        ) and all(_is_literal(value) for value in node.values)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        return _is_literal(node.operand)
    return False


_ALLOWED_EXPRESSION_NODES = (
    ast.BoolOp,
    ast.BinOp,
    ast.UnaryOp,
    ast.Compare,
    ast.Call,
    ast.Name,
    ast.Load,
    ast.Constant,
    ast.List,
    ast.Tuple,
    ast.Set,
    ast.Dict,
    ast.keyword,
    ast.operator,
    ast.unaryop,
    ast.boolop,
    ast.cmpop,
)


def _selftest_guards(
    assertion: ast.Assert, entry_point: str
) -> tuple[dict[str, bool], str | None]:
    calls = [node for node in ast.walk(assertion.test) if isinstance(node, ast.Call)]
    entry_calls = [
        node
        for node in calls
        if isinstance(node.func, ast.Name) and node.func.id == entry_point
    ]
    names = {
        node.id for node in ast.walk(assertion.test) if isinstance(node, ast.Name)
    }
    allowed_names = {entry_point, "abs"}

    direct_entrypoint_call = len(entry_calls) == 1
    expression_names_safe = names <= allowed_names
    expression_calls_safe = all(
        isinstance(call.func, ast.Name)
        and call.func.id in allowed_names
        and (
            call.func.id != "abs"
            or (len(call.args) == 1 and not call.keywords)
        )
        for call in calls
    )
    literal_call_arguments = bool(entry_calls) and all(
        all(_is_literal(arg) for arg in call.args)
        and all(
            keyword.arg is not None and _is_literal(keyword.value)
            for keyword in call.keywords
        )
        for call in entry_calls
    )
    expression_shape_safe = all(
        isinstance(node, _ALLOWED_EXPRESSION_NODES)
        for node in ast.walk(assertion.test)
    )
    message_safe = assertion.msg is None or (
        isinstance(assertion.msg, ast.Constant)
        and isinstance(assertion.msg.value, str)
    )
    standalone_statement = assertion.col_offset == 0

    guards = {
        "assert_direct_entrypoint_call": direct_entrypoint_call,
        "assert_expression_calls_safe": expression_calls_safe,
        "assert_expression_names_safe": expression_names_safe,
        "assert_expression_shape_safe": expression_shape_safe,
        "assert_literal_call_arguments": literal_call_arguments,
        "assert_message_safe": message_safe,
        "assert_standalone_statement": standalone_statement,
    }
    if not direct_entrypoint_call:
        return guards, "assert_not_direct_entrypoint_selftest"
    if not expression_calls_safe:
        return guards, "assert_has_external_or_side_effectful_call"
    if not expression_names_safe:
        return guards, "assert_depends_on_external_state"
    if not literal_call_arguments:
        return guards, "assert_call_arguments_not_literal"
    if not expression_shape_safe:
        return guards, "assert_expression_shape_ambiguous"
    if not message_safe:
        return guards, "assert_message_depends_on_external_state"
    if not standalone_statement:
        return guards, "assert_not_standalone"
    return guards, None


def _function_segment_hashes(source: str, tree: ast.Module) -> list[tuple[str, str]]:
    segments: list[tuple[str, str]] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            segment = ast.get_source_segment(source, node)
            if segment is None:
                return []
            segments.append((node.name, _sha256_text(segment)))
    return segments


def _quarantine_source(source: str, assertion: ast.Assert) -> str | None:
    if assertion.end_lineno is None:
        return None
    lines = source.splitlines(keepends=True)
    start = assertion.lineno - 1
    end = assertion.end_lineno
    if start < 0 or end > len(lines):
        return None

    first_line = lines[start]
    if first_line[: assertion.col_offset].strip():
        return None
    if assertion.end_lineno == assertion.lineno and assertion.end_col_offset is not None:
        line_without_newline = first_line.rstrip("\r\n")
        trailing = line_without_newline[assertion.end_col_offset :].strip()
        if trailing and not trailing.startswith("#"):
            return None

    newline = "\r\n" if "\r\n" in source else "\n"
    assert_lines = lines[start:end]
    guarded = [f'if __name__ == "__main__":{newline}']
    guarded.extend("    " + line for line in assert_lines)
    return "".join(lines[:start] + guarded + lines[end:])


def quarantine_module_assert_entrypoint_selftest(
    source: str,
    entry_point: str,
    *,
    extraction_unambiguous: bool | None,
    source_complete: bool | None,
) -> H2Decision:
    """Apply H2 when every structural and provenance guard is satisfied.

    ``extraction_unambiguous`` and ``source_complete`` are mandatory provenance
    facts.  ``None`` is treated as unknown and therefore abstains.
    """

    base_guards = {
        "extraction_unambiguous": extraction_unambiguous is True,
        "source_complete": source_complete is True,
        "source_parseable": False,
        "entrypoint_unique": False,
        "exactly_one_module_assert": False,
        "output_parseable": False,
        "function_segments_unchanged": False,
    }
    if not isinstance(source, str) or not source.strip():
        return _decision(
            source if isinstance(source, str) else "",
            triggered=False,
            transformed=False,
            reason="empty_or_invalid_source",
            module_assert_count=0,
            entrypoint_status="unknown",
            guard_results=base_guards,
        )
    if not isinstance(entry_point, str) or not entry_point.isidentifier():
        return _decision(
            source,
            triggered=False,
            transformed=False,
            reason="invalid_entry_point",
            module_assert_count=0,
            entrypoint_status="invalid",
            guard_results=base_guards,
        )
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return _decision(
            source,
            triggered=False,
            transformed=False,
            reason="source_unparseable",
            module_assert_count=0,
            entrypoint_status="unparseable",
            guard_results=base_guards,
        )

    base_guards["source_parseable"] = True
    module_asserts = [node for node in tree.body if isinstance(node, ast.Assert)]
    triggered = bool(module_asserts)
    entry_status, _ = _entrypoint_status(tree, entry_point)
    base_guards["entrypoint_unique"] = entry_status == "unique"
    base_guards["exactly_one_module_assert"] = len(module_asserts) == 1

    if extraction_unambiguous is not True:
        return _decision(
            source,
            triggered=triggered,
            transformed=False,
            reason="extraction_ambiguous_or_unknown",
            module_assert_count=len(module_asserts),
            entrypoint_status=entry_status,
            guard_results=base_guards,
        )
    if entry_status != "unique":
        return _decision(
            source,
            triggered=triggered,
            transformed=False,
            reason=f"entry_point_{entry_status}",
            module_assert_count=len(module_asserts),
            entrypoint_status=entry_status,
            guard_results=base_guards,
        )
    if source_complete is not True:
        return _decision(
            source,
            triggered=triggered,
            transformed=False,
            reason="source_truncated_or_completion_unknown",
            module_assert_count=len(module_asserts),
            entrypoint_status=entry_status,
            guard_results=base_guards,
        )
    if len(module_asserts) != 1:
        reason = (
            "no_module_level_assert"
            if not module_asserts
            else "module_assert_count_not_one"
        )
        return _decision(
            source,
            triggered=triggered,
            transformed=False,
            reason=reason,
            module_assert_count=len(module_asserts),
            entrypoint_status=entry_status,
            guard_results=base_guards,
        )

    assertion = module_asserts[0]
    selftest_guards, failure_reason = _selftest_guards(assertion, entry_point)
    all_guards = {**base_guards, **selftest_guards}
    if failure_reason is not None:
        return _decision(
            source,
            triggered=True,
            transformed=False,
            reason=failure_reason,
            module_assert_count=1,
            entrypoint_status=entry_status,
            guard_results=all_guards,
        )

    output = _quarantine_source(source, assertion)
    if output is None:
        return _decision(
            source,
            triggered=True,
            transformed=False,
            reason="source_rewrite_boundary_ambiguous",
            module_assert_count=1,
            entrypoint_status=entry_status,
            guard_results=all_guards,
        )
    try:
        output_tree = ast.parse(output)
    except SyntaxError:
        return _decision(
            source,
            triggered=True,
            transformed=False,
            reason="output_unparseable",
            module_assert_count=1,
            entrypoint_status=entry_status,
            guard_results=all_guards,
        )

    all_guards["output_parseable"] = True
    all_guards["function_segments_unchanged"] = (
        _function_segment_hashes(source, tree)
        == _function_segment_hashes(output, output_tree)
    )
    output_module_asserts = [
        node for node in output_tree.body if isinstance(node, ast.Assert)
    ]
    all_guards["module_assert_removed_from_top_level"] = not output_module_asserts
    if not all_guards["function_segments_unchanged"]:
        return _decision(
            source,
            triggered=True,
            transformed=False,
            reason="function_content_change_detected",
            module_assert_count=1,
            entrypoint_status=entry_status,
            guard_results=all_guards,
        )
    if output_module_asserts:
        return _decision(
            source,
            triggered=True,
            transformed=False,
            reason="module_assert_still_top_level",
            module_assert_count=1,
            entrypoint_status=entry_status,
            guard_results=all_guards,
        )
    return _decision(
        source,
        triggered=True,
        transformed=True,
        reason="transformed_module_assert_quarantined",
        module_assert_count=1,
        entrypoint_status=entry_status,
        guard_results=all_guards,
        output_source=output,
    )


__all__ = [
    "H2Decision",
    "RULE_ID",
    "RULE_STATUS",
    "quarantine_module_assert_entrypoint_selftest",
]
