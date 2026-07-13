"""Current Math Track generation-run manifest and dry-run planner."""
from __future__ import annotations
import argparse, hashlib, json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Sequence

ALLOWED_MODELS={"qwen3:8b":{"model_digest":None,"architecture":"qwen3","parameters":"8B","quantization":None},"qwen3:4b-instruct-2507-q4_K_M":{"model_digest":"0edcdef34593","architecture":"qwen3","parameters":"4.0B","quantization":"Q4_K_M"}}
ALLOWED_CONDITIONS={"Ab1":"math_ab1_minimal_domain_prompt","Ab2g":"math_ab2g_generic_scaffold"}
REQUIRED_KEYS=("task_id","domain","skill_id","task_description","required_entry_point","required_output_keys","seed")
class MathGenerationManifestError(ValueError): pass
@dataclass(frozen=True)
class MathGenerationTask:
    task_id:str; domain:str; skill_id:str; task_description:str; required_entry_point:str; required_output_keys:tuple[str,...]; seed:int
def load_math_tasks(path: str|Path)->tuple[MathGenerationTask,...]:
    tasks=[]
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip(): continue
        value=json.loads(line)
        if not isinstance(value,dict) or set(value)!=set(REQUIRED_KEYS): raise MathGenerationManifestError("invalid task schema")
        task=MathGenerationTask(**{**value,"required_output_keys":tuple(value["required_output_keys"])})
        if not task.task_id or task.required_entry_point!="generate" or tuple(task.required_output_keys)!=("question_text","correct_answer"): raise MathGenerationManifestError("invalid Math task contract")
        tasks.append(task)
    if not tasks or len({x.task_id for x in tasks})!=len(tasks): raise MathGenerationManifestError("tasks must be non-empty with unique task_id")
    return tuple(tasks)
def build_math_ab1_prompt(task: MathGenerationTask)->str:
    return f"Write only Python source for {task.domain}. {task.task_description}\nImplement def generate(level=1, **kwargs) returning a dict with question_text and correct_answer. Do not use input(), files, network, subprocess, Markdown fences, or explanations."
def build_math_ab2g_prompt(task: MathGenerationTask)->str:
    return build_math_ab1_prompt(task)+"\n\nGeneric Safety-and-Format Scaffold: preserve generate(); be deterministic under the supplied seed when applicable; use no external libraries; do not include domain-specific solution hints, injected utilities, or Healer instructions."
def _hash(text:str)->str: return hashlib.sha256(text.encode()).hexdigest()
def dry_run(tasks: Sequence[MathGenerationTask], *, output_root: str|Path, run_id:str, paired_run_id:str, model:str, conditions:Sequence[str], seed:int)->dict[str,Any]:
    if model not in ALLOWED_MODELS: raise MathGenerationManifestError("unsupported model")
    if any(c not in ALLOWED_CONDITIONS for c in conditions): raise MathGenerationManifestError("unsupported condition")
    root=Path(output_root)/run_id
    if root.exists(): raise MathGenerationManifestError("output directory already exists")
    attempts=[]
    for task in tasks:
        for condition in conditions:
            prompt=build_math_ab1_prompt(task) if condition=="Ab1" else build_math_ab2g_prompt(task)
            attempts.append({"run_id":run_id,"paired_run_id":paired_run_id,"task_id":task.task_id,"domain":task.domain,"skill_id":task.skill_id,"model_tag":model,**ALLOWED_MODELS[model],"runtime":"ollama","runtime_version":None,"generation_timestamp":None,"prompt_condition":ALLOWED_CONDITIONS[condition],"prompt_sha256":_hash(prompt),"seed":seed,"source_commit":None,"status":"dry_run","raw_response_path":None,"raw_response_sha256":None,"model_source_path":None,"model_source_sha256":None,"source_with_injected_utils":None,"prompt_eval_count":None,"eval_count":None,"total_token_count":None,"total_duration":None,"load_duration":None,"prompt_eval_duration":None,"eval_duration":None,"wall_clock_seconds":None,"repair_cpu_seconds":0.0,"cold_start_or_warm_run":None,"hardware":None})
    root.mkdir(parents=True)
    (root/"run_manifest.json").write_text(json.dumps({"run_id":run_id,"paired_run_id":paired_run_id,"model":model,"conditions":list(conditions),"task_count":len(tasks),"http_calls":0},indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (root/"attempts.jsonl").write_text("\n".join(json.dumps(a,sort_keys=True) for a in attempts)+"\n",encoding="utf-8")
    (root/"raw_responses").mkdir(); (root/"model_sources").mkdir()
    return {"output":str(root),"attempts":attempts,"http_calls":0}
def main(argv:Sequence[str]|None=None)->int:
    parser=argparse.ArgumentParser(); sub=parser.add_subparsers(dest="command",required=True)
    for name in ("validate-manifest","dry-run","generate"):
        p=sub.add_parser(name); p.add_argument("--task-manifest",required=True)
        if name!="validate-manifest": p.add_argument("--output-root",required=True); p.add_argument("--run-id",required=True); p.add_argument("--paired-run-id",required=True); p.add_argument("--model",required=True); p.add_argument("--condition",action="append",required=True); p.add_argument("--seed",type=int,required=True)
    args=parser.parse_args(argv); tasks=load_math_tasks(args.task_manifest)
    if args.command=="validate-manifest": print(len(tasks)); return 0
    if args.command=="generate": parser.error("generate is intentionally disabled for Phase 1")
    dry_run(tasks,output_root=args.output_root,run_id=args.run_id,paired_run_id=args.paired_run_id,model=args.model,conditions=args.condition,seed=args.seed); return 0
if __name__=="__main__": raise SystemExit(main())
