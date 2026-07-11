"""
Tests for agent_tools/finals_rebuild/extraction.py

Coverage (test IDs map to the 20-test checklist in the task spec)
------------------------------------------------------------------
 9  fenced Python block extraction
10  plain text (no fence) extraction
11  multiple Python blocks → ambiguous
12  empty raw fails (empty status)
13  extraction does not modify code content
 –  single non-python fence → extracted (fenced_other)
 –  unlabelled fence → extracted (fenced_other)
 –  mixed: 1 python + 1 other → python wins
 –  original_raw_hash is deterministic
 –  determinism: same raw → same extracted_code_hash
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from agent_tools.finals_rebuild.extraction import extract_code, ExtractionResult
from agent_tools.finals_rebuild.artifacts import sha256_text


# ── Test 9: fenced Python block ─────────────────────────────────────────────

def test_fenced_python_block_extracted():
    raw = "```python\ndef solve():\n    return 42\n```"
    result = extract_code(raw)
    assert result.extraction_status == "extracted"
    assert result.extraction_method == "fenced_python"
    assert result.extracted_code == "def solve():\n    return 42\n"
    assert result.extracted_code_hash is not None
    assert result.extracted_code_hash == sha256_text("def solve():\n    return 42\n")


def test_fenced_py_alias_extracted():
    raw = "```py\nx = 1\n```"
    result = extract_code(raw)
    assert result.extraction_status == "extracted"
    assert result.extraction_method == "fenced_python"
    assert result.extracted_code == "x = 1\n"


def test_fenced_python_uppercase_extracted():
    raw = "```Python\ndef f(): pass\n```"
    result = extract_code(raw)
    assert result.extraction_status == "extracted"
    assert result.extraction_method == "fenced_python"


# ── Test 10: plain text (no fence) ──────────────────────────────────────────

def test_plain_text_no_fence_extracted():
    raw = "def my_func():\n    return 1\n"
    result = extract_code(raw)
    assert result.extraction_status == "extracted"
    assert result.extraction_method == "plain_text"
    assert result.extracted_code == "def my_func():\n    return 1"
    assert result.extracted_code_hash is not None


def test_plain_text_strips_outer_whitespace():
    raw = "\n\ndef f(): pass\n\n"
    result = extract_code(raw)
    assert result.extraction_status == "extracted"
    assert result.extraction_method == "plain_text"
    assert result.extracted_code == "def f(): pass"


# ── Test 11: multiple Python blocks → ambiguous ──────────────────────────────

def test_multiple_python_blocks_ambiguous():
    raw = "```python\ndef a(): pass\n```\n\n```python\ndef b(): pass\n```"
    result = extract_code(raw)
    assert result.extraction_status == "ambiguous"
    assert result.extraction_method == "fenced_python"
    assert result.extracted_code is None
    assert result.extracted_code_hash is None
    assert "ambiguity_reason" in result.diagnostics


def test_multiple_other_blocks_ambiguous():
    raw = "```js\nconsole.log(1)\n```\n\n```\necho hello\n```"
    result = extract_code(raw)
    assert result.extraction_status == "ambiguous"
    assert result.extracted_code is None


# ── Test 12: empty raw → status=empty ────────────────────────────────────────

def test_empty_raw_returns_empty_status():
    result = extract_code("")
    assert result.extraction_status == "empty"
    assert result.extraction_method == "none"
    assert result.extracted_code is None
    assert result.extracted_code_hash is None


def test_whitespace_only_raw_returns_empty_status():
    result = extract_code("   \n\n  \t  ")
    assert result.extraction_status == "empty"


# ── Test 13: extraction does NOT modify code content ──────────────────────────

def test_extraction_does_not_modify_code():
    original_code = "def broken_syntax(:\n    pas\n"
    raw = f"```python\n{original_code}```"
    result = extract_code(raw)
    assert result.extraction_status == "extracted"
    assert result.extracted_code == original_code, (
        "extraction must not fix or alter code content"
    )


def test_extraction_preserves_indentation():
    code = "def f():\n    x = 1\n    return x\n"
    raw = f"```python\n{code}```"
    result = extract_code(raw)
    assert result.extracted_code == code


def test_extraction_preserves_blank_lines():
    code = "a = 1\n\nb = 2\n"
    raw = f"```python\n{code}```"
    result = extract_code(raw)
    assert result.extracted_code == code


# ── Non-python fenced blocks ─────────────────────────────────────────────────

def test_single_non_python_fence_extracted():
    raw = "```javascript\nconsole.log('hi');\n```"
    result = extract_code(raw)
    assert result.extraction_status == "extracted"
    assert result.extraction_method == "fenced_other"
    assert result.diagnostics.get("fence_language") == "javascript"


def test_unlabelled_fence_extracted():
    raw = "```\ndef f(): pass\n```"
    result = extract_code(raw)
    assert result.extraction_status == "extracted"
    assert result.extraction_method == "fenced_other"
    assert result.diagnostics.get("fence_language") == "unlabelled"


# ── Python wins over non-python when both present ────────────────────────────

def test_python_fence_wins_over_other_fence():
    raw = (
        "Some text.\n"
        "```bash\necho hello\n```\n"
        "```python\ndef f(): pass\n```\n"
    )
    result = extract_code(raw)
    assert result.extraction_status == "extracted"
    assert result.extraction_method == "fenced_python"
    assert "def f(): pass" in result.extracted_code


# ── Determinism and hash consistency ─────────────────────────────────────────

def test_original_raw_hash_is_correct():
    raw = "```python\ndef x(): pass\n```"
    result = extract_code(raw)
    assert result.original_raw_hash == sha256_text(raw)


def test_same_raw_produces_same_extraction():
    raw = "```python\ndef deterministic(): return 1\n```"
    r1 = extract_code(raw)
    r2 = extract_code(raw)
    assert r1.extracted_code_hash == r2.extracted_code_hash
    assert r1.original_raw_hash == r2.original_raw_hash


def test_different_raw_produces_different_hash():
    r1 = extract_code("```python\ndef a(): return 1\n```")
    r2 = extract_code("```python\ndef b(): return 2\n```")
    assert r1.extracted_code_hash != r2.extracted_code_hash
