"""
Tests for agent_tools/finals_rebuild/legacy_migration.py
"""

from __future__ import annotations

import hashlib
import inspect
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import pytest

from agent_tools.finals_rebuild.legacy_migration import (
    MIGRATION_VERSION,
    build_legacy_replay_response,
    check_no_healer_on_header,
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

# The 7 canonical source paths this manifest must use — exact match only.
_EXPECTED_PATHS = [
    "experiments/results/jh_數學1上_FourArithmeticOperationsOfIntegers/"
    "jh_數學1上_FourArithmeticOperationsOfIntegers_gemini-3-flash_Ab2_run01.py",
    "experiments/results/jh_數學1上_FourArithmeticOperationsOfIntegers/"
    "jh_數學1上_FourArithmeticOperationsOfIntegers_qwen3-14b_Ab2_run02.py",
    "experiments/results/jh_數學1上_FourArithmeticOperationsOfNumbers/"
    "jh_數學1上_FourArithmeticOperationsOfNumbers_qwen3-14b_Ab2_run02.py",
    "experiments/results/jh_數學1上_FourArithmeticOperationsOfIntegers/"
    "jh_數學1上_FourArithmeticOperationsOfIntegers_qwen3-8b_Ab2_run04.py",
    "experiments/results/jh_數學1上_FourArithmeticOperationsOfNumbers/"
    "jh_數學1上_FourArithmeticOperationsOfNumbers_gemini-3-flash_Ab2_run01.py",
    "experiments/results/gh_ApplicationsOfDerivatives/"
    "gh_ApplicationsOfDerivatives_qwen2.5-coder-14b_Ab2_run05.py",
    "experiments/results/jh_數學1上_FourArithmeticOperationsOfIntegers/"
    "jh_數學1上_FourArithmeticOperationsOfIntegers_qwen3-14b_Ab2_run01.py",
]

# A known canonical fixture file used for byte-identity checks.
_KNOWN_SOURCE = _EXPECTED_PATHS[0]


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _load():
    return load_manifest(_MANIFEST)


# ---------------------------------------------------------------------------
# 1. Manifest entry count and exact path set
# ---------------------------------------------------------------------------

def test_manifest_has_7_entries():
    entries = _load()
    assert len(entries) == 7, f"Expected 7 entries, got {len(entries)}"


def test_manifest_paths_match_canonical_set_exactly():
    entries = _load()
    actual_paths = {e["source_ab2_path"] for e in entries}
    assert actual_paths == set(_EXPECTED_PATHS)
    # No duplicates either.
    assert len(entries) == len(_EXPECTED_PATHS)


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


def test_load_manifest_rejects_radicals_entry():
    entry = _make_valid_entry_dict()
    entry["skill_id"] = "gh_RadicalsOrchestrator"
    with pytest.raises(ValueError, match="radicals"):
        _load_manifest_from_entries([entry])


# ---------------------------------------------------------------------------
# 3. No Ab3
# ---------------------------------------------------------------------------

def test_manifest_no_ab3():
    entries = _load()
    for e in entries:
        assert "Ab3" not in e["source_ab2_path"], (
            f"Ab3 found in path: {e['source_ab2_path']!r}"
        )


def test_load_manifest_rejects_ab3_path():
    entry = _make_valid_entry_dict()
    entry["source_ab2_path"] = entry["source_ab2_path"].replace("Ab2", "Ab3")
    with pytest.raises(ValueError, match="Ab3"):
        _load_manifest_from_entries([entry])


# ---------------------------------------------------------------------------
# 3b. No skills/temp or backup paths
# ---------------------------------------------------------------------------

def test_manifest_no_temp_or_backup_paths():
    entries = _load()
    for e in entries:
        lower = e["source_ab2_path"].lower()
        assert "skills/temp/" not in lower
        assert "backup" not in lower


def test_load_manifest_rejects_skills_temp_path():
    entry = _make_valid_entry_dict()
    entry["source_ab2_path"] = "skills/temp/gh_ApplicationsOfDerivatives_14B_Ab2.py"
    with pytest.raises(ValueError, match="forbidden segment"):
        _load_manifest_from_entries([entry])


def test_load_manifest_rejects_backup_path():
    entry = _make_valid_entry_dict()
    entry["source_ab2_path"] = "experiments/results_backup/foo_Ab2_run01.py"
    with pytest.raises(ValueError, match="forbidden segment"):
        _load_manifest_from_entries([entry])


# ---------------------------------------------------------------------------
# 4. healer_status is never "healer_on"; header-level Healer ON is fail-closed
# ---------------------------------------------------------------------------

def test_manifest_no_healer_on():
    entries = _load()
    for e in entries:
        assert e["healer_status"] != "healer_on", (
            f"healer_on found in entry {e['sample_id']!r}"
        )


def test_check_no_healer_on_header_passes_for_canonical_sources():
    for path in _EXPECTED_PATHS:
        check_no_healer_on_header(path, _ROOT)  # must not raise


def test_check_no_healer_on_header_fails_closed():
    with tempfile.TemporaryDirectory() as tmpdir:
        bad_file = os.path.join(tmpdir, "healer_on.py")
        with open(bad_file, "w", encoding="utf-8") as fh:
            fh.write(
                "# Ablation ID: 2 | Basic Cleanup: ENABLED | Advanced Healer: ON\n"
                "# [AI GENERATED CODE]\n"
                "def generate():\n    return {}\n"
            )
        with pytest.raises(ValueError, match="Healer is ON"):
            check_no_healer_on_header("healer_on.py", tmpdir)


def test_migrate_entry_rejects_healer_on_source():
    with tempfile.TemporaryDirectory() as tmpdir:
        bad_file = os.path.join(tmpdir, "healer_on.py")
        with open(bad_file, "w", encoding="utf-8") as fh:
            fh.write(
                "# Advanced Healer: FULL\n"
                "# [AI GENERATED CODE]\n"
                "def generate():\n    return {}\n"
            )
        entry = _make_valid_entry_dict()
        entry["source_ab2_path"] = "healer_on.py"
        with pytest.raises(ValueError, match="Healer is ON"):
            migrate_entry(entry, tmpdir)


# ---------------------------------------------------------------------------
# 5. All source paths exist on disk; manifest uses exact paths, no glob
# ---------------------------------------------------------------------------

def test_all_source_paths_exist():
    entries = _load()
    for e in entries:
        abs_path = os.path.join(_ROOT, e["source_ab2_path"].replace("/", os.sep))
        assert os.path.isfile(abs_path), (
            f"Source file missing: {abs_path}"
        )


def test_no_directory_scanning_in_module_source():
    """Structural check: the migration module must reference exact paths
    only — no glob/os.walk/os.scandir/os.listdir directory discovery."""
    import agent_tools.finals_rebuild.legacy_migration as mod

    src = inspect.getsource(mod)
    for forbidden in ("glob.glob", "os.walk", "os.scandir", "os.listdir", "Path.glob", ".rglob("):
        assert forbidden not in src, f"Forbidden directory-scanning call {forbidden!r} found"


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
# 6b. syntax-invalid legacy code is NOT rejected by migration (fail-closed
# decision is deferred to the evaluator)
# ---------------------------------------------------------------------------

def test_syntax_invalid_legacy_code_is_not_rejected():
    with tempfile.TemporaryDirectory() as tmpdir:
        broken = os.path.join(tmpdir, "broken.py")
        with open(broken, "w", encoding="utf-8") as fh:
            fh.write(
                "# Advanced Healer: OFF\n"
                "# [AI GENERATED CODE]\n"
                "def generate(:\n    this is not valid python\n"
            )
        entry = _make_valid_entry_dict()
        entry["source_ab2_path"] = "broken.py"
        entry["source_file_hash"] = compute_source_hash(broken)
        result = migrate_entry(entry, tmpdir)  # must not raise
        assert "def generate(:" in result["extracted_code"]
        assert "this is not valid python" in result["extracted_code"]


# ---------------------------------------------------------------------------
# 7. Extracted code is byte-identical to expected section
# ---------------------------------------------------------------------------

def test_extracted_code_byte_identical():
    abs_source = os.path.join(_ROOT, _KNOWN_SOURCE.replace("/", os.sep))
    with open(abs_source, "r", encoding="utf-8") as fh:
        lines = fh.readlines()

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
# 9. source_file_hash matches sha256 of raw file bytes; recomputed hashes
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


def test_migrate_all_recomputes_extracted_code_hash():
    results = migrate_all(_MANIFEST, _ROOT)
    for r in results:
        expected = hashlib.sha256(r["extracted_code"].encode("utf-8")).hexdigest()
        assert r["extracted_code_hash"] == expected


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


# ---------------------------------------------------------------------------
# Fixtures for negative-path tests
# ---------------------------------------------------------------------------

def _make_valid_entry_dict():
    """A structurally-valid manifest entry (copy of manifest[0]) for
    mutating in negative-path tests."""
    entries = _load()
    return dict(entries[0])


def _load_manifest_from_entries(entries):
    with tempfile.TemporaryDirectory() as tmpdir:
        manifest_path = os.path.join(tmpdir, "manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as fh:
            json.dump(entries, fh)
        return load_manifest(manifest_path)
