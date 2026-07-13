"""Fail-closed subprocess evaluator for raw ``generate()`` source code.

This is bounded process isolation, not an OS security sandbox.
"""
from __future__ import annotations

import ast
import os
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GeneratorEvaluationResult:
    status: str
    success: bool
    parse_status: str
    safety_status: str
    load_status: str
    entry_point_status: str
    execution_status: str
    output_type_status: str
    question_text_status: str
    correct_answer_status: str
    failure_stage: str | None
    error_type: str | None
    error_message: str | None
    stdout: str
    stderr: str
    duration_ms: float
    returned_instance: dict[str, object] | None


_FORBIDDEN_IMPORTS = frozenset({"os", "subprocess", "socket", "requests", "urllib", "http", "ftplib", "pathlib", "shutil", "multiprocessing", "ctypes", "importlib", "builtins"})
_FORBIDDEN_CALLS = frozenset({"open", "exec", "eval", "compile", "__import__", "input", "breakpoint", "globals", "locals", "vars", "getattr", "setattr", "delattr"})
_FORBIDDEN_ATTR_ROOTS = frozenset({"os", "subprocess", "socket", "requests", "urllib"})
_MAX_OUTPUT = 4000


def _cut(value: str) -> str:
    return value if len(value) <= _MAX_OUTPUT else value[:_MAX_OUTPUT] + "...<truncated>"


def _result(*, status="failed", success=False, parse="not_run", safety="not_run", load="not_run", entry="not_run", execution="not_run", output="not_run", question="not_run", answer="not_run", stage=None, error_type=None, error_message=None, stdout="", stderr="", duration=0.0, instance=None) -> GeneratorEvaluationResult:
    return GeneratorEvaluationResult(status, success, parse, safety, load, entry, execution, output, question, answer, stage, error_type, error_message, _cut(stdout), _cut(stderr), duration, instance)


def _unsafe_reason(tree: ast.AST) -> str | None:
    for node in ast.walk(tree):
        if isinstance(node, (ast.AsyncFunctionDef, ast.Await, ast.Yield, ast.YieldFrom, ast.Global, ast.Nonlocal, ast.With, ast.AsyncWith)):
            return f"forbidden syntax: {type(node).__name__}"
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [alias.name for alias in node.names] if isinstance(node, ast.Import) else [node.module or ""]
            if any(name.split(".")[0] in _FORBIDDEN_IMPORTS for name in names):
                return "forbidden import"
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in _FORBIDDEN_CALLS:
                return f"forbidden call: {node.func.id}"
            if isinstance(node.func, ast.Attribute) and node.func.attr in {"write_text", "write_bytes"}:
                return "forbidden attribute call"
            if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                if node.func.value.id in _FORBIDDEN_ATTR_ROOTS:
                    return "forbidden attribute call"
    return None


_WORKER = r'''import contextlib, inspect, io, json, math, sys
source = %r
level = %r
out, err = io.StringIO(), io.StringIO()
def normalise(value):
 if value is None or isinstance(value, (str, int, bool)): return value
 if isinstance(value, float):
  if not math.isfinite(value): raise TypeError
  return value
 if isinstance(value, (list, tuple)): return [normalise(item) for item in value]
 if isinstance(value, dict):
  if not all(isinstance(key, str) for key in value): raise TypeError
  return {key: normalise(item) for key, item in value.items()}
 raise TypeError
try:
 with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
  ns = {"__name__": "__main__"}
  exec(compile(source, "candidate.py", "exec"), ns)
except BaseException as exc:
 payload={"phase":"load","error_type":type(exc).__name__,"error_message":str(exc),"stdout":out.getvalue(),"stderr":err.getvalue()}
else:
 generate=ns.get("generate")
 if generate is None:
  payload={"phase":"entry","error_type":"GenerateEntryPointMissing","error_message":"generate is not defined","stdout":out.getvalue(),"stderr":err.getvalue()}
 elif not callable(generate):
  payload={"phase":"entry","error_type":"GenerateEntryPointNotCallable","error_message":"generate is not callable","stdout":out.getvalue(),"stderr":err.getvalue()}
 else:
  try:
   with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
    sig=inspect.signature(generate)
    params=sig.parameters
    if not params: value=generate()
    elif "level" in params or any(p.kind == p.VAR_KEYWORD for p in params.values()): value=generate(level=level)
    elif len(params) == 1 and next(iter(params.values())).kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD): value=generate(level)
    else: raise ValueError("UnsupportedGenerateSignature")
  except ValueError as exc:
   if str(exc) == "UnsupportedGenerateSignature": payload={"phase":"entry","error_type":"UnsupportedGenerateSignature","error_message":str(exc),"stdout":out.getvalue(),"stderr":err.getvalue()}
   else: payload={"phase":"execution","error_type":type(exc).__name__,"error_message":str(exc),"stdout":out.getvalue(),"stderr":err.getvalue()}
  except BaseException as exc:
   payload={"phase":"execution","error_type":type(exc).__name__,"error_message":str(exc),"stdout":out.getvalue(),"stderr":err.getvalue()}
  else:
   try: payload={"phase":"output","value":normalise(value),"stdout":out.getvalue(),"stderr":err.getvalue()}
   except TypeError: payload={"phase":"unsafe_output","error_type":"UnsafeReturnType","error_message":"return value is not JSON-safe","stdout":out.getvalue(),"stderr":err.getvalue()}
json.dump(payload, open(sys.argv[1],"w",encoding="utf-8"))
'''


def evaluate_generator_code(code: str, *, level: int = 1, timeout_seconds: float = 2.0) -> GeneratorEvaluationResult:
    if not isinstance(code, str) or not isinstance(level, int) or isinstance(level, bool) or not isinstance(timeout_seconds, (int, float)) or timeout_seconds <= 0:
        return _result(stage="input", error_type="InvalidEvaluatorInput", error_message="code must be str, level int, and timeout_seconds > 0")
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return _result(parse="failed", stage="parse", error_type="SyntaxError", error_message=str(exc))
    unsafe = _unsafe_reason(tree)
    if unsafe:
        return _result(status="rejected", parse="passed", safety="rejected", stage="safety", error_type="UnsafeGeneratorCode", error_message=unsafe)
    worker = _WORKER % (code, level)
    start = time.monotonic()
    try:
        with tempfile.TemporaryDirectory(prefix="generator_eval_") as directory:
            runner, report = os.path.join(directory, "runner.py"), os.path.join(directory, "result.json")
            with open(runner, "w", encoding="utf-8") as handle: handle.write(worker)
            proc = subprocess.run([sys.executable, "-I", runner, report], cwd=directory, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=timeout_seconds, env={key:value for key, value in os.environ.items() if key.upper() in {"PATH", "SYSTEMROOT"}})
            duration = (time.monotonic() - start) * 1000
            if proc.returncode or not os.path.exists(report):
                return _result(parse="passed", safety="passed", load="failed", stage="load", error_type="WorkerProtocolError", error_message="worker did not produce a result", stdout=proc.stdout, stderr=proc.stderr, duration=duration)
            import json
            with open(report, encoding="utf-8") as handle: payload = json.load(handle)
    except subprocess.TimeoutExpired as exc:
        return _result(status="timeout", parse="passed", safety="passed", load="passed", entry="passed", execution="timeout", stage="execution", error_type="TimeoutExpired", error_message="generator execution exceeded timeout", stdout=exc.stdout or "", stderr=exc.stderr or "", duration=(time.monotonic() - start) * 1000)
    except Exception as exc:
        return _result(parse="passed", safety="passed", load="failed", stage="load", error_type=type(exc).__name__, error_message=str(exc), duration=(time.monotonic() - start) * 1000)
    phase, stdout, stderr = payload["phase"], payload.get("stdout", ""), payload.get("stderr", "")
    if phase == "load": return _result(parse="passed", safety="passed", load="failed", stage="load", error_type=payload["error_type"], error_message=payload["error_message"], stdout=stdout, stderr=stderr, duration=duration)
    if phase == "entry": return _result(parse="passed", safety="passed", load="passed", entry="failed", stage="entry_point", error_type=payload["error_type"], error_message=payload["error_message"], stdout=stdout, stderr=stderr, duration=duration)
    if phase == "execution": return _result(parse="passed", safety="passed", load="passed", entry="passed", execution="failed", stage="execution", error_type=payload["error_type"], error_message=payload["error_message"], stdout=stdout, stderr=stderr, duration=duration)
    if phase == "unsafe_output": return _result(parse="passed", safety="passed", load="passed", entry="passed", execution="passed", output="failed", stage="output", error_type="UnsafeReturnType", error_message=payload["error_message"], stdout=stdout, stderr=stderr, duration=duration)
    value = payload["value"]
    if not isinstance(value, dict): return _result(parse="passed", safety="passed", load="passed", entry="passed", execution="passed", output="failed", stage="output", error_type="GeneratorOutputNotDict", error_message="generate must return a dict", stdout=stdout, stderr=stderr, duration=duration)
    if "question_text" not in value: return _result(parse="passed", safety="passed", load="passed", entry="passed", execution="passed", output="passed", question="failed", stage="instance_schema", error_type="QuestionTextMissing", error_message="question_text is required", stdout=stdout, stderr=stderr, duration=duration)
    if not isinstance(value["question_text"], str) or not value["question_text"].strip(): return _result(parse="passed", safety="passed", load="passed", entry="passed", execution="passed", output="passed", question="failed", stage="instance_schema", error_type="QuestionTextInvalid", error_message="question_text must be non-empty str", stdout=stdout, stderr=stderr, duration=duration)
    if "correct_answer" not in value: return _result(parse="passed", safety="passed", load="passed", entry="passed", execution="passed", output="passed", question="passed", answer="failed", stage="instance_schema", error_type="CorrectAnswerMissing", error_message="correct_answer is required", stdout=stdout, stderr=stderr, duration=duration)
    if value["correct_answer"] is None: return _result(parse="passed", safety="passed", load="passed", entry="passed", execution="passed", output="passed", question="passed", answer="failed", stage="instance_schema", error_type="CorrectAnswerInvalid", error_message="correct_answer must not be None", stdout=stdout, stderr=stderr, duration=duration)
    return _result(status="passed", success=True, parse="passed", safety="passed", load="passed", entry="passed", execution="passed", output="passed", question="passed", answer="passed", stdout=stdout, stderr=stderr, duration=duration, instance=value)
