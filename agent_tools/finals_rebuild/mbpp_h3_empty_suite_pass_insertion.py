"""Guarded empty-suite pass insertion for IndentationError recovery.

This rule inserts a single ``pass`` statement into a compound statement's suite
when SyntaxError uniquely indicates "expected an indented block".

Used only when:
- Error is uniquely locatable to an empty suite after compound statement
- Insertion position and indentation are unambiguous
- No truncation, multi-error, or core logic loss evidence
- Empty suite is not the entire body of the target entry point
"""

from __future__ import annotations

import ast
import hashlib
import re
from dataclasses import asdict, dataclass
from typing import Any


RULE_ID = "empty_suite_pass_insertion_v0"
RULE_STATUS = "development_candidate_not_frozen"


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class EmptySuiteDecision:
    rule_id: str
    rule_status: str
    triggered: bool
    transformed: bool
    abstained: bool
    reason: str
    parse_error_message: str
    error_line_number: int | None
    empty_suite_location: str
    source_sha256: str
    output_sha256: str
    output_source: str
    guard_results: dict[str, bool]

    def record(self) -> dict[str, Any]:
        return asdict(self)


def _decision(
    source: str,
    *,
    triggered: bool,
    transformed: bool,
    reason: str,
    parse_error_message: str = "",
    error_line_number: int | None = None,
    empty_suite_location: str = "",
    guard_results: dict[str, bool] | None = None,
    output_source: str | None = None,
) -> EmptySuiteDecision:
    if guard_results is None:
        guard_results = {}
    output = source if output_source is None else output_source
    return EmptySuiteDecision(
        rule_id=RULE_ID,
        rule_status=RULE_STATUS,
        triggered=triggered,
        transformed=transformed,
        abstained=not transformed,
        reason=reason,
        parse_error_message=parse_error_message,
        error_line_number=error_line_number,
        empty_suite_location=empty_suite_location,
        source_sha256=_sha256_text(source),
        output_sha256=_sha256_text(output),
        output_source=output,
        guard_results=dict(sorted(guard_results.items())),
    )


def _is_expected_indent_error(error_msg: str) -> bool:
    """Check if SyntaxError is specifically about missing indented block."""
    patterns = [
        r"expected an indented block",
        r"expecting indentation",
        r"unindent does not match",
    ]
    return any(re.search(pattern, error_msg, re.IGNORECASE) for pattern in patterns)


def _analyze_syntax_error(source: str) -> tuple[bool, str, int | None]:
    """Try to parse and extract SyntaxError details.

    Returns (is_expected_indent_error, error_message, error_lineno)
    """
    try:
        ast.parse(source)
        return False, "", None
    except SyntaxError as e:
        msg = str(e.msg) if hasattr(e, "msg") else str(e)
        lineno = e.lineno if hasattr(e, "lineno") else None
        is_indent = _is_expected_indent_error(msg)
        return is_indent, msg, lineno
    except Exception:
        return False, "", None


def _extract_error_context(source: str, lineno: int | None) -> str:
    """Extract the source context around the error line."""
    if lineno is None or lineno < 1:
        return ""
    lines = source.splitlines()
    if lineno - 1 >= len(lines):
        return ""
    context_line = lines[lineno - 1]
    return context_line.rstrip()


def _find_insertion_point(source: str, lineno: int | None) -> tuple[int | None, int | None, str]:
    """Find where to insert pass after a compound statement.

    The error lineno points to the line where the error is detected (usually the first
    unindented line after a compound statement without a suite). We need to work
    backwards to find the compound statement that caused this.

    Returns (line_index, col_offset, indentation_string) or (None, None, "") if ambiguous.
    """
    if lineno is None or lineno < 1:
        return None, None, ""

    lines = source.splitlines(keepends=True)
    error_line_idx = lineno - 1  # Convert to 0-indexed

    if error_line_idx >= len(lines):
        return None, None, ""

    # The error line is where we see insufficient indentation
    error_line = lines[error_line_idx]
    error_line_text = error_line.rstrip('\r\n')
    error_indent = len(error_line_text) - len(error_line_text.lstrip())

    # Look backwards to find the compound statement (line ending with :)
    compound_line_idx = None
    for i in range(error_line_idx - 1, -1, -1):
        prev_line = lines[i]
        prev_line_text = prev_line.rstrip('\r\n')
        prev_stripped = prev_line_text.rstrip()

        if prev_stripped.endswith(':'):
            compound_line_idx = i
            break

        # Stop if we hit something at same or lower indentation (different statement)
        prev_indent = len(prev_line_text) - len(prev_line_text.lstrip())
        if prev_indent <= error_indent and prev_stripped:
            break

    if compound_line_idx is None:
        return None, None, ""

    # Now we found the compound statement at compound_line_idx
    compound_line = lines[compound_line_idx]
    compound_line_text = compound_line.rstrip('\r\n')
    base_indent = len(compound_line_text) - len(compound_line_text.lstrip())
    suite_indent = base_indent + 4

    # Verify that error_line is at the first unindented location after the colon
    # i.e., suite should have started at compound_line_idx + 1
    insertion_idx = compound_line_idx + 1

    if insertion_idx >= len(lines):
        # EOF right after :
        return insertion_idx, suite_indent, ' ' * suite_indent

    # Check what's at the insertion point
    insertion_line = lines[insertion_idx]
    insertion_line_text = insertion_line.rstrip('\r\n')
    insertion_stripped = insertion_line_text.lstrip()

    # Empty or comment-only lines are fine for insertion
    if not insertion_stripped or insertion_stripped.startswith('#'):
        return insertion_idx, suite_indent, ' ' * suite_indent

    # Otherwise, check indentation
    insertion_indent = len(insertion_line_text) - len(insertion_line_text.lstrip())
    if insertion_indent < suite_indent:
        # Unindent found - this is where we insert
        return insertion_idx, suite_indent, ' ' * suite_indent

    # If we get here, there's a suite already or something else
    return None, None, ""


def _count_compound_statements_at_eof(source: str) -> int:
    """Count how many lines end with : at EOF area."""
    lines = source.rstrip().splitlines()
    if not lines:
        return 0
    count = 0
    for line in lines[-5:]:  # Check last 5 lines
        if line.rstrip().endswith(':'):
            count += 1
    return count


def _is_entry_point_entirely_empty(
    tree: ast.Module, entry_point: str
) -> bool:
    """Check if the entry point function body is empty or only pass/..."""
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == entry_point:
            if not node.body:
                return True
            if len(node.body) == 1:
                stmt = node.body[0]
                if isinstance(stmt, ast.Pass):
                    return True
                if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
                    if stmt.value.value is Ellipsis or stmt.value.value == "":
                        return True
            return False
    return False


def _insert_pass(
    source: str,
    insert_line_idx: int,
    suite_indent_str: str
) -> str | None:
    """Insert pass at the specified line with the given indentation."""
    lines = source.splitlines(keepends=True)
    if insert_line_idx < 0 or insert_line_idx > len(lines):
        return None

    newline = "\r\n" if "\r\n" in source else "\n"
    pass_line = suite_indent_str + "pass" + newline

    try:
        new_lines = lines[:insert_line_idx] + [pass_line] + lines[insert_line_idx:]
        result = "".join(new_lines)
        # Verify it parses
        ast.parse(result)
        return result
    except (SyntaxError, Exception):
        return None


def _verify_no_other_errors(source: str) -> bool:
    """Ensure the source has no other SyntaxErrors besides the empty suite."""
    try:
        ast.parse(source)
        return True
    except SyntaxError as e:
        msg = str(e.msg) if hasattr(e, "msg") else str(e)
        # Only allow if it's the empty suite error
        return _is_expected_indent_error(msg)
    except Exception:
        return False


def insert_pass_for_empty_suite(
    source: str,
    entry_point: str,
    *,
    extraction_unambiguous: bool | None,
    source_complete: bool | None,
) -> EmptySuiteDecision:
    """Apply empty suite pass insertion only when every guard is satisfied."""

    base_guards = {
        "extraction_unambiguous": extraction_unambiguous is True,
        "source_complete": source_complete is True,
        "source_is_valid_string": isinstance(source, str),
        "has_syntax_error": False,
        "error_is_empty_suite": False,
        "single_error_location": False,
        "insertion_point_unambiguous": False,
        "entry_point_not_entirely_empty": True,
        "no_truncation_evidence": True,
        "insertion_produces_valid_python": False,
        "pass_inserted_exactly_once": False,
    }

    # Pre-checks
    if not isinstance(source, str):
        return _decision(
            source if isinstance(source, str) else "",
            triggered=False,
            transformed=False,
            reason="invalid_source_type",
            guard_results=base_guards,
        )

    if not source.strip():
        return _decision(
            source,
            triggered=False,
            transformed=False,
            reason="empty_source",
            guard_results=base_guards,
        )

    base_guards["source_is_valid_string"] = True

    if extraction_unambiguous is not True:
        return _decision(
            source,
            triggered=False,
            transformed=False,
            reason="extraction_ambiguous_or_unknown",
            guard_results=base_guards,
        )

    if source_complete is not True:
        return _decision(
            source,
            triggered=False,
            transformed=False,
            reason="source_truncated_or_completion_unknown",
            guard_results=base_guards,
        )

    # Check for syntax error
    is_indent_error, error_msg, error_lineno = _analyze_syntax_error(source)
    base_guards["has_syntax_error"] = True
    base_guards["error_is_empty_suite"] = is_indent_error

    if not is_indent_error:
        return _decision(
            source,
            triggered=False,
            transformed=False,
            reason="syntax_error_not_empty_suite" if error_msg else "no_syntax_error",
            parse_error_message=error_msg,
            guard_results=base_guards,
        )

    # Verify no truncation evidence (source ends with incomplete compound statement)
    if source.rstrip().endswith(':'):
        # Line ends with : but no body at all - could be truncation
        base_guards["no_truncation_evidence"] = False
        return _decision(
            source,
            triggered=True,
            transformed=False,
            reason="possible_truncation_at_eof",
            parse_error_message=error_msg,
            error_line_number=error_lineno,
            guard_results=base_guards,
        )

    base_guards["no_truncation_evidence"] = True

    # Find insertion point
    insert_line_idx, suite_indent, indent_str = _find_insertion_point(source, error_lineno)
    base_guards["single_error_location"] = (
        error_lineno is not None and insert_line_idx is not None
    )
    base_guards["insertion_point_unambiguous"] = (
        insert_line_idx is not None and insert_line_idx >= 0
    )

    if insert_line_idx is None:
        return _decision(
            source,
            triggered=True,
            transformed=False,
            reason="empty_suite_location_ambiguous",
            parse_error_message=error_msg,
            error_line_number=error_lineno,
            guard_results=base_guards,
        )

    # Check entry point is not entirely empty
    try:
        tree = ast.parse(source.rstrip() + "\npass")  # Temporarily add pass to parse
    except Exception:
        tree = None

    if tree is not None:
        if _is_entry_point_entirely_empty(tree, entry_point):
            base_guards["entry_point_not_entirely_empty"] = False
            return _decision(
                source,
                triggered=True,
                transformed=False,
                reason="entry_point_body_entirely_empty",
                parse_error_message=error_msg,
                error_line_number=error_lineno,
                empty_suite_location=_extract_error_context(source, error_lineno),
                guard_results=base_guards,
            )

    # Attempt insertion
    output = _insert_pass(source, insert_line_idx, indent_str)
    base_guards["insertion_produces_valid_python"] = output is not None

    if output is None:
        return _decision(
            source,
            triggered=True,
            transformed=False,
            reason="pass_insertion_failed",
            parse_error_message=error_msg,
            error_line_number=error_lineno,
            empty_suite_location=_extract_error_context(source, error_lineno),
            guard_results=base_guards,
        )

    # Verify exactly one pass was inserted
    original_pass_count = source.count("pass")
    output_pass_count = output.count("pass")
    passes_added = output_pass_count - original_pass_count
    base_guards["pass_inserted_exactly_once"] = passes_added == 1

    if passes_added != 1:
        return _decision(
            source,
            triggered=True,
            transformed=False,
            reason="unexpected_pass_count_change",
            parse_error_message=error_msg,
            error_line_number=error_lineno,
            empty_suite_location=_extract_error_context(source, error_lineno),
            output_source=output,
            guard_results=base_guards,
        )

    # Final verification: output is valid Python and only pass was added
    try:
        output_tree = ast.parse(output)
    except SyntaxError:
        return _decision(
            source,
            triggered=True,
            transformed=False,
            reason="output_unparseable",
            parse_error_message=error_msg,
            error_line_number=error_lineno,
            empty_suite_location=_extract_error_context(source, error_lineno),
            output_source=output,
            guard_results=base_guards,
        )

    # Success
    return _decision(
        source,
        triggered=True,
        transformed=True,
        reason="empty_suite_pass_inserted",
        parse_error_message=error_msg,
        error_line_number=error_lineno,
        empty_suite_location=_extract_error_context(source, error_lineno),
        output_source=output,
        guard_results=base_guards,
    )
