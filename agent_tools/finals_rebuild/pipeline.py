"""
Paired ablation pipeline for the finals-rebuild study.

No model API calls are made here.  The pipeline:

1. Validates prompt hashes and pair_id against PairMetadata.
2. Computes raw hashes and IDs (ab1_raw / scaffold_raw roles).
3. Runs canonical extraction – scaffold raw is extracted ONCE and shared
   across Ab2, Ab3-Core, and Ab3-Full.
4. Applies treatment adapters:
     - Ab1, Ab2: pure pass-through, no adapter invoked.
     - Ab3-Core: Core Adapter runs once on the extracted scaffold
       (agent_tools/finals_rebuild/core_adapter.py).
     - Ab3-Full: Spec Adapter runs once on the Core Adapter's own output
       (agent_tools/finals_rebuild/spec_adapter.py) — never on the raw
       extracted scaffold.
   Commit 3A ships every adapter rule disabled; see core_adapter.py /
   spec_adapter.py for the rule registries and trace.py for the
   TreatmentTrace schema.
5. Builds ArtifactPaths and resolves per-treatment timestamps (idempotent:
   re-uses existing created_at_utc if run metadata already exists).
6. Builds and validates RunMetadata for each treatment; binds each
   adapter's TreatmentTrace to the resolved run_id/timestamp and computes
   RunMetadata.trace_hash from it.
7. Verifies shared run identity (ab2/ab3_core/ab3_full).
8. Completes PairMetadata (stage="complete") and validates.
9. Writes all artifacts via immutable helpers, including trace.json for
   ab3_core / ab3_full.
10. Verifies on-disk output hashes (and trace hashes) match RunMetadata.

Idempotency
-----------
Re-running the pipeline with the same inputs succeeds without errors:
- All text/extracted artifacts are byte-identical → immutable write
  returns "unchanged".
- run metadata JSONs and trace.json preserve their original created_at_utc
  so that repeated serialisation produces bit-identical files.

Treatment status marker
------------------------
Stored in RunMetadata.extra / run JSON for every treatment:
    treatment_applied
    changed
    implementation_status  (see artifacts.ALLOWED_IMPLEMENTATION_STATUSES)

Ab1/Ab2 always carry treatment_applied=false, changed=false,
implementation_status="pass_through". Ab3-Core/Ab3-Full reflect their
adapter's TreatmentTrace; in Commit 3A both are "implemented" or
"implemented_no_safe_rule_triggered" (Core, and Spec on applicable
domains) or "not_applicable" (Spec on non-applicable domains) — never
"healer_applied=True" or "repaired=True" in the misleading sense.
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass, field, replace
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
from agent_tools.finals_rebuild.core_adapter import run_core_adapter
from agent_tools.finals_rebuild.extraction import ExtractionResult, extract_code
from agent_tools.finals_rebuild.spec_adapter import run_spec_adapter
from agent_tools.finals_rebuild.trace import (
    TreatmentTrace,
    compute_trace_hash,
    treatment_trace_to_dict,
    validate_treatment_trace,
)


class PipelineError(Exception):
    """Raised on any invariant violation; pipeline fails closed."""


class ExistingMetadataMismatchError(PipelineError):
    """Raised when an existing run-metadata file is inconsistent with the
    current pipeline run (study_id / pair_id / treatment / run_id mismatch,
    missing required field, or corrupt JSON).

    The pipeline must fail closed rather than silently mixing metadata from
    two different runs.
    """


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
    trace: Optional[TreatmentTrace] = None


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

    # ── Step 5: Treatment adapters ───────────────────────────────────────────
    # Ab1 and Ab2 remain pure pass-through — no adapter is invoked for either.
    # Ab3-Core runs the Core Adapter once on the shared extracted scaffold.
    # Ab3-Full runs the Spec Adapter once on the Core Adapter's own output
    # (never on the raw extracted scaffold), so Core always executes exactly
    # once and Spec always receives Core's output as its input.
    core_result = run_core_adapter(
        pair_id=meta.pair_id,
        input_code=extracted_scaffold,
    )
    spec_result = run_spec_adapter(
        pair_id=meta.pair_id,
        skill_id=meta.skill_id,
        input_code=core_result.output_code,
    )

    _slot: Dict[str, Dict[str, Any]] = {
        "ab1": {
            "output_code": extracted_ab1,
            "input_hash": extracted_ab1_hash,
            "treatment_applied": False,
            "changed": False,
            "implementation_status": "pass_through",
            "trace": None,
        },
        "ab2": {
            "output_code": extracted_scaffold,
            "input_hash": extracted_scaffold_hash,
            "treatment_applied": False,
            "changed": False,
            "implementation_status": "pass_through",
            "trace": None,
        },
        "ab3_core": {
            "output_code": core_result.output_code,
            "input_hash": extracted_scaffold_hash,
            "treatment_applied": core_result.trace.applied,
            "changed": core_result.trace.changed,
            "implementation_status": core_result.trace.implementation_status,
            "trace": core_result.trace,
        },
        "ab3_full": {
            "output_code": spec_result.output_code,
            "input_hash": spec_result.trace.input_hash,
            "treatment_applied": spec_result.trace.applied,
            "changed": spec_result.trace.changed,
            "implementation_status": spec_result.trace.implementation_status,
            "trace": spec_result.trace,
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

        # Preserve existing created_at_utc on re-runs for idempotency.
        # Full ID validation: fail-closed on any mismatch or corruption.
        run_ts = _read_existing_created_at(
            path=ap.run_metadata_json(treatment),
            expected_study_id=meta.study_id,
            expected_pair_id=meta.pair_id,
            expected_treatment=treatment,
            expected_run_id=run_id,
            default=now,
        )

        # Adapters cannot know run_id or the idempotent timestamp in advance
        # (both depend on output_hash / on-disk state resolved above), so
        # they return a trace with placeholders that is bound here.
        finalized_trace: Optional[TreatmentTrace] = None
        trace_hash: Optional[str] = None
        if slot["trace"] is not None:
            finalized_trace = replace(
                slot["trace"], run_id=run_id, created_at_utc=run_ts
            )
            validate_treatment_trace(finalized_trace)
            trace_hash = compute_trace_hash(finalized_trace)

        run_meta = RunMetadata(
            study_id=meta.study_id,
            pair_id=meta.pair_id,
            treatment=treatment,
            run_id=run_id,
            input_artifact_hash=slot["input_hash"],
            output_artifact_hash=output_hash,
            source_git_commit=meta.source_git_commit,
            created_at_utc=run_ts,
            trace_hash=trace_hash,
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
            trace=finalized_trace,
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

    for treatment, to in treatment_outputs.items():
        if to.trace is not None:
            immutable_write_json(
                ap.trace_json(treatment),
                treatment_trace_to_dict(to.trace),
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
        if to.trace is not None:
            actual_trace_bytes = ap.trace_json(treatment).read_bytes()
            actual_trace_hash = sha256_bytes(actual_trace_bytes)
            expected_trace_hash = to.run_metadata.trace_hash
            if actual_trace_hash != expected_trace_hash:
                raise PipelineError(
                    f"{treatment}: trace hash mismatch after write: "
                    f"expected={expected_trace_hash!r}, actual={actual_trace_hash!r}"
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


def _read_existing_created_at(
    path: pathlib.Path,
    expected_study_id: str,
    expected_pair_id: str,
    expected_treatment: str,
    expected_run_id: str,
    default: str,
) -> str:
    """Return ``created_at_utc`` from an existing run-metadata file,
    preserving the original timestamp across idempotent re-runs so that
    repeated serialisation produces byte-identical JSON.

    If *path* does not exist, returns *default* (the current timestamp).

    Raises
    ------
    ExistingMetadataMismatchError
        If the file exists but cannot be parsed, is missing required fields,
        or any of study_id / pair_id / treatment / run_id disagrees with the
        expected values.  The pipeline must fail closed rather than silently
        mixing metadata from two different runs.
    """
    if not path.is_file():
        return default

    try:
        stored = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise ExistingMetadataMismatchError(
            f"Failed to parse existing run metadata at {path!r}: {exc}"
        ) from exc

    for field_name, expected in (
        ("study_id", expected_study_id),
        ("pair_id", expected_pair_id),
        ("treatment", expected_treatment),
        ("run_id", expected_run_id),
    ):
        actual = stored.get(field_name)
        if actual is None:
            raise ExistingMetadataMismatchError(
                f"Existing run metadata at {path!r} is missing required "
                f"field {field_name!r}"
            )
        if actual != expected:
            raise ExistingMetadataMismatchError(
                f"Existing run metadata at {path!r}: "
                f"{field_name}={actual!r} does not match "
                f"expected {expected!r}"
            )

    ts = stored.get("created_at_utc", "")
    if not ts:
        raise ExistingMetadataMismatchError(
            f"Existing run metadata at {path!r} is missing created_at_utc"
        )
    return ts
