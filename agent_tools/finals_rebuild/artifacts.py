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
pair_id = SHA-256(
    study_id | model_id | model_revision | skill_id | sample_index
    | seed | bare_prompt_hash | scaffold_prompt_hash | generation_config_hash
)

raw_id = SHA-256( pair_id | raw_role | raw_response_hash )
    raw_role in {"ab1_raw", "scaffold_raw"}

run_id = SHA-256( pair_id | treatment | output_artifact_hash )

created_at_utc and source_git_commit are EXCLUDED from all three IDs.

Metadata layers
---------------
PairMetadata  – one record per experimental sample; no treatment, no run_id.
RunMetadata   – one record per treatment execution; validated independently.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Literal, Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ALLOWED_TREATMENTS: frozenset[str] = frozenset(
    {"ab1", "ab2", "ab3_core", "ab3_full"}
)

ALLOWED_RAW_ROLES: frozenset[str] = frozenset({"ab1_raw", "scaffold_raw"})

SHARED_TREATMENTS: frozenset[str] = frozenset({"ab2", "ab3_core", "ab3_full"})

# RunMetadata.extra["implementation_status"] allowlist. "pass_through" is the
# Ab1/Ab2 (and pre-Commit-3A Ab3) value; the other three are emitted by the
# Core/Spec adapters (see agent_tools/finals_rebuild/trace.py).
ALLOWED_IMPLEMENTATION_STATUSES: frozenset[str] = frozenset({
    "pass_through",
    "implemented",
    "implemented_no_safe_rule_triggered",
    "not_applicable",
})

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

# Accepts Z and +00:00; rejects naive datetimes and non-UTC offsets.
_ISO8601_UTC_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|\+00:00)$"
)

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PairMetadata:
    """
    Pair-level metadata for one experimental sample.

    Covers one (study, model, skill, sample_index) unit.

    - Does NOT include treatment, run_id, or per-treatment output hashes.
    - Supports incremental population: nullable fields may be None until the
      corresponding artifacts are produced.
    - Use validate_pair_metadata(stage="draft") during construction and
      validate_pair_metadata(stage="complete") once all artifacts exist.
    """

    study_id: str
    pair_id: str
    model_id: str
    model_revision: str
    skill_id: str
    sample_index: int
    seed: Optional[int]
    bare_prompt_hash: str
    scaffold_prompt_hash: str
    generation_config_hash: str
    source_git_commit: str
    created_at_utc: str
    # Nullable until artifacts are produced
    raw_ab1_id: Optional[str] = None
    raw_ab2_id: Optional[str] = None
    raw_ab1_hash: Optional[str] = None
    raw_ab2_hash: Optional[str] = None
    extracted_ab1_hash: Optional[str] = None
    extracted_ab2_hash: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RunMetadata:
    """
    Run-level metadata for one treatment execution.

    Each treatment (ab1, ab2, ab3_core, ab3_full) has its own RunMetadata.
    run_id is deterministic: SHA-256(pair_id | treatment | output_artifact_hash).

    trace_hash and evaluation_hash are nullable until those artifacts exist.
    Validation is independent of other treatments.
    """

    study_id: str
    pair_id: str
    treatment: str
    run_id: str
    input_artifact_hash: str
    output_artifact_hash: str
    source_git_commit: str
    created_at_utc: str
    trace_hash: Optional[str] = None
    evaluation_hash: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ArtifactPaths:
    """
    Canonical path layout under a given artifact root.

    Directory structure::

        artifacts/<study_id>/<pair_id>/
          pair_metadata.json
          prompts/
            ab1.txt
            ab2.txt
          raw/
            ab1_response.txt
            ab2_response.txt
          extracted/
            ab1.py
            ab2.py
          treatments/
            ab1.py  ab2.py  ab3_core.py  ab3_full.py
          traces/
            healer_trace.json
          evaluations/
            evaluation.json
          runs/
            ab1/metadata.json
            ab2/metadata.json
            ab3_core/metadata.json
            ab3_full/metadata.json

    study_id and pair_id are validated at construction time to prevent
    path traversal.
    """

    root: pathlib.Path
    study_id: str
    pair_id: str

    def __post_init__(self) -> None:
        _validate_path_component(self.study_id, "study_id")
        _validate_path_component(self.pair_id, "pair_id")
        resolved_root = pathlib.Path(self.root).resolve()
        candidate = (resolved_root / self.study_id / self.pair_id).resolve()
        try:
            candidate.relative_to(resolved_root)
        except ValueError:
            raise ValueError(
                f"Constructed pair_dir {candidate!r} escapes artifact root "
                f"{resolved_root!r}"
            )

    # -- Directories --

    @property
    def pair_dir(self) -> pathlib.Path:
        return pathlib.Path(self.root) / self.study_id / self.pair_id

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

    @property
    def runs_dir(self) -> pathlib.Path:
        return self.pair_dir / "runs"

    # -- Pair-level files --

    @property
    def pair_metadata_json(self) -> pathlib.Path:
        return self.pair_dir / "pair_metadata.json"

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

    # -- Run-level paths --

    def run_dir(self, treatment: str) -> pathlib.Path:
        _validate_treatment(treatment)
        return self.runs_dir / treatment

    def run_metadata_json(self, treatment: str) -> pathlib.Path:
        return self.run_dir(treatment) / "metadata.json"

    def trace_json(self, treatment: str) -> pathlib.Path:
        _validate_treatment(treatment)
        return self.run_dir(treatment) / "trace.json"


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
    and minimal separators (stable regardless of dict insertion order)."""
    canonical = json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    )
    return sha256_text(canonical)


def _join_fields(*parts: str) -> str:
    """Concatenate fields with NUL separators to prevent field-boundary
    ambiguity (e.g. "ab"+"c" would otherwise be indistinguishable from
    "a"+"bc")."""
    return "\x00".join(parts)


# ---------------------------------------------------------------------------
# Deterministic ID builders
# ---------------------------------------------------------------------------


def build_pair_id(
    study_id: str,
    model_id: str,
    model_revision: str,
    skill_id: str,
    sample_index: int,
    seed: Optional[int],
    bare_prompt_hash: str,
    scaffold_prompt_hash: str,
    generation_config_hash: str,
) -> str:
    """
    Deterministic pair_id.

    Inputs  : study_id, model_id, model_revision, skill_id, sample_index,
              seed, bare_prompt_hash, scaffold_prompt_hash,
              generation_config_hash.
    Excluded: created_at_utc, source_git_commit.

    seed=None is represented as the canonical string "null".
    """
    _require_nonempty(study_id, "study_id")
    _require_nonempty(model_id, "model_id")
    _require_nonempty(model_revision, "model_revision")
    _require_nonempty(skill_id, "skill_id")
    _require_nonneg_int(sample_index, "sample_index")
    _require_optional_seed(seed, "seed")
    _require_sha256(bare_prompt_hash, "bare_prompt_hash")
    _require_sha256(scaffold_prompt_hash, "scaffold_prompt_hash")
    _require_sha256(generation_config_hash, "generation_config_hash")

    seed_str = "null" if seed is None else str(seed)
    payload = _join_fields(
        study_id,
        model_id,
        model_revision,
        skill_id,
        str(sample_index),
        seed_str,
        bare_prompt_hash,
        scaffold_prompt_hash,
        generation_config_hash,
    )
    return sha256_text(payload)


def build_raw_id(
    pair_id: str,
    raw_role: str,
    raw_response_hash: str,
) -> str:
    """
    Deterministic raw_id.

    raw_role must be "ab1_raw" (bare prompt response) or "scaffold_raw"
    (scaffold prompt response).  The explicit role ensures Ab1 and Scaffold
    raw IDs are distinguishable even if their content happens to be identical.
    """
    _require_sha256(pair_id, "pair_id")
    if raw_role not in ALLOWED_RAW_ROLES:
        raise ValueError(
            f"raw_role must be one of {sorted(ALLOWED_RAW_ROLES)}, "
            f"got {raw_role!r}"
        )
    _require_sha256(raw_response_hash, "raw_response_hash")

    payload = _join_fields(pair_id, raw_role, raw_response_hash)
    return sha256_text(payload)


def build_run_id(
    pair_id: str,
    treatment: str,
    output_artifact_hash: str,
) -> str:
    """
    Deterministic run_id reflecting the treatment's actual output.

    Excluded: created_at_utc, source_git_commit.
    """
    _require_sha256(pair_id, "pair_id")
    _validate_treatment(treatment)
    _require_sha256(output_artifact_hash, "output_artifact_hash")

    payload = _join_fields(pair_id, treatment, output_artifact_hash)
    return sha256_text(payload)


# ---------------------------------------------------------------------------
# Private validation helpers
# ---------------------------------------------------------------------------


def _require_nonempty(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string, got {value!r}")


def _require_nonneg_int(value: int, name: str) -> None:
    """Non-negative integer; bool subclass is always rejected."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(
            f"{name} must be a non-negative integer, got {value!r}"
        )


def _require_optional_seed(value: Optional[int], name: str) -> None:
    """seed may be None or a non-negative integer; bool is always rejected."""
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(
            f"{name} must be None or a non-negative integer, got {value!r}"
        )


def _require_sha256(value: str, name: str) -> None:
    if not isinstance(value, str) or not _SHA256_RE.match(value):
        raise ValueError(
            f"{name} must be a 64-char lowercase hex SHA-256, got {value!r}"
        )


def _require_optional_sha256(value: Optional[str], name: str) -> None:
    if value is not None:
        _require_sha256(value, name)


def _validate_treatment(treatment: str) -> None:
    if treatment not in ALLOWED_TREATMENTS:
        raise ValueError(
            f"treatment must be one of {sorted(ALLOWED_TREATMENTS)}, "
            f"got {treatment!r}"
        )


def _validate_utc_timestamp(ts: str, name: str) -> None:
    """Require UTC ISO-8601 with Z or +00:00.  Naive datetimes are rejected.
    Non-UTC offsets (e.g. +08:00) are rejected."""
    if not isinstance(ts, str) or not _ISO8601_UTC_RE.match(ts):
        raise ValueError(
            f"{name} must be UTC ISO-8601 with Z or +00:00 offset, "
            f"got {ts!r}"
        )


def _validate_path_component(component: str, label: str) -> None:
    """Reject '', '.', '..', and any component containing '/' or '\\'."""
    if not isinstance(component, str) or not component:
        raise ValueError(f"{label}: path component must not be empty")
    if component in {".", ".."}:
        raise ValueError(
            f"{label}: path component {component!r} is forbidden"
        )
    for char in ("/", "\\"):
        if char in component:
            raise ValueError(
                f"{label}: path component {component!r} contains "
                f"forbidden character {char!r}"
            )


# ---------------------------------------------------------------------------
# PairMetadata validation
# ---------------------------------------------------------------------------

_PAIR_NULLABLE_FIELDS = (
    "raw_ab1_id", "raw_ab2_id",
    "raw_ab1_hash", "raw_ab2_hash",
    "extracted_ab1_hash", "extracted_ab2_hash",
)


def validate_pair_metadata(
    meta: PairMetadata,
    stage: Literal["draft", "complete"] = "draft",
) -> None:
    """
    Validate *meta*.

    stage="draft"
        Nullable raw / extracted fields may be None.
        Identity fields and non-nullable fields must be valid.

    stage="complete"
        All hash fields must be present and internally consistent
        (raw IDs verified against raw hashes).
    """
    if stage not in ("draft", "complete"):
        raise ValueError(
            f"stage must be 'draft' or 'complete', got {stage!r}"
        )

    _require_nonempty(meta.study_id, "study_id")
    _require_nonempty(meta.model_id, "model_id")
    _require_nonempty(meta.model_revision, "model_revision")
    _require_nonempty(meta.skill_id, "skill_id")
    _require_nonneg_int(meta.sample_index, "sample_index")
    _require_optional_seed(meta.seed, "seed")
    _require_sha256(meta.bare_prompt_hash, "bare_prompt_hash")
    _require_sha256(meta.scaffold_prompt_hash, "scaffold_prompt_hash")
    _require_sha256(meta.generation_config_hash, "generation_config_hash")
    _require_sha256(meta.pair_id, "pair_id")
    _require_nonempty(meta.source_git_commit, "source_git_commit")
    _validate_utc_timestamp(meta.created_at_utc, "created_at_utc")

    # Verify pair_id is consistent with identity fields
    expected_pair_id = build_pair_id(
        study_id=meta.study_id,
        model_id=meta.model_id,
        model_revision=meta.model_revision,
        skill_id=meta.skill_id,
        sample_index=meta.sample_index,
        seed=meta.seed,
        bare_prompt_hash=meta.bare_prompt_hash,
        scaffold_prompt_hash=meta.scaffold_prompt_hash,
        generation_config_hash=meta.generation_config_hash,
    )
    if meta.pair_id != expected_pair_id:
        raise ValueError(
            f"pair_id mismatch: stored={meta.pair_id!r}, "
            f"recalculated={expected_pair_id!r}"
        )

    # Validate format of nullable fields when present
    for fname in _PAIR_NULLABLE_FIELDS:
        _require_optional_sha256(getattr(meta, fname), fname)

    if stage == "complete":
        for fname in _PAIR_NULLABLE_FIELDS:
            if getattr(meta, fname) is None:
                raise ValueError(
                    f"stage='complete' requires {fname!r} to be present"
                )
        # Verify raw IDs against hashes
        expected_raw_ab1_id = build_raw_id(
            meta.pair_id, "ab1_raw", meta.raw_ab1_hash
        )
        if meta.raw_ab1_id != expected_raw_ab1_id:
            raise ValueError(
                f"raw_ab1_id mismatch: stored={meta.raw_ab1_id!r}, "
                f"recalculated={expected_raw_ab1_id!r}"
            )
        expected_raw_ab2_id = build_raw_id(
            meta.pair_id, "scaffold_raw", meta.raw_ab2_hash
        )
        if meta.raw_ab2_id != expected_raw_ab2_id:
            raise ValueError(
                f"raw_ab2_id mismatch: stored={meta.raw_ab2_id!r}, "
                f"recalculated={expected_raw_ab2_id!r}"
            )


# ---------------------------------------------------------------------------
# RunMetadata validation
# ---------------------------------------------------------------------------


def validate_run_metadata(meta: RunMetadata) -> None:
    """
    Validate *meta*.  Independent of other treatments.

    Verifies run_id is consistent with pair_id + treatment +
    output_artifact_hash.

    Raises ValueError if meta.extra contains any key that is an official
    RunMetadata field name (would shadow the authoritative value).
    """
    _require_nonempty(meta.study_id, "study_id")
    _require_sha256(meta.pair_id, "pair_id")
    _validate_treatment(meta.treatment)
    _require_sha256(meta.run_id, "run_id")
    _require_sha256(meta.input_artifact_hash, "input_artifact_hash")
    _require_sha256(meta.output_artifact_hash, "output_artifact_hash")
    _require_nonempty(meta.source_git_commit, "source_git_commit")
    _validate_utc_timestamp(meta.created_at_utc, "created_at_utc")
    _require_optional_sha256(meta.trace_hash, "trace_hash")
    _require_optional_sha256(meta.evaluation_hash, "evaluation_hash")

    extra_conflicts = set(meta.extra) & _RUN_KNOWN_FIELDS
    if extra_conflicts:
        raise ValueError(
            f"RunMetadata.extra must not contain official field names; "
            f"conflicts: {sorted(extra_conflicts)}"
        )

    # extra["implementation_status"] / extra["treatment_applied"] /
    # extra["changed"] are not yet official RunMetadata fields, but they are
    # not free-form either: unknown implementation_status values are
    # rejected so a typo or an unreviewed new status can never slip through.
    if "implementation_status" in meta.extra:
        status = meta.extra["implementation_status"]
        if status not in ALLOWED_IMPLEMENTATION_STATUSES:
            raise ValueError(
                f"RunMetadata.extra['implementation_status'] must be one of "
                f"{sorted(ALLOWED_IMPLEMENTATION_STATUSES)}, got {status!r}"
            )
    if "treatment_applied" in meta.extra and not isinstance(
        meta.extra["treatment_applied"], bool
    ):
        raise ValueError(
            "RunMetadata.extra['treatment_applied'] must be a bool"
        )
    if "changed" in meta.extra and not isinstance(meta.extra["changed"], bool):
        raise ValueError("RunMetadata.extra['changed'] must be a bool")

    expected_run_id = build_run_id(
        meta.pair_id, meta.treatment, meta.output_artifact_hash
    )
    if meta.run_id != expected_run_id:
        raise ValueError(
            f"run_id mismatch: stored={meta.run_id!r}, "
            f"recalculated={expected_run_id!r}"
        )


# ---------------------------------------------------------------------------
# Shared run identity validator
# ---------------------------------------------------------------------------


def validate_shared_run_identity(
    ab2_run: RunMetadata,
    ab3_core_run: RunMetadata,
    ab3_full_run: RunMetadata,
) -> None:
    """
    Assert that ab2 / ab3_core / ab3_full runs share:

    - pair_id
    - input_artifact_hash  (all three use extracted_ab2 as their input)

    Their run_ids will legitimately differ because output_artifact_hash
    differs across treatments.

    Raises ValueError on any inconsistency.
    """
    runs = {
        "ab2": ab2_run,
        "ab3_core": ab3_core_run,
        "ab3_full": ab3_full_run,
    }

    for name, run in runs.items():
        if run.treatment != name:
            raise ValueError(
                f"Expected treatment={name!r}, got {run.treatment!r}"
            )

    for shared_field in ("pair_id", "input_artifact_hash"):
        values = {
            name: getattr(run, shared_field) for name, run in runs.items()
        }
        if len(set(values.values())) != 1:
            raise ValueError(
                f"Shared run identity mismatch on {shared_field!r}: {values}"
            )


# ---------------------------------------------------------------------------
# Immutable write helpers
# ---------------------------------------------------------------------------


class ImmutableWriteError(Exception):
    """Raised when attempting to overwrite an existing artifact with
    different content."""


def immutable_write_bytes(
    path: pathlib.Path,
    data: bytes,
    artifact_root: pathlib.Path,
) -> Literal["written", "unchanged"]:
    """
    Write *data* to *path* immutably using exclusive file creation.

    Uses ``open(..., 'xb')`` to atomically create the file.  If the file
    already exists (FileExistsError), reads the existing content and either
    returns "unchanged" or raises ImmutableWriteError.

    Returns
    -------
    "written"   – file did not exist; it has been created.
    "unchanged" – file existed with identical content; nothing done.

    Raises
    ------
    ImmutableWriteError  – file existed with *different* content.
    ValueError           – *path* escapes *artifact_root*.
    """
    _check_no_traversal(path, artifact_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(path, "xb") as fh:
            fh.write(data)
        return "written"
    except FileExistsError:
        existing = path.read_bytes()
        if existing == data:
            return "unchanged"
        raise ImmutableWriteError(
            f"Cannot overwrite existing artifact with different content: "
            f"{path}"
        )


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
    """Stable-serialise *obj* (sorted keys) and write immutably."""
    serialised = (
        json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=True) + "\n"
    )
    return immutable_write_text(path, serialised, artifact_root)


def _check_no_traversal(
    path: pathlib.Path,
    artifact_root: pathlib.Path,
) -> None:
    """Raise ValueError if *path* resolves outside *artifact_root*."""
    try:
        resolved_path = pathlib.Path(path).resolve()
        resolved_root = pathlib.Path(artifact_root).resolve()
        resolved_path.relative_to(resolved_root)
    except ValueError:
        raise ValueError(
            f"Path traversal detected: {path!r} is outside "
            f"artifact root {artifact_root!r}"
        )


# ---------------------------------------------------------------------------
# JSON round-trip helpers
# ---------------------------------------------------------------------------

_PAIR_KNOWN_FIELDS: frozenset[str] = frozenset({
    "study_id", "pair_id", "model_id", "model_revision", "skill_id",
    "sample_index", "seed", "bare_prompt_hash", "scaffold_prompt_hash",
    "generation_config_hash", "source_git_commit", "created_at_utc",
    "raw_ab1_id", "raw_ab2_id", "raw_ab1_hash", "raw_ab2_hash",
    "extracted_ab1_hash", "extracted_ab2_hash",
})

_RUN_KNOWN_FIELDS: frozenset[str] = frozenset({
    "study_id", "pair_id", "treatment", "run_id",
    "input_artifact_hash", "output_artifact_hash",
    "source_git_commit", "created_at_utc",
    "trace_hash", "evaluation_hash",
})


def pair_metadata_to_dict(meta: PairMetadata) -> Dict[str, Any]:
    """Serialise *meta* to a plain dict (JSON-safe)."""
    d: Dict[str, Any] = {
        "study_id": meta.study_id,
        "pair_id": meta.pair_id,
        "model_id": meta.model_id,
        "model_revision": meta.model_revision,
        "skill_id": meta.skill_id,
        "sample_index": meta.sample_index,
        "seed": meta.seed,
        "bare_prompt_hash": meta.bare_prompt_hash,
        "scaffold_prompt_hash": meta.scaffold_prompt_hash,
        "generation_config_hash": meta.generation_config_hash,
        "source_git_commit": meta.source_git_commit,
        "created_at_utc": meta.created_at_utc,
        "raw_ab1_id": meta.raw_ab1_id,
        "raw_ab2_id": meta.raw_ab2_id,
        "raw_ab1_hash": meta.raw_ab1_hash,
        "raw_ab2_hash": meta.raw_ab2_hash,
        "extracted_ab1_hash": meta.extracted_ab1_hash,
        "extracted_ab2_hash": meta.extracted_ab2_hash,
    }
    d.update(meta.extra)
    return d


def pair_metadata_from_dict(d: Dict[str, Any]) -> PairMetadata:
    """Deserialise a plain dict to :class:`PairMetadata`."""
    extra = {k: v for k, v in d.items() if k not in _PAIR_KNOWN_FIELDS}
    return PairMetadata(
        study_id=d["study_id"],
        pair_id=d["pair_id"],
        model_id=d["model_id"],
        model_revision=d["model_revision"],
        skill_id=d["skill_id"],
        sample_index=d["sample_index"],
        seed=d.get("seed"),
        bare_prompt_hash=d["bare_prompt_hash"],
        scaffold_prompt_hash=d["scaffold_prompt_hash"],
        generation_config_hash=d["generation_config_hash"],
        source_git_commit=d["source_git_commit"],
        created_at_utc=d["created_at_utc"],
        raw_ab1_id=d.get("raw_ab1_id"),
        raw_ab2_id=d.get("raw_ab2_id"),
        raw_ab1_hash=d.get("raw_ab1_hash"),
        raw_ab2_hash=d.get("raw_ab2_hash"),
        extracted_ab1_hash=d.get("extracted_ab1_hash"),
        extracted_ab2_hash=d.get("extracted_ab2_hash"),
        extra=extra,
    )


def pair_metadata_json_round_trip(meta: PairMetadata) -> PairMetadata:
    """Serialise to JSON string and back; used for round-trip tests."""
    raw_json = json.dumps(
        pair_metadata_to_dict(meta),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return pair_metadata_from_dict(json.loads(raw_json))


def run_metadata_to_dict(meta: RunMetadata) -> Dict[str, Any]:
    """Serialise *meta* to a plain dict (JSON-safe).

    Raises ValueError if meta.extra conflicts with any official field
    (defence-in-depth: validate_run_metadata enforces this too, but
    serialisation must never silently shadow authoritative values).
    """
    d: Dict[str, Any] = {
        "study_id": meta.study_id,
        "pair_id": meta.pair_id,
        "treatment": meta.treatment,
        "run_id": meta.run_id,
        "input_artifact_hash": meta.input_artifact_hash,
        "output_artifact_hash": meta.output_artifact_hash,
        "source_git_commit": meta.source_git_commit,
        "created_at_utc": meta.created_at_utc,
        "trace_hash": meta.trace_hash,
        "evaluation_hash": meta.evaluation_hash,
    }
    conflicts = set(meta.extra) & set(d)
    if conflicts:
        raise ValueError(
            f"run_metadata_to_dict: extra fields conflict with official fields; "
            f"conflicts: {sorted(conflicts)}"
        )
    d.update(meta.extra)
    return d


def run_metadata_from_dict(d: Dict[str, Any]) -> RunMetadata:
    """Deserialise a plain dict to :class:`RunMetadata`."""
    extra = {k: v for k, v in d.items() if k not in _RUN_KNOWN_FIELDS}
    return RunMetadata(
        study_id=d["study_id"],
        pair_id=d["pair_id"],
        treatment=d["treatment"],
        run_id=d["run_id"],
        input_artifact_hash=d["input_artifact_hash"],
        output_artifact_hash=d["output_artifact_hash"],
        source_git_commit=d["source_git_commit"],
        created_at_utc=d["created_at_utc"],
        trace_hash=d.get("trace_hash"),
        evaluation_hash=d.get("evaluation_hash"),
        extra=extra,
    )


def run_metadata_json_round_trip(meta: RunMetadata) -> RunMetadata:
    """Serialise to JSON string and back; used for round-trip tests."""
    raw_json = json.dumps(
        run_metadata_to_dict(meta),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return run_metadata_from_dict(json.loads(raw_json))


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------


def utc_now_iso8601() -> str:
    """Return current UTC time as ISO-8601 string with +00:00 offset."""
    return datetime.now(tz=timezone.utc).isoformat(timespec="microseconds")
