"""
Tests for agent_tools/finals_rebuild/legacy_migration.py

All 12 required test cases for the V1 legacy Ab2 migration adapter.
"""

from __future__ import annotations

import hashlib
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import pytest

from agent_tools.finals_rebuild.legacy_migration import (
    MIGRATION_VERSION,
    build_legacy_replay_response,
    compute_source_hash,
    extract_legacy_code,
    load_manifest,
    migrate_all,
    migrate_entry,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
_MANIFEST = os.path.join(
    _ROOT, "tests", "finals_rebuild", "fixtures", "legacy_replay_manifest.json"
)
_MARKER = "# [AI GENERATED CODE]"

# A known fixture file used for byte-identity test
_KNOWN_SOURCE = "skills/temp/gh_ApplicationsOfDerivatives_14B_Ab2.py"


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _load():
    return load_manifest(_MANIFEST)


# ---------------------------------------------------------------------------
# 1. Manifest entry count
# ---------------------------------------------------------------------------

def test_manifest_has_7_entries():
    entries = _load()
    assert len(entries) == 7, f"Expected 7 entries, got {len(entries)}"


# ---------------------------------------------------------------------------
# 2. No radicals
# ---------------------------------------------------------------------------

def test_manifest_no_radicals():
    entries = _load()
    for e in entries:
        combined = e["skill_id"] + e["source_ab2_path"]
        assert "Radicals" not in combined and "radicals" not in combined, (
            f"Radicals found in entry {e['sample_id']!r}"
        )


# ---------------------------------------------------------------------------
# 3. No Ab3
# ---------------------------------------------------------------------------

def test_manifest_no_ab3():
    entries = _load()
    for e in entries:
        assert "Ab3" not in e["source_ab2_path"], (
            f"Ab3 found in path: {e['source_ab2_path']!r}"
        )


# ---------------------------------------------------------------------------
# 4. healer_status is never "healer_on"
# ---------------------------------------------------------------------------

def test_manifest_no_healer_on():
    entries = _load()
    for e in entries:
        assert e["healer_status"] != "healer_on", (
            f"healer_on found in entry {e['sample_id']!r}"
        )


# ---------------------------------------------------------------------------
# 5. All source paths exist on disk
# ---------------------------------------------------------------------------

def test_all_source_paths_exist():
    entries = _load()
    for e in entries:
        abs_path = os.path.join(_ROOT, e["source_ab2_path"].replace("/", os.sep))
        assert os.path.isfile(abs_path), (
            f"Source file missing: {abs_path}"
        )


# ---------------------------------------------------------------------------
# 6. extract_legacy_code fails-closed when marker is absent
# ---------------------------------------------------------------------------

def test_no_marker_fails_closed():
    with tempfile.TemporaryDirectory() as tmpdir:
        no_marker = os.path.join(tmpdir, "no_marker.py")
        with open(no_marker, "w", encoding="utf-8") as fh:
            fh.write("def generate():\n    return {}\n")
        with pytest.raises(ValueError, match="not found"):
            extract_legacy_code("no_marker.py", tmpdir)


# ---------------------------------------------------------------------------
# 7. Extracted code is byte-identical to expected section
# ---------------------------------------------------------------------------

def test_extracted_code_byte_identical():
    abs_source = os.path.join(_ROOT, _KNOWN_SOURCE.replace("/", os.sep))
    with open(abs_source, "r", encoding="utf-8") as fh:
        lines = fh.readlines()

    # Find marker line index
    marker_idx = next(
        (i for i, ln in enumerate(lines) if ln.rstrip("\n\r") == _MARKER),
        None,
    )
    assert marker_idx is not None, "Marker not found in known fixture"

    expected = "".join(lines[marker_idx + 1 :])
    actual = extract_legacy_code(_KNOWN_SOURCE, _ROOT)
    assert actual == expected, "Extracted code is not byte-identical to expected section"


# ---------------------------------------------------------------------------
# 8. migrate_all is deterministic (same hashes on two calls)
# ---------------------------------------------------------------------------

def test_migration_deterministic():
    results_a = migrate_all(_MANIFEST, _ROOT)
    results_b = migrate_all(_MANIFEST, _ROOT)
    for a, b in zip(results_a, results_b):
        assert a["extracted_code_hash"] == b["extracted_code_hash"], (
            f"Non-deterministic hash for {a['metadata']['sample_id']!r}"
        )
        assert a["source_file_hash"] == b["source_file_hash"]


# ---------------------------------------------------------------------------
# 9. source_file_hash matches sha256 of raw file bytes
# ---------------------------------------------------------------------------

def test_source_hash_correct():
    entries = _load()
    for e in entries:
        abs_path = os.path.join(_ROOT, e["source_ab2_path"].replace("/", os.sep))
        expected_hash = hashlib.sha256(open(abs_path, "rb").read()).hexdigest()
        assert e["source_file_hash"] == expected_hash, (
            f"Hash mismatch for {e['sample_id']!r}: "
            f"manifest={e['source_file_hash']!r}, actual={expected_hash!r}"
        )


# ---------------------------------------------------------------------------
# 10. migrate_all output does NOT contain test_suite or test_pass keys
# ---------------------------------------------------------------------------

def test_no_test_suite_created():
    results = migrate_all(_MANIFEST, _ROOT)
    for r in results:
        assert "test_suite" not in r, "test_suite key found in migration result"
        assert "test_pass" not in r, "test_pass key found in migration result"


# ---------------------------------------------------------------------------
# 11. Module source does not reference AI/network libraries
# ---------------------------------------------------------------------------

def test_no_model_or_network():
    import inspect
    import agent_tools.finals_rebuild.legacy_migration as mod

    src = inspect.getsource(mod)
    forbidden = [
        "openai",
        "anthropic",
        "google.generativeai",
        "call_ai_with_retry",
    ]
    for token in forbidden:
        assert token not in src, f"Forbidden reference {token!r} found in legacy_migration.py"


# ---------------------------------------------------------------------------
# 12. Each migrated result has migration_version == MIGRATION_VERSION
# ---------------------------------------------------------------------------

def test_migration_version_present():
    results = migrate_all(_MANIFEST, _ROOT)
    for r in results:
        assert "migration_version" in r, (
            f"migration_version missing for {r['metadata']['sample_id']!r}"
        )
        assert r["migration_version"] == MIGRATION_VERSION, (
            f"Wrong migration_version: {r['migration_version']!r}"
        )
