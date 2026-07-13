"""Raw generator failure census helpers."""
from __future__ import annotations
import hashlib
import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence
from agent_tools.finals_rebuild.generator_evaluator import GeneratorEvaluationResult, evaluate_generator_code
from agent_tools.finals_rebuild.generator_integration_pilot import _observed

CATEGORIES = ("passed", "parse_failure", "safety_rejected", "load_failure", "entry_point_failure", "runtime_failure", "timeout", "output_failure", "instance_schema_failure", "legacy_runtime_dependency")
class GeneratorFailureCensusManifestError(ValueError): pass
@dataclass(frozen=True)
class GeneratorFailureCensusCase:
    case_id: str; source_file: str; source_group: str; curriculum_level: str; domain: str; model: str; ablation: str; selection_seed: int
@dataclass(frozen=True)
class GeneratorFailureCensusRecord:
    case: GeneratorFailureCensusCase; source_sha256: str; source_size_bytes: int; evaluation: GeneratorEvaluationResult; observed_category: str; repairability_class: str; repairability_reason: str
@dataclass(frozen=True)
class GeneratorFailureCensusSummary:
    total: int; passed: int; failed: int; category_counts: tuple[tuple[str,int],...]; tier1_candidates: int; not_tier1: int; unknown_repairability: int; model_counts: tuple[tuple[str,int],...]; ablation_counts: tuple[tuple[str,int],...]; domain_counts: tuple[tuple[str,int],...]
def load_generator_failure_census_manifest(manifest_path: str | Path, *, repo_root: str | Path) -> tuple[GeneratorFailureCensusCase,...]:
    try: data=json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as exc: raise GeneratorFailureCensusManifestError(str(exc)) from exc
    if not isinstance(data,list) or not 30 <= len(data) <= 50: raise GeneratorFailureCensusManifestError("manifest must contain 30 to 50 cases")
    root=Path(repo_root).resolve(); cases=[]
    for item in data:
        try: case=GeneratorFailureCensusCase(**item)
        except (TypeError, AttributeError) as exc: raise GeneratorFailureCensusManifestError("invalid case fields") from exc
        path=Path(case.source_file); resolved=(root/path).resolve()
        if not case.case_id or not case.source_file or case.selection_seed != 20260713 or path.suffix != ".py" or path.is_absolute() or ".." in path.parts or root not in resolved.parents or not resolved.is_file(): raise GeneratorFailureCensusManifestError("invalid case")
        cases.append(case)
    if len({c.case_id for c in cases}) != len(cases) or len({c.source_file for c in cases}) != len(cases): raise GeneratorFailureCensusManifestError("case ids and source files must be unique")
    return tuple(cases)
def _repairability(category, evaluation, source):
    if category == "passed": return "not_tier1","already_executable"
    if category == "safety_rejected": return "not_tier1","unsafe_code"
    if category == "legacy_runtime_dependency": return "not_tier1","legacy_dependency"
    if category in {"output_failure","instance_schema_failure"}: return "not_tier1","output_contract_failure"
    if category == "runtime_failure": return "not_tier1","runtime_semantic_failure"
    if category == "parse_failure" and any(x in (source+" "+(evaluation.error_message or "")).lower() for x in ("```","markdown","cleanup")): return "tier1_candidate","markdown_fence_candidate"
    return "unknown","insufficient_evidence"
def run_generator_failure_census_case(case, *, repo_root, timeout_seconds=2.0):
    raw=(Path(repo_root)/case.source_file).read_bytes(); source=raw.decode("utf-8"); evaluation=evaluate_generator_code(source,level=1,timeout_seconds=timeout_seconds); category=_observed(evaluation); klass,reason=_repairability(category,evaluation,source)
    return GeneratorFailureCensusRecord(case,hashlib.sha256(raw).hexdigest(),len(raw),evaluation,category,klass,reason)
def run_generator_failure_census(cases: Sequence[GeneratorFailureCensusCase], *, repo_root, timeout_seconds=2.0):
    return tuple(run_generator_failure_census_case(c,repo_root=repo_root,timeout_seconds=timeout_seconds) for c in cases)
def summarize_generator_failure_census(records):
    categories=Counter(r.observed_category for r in records)
    return GeneratorFailureCensusSummary(len(records),categories["passed"],len(records)-categories["passed"],tuple((x,categories[x]) for x in CATEGORIES),sum(r.repairability_class=="tier1_candidate" for r in records),sum(r.repairability_class=="not_tier1" for r in records),sum(r.repairability_class=="unknown" for r in records),tuple(sorted(Counter(r.case.model for r in records).items())),tuple(sorted(Counter(r.case.ablation for r in records).items())),tuple(sorted(Counter(r.case.domain for r in records).items())))
def write_generator_failure_census_jsonl(records, output_path):
    rows=[]
    for r in records:
        e=r.evaluation; rows.append(json.dumps(asdict(r.case)|{"source_sha256":r.source_sha256,"source_size_bytes":r.source_size_bytes,"status":e.status,"success":e.success,"failure_stage":e.failure_stage,"error_type":e.error_type,"observed_category":r.observed_category,"repairability_class":r.repairability_class,"repairability_reason":r.repairability_reason},sort_keys=True))
    Path(output_path).write_text("\n".join(rows)+"\n",encoding="utf-8")
def write_generator_failure_census_summary(summary, output_path):
    data=asdict(summary)
    for key in ("category_counts","model_counts","ablation_counts","domain_counts"): data[key]=dict(data[key])
    Path(output_path).write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf-8")
