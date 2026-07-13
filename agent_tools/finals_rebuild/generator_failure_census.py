"""Raw generator failure census helpers."""
from __future__ import annotations
import argparse
import hashlib
import json
import random
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
from agent_tools.finals_rebuild.generator_evaluator import GeneratorEvaluationResult, evaluate_generator_code
from agent_tools.finals_rebuild.generator_integration_pilot import _observed

CATEGORIES = ("passed", "parse_failure", "safety_rejected", "load_failure", "entry_point_failure", "runtime_failure", "timeout", "output_failure", "instance_schema_failure", "legacy_runtime_dependency")
REQUIRED_DOMAINS = ("applications_of_derivatives", "four_arithmetic_operations_of_integers", "four_arithmetic_operations_of_numbers")
class GeneratorFailureCensusManifestError(ValueError): pass
@dataclass(frozen=True)
class GeneratorSource:
    source_file: str; domain: str; model: str; ablation: str
@dataclass(frozen=True)
class GeneratorFailureCensusCase:
    case_id: str; source_file: str; source_group: str; curriculum_level: str; domain: str; model: str; ablation: str; selection_seed: int
@dataclass(frozen=True)
class GeneratorFailureCensusRecord:
    case: GeneratorFailureCensusCase; source_sha256: str; source_size_bytes: int; evaluation: GeneratorEvaluationResult; observed_category: str; repairability_class: str; repairability_reason: str
@dataclass(frozen=True)
class GeneratorFailureCensusSummary:
    total: int; passed: int; failed: int; category_counts: tuple[tuple[str,int],...]; tier1_candidates: int; not_tier1: int; unknown_repairability: int; model_counts: tuple[tuple[str,int],...]; ablation_counts: tuple[tuple[str,int],...]; domain_counts: tuple[tuple[str,int],...]
def parse_generator_source_metadata(source_path: Path, results_root: Path) -> GeneratorSource:
    relative=source_path.relative_to(results_root).as_posix()
    lowered=relative.lower()
    domain=next((d for d in REQUIRED_DOMAINS if d.replace("_","") in re.sub(r"[^a-z]","",lowered)),None)
    if domain is None: raise GeneratorFailureCensusManifestError(f"unknown domain: {relative}")
    stem=source_path.stem; ablation=(re.search(r"_(Ab\d+)_",stem) or re.search(r"_(Ab\d+)$",stem))
    model_match=re.search(r"_(.+?)_(Ab\d+)_run\d+$",stem)
    if not ablation or not model_match: raise GeneratorFailureCensusManifestError(f"unparseable metadata: {relative}")
    return GeneratorSource(relative,domain,model_match.group(1),ablation.group(1))
def discover_generator_sources(results_root: Path) -> list[GeneratorSource]:
    if not results_root.is_dir(): raise GeneratorFailureCensusManifestError(f"missing results root: {results_root}")
    sources=[]
    for path in sorted(results_root.rglob("*.py")):
        if path.name == "__init__.py" or any(x in path.name.lower() for x in ("manifest","report","cache","temp")): continue
        try: sources.append(parse_generator_source_metadata(path,results_root))
        except GeneratorFailureCensusManifestError:
            continue
    return sources
def stratified_sample_generator_sources(sources: Sequence[GeneratorSource], required_domains: Sequence[str], per_domain: int, seed: int) -> list[GeneratorSource]:
    selected=[]
    for domain in required_domains:
        pool=sorted((s for s in sources if s.domain == domain),key=lambda s:s.source_file)
        if len(pool) < per_domain: raise GeneratorFailureCensusManifestError(f"domain={domain} available={len(pool)} required={per_domain}")
        rng=random.Random(f"{seed}:{domain}"); selected.extend(rng.sample(pool,per_domain))
    return selected
def build_generator_failure_census_manifest(results_root: Path, required_domains: Sequence[str]=REQUIRED_DOMAINS, per_domain: int=10, seed: int=20260713) -> dict[str,Any]:
    sources=discover_generator_sources(results_root); selected=stratified_sample_generator_sources(sources,required_domains,per_domain,seed)
    cases=[{"case_id":f"census_{i:03d}","source_file":f"experiments/results/{s.source_file}","source_group":"experiments_results","curriculum_level":"unknown","domain":s.domain,"model":s.model,"ablation":s.ablation,"selection_seed":seed} for i,s in enumerate(selected,1)]
    return {"census_type":"cross_domain_calibration_census","sampling_validity":"valid_stratified_sampling","selection_seed":seed,"target_per_domain":per_domain,"selected_total":len(cases),"required_domains":list(required_domains),"eligible_counts_by_domain":dict(sorted(Counter(s.domain for s in sources).items())),"selected_counts_by_domain":dict(sorted(Counter(s.domain for s in selected).items())),"cases":cases}
def write_generator_failure_census_manifest(manifest: Mapping[str,Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True,exist_ok=True); output_path.write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
def run_cross_domain_calibration_census(manifest_path: Path, repo_root: Path, output_path: Path, report_path: Path) -> dict[str,Any]:
    cases=load_generator_failure_census_manifest(manifest_path,repo_root=repo_root)
    records=run_generator_failure_census(cases,repo_root=repo_root)
    rows=[]
    for record in records:
        evaluation=record.evaluation; category=record.observed_category
        outcome={"passed":"passed","parse_failure":"parse_failure","safety_rejected":"safety_rejected"}.get(category,"execution_failure" if category in {"runtime_failure","timeout","load_failure","entry_point_failure"} else "other_failure")
        detail="catastrophic_truncation" if category=="parse_failure" and record.repairability_reason=="non_repairable_deterministically" else (evaluation.error_type or "")
        rows.append({"case_id":record.case.case_id,"source_file":record.case.source_file,"domain":record.case.domain,"model":record.case.model,"ablation":record.case.ablation,"parse_status":evaluation.parse_status,"safety_status":evaluation.safety_status,"execution_status":evaluation.execution_status,"question_evaluable":evaluation.question_text_status=="passed","answer_correct":None,"raw_outcome":outcome,"corrected_outcome":outcome,"failure_category":outcome,"failure_detail":detail,"exception_type":evaluation.error_type,"exception_message":evaluation.error_message,"execution_stage":evaluation.failure_stage,"tier1_candidate":False,"safety_rule":evaluation.safety_rule,"safety_detail":evaluation.safety_detail,"code_origin":evaluation.code_origin,"safety_attribution":evaluation.safety_attribution})
    report={"census_type":"cross_domain_calibration","total":len(rows),"outcomes":dict(Counter(r["failure_category"] for r in rows)),"by_domain":{d:dict(Counter(r["failure_category"] for r in rows if r["domain"]==d)) for d in REQUIRED_DOMAINS},"by_model":{m:{"n":sum(r["model"]==m for r in rows),"passed":sum(r["model"]==m and r["failure_category"]=="passed" for r in rows)} for m in sorted({r["model"] for r in rows})},"by_ablation":{a:dict(Counter(r["failure_category"] for r in rows if r["ablation"]==a)) for a in sorted({r["ablation"] for r in rows})},"preliminary_tier1_candidates":sum(r["failure_category"]=="parse_failure" for r in rows),"true_tier1_candidates":0,"proceed_to_healer_pilot":False}
    output_path.parent.mkdir(parents=True,exist_ok=True); output_path.write_text(json.dumps(rows,indent=2,sort_keys=True)+"\n",encoding="utf-8"); report_path.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return report
def load_generator_failure_census_manifest(manifest_path: str | Path, *, repo_root: str | Path) -> tuple[GeneratorFailureCensusCase,...]:
    try: data=json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as exc: raise GeneratorFailureCensusManifestError(str(exc)) from exc
    if isinstance(data, dict):
        if data.get("sampling_validity") != "valid_stratified_sampling" or data.get("census_type") != "cross_domain_calibration_census": raise GeneratorFailureCensusManifestError("invalid calibration metadata")
        data = data.get("cases")
    if not isinstance(data,list) or not 30 <= len(data) <= 50: raise GeneratorFailureCensusManifestError("manifest must contain 30 to 50 cases")
    root=Path(repo_root).resolve(); cases=[]
    for item in data:
        try: case=GeneratorFailureCensusCase(**item)
        except (TypeError, AttributeError) as exc: raise GeneratorFailureCensusManifestError("invalid case fields") from exc
        path=Path(case.source_file); resolved=(root/path).resolve()
        if not case.case_id or not case.source_file or case.selection_seed != 20260713 or path.suffix != ".py" or path.is_absolute() or ".." in path.parts or root not in resolved.parents or not resolved.is_file(): raise GeneratorFailureCensusManifestError("invalid case")
        cases.append(case)
    if len({c.case_id for c in cases}) != len(cases) or len({c.source_file for c in cases}) != len(cases): raise GeneratorFailureCensusManifestError("case ids and source files must be unique")
    counts = Counter(c.domain for c in cases)
    if any(counts[d] != 10 for d in REQUIRED_DOMAINS): raise GeneratorFailureCensusManifestError(f"required domains need 10 cases; counts={dict(counts)}")
    return tuple(cases)
def _repairability(category, evaluation, source):
    if category == "passed": return "not_tier1","already_executable"
    if category == "safety_rejected": return "not_tier1","unsafe_code"
    if category == "legacy_runtime_dependency": return "not_tier1","legacy_dependency"
    if category in {"output_failure","instance_schema_failure"}: return "not_tier1","output_contract_failure"
    if category == "runtime_failure": return "not_tier1","runtime_semantic_failure"
    if category == "parse_failure": return "not_tier1","non_repairable_deterministically"
    if category == "parse_failure" and source.rstrip().endswith("def _"): return "not_tier1","non_repairable_deterministically"
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
def main(argv: Sequence[str] | None=None) -> int:
    parser=argparse.ArgumentParser()
    commands=parser.add_subparsers(dest="command",required=True)
    build=commands.add_parser("build-manifest")
    build.add_argument("--results-root",type=Path,required=True); build.add_argument("--output",type=Path,required=True)
    build.add_argument("--domain",action="append",required=True); build.add_argument("--per-domain",type=int,default=10)
    build.add_argument("--seed",type=int,default=20260713); build.add_argument("--overwrite",action="store_true")
    run=commands.add_parser("run-census")
    run.add_argument("--manifest",type=Path,required=True); run.add_argument("--repo-root",type=Path,default=Path("."))
    run.add_argument("--output",type=Path,required=True); run.add_argument("--report",type=Path,required=True)
    args=parser.parse_args(argv)
    if args.command == "build-manifest":
        if args.output.exists() and not args.overwrite: parser.error("output exists; pass --overwrite")
        write_generator_failure_census_manifest(build_generator_failure_census_manifest(args.results_root,args.domain,args.per_domain,args.seed),args.output)
    else: run_cross_domain_calibration_census(args.manifest,args.repo_root,args.output,args.report)
    return 0
if __name__ == "__main__": raise SystemExit(main())
