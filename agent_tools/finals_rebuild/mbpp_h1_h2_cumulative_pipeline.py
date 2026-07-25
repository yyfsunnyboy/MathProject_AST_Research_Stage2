"""Cumulative H1 → H2 → H3 → H4 pipeline for Stage2 MBPP+ development evidence.

Data flow (no model calls; rules are imported unchanged)::

  pipeline-normalized source
        │
        ▼
  H1  apply_healer(...)                         # entry-point alias
        │
        ▼
  H2  quarantine_module_assert_entrypoint_selftest(...)
        │
        ▼
  H3  insert_pass_for_empty_suite(...)          # empty suite recovery
        │
        ▼
  H4  quarantine_post_h2_top_level_demo_print(...)  # post-H2 provenance-gated print merge
        │
        ▼
  EvalPlus-ready completion (hook only; this module never runs EvalPlus)

Each stage input is previous stage's output_source. H4 is the one exception:
because it requires structural H2 provenance (see
mbpp_h4_top_level_demo_print_quarantine), it additionally receives H2's own
input source and H2's changed flag, not only H3's output_source.
"""

from __future__ import annotations

import difflib
import hashlib
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping

from agent_tools.finals_rebuild.mbpp_evaluator_blind_healer import (
    RULE_ID as H1_RULE_ID,
    apply_healer,
)
from agent_tools.finals_rebuild.mbpp_h2_module_assert_quarantine import (
    RULE_ID as H2_RULE_ID,
    quarantine_module_assert_entrypoint_selftest,
)
from agent_tools.finals_rebuild.mbpp_h3_empty_suite_pass_insertion import (
    RULE_ID as H3_RULE_ID,
    insert_pass_for_empty_suite,
)
from agent_tools.finals_rebuild.mbpp_h4_top_level_demo_print_quarantine import (
    RULE_ID as H4_RULE_ID,
    quarantine_post_h2_top_level_demo_print,
)

TRANSFORM_CLASSES = (
    "H1_ONLY", "H2_ONLY", "H3_ONLY", "H4_ONLY",
    "H1_AND_H2", "H1_AND_H3", "H1_AND_H4", "H2_AND_H3", "H2_AND_H4", "H3_AND_H4",
    "H1_AND_H2_AND_H3", "H1_AND_H2_AND_H4", "H1_AND_H3_AND_H4", "H2_AND_H3_AND_H4",
    "H1_AND_H2_AND_H3_AND_H4",
    "UNCHANGED"
)


def _sha256_text(value: str | None) -> str | None:
    if value is None:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _unified_diff(before: str | None, after: str | None, *, from_label: str, to_label: str) -> str:
    left = (before or "").splitlines(keepends=True)
    right = (after or "").splitlines(keepends=True)
    if left == right:
        return ""
    return "".join(
        difflib.unified_diff(
            left,
            right,
            fromfile=from_label,
            tofile=to_label,
            n=3,
        )
    )


@dataclass(frozen=True)
class StageRecord:
    stage: str
    rule_id: str | None
    status: str
    changed: bool
    abstained: bool
    reason: str
    input_sha256: str | None
    output_sha256: str | None
    input_source: str | None
    output_source: str | None
    diff: str
    extras: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        # Keep diffs for audit; callers may strip bulky source fields.
        return payload


@dataclass(frozen=True)
class CumulativePipelineResult:
    input_sha256: str | None
    h1_output_sha256: str | None
    h2_output_sha256: str | None
    h3_output_sha256: str | None
    h4_output_sha256: str | None
    final_source: str | None
    final_sha256: str | None
    transform_class: str
    h1: StageRecord
    h2: StageRecord
    h3: StageRecord
    h4: StageRecord
    evalplus: dict[str, Any]

    def to_dict(self, *, include_sources: bool = False) -> dict[str, Any]:
        def _stage(stage: StageRecord) -> dict[str, Any]:
            row = stage.to_dict()
            if not include_sources:
                row.pop("input_source", None)
                row.pop("output_source", None)
            return row

        return {
            "input_sha256": self.input_sha256,
            "h1_output_sha256": self.h1_output_sha256,
            "h2_output_sha256": self.h2_output_sha256,
            "h3_output_sha256": self.h3_output_sha256,
            "h4_output_sha256": self.h4_output_sha256,
            "final_sha256": self.final_sha256,
            "transform_class": self.transform_class,
            "h1": _stage(self.h1),
            "h2": _stage(self.h2),
            "h3": _stage(self.h3),
            "h4": _stage(self.h4),
            "evalplus": dict(self.evalplus),
            "final_source": self.final_source if include_sources else None,
        }


def classify_transform(*, h1_changed: bool, h2_changed: bool, h3_changed: bool, h4_changed: bool = False) -> str:
    if h1_changed and h2_changed and h3_changed and h4_changed:
        return "H1_AND_H2_AND_H3_AND_H4"
    if h1_changed and h2_changed and h3_changed:
        return "H1_AND_H2_AND_H3"
    if h1_changed and h2_changed and h4_changed:
        return "H1_AND_H2_AND_H4"
    if h1_changed and h3_changed and h4_changed:
        return "H1_AND_H3_AND_H4"
    if h2_changed and h3_changed and h4_changed:
        return "H2_AND_H3_AND_H4"
    if h1_changed and h2_changed:
        return "H1_AND_H2"
    if h1_changed and h3_changed:
        return "H1_AND_H3"
    if h1_changed and h4_changed:
        return "H1_AND_H4"
    if h2_changed and h3_changed:
        return "H2_AND_H3"
    if h2_changed and h4_changed:
        return "H2_AND_H4"
    if h3_changed and h4_changed:
        return "H3_AND_H4"
    if h1_changed:
        return "H1_ONLY"
    if h2_changed:
        return "H2_ONLY"
    if h3_changed:
        return "H3_ONLY"
    if h4_changed:
        return "H4_ONLY"
    return "UNCHANGED"


def apply_h1_stage(
    *,
    normalized_source: str | None,
    entry_point: str,
    expected_positional_arities: Iterable[int],
    generation_truncated: bool,
) -> StageRecord:
    result = apply_healer(
        normalized_source,
        entry_point,
        expected_positional_arities,
        generation_truncated,
    )
    changed = result.status == "transformed"
    abstained = result.status == "abstained"
    return StageRecord(
        stage="H1",
        rule_id=H1_RULE_ID,
        status=result.status,
        changed=changed,
        abstained=abstained,
        reason=result.diagnostic,
        input_sha256=result.input_sha256,
        output_sha256=result.output_sha256,
        input_source=normalized_source,
        output_source=result.output_source,
        diff=_unified_diff(
            normalized_source,
            result.output_source,
            from_label="pipeline_normalized",
            to_label="h1_output",
        ),
        extras={
            "triggered_rule_ids": list(result.triggered_rule_ids),
            "applied_rule_ids": list(result.applied_rule_ids),
            "ast_prefix_preserved": result.ast_prefix_preserved,
        },
    )


def apply_h2_stage(
    *,
    source: str | None,
    entry_point: str,
    extraction_unambiguous: bool | None,
    source_complete: bool | None,
) -> StageRecord:
    if source is None or not str(source).strip():
        digest = _sha256_text(source) if isinstance(source, str) else None
        return StageRecord(
            stage="H2",
            rule_id=H2_RULE_ID,
            status="abstained",
            changed=False,
            abstained=True,
            reason="missing_or_empty_source_for_h2",
            input_sha256=digest,
            output_sha256=digest,
            input_source=source,
            output_source=source,
            diff="",
            extras={
                "extraction_unambiguous": extraction_unambiguous,
                "source_complete": source_complete,
            },
        )

    decision = quarantine_module_assert_entrypoint_selftest(
        source=source,
        entry_point=entry_point,
        extraction_unambiguous=extraction_unambiguous,
        source_complete=source_complete,
    )
    return StageRecord(
        stage="H2",
        rule_id=decision.rule_id,
        status=(
            "transformed"
            if decision.transformed
            else ("abstained" if decision.abstained else "no_op")
        ),
        changed=decision.transformed,
        abstained=decision.abstained,
        reason=decision.reason,
        input_sha256=decision.source_sha256,
        output_sha256=decision.output_sha256,
        input_source=source,
        output_source=decision.output_source,
        diff=_unified_diff(
            source,
            decision.output_source,
            from_label="h1_output",
            to_label="h2_output",
        ),
        extras={
            "triggered": decision.triggered,
            "guard_results": decision.guard_results,
            "rule_status": decision.rule_status,
            "extraction_unambiguous": extraction_unambiguous,
            "source_complete": source_complete,
        },
    )


def apply_h3_stage(
    *,
    source: str | None,
    entry_point: str,
    extraction_unambiguous: bool | None,
    source_complete: bool | None,
) -> StageRecord:
    if source is None or not str(source).strip():
        digest = _sha256_text(source) if isinstance(source, str) else None
        return StageRecord(
            stage="H3",
            rule_id=H3_RULE_ID,
            status="abstained",
            changed=False,
            abstained=True,
            reason="missing_or_empty_source_for_h3",
            input_sha256=digest,
            output_sha256=digest,
            input_source=source,
            output_source=source,
            diff="",
            extras={
                "extraction_unambiguous": extraction_unambiguous,
                "source_complete": source_complete,
            },
        )

    decision = insert_pass_for_empty_suite(
        source,
        entry_point,
        extraction_unambiguous=extraction_unambiguous,
        source_complete=source_complete,
    )
    return StageRecord(
        stage="H3",
        rule_id=decision.rule_id,
        status=(
            "transformed"
            if decision.transformed
            else ("abstained" if decision.abstained else "no_op")
        ),
        changed=decision.transformed,
        abstained=decision.abstained,
        reason=decision.reason,
        input_sha256=decision.source_sha256,
        output_sha256=decision.output_sha256,
        input_source=source,
        output_source=decision.output_source,
        diff=_unified_diff(
            source,
            decision.output_source,
            from_label="h2_output",
            to_label="h3_output",
        ),
        extras={
            "triggered": decision.triggered,
            "guard_results": decision.guard_results,
            "error_line_number": decision.error_line_number,
            "empty_suite_location": decision.empty_suite_location,
            "parse_error_message": decision.parse_error_message,
        },
    )


def apply_h4_stage(
    *,
    source: str | None,
    h2_input_source: str | None,
    h2_changed: bool,
    entry_point: str,
    extraction_unambiguous: bool | None,
    source_complete: bool | None,
    public_assert_fingerprints: Iterable[str] | None = None,
) -> StageRecord:
    """``source`` is H3's output_source (H4's input, per fixed H1->H2->H3->H4
    order). ``h2_input_source`` is H2's own input (H1's output_source) and
    ``h2_changed`` is H2's StageRecord.changed for this cell -- both required
    for H4's post-H2 structural provenance check; see
    mbpp_h4_top_level_demo_print_quarantine for why H4 cannot safely reuse
    the pre-H2 top-level-assert guard shape.
    """
    if source is None or not str(source).strip():
        digest = _sha256_text(source) if isinstance(source, str) else None
        return StageRecord(
            stage="H4",
            rule_id=H4_RULE_ID,
            status="abstained",
            changed=False,
            abstained=True,
            reason="missing_or_empty_source_for_h4",
            input_sha256=digest,
            output_sha256=digest,
            input_source=source,
            output_source=source,
            diff="",
            extras={
                "extraction_unambiguous": extraction_unambiguous,
                "source_complete": source_complete,
                "h2_changed": h2_changed,
                "public_assert_fingerprints_provided": public_assert_fingerprints is not None,
            },
        )

    decision = quarantine_post_h2_top_level_demo_print(
        h2_input_source=h2_input_source or "",
        h4_input_source=source,
        h2_changed=h2_changed,
        entry_point=entry_point,
        extraction_unambiguous=extraction_unambiguous,
        source_complete=source_complete,
        public_assert_fingerprints=public_assert_fingerprints or [],
    )
    return StageRecord(
        stage="H4",
        rule_id=decision.rule_id,
        status=(
            "transformed"
            if decision.transformed
            else ("abstained" if decision.abstained else "no_op")
        ),
        changed=decision.transformed,
        abstained=decision.abstained,
        reason=decision.reason,
        input_sha256=decision.source_sha256,
        output_sha256=decision.output_sha256,
        input_source=source,
        output_source=decision.output_source,
        diff=_unified_diff(
            source,
            decision.output_source,
            from_label="h3_output",
            to_label="h4_output",
        ),
        extras={
            "triggered": decision.triggered,
            "guard_results": decision.guard_results,
            "h2_changed": h2_changed,
        },
    )


def evalplus_stage_hook(
    *,
    final_source: str | None,
    task_id: str | None = None,
    execute: bool = False,
) -> dict[str, Any]:
    """Wire-only EvalPlus stage. Refuses live execution in this packaging round."""
    if execute:
        raise RuntimeError(
            "cumulative H1→H2 pipeline refuses live EvalPlus in this wiring round"
        )
    return {
        "status": "wired_not_executed",
        "engine": "evalplus_deferred",
        "task_id": task_id,
        "final_sha256": _sha256_text(final_source),
        "model_calls": 0,
        "executed": False,
    }


def run_h1_then_h2_then_h3_then_h4(
    *,
    normalized_source: str | None,
    entry_point: str,
    expected_positional_arities: Iterable[int],
    generation_truncated: bool,
    extraction_unambiguous: bool | None,
    source_complete: bool | None,
    task_id: str | None = None,
    execute_evalplus: bool = False,
    public_assert_fingerprints: Iterable[str] | None = None,
) -> CumulativePipelineResult:
    """Apply H1 then H2 then H3 then H4. Each stage input is previous stage's output_source."""
    h1 = apply_h1_stage(
        normalized_source=normalized_source,
        entry_point=entry_point,
        expected_positional_arities=expected_positional_arities,
        generation_truncated=generation_truncated,
    )
    h2 = apply_h2_stage(
        source=h1.output_source,
        entry_point=entry_point,
        extraction_unambiguous=extraction_unambiguous,
        source_complete=source_complete,
    )
    h3 = apply_h3_stage(
        source=h2.output_source,
        entry_point=entry_point,
        extraction_unambiguous=extraction_unambiguous,
        source_complete=source_complete,
    )
    h4 = apply_h4_stage(
        source=h3.output_source,
        h2_input_source=h1.output_source,
        h2_changed=h2.changed,
        entry_point=entry_point,
        extraction_unambiguous=extraction_unambiguous,
        source_complete=source_complete,
        public_assert_fingerprints=public_assert_fingerprints,
    )
    transform_class = classify_transform(
        h1_changed=h1.changed, h2_changed=h2.changed, h3_changed=h3.changed, h4_changed=h4.changed
    )
    final_source = h4.output_source
    evalplus = evalplus_stage_hook(
        final_source=final_source,
        task_id=task_id,
        execute=execute_evalplus,
    )
    return CumulativePipelineResult(
        input_sha256=h1.input_sha256,
        h1_output_sha256=h1.output_sha256,
        h2_output_sha256=h2.output_sha256,
        h3_output_sha256=h3.output_sha256,
        h4_output_sha256=h4.output_sha256,
        final_source=final_source,
        final_sha256=h4.output_sha256,
        transform_class=transform_class,
        h1=h1,
        h2=h2,
        h3=h3,
        h4=h4,
        evalplus=evalplus,
    )


def run_h1_then_h2_then_h3(
    *,
    normalized_source: str | None,
    entry_point: str,
    expected_positional_arities: Iterable[int],
    generation_truncated: bool,
    extraction_unambiguous: bool | None,
    source_complete: bool | None,
    task_id: str | None = None,
    execute_evalplus: bool = False,
) -> CumulativePipelineResult:
    """Deprecated: use run_h1_then_h2_then_h3_then_h4 instead. Kept for backward compatibility."""
    return run_h1_then_h2_then_h3_then_h4(
        normalized_source=normalized_source,
        entry_point=entry_point,
        expected_positional_arities=expected_positional_arities,
        generation_truncated=generation_truncated,
        extraction_unambiguous=extraction_unambiguous,
        source_complete=source_complete,
        task_id=task_id,
        execute_evalplus=execute_evalplus,
        public_assert_fingerprints=None,
    )


def run_h1_then_h2(
    *,
    normalized_source: str | None,
    entry_point: str,
    expected_positional_arities: Iterable[int],
    generation_truncated: bool,
    extraction_unambiguous: bool | None,
    source_complete: bool | None,
    task_id: str | None = None,
    execute_evalplus: bool = False,
) -> CumulativePipelineResult:
    """Deprecated: use run_h1_then_h2_then_h3_then_h4 instead. Kept for backward compatibility."""
    return run_h1_then_h2_then_h3_then_h4(
        normalized_source=normalized_source,
        entry_point=entry_point,
        expected_positional_arities=expected_positional_arities,
        generation_truncated=generation_truncated,
        extraction_unambiguous=extraction_unambiguous,
        source_complete=source_complete,
        task_id=task_id,
        execute_evalplus=execute_evalplus,
        public_assert_fingerprints=None,
    )


def summarize_transform_classes(results: Iterable[CumulativePipelineResult]) -> dict[str, int]:
    counts = {name: 0 for name in TRANSFORM_CLASSES}
    for result in results:
        counts[result.transform_class] = counts.get(result.transform_class, 0) + 1
    return counts


def summarize_outcome_placeholders(
    *,
    results: Iterable[Mapping[str, Any]],
) -> dict[str, int]:
    """Count paired EvalPlus-style outcomes when provided by the caller.

    This helper never invents pass/fail; missing outcome fields are ignored.
    """
    counts = {
        "verified_rescue": 0,
        "regression": 0,
        "preserved_pass": 0,
        "unchanged_failure": 0,
        "missing_outcome": 0,
    }
    for row in results:
        outcome = row.get("outcome")
        if outcome is None:
            counts["missing_outcome"] += 1
        elif outcome in counts:
            counts[outcome] += 1
    return counts
