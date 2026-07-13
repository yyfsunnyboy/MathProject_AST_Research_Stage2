"""Deterministic execution-and-validation harness for frozen MathTask records.

This is a bounded subprocess runner, not a security sandbox.  It applies a
small fail-closed AST policy before execution and never executes candidate code
in the evaluator process.
"""
from __future__ import annotations

import ast
import json
import math
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from typing import Any, Optional

from agent_tools.finals_rebuild.extraction import extract_code
from agent_tools.finals_rebuild.math_task_schema import MathTask
from agent_tools.finals_rebuild.math_validator import ValidationResult, validate_answer


@dataclass(frozen=True)
class MathEvaluationResult:
    task_id: str
    source_kind: str
    raw_response_available: bool
    extraction_status: str
    extracted_code: str | None
    parse_status: str
    entry_point_count: int | None
    execution_status: str
    returned_value: Any
    stdout: str
    stderr: str
    math_validation: ValidationResult | None
    overall_status: str
    failure_stage: str | None
    error_code: str | None
    details: dict[str, Any] = field(default_factory=dict)


_ALLOWED_IMPORTS = frozenset({"math", "fractions"})
_FORBIDDEN_CALLS = frozenset({"input", "open", "exec", "eval", "compile", "__import__"})
_FORBIDDEN_ROOTS = frozenset({"os", "sys", "subprocess", "socket", "requests", "urllib", "pathlib"})


def _result(task: MathTask, *, source_kind: str, raw: bool, code: str | None,
            extraction: str, parse: str = "not_run", count: int | None = None,
            execution: str = "not_run", value: Any = None, stdout: str = "",
            stderr: str = "", validation: ValidationResult | None = None,
            overall: str = "fail", stage: str | None = "extraction",
            error: str | None = None, details: dict[str, Any] | None = None) -> MathEvaluationResult:
    return MathEvaluationResult(task.task_id, source_kind, raw, extraction, code, parse,
        count, execution, value, stdout, stderr, validation, overall, stage, error,
        details or {})


def _policy_error(tree: ast.AST) -> str | None:
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = ([a.name for a in node.names] if isinstance(node, ast.Import)
                     else [node.module or ""])
            if any(name.split(".")[0] not in _ALLOWED_IMPORTS for name in names):
                return "forbidden_operation"
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in _FORBIDDEN_CALLS:
                return "forbidden_operation"
            if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                if node.func.value.id in _FORBIDDEN_ROOTS:
                    return "forbidden_operation"
        if isinstance(node, ast.Name) and node.id in _FORBIDDEN_ROOTS:
            return "forbidden_operation"
    return None


def _entry_point_count(tree: ast.Module, name: str) -> int:
    return sum(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name
               for node in tree.body)


def _serialize(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value): raise TypeError("unsupported_return_type")
        return value
    from fractions import Fraction
    if isinstance(value, Fraction):
        return {"type": "fraction", "numerator": value.numerator, "denominator": value.denominator}
    if isinstance(value, tuple): return {"type": "tuple", "items": [_serialize(x) for x in value]}
    if isinstance(value, list): return [_serialize(x) for x in value]
    if isinstance(value, dict):
        if not all(isinstance(k, str) for k in value): raise TypeError("unsupported_return_type")
        return {k: _serialize(v) for k, v in value.items()}
    raise TypeError("unsupported_return_type")


def _deserialize(value: Any) -> Any:
    from fractions import Fraction
    if isinstance(value, list): return [_deserialize(x) for x in value]
    if isinstance(value, dict):
        if value.get("type") == "fraction": return Fraction(value["numerator"], value["denominator"])
        if value.get("type") == "tuple": return tuple(_deserialize(x) for x in value["items"])
        return {k: _deserialize(v) for k, v in value.items()}
    return value


def _run(code: str, timeout: float) -> tuple[str, Any, str, str, str | None]:
    # The wrapper owns reporting; candidate output is captured so it can be a
    # representation violation rather than corrupting the protocol.
    wrapper = '''import contextlib, io, json, sys, traceback\nsource = %r\nout, err = io.StringIO(), io.StringIO()\ndef enc(v):\n from fractions import Fraction\n import math\n if v is None or isinstance(v, (bool,int,str)): return v\n if isinstance(v,float):\n  if not math.isfinite(v): raise TypeError("unsupported_return_type")\n  return v\n if isinstance(v,Fraction): return {"type":"fraction","numerator":v.numerator,"denominator":v.denominator}\n if isinstance(v,tuple): return {"type":"tuple","items":[enc(x) for x in v]}\n if isinstance(v,list): return [enc(x) for x in v]\n if isinstance(v,dict) and all(isinstance(k,str) for k in v): return {k:enc(x) for k,x in v.items()}\n raise TypeError("unsupported_return_type")\ntry:\n with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):\n  ns={"__name__":"__main__"}; exec(compile(source,"candidate.py","exec"),ns); value=ns["solve"]()\n payload={"ok":True,"value":enc(value),"stdout":out.getvalue(),"stderr":err.getvalue()}\nexcept BaseException as exc:\n payload={"ok":False,"type":type(exc).__name__,"message":str(exc),"stdout":out.getvalue(),"stderr":err.getvalue()}\njson.dump(payload, open(sys.argv[1],"w",encoding="utf-8"))\n''' % code
    with tempfile.TemporaryDirectory(prefix="math_eval_") as directory:
        script, report = os.path.join(directory, "runner.py"), os.path.join(directory, "result.json")
        with open(script, "w", encoding="utf-8") as f: f.write(wrapper)
        try:
            proc = subprocess.run([sys.executable, "-I", script, report], cwd=directory,
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                env={k:v for k,v in os.environ.items() if k.upper() in {"PATH", "SYSTEMROOT"}},
                text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return "timeout", None, "", "", "timeout"
        except Exception as exc:
            return "infrastructure_error", None, "", str(exc), "infrastructure_error"
        if proc.returncode or not os.path.exists(report):
            return "infrastructure_error", None, proc.stdout, proc.stderr, "infrastructure_error"
        try:
            with open(report, encoding="utf-8") as report_file:
                data = json.load(report_file)
        except (OSError, ValueError, TypeError) as exc:
            return "infrastructure_error", None, proc.stdout, proc.stderr, str(exc)
        if not data["ok"]:
            return "runtime_error", None, data["stdout"], data["stderr"], data["message"] or data["type"]
        return "success", _deserialize(data["value"]), data["stdout"], data["stderr"], None


def evaluate_math_code(task: MathTask, code: str, *, timeout_seconds: float = 2.0) -> MathEvaluationResult:
    try: tree = ast.parse(code)
    except SyntaxError as exc:
        return _result(task, source_kind="extracted_code", raw=False, code=code, extraction="not_applicable", parse="failed", overall="fail", stage="parse", error="syntax_error", details={"message": str(exc)})
    policy = _policy_error(tree)
    if policy:
        return _result(task, source_kind="extracted_code", raw=False, code=code, extraction="not_applicable", parse="success", execution="not_run", overall="fail", stage="execution", error=policy)
    count = _entry_point_count(tree, task.entry_point)
    if count != 1:
        return _result(task, source_kind="extracted_code", raw=False, code=code, extraction="not_applicable", parse="success", count=count, overall="fail", stage="entry_point", error="invalid_entry_point_count")
    func = next(n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == task.entry_point)
    if isinstance(func, ast.AsyncFunctionDef) or func.args.args or func.args.posonlyargs or func.args.kwonlyargs or func.args.vararg or func.args.kwarg:
        return _result(task, source_kind="extracted_code", raw=False, code=code, extraction="not_applicable", parse="success", count=count, overall="fail", stage="entry_point", error="invalid_entry_point_signature")
    status, value, stdout, stderr, error = _run(code, timeout_seconds)
    if status != "success":
        overall = "error" if status == "infrastructure_error" else "fail"
        return _result(task, source_kind="extracted_code", raw=False, code=code, extraction="not_applicable", parse="success", count=count, execution=status, stdout=stdout, stderr=stderr, overall=overall, stage="infrastructure" if overall == "error" else "execution", error=error)
    if stdout:
        return _result(task, source_kind="extracted_code", raw=False, code=code, extraction="not_applicable", parse="success", count=count, execution=status, value=value, stdout=stdout, stderr=stderr, overall="fail", stage="math_validation", error="unexpected_stdout")
    if stderr:
        return _result(task, source_kind="extracted_code", raw=False, code=code, extraction="not_applicable", parse="success", count=count, execution=status, value=value, stdout=stdout, stderr=stderr, overall="fail", stage="math_validation", error="unexpected_stderr")
    validation = validate_answer(value, task.reference_semantic, task.output_contract)
    if validation.is_correct:
        return _result(task, source_kind="extracted_code", raw=False, code=code, extraction="not_applicable", parse="success", count=count, execution=status, value=value, validation=validation, overall="pass", stage=None)
    return _result(task, source_kind="extracted_code", raw=False, code=code, extraction="not_applicable", parse="success", count=count, execution=status, value=value, validation=validation, overall="fail", stage="math_validation", error=validation.error_code)


def evaluate_math_raw_response(task: MathTask, raw_response: str, *, timeout_seconds: float = 2.0) -> MathEvaluationResult:
    try: extracted = extract_code(raw_response)
    except Exception as exc:
        return _result(task, source_kind="raw_response", raw=True, code=None, extraction="error", overall="error", stage="extraction", error="extraction_error", details={"message":str(exc)})
    status = {"extracted":"success", "empty":"no_candidate", "ambiguous":"ambiguous", "unsupported":"no_candidate"}[extracted.extraction_status]
    if status != "success":
        return _result(task, source_kind="raw_response", raw=True, code=extracted.extracted_code, extraction=status, overall="fail", stage="extraction", error=status, details=extracted.diagnostics)
    result = evaluate_math_code(task, extracted.extracted_code or "", timeout_seconds=timeout_seconds)
    return MathEvaluationResult(**{**result.__dict__, "source_kind":"raw_response", "raw_response_available":True, "extraction_status":"success"})
