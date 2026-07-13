"""Read-only, offline integration pilot for real historical generator sources."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from agent_tools.finals_rebuild.generator_evaluator import GeneratorEvaluationResult, evaluate_generator_code


EXPECTED_CATEGORIES = frozenset({"candidate_success", "known_parse_failure", "known_runtime_failure", "legacy_runtime_dependency", "unknown_baseline"})
OBSERVED_CATEGORIES = frozenset({"passed", "parse_failure", "safety_rejected", "load_failure", "entry_point_failure", "runtime_failure", "timeout", "output_failure", "instance_schema_failure", "legacy_runtime_dependency"})


class GeneratorPilotManifestError(ValueError): pass


@dataclass(frozen=True)
class GeneratorPilotCase:
    case_id: str; source_file: str; expected_category: str; curriculum_level: str; domain: str; model: str; ablation: str; notes: str


@dataclass(frozen=True)
class GeneratorPilotResult:
    case: GeneratorPilotCase; source_sha256: str; source_size_bytes: int; evaluation: GeneratorEvaluationResult; observed_category: str; expectation_match: bool


@dataclass(frozen=True)
class GeneratorPilotSummary:
    total: int; passed: int; failed: int; category_counts: tuple[tuple[str, int], ...]; expectation_matches: int; expectation_mismatches: int


def load_generator_pilot_manifest(manifest_path: str | Path, *, repo_root: str | Path) -> tuple[GeneratorPilotCase, ...]:
    root = Path(repo_root).resolve(); path = Path(manifest_path)
    try: data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc: raise GeneratorPilotManifestError(str(exc)) from exc
    if not isinstance(data, list): raise GeneratorPilotManifestError("manifest must be a list")
    cases=[]; seen=set(); fields={"case_id","source_file","expected_category","curriculum_level","domain","model","ablation","notes"}
    for item in data:
        if not isinstance(item, dict) or set(item) != fields: raise GeneratorPilotManifestError("invalid manifest record fields")
        if not all(isinstance(item[key], str) and item[key].strip() for key in fields): raise GeneratorPilotManifestError("manifest metadata must be non-empty strings")
        if item["case_id"] in seen: raise GeneratorPilotManifestError("duplicate case_id")
        if item["expected_category"] not in EXPECTED_CATEGORIES: raise GeneratorPilotManifestError("invalid expected_category")
        relative=Path(item["source_file"])
        if relative.is_absolute() or ".." in relative.parts or relative.suffix != ".py": raise GeneratorPilotManifestError("source_file must be a safe relative .py path")
        resolved=(root / relative).resolve()
        if root not in resolved.parents or not resolved.is_file(): raise GeneratorPilotManifestError("source_file is outside repo_root or missing")
        seen.add(item["case_id"]); cases.append(GeneratorPilotCase(**item))
    return tuple(cases)


def _observed(evaluation: GeneratorEvaluationResult) -> str:
    if evaluation.success: return "passed"
    if evaluation.failure_stage == "parse": return "parse_failure"
    if evaluation.failure_stage == "safety": return "safety_rejected"
    if evaluation.failure_stage == "load":
        text=f"{evaluation.error_type} {evaluation.error_message}".lower()
        return "legacy_runtime_dependency" if any(word in text for word in ("helper", "module", "global")) else "load_failure"
    if evaluation.failure_stage == "entry_point": return "entry_point_failure"
    if evaluation.failure_stage == "execution": return "timeout" if evaluation.status == "timeout" else "runtime_failure"
    if evaluation.failure_stage == "output": return "output_failure"
    if evaluation.failure_stage == "instance_schema": return "instance_schema_failure"
    return "runtime_failure"


def _matches(expected: str, observed: str) -> bool:
    return expected == "unknown_baseline" or (expected == "candidate_success" and observed == "passed") or (expected == "known_parse_failure" and observed == "parse_failure") or (expected == "known_runtime_failure" and observed in {"runtime_failure", "timeout"}) or (expected == "legacy_runtime_dependency" and observed == "legacy_runtime_dependency")


def run_generator_pilot_case(case: GeneratorPilotCase, *, repo_root: str | Path, timeout_seconds: float = 2.0) -> GeneratorPilotResult:
    root=Path(repo_root).resolve(); relative=Path(case.source_file); source_path=(root / relative).resolve()
    if relative.is_absolute() or ".." in relative.parts or source_path.suffix != ".py" or root not in source_path.parents:
        raise GeneratorPilotManifestError("source_file is outside repo_root")
    source=source_path.read_bytes()
    evaluation=evaluate_generator_code(source.decode("utf-8"), timeout_seconds=timeout_seconds)
    observed=_observed(evaluation)
    return GeneratorPilotResult(case, hashlib.sha256(source).hexdigest(), len(source), evaluation, observed, _matches(case.expected_category, observed))


def run_generator_pilot(cases: Sequence[GeneratorPilotCase], *, repo_root: str | Path, timeout_seconds: float = 2.0) -> tuple[GeneratorPilotResult, ...]:
    return tuple(run_generator_pilot_case(case, repo_root=repo_root, timeout_seconds=timeout_seconds) for case in cases)


def summarize_generator_pilot(results: Sequence[GeneratorPilotResult]) -> GeneratorPilotSummary:
    counts={category: 0 for category in sorted(OBSERVED_CATEGORIES)}
    for result in results: counts[result.observed_category] += 1
    matches=sum(result.expectation_match for result in results)
    return GeneratorPilotSummary(len(results), counts["passed"], len(results)-counts["passed"], tuple(counts.items()), matches, len(results)-matches)
