"""
Immutable paired artifact schema for the finals-rebuild ablation pipeline.

Treatments
----------
ab1        : Bare Prompt  (independent raw)
ab2        : Scaffold Prompt  (shared raw with ab3_core / ab3_full)
ab3_core   : Scaffold + Core Healer  (shared raw with ab2 / ab3_full)
ab3_full   : Scaffold + Core Healer + Math Adapter  (shared raw with ab2 / ab3_core)

Identity rules
--------------
pair_id  = SHA-256( study_id | model_id | skill_id | sample_index
                    | scaffold_prompt_hash | generation_config_hash )
raw_id   = SHA-256( pair_id | raw_response_hash )
run_id   = SHA-256( pair_id | treatment | output_artifact_hash )

timestamp_utc is EXCLUDED from all three IDs.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import pathlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Literal, Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ALLOWED_TREATMENTS: frozenset[str] = frozenset(
    {"ab1", "ab2", "ab3_core", "ab3_full"}
)

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ISO8601_UTC_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(\+00:00|Z)$"
)

SHARED_TREATMENTS: frozenset[str] = frozenset({"ab2", "ab3_core", "ab3_full"})

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ArtifactIdentity:
    """Core IDs that never change for a given experimental unit."""

    study_id: str
    pair_id: str
    raw_id: str
    run_id: str
    treatment: str


@dataclass(frozen=True)
class ArtifactMetadata:
    """Full metadata record attached to every run artifact."""

    study_id: str
    pair_id: str
    raw_id: str
    run_id: str
    model_id: str
    skill_id: str
    sample_index: int
    seed: int
    prompt_hash: str
    generation_config_hash: str
    source_git_commit: str
    timestamp_utc: str
    treatment: str
    raw_ab1_hash: str
    raw_ab2_hash: str
    extracted_ab1_hash: str
    extracted_ab2_hash: str
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ArtifactPaths:
    """Canonical path layout under a given artifact root."""

    root: pathlib.Path
    study_id: str
    pair_id: str

    # Directories
    @property
    def pair_dir(self) -> pathlib.Path:
        return self.root / self.study_id / self.pair_id

    @property
    def prompts_dir(self) -> pathlib.Path:
        return self.pair_dir / "prompts"

    @property
    def raw_dir(self) -> pathlib.Path:
        return self.pair_dir / "raw"

    @property
    def extracted_dir(self) -> pathlib.Path:
        return self.pair_dir / "extracted"

    @property
    def treatments_dir(self) -> pathlib.Path:
        return self.pair_dir / "treatments"

    @property
    def traces_dir(self) -> pathlib.Path:
        return self.pair_dir / "traces"

    @property
    def evaluations_dir(self) -> pathlib.Path:
        return self.pair_dir / "evaluations"

    # Files
    @property
    def metadata_json(self) -> pathlib.Path:
        return self.pair_dir / "metadata.json"

    @property
    def prompt_ab1(self) -> pathlib.Path:
        return self.prompts_dir / "ab1.txt"

    @property
    def prompt_ab2(self) -> pathlib.Path:
        return self.prompts_dir / "ab2.txt"

    @property
    def raw_ab1(self) -> pathlib.Path:
        return self.raw_dir / "ab1_response.txt"

    @property
    def raw_ab2(self) -> pathlib.Path:
        return self.raw_dir / "ab2_response.txt"

    @property
    def extracted_ab1(self) -> pathlib.Path:
        return self.extracted_dir / "ab1.py"

    @property
    def extracted_ab2(self) -> pathlib.Path:
        return self.extracted_dir / "ab2.py"

    def treatment_file(self, treatment: str) -> pathlib.Path:
        _validate_treatment(treatment)
        return self.treatments_dir / f"{treatment}.py"

    @property
    def healer_trace(self) -> pathlib.Path:
        return self.traces_dir / "healer_trace.json"

    @property
    def evaluation_json(self) -> pathlib.Path:
        return self.evaluations_dir / "evaluation.json"


# ---------------------------------------------------------------------------
# SHA-256 helpers
# ---------------------------------------------------------------------------


def sha256_text(text: str, encoding: str = "utf-8") -> str:
    """Return lowercase hex SHA-256 of *text*."""
    return hashlib.sha256(text.encode(encoding)).hexdigest()


def sha256_bytes(data: bytes) -> str:
    """Return lowercase hex SHA-256 of *data*."""
    return hashlib.sha256(data).hexdigest()


def sha256_json(obj: Any) -> str:
    """Return lowercase hex SHA-256 of *obj* serialised with sorted keys
    and no extraneous whitespace (stable across Python versions)."""
    canonical = json.dumps(obj, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=True)
    return sha256_text(canonical)


def _join_fields(*parts: str) -> str:
    """Concatenate fields with NUL separator to prevent length-extension."""
    return "\x00".join(parts)


# ---------------------------------------------------------------------------
# Deterministic ID builders
# ---------------------------------------------------------------------------


def build_pair_id(
    study_id: str,
    model_id: str,
    skill_id: str,
    sample_index: int,
    scaffold_prompt_hash: str,
    generation_config_hash: str,
) -> str:
    """Deterministic pair_id; timestamp is intentionally excluded."""
    _require_nonempty(study_id, "study_id")
    _require_nonempty(model_id, "model_id")
    _require_nonempty(skill_id, "skill_id")
    _require_nonneg_int(sample_index, "sample_index")
    _require_sha256(scaffold_prompt_hash, "scaffold_prompt_hash")
    _require_sha256(generation_config_hash, "generation_config_hash")

    payload = _join_fields(
        study_id,
        model_id,
        skill_id,
        str(sample_index),
        scaffold_prompt_hash,
        generation_config_hash,
    )
    return sha256_text(payload)


def build_raw_id(pair_id: str, raw_response_hash: str) -> str:
    """Deterministic raw_id; timestamp is intentionally excluded."""
    _require_sha256(pair_id, "pair_id")
    _require_sha256(raw_response_hash, "raw_response_hash")

    payload = _join_fields(pair_id, raw_response_hash)
    return sha256_text(payload)


def build_run_id(
    pair_id: str,
    treatment: str,
    output_artifact_hash: str,
) -> str:
    """Deterministic run_id; timestamp is intentionally excluded."""
    _require_sha256(pair_id, "pair_id")
    _validate_treatment(treatment)
    _require_sha256(output_artifact_hash, "output_artifact_hash")

    payload = _join_fields(pair_id, treatment, output_artifact_hash)
    return sha256_text(payload)


# ---------------------------------------------------------------------------
# Validation helpers (private)
# ---------------------------------------------------------------------------


def _require_nonempty(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string, got {value!r}")


def _require_nonneg_int(value: int, name: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(
            f"{name} must be a non-negative integer, got {value!r}"
        )


def _require_sha256(value: str, name: str) -> None:
    if not isinstance(value, str) or not _SHA256_RE.match(value):
        raise ValueError(
            f"{name} must be a 64-char lowercase hex SHA-256, got {value!r}"
        )


def _validate_treatment(treatment: str) -> None:
    if treatment not in ALLOWED_TREATMENTS:
        raise ValueError(
            f"treatment must be one of {sorted(ALLOWED_TREATMENTS)}, "
            f"got {treatment!r}"
        )


def _validate_path_component(component: str, label: str) -> None:
    """Reject empty string, '..' , '/' , and '\\'."""
    if not component:
        raise ValueError(f"{label}: path component must not be empty")
    for forbidden in ("..", "/", "\\"):
        if forbidden in component:
            raise ValueError(
                f"{label}: path component {component!r} contains "
                f"forbidden sequence {forbidden!r}"
            )


# ---------------------------------------------------------------------------
# Public metadata validator
# ---------------------------------------------------------------------------

_REQUIRED_FIELDS = (
    "study_id", "pair_id", "raw_id", "run_id", "model_id", "skill_id",
    "sample_index", "seed", "prompt_hash", "generation_config_hash",
    "source_git_commit", "timestamp_utc", "treatment",
    "raw_ab1_hash", "raw_ab2_hash", "extracted_ab1_hash", "extracted_ab2_hash",
)

_SHA256_FIELDS = (
    "pair_id", "raw_id", "run_id",
    "prompt_hash", "generation_config_hash",
    "raw_ab1_hash", "raw_ab2_hash",
    "extracted_ab1_hash", "extracted_ab2_hash",
)


def validate_metadata(meta: Dict[str, Any]) -> None:
    """
    Raise *ValueError* if *meta* violates schema rules.

    Unknown extra fields are tolerated but do NOT participate in ID
    recalculation.
    """
    # 1. Required fields present
    for f in _REQUIRED_FIELDS:
        if f not in meta:
            raise ValueError(f"Missing required field: {f!r}")

    # 2. Non-empty strings
    for f in ("study_id", "model_id", "skill_id"):
        _require_nonempty(meta[f], f)

    # 3. sample_index non-negative int
    _require_nonneg_int(meta["sample_index"], "sample_index")

    # 4. SHA-256 fields
    for f in _SHA256_FIELDS:
        _require_sha256(meta[f], f)

    # 5. timestamp UTC ISO-8601
    ts = meta["timestamp_utc"]
    if not isinstance(ts, str) or not _ISO8601_UTC_RE.match(ts):
        raise ValueError(
            f"timestamp_utc must be UTC ISO-8601, got {ts!r}"
        )

    # 6. treatment in allowed list
    _validate_treatment(meta["treatment"])

    # 7. Re-derive IDs and compare
    #    (requires scaffold_prompt_hash == prompt_hash for ab2/ab3 treatments,
    #     but the spec stores it under prompt_hash generically)
    expected_pair_id = build_pair_id(
        study_id=meta["study_id"],
        model_id=meta["model_id"],
        skill_id=meta["skill_id"],
        sample_index=meta["sample_index"],
        scaffold_prompt_hash=meta["prompt_hash"],
        generation_config_hash=meta["generation_config_hash"],
    )
    if meta["pair_id"] != expected_pair_id:
        raise ValueError(
            f"pair_id mismatch: stored={meta['pair_id']!r}, "
            f"recalculated={expected_pair_id!r}"
        )

    raw_hash = (
        meta["raw_ab1_hash"]
        if meta["treatment"] == "ab1"
        else meta["raw_ab2_hash"]
    )
    expected_raw_id = build_raw_id(meta["pair_id"], raw_hash)
    if meta["raw_id"] != expected_raw_id:
        raise ValueError(
            f"raw_id mismatch: stored={meta['raw_id']!r}, "
            f"recalculated={expected_raw_id!r}"
        )

    output_hash = (
        meta["extracted_ab1_hash"]
        if meta["treatment"] == "ab1"
        else meta["extracted_ab2_hash"]
    )
    expected_run_id = build_run_id(
        meta["pair_id"], meta["treatment"], output_hash
    )
    if meta["run_id"] != expected_run_id:
        raise ValueError(
            f"run_id mismatch: stored={meta['run_id']!r}, "
            f"recalculated={expected_run_id!r}"
        )


# ---------------------------------------------------------------------------
# Shared paired-identity validator
# ---------------------------------------------------------------------------


def validate_shared_identity(
    ab2_meta: Dict[str, Any],
    ab3_core_meta: Dict[str, Any],
    ab3_full_meta: Dict[str, Any],
) -> None:
    """
    Assert that ab2 / ab3_core / ab3_full share:
      - pair_id
      - raw_id
      - raw_ab2_hash
      - extracted_ab2_hash

    Raises *ValueError* on any inconsistency.
    """
    metas = {
        "ab2": ab2_meta,
        "ab3_core": ab3_core_meta,
        "ab3_full": ab3_full_meta,
    }

    for shared_field in ("pair_id", "raw_id", "raw_ab2_hash",
                         "extracted_ab2_hash"):
        values = {name: m[shared_field] for name, m in metas.items()}
        unique = set(values.values())
        if len(unique) != 1:
            raise ValueError(
                f"Shared identity mismatch on {shared_field!r}: {values}"
            )

    for name, meta in metas.items():
        if meta.get("treatment") != name:
            raise ValueError(
                f"Expected treatment={name!r}, got {meta.get('treatment')!r}"
            )


# ---------------------------------------------------------------------------
# Immutable write helpers
# ---------------------------------------------------------------------------


class ImmutableWriteError(Exception):
    """Raised when attempting to overwrite an existing artifact with
    different content."""


_UNCHANGED = "unchanged"


def immutable_write_bytes(
    path: pathlib.Path,
    data: bytes,
    artifact_root: pathlib.Path,
) -> Literal["written", "unchanged"]:
    """
    Write *data* to *path* immutably.

    Returns
    -------
    "written"   – file did not exist; it has been created.
    "unchanged" – file existed with identical content; nothing done.

    Raises
    ------
    ImmutableWriteError  – file existed with *different* content.
    ValueError           – *path* escapes *artifact_root* (path traversal).
    """
    _check_no_traversal(path, artifact_root)

    if path.exists():
        existing = path.read_bytes()
        if existing == data:
            return _UNCHANGED
        raise ImmutableWriteError(
            f"Cannot overwrite existing artifact with different content: "
            f"{path}"
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return "written"


def immutable_write_text(
    path: pathlib.Path,
    text: str,
    artifact_root: pathlib.Path,
    encoding: str = "utf-8",
) -> Literal["written", "unchanged"]:
    """Text wrapper for :func:`immutable_write_bytes`."""
    return immutable_write_bytes(path, text.encode(encoding), artifact_root)


def immutable_write_json(
    path: pathlib.Path,
    obj: Any,
    artifact_root: pathlib.Path,
) -> Literal["written", "unchanged"]:
    """Stable-serialise *obj* and write immutably."""
    serialised = json.dumps(obj, sort_keys=True, indent=2,
                            ensure_ascii=True) + "\n"
    return immutable_write_text(path, serialised, artifact_root)


def _check_no_traversal(
    path: pathlib.Path, artifact_root: pathlib.Path
) -> None:
    """Raise *ValueError* if *path* is outside *artifact_root*."""
    try:
        resolved_path = path.resolve()
        resolved_root = artifact_root.resolve()
        resolved_path.relative_to(resolved_root)
    except ValueError:
        raise ValueError(
            f"Path traversal detected: {path!r} is outside "
            f"artifact root {artifact_root!r}"
        )


# ---------------------------------------------------------------------------
# JSON round-trip helper
# ---------------------------------------------------------------------------


def metadata_to_dict(meta: ArtifactMetadata) -> Dict[str, Any]:
    """Serialise *meta* to a plain dict (JSON-safe)."""
    d: Dict[str, Any] = {
        "study_id": meta.study_id,
        "pair_id": meta.pair_id,
        "raw_id": meta.raw_id,
        "run_id": meta.run_id,
        "model_id": meta.model_id,
        "skill_id": meta.skill_id,
        "sample_index": meta.sample_index,
        "seed": meta.seed,
        "prompt_hash": meta.prompt_hash,
        "generation_config_hash": meta.generation_config_hash,
        "source_git_commit": meta.source_git_commit,
        "timestamp_utc": meta.timestamp_utc,
        "treatment": meta.treatment,
        "raw_ab1_hash": meta.raw_ab1_hash,
        "raw_ab2_hash": meta.raw_ab2_hash,
        "extracted_ab1_hash": meta.extracted_ab1_hash,
        "extracted_ab2_hash": meta.extracted_ab2_hash,
    }
    d.update(meta.extra)
    return d


def metadata_from_dict(d: Dict[str, Any]) -> ArtifactMetadata:
    """Deserialise a plain dict to *ArtifactMetadata*."""
    known = set(_REQUIRED_FIELDS)
    extra = {k: v for k, v in d.items() if k not in known}
    return ArtifactMetadata(
        study_id=d["study_id"],
        pair_id=d["pair_id"],
        raw_id=d["raw_id"],
        run_id=d["run_id"],
        model_id=d["model_id"],
        skill_id=d["skill_id"],
        sample_index=d["sample_index"],
        seed=d["seed"],
        prompt_hash=d["prompt_hash"],
        generation_config_hash=d["generation_config_hash"],
        source_git_commit=d["source_git_commit"],
        timestamp_utc=d["timestamp_utc"],
        treatment=d["treatment"],
        raw_ab1_hash=d["raw_ab1_hash"],
        raw_ab2_hash=d["raw_ab2_hash"],
        extracted_ab1_hash=d["extracted_ab1_hash"],
        extracted_ab2_hash=d["extracted_ab2_hash"],
        extra=extra,
    )


def metadata_json_round_trip(meta: ArtifactMetadata) -> ArtifactMetadata:
    """Serialise to JSON string and deserialise; used for round-trip tests."""
    raw_json = json.dumps(
        metadata_to_dict(meta), sort_keys=True, separators=(",", ":"),
        ensure_ascii=True
    )
    restored_dict = json.loads(raw_json)
    return metadata_from_dict(restored_dict)


# ---------------------------------------------------------------------------
# Utility: current UTC timestamp
# ---------------------------------------------------------------------------


def utc_now_iso8601() -> str:
    """Return current UTC time as ISO-8601 string (always +00:00 suffix)."""
    return (
        datetime.now(tz=timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "+00:00")
    )
