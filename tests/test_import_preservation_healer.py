import ast

from core.healers.ast_healer import ASTHealer


def heal(source):
    return ASTHealer(require_entry_point=False).heal(source)[0]


def imports(source):
    return [
        ast.unparse(node)
        for node in ast.walk(ast.parse(source))
        if isinstance(node, (ast.Import, ast.ImportFrom))
    ]


def test_import_math_with_attribute_use_is_preserved():
    healed = heal("import math\nresult = math.sqrt(9)\n")
    namespace = {}
    exec(healed, namespace)
    assert "import math" in imports(healed)
    assert namespace["result"] == 3


def test_import_math_alias_with_attribute_use_is_preserved():
    healed = heal("import math as m\nresult = m.sqrt(16)\n")
    namespace = {}
    exec(healed, namespace)
    assert "import math as m" in imports(healed)
    assert namespace["result"] == 4


def test_from_collections_import_counter_with_name_use_is_preserved():
    healed = heal(
        "from collections import Counter\nresult = Counter(['a', 'a'])['a']\n"
    )
    namespace = {}
    exec(healed, namespace)
    assert "from collections import Counter" in imports(healed)
    assert namespace["result"] == 2


def test_from_import_alias_is_tracked():
    healed = heal("from collections import Counter as C\nresult = C('aba')['a']\n")
    assert "from collections import Counter as C" in imports(healed)


def test_unused_import_follows_existing_removal_strategy():
    healed = heal("import heapq\nresult = 1\n")
    assert imports(healed) == []


def test_symbol_in_string_is_not_a_use():
    healed = heal("from collections import Counter\nresult = 'Counter'\n")
    assert imports(healed) == []


def test_local_rebinding_prevents_import_preservation():
    healed = heal(
        "import heapq\nheapq = object()\nresult = getattr(heapq, 'merge', None)\n"
    )
    assert imports(healed) == []


def test_dangerous_module_is_not_preserved_when_used():
    healed = heal("import os\nresult = os.getcwd()\n")
    assert imports(healed) == []


def test_star_import_fails_closed():
    healed = heal("from math import *\nresult = sqrt(4)\n")
    assert imports(healed) == []


def test_relative_import_fails_closed():
    healed = heal("from .collections import Counter\nresult = Counter()\n")
    assert imports(healed) == []


def test_unknown_third_party_import_fails_closed():
    healed = heal("import imaginary_package\nresult = imaginary_package.value\n")
    assert imports(healed) == []


def test_mixed_import_aliases_keep_only_referenced_safe_alias():
    healed = heal("import heapq, bisect\nresult = heapq.merge([], [])\n")
    assert imports(healed) == ["import heapq"]
