from agent_tools.finals_rebuild.math_generation_runner import *
def test_manifest_and_prompts(tmp_path):
    path=tmp_path/"tasks.jsonl"; path.write_text('{"task_id":"t","domain":"integers","skill_id":"s","task_description":"x","required_entry_point":"generate","required_output_keys":["question_text","correct_answer"],"seed":1}\n',encoding="utf8")
    task=load_math_tasks(path)[0]
    assert task.domain in build_math_ab1_prompt(task)
    assert "# [INJECTED UTILS]" not in build_math_ab2g_prompt(task)
def test_dry_run_never_calls_http(tmp_path):
    task=MathGenerationTask("t","integers","s","x","generate",("question_text","correct_answer"),1)
    result=dry_run((task,),output_root=tmp_path,run_id="r",paired_run_id="p",model="qwen3:4b-instruct-2507-q4_K_M",conditions=("Ab1","Ab2g"),seed=1)
    assert result["http_calls"]==0 and len(result["attempts"])==2
def test_mock_live_generation_persists_metrics(tmp_path):
    task=MathGenerationTask("t","integers","s","x","generate",("question_text","correct_answer"),1)
    seen=[]
    def client(url,payload,timeout):
        seen.append(payload); return {"message":{"content":"def generate(level=1, **kwargs): return {'question_text':'q','correct_answer':'1'}"},"created_at":"now","prompt_eval_count":2,"eval_count":3}
    result=generate_live((task,),output_root=tmp_path,run_id="r",paired_run_id="p",model="qwen3:4b-instruct-2507-q4_K_M",conditions=("Ab1",),seed=1,cold_start_or_warm_run="cold_start",ollama_url="mock",client=client)
    assert len(seen)==1 and result["attempts"][0]["total_token_count"]==5 and result["attempts"][0]["repair_cpu_seconds"]==0.0
def test_summary_includes_failed_and_missing_cells(tmp_path):
    path=tmp_path/"run"; path.mkdir()
    record={"paired_run_id":"p","run_id":"r","task_id":"t","model_tag":"qwen3:8b","prompt_condition":"math_ab1_minimal_domain_prompt","status":"failed","failure_stage":"generation"}
    (path/"attempts.jsonl").write_text(__import__("json").dumps(record)+"\n",encoding="utf8")
    summary=build_live_smoke_summary("p",[path])
    assert summary["failed_attempts"]==1 and len(summary["missing_attempts"])==3
