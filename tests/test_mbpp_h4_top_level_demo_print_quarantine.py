"""Tests for H4: post-H2 stage-aware demo-print quarantine.

Fixed pipeline order under test: H1 -> H2 -> H3 -> H4. H4's rule
(quarantine_post_h2_top_level_demo_print) requires structural H2 provenance
-- it acts only when H2 itself reports changed=True for the cell and the
resulting `if __name__ == "__main__":` guard's sole statement structurally
matches (by ast.dump) the Assert that was top-level in H2's own input.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import ast

from agent_tools.finals_rebuild.mbpp_h2_module_assert_quarantine import (
    quarantine_module_assert_entrypoint_selftest,
)
from agent_tools.finals_rebuild.mbpp_h4_top_level_demo_print_quarantine import (
    quarantine_post_h2_top_level_demo_print,
    assert_fingerprint,
    RULE_ID,
)
from agent_tools.finals_rebuild.mbpp_h1_h2_cumulative_pipeline import (
    run_h1_then_h2_then_h3_then_h4,
)


def _fingerprint_of_sole_top_level_assert(source: str) -> str:
    tree = ast.parse(source)
    asserts = [n for n in tree.body if isinstance(n, ast.Assert)]
    assert len(asserts) == 1
    return assert_fingerprint(asserts[0])


def _run_h2_then_h4(h1_output: str, entry_point: str, fingerprints):
    h2 = quarantine_module_assert_entrypoint_selftest(
        h1_output, entry_point, extraction_unambiguous=True, source_complete=True
    )
    h4 = quarantine_post_h2_top_level_demo_print(
        h2_input_source=h1_output,
        h4_input_source=h2.output_source,
        h2_changed=h2.transformed,
        entry_point=entry_point,
        extraction_unambiguous=True,
        source_complete=True,
        public_assert_fingerprints=fingerprints,
    )
    return h2, h4


class TestPositiveTransform:
    """H4 must have at least one genuine positive transformation."""

    def test_assert_guard_and_adjacent_print_merged(self):
        source = "def solve(x):\n    return x * 2\n\nassert solve(2) == 4\nprint(solve(2))\n"
        fp = _fingerprint_of_sole_top_level_assert(source)
        h2, h4 = _run_h2_then_h4(source, "solve", [fp])
        assert h2.transformed is True
        assert h4.transformed is True, h4.reason
        assert h4.output_source is not None
        expected = (
            "def solve(x):\n"
            "    return x * 2\n"
            "\n"
            'if __name__ == "__main__":\n'
            "    assert solve(2) == 4\n"
            "    print(solve(2))\n"
        )
        assert h4.output_source == expected

    def test_print_moved_not_deleted(self):
        source = "def solve(x):\n    return x\n\nassert solve(1) == 1\nprint(solve(1))\n"
        fp = _fingerprint_of_sole_top_level_assert(source)
        h2, h4 = _run_h2_then_h4(source, "solve", [fp])
        assert h4.transformed is True
        assert "print(solve(1))" in h4.output_source

    def test_print_inside_same_guard_as_assert(self):
        source = "def solve(x):\n    return x\n\nassert solve(1) == 1\nprint(solve(1))\n"
        fp = _fingerprint_of_sole_top_level_assert(source)
        h2, h4 = _run_h2_then_h4(source, "solve", [fp])
        tree = ast.parse(h4.output_source)
        guards = [n for n in tree.body if isinstance(n, ast.If)]
        assert len(guards) == 1
        assert len(guards[0].body) == 2
        assert isinstance(guards[0].body[0], ast.Assert)
        assert isinstance(guards[0].body[1], ast.Expr)

    def test_statement_order_and_content_preserved(self):
        source = "def solve(x):\n    return x\n\nassert solve(1) == 1\nprint(solve(1))\n"
        fp = _fingerprint_of_sole_top_level_assert(source)
        h2, h4 = _run_h2_then_h4(source, "solve", [fp])
        tree = ast.parse(h4.output_source)
        guard = [n for n in tree.body if isinstance(n, ast.If)][0]
        assert isinstance(guard.body[0], ast.Assert)
        assert isinstance(guard.body[1], ast.Expr) and isinstance(guard.body[1].value, ast.Call)


class TestH2ProvenanceRequired:
    """Without confirmed H2 provenance, H4 must never trigger."""

    def test_arbitrary_preexisting_main_guard_does_not_trigger(self):
        source = (
            "def solve(x):\n    return x\n\n"
            'if __name__ == "__main__":\n    assert solve(1) == 1\n\n'
            "print(solve(1))\n"
        )
        fp = _fingerprint_of_sole_top_level_assert(
            "def solve(x):\n    return x\n\nassert solve(1) == 1\nprint(solve(1))\n"
        )
        h4 = quarantine_post_h2_top_level_demo_print(
            h2_input_source=source,
            h4_input_source=source,
            h2_changed=False,
            entry_point="solve",
            extraction_unambiguous=True,
            source_complete=True,
            public_assert_fingerprints=[fp],
        )
        assert h4.transformed is False
        assert h4.reason == "h2_did_not_transform_no_provenance"

    def test_h2_did_not_change_source_abstain(self):
        source = "def solve(x):\n    return x\n\nassert solve(1) == 2\nprint(solve(1))\n"
        fp = _fingerprint_of_sole_top_level_assert(source)
        h2, h4 = _run_h2_then_h4(source, "solve", [fp])
        # assert(1)==2 is still a literal selftest so H2 *would* transform it;
        # force h2_changed=False explicitly to simulate "H2 abstained" contract.
        h4_forced = quarantine_post_h2_top_level_demo_print(
            h2_input_source=source,
            h4_input_source=source,
            h2_changed=False,
            entry_point="solve",
            extraction_unambiguous=True,
            source_complete=True,
            public_assert_fingerprints=[fp],
        )
        assert h4_forced.transformed is False
        assert h4_forced.reason == "h2_did_not_transform_no_provenance"

    def test_guard_body_not_single_assert_no_provenance(self):
        # An if __name__ guard whose body has more than the assert alone must
        # not be treated as H2 provenance even if h2_changed is (incorrectly) True.
        h4_input = (
            "def solve(x):\n    return x\n\n"
            'if __name__ == "__main__":\n'
            "    assert solve(1) == 1\n"
            "    x = 5\n"
        )
        fp = _fingerprint_of_sole_top_level_assert(
            "def solve(x):\n    return x\n\nassert solve(1) == 1\nprint(solve(1))\n"
        )
        h4 = quarantine_post_h2_top_level_demo_print(
            h2_input_source="def solve(x):\n    return x\n\nassert solve(1) == 1\nprint(solve(1))\n",
            h4_input_source=h4_input,
            h2_changed=True,
            entry_point="solve",
            extraction_unambiguous=True,
            source_complete=True,
            public_assert_fingerprints=[fp],
        )
        assert h4.transformed is False
        assert h4.reason == "h2_guard_provenance_not_confirmed"


class TestNoRepeatedWrapping:
    def test_second_pass_does_not_rewrap(self):
        source = "def solve(x):\n    return x\n\nassert solve(1) == 1\nprint(solve(1))\n"
        fp = _fingerprint_of_sole_top_level_assert(source)
        h2, h4_first = _run_h2_then_h4(source, "solve", [fp])
        assert h4_first.transformed is True
        h2_second = quarantine_module_assert_entrypoint_selftest(
            h4_first.output_source, "solve", extraction_unambiguous=True, source_complete=True
        )
        h4_second = quarantine_post_h2_top_level_demo_print(
            h2_input_source=h4_first.output_source,
            h4_input_source=h2_second.output_source,
            h2_changed=h2_second.transformed,
            entry_point="solve",
            extraction_unambiguous=True,
            source_complete=True,
            public_assert_fingerprints=[fp],
        )
        assert h4_second.transformed is False
        assert h4_second.output_source == h4_first.output_source


class TestAssertNotYetH2Processed:
    def test_top_level_assert_no_h2_change_abstains(self):
        """Stage contract: an assert H2 has not (yet) moved must abstain, not
        fall back to old top-level-assert-seeking behavior."""
        source = "def solve(x):\n    return x\n\nassert solve(1) == 1\nprint(solve(1))\n"
        fp = _fingerprint_of_sole_top_level_assert(source)
        h4 = quarantine_post_h2_top_level_demo_print(
            h2_input_source=source,
            h4_input_source=source,  # H3 pass-through, H2 supposedly did nothing
            h2_changed=False,
            entry_point="solve",
            extraction_unambiguous=True,
            source_complete=True,
            public_assert_fingerprints=[fp],
        )
        assert h4.transformed is False
        assert h4.reason == "h2_did_not_transform_no_provenance"


class TestFunctionAndMethodPrintsUnchanged:
    def test_print_inside_function_untouched(self):
        source = (
            "def solve(x):\n    print(x)\n    return x\n\n"
            "assert solve(1) == 1\nprint(solve(1))\n"
        )
        fp = _fingerprint_of_sole_top_level_assert(
            "def solve(x):\n    return x\n\nassert solve(1) == 1\nprint(solve(1))\n"
        )
        h2, h4 = _run_h2_then_h4(source, "solve", [fp])
        assert h4.transformed is True
        assert "print(x)" in h4.output_source
        # the in-function print must remain inside the function, not merged
        tree = ast.parse(h4.output_source)
        fn = [n for n in tree.body if isinstance(n, ast.FunctionDef)][0]
        assert any(
            isinstance(s, ast.Expr)
            and isinstance(s.value, ast.Call)
            and isinstance(s.value.func, ast.Name)
            and s.value.func.id == "print"
            for s in fn.body
        )

    def test_print_inside_method_untouched(self):
        source = (
            "class Foo:\n"
            "    def bar(self):\n"
            "        print('hi')\n"
            "        return 1\n\n"
            "def solve(x):\n    return x\n\n"
            "assert solve(1) == 1\nprint(solve(1))\n"
        )
        fp = _fingerprint_of_sole_top_level_assert(
            "def solve(x):\n    return x\n\nassert solve(1) == 1\nprint(solve(1))\n"
        )
        h2, h4 = _run_h2_then_h4(source, "solve", [fp])
        assert h4.transformed is True
        assert "print('hi')" in h4.output_source


class TestShadowedPrintAbstains:
    def test_shadowed_print_abstains(self):
        source = (
            "def solve(x):\n    return x\n\n"
            "print = None\n"
            "assert solve(1) == 1\nprint(solve(1))\n"
        )
        # note: assert must still be the sole top-level assert & H2 must transform
        h2 = quarantine_module_assert_entrypoint_selftest(
            source, "solve", extraction_unambiguous=True, source_complete=True
        )
        fp = _fingerprint_of_sole_top_level_assert(
            "def solve(x):\n    return x\n\nassert solve(1) == 1\nprint(solve(1))\n"
        )
        h4 = quarantine_post_h2_top_level_demo_print(
            h2_input_source=source,
            h4_input_source=h2.output_source,
            h2_changed=h2.transformed,
            entry_point="solve",
            extraction_unambiguous=True,
            source_complete=True,
            public_assert_fingerprints=[fp],
        )
        assert h4.transformed is False
        assert h4.reason == "print_name_shadowed"


class TestNonLiteralArgumentAbstains:
    def test_non_literal_print_argument_abstains(self):
        source = (
            "def solve(x):\n    return x\n\n"
            "y = compute()\n"
            "assert solve(1) == 1\nprint(y)\n"
        )
        h2 = quarantine_module_assert_entrypoint_selftest(
            source, "solve", extraction_unambiguous=True, source_complete=True
        )
        fp = _fingerprint_of_sole_top_level_assert(
            "def solve(x):\n    return x\n\nassert solve(1) == 1\nprint(solve(1))\n"
        )
        h4 = quarantine_post_h2_top_level_demo_print(
            h2_input_source=source,
            h4_input_source=h2.output_source,
            h2_changed=h2.transformed,
            entry_point="solve",
            extraction_unambiguous=True,
            source_complete=True,
            public_assert_fingerprints=[fp],
        )
        assert h4.transformed is False


class TestNonEntryPointCallAbstains:
    def test_print_of_other_function_call_abstains(self):
        source = (
            "def solve(x):\n    return x\n\n"
            "assert solve(1) == 1\nprint(other(1))\n"
        )
        h2 = quarantine_module_assert_entrypoint_selftest(
            source, "solve", extraction_unambiguous=True, source_complete=True
        )
        fp = _fingerprint_of_sole_top_level_assert(
            "def solve(x):\n    return x\n\nassert solve(1) == 1\nprint(solve(1))\n"
        )
        h4 = quarantine_post_h2_top_level_demo_print(
            h2_input_source=source,
            h4_input_source=h2.output_source,
            h2_changed=h2.transformed,
            entry_point="solve",
            extraction_unambiguous=True,
            source_complete=True,
            public_assert_fingerprints=[fp],
        )
        assert h4.transformed is False
        assert h4.reason == "print_arguments_not_literal_or_entrypoint_literal_call"


class TestGlobalMutationCallAbstains:
    def test_other_top_level_call_abstains(self):
        source = (
            "def solve(x):\n    return x\n\n"
            "register(solve)\n"
            "assert solve(1) == 1\nprint(solve(1))\n"
        )
        h2 = quarantine_module_assert_entrypoint_selftest(
            source, "solve", extraction_unambiguous=True, source_complete=True
        )
        fp = _fingerprint_of_sole_top_level_assert(
            "def solve(x):\n    return x\n\nassert solve(1) == 1\nprint(solve(1))\n"
        )
        h4 = quarantine_post_h2_top_level_demo_print(
            h2_input_source=source,
            h4_input_source=h2.output_source,
            h2_changed=h2.transformed,
            entry_point="solve",
            extraction_unambiguous=True,
            source_complete=True,
            public_assert_fingerprints=[fp],
        )
        assert h4.transformed is False
        assert h4.reason == "other_unclassified_top_level_call_present"


class TestMultipleAssertBoundary:
    def test_multiple_top_level_asserts_h2_abstains_h4_abstains(self):
        source = (
            "def solve(x):\n    return x\n\n"
            "assert solve(1) == 1\n"
            "assert solve(2) == 2\n"
            "print(solve(1))\n"
        )
        h2 = quarantine_module_assert_entrypoint_selftest(
            source, "solve", extraction_unambiguous=True, source_complete=True
        )
        assert h2.transformed is False
        fp = _fingerprint_of_sole_top_level_assert(
            "def solve(x):\n    return x\n\nassert solve(1) == 1\nprint(solve(1))\n"
        )
        h4 = quarantine_post_h2_top_level_demo_print(
            h2_input_source=source,
            h4_input_source=h2.output_source,
            h2_changed=h2.transformed,
            entry_point="solve",
            extraction_unambiguous=True,
            source_complete=True,
            public_assert_fingerprints=[fp],
        )
        assert h4.transformed is False
        assert h4.reason == "h2_did_not_transform_no_provenance"


class TestUnparseableAbstains:
    def test_unparseable_h4_input_abstains(self):
        h4 = quarantine_post_h2_top_level_demo_print(
            h2_input_source="def solve(x):\n    return x\n\nassert solve(1) == 1\nprint(solve(1))\n",
            h4_input_source="def solve(x):\n    return x\n    ][broken",
            h2_changed=True,
            entry_point="solve",
            extraction_unambiguous=True,
            source_complete=True,
            public_assert_fingerprints=[],
        )
        assert h4.transformed is False
        assert h4.reason == "h4_input_source_unparseable"


class TestExtractionAndCompletionFlags:
    def test_ambiguous_extraction_abstains(self):
        source = "def solve(x):\n    return x\n\nassert solve(1) == 1\nprint(solve(1))\n"
        h2 = quarantine_module_assert_entrypoint_selftest(
            source, "solve", extraction_unambiguous=True, source_complete=True
        )
        fp = _fingerprint_of_sole_top_level_assert(source)
        h4 = quarantine_post_h2_top_level_demo_print(
            h2_input_source=source,
            h4_input_source=h2.output_source,
            h2_changed=h2.transformed,
            entry_point="solve",
            extraction_unambiguous=False,
            source_complete=True,
            public_assert_fingerprints=[fp],
        )
        assert h4.transformed is False
        assert h4.reason == "extraction_ambiguous_or_unknown"

    def test_incomplete_source_abstains(self):
        source = "def solve(x):\n    return x\n\nassert solve(1) == 1\nprint(solve(1))\n"
        h2 = quarantine_module_assert_entrypoint_selftest(
            source, "solve", extraction_unambiguous=True, source_complete=True
        )
        fp = _fingerprint_of_sole_top_level_assert(source)
        h4 = quarantine_post_h2_top_level_demo_print(
            h2_input_source=source,
            h4_input_source=h2.output_source,
            h2_changed=h2.transformed,
            entry_point="solve",
            extraction_unambiguous=True,
            source_complete=False,
            public_assert_fingerprints=[fp],
        )
        assert h4.transformed is False
        assert h4.reason == "source_truncated_or_completion_unknown"


class TestIdempotence:
    def test_direct_reapplication_idempotent(self):
        source = "def solve(x):\n    return x\n\nassert solve(1) == 1\nprint(solve(1))\n"
        fp = _fingerprint_of_sole_top_level_assert(source)
        h2, h4_first = _run_h2_then_h4(source, "solve", [fp])
        assert h4_first.transformed is True
        h4_second = quarantine_post_h2_top_level_demo_print(
            h2_input_source=source,
            h4_input_source=h4_first.output_source,
            h2_changed=h2.transformed,
            entry_point="solve",
            extraction_unambiguous=True,
            source_complete=True,
            public_assert_fingerprints=[fp],
        )
        assert h4_second.transformed is False
        assert h4_second.output_source == h4_first.output_source

    def test_full_pipeline_idempotent(self):
        source = "def solve(x):\n    return x * 2\n\nassert solve(2) == 4\nprint(solve(2))\n"
        fp = _fingerprint_of_sole_top_level_assert(source)
        result1 = run_h1_then_h2_then_h3_then_h4(
            normalized_source=source,
            entry_point="solve",
            expected_positional_arities=(1,),
            generation_truncated=False,
            extraction_unambiguous=True,
            source_complete=True,
            public_assert_fingerprints=[fp],
        )
        assert result1.h4.changed is True
        result2 = run_h1_then_h2_then_h3_then_h4(
            normalized_source=result1.final_source,
            entry_point="solve",
            expected_positional_arities=(1,),
            generation_truncated=False,
            extraction_unambiguous=True,
            source_complete=True,
            public_assert_fingerprints=[fp],
        )
        assert result2.transform_class == "UNCHANGED"
        assert result2.final_source == result1.final_source


class TestHashRecording:
    def test_source_and_output_sha(self):
        source = "def solve(x):\n    return x\n\nassert solve(1) == 1\nprint(solve(1))\n"
        fp = _fingerprint_of_sole_top_level_assert(source)
        h2, h4 = _run_h2_then_h4(source, "solve", [fp])
        assert h4.source_sha256 != h4.output_sha256
        h2b, h4b = _run_h2_then_h4(source, "solve", [fp])
        assert h4.source_sha256 == h4b.source_sha256
        assert h4.output_sha256 == h4b.output_sha256


class TestTransformClassification:
    """H1_ONLY / H2_ONLY / H3_ONLY / H4_ONLY / MULTI_STAGE / UNCHANGED."""

    def test_h1_only(self):
        source = "def helper(x):\n    return x + 1\n"
        result = run_h1_then_h2_then_h3_then_h4(
            normalized_source=source,
            entry_point="solve",
            expected_positional_arities=(1,),
            generation_truncated=False,
            extraction_unambiguous=True,
            source_complete=True,
            public_assert_fingerprints=[],
        )
        assert result.transform_class == "H1_ONLY"

    def test_h2_only(self):
        source = "def solve(x):\n    return x + 1\n\nassert solve(1) == 2\n"
        result = run_h1_then_h2_then_h3_then_h4(
            normalized_source=source,
            entry_point="solve",
            expected_positional_arities=(1,),
            generation_truncated=False,
            extraction_unambiguous=True,
            source_complete=True,
            public_assert_fingerprints=[],
        )
        assert result.transform_class == "H2_ONLY"

    def test_h3_only(self):
        source = "def solve(x):\n    if x > 0:\n    return x\n"
        result = run_h1_then_h2_then_h3_then_h4(
            normalized_source=source,
            entry_point="solve",
            expected_positional_arities=(1,),
            generation_truncated=False,
            extraction_unambiguous=True,
            source_complete=True,
            public_assert_fingerprints=[],
        )
        assert result.transform_class == "H3_ONLY"

    def test_h4_only_not_reachable_without_h2(self):
        """H4 structurally cannot fire without H2 provenance, so H4_ONLY is
        not reachable through the public pipeline entry point -- this test
        documents that fact rather than asserting a false positive."""
        source = "def solve(x):\n    return x\n\nassert solve(1) == 1\nprint(solve(1))\n"
        result = run_h1_then_h2_then_h3_then_h4(
            normalized_source=source,
            entry_point="solve",
            expected_positional_arities=(1,),
            generation_truncated=False,
            extraction_unambiguous=True,
            source_complete=True,
            public_assert_fingerprints=[_fingerprint_of_sole_top_level_assert(source)],
        )
        assert result.transform_class != "H4_ONLY"
        assert result.transform_class == "H2_AND_H4"

    def test_multi_stage_h2_and_h4(self):
        source = "def solve(x):\n    return x * 2\n\nassert solve(2) == 4\nprint(solve(2))\n"
        fp = _fingerprint_of_sole_top_level_assert(source)
        result = run_h1_then_h2_then_h3_then_h4(
            normalized_source=source,
            entry_point="solve",
            expected_positional_arities=(1,),
            generation_truncated=False,
            extraction_unambiguous=True,
            source_complete=True,
            public_assert_fingerprints=[fp],
        )
        assert result.transform_class == "H2_AND_H4"

    def test_unchanged(self):
        source = "def solve(x):\n    return x\n"
        result = run_h1_then_h2_then_h3_then_h4(
            normalized_source=source,
            entry_point="solve",
            expected_positional_arities=(1,),
            generation_truncated=False,
            extraction_unambiguous=True,
            source_complete=True,
            public_assert_fingerprints=[],
        )
        assert result.transform_class == "UNCHANGED"


class TestRuleIdentity:
    def test_rule_id_stable(self):
        assert RULE_ID == "top_level_demo_print_quarantine_v0"


if __name__ == "__main__":
    import inspect

    passed = 0
    failed = 0
    for name, obj in list(globals().items()):
        if inspect.isclass(obj) and name.startswith("Test"):
            for method_name, method in inspect.getmembers(obj, predicate=inspect.isfunction):
                if method_name.startswith("test_"):
                    try:
                        instance = obj()
                        method(instance)
                        print(f"PASS {name}.{method_name}")
                        passed += 1
                    except AssertionError as e:
                        print(f"FAIL {name}.{method_name}: {e}")
                        failed += 1
                    except Exception as e:
                        print(f"FAIL {name}.{method_name}: {type(e).__name__}: {e}")
                        failed += 1
    print(f"\n{passed} passed, {failed} failed")
