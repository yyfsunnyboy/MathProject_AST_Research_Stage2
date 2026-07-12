"""
Legacy Ab2 replay runner — deterministic Core Adapter operational audit.

Scope
-----
Takes the 7 canonical legacy Ab2 code samples locked by
tests/finals_rebuild/fixtures/legacy_replay_manifest.json (via
legacy_migration.migrate_all()) and, for each one:

    legacy Ab2 code
    -> static evaluation + bounded execution (before)
    -> run_core_adapter()  [deterministic, no LLM]
    -> static evaluation + bounded execution (after)
    -> treatment trace
    -> operational classification

This module never generates Ab1/Ab2g (they already exist as legacy raw
code), never runs the Spec Adapter, never calls a model, and never
fabricates a TestSuite. HumanEval/MBPP/EvalPlus/MCRI are out of scope.

test_pass is always None here: legacy samples have no reliable fixture
TestSuite, so this module only ever reports syntax/execution operational
outcome (test_status="not_run"), never a fabricated functional-correctness
verdict.

Reproducibility
---------------
No wall-clock timestamps or random identifiers are embedded in the output:
_FIXED_CREATED_AT_UTC is a constant placeholder (not datetime.now()) used
only so TreatmentTrace/EvaluationResult's created_at_utc validators are
satisfied; it never varies between runs. Re-running with the same
manifest, source files, and evaluator_git_commit reproduces identical
pair_id / source_hash / before_code_hash / after_code_hash /
classification / summary counts / JSON byte content.
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import replace
from typing import Any, Dict, List, Union

from agent_tools.finals_rebuild.artifacts import build_run_id, sha256_text
from agent_tools.finals_rebuild.core_adapter import run_core_adapter
from agent_tools.finals_rebuild.evaluation import (
    EvaluationResult,
    evaluation_result_to_dict,
    validate_evaluation_result,
)
from agent_tools.finals_rebuild.execution_evaluator import evaluate_with_execution
from agent_tools.finals_rebuild.legacy_migration import migrate_all
from agent_tools.finals_rebuild.trace import (
    TreatmentTrace,
    treatment_trace_to_dict,
    validate_treatment_trace,
)

EXPECTED_ENTRY_COUNT = 7

# Fixed, non-current placeholder timestamp — required only to satisfy the
# UTC ISO-8601 format validators on TreatmentTrace/EvaluationResult.
# Never derived from datetime.now(); never varies between runs.
_FIXED_CREATED_AT_UTC = "2000-01-01T00:00:00+00:00"

_BEFORE_TREATMENT = "ab2"
_AFTER_TREATMENT = "ab3_core"

OPERATIONAL_RESCUED = "operational_rescued"
OPERATIONAL_REGRESSION = "operational_regression"
OPERATIONAL_UNCHANGED_PASS = "operational_unchanged_pass"
OPERATIONAL_UNCHANGED_FAIL = "operational_unchanged_fail"


class LegacyReplayError(ValueError):
    """Raised on any legacy-replay invariant violation; fails closed."""


# ---------------------------------------------------------------------------
# Pair identity
# ---------------------------------------------------------------------------


def build_legacy_pair_id(
    sample_id: str,
    skill_id: str,
    model_id: str,
    sample_index: int,
    declared_source_hash: str,
) -> str:
    """Deterministic pair_id for one legacy replay sample.

    Distinct from artifacts.build_pair_id (which requires bare/scaffold
    prompt hashes that do not exist for legacy single-code replay) — this
    is the legacy-replay module's own identity scheme, built only from
    manifest-declared identity fields plus the declared source hash so
    that it is fully independent of anything computed at replay time.
    """
    payload = "\x00".join(
        (
            "legacy_replay",
            sample_id,
            skill_id,
            model_id,
            str(sample_index),
            declared_source_hash,
        )
    )
    return sha256_text(payload)


# ---------------------------------------------------------------------------
# Operational classification
# ---------------------------------------------------------------------------


def _is_operational_pass(evaluation: EvaluationResult) -> bool:
    """syntax_pass is True AND execution_success is True. None never
    counts as pass."""
    return evaluation.syntax_pass is True and evaluation.execution_success is True


def classify_operational(before: EvaluationResult, after: EvaluationResult) -> str:
    """Pure classification of the before/after operational outcome.

    before fail, after pass -> operational_rescued
    before pass, after fail -> operational_regression
    before pass, after pass -> operational_unchanged_pass
    before fail, after fail -> operational_unchanged_fail
    """
    before_pass = _is_operational_pass(before)
    after_pass = _is_operational_pass(after)

    if not before_pass and after_pass:
        return OPERATIONAL_RESCUED
    if before_pass and not after_pass:
        return OPERATIONAL_REGRESSION
    if before_pass and after_pass:
        return OPERATIONAL_UNCHANGED_PASS
    return OPERATIONAL_UNCHANGED_FAIL


# ---------------------------------------------------------------------------
# Single-entry replay
# ---------------------------------------------------------------------------


def _replay_one(
    migrated: Dict[str, Any],
    evaluator_git_commit: str,
) -> Dict[str, Any]:
    metadata = migrated["metadata"]
    sample_id = metadata["sample_id"]
    skill_id = metadata["skill_id"]
    model_id = metadata["model_id"]
    sample_index = metadata["sample_index"]
    source_path = metadata["source_ab2_path"]
    declared_source_hash = metadata["source_file_hash"]
    actual_source_hash = migrated["source_file_hash"]

    if actual_source_hash != declared_source_hash:
        raise LegacyReplayError(
            f"{sample_id!r}: source_file_hash mismatch: "
            f"manifest={declared_source_hash!r}, actual={actual_source_hash!r}"
        )

    pair_id = build_legacy_pair_id(
        sample_id=sample_id,
        skill_id=skill_id,
        model_id=model_id,
        sample_index=sample_index,
        declared_source_hash=declared_source_hash,
    )

    before_code = migrated["extracted_code"]
    before_code_hash = sha256_text(before_code)

    core_result = run_core_adapter(pair_id=pair_id, input_code=before_code)
    after_code = core_result.output_code
    after_code_hash = sha256_text(after_code)
    changed = core_result.trace.changed
    core_fix_count = len(core_result.trace.rules_triggered)

    after_run_id = build_run_id(pair_id, _AFTER_TREATMENT, after_code_hash)
    finalized_trace: TreatmentTrace = replace(
        core_result.trace,
        run_id=after_run_id,
        created_at_utc=_FIXED_CREATED_AT_UTC,
    )
    try:
        validate_treatment_trace(finalized_trace)
    except Exception as exc:
        raise LegacyReplayError(
            f"{sample_id!r}: adapter trace failed validation: {exc}"
        ) from exc

    before_run_id = build_run_id(pair_id, _BEFORE_TREATMENT, before_code_hash)
    before_eval_raw = evaluate_with_execution(
        code=before_code,
        pair_id=pair_id,
        run_id=before_run_id,
        treatment=_BEFORE_TREATMENT,
        artifact_hash=before_code_hash,
        evaluator_git_commit=evaluator_git_commit,
    )
    before_evaluation = replace(before_eval_raw, created_at_utc=_FIXED_CREATED_AT_UTC)

    after_eval_raw = evaluate_with_execution(
        code=after_code,
        pair_id=pair_id,
        run_id=after_run_id,
        treatment=_AFTER_TREATMENT,
        artifact_hash=after_code_hash,
        evaluator_git_commit=evaluator_git_commit,
    )
    after_evaluation = replace(after_eval_raw, created_at_utc=_FIXED_CREATED_AT_UTC)

    for label, evaluation in (("before", before_evaluation), ("after", after_evaluation)):
        try:
            validate_evaluation_result(evaluation)
        except Exception as exc:
            raise LegacyReplayError(
                f"{sample_id!r}: {label} evaluation failed schema validation: {exc}"
            ) from exc

    operational_classification = classify_operational(before_evaluation, after_evaluation)

    return {
        "pair_id": pair_id,
        "skill_id": skill_id,
        "sample_index": sample_index,
        "source_path": source_path,
        "source_hash": actual_source_hash,
        "before_code_hash": before_code_hash,
        "after_code_hash": after_code_hash,
        "changed": changed,
        "core_fix_count": core_fix_count,
        "trace": treatment_trace_to_dict(finalized_trace),
        "before_evaluation": evaluation_result_to_dict(before_evaluation),
        "after_evaluation": evaluation_result_to_dict(after_evaluation),
        "operational_classification": operational_classification,
        "test_status": after_evaluation.test_status,
    }


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


def _build_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(results)
    changed_count = sum(1 for r in results if r["changed"])
    unchanged_count = total - changed_count

    classification_counts = {
        OPERATIONAL_RESCUED: 0,
        OPERATIONAL_REGRESSION: 0,
        OPERATIONAL_UNCHANGED_PASS: 0,
        OPERATIONAL_UNCHANGED_FAIL: 0,
    }
    not_test_assessable_count = 0
    for r in results:
        classification_counts[r["operational_classification"]] += 1
        if r["test_status"] != "completed":
            not_test_assessable_count += 1

    return {
        "total": total,
        "changed_count": changed_count,
        "unchanged_count": unchanged_count,
        "operational_rescued": classification_counts[OPERATIONAL_RESCUED],
        "operational_regression": classification_counts[OPERATIONAL_REGRESSION],
        "operational_unchanged_pass": classification_counts[OPERATIONAL_UNCHANGED_PASS],
        "operational_unchanged_fail": classification_counts[OPERATIONAL_UNCHANGED_FAIL],
        "operational_net_gain": (
            classification_counts[OPERATIONAL_RESCUED]
            - classification_counts[OPERATIONAL_REGRESSION]
        ),
        "not_test_assessable_count": not_test_assessable_count,
    }


# ---------------------------------------------------------------------------
# JSON writing
# ---------------------------------------------------------------------------


def _write_json_deterministic(obj: Any, path: pathlib.Path) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        serialised = (
            json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
        )
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(serialised)
    except OSError as exc:
        raise LegacyReplayError(f"failed to write output file {path}: {exc}") from exc


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


def run_legacy_replay(
    manifest_path: Union[str, pathlib.Path],
    project_root: Union[str, pathlib.Path],
    artifact_root: Union[str, pathlib.Path],
    output_dir: Union[str, pathlib.Path],
    evaluator_git_commit: str,
) -> Dict[str, Any]:
    """
    Run the full legacy replay over every manifest entry and write
    ``legacy_replay_results.json`` / ``legacy_replay_summary.json`` under
    *output_dir*.

    Only calls migrate_all()/run_core_adapter() — never the Spec Adapter,
    never a model, never a fabricated TestSuite. Fails closed (raises
    LegacyReplayError) on: missing manifest/source, source hash mismatch,
    duplicate pair identity, a migration result count other than
    EXPECTED_ENTRY_COUNT, an invalid adapter trace, an evaluation schema
    failure, or an unwritable output_dir. Never warns-and-skips.

    *artifact_root* is accepted for interface symmetry with the paired
    pipeline's artifact-root convention but is not itself written to by
    this function; all replay output goes to *output_dir*.
    """
    manifest_path = pathlib.Path(manifest_path)
    if not manifest_path.is_file():
        raise LegacyReplayError(f"manifest not found: {manifest_path}")

    try:
        migrated_entries = migrate_all(manifest_path, project_root)
    except (OSError, ValueError) as exc:
        raise LegacyReplayError(f"migration failed: {exc}") from exc

    if len(migrated_entries) != EXPECTED_ENTRY_COUNT:
        raise LegacyReplayError(
            f"expected exactly {EXPECTED_ENTRY_COUNT} migrated entries, "
            f"got {len(migrated_entries)}"
        )

    results: List[Dict[str, Any]] = []
    seen_pair_ids: set[str] = set()

    for migrated in migrated_entries:
        result = _replay_one(migrated, evaluator_git_commit)
        if result["pair_id"] in seen_pair_ids:
            raise LegacyReplayError(
                f"duplicate pair identity: {result['pair_id']!r} "
                f"(sample_id={migrated['metadata']['sample_id']!r})"
            )
        seen_pair_ids.add(result["pair_id"])
        results.append(result)

    summary = _build_summary(results)

    output_dir = pathlib.Path(output_dir)
    _write_json_deterministic(results, output_dir / "legacy_replay_results.json")
    _write_json_deterministic(summary, output_dir / "legacy_replay_summary.json")

    return {"results": results, "summary": summary}
