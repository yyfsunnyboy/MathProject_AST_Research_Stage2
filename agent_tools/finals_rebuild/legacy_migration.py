"""
V1 Legacy Ab2 Migration Adapter.

Loads a legacy_replay_manifest.json and extracts the AI-generated code
section from each source file, wrapping it in a fenced legacy_replay_response
block. No model calls, no network calls, no TestSuite creation.

Manifest entries reference exact literal file paths only — this module
never globs or walks a directory to discover candidates. load_manifest()
fails closed on any entry pointing under skills/temp/ or a "backup" path,
referencing Ab3, or referencing a radicals skill/sample; migrate_entry()
additionally fails closed if the source file's own header declares the
Advanced Healer as ON/FULL/ENABLED (check_no_healer_on_header()),
independent of what the manifest's healer_status field claims.

extract_legacy_code() does not validate Python syntax — syntax-invalid
legacy code is intentionally passed through unchanged so the downstream
evaluator (not this migration step) is the one that observes and records
the syntax failure.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

MIGRATION_VERSION = "legacy_migration/1.0.0"

_MARKER = "# [AI GENERATED CODE]"

# Path-based rejection rules. Exact-path manifests only — these are
# substring/regex checks against the literal source_ab2_path string, never
# glob expansion and never directory scanning.
_FORBIDDEN_PATH_SUBSTRINGS = ("skills/temp/", "skills\\temp\\", "backup")
# Plain substring match (not \b-bounded regex): manifest paths use "Ab3"
# joined to surrounding text with underscores, e.g. "..._Ab3_run01.py" —
# "_" counts as a word character, so a \b-anchored regex would silently
# fail to match here.
_RADICALS_PATTERN = re.compile(r"radicals", re.IGNORECASE)

# Matches header lines that declare the Advanced Healer as fully engaged,
# e.g. "Advanced Healer: ON", "Advanced Healer: FULL", "Healer ON".
# Case-insensitive; deliberately does NOT match "OFF" or "MINIMAL (...)".
_HEALER_ON_HEADER_RE = re.compile(
    r"healer\s*[:\s]\s*(ON|FULL|ENABLED)\b", re.IGNORECASE
)
_HEALER_HEADER_SCAN_LINES = 20


def load_manifest(manifest_path: str | os.PathLike) -> list[dict]:
    """Load and validate a legacy_replay_manifest.json file.

    Fails closed (raises ValueError) on:
      - missing/invalid required fields
      - source_ab2_path pointing under skills/temp/ or any "backup" path
      - source_ab2_path referencing Ab3 or a radicals skill
      - skill_id referencing radicals

    Manifest entries are matched by their exact literal path only — this
    function never globs or walks any directory.
    """
    manifest_path = Path(manifest_path)
    with open(manifest_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    if not isinstance(data, list):
        raise ValueError(f"Manifest must be a JSON array, got {type(data)}")

    required_fields = {
        "sample_id",
        "skill_id",
        "model_id",
        "sample_index",
        "source_ab2_path",
        "source_kind",
        "is_original_raw",
        "legacy_replay",
        "healer_status",
        "source_file_hash",
    }
    for i, entry in enumerate(data):
        missing = required_fields - set(entry.keys())
        if missing:
            raise ValueError(f"Entry {i} missing fields: {missing}")
        if entry["source_kind"] != "legacy_extracted_code":
            raise ValueError(
                f"Entry {i} source_kind must be 'legacy_extracted_code', got {entry['source_kind']!r}"
            )
        if entry["is_original_raw"] is not False:
            raise ValueError(f"Entry {i} is_original_raw must be False")
        if entry["legacy_replay"] is not True:
            raise ValueError(f"Entry {i} legacy_replay must be True")
        if entry["healer_status"] not in ("healer_off", "basic_only", "unknown"):
            raise ValueError(
                f"Entry {i} healer_status invalid: {entry['healer_status']!r}"
            )

        path = entry["source_ab2_path"]
        skill_id = entry["skill_id"]
        sample_id = entry["sample_id"]

        lower_path = path.lower()
        for forbidden in _FORBIDDEN_PATH_SUBSTRINGS:
            if forbidden.lower() in lower_path:
                raise ValueError(
                    f"Entry {i} ({sample_id!r}): source_ab2_path {path!r} "
                    f"contains forbidden segment {forbidden!r}"
                )
        if "Ab3" in path:
            raise ValueError(
                f"Entry {i} ({sample_id!r}): source_ab2_path {path!r} references Ab3"
            )
        if _RADICALS_PATTERN.search(path) or _RADICALS_PATTERN.search(skill_id):
            raise ValueError(
                f"Entry {i} ({sample_id!r}): radicals sample rejected "
                f"(skill_id={skill_id!r}, path={path!r})"
            )

    return data


def check_no_healer_on_header(
    source_path: str | os.PathLike, project_root: str | os.PathLike
) -> None:
    """Raise ValueError if the file header at *source_path* declares the
    Advanced Healer as ON/FULL/ENABLED.

    Scans only the first _HEALER_HEADER_SCAN_LINES lines (the header
    block) — never the whole file, never other files. Fail-closed: this
    is a defense-in-depth check independent of the manifest's own
    healer_status field, so a mislabeled manifest entry cannot bypass it.
    """
    abs_path = Path(project_root) / source_path
    with open(abs_path, "r", encoding="utf-8") as fh:
        for _ in range(_HEALER_HEADER_SCAN_LINES):
            line = fh.readline()
            if not line:
                break
            if _HEALER_ON_HEADER_RE.search(line):
                raise ValueError(
                    f"{abs_path}: header indicates Advanced Healer is ON — "
                    f"legacy replay sources must not have Healer enabled. "
                    f"Offending line: {line.strip()!r}"
                )


def extract_legacy_code(source_path: str | os.PathLike, project_root: str | os.PathLike) -> str:
    """
    Find the ``# [AI GENERATED CODE]`` marker in *source_path* and return
    the code that follows it (not including the marker line itself).

    Raises ValueError if the marker cannot be found.
    """
    abs_path = Path(project_root) / source_path
    with open(abs_path, "r", encoding="utf-8") as fh:
        lines = fh.readlines()

    marker_idx = None
    for idx, line in enumerate(lines):
        if line.rstrip("\n\r") == _MARKER:
            marker_idx = idx
            break

    if marker_idx is None:
        raise ValueError(
            f"Marker {_MARKER!r} not found in {abs_path}. "
            "Cannot determine legacy generated section — failing closed."
        )

    extracted = "".join(lines[marker_idx + 1 :])
    return extracted


def compute_source_hash(source_path: str | os.PathLike) -> str:
    """Return the SHA-256 hex digest of the raw bytes of *source_path*."""
    with open(source_path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def build_legacy_replay_response(extracted_code: str) -> str:
    """Wrap *extracted_code* in a fenced ``legacy_replay_response`` block."""
    return f"```python\n{extracted_code}\n```"


def migrate_entry(entry: dict, project_root: str | os.PathLike) -> dict[str, Any]:
    """
    Migrate a single manifest entry.

    Returns a dict with:
      - metadata           : the original manifest entry
      - extracted_code     : code section after the AI GENERATED CODE marker
      - extracted_code_hash: sha256 of the extracted_code string (utf-8)
      - legacy_replay_response: fenced block wrapping extracted_code
      - source_file_hash   : sha256 of the raw source file bytes
      - migration_version  : MIGRATION_VERSION constant
    """
    source_rel = entry["source_ab2_path"]
    abs_source = Path(project_root) / source_rel

    check_no_healer_on_header(source_rel, project_root)
    extracted_code = extract_legacy_code(source_rel, project_root)
    source_file_hash = compute_source_hash(abs_source)
    extracted_code_hash = hashlib.sha256(extracted_code.encode("utf-8")).hexdigest()
    legacy_replay_response = build_legacy_replay_response(extracted_code)

    return {
        "metadata": entry,
        "extracted_code": extracted_code,
        "extracted_code_hash": extracted_code_hash,
        "legacy_replay_response": legacy_replay_response,
        "source_file_hash": source_file_hash,
        "migration_version": MIGRATION_VERSION,
    }


def migrate_all(
    manifest_path: str | os.PathLike,
    project_root: str | os.PathLike,
) -> list[dict[str, Any]]:
    """Migrate all entries in the manifest and return the results as a list."""
    entries = load_manifest(manifest_path)
    return [migrate_entry(entry, project_root) for entry in entries]
