"""Guarded quarantine for one literal-only top-level demo ``print``.

This rule is independent from H1 and H2.  It uses no evaluator outcome,
hidden test, canonical solution, task ID, or candidate execution.  It moves
only a narrowly recognized public-self-test-adjacent ``print`` behind
``if __name__ == "__main__":`` and leaves an adjacent Assert untouched for
the separately governed H2 rule.
"""

from __future__ import annotations

import ast
import hashlib
from dataclasses import asdict, dataclass
from typing import Any, Iterable


RULE_ID = "top_level_literal_only_demo_print_quarantine_v0"
RULE_STATUS = "development_candidate_not_frozen"


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def assert_fingerprint(assertion: ast.Assert) -> str:
    """Return a location-independent fingerprint for a public Assert."""
    return hashlib.sha256(
        ast.dump(assertion, annotate_fields=True, include_attributes=False).encode(
            "utf-8"
        )
    ).hexdigest()


@dataclass(frozen=True)
class DemoPrintDecision:
    rule_id: str
    rule_status: str
    triggered: bool
    transformed: bool
    abstained: bool
    reason: str
    entrypoint_status: str
    top_level_print_count: int
    top_level_assert_count: int
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
    entrypoint_status: str,
    top_level_print_count: int,
    top_level_assert_count: int,
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
        entrypoint_status=entrypoint_status,
        top_level_print_count=top_level_print_count,
        top_level_assert_count=top_level_assert_count,
        guard_results=dict(sorted(guard_results.items())),
        source_sha256=_sha256_text(source),
        output_sha256=_sha256_text(output),
        output_source=output,
        claim="top_level_demo_print_quarantined_only_no_correctness_claim",
    )


def _entrypoint_status(tree: ast.Module, entry_point: str) -> str:
    count = sum(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == entry_point
        for node in tree.body
    )
    if count == 1:
        return "unique"
    if count == 0:
        return "missing"
    return "multiple"


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


def _assert_is_literal_entrypoint_selftest(
    assertion: ast.Assert, entry_point: str
) -> bool:
    calls = [node for node in ast.walk(assertion.test) if isinstance(node, ast.Call)]
    entry_calls = [
        node
        for node in calls
        if isinstance(node.func, ast.Name) and node.func.id == entry_point
    ]
    names = {
        node.id for node in ast.walk(assertion.test) if isinstance(node, ast.Name)
    }
    if len(entry_calls) != 1 or not names <= {entry_point, "abs"}:
        return False
    if not all(
        isinstance(call.func, ast.Name)
        and call.func.id in {entry_point, "abs"}
        and (
            call.func.id != "abs"
            or (len(call.args) == 1 and not call.keywords)
        )
        for call in calls
    ):
        return False
    return all(
        all(_is_literal(argument) for argument in call.args)
        and all(
            keyword.arg is not None and _is_literal(keyword.value)
            for keyword in call.keywords
        )
        for call in entry_calls
    )


def _print_is_safe(call: ast.Call, entry_point: str) -> bool:
    if not isinstance(call.func, ast.Name) or call.func.id != "print":
        return False
    for argument in call.args:
        if _is_literal(argument):
            continue
        if not (
            isinstance(argument, ast.Call)
            and isinstance(argument.func, ast.Name)
            and argument.func.id == entry_point
            and all(_is_literal(item) for item in argument.args)
            and all(
                keyword.arg is not None and _is_literal(keyword.value)
                for keyword in argument.keywords
            )
        ):
            return False
    return all(
        keyword.arg is not None and _is_literal(keyword.value)
        for keyword in call.keywords
    )


def _is_main_guard(statement: ast.stmt) -> bool:
    return (
        isinstance(statement, ast.If)
        and isinstance(statement.test, ast.Compare)
        and isinstance(statement.test.left, ast.Name)
        and statement.test.left.id == "__name__"
        and len(statement.test.ops) == 1
        and isinstance(statement.test.ops[0], ast.Eq)
        and len(statement.test.comparators) == 1
        and isinstance(statement.test.comparators[0], ast.Constant)
        and statement.test.comparators[0].value == "__main__"
    )


class _ExecutableCallFinder(ast.NodeVisitor):
    """Find calls evaluated at module load without entering deferred bodies."""

    def __init__(self) -> None:
        self.calls: list[ast.Call] = []

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        self.calls.append(node)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        for decorator in node.decorator_list:
            self.visit(decorator)
        for default in [*node.args.defaults, *node.args.kw_defaults]:
            if default is not None:
                self.visit(default)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        self.visit_FunctionDef(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: N802
        for decorator in node.decorator_list:
            self.visit(decorator)
        for base in node.bases:
            self.visit(base)
        for keyword in node.keywords:
            self.visit(keyword.value)

    def visit_Lambda(self, node: ast.Lambda) -> None:  # noqa: N802
        for default in [*node.args.defaults, *node.args.kw_defaults]:
            if default is not None:
                self.visit(default)


def _unclassified_top_level_call_count(
    tree: ast.Module, target_print: ast.Expr, public_assert: ast.Assert
) -> int:
    count = 0
    for statement in tree.body:
        if statement is target_print or statement is public_assert:
            continue
        if _is_main_guard(statement):
            continue
        finder = _ExecutableCallFinder()
        finder.visit(statement)
        count += len(finder.calls)
    return count


def _function_segment_hashes(source: str, tree: ast.Module) -> list[tuple[str, str]]:
    segments: list[tuple[str, str]] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            segment = ast.get_source_segment(source, node)
            if segment is None:
                return []
            segments.append((node.name, _sha256_text(segment)))
    return segments


def _quarantine_source(source: str, statement: ast.Expr) -> str | None:
    if statement.end_lineno is None:
        return None
    lines = source.splitlines(keepends=True)
    start = statement.lineno - 1
    end = statement.end_lineno
    if start < 0 or end > len(lines):
        return None
    first_line = lines[start]
    if first_line[: statement.col_offset].strip():
        return None
    newline = "\r\n" if "\r\n" in source else "\n"
    statement_lines = lines[start:end]
    guarded = [f'if __name__ == "__main__":{newline}']
    guarded.extend("    " + line for line in statement_lines)
    return "".join(lines[:start] + guarded + lines[end:])


def quarantine_top_level_literal_only_demo_print(
    source: str,
    entry_point: str,
    *,
    extraction_unambiguous: bool | None,
    source_complete: bool | None,
    public_assert_fingerprints: Iterable[str],
) -> DemoPrintDecision:
    """Apply the demo-print quarantine only when every guard is satisfied."""
    base_guards = {
        "extraction_unambiguous": extraction_unambiguous is True,
        "source_complete": source_complete is True,
        "source_parseable": False,
        "entrypoint_unique": False,
        "exactly_one_top_level_print": False,
        "exactly_one_top_level_assert": False,
        "print_adjacent_to_assert": False,
        "assert_matches_public_selftest": False,
        "assert_literal_entrypoint_selftest": False,
        "print_arguments_safe": False,
        "builtin_print_unshadowed": False,
        "no_other_unclassified_top_level_calls": False,
        "output_parseable": False,
        "function_segments_unchanged": False,
        "assert_remains_top_level": False,
        "print_removed_from_top_level": False,
    }
    if not isinstance(source, str) or not source.strip():
        return _decision(
            source if isinstance(source, str) else "",
            triggered=False,
            transformed=False,
            reason="empty_or_invalid_source",
            entrypoint_status="unknown",
            top_level_print_count=0,
            top_level_assert_count=0,
            guard_results=base_guards,
        )
    if not isinstance(entry_point, str) or not entry_point.isidentifier():
        return _decision(
            source,
            triggered=False,
            transformed=False,
            reason="invalid_entry_point",
            entrypoint_status="invalid",
            top_level_print_count=0,
            top_level_assert_count=0,
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
            entrypoint_status="unparseable",
            top_level_print_count=0,
            top_level_assert_count=0,
            guard_results=base_guards,
        )
    base_guards["source_parseable"] = True
    entry_status = _entrypoint_status(tree, entry_point)
    base_guards["entrypoint_unique"] = entry_status == "unique"
    print_statements = [
        node
        for node in tree.body
        if isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == "print"
    ]
    assertions = [node for node in tree.body if isinstance(node, ast.Assert)]
    triggered = bool(print_statements)
    base_guards["exactly_one_top_level_print"] = len(print_statements) == 1
    base_guards["exactly_one_top_level_assert"] = len(assertions) == 1

    common = {
        "triggered": triggered,
        "transformed": False,
        "entrypoint_status": entry_status,
        "top_level_print_count": len(print_statements),
        "top_level_assert_count": len(assertions),
        "guard_results": base_guards,
    }
    if extraction_unambiguous is not True:
        return _decision(source, reason="extraction_ambiguous_or_unknown", **common)
    if source_complete is not True:
        return _decision(source, reason="source_truncated_or_completion_unknown", **common)
    if entry_status != "unique":
        return _decision(source, reason=f"entry_point_{entry_status}", **common)
    if len(print_statements) != 1:
        reason = "no_top_level_print" if not print_statements else "top_level_print_count_not_one"
        return _decision(source, reason=reason, **common)
    if len(assertions) != 1:
        reason = "no_top_level_assert" if not assertions else "top_level_assert_count_not_one"
        return _decision(source, reason=reason, **common)

    print_statement = print_statements[0]
    assertion = assertions[0]
    print_index = tree.body.index(print_statement)
    assert_index = tree.body.index(assertion)
    base_guards["print_adjacent_to_assert"] = abs(print_index - assert_index) == 1
    public_fingerprints = {
        value for value in public_assert_fingerprints if isinstance(value, str)
    }
    base_guards["assert_matches_public_selftest"] = (
        assert_fingerprint(assertion) in public_fingerprints
    )
    base_guards["assert_literal_entrypoint_selftest"] = (
        _assert_is_literal_entrypoint_selftest(assertion, entry_point)
    )
    base_guards["print_arguments_safe"] = _print_is_safe(
        print_statement.value, entry_point
    )
    module_bound_print = any(
        (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and node.name == "print"
        )
        or (
            isinstance(node, (ast.Import, ast.ImportFrom))
            and any((alias.asname or alias.name.split(".")[-1]) == "print" for alias in node.names)
        )
        or (
            isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "print" for target in node.targets)
        )
        for node in tree.body
    )
    base_guards["builtin_print_unshadowed"] = not module_bound_print
    base_guards["no_other_unclassified_top_level_calls"] = (
        _unclassified_top_level_call_count(tree, print_statement, assertion) == 0
    )
    guard_reason_order = [
        ("print_adjacent_to_assert", "print_not_adjacent_to_public_selftest"),
        ("assert_matches_public_selftest", "adjacent_assert_not_in_public_prompt"),
        ("assert_literal_entrypoint_selftest", "assert_not_literal_entrypoint_selftest"),
        ("print_arguments_safe", "print_arguments_not_literal_or_entrypoint_literal_call"),
        ("builtin_print_unshadowed", "print_name_shadowed"),
        (
            "no_other_unclassified_top_level_calls",
            "other_unclassified_top_level_call_present",
        ),
    ]
    for guard, reason in guard_reason_order:
        if not base_guards[guard]:
            return _decision(source, reason=reason, **common)

    output = _quarantine_source(source, print_statement)
    if output is None:
        return _decision(source, reason="source_rewrite_boundary_ambiguous", **common)
    try:
        output_tree = ast.parse(output)
    except SyntaxError:
        return _decision(source, reason="output_unparseable", **common)
    base_guards["output_parseable"] = True
    base_guards["function_segments_unchanged"] = (
        _function_segment_hashes(source, tree)
        == _function_segment_hashes(output, output_tree)
    )
    base_guards["assert_remains_top_level"] = (
        sum(isinstance(node, ast.Assert) for node in output_tree.body) == 1
    )
    base_guards["print_removed_from_top_level"] = not any(
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == "print"
        for node in output_tree.body
    )
    for guard, reason in [
        ("function_segments_unchanged", "function_content_change_detected"),
        ("assert_remains_top_level", "h2_assert_boundary_changed"),
        ("print_removed_from_top_level", "print_still_top_level"),
    ]:
        if not base_guards[guard]:
            return _decision(source, reason=reason, **common)
    return _decision(
        source,
        triggered=True,
        transformed=True,
        reason="transformed_top_level_demo_print_quarantined",
        entrypoint_status=entry_status,
        top_level_print_count=1,
        top_level_assert_count=1,
        guard_results=base_guards,
        output_source=output,
    )


__all__ = [
    "DemoPrintDecision",
    "RULE_ID",
    "RULE_STATUS",
    "assert_fingerprint",
    "quarantine_top_level_literal_only_demo_print",
]
