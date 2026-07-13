"""
Offline pilot mechanical-repair coverage audit (Stage 1).

Reads saved generation artifacts, runs Tier-1 (core) and provisional
Tier-1+exploratory (core + spec) repair paths without model calls,
network access, evaluator execution, or source artifact mutation.
"""

from __future__ import annotations

import argparse
import ast
import json
import pathlib
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from agent_tools.finals_rebuild.artifacts import sha256_text
from agent_tools.finals_rebuild.core_adapter import run_core_adapter
from agent_tools.finals_rebuild.extraction import extract_code
from agent_tools.finals_rebuild.pilot_artifact_loader import (
    FIDELITY_EXTRACTED_ONLY,
    FIDELITY_RAW_RESPONSE,
    LEGACY_TREATMENT,
    PilotArtifactLoaderError,
    PilotLoadedSample,
    SOURCE_FORMAT_AUTO,
    SUPPORTED_SOURCE_FORMATS,
    load_pilot_samples,
)
from agent_tools.finals_rebuild.spec_adapter import is_k12_math_domain, run_spec_adapter
from agent_tools.finals_rebuild.trace import (
    TraceStep,
    TreatmentTrace,
    treatment_trace_to_dict,
)

REPAIR_PATH_TIER1 = "tier1"
REPAIR_PATH_TIER1_EXPLORATORY = "tier1_exploratory"
SUPPORTED_REPAIR_PATHS: frozenset[str] = frozenset(
    {REPAIR_PATH_TIER1, REPAIR_PATH_TIER1_EXPLORATORY}
)

TAXONOMY_PRECEDENCE: Tuple[str, ...] = (
    "infrastructure_failure",
    "generation_catastrophic",
    "no_code_candidate",
    "ambiguous_candidates",
    "syntax_or_format",
    "missing_entry_point",
    "duplicate_or_multiple_entry_point",
    "runtime_error",
    "timeout",
    "semantic_or_test_failure",
    "none",
    "unknown",
)

_STAGE2_FORBIDDEN_SUMMARY_KEYS: frozenset[str] = frozenset(
    {"rescue", "regression", "net_gain", "pass@1", "pass_at_1"}
)

STAGE1_FULL = "full_stage1"
STAGE1_PARTIAL = "partial_stage1_extracted_only"
STAGE1_EXCLUDED = "excluded"


class PilotAuditError(Exception):
    """Raised when the pilot audit cannot proceed safely."""


@dataclass(frozen=True)
class CodeAnalysis:
    extraction_status: str
    extracted_code: Optional[str]
    code_hash: Optional[str]
    parse_status: str
    entry_point_count: int
    taxonomy_primary: str


@dataclass(frozen=True)
class RepairOutcome:
    code: Optional[str]
    code_hash: Optional[str]
    extraction_status: str
    parse_status: str
    entry_point_count: int
    taxonomy_primary: str
    triggered: bool
    triggered_rules: List[str]
    trace: List[Dict[str, Any]]


def _resolve_treatments(selection: str) -> List[str]:
    if selection == "all":
        return ["all"]
    return [selection.strip().lower()]


def _resolve_repair_paths(selection: str) -> List[str]:
    if selection == "all":
        return [REPAIR_PATH_TIER1, REPAIR_PATH_TIER1_EXPLORATORY]
    normalized = selection.strip().lower()
    if normalized not in SUPPORTED_REPAIR_PATHS:
        raise PilotAuditError(
            f"unsupported repair path {selection!r}; expected "
            f"tier1, tier1_exploratory, or all"
        )
    return [normalized]


def _pair_id_for_sample(sample: PilotLoadedSample) -> str:
    return sha256_text(f"pilot|{sample.task_id}|{sample.treatment}|{sample.source_id}")


def _count_entry_points(code: str, entry_point: str) -> Tuple[str, int]:
    if not code or not code.strip():
        return "skipped_no_candidate", 0
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return "failed", 0

    if not entry_point:
        defs = [
            node
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        return "success", len(defs)

    count = sum(
        1
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == entry_point
    )
    return "success", count


def _artifact_runtime_taxonomy(
    record_hints: Optional[Dict[str, Any]],
) -> Optional[str]:
    if not record_hints:
        return None
    for key, label in (
        ("runtime_error", "runtime_error"),
        ("timeout", "timeout"),
        ("semantic_or_test_failure", "semantic_or_test_failure"),
        ("infrastructure_failure", "infrastructure_failure"),
    ):
        if record_hints.get(key) is True:
            return label
    status = record_hints.get("execution_status")
    if status == "timeout":
        return "timeout"
    if status in ("failure", "error"):
        return "runtime_error"
    test_pass = record_hints.get("test_pass")
    if test_pass is False:
        return "semantic_or_test_failure"
    return None


def classify_taxonomy(
    *,
    raw_response: Optional[str],
    extraction_status: str,
    extracted_code: Optional[str],
    parse_status: str,
    entry_point_count: int,
    artifact_hints: Optional[Dict[str, Any]] = None,
    check_empty_raw: bool = True,
) -> str:
    candidates: List[str] = []

    artifact_label = _artifact_runtime_taxonomy(artifact_hints)
    if artifact_label:
        candidates.append(artifact_label)

    if check_empty_raw and (raw_response is None or not str(raw_response).strip()):
        candidates.append("generation_catastrophic")

    if extraction_status in ("empty", "unsupported"):
        candidates.append("no_code_candidate")
    elif extraction_status == "ambiguous":
        candidates.append("ambiguous_candidates")
    elif extraction_status == "not_replayed":
        if extracted_code is None or not str(extracted_code).strip():
            candidates.append("no_code_candidate")

    if parse_status == "failed":
        candidates.append("syntax_or_format")

    if parse_status == "success":
        if entry_point_count == 0:
            candidates.append("missing_entry_point")
        elif entry_point_count > 1:
            candidates.append("duplicate_or_multiple_entry_point")
        elif entry_point_count == 1:
            candidates.append("none")

    if not candidates:
        return "unknown"

    for label in TAXONOMY_PRECEDENCE:
        if label in candidates:
            return label
    return "unknown"


def analyze_raw_response(
    raw_response: Optional[str],
    *,
    entry_point: Optional[str],
    artifact_hints: Optional[Dict[str, Any]] = None,
) -> CodeAnalysis:
    if raw_response is None or not raw_response.strip():
        return CodeAnalysis(
            extraction_status="empty",
            extracted_code=None,
            code_hash=None,
            parse_status="skipped_no_candidate",
            entry_point_count=0,
            taxonomy_primary=classify_taxonomy(
                raw_response=raw_response,
                extraction_status="empty",
                extracted_code=None,
                parse_status="skipped_no_candidate",
                entry_point_count=0,
                artifact_hints=artifact_hints,
            ),
        )

    ext = extract_code(raw_response)
    extracted = ext.extracted_code if ext.extraction_status == "extracted" else None
    code_hash = sha256_text(extracted) if extracted else None
    parse_status, entry_point_count = _count_entry_points(
        extracted or "", entry_point or ""
    )
    taxonomy = classify_taxonomy(
        raw_response=raw_response,
        extraction_status=ext.extraction_status,
        extracted_code=extracted,
        parse_status=parse_status,
        entry_point_count=entry_point_count,
        artifact_hints=artifact_hints,
    )
    return CodeAnalysis(
        extraction_status=ext.extraction_status,
        extracted_code=extracted,
        code_hash=code_hash,
        parse_status=parse_status,
        entry_point_count=entry_point_count,
        taxonomy_primary=taxonomy,
    )


def analyze_extracted_code(
    extracted_code: Optional[str],
    *,
    entry_point: Optional[str],
) -> CodeAnalysis:
    if extracted_code is None or not extracted_code.strip():
        return CodeAnalysis(
            extraction_status="not_replayed",
            extracted_code=None,
            code_hash=None,
            parse_status="skipped_no_candidate",
            entry_point_count=0,
            taxonomy_primary="no_code_candidate",
        )

    parse_status, entry_point_count = _count_entry_points(
        extracted_code, entry_point or ""
    )
    taxonomy = classify_taxonomy(
        raw_response=None,
        extraction_status="not_replayed",
        extracted_code=extracted_code,
        parse_status=parse_status,
        entry_point_count=entry_point_count,
        check_empty_raw=False,
    )
    return CodeAnalysis(
        extraction_status="not_replayed",
        extracted_code=extracted_code,
        code_hash=sha256_text(extracted_code),
        parse_status=parse_status,
        entry_point_count=entry_point_count,
        taxonomy_primary=taxonomy,
    )


def assess_stage1_eligibility(sample: PilotLoadedSample) -> Tuple[bool, str, Optional[str]]:
    if not sample.task_id or not str(sample.task_id).strip():
        return False, STAGE1_EXCLUDED, "missing_task_id"

    has_raw = sample.raw_response is not None and bool(str(sample.raw_response).strip())
    has_extracted = sample.extracted_code is not None and bool(
        str(sample.extracted_code).strip()
    )

    if has_raw:
        return True, STAGE1_FULL, None
    if has_extracted:
        return True, STAGE1_PARTIAL, None
    return False, STAGE1_EXCLUDED, "missing_raw_response_and_extracted_code"


def _step_guard_hit(step: TraceStep) -> bool:
    return step.enabled and step.changed


def _trace_triggered_rules(trace: TreatmentTrace) -> List[str]:
    triggered = list(trace.rules_triggered)
    if triggered:
        return triggered
    return [step.rule_id for step in trace.steps if _step_guard_hit(step)]


def _apply_repair_path(
    *,
    pair_id: str,
    input_code: Optional[str],
    entry_point: Optional[str],
    repair_path: str,
    skill_id: Optional[str],
) -> RepairOutcome:
    if input_code is None:
        return RepairOutcome(
            code=None,
            code_hash=None,
            extraction_status="empty",
            parse_status="skipped_no_candidate",
            entry_point_count=0,
            taxonomy_primary="no_code_candidate",
            triggered=False,
            triggered_rules=[],
            trace=[],
        )

    traces: List[TreatmentTrace] = []
    code = input_code

    core_result = run_core_adapter(pair_id=pair_id, input_code=code)
    code = core_result.output_code
    traces.append(core_result.trace)

    if repair_path == REPAIR_PATH_TIER1_EXPLORATORY:
        effective_skill = skill_id or ""
        if is_k12_math_domain(effective_skill):
            spec_result = run_spec_adapter(
                pair_id=pair_id,
                skill_id=effective_skill,
                input_code=code,
            )
        else:
            spec_result = run_spec_adapter(
                pair_id=pair_id,
                skill_id="",
                input_code=code,
                domain_applicable=False,
            )
        code = spec_result.output_code
        traces.append(spec_result.trace)

    parse_status, entry_point_count = _count_entry_points(code, entry_point or "")
    code_hash = sha256_text(code) if code else None
    taxonomy = classify_taxonomy(
        raw_response=None,
        extraction_status="extracted",
        extracted_code=code,
        parse_status=parse_status,
        entry_point_count=entry_point_count,
        check_empty_raw=False,
    )

    triggered_rules: List[str] = []
    for trace in traces:
        triggered_rules.extend(_trace_triggered_rules(trace))

    return RepairOutcome(
        code=code,
        code_hash=code_hash,
        extraction_status="extracted",
        parse_status=parse_status,
        entry_point_count=entry_point_count,
        taxonomy_primary=taxonomy,
        triggered=bool(triggered_rules),
        triggered_rules=sorted(set(triggered_rules)),
        trace=[treatment_trace_to_dict(t) for t in traces],
    )


def audit_sample(
    sample: PilotLoadedSample,
    *,
    repair_path: str,
) -> Dict[str, Any]:
    eligible, stage1_mode, exclusion_reason = assess_stage1_eligibility(sample)
    raw_available = sample.raw_response is not None and bool(
        str(sample.raw_response).strip()
    )
    extraction_replay_available = sample.source_fidelity == FIDELITY_RAW_RESPONSE

    if not eligible:
        return {
            "source_id": sample.source_id,
            "source_type": sample.source_type,
            "source_fidelity": sample.source_fidelity,
            "dataset": sample.dataset,
            "model_tag": sample.model_tag,
            "task_id": sample.task_id,
            "treatment": sample.treatment,
            "attempt_kind": sample.attempt_kind,
            "first_attempt_selection_status": sample.first_attempt_selection_status,
            "repair_path": repair_path,
            "repair_path_mapping_status": (
                "provisional"
                if repair_path == REPAIR_PATH_TIER1_EXPLORATORY
                else "stable"
            ),
            "pilot_only": True,
            "confirmatory_eligible": False,
            "raw_response_available": raw_available,
            "extraction_replay_available": extraction_replay_available,
            "stage1_eligible": False,
            "stage1_exclusion_reason": exclusion_reason,
            "stage1_mode": stage1_mode,
            "raw_response_sha256": sample.raw_response_sha256,
            "extraction_status_before": None,
            "extracted_code_before": None,
            "before_sha256": None,
            "parse_status_before": None,
            "entry_point_count_before": None,
            "taxonomy_primary_before": None,
            "triggered": False,
            "triggered_rules": [],
            "changed": False,
            "extraction_status_after": None,
            "extracted_code_after": None,
            "after_sha256": None,
            "parse_status_after": None,
            "entry_point_count_after": None,
            "taxonomy_primary_after": None,
            "trace": [],
        }

    if sample.source_fidelity == FIDELITY_RAW_RESPONSE:
        before = analyze_raw_response(
            sample.raw_response,
            entry_point=sample.entry_point,
        )
        repair_input = before.extracted_code
    else:
        before = analyze_extracted_code(
            sample.extracted_code,
            entry_point=sample.entry_point,
        )
        repair_input = sample.extracted_code

    pair_id = _pair_id_for_sample(sample)
    after = _apply_repair_path(
        pair_id=pair_id,
        input_code=repair_input,
        entry_point=sample.entry_point,
        repair_path=repair_path,
        skill_id=sample.skill_id,
    )

    changed = (
        before.code_hash is not None
        and after.code_hash is not None
        and before.code_hash != after.code_hash
    ) or (
        before.code_hash is None
        and after.code_hash is not None
    )

    return {
        "source_id": sample.source_id,
        "source_type": sample.source_type,
        "source_fidelity": sample.source_fidelity,
        "dataset": sample.dataset,
        "model_tag": sample.model_tag,
        "task_id": sample.task_id,
        "treatment": sample.treatment,
        "attempt_kind": sample.attempt_kind,
        "first_attempt_selection_status": sample.first_attempt_selection_status,
        "repair_path": repair_path,
        "repair_path_mapping_status": (
            "provisional"
            if repair_path == REPAIR_PATH_TIER1_EXPLORATORY
            else "stable"
        ),
        "pilot_only": True,
        "confirmatory_eligible": False,
        "raw_response_available": raw_available,
        "extraction_replay_available": extraction_replay_available,
        "stage1_eligible": True,
        "stage1_exclusion_reason": None,
        "stage1_mode": stage1_mode,
        "raw_response_sha256": sample.raw_response_sha256,
        "extraction_status_before": before.extraction_status,
        "extracted_code_before": before.extracted_code,
        "before_sha256": before.code_hash,
        "parse_status_before": before.parse_status,
        "entry_point_count_before": before.entry_point_count,
        "taxonomy_primary_before": before.taxonomy_primary,
        "triggered": after.triggered,
        "triggered_rules": after.triggered_rules,
        "changed": changed,
        "extraction_status_after": after.extraction_status,
        "extracted_code_after": after.code,
        "after_sha256": after.code_hash,
        "parse_status_after": after.parse_status,
        "entry_point_count_after": after.entry_point_count,
        "taxonomy_primary_after": after.taxonomy_primary,
        "trace": after.trace,
    }


def _transition_count(
    rows: Sequence[Dict[str, Any]],
    *,
    before_field: str,
    after_field: str,
    before_value: Any,
    after_value: Any,
) -> int:
    return sum(
        1
        for row in rows
        if row.get("stage1_eligible")
        and row.get(before_field) == before_value
        and row.get(after_field) == after_value
    )


def build_summary(
    sample_results: Sequence[Dict[str, Any]],
    *,
    source_bundle_id: str,
) -> Dict[str, Any]:
    grouped: Dict[Tuple[str, str, str], List[Dict[str, Any]]] = defaultdict(list)
    for row in sample_results:
        grouped[(source_bundle_id, row["treatment"], row["repair_path"])].append(row)

    by_source_treatment_repair_path: Dict[str, Dict[str, Any]] = {}
    for (bundle_id, treatment, repair_path), rows in sorted(grouped.items()):
        key = f"{bundle_id}__{treatment}__{repair_path}"
        eligible_rows = [r for r in rows if r.get("stage1_eligible")]
        taxonomy_before = Counter(
            r["taxonomy_primary_before"] for r in eligible_rows if r.get("taxonomy_primary_before")
        )
        taxonomy_after = Counter(
            r["taxonomy_primary_after"] for r in eligible_rows if r.get("taxonomy_primary_after")
        )
        rule_trigger_counts: Counter[str] = Counter()
        for row in eligible_rows:
            for rule_id in row.get("triggered_rules") or []:
                rule_trigger_counts[rule_id] += 1

        by_source_treatment_repair_path[key] = {
            "source_id": bundle_id,
            "treatment": treatment,
            "repair_path": repair_path,
            "N_loaded": len(rows),
            "N_stage1_eligible": len(eligible_rows),
            "N_full_stage1": sum(
                1 for r in rows if r.get("stage1_mode") == STAGE1_FULL
            ),
            "N_partial_stage1": sum(
                1 for r in rows if r.get("stage1_mode") == STAGE1_PARTIAL
            ),
            "N_excluded": sum(
                1 for r in rows if r.get("stage1_mode") == STAGE1_EXCLUDED
            ),
            "raw_response_available": sum(
                1 for r in rows if r.get("raw_response_available")
            ),
            "extraction_replay_available": sum(
                1 for r in rows if r.get("extraction_replay_available")
            ),
            "triggered": sum(1 for r in eligible_rows if r.get("triggered")),
            "changed": sum(1 for r in eligible_rows if r.get("changed")),
            "unchanged": sum(1 for r in eligible_rows if not r.get("changed")),
            "parse_fail_to_success": _transition_count(
                eligible_rows,
                before_field="parse_status_before",
                after_field="parse_status_after",
                before_value="failed",
                after_value="success",
            ),
            "parse_success_to_fail": _transition_count(
                eligible_rows,
                before_field="parse_status_before",
                after_field="parse_status_after",
                before_value="success",
                after_value="failed",
            ),
            "entry_point_0_to_1": _transition_count(
                eligible_rows,
                before_field="entry_point_count_before",
                after_field="entry_point_count_after",
                before_value=0,
                after_value=1,
            ),
            "entry_point_1_to_0": _transition_count(
                eligible_rows,
                before_field="entry_point_count_before",
                after_field="entry_point_count_after",
                before_value=1,
                after_value=0,
            ),
            "entry_point_1_to_multiple": sum(
                1
                for r in eligible_rows
                if r.get("entry_point_count_before") == 1
                and (r.get("entry_point_count_after") or 0) > 1
            ),
            "taxonomy_before_counts": dict(sorted(taxonomy_before.items())),
            "taxonomy_after_counts": dict(sorted(taxonomy_after.items())),
            "rule_trigger_counts": dict(sorted(rule_trigger_counts.items())),
        }

    summary = {
        "stage": "pilot_mechanical_repair_stage1",
        "source_bundle_id": source_bundle_id,
        "by_source_treatment_repair_path": by_source_treatment_repair_path,
    }
    for forbidden in _STAGE2_FORBIDDEN_SUMMARY_KEYS:
        if forbidden in summary or any(
            forbidden in block for block in by_source_treatment_repair_path.values()
        ):
            raise PilotAuditError(
                f"summary must not include Stage 2 metric {forbidden!r}"
            )
    return summary


def _write_jsonl(path: pathlib.Path, rows: Sequence[Dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def _write_json(path: pathlib.Path, obj: Dict[str, Any]) -> None:
    path.write_text(
        json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def run_pilot_audit(
    *,
    artifacts_root: pathlib.Path,
    output_dir: pathlib.Path,
    treatments: Sequence[str],
    repair_paths: Sequence[str],
    source_format: str = SOURCE_FORMAT_AUTO,
    source_bundle_id: Optional[str] = None,
    overwrite: bool = False,
) -> Dict[str, Any]:
    if output_dir.exists():
        if any(output_dir.iterdir()):
            if not overwrite:
                raise PilotAuditError(
                    f"output directory already exists and is non-empty: {output_dir}"
                )
    else:
        output_dir.mkdir(parents=True, exist_ok=True)

    treatment_filter = None if treatments == ["all"] else list(treatments)
    samples = load_pilot_samples(
        artifacts_root,
        source_format=source_format,
        treatments=treatment_filter,
    )

    bundle_id = source_bundle_id or artifacts_root.name
    results: List[Dict[str, Any]] = []
    for sample in sorted(samples, key=lambda s: (s.treatment, s.task_id, s.source_id)):
        for repair_path in repair_paths:
            results.append(audit_sample(sample, repair_path=repair_path))

    summary = build_summary(results, source_bundle_id=bundle_id)

    _write_jsonl(output_dir / "sample_results.jsonl", results)
    _write_json(output_dir / "summary.json", summary)

    return {
        "sample_count": len(results),
        "unique_samples": len(samples),
        "output_dir": str(output_dir),
        "summary": summary,
    }


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m agent_tools.finals_rebuild.pilot_audit",
        description="Offline pilot mechanical-repair coverage audit (Stage 1).",
    )
    parser.add_argument("--artifacts-root", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument(
        "--source-format",
        default=SOURCE_FORMAT_AUTO,
        choices=sorted(SUPPORTED_SOURCE_FORMATS),
    )
    parser.add_argument(
        "--treatment",
        dest="treatments",
        action="append",
        required=True,
        help="ab1, ab2g, ab2, all, or unknown (repeatable).",
    )
    parser.add_argument(
        "--repair-path",
        dest="repair_paths",
        action="append",
        required=True,
        help="tier1, tier1_exploratory, or all (repeatable).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow overwriting existing audit output files.",
    )
    return parser


def _expand_cli_selections(values: Sequence[str], resolver) -> List[str]:
    expanded: List[str] = []
    for value in values:
        expanded.extend(resolver(value))
    return sorted(set(expanded))


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    try:
        treatments = _expand_cli_selections(args.treatments, _resolve_treatments)
        repair_paths = _expand_cli_selections(args.repair_paths, _resolve_repair_paths)
        run_pilot_audit(
            artifacts_root=pathlib.Path(args.artifacts_root),
            output_dir=pathlib.Path(args.output_dir),
            treatments=treatments,
            repair_paths=repair_paths,
            source_format=args.source_format,
            overwrite=args.overwrite,
        )
        return 0
    except (PilotAuditError, PilotArtifactLoaderError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
