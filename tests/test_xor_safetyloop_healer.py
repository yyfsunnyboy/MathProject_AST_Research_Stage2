import ast

import pytest

from core.healers.ast_healer import ASTHealer


def heal(source, domain_mode="benchmark"):
    return ASTHealer(
        require_entry_point=False,
        domain_mode=domain_mode,
    ).heal(source)[0]


def test_bitmask_xor_is_preserved_in_benchmark_mode():
    source = "def toggle(value, mask):\n    return value ^ mask\n"
    healed = heal(source)

    function = ast.parse(healed).body[0]
    assert isinstance(function.body[0].value.op, ast.BitXor)
    namespace = {}
    exec(healed, namespace)
    assert namespace["toggle"](10, 3) == 9


def test_explicit_math_generator_mode_allows_xor_to_pow():
    source = "def formula(value):\n    return value ^ 2\n"
    healed = heal(source, domain_mode="math_generator")

    function = ast.parse(healed).body[0]
    assert isinstance(function.body[0].value.op, ast.Pow)
    namespace = {}
    exec(healed, namespace)
    assert namespace["formula"](3) == 9


def test_xor_in_string_is_not_processed():
    source = "def symbol():\n    return 'x ^ 2'\n"
    healed = heal(source, domain_mode="math_generator")

    assert "x ^ 2" in healed


def test_augmented_xor_assignment_is_not_rewritten():
    source = "def toggle(value, mask):\n    value ^= mask\n    return value\n"
    healed = heal(source, domain_mode="math_generator")

    function = ast.parse(healed).body[0]
    assert isinstance(function.body[0], ast.AugAssign)
    assert isinstance(function.body[0].op, ast.BitXor)


def test_unrelated_binary_operators_are_unchanged():
    source = "def combine(a, b):\n    return (a + b) * (a - b)\n"
    before = ast.dump(ast.parse(source), include_attributes=False)
    after = ast.dump(ast.parse(heal(source)), include_attributes=False)

    assert after == before


def test_while_true_with_break_is_preserved():
    source = """\
def first_positive(values):
    while True:
        value = values.pop(0)
        if value > 0:
            break
    return value
"""
    healed = heal(source)

    assert any(isinstance(node, ast.While) for node in ast.walk(ast.parse(healed)))
    assert "_safety_loop_var" not in healed


def test_while_true_with_return_is_preserved():
    source = """\
def find(values):
    while True:
        value = values.pop(0)
        if value:
            return value
"""
    healed = heal(source)

    assert any(isinstance(node, ast.While) for node in ast.walk(ast.parse(healed)))
    assert "range(1000)" not in healed


def test_nested_while_loop_is_not_rewritten_in_benchmark_mode():
    source = """\
def outer(limit):
    total = 0
    while True:
        while total < limit:
            total += 1
        break
    return total
"""
    healed = heal(source)

    tree = ast.parse(healed)
    assert sum(isinstance(node, ast.While) for node in ast.walk(tree)) == 2
    assert "_safety_loop_var" not in healed


def test_evaluator_timeout_is_not_implemented_as_ast_rewrite():
    source = "def wait_forever():\n    while True:\n        pass\n"
    healed = heal(source)

    assert any(isinstance(node, ast.While) for node in ast.walk(ast.parse(healed)))
    assert "range(1000)" not in healed


def test_explicit_math_generator_mode_retains_legacy_loop_gate():
    source = "def bounded_generator():\n    while True:\n        yield 1\n"
    healed = heal(source, domain_mode="math_generator")

    assert not any(isinstance(node, ast.While) for node in ast.walk(ast.parse(healed)))
    assert "range(1000)" in healed


def test_unknown_domain_mode_is_rejected():
    with pytest.raises(ValueError, match="domain_mode"):
        ASTHealer(require_entry_point=False, domain_mode="unknown")
