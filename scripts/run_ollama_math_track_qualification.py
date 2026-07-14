"""Safe-by-default Ollama qualification runner for the CE115 math track."""
from __future__ import annotations
import argparse, hashlib, json, os, sys, time, urllib.request
from pathlib import Path
from typing import Any, Callable
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from scripts import run_gemini_ab2g_math_core_qualification as base
from agent_tools.finals_rebuild.ab2d_local_prompt import assemble_ab2d_local_prompt, assemble_ab2g_math_core_prompt, measure_prompt_size
from agent_tools.finals_rebuild.math_answer_contracts import render_answer_contract
from agent_tools.finals_rebuild.math_task_sampler import sample_task_parameters
from agent_tools.finals_rebuild.math_boundary_pilot import classify_response
PROVENANCE={"qwen3:4b-instruct-2507-q4_K_M":{"digest":"0edcdef34593","parameters":"4.0B","quantization":"Q4_K_M"},"qwen3:8b":{"digest":"500a1f067a9f","parameters":"8.2B","quantization":"Q4_K_M","architecture":"qwen3","context_length":40960,"embedding_length":4096}}
CONDITIONS=("ab1","ab2g_math_core","ab2d_local")
def _prompt(task, condition):
 p=sample_task_parameters(task,base.SEED)["oracle_payload"]; c=render_answer_contract(task,p)
 if condition=="ab1": text=c.strip()+"\n\n## Frozen parameters\n"+json.dumps(p,sort_keys=True)+"\n"
 elif condition=="ab2g_math_core": text=assemble_ab2g_math_core_prompt(c,p)
 else: text=assemble_ab2d_local_prompt(task["skill_id"],c,p)
 return p,text
def records(model,condition,family=None):
 if model not in PROVENANCE: raise ValueError("unverified model tag")
 rows=[]
 for task in base._tasks(family):
  payload,prompt=_prompt(task,condition); rows.append({"model_tag":model,"model_digest":PROVENANCE[model]["digest"],"parameters":PROVENANCE[model]["parameters"],"quantization":PROVENANCE[model]["quantization"],"runtime":"Ollama","runtime_version":"0.31.2","prompt_condition":condition,"task_family":task["skill_id"],"task_id":task["task_id"],"task_parameters":payload,"final_prompt":prompt,"prompt_size":measure_prompt_size(prompt),"prompt_hash":hashlib.sha256(prompt.encode()).hexdigest(),"attempt_index":0,"request_count":1,"retry_count":0,"healer_enabled":False,"raw_first_attempt_output":None,"candidate_extracted":None,"evaluable":False,"oracle_pass":False,"failure_category":None,"failure_detail":None})
 return rows
def _append(path,row):
 with path.open("a",encoding="utf-8") as h: h.write(json.dumps(row,ensure_ascii=False)+"\n");h.flush();os.fsync(h.fileno())
def _call(prompt,model):
 req=urllib.request.Request("http://127.0.0.1:11434/api/generate",data=json.dumps({"model":model,"prompt":prompt,"stream":False,"options":{"num_predict":4096}}).encode(),headers={"Content-Type":"application/json"})
 return json.loads(urllib.request.urlopen(req,timeout=120).read())
def _summary(rows):
 n=len(rows); return "\n".join(["# Ollama math track qualification","",f"- task_count: {n}",f"- evaluable: {sum(r['evaluable'] for r in rows)} / {n}",f"- oracle_pass: {sum(r['oracle_pass'] for r in rows)} / {n}",f"- qualified: {n>0 and all(r['evaluable'] and r['oracle_pass'] for r in rows)}",f"- provider_duration_total: {sum(r.get('provider_duration') or 0 for r in rows):.3f}",""])
def main(argv=None):
 p=argparse.ArgumentParser();m=p.add_mutually_exclusive_group();m.add_argument("--dry-run",action="store_true");m.add_argument("--execute-model",action="store_true");p.add_argument("--model-tag",required=True,choices=PROVENANCE);p.add_argument("--condition",required=True,choices=CONDITIONS);p.add_argument("--run-id",required=True);p.add_argument("--task-family",choices=base.FAMILIES);a=p.parse_args(argv); rows=records(a.model_tag,a.condition,a.task_family)
 if a.dry_run: print(json.dumps({"provenance":PROVENANCE[a.model_tag],"model_tag":a.model_tag,"condition":a.condition,"task_count":len(rows),"prompt_sizes":[r["prompt_size"] for r in rows],"retry_count":0,"healer_enabled":False,"model_calls":0}));return 0
 if not a.execute_model: p.print_usage();return 2
 stem=f"ollama_{a.model_tag.replace(':','_').replace('-','_')}_{a.condition}_{a.run_id}";out=ROOT/"docs/experiments/results"/f"{stem}.jsonl";summary=ROOT/"docs/experiments"/f"{stem}_summary.md"
 if out.exists(): raise FileExistsError(out)
 out.parent.mkdir(parents=True,exist_ok=True)
 for r in rows:
  started=time.monotonic()
  try:
   response=_call(r["final_prompt"],a.model_tag);raw=response["response"];task=next(x for x in base._tasks(a.task_family) if x["skill_id"]==r["task_family"]);status,candidate,detail=classify_response(raw,{"oracle_payload":r["task_parameters"]},task,execution_timeout=3);r.update({"raw_first_attempt_output":raw,"candidate_extracted":candidate,"evaluable":status not in {"empty_response","extraction_failure","parse_minor","catastrophic_truncation"},"oracle_pass":status=="passed","failure_category":None if status=="passed" else status,"failure_detail":str(detail) or None,"provider_duration":response.get("total_duration",0)/1e9,"prompt_token_count":response.get("prompt_eval_count"),"output_token_count":response.get("eval_count"),"total_token_count":(response.get("prompt_eval_count") or 0)+(response.get("eval_count") or 0)})
  except Exception as e:r.update({"failure_category":"provider_error","failure_detail":str(e),"provider_duration":None})
  r["wall_clock_seconds"]=time.monotonic()-started;_append(out,r)
 summary.write_text(_summary(rows),encoding="utf-8")
 return 0
if __name__=="__main__": raise SystemExit(main())
