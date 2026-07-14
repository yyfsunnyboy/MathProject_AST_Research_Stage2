"""Current Math Track generation-run manifest and dry-run planner."""
from __future__ import annotations
import argparse, ast, hashlib, json, time, urllib.error, urllib.request
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Sequence

ALLOWED_MODELS={"qwen3:8b":{"model_digest":"500a1f067a9f","architecture":"qwen3","parameters":"8.2B","quantization":"Q4_K_M"},"qwen3:4b-instruct-2507-q4_K_M":{"model_digest":"0edcdef34593","architecture":"qwen3","parameters":"4.0B","quantization":"Q4_K_M"}}
ALLOWED_CONDITIONS={"Ab1":"math_ab1_minimal_domain_prompt","Ab2g":"math_ab2g_generic_scaffold"}
REQUIRED_KEYS=("task_id","domain","skill_id","task_description","required_entry_point","required_output_keys","seed")
class MathGenerationManifestError(ValueError): pass
class OllamaHTTPError(RuntimeError):
    """HTTP failure with the response body retained for smoke-run diagnostics."""
    def __init__(self, status: int, body: str):
        self.status = status
        self.body = body
        super().__init__(f"Ollama HTTP {status}: {body}")
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
def call_ollama_chat(url, payload, timeout):
    request=urllib.request.Request(url.rstrip("/")+"/api/chat",data=json.dumps(payload).encode(),headers={"Content-Type":"application/json"})
    for attempt in range(2):
        try:
            with urllib.request.urlopen(request,timeout=timeout) as response: return json.loads(response.read())
        except urllib.error.HTTPError as exc:
            body=exc.read().decode("utf-8", errors="replace")
            raise OllamaHTTPError(exc.code, body) from exc
        except (urllib.error.URLError, TimeoutError):
            if attempt: raise
def _extract(text):
    fence=chr(96)*3
    if text.strip().startswith(fence) and text.strip().endswith(fence):
        return "\n".join(text.strip().splitlines()[1:-1])
    return text
def generate_live(tasks, *, output_root, run_id, paired_run_id, model, conditions, seed, ollama_url, cold_start_or_warm_run, temperature=0.0, top_k=20, top_p=.8, repeat_penalty=1.0, timeout=300, client=call_ollama_chat):
    if model not in ALLOWED_MODELS: raise MathGenerationManifestError("unsupported model")
    root=Path(output_root)/run_id
    if root.exists(): raise MathGenerationManifestError("output directory already exists")
    root.mkdir(parents=True); (root/"raw_responses").mkdir(); (root/"model_sources").mkdir(); rows=[]
    for i,task in enumerate(tasks):
        for condition in conditions:
            prompt=build_math_ab1_prompt(task) if condition=="Ab1" else build_math_ab2g_prompt(task); started=time.monotonic()
            payload={"model":model,"messages":[{"role":"user","content":prompt}],"stream":False,"options":{"temperature":temperature,"top_k":top_k,"top_p":top_p,"repeat_penalty":repeat_penalty,"seed":seed}}
            base={"run_id":run_id,"paired_run_id":paired_run_id,"task_id":task.task_id,"domain":task.domain,"skill_id":task.skill_id,"model_tag":model,**ALLOWED_MODELS[model],"prompt_condition":ALLOWED_CONDITIONS[condition],"prompt_sha256":_hash(prompt),"seed":seed,"cold_start_or_warm_run":cold_start_or_warm_run,"repair_cpu_seconds":0.0}
            try:
                raw=client(ollama_url,payload,timeout); content=raw.get("message",{}).get("content")
                if not isinstance(content,str): raise MathGenerationManifestError("missing message.content")
                aid=f"{i:02d}_{condition.lower()}"; rp=root/"raw_responses"/f"{aid}.json"; sp=root/"model_sources"/f"{aid}.py"; rp.write_text(json.dumps(raw,indent=2,sort_keys=True)+"\n",encoding="utf8"); source=_extract(content); sp.write_text(source,encoding="utf8")
                try: ast.parse(source); parsed=True; error=None
                except SyntaxError as exc: parsed=False; error=str(exc)
                row=base|{"status":"generated","raw_response_path":str(rp),"model_source_path":str(sp),"contains_markdown_fence_raw":chr(96)*3 in content,"contains_markdown_fence_model_source":chr(96)*3 in source,"ast_parse_success":parsed,"parse_error":error,"prompt_eval_count":raw.get("prompt_eval_count"),"eval_count":raw.get("eval_count"),"total_token_count":(raw.get("prompt_eval_count") or 0)+(raw.get("eval_count") or 0),"wall_clock_seconds":time.monotonic()-started}
            except Exception as exc: row=base|{"status":"failed","failure_stage":"generation","exception_type":type(exc).__name__,"exception_message":str(exc),"retry_count":1 if isinstance(exc,(TimeoutError,urllib.error.URLError)) else 0,"raw_response_path":None,"model_source_path":None,"wall_clock_seconds":time.monotonic()-started}
            rows.append(row)
    (root/"attempts.jsonl").write_text("\n".join(json.dumps(x,sort_keys=True) for x in rows)+"\n",encoding="utf8"); return {"output":str(root),"attempts":rows}
def build_live_smoke_summary(paired_run_id, run_dirs):
    expected={(model,condition) for model in ALLOWED_MODELS for condition in ALLOWED_CONDITIONS}
    records=[]
    for directory in run_dirs:
        path=Path(directory)/"attempts.jsonl"
        if path.is_file():
            records.extend(json.loads(line) for line in path.read_text(encoding="utf8").splitlines() if line.strip())
    records=[r for r in records if r.get("paired_run_id")==paired_run_id]
    seen=set()
    for record in records:
        cell=(record.get("model_tag"),next((k for k,v in ALLOWED_CONDITIONS.items() if v==record.get("prompt_condition")),None))
        if cell in seen: raise MathGenerationManifestError(f"duplicate smoke cell: {cell}")
        seen.add(cell)
    missing=[{"model_tag":m,"condition":c} for m,c in sorted(expected-seen)]
    completed=[r for r in records if r.get("status")!="failed"]
    return {"paired_run_id":paired_run_id,"expected_attempts":4,"completed_attempts":len(completed),"failed_attempts":len(records)-len(completed),"missing_attempts":missing,"task_ids":sorted({r.get("task_id") for r in records}),"models":sorted({r.get("model_tag") for r in records}),"conditions":sorted({r.get("prompt_condition") for r in records}),"per_attempt":records}
def write_live_smoke_summary(summary, output_path):
    Path(output_path).parent.mkdir(parents=True,exist_ok=True); Path(output_path).write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf8")
def main(argv:Sequence[str]|None=None)->int:
    parser=argparse.ArgumentParser(); sub=parser.add_subparsers(dest="command",required=True)
    summary=sub.add_parser("summarize-smoke"); summary.add_argument("--paired-run-id",required=True); summary.add_argument("--run-dir",action="append",required=True); summary.add_argument("--output",required=True)
    for name in ("validate-manifest","dry-run","generate"):
        p=sub.add_parser(name); p.add_argument("--task-manifest",required=True)
        if name!="validate-manifest": p.add_argument("--output-root",required=True); p.add_argument("--run-id",required=True); p.add_argument("--paired-run-id",required=True); p.add_argument("--model",required=True); p.add_argument("--condition",action="append",required=True); p.add_argument("--seed",type=int,required=True); p.add_argument("--cold-start-or-warm-run",choices=("cold_start","warm_run"),required=True); p.add_argument("--ollama-url",default="http://localhost:11434"); p.add_argument("--temperature",type=float,default=0.0); p.add_argument("--top-k",type=int,default=20); p.add_argument("--top-p",type=float,default=.8); p.add_argument("--repeat-penalty",type=float,default=1.0); p.add_argument("--timeout",type=int,default=300)
    args=parser.parse_args(argv)
    if args.command=="summarize-smoke": write_live_smoke_summary(build_live_smoke_summary(args.paired_run_id,args.run_dir),args.output); return 0
    tasks=load_math_tasks(args.task_manifest)
    if args.command=="validate-manifest": print(len(tasks)); return 0
    if args.command=="generate": generate_live(tasks,output_root=args.output_root,run_id=args.run_id,paired_run_id=args.paired_run_id,model=args.model,conditions=args.condition,seed=args.seed,cold_start_or_warm_run=args.cold_start_or_warm_run,ollama_url=args.ollama_url,temperature=args.temperature,top_k=args.top_k,top_p=args.top_p,repeat_penalty=args.repeat_penalty,timeout=args.timeout)
    else: dry_run(tasks,output_root=args.output_root,run_id=args.run_id,paired_run_id=args.paired_run_id,model=args.model,conditions=args.condition,seed=args.seed)
    return 0
if __name__=="__main__": raise SystemExit(main())
