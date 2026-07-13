"""Narrow, deterministic AST repairs for frozen Math output contracts."""
from __future__ import annotations

import ast
import hashlib
from dataclasses import dataclass

from agent_tools.finals_rebuild.math_task_schema import MathOutputContract


RATIONAL_LITERAL_DIVISION_RULE_ID = "rational_literal_division_to_fraction"


@dataclass(frozen=True)
class MathSpecRepairResult:
    rule_id: str
    triggered: bool
    changed: bool
    code_before: str
    code_after: str
    before_hash: str
    after_hash: str
    reason: str


def _hash(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def _result(code: str, *, triggered: bool, changed: bool, reason: str, after: str | None = None) -> MathSpecRepairResult:
    code_after = code if after is None else after
    return MathSpecRepairResult(
        rule_id=RATIONAL_LITERAL_DIVISION_RULE_ID,
        triggered=triggered,
        changed=changed,
        code_before=code,
        code_after=code_after,
        before_hash=_hash(code),
        after_hash=_hash(code_after),
        reason=reason,
    )


def _literal_integer(node: ast.AST) -> tuple[bool, int | None]:
    if isinstance(node, ast.Constant) and isinstance(node.value, int) and not isinstance(node.value, bool):
        return True, node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        ok, value = _literal_integer(node.operand)
        if ok and value is not None:
            return True, value if isinstance(node.op, ast.UAdd) else -value
    return False, None


def _has_fraction_conflict(tree: ast.Module) -> bool:
    """Reject any binding of ``Fraction`` other than its canonical import."""
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == "Fraction" and not (node.module == "fractions" and alias.asname is None):
                    return True
        elif isinstance(node, ast.Import):
            if any(alias.asname == "Fraction" for alias in node.names):
                return True
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name == "Fraction":
            return True
        elif isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)) and node.id == "Fraction":
            return True
        elif isinstance(node, ast.arg) and node.arg == "Fraction":
            return True
    return False


def _has_canonical_import(tree: ast.Module) -> bool:
    return any(
        isinstance(node, ast.ImportFrom)
        and node.module == "fractions"
        and any(alias.name == "Fraction" and alias.asname is None for alias in node.names)
        for node in tree.body
    )


def _insert_fraction_import(tree: ast.Module) -> None:
    index = 0
    if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant) and isinstance(tree.body[0].value.value, str):
        index = 1
    while index < len(tree.body):
        node = tree.body[index]
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            index += 1
        else:
            break
    tree.body.insert(index, ast.ImportFrom(module="fractions", names=[ast.alias(name="Fraction")], level=0))


def repair_rational_literal_division(code: str, contract: MathOutputContract) -> MathSpecRepairResult:
    """Convert one safe ``return <int> / <int>`` to ``Fraction``.

    The deliberately strict shape check avoids altering branches, calculations,
    dynamically-derived values, or any code with a potentially shadowed
    ``Fraction`` binding.
    """
    if not (
        contract.answer_type == "rational"
        and contract.python_return_type == "Fraction"
        and contract.representation_policy == "exact_answer_type"
    ):
        return _result(code, triggered=False, changed=False, reason="contract_not_applicable")
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return _result(code, triggered=False, changed=False, reason="parse_error")

    solves = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "solve"]
    if not solves:
        return _result(code, triggered=False, changed=False, reason="solve_not_found")
    if len(solves) != 1:
        return _result(code, triggered=False, changed=False, reason="multiple_solve_functions")
    solve = solves[0]
    if isinstance(solve, ast.AsyncFunctionDef) or solve.args.posonlyargs or solve.args.args or solve.args.kwonlyargs or solve.args.vararg or solve.args.kwarg:
        return _result(code, triggered=False, changed=False, reason="invalid_solve_signature")
    if len(solve.body) != 1 or not isinstance(solve.body[0], ast.Return) or solve.body[0].value is None:
        return _result(code, triggered=False, changed=False, reason="unsupported_return_structure")
    value = solve.body[0].value
    if _has_fraction_conflict(tree):
        return _result(code, triggered=False, changed=False, reason="fraction_name_conflict")
    if isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id == "Fraction":
        return _result(code, triggered=False, changed=False, reason="already_compliant")
    if not isinstance(value, ast.BinOp) or not isinstance(value.op, ast.Div):
        return _result(code, triggered=False, changed=False, reason="unsupported_expression")
    numerator_ok, _ = _literal_integer(value.left)
    denominator_ok, denominator = _literal_integer(value.right)
    if not numerator_ok or not denominator_ok:
        return _result(code, triggered=False, changed=False, reason="unsupported_expression")
    if denominator == 0:
        return _result(code, triggered=False, changed=False, reason="zero_denominator")
    solve.body[0].value = ast.Call(
        func=ast.Name(id="Fraction", ctx=ast.Load()),
        args=[value.left, value.right],
        keywords=[],
    )
    if not _has_canonical_import(tree):
        _insert_fraction_import(tree)
    ast.fix_missing_locations(tree)
    return _result(code, triggered=True, changed=True, reason="repaired", after=ast.unparse(tree) + "\n")
