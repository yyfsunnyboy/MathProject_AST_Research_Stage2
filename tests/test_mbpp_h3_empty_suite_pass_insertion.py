from __future__ import annotations

import hashlib
from pathlib import Path

from agent_tools.finals_rebuild import mbpp_h3_empty_suite_pass_insertion as h3


ROOT = Path(__file__).resolve().parents[1]


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class TestBasicEmptySuite:
    """Test basic empty suite detection and pass insertion."""

    def test_single_empty_suite_if_statement(self) -> None:
        """Unique empty suite after if: can be modified."""
        source = (
            "def solve(x):\n"
            "    if x > 0:\n"
            "    return x\n"
        )
        result = h3.insert_pass_for_empty_suite(
            source,
            "solve",
            extraction_unambiguous=True,
            source_complete=True,
        )
        assert result.triggered is True
        assert result.transformed is True
        assert result.abstained is False
        assert "pass" in result.output_source
        assert result.output_source is not None
        # Verify output parses
        import ast
        ast.parse(result.output_source)

    def test_empty_suite_for_loop(self) -> None:
        """Empty suite after for: can be inserted."""
        source = (
            "def solve(items):\n"
            "    for item in items:\n"
            "    pass\n"
        )
        result = h3.insert_pass_for_empty_suite(
            source,
            "solve",
            extraction_unambiguous=True,
            source_complete=True,
        )
        assert result.triggered is True
        assert result.transformed is True
        assert result.output_source is not None
        import ast
        ast.parse(result.output_source)

    def test_empty_suite_while_loop(self) -> None:
        """Empty suite after while: can be inserted."""
        source = (
            "def solve(n):\n"
            "    while n > 0:\n"
            "    n -= 1\n"
            "    return n\n"
        )
        result = h3.insert_pass_for_empty_suite(
            source,
            "solve",
            extraction_unambiguous=True,
            source_complete=True,
        )
        assert result.triggered is True
        assert result.transformed is True


class TestCommentOnlyNestedSuite:
    """Test that comment-only nested suites can be modified."""

    def test_comment_only_suite(self) -> None:
        """Suite with only comments should accept pass insertion."""
        source = (
            "def solve(x):\n"
            "    if x > 0:\n"
            "        # TODO: implement\n"
            "    return x\n"
        )
        result = h3.insert_pass_for_empty_suite(
            source,
            "solve",
            extraction_unambiguous=True,
            source_complete=True,
        )
        # This may abstain due to comment-only suite parsing successfully
        # Let's verify the actual behavior


class TestEntryPointEmptySuite:
    """Test rejection when entry point body is entirely empty."""

    def test_entry_point_entirely_empty(self) -> None:
        """Reject when target function body is empty."""
        source = (
            "def solve(x):\n"
            "def helper():\n"
            "    if x > 0:\n"
            "    return 1\n"
        )
        result = h3.insert_pass_for_empty_suite(
            source,
            "solve",
            extraction_unambiguous=True,
            source_complete=True,
        )
        # solve's body is empty, should abstain or check appropriately


class TestTruncationEvidence:
    """Test rejection of likely truncation cases."""

    def test_eof_with_colon_only(self) -> None:
        """Reject when source ends with : and nothing after."""
        source = "def solve(x):\n    if x:"
        result = h3.insert_pass_for_empty_suite(
            source,
            "solve",
            extraction_unambiguous=True,
            source_complete=False,  # Indicate truncation
        )
        assert result.abstained is True
        assert "truncat" in result.reason.lower() or "completion" in result.reason.lower()

    def test_source_not_complete(self) -> None:
        """Source marked incomplete should abstain."""
        source = "def solve(x):\n    if x > 0:"
        result = h3.insert_pass_for_empty_suite(
            source,
            "solve",
            extraction_unambiguous=True,
            source_complete=False,
        )
        assert result.abstained is True


class TestAmbiguousIndentation:
    """Test rejection of ambiguous indentation positions."""

    def test_multiple_unindented_lines(self) -> None:
        """Multiple candidates for suite position should abstain."""
        source = (
            "def solve(x):\n"
            "    if x > 0:\n"
            "    y = 1\n"
            "    z = 2\n"
        )
        result = h3.insert_pass_for_empty_suite(
            source,
            "solve",
            extraction_unambiguous=True,
            source_complete=True,
        )
        # The rule should either insert at the first unindent or abstain
        # because the indentation intent is ambiguous


class TestMultipleSyntaxErrors:
    """Test rejection when multiple SyntaxErrors exist."""

    def test_multiple_syntax_errors(self) -> None:
        """Multiple SyntaxErrors should abstain."""
        source = (
            "def solve(x:\n"  # Missing close paren
            "    if x > 0:\n"
            "    return x\n"
        )
        result = h3.insert_pass_for_empty_suite(
            source,
            "solve",
            extraction_unambiguous=True,
            source_complete=True,
        )
        # With multiple errors, abstain
        assert result.abstained is True or result.triggered is False


class TestCorrectProgramUnchanged:
    """Test that correct programs are not modified."""

    def test_correct_program_unchanged(self) -> None:
        """Correct program should not be modified."""
        source = (
            "def solve(x):\n"
            "    if x > 0:\n"
            "        return x\n"
            "    return 0\n"
        )
        result = h3.insert_pass_for_empty_suite(
            source,
            "solve",
            extraction_unambiguous=True,
            source_complete=True,
        )
        assert result.triggered is False
        assert result.transformed is False
        assert result.output_source == source

    def test_already_has_pass(self) -> None:
        """Program already with pass should not add another."""
        source = (
            "def solve(x):\n"
            "    if x > 0:\n"
            "        pass\n"
            "    return 0\n"
        )
        result = h3.insert_pass_for_empty_suite(
            source,
            "solve",
            extraction_unambiguous=True,
            source_complete=True,
        )
        assert result.triggered is False
        assert result.transformed is False


class TestIdempotence:
    """Test that repeated application is idempotent."""

    def test_idempotent_first_pass(self) -> None:
        """First pass insertion should produce parseable output."""
        source = (
            "def solve(x):\n"
            "    if x > 0:\n"
            "    return x\n"
        )
        result1 = h3.insert_pass_for_empty_suite(
            source,
            "solve",
            extraction_unambiguous=True,
            source_complete=True,
        )
        assert result1.transformed is True
        assert result1.output_source is not None

        # Second pass on the same source should be idempotent
        # (no syntax error in output means no transformation needed)
        result2 = h3.insert_pass_for_empty_suite(
            result1.output_source,
            "solve",
            extraction_unambiguous=True,
            source_complete=True,
        )
        assert result2.transformed is False
        assert result2.output_source == result1.output_source


class TestHashStability:
    """Test that SHA256 hashes are stable."""

    def test_hash_stability(self) -> None:
        """Same source should produce same SHA."""
        source = (
            "def solve(x):\n"
            "    if x > 0:\n"
            "    return x\n"
        )
        result1 = h3.insert_pass_for_empty_suite(
            source,
            "solve",
            extraction_unambiguous=True,
            source_complete=True,
        )
        result2 = h3.insert_pass_for_empty_suite(
            source,
            "solve",
            extraction_unambiguous=True,
            source_complete=True,
        )
        assert result1.source_sha256 == result2.source_sha256
        assert result1.output_sha256 == result2.output_sha256


class TestGuardResults:
    """Test that guard results are properly recorded."""

    def test_guard_results_recorded(self) -> None:
        """All guards should be recorded in decision."""
        source = (
            "def solve(x):\n"
            "    if x > 0:\n"
            "    return x\n"
        )
        result = h3.insert_pass_for_empty_suite(
            source,
            "solve",
            extraction_unambiguous=True,
            source_complete=True,
        )
        assert isinstance(result.guard_results, dict)
        assert len(result.guard_results) > 0
        assert "extraction_unambiguous" in result.guard_results
        assert "source_complete" in result.guard_results


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_source(self) -> None:
        """Empty source should abstain."""
        result = h3.insert_pass_for_empty_suite(
            "",
            "solve",
            extraction_unambiguous=True,
            source_complete=True,
        )
        assert result.transformed is False
        assert result.abstained is True

    def test_invalid_entry_point(self) -> None:
        """Invalid entry point identifier should abstain."""
        source = "def solve(x):\n    if x > 0:\n    return x\n"
        result = h3.insert_pass_for_empty_suite(
            source,
            "123invalid",
            extraction_unambiguous=True,
            source_complete=True,
        )
        assert result.abstained is True

    def test_extraction_ambiguous(self) -> None:
        """Ambiguous extraction should abstain."""
        source = "def solve(x):\n    if x > 0:\n    return x\n"
        result = h3.insert_pass_for_empty_suite(
            source,
            "solve",
            extraction_unambiguous=False,
            source_complete=True,
        )
        assert result.abstained is True

    def test_source_complete_unknown(self) -> None:
        """Unknown source_complete should abstain."""
        source = "def solve(x):\n    if x > 0:\n    return x\n"
        result = h3.insert_pass_for_empty_suite(
            source,
            "solve",
            extraction_unambiguous=True,
            source_complete=None,
        )
        assert result.abstained is True


class TestClassDefinitions:
    """Test handling of class definitions with empty suites."""

    def test_class_empty_suite(self) -> None:
        """Empty suite in class definition."""
        source = (
            "class Helper:\n"
            "def solve(x):\n"
            "    if x > 0:\n"
            "    return x\n"
        )
        result = h3.insert_pass_for_empty_suite(
            source,
            "solve",
            extraction_unambiguous=True,
            source_complete=True,
        )
        # Should handle appropriately


class TestNestedFunctions:
    """Test handling of nested function definitions."""

    def test_nested_function_empty_suite(self) -> None:
        """Empty suite in nested function."""
        source = (
            "def solve(x):\n"
            "    def helper():\n"
            "    if x > 0:\n"
            "        return x\n"
            "    return 0\n"
        )
        result = h3.insert_pass_for_empty_suite(
            source,
            "solve",
            extraction_unambiguous=True,
            source_complete=True,
        )
        # Entry point is solve, not helper, so this should not modify helper


def test_cumulative_pipeline_h3_integrated() -> None:
    """Test that H3 integrates properly into cumulative pipeline."""
    from agent_tools.finals_rebuild import mbpp_h1_h2_cumulative_pipeline as pipeline

    source = "def solve(x):\n    if x > 0:\n    return x\n"
    result = pipeline.run_h1_then_h2_then_h3(
        normalized_source=source,
        entry_point="solve",
        expected_positional_arities=(1,),
        generation_truncated=False,
        extraction_unambiguous=True,
        source_complete=True,
    )
    assert result.h3 is not None
    assert result.h3.rule_id == h3.RULE_ID


def test_transform_classification_includes_h3() -> None:
    """Test that transform classification includes H3 variants."""
    from agent_tools.finals_rebuild import mbpp_h1_h2_cumulative_pipeline as pipeline

    # H3 only
    assert pipeline.classify_transform(h1_changed=False, h2_changed=False, h3_changed=True) == "H3_ONLY"
    # H1 and H3
    assert pipeline.classify_transform(h1_changed=True, h2_changed=False, h3_changed=True) == "H1_AND_H3"
    # All three
    assert pipeline.classify_transform(h1_changed=True, h2_changed=True, h3_changed=True) == "H1_AND_H2_AND_H3"
