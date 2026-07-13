"""
Math answer validator (v1).

Separates mathematical_equivalence from representation_compliance.
Does not execute arbitrary Python, call models, or recompute answers
from problem text.
"""

from __future__ import annotations

import ast
import math
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, Callable, Dict, Optional, Sequence, Set, Tuple, Union

from agent_tools.finals_rebuild.math_task_schema import MathOutputContract

DEFAULT_FLOAT_TOLERANCE = 1e-9

STATUS_SUCCESS = "success"
STATUS_FAILED = "failed"
STATUS_ERROR = "error"

ERROR_INVALID_TYPE = "invalid_type"
ERROR_PARSE_ERROR = "parse_error"
ERROR_AMBIGUOUS_OUTPUT = "ambiguous_output"
ERROR_NON_FINITE_VALUE = "non_finite_value"
ERROR_WRONG_FIELD = "wrong_field"
ERROR_MISSING_FIELD = "missing_field"
ERROR_EXTRA_FIELD = "extra_field"
ERROR_OUT_OF_TOLERANCE = "out_of_tolerance"
ERROR_NOT_EQUIVALENT = "not_equivalent"
ERROR_UNDECLARED_SYMBOL = "undeclared_symbol"
ERROR_UNSUPPORTED_CONTRACT = "unsupported_contract"
ERROR_VALIDATOR_ERROR = "validator_error"

_ALLOWED_SYMBOLIC_BINOPS = (
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Pow,
)
_ALLOWED_SYMBOLIC_UNARYOPS = (ast.UAdd, ast.USub)


class MathValidatorError(Exception):
    """Internal validator failure; never leaks to callers."""


@dataclass(frozen=True)
class ValidationResult:
    status: str
    is_correct: bool
    mathematical_equivalence: bool
    representation_compliance: bool
    canonical_actual: Any
    canonical_reference: Any
    error_code: Optional[str]
    details: Dict[str, Any] = field(default_factory=dict)


def validate_answer(
    actual: Any,
    reference: Any,
    contract: MathOutputContract,
) -> ValidationResult:
    """Validate *actual* against frozen *reference* under *contract*."""
    try:
        dispatchers: Dict[str, Callable[[Any, Any, MathOutputContract], ValidationResult]] = {
            "number": _validate_number,
            "rational": _validate_rational,
            "symbolic_expression": _validate_symbolic_expression,
            "coordinate_pair": _validate_coordinate_pair,
            "multi_field_answer": _validate_multi_field_answer,
        }
        handler = dispatchers.get(contract.answer_type)
        if handler is None:
            return _error_result(
                ERROR_UNSUPPORTED_CONTRACT,
                {"answer_type": contract.answer_type},
            )
        return handler(actual, reference, contract)
    except MathValidatorError as exc:
        return _error_result(ERROR_VALIDATOR_ERROR, {"message": str(exc)})
    except Exception:
        return _error_result(ERROR_VALIDATOR_ERROR, {})


def _error_result(
    error_code: str,
    details: Dict[str, Any],
    *,
    canonical_actual: Any = None,
    canonical_reference: Any = None,
    mathematical_equivalence: bool = False,
    representation_compliance: bool = False,
) -> ValidationResult:
    return ValidationResult(
        status=STATUS_ERROR,
        is_correct=False,
        mathematical_equivalence=mathematical_equivalence,
        representation_compliance=representation_compliance,
        canonical_actual=canonical_actual,
        canonical_reference=canonical_reference,
        error_code=error_code,
        details=dict(details),
    )


def _final_result(
    *,
    mathematical_equivalence: bool,
    representation_compliance: bool,
    canonical_actual: Any,
    canonical_reference: Any,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> ValidationResult:
    is_correct = mathematical_equivalence and representation_compliance
    status = STATUS_SUCCESS if is_correct else STATUS_FAILED
    return ValidationResult(
        status=status,
        is_correct=is_correct,
        mathematical_equivalence=mathematical_equivalence,
        representation_compliance=representation_compliance,
        canonical_actual=canonical_actual,
        canonical_reference=canonical_reference,
        error_code=error_code,
        details=dict(details or {}),
    )


def _tolerance(contract: MathOutputContract) -> float:
    if contract.allowed_tolerance is None:
        return DEFAULT_FLOAT_TOLERANCE
    return float(contract.allowed_tolerance)


def _semantic_only(contract: MathOutputContract) -> bool:
    return contract.representation_policy == "semantic_only"


def _reject_bool(value: Any) -> bool:
    return isinstance(value, bool)


def _is_finite_number(value: Union[int, float]) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    return False


def _numbers_equivalent(
    actual: Union[int, float],
    reference: Union[int, float],
    *,
    tolerance: float,
) -> bool:
    return abs(float(actual) - float(reference)) <= tolerance


def _canonical_number_reference(
    reference: Any,
    *,
    python_return_type: str,
) -> Union[int, float]:
    if _reject_bool(reference):
        raise MathValidatorError("reference bool rejected")
    if python_return_type == "int":
        if isinstance(reference, int):
            return reference
        if isinstance(reference, float) and reference.is_integer():
            return int(reference)
        raise MathValidatorError("invalid reference for int number")
    if python_return_type == "float":
        if isinstance(reference, (int, float)) and _is_finite_number(reference):
            return float(reference)
        raise MathValidatorError("invalid reference for float number")
    raise MathValidatorError("unsupported number return type")


def _parse_numeric_value(actual: Any) -> Tuple[Optional[Union[int, float]], Optional[str]]:
    if _reject_bool(actual):
        return None, ERROR_INVALID_TYPE
    if isinstance(actual, int):
        return actual, None
    if isinstance(actual, float):
        if not math.isfinite(actual):
            return None, ERROR_NON_FINITE_VALUE
        return actual, None
    return None, ERROR_INVALID_TYPE


def _parse_actual_number(
    actual: Any,
    *,
    contract: MathOutputContract,
) -> Tuple[Optional[Union[int, float]], bool, Optional[str]]:
    parsed, error = _parse_numeric_value(actual)
    if parsed is None:
        return None, False, error
    return parsed, True, None


def _number_representation_compliance(
    actual: Any,
    *,
    contract: MathOutputContract,
) -> bool:
    if _semantic_only(contract):
        if _reject_bool(actual):
            return False
        if isinstance(actual, int):
            return True
        if isinstance(actual, float):
            return _is_finite_number(actual)
        return False
    if contract.python_return_type == "int":
        return isinstance(actual, int) and not _reject_bool(actual)
    if contract.python_return_type == "float":
        return isinstance(actual, float) and _is_finite_number(actual)
    return False


def _validate_number(
    actual: Any,
    reference: Any,
    contract: MathOutputContract,
) -> ValidationResult:
    try:
        canonical_reference = _canonical_number_reference(
            reference,
            python_return_type=contract.python_return_type,
        )
    except MathValidatorError:
        return _error_result(ERROR_VALIDATOR_ERROR, {"field": "reference"})

    parsed, parse_ok, parse_error = _parse_actual_number(actual, contract=contract)
    if not parse_ok or parsed is None:
        return _error_result(
            parse_error or ERROR_INVALID_TYPE,
            {"actual_type": type(actual).__name__},
        )

    representation_ok = _number_representation_compliance(actual, contract=contract)
    tolerance = _tolerance(contract)

    if contract.python_return_type == "int" and isinstance(canonical_reference, int):
        if isinstance(parsed, int):
            math_ok = parsed == canonical_reference
            canonical_actual: Union[int, float] = parsed
        else:
            math_ok = _numbers_equivalent(parsed, canonical_reference, tolerance=tolerance)
            canonical_actual = parsed
    else:
        math_ok = _numbers_equivalent(
            parsed,
            canonical_reference,
            tolerance=tolerance,
        )
        canonical_actual = float(parsed) if isinstance(parsed, int) else parsed

    error_code = None
    details: Dict[str, Any] = {}
    if not math_ok:
        error_code = ERROR_NOT_EQUIVALENT
    elif not representation_ok:
        error_code = ERROR_INVALID_TYPE

    return _final_result(
        mathematical_equivalence=math_ok,
        representation_compliance=representation_ok,
        canonical_actual=canonical_actual,
        canonical_reference=canonical_reference,
        error_code=error_code,
        details=details,
    )


def _canonical_fraction(value: Any) -> Fraction:
    if isinstance(value, Fraction):
        if value.denominator == 0:
            raise MathValidatorError("zero denominator")
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return Fraction(value, 1)
    if isinstance(value, dict):
        numerator = value.get("numerator")
        denominator = value.get("denominator")
        if isinstance(numerator, int) and isinstance(denominator, int):
            frac = Fraction(numerator, denominator)
            if frac.denominator == 0:
                raise MathValidatorError("zero denominator")
            return frac
    if isinstance(value, str):
        frac = Fraction(value)
        if frac.denominator == 0:
            raise MathValidatorError("zero denominator")
        return frac
    raise MathValidatorError("invalid rational reference")


def _parse_actual_rational(
    actual: Any,
    *,
    contract: MathOutputContract,
) -> Tuple[Optional[Fraction], bool, Optional[str]]:
    if _reject_bool(actual):
        return None, False, ERROR_INVALID_TYPE
    if isinstance(actual, Fraction):
        if actual.denominator == 0:
            return None, False, ERROR_NON_FINITE_VALUE
        return actual, True, None
    if not _semantic_only(contract):
        return None, False, ERROR_INVALID_TYPE
    if isinstance(actual, int):
        return Fraction(actual, 1), True, None
    if isinstance(actual, float):
        if not math.isfinite(actual):
            return None, False, ERROR_NON_FINITE_VALUE
        try:
            return Fraction(str(actual)), True, None
        except (ValueError, ZeroDivisionError):
            return None, False, ERROR_PARSE_ERROR
    return None, False, ERROR_INVALID_TYPE


def _rational_representation_compliance(
    actual: Any,
    *,
    contract: MathOutputContract,
) -> bool:
    if _semantic_only(contract):
        parsed, ok, _ = _parse_actual_rational(actual, contract=contract)
        return ok and parsed is not None
    return isinstance(actual, Fraction) and not _reject_bool(actual)


def _validate_rational(
    actual: Any,
    reference: Any,
    contract: MathOutputContract,
) -> ValidationResult:
    try:
        canonical_reference = _canonical_fraction(reference)
    except MathValidatorError:
        return _error_result(ERROR_VALIDATOR_ERROR, {"field": "reference"})

    parsed, parse_ok, parse_error = _parse_actual_rational(actual, contract=contract)
    if not parse_ok or parsed is None:
        return _error_result(
            parse_error or ERROR_INVALID_TYPE,
            {"actual_type": type(actual).__name__},
        )

    representation_ok = _rational_representation_compliance(actual, contract=contract)
    math_ok = parsed == canonical_reference

    error_code = ERROR_NOT_EQUIVALENT if not math_ok else None
    if math_ok and not representation_ok:
        error_code = ERROR_INVALID_TYPE

    return _final_result(
        mathematical_equivalence=math_ok,
        representation_compliance=representation_ok,
        canonical_actual=parsed,
        canonical_reference=canonical_reference,
        error_code=error_code,
        details={},
    )


def _validate_coordinate_element(
    actual: Any,
    reference: Any,
    *,
    tolerance: float,
) -> Tuple[bool, bool, Any, Any, Optional[str]]:
    if isinstance(reference, bool) or isinstance(actual, bool):
        return False, False, None, None, ERROR_INVALID_TYPE

    if isinstance(reference, int) and not isinstance(reference, bool):
        ref_num: Union[int, float] = reference
        act_contract = _number_contract_int(representation_policy="semantic_only")
    elif isinstance(reference, float):
        ref_num = reference
        act_contract = _number_contract_float(tolerance, representation_policy="semantic_only")
    elif isinstance(reference, Fraction):
        sub = _validate_rational(actual, reference, _rational_contract_semantic())
        return (
            sub.mathematical_equivalence,
            sub.representation_compliance,
            sub.canonical_actual,
            sub.canonical_reference,
            sub.error_code,
        )
    else:
        return False, False, None, None, ERROR_VALIDATOR_ERROR

    if isinstance(actual, int) and not isinstance(actual, bool):
        act_num: Union[int, float] = actual
    elif isinstance(actual, float):
        if not math.isfinite(actual):
            return False, False, None, None, ERROR_NON_FINITE_VALUE
        act_num = actual
    elif isinstance(actual, Fraction):
        sub = _validate_rational(actual, reference, _rational_contract_semantic())
        return (
            sub.mathematical_equivalence,
            sub.representation_compliance,
            sub.canonical_actual,
            sub.canonical_reference,
            sub.error_code,
        )
    else:
        return False, False, None, None, ERROR_INVALID_TYPE

    math_ok = _numbers_equivalent(act_num, ref_num, tolerance=tolerance)
    rep_ok = True
    return math_ok, rep_ok, act_num, ref_num, ERROR_NOT_EQUIVALENT if not math_ok else None


def _number_contract_int(*, representation_policy: str = "semantic_only") -> MathOutputContract:
    return MathOutputContract(
        answer_type="number",
        representation_subtype="integer",
        python_return_type="int",
        representation_policy=representation_policy,
        validator_type="number_exact",
        allowed_tolerance=None,
        symbolic_variables=(),
        answer_fields=(),
    )


def _number_contract_float(
    tolerance: float,
    *,
    representation_policy: str = "semantic_only",
) -> MathOutputContract:
    return MathOutputContract(
        answer_type="number",
        representation_subtype="decimal",
        python_return_type="float",
        representation_policy=representation_policy,
        validator_type="number_exact",
        allowed_tolerance=tolerance,
        symbolic_variables=(),
        answer_fields=(),
    )


def _rational_contract_semantic(*, representation_policy: str = "semantic_only") -> MathOutputContract:
    return MathOutputContract(
        answer_type="rational",
        representation_subtype=None,
        python_return_type="Fraction",
        representation_policy=representation_policy,
        validator_type="rational_exact",
        allowed_tolerance=None,
        symbolic_variables=(),
        answer_fields=(),
    )


def _canonical_coordinate_reference(reference: Any) -> Tuple[Any, Any]:
    if isinstance(reference, tuple):
        items = list(reference)
    elif isinstance(reference, list):
        items = reference
    else:
        raise MathValidatorError("invalid coordinate reference")
    if len(items) != 2:
        raise MathValidatorError("coordinate reference length must be 2")
    return (items[0], items[1])


def _parse_coordinate_actual(
    actual: Any,
    *,
    contract: MathOutputContract,
) -> Tuple[Optional[Tuple[Any, Any]], bool, Optional[str]]:
    if isinstance(actual, tuple):
        items = list(actual)
    elif _semantic_only(contract) and isinstance(actual, list):
        items = actual
    else:
        return None, False, ERROR_INVALID_TYPE
    if len(items) != 2:
        return None, False, ERROR_PARSE_ERROR
    return (items[0], items[1]), True, None


def _coordinate_representation_compliance(
    actual: Any,
    *,
    contract: MathOutputContract,
) -> bool:
    if _semantic_only(contract):
        parsed, ok, _ = _parse_coordinate_actual(actual, contract=contract)
        return ok and parsed is not None
    return isinstance(actual, tuple)


def _validate_coordinate_pair(
    actual: Any,
    reference: Any,
    contract: MathOutputContract,
) -> ValidationResult:
    try:
        ref_pair = _canonical_coordinate_reference(reference)
    except MathValidatorError:
        return _error_result(ERROR_VALIDATOR_ERROR, {"field": "reference"})

    parsed, parse_ok, parse_error = _parse_coordinate_actual(actual, contract=contract)
    if not parse_ok or parsed is None:
        return _error_result(
            parse_error or ERROR_INVALID_TYPE,
            {"actual_type": type(actual).__name__},
        )

    representation_ok = _coordinate_representation_compliance(actual, contract=contract)
    tolerance = _tolerance(contract)

    math_results = []
    canonical_actual_items = []
    canonical_reference_items = []
    first_error: Optional[str] = None

    for index, (act_item, ref_item) in enumerate(zip(parsed, ref_pair)):
        math_ok, rep_ok, can_act, can_ref, err = _validate_coordinate_element(
            act_item,
            ref_item,
            tolerance=tolerance,
        )
        math_results.append(math_ok)
        canonical_actual_items.append(can_act)
        canonical_reference_items.append(can_ref)
        if err and first_error is None:
            first_error = err

    math_ok = all(math_results)
    canonical_actual = tuple(canonical_actual_items)
    canonical_reference = tuple(canonical_reference_items)

    error_code = first_error if not math_ok else None
    if math_ok and not representation_ok:
        error_code = ERROR_INVALID_TYPE

    return _final_result(
        mathematical_equivalence=math_ok,
        representation_compliance=representation_ok,
        canonical_actual=canonical_actual,
        canonical_reference=canonical_reference,
        error_code=error_code,
        details={},
    )


def _validate_symbolic_ast(
    node: ast.AST,
    *,
    allowed_names: Set[str],
    allow_float_literals: bool,
) -> None:
    if isinstance(node, ast.Expression):
        _validate_symbolic_ast(
            node.body,
            allowed_names=allowed_names,
            allow_float_literals=allow_float_literals,
        )
        return
    if isinstance(node, ast.BinOp):
        if not isinstance(node.op, _ALLOWED_SYMBOLIC_BINOPS):
            raise MathValidatorError("unsupported operator")
        _validate_symbolic_ast(
            node.left,
            allowed_names=allowed_names,
            allow_float_literals=allow_float_literals,
        )
        _validate_symbolic_ast(
            node.right,
            allowed_names=allowed_names,
            allow_float_literals=allow_float_literals,
        )
        return
    if isinstance(node, ast.UnaryOp):
        if not isinstance(node.op, _ALLOWED_SYMBOLIC_UNARYOPS):
            raise MathValidatorError("unsupported unary operator")
        _validate_symbolic_ast(
            node.operand,
            allowed_names=allowed_names,
            allow_float_literals=allow_float_literals,
        )
        return
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool):
            raise MathValidatorError("bool literal rejected")
        if isinstance(node.value, int):
            return
        if isinstance(node.value, float):
            if not allow_float_literals:
                raise MathValidatorError("float literal rejected for radical subtype")
            if not math.isfinite(node.value):
                raise MathValidatorError("non-finite float literal")
            return
        raise MathValidatorError("unsupported constant")
    if isinstance(node, ast.Name):
        if node.id not in allowed_names:
            raise MathValidatorError(f"undeclared symbol {node.id!r}")
        return
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id != "sqrt":
            raise MathValidatorError("unsupported function call")
        if len(node.args) != 1 or node.keywords:
            raise MathValidatorError("invalid sqrt call")
        _validate_symbolic_ast(
            node.args[0],
            allowed_names=allowed_names,
            allow_float_literals=allow_float_literals,
        )
        return
    raise MathValidatorError(f"unsupported syntax: {type(node).__name__}")


def _parse_symbolic_expression(
    expr: str,
    *,
    symbolic_variables: Sequence[str],
    allow_float_literals: bool,
) -> Any:
    try:
        import sympy as sp
        from sympy.parsing.sympy_parser import (
            implicit_multiplication_application,
            parse_expr,
            standard_transformations,
        )
    except ImportError as exc:
        raise MathValidatorError("sympy is required for symbolic validation") from exc

    if not isinstance(expr, str) or not expr.strip():
        raise MathValidatorError("symbolic expression must be a non-empty string")

    allowed_names = set(symbolic_variables)
    try:
        tree = ast.parse(expr.strip(), mode="eval")
    except SyntaxError as exc:
        raise MathValidatorError(ERROR_PARSE_ERROR) from exc
    try:
        _validate_symbolic_ast(
            tree,
            allowed_names=allowed_names,
            allow_float_literals=allow_float_literals,
        )
    except MathValidatorError as exc:
        message = str(exc)
        if "undeclared symbol" in message:
            raise MathValidatorError(ERROR_UNDECLARED_SYMBOL) from exc
        raise

    local_dict = {name: sp.Symbol(name) for name in symbolic_variables}
    local_dict["sqrt"] = sp.sqrt
    transformations = standard_transformations + (implicit_multiplication_application,)
    return parse_expr(
        expr.strip(),
        local_dict=local_dict,
        transformations=transformations,
        evaluate=True,
    )


def _symbolic_equivalent(actual_expr: Any, reference_expr: Any) -> bool:
    import sympy as sp

    try:
        return sp.simplify(actual_expr - reference_expr) == 0
    except Exception as exc:
        raise MathValidatorError("symbolic equivalence failed") from exc


def _validate_symbolic_expression(
    actual: Any,
    reference: Any,
    contract: MathOutputContract,
) -> ValidationResult:
    if not isinstance(actual, str):
        return _error_result(
            ERROR_INVALID_TYPE,
            {"actual_type": type(actual).__name__},
        )
    if not isinstance(reference, str):
        return _error_result(ERROR_VALIDATOR_ERROR, {"field": "reference"})

    representation_ok = isinstance(actual, str)
    if contract.representation_policy == "exact_answer_type" and not isinstance(actual, str):
        representation_ok = False

    allow_float_literals = contract.representation_subtype != "radical"

    try:
        actual_expr = _parse_symbolic_expression(
            actual,
            symbolic_variables=contract.symbolic_variables,
            allow_float_literals=allow_float_literals,
        )
        reference_expr = _parse_symbolic_expression(
            reference,
            symbolic_variables=contract.symbolic_variables,
            allow_float_literals=True,
        )
    except MathValidatorError as exc:
        code = str(exc)
        if code == ERROR_UNDECLARED_SYMBOL:
            return _error_result(ERROR_UNDECLARED_SYMBOL, {})
        if code == ERROR_PARSE_ERROR:
            return _error_result(ERROR_PARSE_ERROR, {})
        return _error_result(ERROR_PARSE_ERROR, {"message": code})

    try:
        math_ok = _symbolic_equivalent(actual_expr, reference_expr)
    except MathValidatorError:
        return _error_result(ERROR_VALIDATOR_ERROR, {})

    if contract.representation_subtype == "radical":
        try:
            import sympy as sp

            if actual_expr.has(sp.Float):
                math_ok = False
        except Exception:
            return _error_result(ERROR_VALIDATOR_ERROR, {})

    error_code = ERROR_NOT_EQUIVALENT if not math_ok else None
    return _final_result(
        mathematical_equivalence=math_ok,
        representation_compliance=representation_ok,
        canonical_actual=str(actual_expr),
        canonical_reference=str(reference_expr),
        error_code=error_code,
        details={},
    )


def _infer_field_contract(
    reference_value: Any,
    *,
    parent: MathOutputContract,
) -> Optional[MathOutputContract]:
    if isinstance(reference_value, bool):
        return None
    if isinstance(reference_value, int):
        return _number_contract_int(representation_policy=parent.representation_policy)
    if isinstance(reference_value, float):
        return _number_contract_float(
            _tolerance(parent),
            representation_policy=parent.representation_policy,
        )
    if isinstance(reference_value, Fraction) or (
        isinstance(reference_value, dict)
        and "numerator" in reference_value
        and "denominator" in reference_value
    ):
        return _rational_contract_semantic(representation_policy=parent.representation_policy)
    if isinstance(reference_value, str):
        return MathOutputContract(
            answer_type="symbolic_expression",
            representation_subtype="generic",
            python_return_type="str",
            representation_policy=parent.representation_policy,
            validator_type="symbolic_expression",
            allowed_tolerance=None,
            symbolic_variables=parent.symbolic_variables,
            answer_fields=(),
        )
    if isinstance(reference_value, (tuple, list)) and len(reference_value) == 2:
        return MathOutputContract(
            answer_type="coordinate_pair",
            representation_subtype=None,
            python_return_type="tuple",
            representation_policy=parent.representation_policy,
            validator_type="coordinate_pair_exact",
            allowed_tolerance=parent.allowed_tolerance,
            symbolic_variables=(),
            answer_fields=(),
        )
    return None


def _validate_multi_field_answer(
    actual: Any,
    reference: Any,
    contract: MathOutputContract,
) -> ValidationResult:
    if not isinstance(reference, dict):
        return _error_result(ERROR_VALIDATOR_ERROR, {"field": "reference"})
    if not isinstance(actual, dict):
        return _error_result(
            ERROR_INVALID_TYPE,
            {"actual_type": type(actual).__name__},
        )

    expected_fields = set(contract.answer_fields)
    actual_fields = set(actual.keys())

    if actual_fields != expected_fields:
        if expected_fields - actual_fields:
            return _error_result(
                ERROR_MISSING_FIELD,
                {"missing": sorted(expected_fields - actual_fields)},
            )
        if actual_fields - expected_fields:
            return _error_result(
                ERROR_EXTRA_FIELD,
                {"extra": sorted(actual_fields - expected_fields)},
            )
        return _error_result(ERROR_WRONG_FIELD, {})

    representation_ok = True
    math_ok = True
    canonical_actual: Dict[str, Any] = {}
    canonical_reference: Dict[str, Any] = {}
    first_error: Optional[str] = None

    for field_name in contract.answer_fields:
        ref_value = reference.get(field_name)
        field_contract = _infer_field_contract(ref_value, parent=contract)
        if field_contract is None:
            return _error_result(
                ERROR_VALIDATOR_ERROR,
                {"field": field_name, "reason": "cannot infer field validator"},
            )
        sub = validate_answer(actual[field_name], ref_value, field_contract)
        canonical_actual[field_name] = sub.canonical_actual
        canonical_reference[field_name] = sub.canonical_reference
        if not sub.mathematical_equivalence:
            math_ok = False
            if first_error is None:
                first_error = sub.error_code or ERROR_NOT_EQUIVALENT
        if not sub.representation_compliance:
            representation_ok = False
            if first_error is None:
                first_error = sub.error_code or ERROR_INVALID_TYPE

    error_code = first_error if not (math_ok and representation_ok) else None
    return _final_result(
        mathematical_equivalence=math_ok,
        representation_compliance=representation_ok,
        canonical_actual=canonical_actual,
        canonical_reference=canonical_reference,
        error_code=error_code,
        details={},
    )
