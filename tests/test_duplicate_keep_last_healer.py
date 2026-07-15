import ast

from core.healers.unified_cleanup_healer import UnifiedCleanupHealer


def heal(source):
    return UnifiedCleanupHealer().heal(source)


def module_function_names(source):
    return [
        node.name
        for node in ast.parse(source).body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]


def test_duplicate_module_function_keeps_last_definition():
    source = """\
def target():
    return "first"

def target():
    return "last"
"""

    healed, fixes = heal(source)
    namespace = {}
    exec(healed, namespace)

    assert fixes == 1
    assert module_function_names(healed) == ["target"]
    assert namespace["target"]() == "last"


def test_identical_body_duplicate_keeps_one_definition():
    source = """\
def target(value):
    return value + 1

def target(value):
    return value + 1
"""

    healed, fixes = heal(source)

    assert fixes == 1
    assert module_function_names(healed) == ["target"]


def test_different_function_names_are_unchanged():
    source = """\
def first():
    return 1

def second():
    return 2
"""

    healed, fixes = heal(source)

    assert fixes == 0
    assert healed == source


def test_nested_duplicate_functions_are_not_processed():
    source = """\
def outer():
    def target():
        return "first"

    def target():
        return "last"

    return target()
"""

    healed, fixes = heal(source)

    assert fixes == 0
    assert healed == source
    assert healed.count("def target") == 2


def test_duplicate_class_methods_are_not_processed():
    source = """\
class Example:
    def target(self):
        return "first"

    def target(self):
        return "last"
"""

    healed, fixes = heal(source)

    assert fixes == 0
    assert healed == source
    assert healed.count("def target") == 2


def test_decorator_mismatch_is_not_processed():
    source = """\
def decorate(function):
    return function

@decorate
def target():
    return "decorated"

def target():
    return "plain"
"""

    healed, fixes = heal(source)

    assert fixes == 0
    assert healed == source
    assert module_function_names(healed).count("target") == 2


def test_mbpp_279_counterfactual_replay_preserves_runtime_keep_last_semantics():
    source = """\
def is_num_decagonal(n):
    import math
    return n * (3 * n - 1) == 27

def nth_decagonal_number(n):
    return n * (3 * n - 1)

def is_num_decagonal(n):
    import math
    x = (1 + math.sqrt(1 + 24 * n)) / 6
    return x.is_integer() and x >= 1

def nth_decagonal_number(n):
    return n * (3 * n - 1)
"""
    raw_namespace = {}
    exec(source, raw_namespace)

    healed, fixes = heal(source)
    candidate_namespace = {}
    exec(healed, candidate_namespace)

    assert raw_namespace["is_num_decagonal"](5) is True
    assert fixes == 2
    assert module_function_names(healed) == [
        "is_num_decagonal",
        "nth_decagonal_number",
    ]
    assert candidate_namespace["is_num_decagonal"](5) is True
    assert ast.dump(ast.parse(healed)) == ast.dump(
        ast.parse(
            """\
def is_num_decagonal(n):
    import math
    x = (1 + math.sqrt(1 + 24 * n)) / 6
    return x.is_integer() and x >= 1

def nth_decagonal_number(n):
    return n * (3 * n - 1)
"""
        )
    )
