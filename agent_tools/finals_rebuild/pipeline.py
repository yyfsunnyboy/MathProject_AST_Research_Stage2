"""
Paired ablation pipeline for the finals-rebuild study.

No model API calls are made here.  The pipeline:

1. Validates prompt hashes and pair_id against PairMetadata.
2. Computes raw hashes and IDs (ab1_raw / scaffold_raw roles).
3. Runs canonical extraction – scaffold raw is extracted ONCE and shared
   across Ab2, Ab3-Core, and Ab3-Full.
4. Applies pass-through treatment adapters (real Healer/Adapter to be
   wired in Commit 3).
5. Builds ArtifactPaths and resolves per-treatment timestamps (idempotent:
   re-uses existing created_at_utc if run metadata already exists).
6. Builds and validates RunMetadata for each treatment.
7. Verifies shared run identity (ab2/ab3_core/ab3_full).
8. Completes PairMetadata (stage="complete") and validates.
9. Writes all artifacts via immutable helpers.
10. Verifies on-disk output hashes match RunMetadata.

Idempotency
-----------
Re-running the pipeline with the same inputs succeeds without errors:
- All text/extracted artifacts are byte-identical → immutable write
  returns "unchanged".
- run metadata JSONs preserve their original created_at_utc so that
  repeated serialisation produces bit-identical files.

Pass-through marker
-------------------
All four treatments carry (stored in RunMetadata.extra / run JSON):
    treatment_applied = false
    changed           = false
    implementation_status = "pass_through"

This is NOT "healer_applied=True" or "repaired=True".
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from agent_tools.finals_rebuild.artifacts import (
    ArtifactPaths,
    PairMetadata,
    RunMetadata,
    build_pair_id,
    build_raw_id,
    build_run_id,
    immutable_write_json,
    immutable_write_text,
    pair_metadata_to_dict,
    run_metadata_to_dict,
    sha256_bytes,
    sha256_text,
    utc_now_iso8601,
    validate_pair_metadata,
    validate_run_metadata,
    validate_shared_run_identity,
)
from agent_tools.finals_rebuild.extraction import ExtractionResult, extract_code


class PipelineError(Exception):
    """Raised on any invariant violation; pipeline fails closed."""


# ---------------------------------------------------------------------------
# Input / Output data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TreatmentOutput:
    """Immutable result for one treatment slot."""

    treatment: str
    output_code: str
    output_hash: str
    run_id: str
    treatment_applied: bool
    changed: bool
    implementation_status: str
    run_metadata: RunMetadata


@dataclass(frozen=True)
class PairedPipelineInput:
    """
    All inputs for one paired ablation run.

    ``raw_scaffold_response`` is intentionally a single field shared by
    Ab2, Ab3-Core, and Ab3-Full.  There is no separate ``raw_ab2_response``,
    ``raw_ab3_core_response``, or ``raw_ab3_full_response`` parameter –
    making it structurally impossible to supply different scaffold raws per
    treatment.
    """

    pair_metadata: PairMetadata
    bare_prompt_text: str
    scaffold_prompt_text: str
    raw_ab1_response: str
    raw_scaffold_response: str
    artifact_root: pathlib.Path


@dataclass(frozen=True)
class PairedPipelineResult:
    """Immutable result of a complete paired pipeline run."""

    pair_id: str
    raw_ab1_id: str
    raw_scaffold_id: str
    extracted_ab1_hash: str
    extracted_scaffold_hash: str
    treatment_outputs: Dict[str, TreatmentOutput]
    artifact_paths: ArtifactPaths
    validation_status: str


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


def run_paired_pipeline(inp: PairedPipelineInput) -> PairedPipelineResult:
    """
    Execute one paired ablation run.  See module docstring for steps.
    """
    meta = inp.pair_metadata
    artifact_root = pathlib.Path(inp.artifact_root)
    now = utc_now_iso8601()

    # ── Step 1: Prompt hash validation ──────────────────────────────────────
    bare_hash_actual = sha256_text(inp.bare_prompt_text)
    if bare_hash_actual != meta.bare_prompt_hash:
        raise PipelineError(
            f"bare_prompt_text hash mismatch: "
            f"computed={bare_hash_actual!r}, "
            f"stored={meta.bare_prompt_hash!r}"
        )

    scaffold_hash_actual = sha256_text(inp.scaffold_prompt_text)
    if scaffold_hash_actual != meta.scaffold_prompt_hash:
        raise PipelineError(
            f"scaffold_prompt_text hash mismatch: "
            f"computed={scaffold_hash_actual!r}, "
            f"stored={meta.scaffold_prompt_hash!r}"
        )

    # ── Step 2: pair_id consistency ─────────────────────────────────────────
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
        raise PipelineError(
            f"pair_id mismatch: stored={meta.pair_id!r}, "
            f"expected={expected_pair_id!r}"
        )

    # ── Step 3: Raw hashes and IDs ──────────────────────────────────────────
    raw_ab1_hash = sha256_text(inp.raw_ab1_response)
    raw_scaffold_hash = sha256_text(inp.raw_scaffold_response)

    raw_ab1_id = build_raw_id(meta.pair_id, "ab1_raw", raw_ab1_hash)
    raw_scaffold_id = build_raw_id(meta.pair_id, "scaffold_raw", raw_scaffold_hash)

    # ── Step 4: Canonical extraction (scaffold extracted ONCE) ──────────────
    ext_ab1: ExtractionResult = extract_code(inp.raw_ab1_response)
    ext_scaffold: ExtractionResult = extract_code(inp.raw_scaffold_response)

    _assert_extractable(ext_ab1, "ab1")
    _assert_extractable(ext_scaffold, "scaffold")

    extracted_ab1: str = ext_ab1.extracted_code  # type: ignore[assignment]
    extracted_ab1_hash: str = ext_ab1.extracted_code_hash  # type: ignore[assignment]
    extracted_scaffold: str = ext_scaffold.extracted_code  # type: ignore[assignment]
    extracted_scaffold_hash: str = ext_scaffold.extracted_code_hash  # type: ignore[assignment]

    # ── Step 5: Pass-through treatment adapters ─────────────────────────────
    _slot: Dict[str, Dict[str, Any]] = {
        "ab1": {
            "output_code": extracted_ab1,
            "input_hash": extracted_ab1_hash,
            "treatment_applied": False,
            "changed": False,
            "implementation_status": "pass_through",
        },
        "ab2": {
            "output_code": extracted_scaffold,
            "input_hash": extracted_scaffold_hash,
            "treatment_applied": False,
            "changed": False,
            "implementation_status": "pass_through",
        },
        "ab3_core": {
            "output_code": extracted_scaffold,
            "input_hash": extracted_scaffold_hash,
            "treatment_applied": False,
            "changed": False,
            "implementation_status": "pass_through",
        },
        "ab3_full": {
            "output_code": extracted_scaffold,
            "input_hash": extracted_scaffold_hash,
            "treatment_applied": False,
            "changed": False,
            "implementation_status": "pass_through",
        },
    }

    # ── Step 6: ArtifactPaths (created here so timestamps can be resolved) ──
    ap = ArtifactPaths(
        root=artifact_root,
        study_id=meta.study_id,
        pair_id=meta.pair_id,
    )

    # ── Build RunMetadata (idempotent timestamps) ────────────────────────────
    treatment_outputs: Dict[str, TreatmentOutput] = {}
    for treatment, slot in _slot.items():
        output_hash = sha256_text(slot["output_code"])
        run_id = build_run_id(meta.pair_id, treatment, output_hash)

        # Preserve existing created_at_utc on re-runs for idempotency
        run_ts = _read_existing_created_at(ap.run_metadata_json(treatment), now)

        run_meta = RunMetadata(
            study_id=meta.study_id,
            pair_id=meta.pair_id,
            treatment=treatment,
            run_id=run_id,
            input_artifact_hash=slot["input_hash"],
            output_artifact_hash=output_hash,
            source_git_commit=meta.source_git_commit,
            created_at_utc=run_ts,
            trace_hash=None,
            evaluation_hash=None,
            extra={
                "treatment_applied": slot["treatment_applied"],
                "changed": slot["changed"],
                "implementation_status": slot["implementation_status"],
            },
        )
        validate_run_metadata(run_meta)
        treatment_outputs[treatment] = TreatmentOutput(
            treatment=treatment,
            output_code=slot["output_code"],
            output_hash=output_hash,
            run_id=run_id,
            treatment_applied=slot["treatment_applied"],
            changed=slot["changed"],
            implementation_status=slot["implementation_status"],
            run_metadata=run_meta,
        )

    # ── Step 7: Shared run identity ─────────────────────────────────────────
    validate_shared_run_identity(
        ab2_run=treatment_outputs["ab2"].run_metadata,
        ab3_core_run=treatment_outputs["ab3_core"].run_metadata,
        ab3_full_run=treatment_outputs["ab3_full"].run_metadata,
    )

    # ── Step 8: Complete PairMetadata ───────────────────────────────────────
    completed_meta = PairMetadata(
        study_id=meta.study_id,
        pair_id=meta.pair_id,
        model_id=meta.model_id,
        model_revision=meta.model_revision,
        skill_id=meta.skill_id,
        sample_index=meta.sample_index,
        seed=meta.seed,
        bare_prompt_hash=meta.bare_prompt_hash,
        scaffold_prompt_hash=meta.scaffold_prompt_hash,
        generation_config_hash=meta.generation_config_hash,
        source_git_commit=meta.source_git_commit,
        created_at_utc=meta.created_at_utc,
        raw_ab1_id=raw_ab1_id,
        raw_ab2_id=raw_scaffold_id,
        raw_ab1_hash=raw_ab1_hash,
        raw_ab2_hash=raw_scaffold_hash,
        extracted_ab1_hash=extracted_ab1_hash,
        extracted_ab2_hash=extracted_scaffold_hash,
        extra=meta.extra,
    )
    validate_pair_metadata(completed_meta, stage="complete")

    # ── Step 9: Artifact writes ─────────────────────────────────────────────
    immutable_write_text(ap.prompt_ab1, inp.bare_prompt_text, artifact_root)
    immutable_write_text(ap.prompt_ab2, inp.scaffold_prompt_text, artifact_root)
    immutable_write_text(ap.raw_ab1, inp.raw_ab1_response, artifact_root)
    immutable_write_text(ap.raw_ab2, inp.raw_scaffold_response, artifact_root)
    immutable_write_text(ap.extracted_ab1, extracted_ab1, artifact_root)
    immutable_write_text(ap.extracted_ab2, extracted_scaffold, artifact_root)

    for treatment, to in treatment_outputs.items():
        immutable_write_text(
            ap.treatment_file(treatment), to.output_code, artifact_root
        )

    immutable_write_json(
        ap.pair_metadata_json,
        pair_metadata_to_dict(completed_meta),
        artifact_root,
    )

    for treatment, to in treatment_outputs.items():
        immutable_write_json(
            ap.run_metadata_json(treatment),
            run_metadata_to_dict(to.run_metadata),
            artifact_root,
        )

    # ── Step 10: Verify output hashes ───────────────────────────────────────
    for treatment, to in treatment_outputs.items():
        actual_bytes = ap.treatment_file(treatment).read_bytes()
        actual_hash = sha256_bytes(actual_bytes)
        expected_hash = to.run_metadata.output_artifact_hash
        if actual_hash != expected_hash:
            raise PipelineError(
                f"{treatment}: output hash mismatch after write: "
                f"expected={expected_hash!r}, actual={actual_hash!r}"
            )

    return PairedPipelineResult(
        pair_id=meta.pair_id,
        raw_ab1_id=raw_ab1_id,
        raw_scaffold_id=raw_scaffold_id,
        extracted_ab1_hash=extracted_ab1_hash,
        extracted_scaffold_hash=extracted_scaffold_hash,
        treatment_outputs=treatment_outputs,
        artifact_paths=ap,
        validation_status="complete",
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _assert_extractable(result: ExtractionResult, label: str) -> None:
    """Raise PipelineError if extraction did not succeed (fail-closed)."""
    if result.extraction_status == "extracted":
        return
    raise PipelineError(
        f"{label} extraction failed: "
        f"status={result.extraction_status!r}, "
        f"diagnostics={result.diagnostics}"
    )


def _read_existing_created_at(path: pathlib.Path, default: str) -> str:
    """
    Return the ``created_at_utc`` stored in *path* if the file exists and is
    valid JSON; otherwise return *default*.

    This preserves the original timestamp across idempotent re-runs so that
    the serialised run metadata JSON remains byte-identical and passes the
    immutable write content check.
    """
    if path.is_file():
        try:
            d = json.loads(path.read_text(encoding="utf-8"))
            ts = d.get("created_at_utc", "")
            if ts:
                return ts
        except (json.JSONDecodeError, OSError):
            pass
    return default
