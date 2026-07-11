"""
V1 Legacy Ab2 Migration Adapter.

Loads a legacy_replay_manifest.json and extracts the AI-generated code
section from each source file, wrapping it in a fenced legacy_replay_response
block. No model calls, no network calls, no TestSuite creation.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

MIGRATION_VERSION = "legacy_migration/1.0.0"

_MARKER = "# [AI GENERATED CODE]"


def load_manifest(manifest_path: str | os.PathLike) -> list[dict]:
    """Load and validate a legacy_replay_manifest.json file."""
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

    return data


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
