"""
Canonical code extraction for the finals-rebuild ablation pipeline.

Contract
--------
- Deterministic: identical raw text always produces identical
  extracted_code_hash.
- Non-modifying: grammar, imports, function names, and signatures are
  NEVER altered.
- Fail-visible: ambiguous, empty, and unsupported states are surfaced
  explicitly; nothing is silently treated as success.
- No Healer, no model calls, no code execution.

Extraction precedence
---------------------
1. python/py labelled fenced code blocks.
2. Other labelled or unlabelled fenced code blocks.
3. Full stripped text (no fences detected).

Ambiguity rule: if more than one candidate exists at the winning
priority level, status is "ambiguous".
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from agent_tools.finals_rebuild.artifacts import sha256_text

# Matches standard triple-backtick fenced blocks.
# Group 1: language tag (may be empty).
# Group 2: block content (everything up to the closing ```).
_FENCE_RE = re.compile(
    r"```([a-zA-Z0-9_+.-]*)\s*\n(.*?)```",
    re.DOTALL,
)

_PYTHON_LANGS: frozenset[str] = frozenset({"python", "py"})

EXTRACTION_STATUSES: frozenset[str] = frozenset(
    {"extracted", "ambiguous", "empty", "unsupported"}
)

EXTRACTION_METHODS: frozenset[str] = frozenset(
    {"fenced_python", "fenced_other", "plain_text", "none"}
)


@dataclass(frozen=True)
class ExtractionResult:
    """
    Result of one canonical extraction attempt.

    extraction_status
        "extracted"   – exactly one candidate found; code returned.
        "ambiguous"   – multiple candidates at the winning priority level.
        "empty"       – raw text is blank/all-whitespace, OR a fenced block
                        was found but its content was empty/whitespace-only.
        "unsupported" – reserved for future format restrictions.

    extraction_method
        "fenced_python" – from a python/py labelled fence.
        "fenced_other"  – from a non-python (or unlabelled) fence.
        "plain_text"    – no fences; full stripped text used.
        "none"          – nothing extracted.

    original_raw_hash is always populated.
    extracted_code is None when status is "ambiguous" or "unsupported",
    empty string ("") when status is "empty" due to an empty fenced block,
    and None when status is "empty" due to blank raw text.
    extracted_code_hash is None whenever status ≠ "extracted".
    """

    original_raw_hash: str
    extracted_code: Optional[str]
    extracted_code_hash: Optional[str]
    extraction_status: str
    extraction_method: str
    diagnostics: Dict[str, Any] = field(default_factory=dict)


def extract_code(raw_text: str) -> ExtractionResult:
    """
    Deterministically extract Python code from *raw_text*.

    See module docstring for the full contract.
    """
    raw_hash = sha256_text(raw_text)
    diag: Dict[str, Any] = {}

    all_fences: List[Tuple[str, str]] = _FENCE_RE.findall(raw_text)
    python_fences = [
        (lang, code)
        for lang, code in all_fences
        if lang.strip().lower() in _PYTHON_LANGS
    ]
    other_fences = [
        (lang, code)
        for lang, code in all_fences
        if lang.strip().lower() not in _PYTHON_LANGS
    ]

    diag["total_fenced_blocks"] = len(all_fences)
    diag["python_fenced_blocks"] = len(python_fences)
    diag["other_fenced_blocks"] = len(other_fences)

    # Priority 1: python/py labelled fences
    if python_fences:
        if len(python_fences) == 1:
            code = python_fences[0][1]
            if not code.strip():
                diag["empty_reason"] = "fenced python block contains no code"
                return _make(raw_hash, "", "empty", "fenced_python", diag)
            return _make(raw_hash, code, "extracted", "fenced_python", diag)
        diag["ambiguity_reason"] = (
            f"{len(python_fences)} python-fenced blocks found"
        )
        return _make(raw_hash, None, "ambiguous", "fenced_python", diag)

    # Priority 2: other (non-python or unlabelled) fences
    if other_fences:
        if len(other_fences) == 1:
            lang_label = other_fences[0][0].strip() or "unlabelled"
            diag["fence_language"] = lang_label
            code = other_fences[0][1]
            if not code.strip():
                diag["empty_reason"] = "fenced block contains no code"
                return _make(raw_hash, "", "empty", "fenced_other", diag)
            return _make(raw_hash, code, "extracted", "fenced_other", diag)
        diag["ambiguity_reason"] = (
            f"{len(other_fences)} non-python fenced blocks found"
        )
        return _make(raw_hash, None, "ambiguous", "fenced_other", diag)

    # Priority 3: full text (no fences)
    stripped = raw_text.strip()
    if not stripped:
        return _make(raw_hash, None, "empty", "none", diag)

    return _make(raw_hash, stripped, "extracted", "plain_text", diag)


def _make(
    raw_hash: str,
    code: Optional[str],
    status: str,
    method: str,
    diag: Dict[str, Any],
) -> ExtractionResult:
    # Compute hash only for non-None, non-empty extracted code.
    code_hash = sha256_text(code) if code else None
    return ExtractionResult(
        original_raw_hash=raw_hash,
        extracted_code=code,
        extracted_code_hash=code_hash,
        extraction_status=status,
        extraction_method=method,
        diagnostics=diag,
    )
