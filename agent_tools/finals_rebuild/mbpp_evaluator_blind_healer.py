"""Development-only evaluator-blind MBPP+ Healer candidate.

This module consumes the frozen Pipeline-normalized source.  It deliberately
does not accept a treatment label, evaluator result, or test result: the same
rule order and guards therefore apply to P0 and Scaffold-conditioned output.
"""

from __future__ import annotations

import ast
import hashlib
from dataclasses import dataclass
from typing import Iterable


CANDIDATE_ID = "mbpp_evaluator_blind_healer_candidate_v0"
CANDIDATE_STATUS = "development_candidate_not_frozen"
RULE_ID = "entrypoint_alias_unique_arity_compatible_v0"
RULE_ORDER = (RULE_ID,)


@dataclass(frozen=True)
class HealerResult:
    """Deterministic result of applying the development-only candidate."""

    status: str
    output_source: str | None
    input_sha256: str | None
    output_sha256: str | None
    triggered_rule_ids: tuple[str, ...]
    applied_rule_ids: tuple[str, ...]
    diagnostic: str
    ast_prefix_preserved: bool


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class _ModuleBindingVisitor(ast.NodeVisitor):
    """Collect module bindings while excluding function/class local scopes."""

    def __init__(self) -> None:
        self.names: set[str] = set()

    def _target(self, node: ast.AST) -> None:
        if isinstance(node, ast.Name):
            self.names.add(node.id)
        elif isinstance(node, (ast.Tuple, ast.List)):
            for element in node.elts:
                self._target(element)
        elif isinstance(node, ast.Starred):
            self._target(node.value)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        self.names.add(node.name)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        self.names.add(node.name)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: N802
        self.names.add(node.name)

    def visit_Name(self, node: ast.Name) -> None:  # noqa: N802
        if isinstance(node.ctx, ast.Store):
            self.names.add(node.id)

    def visit_Import(self, node: ast.Import) -> None:  # noqa: N802
        for alias in node.names:
            self.names.add(alias.asname or alias.name.split(".")[0])

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: N802
        for alias in node.names:
            self.names.add(alias.asname or alias.name)


def _module_bound_names(tree: ast.Module) -> set[str]:
    visitor = _ModuleBindingVisitor()
    for statement in tree.body:
        visitor.visit(statement)
    return visitor.names


def _accepts_arity(function: ast.FunctionDef, arity: int) -> bool:
    args = function.args
    positional = len(args.posonlyargs) + len(args.args)
    required = positional - len(args.defaults)
    required_kwonly = sum(default is None for default in args.kw_defaults)
    return (
        required_kwonly == 0
        and arity >= required
        and (args.vararg is not None or arity <= positional)
    )


def _unchanged(source: str | None, status: str, diagnostic: str) -> HealerResult:
    digest = _sha256_text(source) if source is not None else None
    return HealerResult(
        status=status,
        output_source=source,
        input_sha256=digest,
        output_sha256=digest,
        triggered_rule_ids=(),
        applied_rule_ids=(),
        diagnostic=diagnostic,
        ast_prefix_preserved=False,
    )


def apply_healer(
    normalized_source: str | None,
    expected_entry_point: str,
    expected_positional_arities: Iterable[int],
    generation_truncated: bool,
) -> HealerResult:
    """Apply the fixed candidate to Pipeline-normalized source.

    The expected name and arities are model-visible prompt contract metadata,
    not oracle answers or evaluator feedback.  Unsafe or ambiguous cases are
    returned unchanged with ``status == "abstained"``.
    """

    if normalized_source is None:
        return _unchanged(None, "abstained", "pipeline_output_unavailable")
    if generation_truncated:
        return _unchanged(normalized_source, "abstained", "generation_truncated")
    if not expected_entry_point.isidentifier():
        return _unchanged(normalized_source, "abstained", "invalid_expected_entry_point")

    arities = tuple(sorted(set(expected_positional_arities)))
    if not arities or any(not isinstance(arity, int) or arity < 0 for arity in arities):
        return _unchanged(normalized_source, "abstained", "missing_or_invalid_arity_evidence")

    try:
        original_tree = ast.parse(normalized_source)
    except (SyntaxError, ValueError, OverflowError):
        return _unchanged(normalized_source, "abstained", "syntax_parse_failure")

    top_level_functions = [
        node for node in original_tree.body if isinstance(node, ast.FunctionDef)
    ]
    if any(function.name == expected_entry_point for function in top_level_functions):
        return _unchanged(normalized_source, "no_trigger", "expected_entry_point_present")
    if expected_entry_point in _module_bound_names(original_tree):
        return _unchanged(normalized_source, "abstained", "target_name_already_bound")
    if any(isinstance(node, ast.AsyncFunctionDef) for node in original_tree.body):
        return _unchanged(normalized_source, "abstained", "async_function_ambiguity")
    if len(top_level_functions) != 1:
        return _unchanged(normalized_source, "abstained", "top_level_function_count_not_one")

    function = top_level_functions[0]
    if function.decorator_list:
        return _unchanged(normalized_source, "abstained", "decorated_function")
    if not all(_accepts_arity(function, arity) for arity in arities):
        return _unchanged(normalized_source, "abstained", "positional_arity_incompatible")

    transformed = (
        normalized_source.rstrip()
        + "\n\n"
        + f"{expected_entry_point} = {function.name}\n"
    )
    try:
        transformed_tree = ast.parse(transformed)
        compile(transformed, "<mbpp-healer-candidate>", "exec")
    except (SyntaxError, ValueError, OverflowError):
        return _unchanged(normalized_source, "abstained", "post_transform_validation_failure")

    prefix_preserved = (
        len(transformed_tree.body) == len(original_tree.body) + 1
        and ast.dump(ast.Module(body=transformed_tree.body[:-1], type_ignores=[]), include_attributes=False)
        == ast.dump(original_tree, include_attributes=False)
    )
    last = transformed_tree.body[-1]
    alias_shape_valid = (
        isinstance(last, ast.Assign)
        and len(last.targets) == 1
        and isinstance(last.targets[0], ast.Name)
        and last.targets[0].id == expected_entry_point
        and isinstance(last.value, ast.Name)
        and last.value.id == function.name
    )
    if not prefix_preserved or not alias_shape_valid:
        return _unchanged(normalized_source, "abstained", "ast_diff_budget_violation")

    return HealerResult(
        status="transformed",
        output_source=transformed,
        input_sha256=_sha256_text(normalized_source),
        output_sha256=_sha256_text(transformed),
        triggered_rule_ids=RULE_ORDER,
        applied_rule_ids=RULE_ORDER,
        diagnostic="unique_undecorated_sync_function_arity_compatible_alias_appended",
        ast_prefix_preserved=True,
    )
