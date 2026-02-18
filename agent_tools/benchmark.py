import multiprocessing

# --- Windows multiprocessing: 必須 module-level ---
def run_mcri_eval(temp_path, ab_id, model_name, gen_kwargs, idx, healer_applied, healer_fixes, skill_name, run_i, result_queue):
    from scripts.evaluate_mcri import MCRI_Evaluator
    evaluator = MCRI_Evaluator(temp_path, ablation_id=ab_id, model_name=model_name, generation_kwargs=gen_kwargs)
    if evaluator.load_skill_module():
        run_record, run_items = evaluator.run_full_evaluation(sample_index=idx, repetitions=3)
        run_record['skill_name'] = skill_name
        run_record['healer_applied'] = 1 if healer_applied else 0
        run_record['healer_fix_count'] = sum(v for v in healer_fixes.values() if isinstance(v, int)) if healer_fixes else 0
        run_record['notes'] += f" | GenRun:{run_i+1}"
        result_queue.put((run_record, run_items, None))
    else:
        result_queue.put((None, None, 'load_failed'))
# -*- coding: utf-8 -*-
# ==============================================================================
# ID: benchmark.py
# Version: V9.6.0 (Report Directory & Naming Convention)
# Last Updated: 2026-02-17
# Author: Math AI Research Team (Advisor & Student)
#
# [Description]:
#   本程式是科展實驗的核心執行控制台 (Experiment Runner)，負責驅動「自動出題與修復流水線」。
#   V9.6 新增功能：自定義報表輸出路徑 (agent_tools/reports/) 與動態檔名生成。
#
# [Features]:
#   - Interactive Menu: 互動式選單
#   - Filtering: Skill/Ablation 過濾
#   - Repeated Runs: 重複生成測試
#   - MCRI Integration: 詳細 L1-L5 評分
#   - Data Export: SQLite + CSV (Runs, Items, Summary)
# ==============================================================================
import sys
import os
import json
import time
import argparse
import uuid
import shutil
import sqlite3
import pandas as pd
import re
from datetime import datetime

# 設定專案根目錄
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from config import Config
from core.ai_wrapper import get_ai_client, call_ai_with_retry, LocalAIClient, GoogleAIClient
from core.validators.code_validator import validate_python_code
from core.healers.regex_healer import RegexHealer
from core.healers.ast_healer import ASTHealer
from core.code_generator import build_calculation_skeleton, _inject_domain_libs

# Import MCRI tools
try:
    from scripts.evaluate_mcri import (
        MCRI_Evaluator, create_database, insert_experiment_runs, insert_evaluation_items,
        compute_and_insert_summary, write_experiment_runs_csv, write_evaluation_items_csv,
        write_ablation_summary_csv
    )
    MCRI_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ MCRI Import Error: {e}")
    MCRI_AVAILABLE = False

# ==============================================================================
# Model Selection Menu
# ==============================================================================

def show_model_selection_menu():
    """
    顯示模型選擇菜單
    
    Returns:
        str: 選擇的模型 KEY (如 'qwen3-14b', 'gemini-3-flash')
    """
    # 從 Config.CODER_PRESETS 構建模型列表
    # [白名單] 只顯示實驗用的主要模型，排除 Legacy 模型
    BENCHMARK_MODELS = ['gemini-3-flash', 'qwen3-14b', 'qwen3-8b']
    
    available_models = []
    model_display_names = {}
    
    if hasattr(Config, 'CODER_PRESETS'):
        for key in BENCHMARK_MODELS:
            if key in Config.CODER_PRESETS:
                preset = Config.CODER_PRESETS[key]
                provider = preset.get('provider', 'unknown')
                model_name = preset.get('model', key)
                desc = preset.get('description', key)
                
                available_models.append(key)
                if provider == 'google':
                    model_display_names[key] = f"☁️  {model_name} ({desc})"
                else:
                    model_display_names[key] = f"💻 {model_name} ({desc})"
    
    # Fallback if no CODER_PRESETS found
    if not available_models:
        available_models = ['qwen3-14b', 'qwen3-8b', 'gemini-3-flash']
        model_display_names = {
            'qwen3-14b': '💻 Qwen3-14B (Local)',
            'qwen3-8b': '💻 Qwen3-8B (Local)',
            'gemini-3-flash': '☁️  Gemini 3.0 Flash (Cloud)'
        }
    
    print("\n" + "="*70)
    print("🤖 [模型選擇] 請選擇要使用的 AI 模型")
    print("="*70)
    
    for i, model_key in enumerate(available_models, 1):
        display_name = model_display_names.get(model_key, model_key)
        print(f"   [{i}] {display_name}")
    
    while True:
        try:
            choice = input(f"\n👉 請輸入選項 (1-{len(available_models)}): ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(available_models):
                selected = available_models[idx]
                print(f"✅ 已選擇: {model_display_names.get(selected, selected)}")
                return selected
            print("❌ 輸入無效，請重試。")
        except ValueError:
            print("❌ 請輸入數字。")
        except KeyboardInterrupt:
            print("\n⚠️  已取消選擇")
            return None

def load_prompt_from_skill(skill_name, ablation_target="Ab3"):
    """
    從 agent_skills/{skill_name}/ 讀取 Prompt
    """
    if ablation_target == "Ab1":
        path = os.path.join(PROJECT_ROOT, "agent_skills", skill_name, "experiments", "ab1_bare_prompt.md")
    else:
        path = os.path.join(PROJECT_ROOT, "agent_skills", skill_name, "SKILL.md")
    
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
            
    print(f"⚠️ Prompt file not found: {path}")
    return None

def run_benchmark(evals_file="math-problem-generator/evals/evals_full.json", filter_skill=None, filter_ablation=None, repeat_count=1, override_model=None):
    print("🚀 Starting Math Problem Generator Benchmark (Deep Analysis)...")
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Generations per Case: {repeat_count}")
    if override_model:
        print(f"🤖 Override Model: {override_model}")

    # ==============================================================================
    # 1. Load Evals (Dynamic Aggregation)
    # [V9.7 Refactor] Now aggregates from agent_skills/*/evals.json
    # ==============================================================================
    
    evals = []
    agent_skills_dir = os.path.join(PROJECT_ROOT, "agent_skills")
    
    # 優先從各 Skill 目錄載入
    print(f"📂 Scanning skills in: {agent_skills_dir}")
    if os.path.exists(agent_skills_dir):
        for skill_dir in os.listdir(agent_skills_dir):
            skill_path = os.path.join(agent_skills_dir, skill_dir)
            if not os.path.isdir(skill_path):
                continue
                
            eval_file = os.path.join(skill_path, "evals.json")
            if os.path.exists(eval_file):
                try:
                    with open(eval_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        skill_evals = data.get("evals", [])
                        if skill_evals:
                            # 確保 skill_name 正確 (可選)
                            for e in skill_evals:
                                if "skill_name" not in e:
                                    e["skill_name"] = skill_dir
                            evals.extend(skill_evals)
                except Exception as e:
                    print(f"⚠️ Failed to load {eval_file}: {e}")

    # Fallback: 如果什麼都沒掃到，才嘗試讀舊的 evals_full.json
    if not evals:
        print("⚠️ No skill-specific evals found. Trying fallback to evals_full.json...")
        if os.path.isabs(evals_file):
            evals_path = evals_file
        else:
            try_path = os.path.join(PROJECT_ROOT, "math-problem-generator", "evals", evals_file)
            if os.path.exists(try_path):
                evals_path = try_path
            else:
                 try_path_root = os.path.join(PROJECT_ROOT, evals_file)
                 if os.path.exists(try_path_root):
                    evals_path = try_path_root
                 else:
                    evals_path = evals_file

        if os.path.exists(evals_path):
            try:
                with open(evals_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    evals = data.get("evals", [])
            except Exception as e:
                print(f"❌ Failed to load fallback evals.json: {e}")
                return

    # Filter logic
    if filter_skill:
        evals = [e for e in evals if filter_skill in e.get("skill_name", "")]
    if filter_ablation:
        evals = [e for e in evals if e.get("ablation_target") == filter_ablation]
        
    if not evals:
         print(f"⚠️ No matching test cases found. Exiting.")
         return

    print(f"📋 Loaded {len(evals)} test cases (Dynamic Aggregation).")

    # 2. Setup AI & Healers
    # [V9.7] Support override_model parameter
    if override_model:
        # Get preset from Config.CODER_PRESETS
        if hasattr(Config, 'CODER_PRESETS') and override_model in Config.CODER_PRESETS:
            preset = Config.CODER_PRESETS[override_model]
            provider = preset.get('provider', 'local').lower()
            model_name = preset.get('model', override_model)
            temperature = preset.get('temperature', 0.1)
            max_tokens = preset.get('max_tokens', 16384)
            extra_body = preset.get('extra_body', {})
            safety_settings = preset.get('safety_settings')
            
            # Instantiate client based on provider
            if provider in ['google', 'gemini']:
                client = GoogleAIClient(model_name, temperature, max_tokens=max_tokens, safety_settings=safety_settings)
            else:
                client = LocalAIClient(model_name, temperature, max_tokens=max_tokens, extra_body=extra_body)
        else:
            print(f"⚠️ Model '{override_model}' not found in CODER_PRESETS, using default")
            client = get_ai_client()
    else:
        client = get_ai_client()
        
    regex_healer = RegexHealer()
    ast_healer = ASTHealer()

    # 3. Setup Storage
    instance_dir = os.path.join(PROJECT_ROOT, "instance")
    os.makedirs(instance_dir, exist_ok=True)
    db_path = os.path.join(instance_dir, "benchmark.db")
    
    if MCRI_AVAILABLE:
        create_database(db_path)
    
    all_runs = []
    all_items = []

    # 4. Main Loop
    for idx, test_case in enumerate(evals):
        eval_id_base = test_case.get("eval_id", f"case_{idx}")
        skill_name = test_case.get("skill_name", "")
        ablation_target = test_case.get("ablation_target", "Ab3")
        desc = test_case.get("description", "")
        
        # Mapping logic for backwards compatibility
        if not skill_name and "prompt_file" in test_case:
             mapping = {
                "jh_數學2上_FourOperationsOfRadicals_Ab2.txt": "jh_數學2上_FourOperationsOfRadicals",
                "jh_數學1上_FourArithmeticOperationsOfIntegers_Ab2.txt": "jh_數學1上_FourArithmeticOperationsOfIntegers",
                "gh_ApplicationsOfDerivatives_Ab2.txt": "gh_ApplicationsOfDerivatives"
            }
             pf = test_case["prompt_file"]
             skill_name = mapping.get(pf, pf.replace("_Ab2.txt", "").replace("_Ab1.txt", ""))

        print(f"\nExample {idx+1}/{len(evals)}: [{eval_id_base}] Ab:{ablation_target}")
        skill_prompt = load_prompt_from_skill(skill_name, ablation_target)
        if not skill_prompt:
            continue

        ab_id_map = {"Ab1": 1, "Ab2": 2, "Ab3": 3}
        ab_id = ab_id_map.get(ablation_target, 3)

        for run_i in range(repeat_count):
            print(f"  🔹 Gen {run_i+1}/{repeat_count}...", end="", flush=True)
            
            try:
                # A. Generate
                response = call_ai_with_retry(client, skill_prompt, max_retries=3, timeout=180)
                if hasattr(response, 'text'):
                    raw_code = response.text
                else:
                    raw_code = str(response)
                
                # B. Heal & Extract Code
                # [Robust Extraction] Search for code blocks anywhere in the text
                cleaned_code = raw_code.strip()
                
                # [V9.8 Robust Extraction]
                # 1. Try Markdown Fences
                code_block_match = re.search(r'```python\s*(.*?)```', cleaned_code, re.DOTALL)
                if code_block_match:
                    cleaned_code = code_block_match.group(1).strip()
                else:
                    code_block_match = re.search(r'```\s*(.*?)```', cleaned_code, re.DOTALL)
                    if code_block_match:
                        cleaned_code = code_block_match.group(1).strip()
                
                # 2. [NEW] Aggressive Prelude Stripper
                # Identify the start of valid code (import or def)
                # This removes "好的，..." or "Sure, here is..." thinking text
                match_start = re.search(r'^(import|from|def\s+)', cleaned_code, re.MULTILINE)
                if match_start:
                    start_index = match_start.start()
                    if start_index > 0:
                        # Keep only from the first code token onwards
                         cleaned_code = cleaned_code[start_index:]
                
                # 3. Cleanup Fences (Double Safety)
                cleaned_code = re.sub(r'^```python\s*', '', cleaned_code, flags=re.MULTILINE)
                cleaned_code = re.sub(r'^```\s*', '', cleaned_code, flags=re.MULTILINE)
                cleaned_code = re.sub(r'```$', '', cleaned_code.strip(), flags=re.MULTILINE)
                
                
                raw_code = cleaned_code.strip()
                print(f" 🔍 [Pre-Heal] Code: {raw_code[:100].replace(chr(10), ' ')}...")



                healer_fixes = {}
                healer_applied = False
                
                if ablation_target == "Ab1":
                    healed_code = raw_code
                elif ablation_target == "Ab2":
                    healed_code, stats = regex_healer.heal_minimal(raw_code)
                    healer_fixes = stats if isinstance(stats, dict) else {"regex": stats}
                    healer_applied = True
                    skel = build_calculation_skeleton(skill_name)
                    healed_code = skel + "\n" + healed_code
                    healed_code, _ = _inject_domain_libs(healed_code)
                elif ablation_target == "Ab3":
                    temp_code, r_fixes = regex_healer.heal(raw_code)
                    healed_code, a_fixes = ast_healer.heal(temp_code)
                    a_fixes_dict = {"ast": a_fixes} if isinstance(a_fixes, int) else a_fixes
                    healer_fixes = {**r_fixes, **a_fixes_dict}
                    healer_applied = True
                    skel = build_calculation_skeleton(skill_name)
                    healed_code = skel + "\n" + healed_code
                    healed_code, _ = _inject_domain_libs(healed_code)
                else:
                    healed_code = raw_code # Fallback

                # [Debug] Save artifacts for analysis
                try:
                    debug_dir = os.path.join(PROJECT_ROOT, "agent_tools", "temp_code")
                    os.makedirs(debug_dir, exist_ok=True)
                    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                    
                    # 1. Raw Response (Full Thinking + Code)
                    original_text = response.text if hasattr(response, 'text') else str(response)
                    with open(os.path.join(debug_dir, f"{eval_id_base}_gen{run_i+1}_{timestamp_str}_raw.txt"), "w", encoding="utf-8") as f:
                        f.write(original_text)
                    
                    # 2. Extracted Code (Pre-Heal)
                    with open(os.path.join(debug_dir, f"{eval_id_base}_gen{run_i+1}_{timestamp_str}_extracted.py"), "w", encoding="utf-8") as f:
                        f.write(raw_code)
                    
                    # 3. Healed Code (Final)
                    with open(os.path.join(debug_dir, f"{eval_id_base}_gen{run_i+1}_{timestamp_str}_healed.py"), "w", encoding="utf-8") as f:
                        f.write(healed_code)
                except Exception as e:
                    print(f"⚠️ Failed to save debug files: {e}")

                # C. Evaluate using MCRI
                if MCRI_AVAILABLE:
                    temp_name = f"temp_gen_{uuid.uuid4().hex[:8]}.py"
                    temp_dir = os.path.join(PROJECT_ROOT, "agent_tools", "temp_code")
                    os.makedirs(temp_dir, exist_ok=True)
                    temp_path = os.path.join(temp_dir, temp_name)
                    # [V6.3 FIX] Inject Metadata Headers for L5 Scoring
                    header_lines = []
                    header_lines.append(f"# Created At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    if ab_id == 3:
                        fix_tag = "[Full Healer]"
                    elif ab_id == 2:
                        fix_tag = "[Minimal Healer]"
                    else:
                        fix_tag = "[Bare]"
                        
                    # Calculate fix counts for header
                    basic_fixes = healer_fixes.get('basic', 0) if healer_fixes else 0
                    regex_fixes = healer_fixes.get('regex', 0) if healer_fixes else 0
                    ast_fixes = healer_fixes.get('ast', 0) if healer_fixes else 0
                    
                    header_lines.append(f"# Fix Status: {fix_tag} | Fixes: Basic={basic_fixes}, Advanced=(Regex={regex_fixes}, AST={ast_fixes})")
                    header_lines.append(f"# Performance: {response.latency_ms/1000 if hasattr(response, 'latency_ms') else 0:.2f}s | Tokens: In={response.prompt_tokens if hasattr(response, 'prompt_tokens') else 0}, Out={response.completion_tokens if hasattr(response, 'completion_tokens') else 0}")
                    header_lines.append("") # Empty line separator
                    
                    final_file_content = "\n".join(header_lines) + "\n" + healed_code
                    
                    with open(temp_path, "w", encoding="utf-8") as f:
                        f.write(final_file_content)
                    gen_kwargs = test_case.get("generation_kwargs", {})
                    result_queue = multiprocessing.Queue()
                    p = multiprocessing.Process(target=run_mcri_eval, args=(temp_path, ab_id, test_case.get("model", "unknown"), gen_kwargs, idx, healer_applied, healer_fixes, skill_name, run_i, result_queue))
                    p.start()
                    p.join(Config.EXECUTION_TIMEOUT if hasattr(Config, 'EXECUTION_TIMEOUT') else 10)
                    if p.is_alive():
                        p.terminate()
                        print(" -> 評分超時 (Timeout)")
                        # 記錄超時
                        failed_record = {
                            'run_id': str(uuid.uuid4()),
                            'timestamp': datetime.now().isoformat(),
                            'model_name': test_case.get("model", "unknown"),
                            'skill_name': skill_name,
                            'ablation_id': ab_id,
                            'sample_index': idx,
                            'score_program_total': 0, 'score_math_total': 0, 'avg_mcri_total': 0,
                            'pass_rate': 0.0, 'fail_count': 3, 'repetitions_planned': 3, 'repetitions_completed': 0,
                            'notes': f"評分超時 (>={Config.EXECUTION_TIMEOUT if hasattr(Config, 'EXECUTION_TIMEOUT') else 10}s)",
                            'healer_applied': 1 if healer_applied else 0,
                            'healer_fix_count': sum(v for v in healer_fixes.values() if isinstance(v, int)) if healer_fixes else 0,
                            'avg_exec_time': 0, 'score_l1_total': 0, 'score_l2_total': 0, 
                            'avg_l3_total': 0, 'avg_l4_total': 0, 'score_l5_architecture': 0,
                            'avg_l4_4_mqi': 0, 'avg_complexity_math_ops': 0, 'avg_complexity_inference_steps': 0,
                            'avg_complexity_ast_nodes': 0, 'avg_complexity_loop_depth': 0,
                            'score_l1_1_syntax': 0, 'score_l1_2_runtime': 0,
                            'score_l2_1_contract': 0, 'score_l2_2_purity': 0,
                            'avg_l3_1_internal': 0, 'avg_l3_2_external': 0,
                            'avg_l4_1_numeric': 0, 'avg_l4_2_visual': 0, 'avg_l4_3_artifacts': 0,
                            'source_code_path': temp_path,
                            'code_commit_hash': '', 'python_version': '', 'mcri_version': '', 
                            'model_temperature': 0, 'batch_id': '', 'golden_prompt_path': '', 
                            'prompt_hash': '', 'prompt_tokens': 0, 'completion_tokens': 0, 
                            'total_tokens': 0, 'latency_ms': 0
                        }
                        all_runs.append(failed_record)
                    else:
                        if not result_queue.empty():
                            run_record, run_items, err = result_queue.get()
                            if run_record is not None:
                                all_runs.append(run_record)
                                all_items.extend(run_items)
                                print(f" -> Score: {run_record['avg_mcri_total']:.1f}")
                            else:
                                print(f" -> Load Failed (Score: 0)")
                                # Create a failed record for statistics
                                failed_record = {
                                    'run_id': str(uuid.uuid4()),
                                    'timestamp': datetime.now().isoformat(),
                                    'model_name': test_case.get("model", "unknown"),
                                    'skill_name': skill_name,
                                    'ablation_id': ab_id,
                                    'sample_index': idx,
                                    'score_program_total': 0, 'score_math_total': 0, 'avg_mcri_total': 0,
                                    'pass_rate': 0.0, 'fail_count': 3, 'repetitions_planned': 3, 'repetitions_completed': 0,
                                    'notes': "Load Failed (SyntaxError or Import Error)",
                                    'healer_applied': 1 if healer_applied else 0,
                                    'healer_fix_count': sum(v for v in healer_fixes.values() if isinstance(v, int)) if healer_fixes else 0,
                                    'avg_exec_time': 0, 'score_l1_total': 0, 'score_l2_total': 0, 
                                    'avg_l3_total': 0, 'avg_l4_total': 0, 'score_l5_architecture': 0,
                                    'avg_l4_4_mqi': 0, 'avg_complexity_math_ops': 0, 'avg_complexity_inference_steps': 0,
                                    'avg_complexity_ast_nodes': 0, 'avg_complexity_loop_depth': 0,
                                    'score_l1_1_syntax': 0, 'score_l1_2_runtime': 0,
                                    'score_l2_1_contract': 0, 'score_l2_2_purity': 0,
                                    'avg_l3_1_internal': 0, 'avg_l3_2_external': 0,
                                    'avg_l4_1_numeric': 0, 'avg_l4_2_visual': 0, 'avg_l4_3_artifacts': 0,
                                    'source_code_path': temp_path,
                                    'code_commit_hash': '', 'python_version': '', 'mcri_version': '', 
                                    'model_temperature': 0, 'batch_id': '', 'golden_prompt_path': '', 
                                    'prompt_hash': '', 'prompt_tokens': 0, 'completion_tokens': 0, 
                                    'total_tokens': 0, 'latency_ms': 0
                                }
                                all_runs.append(failed_record)
                        else:
                            print(f" -> 評分異常 (No result)")
                    try:
                        os.remove(temp_path)
                    except: pass
                else:
                    print(" -> MCRI Unavailable")

            except Exception as e:
                print(f" -> Error: {e}")

    # 5. Save Results
    if MCRI_AVAILABLE and all_runs:
        conn = sqlite3.connect(db_path)
        insert_experiment_runs(conn, all_runs)
        insert_evaluation_items(conn, all_items)
        summary_data = compute_and_insert_summary(conn)
        conn.close()
        
        # Export CSVs
        report_dir = os.path.join(PROJECT_ROOT, "agent_tools", "reports")
        os.makedirs(report_dir, exist_ok=True)
        
        # Determine Prefix based on filter
        prefix = "benchmark"
        if filter_skill:
            prefix = filter_skill
            if filter_ablation:
                prefix += f"_{filter_ablation}"  # e.g., SkillName_Ab1
        
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        run_file = os.path.join(report_dir, f"{prefix}_runs_{ts}.csv")
        item_file = os.path.join(report_dir, f"{prefix}_items_{ts}.csv")
        sum_file = os.path.join(report_dir, f"{prefix}_summary_{ts}.csv")
        
        write_experiment_runs_csv(all_runs, run_file)
        write_evaluation_items_csv(all_items, item_file)
        write_ablation_summary_csv(summary_data, sum_file)
        
        print(f"\n✅ Results saved to {report_dir}")
        print(f"   - {os.path.basename(run_file)}")
        print(f"   - {os.path.basename(item_file)}")
        print(f"   - {os.path.basename(sum_file)}")
        print(f"   - DB: {db_path}")

def show_interactive_menu(evals_file):
    # ... (Same as before) ...
    print("\n" + "="*60)
    print("🔎 Benchmark Interactive Menu")
    print("="*60)
    
    if os.path.isabs(evals_file):
        evals_path = evals_file
    else:
        try_path = os.path.join(PROJECT_ROOT, "math-problem-generator", "evals", evals_file)
        if os.path.exists(try_path):
            evals_path = try_path
        else:
             try_path_root = os.path.join(PROJECT_ROOT, evals_file)
             if os.path.exists(try_path_root):
                evals_path = try_path_root
             else:
                print(f"❌ Evals file not found: {evals_file}")
                return

    try:
        with open(evals_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            evals = data.get("evals", [])
    except Exception as e:
        print(f"❌ Failed to load evals.json: {e}")
        return
        
    skills = sorted(list(set(e.get("skill_name", "Unknown") for e in evals if e.get("skill_name"))))
    
    print("[0] Run All Skills")
    for i, skill in enumerate(skills, 1):
        print(f"[{i}] {skill}")
        
    choice = input(f"\n👉 Select Skill (0-{len(skills)}): ").strip()
    
    selected_skill = None
    if choice != '0':
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(skills):
                selected_skill = skills[idx]
        except: return

    print("\n[Ablation Filter]")
    print("[0] Run All Ablations")
    print("[1] Ab1 (Bare)")
    print("[2] Ab2 (Regex)")
    print("[3] Ab3 (AST)")
    
    ab_choice = input("\n👉 Select Ablation (0-3): ").strip()
    selected_ablation = None
    if ab_choice == '1': selected_ablation = "Ab1"
    elif ab_choice == '2': selected_ablation = "Ab2"
    elif ab_choice == '3': selected_ablation = "Ab3"
    
    print("\n[Repetitions for Generation]")
    rep_choice = input("👉 Enter number of generations per case (default 1): ").strip()
    try:
        repeat_count = int(rep_choice)
        if repeat_count < 1: repeat_count = 1
    except:
        repeat_count = 1
    
    # Model Selection
    selected_model = show_model_selection_menu()
    if not selected_model:
        print("⚠️  未選擇模型，使用預設模型")
        selected_model = None
    
    run_benchmark(evals_path, filter_skill=selected_skill, filter_ablation=selected_ablation, repeat_count=repeat_count, override_model=selected_model)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--evals", default="math-problem-generator/evals/evals_full.json", help="Path to evals json file")
    parser.add_argument("--skill", help="Filter by skill name (partial match supported)")
    parser.add_argument("--ablation", help="Filter by ablation (Ab1, Ab2, Ab3)")
    parser.add_argument("--repeat", type=int, default=1, help="Number of generations per test case")
    parser.add_argument("--model", help="Override AI model (e.g. qwen3-14b, gemini-3-flash)")
    parser.add_argument("--menu", action="store_true", help="Show interactive menu")
    args = parser.parse_args()
    
    if args.skill or args.ablation or args.repeat > 1 or args.model:
        run_benchmark(args.evals, filter_skill=args.skill, filter_ablation=args.ablation, repeat_count=args.repeat, override_model=args.model)
    else:
        show_interactive_menu(args.evals)
