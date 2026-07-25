from __future__ import annotations

import ast
import hashlib

from agent_tools.finals_rebuild.mbpp_top_level_demo_print_quarantine import (
    RULE_ID,
    assert_fingerprint,
    quarantine_top_level_literal_only_demo_print,
)


def fingerprints(source: str) -> tuple[str, ...]:
    return tuple(
        assert_fingerprint(node)
        for node in ast.parse(source).body
        if isinstance(node, ast.Assert)
    )


def apply(source: str, entry: str, public: str | None = None):
    return quarantine_top_level_literal_only_demo_print(
        source,
        entry,
        extraction_unambiguous=True,
        source_complete=True,
        public_assert_fingerprints=fingerprints(public or source),
    )


def test_exact_literal_print_is_quarantined_without_touching_assert_or_function() -> None:
    source = (
        "def text_match_three(text):\n"
        "    return text == 'abbb'\n\n"
        "assert not text_match_three('ac')\n"
        'print("All tests passed.")\n'
    )
    result = apply(source, "text_match_three")
    assert result.rule_id == RULE_ID
    assert result.transformed
    assert "assert not text_match_three('ac')\nif __name__" in result.output_source
    assert '    print("All tests passed.")' in result.output_source
    assert "def text_match_three(text):\n    return text == 'abbb'" in result.output_source
    assert ast.parse(result.output_source)


def test_literal_entrypoint_call_inside_print_is_allowed_and_idempotent() -> None:
    source = (
        "def f(n):\n    return n > 0\n\n"
        "assert f(10) == True\n"
        "print(f(10))\n"
    )
    first = apply(source, "f")
    assert first.transformed
    second = apply(first.output_source, "f", source)
    assert not second.transformed
    assert second.reason == "no_top_level_print"
    assert second.output_source == first.output_source


def test_every_required_abstention_guard_fails_closed() -> None:
    valid = "def f(n):\n    return n\n\nassert f(1) == 1\nprint(f(1))\n"
    assert not quarantine_top_level_literal_only_demo_print(
        valid,
        "f",
        extraction_unambiguous=False,
        source_complete=True,
        public_assert_fingerprints=fingerprints(valid),
    ).transformed
    assert not quarantine_top_level_literal_only_demo_print(
        valid,
        "f",
        extraction_unambiguous=True,
        source_complete=False,
        public_assert_fingerprints=fingerprints(valid),
    ).transformed
    cases = [
        ("def g(n):\n    return n\nassert g(1) == 1\nprint(g(1))\n", "f"),
        ("def f(n):\n    return n\nassert f(1) == 1\nprint(f(x))\n", "f"),
        ("def f(n):\n    return n\nprint(f(1))\nassert f(1) == 1\nprint('x')\n", "f"),
        ("def f(n):\n    return n\nassert f(1) == 1\nx = g()\nprint(f(1))\n", "f"),
        ("def print(x):\n    return x\ndef f(n):\n    return n\nassert f(1) == 1\nprint(f(1))\n", "f"),
    ]
    for source, entry in cases:
        assert not apply(source, entry).transformed


def test_public_assert_fingerprint_must_match() -> None:
    source = "def f(n):\n    return n\nassert f(1) == 1\nprint(f(1))\n"
    other = "assert f(2) == 2\n"
    result = apply(source, "f", other)
    assert not result.transformed
    assert result.reason == "adjacent_assert_not_in_public_prompt"


def test_output_sha_and_all_guards_are_stable() -> None:
    source = "def f(n):\n    return n\nassert f(1) == 1\nprint(f(1))\n"
    result = apply(source, "f")
    assert result.source_sha256 == hashlib.sha256(source.encode()).hexdigest()
    assert result.output_sha256 == hashlib.sha256(result.output_source.encode()).hexdigest()
    assert all(result.guard_results.values())
