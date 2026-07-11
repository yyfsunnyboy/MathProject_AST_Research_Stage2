"""
Tests for agent_tools/finals_rebuild/static_evaluator.py
"""

from __future__ import annotations

import inspect
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from agent_tools.finals_rebuild.evaluation import validate_evaluation_result
from agent_tools.finals_rebuild.static_evaluator import (
    STATIC_EVALUATOR_VERSION,
    compute_evaluator_config_hash,
    evaluate_static,
)

_PAIR_ID = "a" * 64
_RUN_ID = "b" * 64
_HASH = "c" * 64


def _eval(code, **overrides):
    kwargs = dict(
        code=code,
        pair_id=_PAIR_ID,
        run_id=_RUN_ID,
        treatment="ab1",
        artifact_hash=_HASH,
        evaluator_git_commit="deadbeef",
    )
    kwargs.update(overrides)
    return evaluate_static(**kwargs)


# ---------------------------------------------------------------------------
# 1/2/3: syntax_pass true/false + exception_type
# ---------------------------------------------------------------------------


def test_1_legal_python_syntax_pass_true():
    result = _eval("def generate():\n    return 1\n")
    assert result.syntax_pass is True
    assert result.exception_type is None


def test_2_illegal_python_syntax_pass_false():
    result = _eval("def generate(:\n    return 1\n")
    assert result.syntax_pass is False


def test_3_syntax_error_has_exception_type():
    result = _eval("def generate(:\n    return 1\n")
    assert result.exception_type == "SyntaxError"
    assert result.exception_message is not None
    assert len(result.exception_message) > 0


# ---------------------------------------------------------------------------
# 4/5/6: contract inspection
# ---------------------------------------------------------------------------


def test_4_required_function_present_contract_pass():
    result = _eval(
        "def generate():\n    return 1\n", required_functions=["generate"]
    )
    assert result.contract_status == "pass"
    assert "generate" in result.discovered_functions


def test_5_required_function_missing_contract_fail():
    result = _eval(
        "def other():\n    return 1\n", required_functions=["generate"]
    )
    assert result.contract_status == "fail"


def test_6_empty_required_functions_not_required():
    result = _eval("def generate():\n    return 1\n", required_functions=None)
    assert result.contract_status == "not_required"

    result2 = _eval("def generate():\n    return 1\n", required_functions=[])
    assert result2.contract_status == "not_required"


def test_missing_required_function_on_unparseable_code_is_fail_not_crash():
    result = _eval("def generate(:\n", required_functions=["generate"])
    assert result.syntax_pass is False
    assert result.contract_status == "fail"
    assert result.discovered_functions == []


# ---------------------------------------------------------------------------
# 7: no top-level side effects executed
# ---------------------------------------------------------------------------


def test_7_no_top_level_side_effects_executed(tmp_path, monkeypatch):
    """
    A module-level statement that would have an observable side effect if
    ever exec'd/imported (writing a file) must NOT run — evaluate_static
    only parses the AST, never executes it.
    """
    sentinel = tmp_path / "should_not_exist.txt"
    code = (
        f"import pathlib\n"
        f"pathlib.Path(r'{sentinel}').write_text('boom')\n"
        f"def generate():\n"
        f"    return 1\n"
    )
    result = _eval(code)
    assert result.syntax_pass is True
    assert not sentinel.exists()


def test_no_exec_compile_or_subprocess_in_module_source():
    """
    Structural check for actual CODE usage, not docstring mentions (the
    module docstring legitimately explains what it does NOT do, which
    means the word "subprocess" appears there on purpose).
    """
    import ast as _ast
    import agent_tools.finals_rebuild.static_evaluator as mod

    source = inspect.getsource(mod)
    tree = _ast.parse(source)

    import_lines = "\n".join(
        line.strip() for line in source.splitlines()
        if line.strip().startswith(("import ", "from "))
    )
    for forbidden_import in ("subprocess", "importlib"):
        assert forbidden_import not in import_lines, (
            f"static_evaluator.py must not import {forbidden_import!r}"
        )

    forbidden_calls = {"exec", "eval", "compile", "__import__"}
    for node in _ast.walk(tree):
        if isinstance(node, _ast.Call) and isinstance(node.func, _ast.Name):
            assert node.func.id not in forbidden_calls, (
                f"static_evaluator.py must not call {node.func.id}()"
            )
        if isinstance(node, _ast.Attribute) and node.attr == "system":
            assert False, "static_evaluator.py must not call os.system()"


# ---------------------------------------------------------------------------
# 8: execution/test/MCRI fields are None/not_run
# ---------------------------------------------------------------------------


def test_8_unevaluated_fields_are_none_or_not_run():
    result = _eval("def generate():\n    return 1\n")
    assert result.execution_status == "not_run"
    assert result.execution_success is None
    assert result.test_status == "not_run"
    assert result.test_pass is None
    assert result.tests_passed is None
    assert result.tests_total is None
    assert result.mcri_code is None
    assert result.mcri_math is None


# ---------------------------------------------------------------------------
# Deterministic evaluator_config_hash
# ---------------------------------------------------------------------------


def test_9_deterministic_evaluator_config_hash_same_inputs():
    h1 = compute_evaluator_config_hash(STATIC_EVALUATOR_VERSION, ["generate"])
    h2 = compute_evaluator_config_hash(STATIC_EVALUATOR_VERSION, ["generate"])
    assert h1 == h2


def test_config_hash_independent_of_code_content():
    r1 = _eval("def generate():\n    return 1\n", required_functions=["generate"])
    r2 = _eval("def generate():\n    return 2\n", required_functions=["generate"])
    assert r1.evaluator_config_hash == r2.evaluator_config_hash


def test_config_hash_changes_with_required_functions():
    r1 = _eval("def generate():\n    return 1\n", required_functions=["generate"])
    r2 = _eval("def generate():\n    return 1\n", required_functions=["other"])
    assert r1.evaluator_config_hash != r2.evaluator_config_hash


def test_config_hash_order_independent():
    h1 = compute_evaluator_config_hash(STATIC_EVALUATOR_VERSION, ["a", "b"])
    h2 = compute_evaluator_config_hash(STATIC_EVALUATOR_VERSION, ["b", "a"])
    assert h1 == h2


# ---------------------------------------------------------------------------
# 10: artifact_hash caller contract (evaluator records exactly what it's given)
# ---------------------------------------------------------------------------


def test_10_artifact_hash_is_recorded_verbatim():
    result = _eval("def generate():\n    return 1\n", artifact_hash="9" * 64)
    assert result.artifact_hash == "9" * 64


# ---------------------------------------------------------------------------
# Fail-closed / finalized result validity
# ---------------------------------------------------------------------------


def test_result_validates_once_finalized():
    import dataclasses
    result = _eval("def generate():\n    return 1\n")
    finalized = dataclasses.replace(
        result, created_at_utc="2026-07-11T09:00:00+00:00"
    )
    validate_evaluation_result(finalized)


def test_syntax_error_result_validates_once_finalized():
    import dataclasses
    result = _eval("def generate(:\n")
    finalized = dataclasses.replace(
        result, created_at_utc="2026-07-11T09:00:00+00:00"
    )
    validate_evaluation_result(finalized)
    assert finalized.fail_closed is True


def test_created_at_utc_and_run_id_are_placeholders():
    """The adapter cannot know the resolved run timestamp in advance; the
    pipeline binds it, exactly like TreatmentTrace."""
    result = _eval("def generate():\n    return 1\n")
    assert result.created_at_utc == ""


def test_only_top_level_functions_discovered_not_nested_or_class_methods():
    code = (
        "def outer():\n"
        "    def inner():\n"
        "        return 1\n"
        "    return inner\n"
        "\n"
        "class C:\n"
        "    def method(self):\n"
        "        return 1\n"
        "\n"
        "def generate():\n"
        "    return 1\n"
    )
    result = _eval(code)
    assert set(result.discovered_functions) == {"outer", "generate"}
