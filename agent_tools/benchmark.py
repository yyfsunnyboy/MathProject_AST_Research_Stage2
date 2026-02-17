import sys
import os
import json
import time

# 設定專案根目錄
# benchmark.py 在 math-problem-generator/scripts/ 下，需往上跳 3 層回到專案根目錄
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(PROJECT_ROOT)

from core.ai_wrapper import get_ai_client, call_ai_with_retry
from core.validators.code_validator import validate_python_code
from core.healers.regex_healer import RegexHealer
from core.healers.ast_healer import ASTHealer

# Try importing MCRI Evaluator
try:
    from scripts.evaluate_mcri import MCRI_Evaluator
    MCRI_EVALUATOR_AVAILABLE = True
except ImportError:
    print("⚠️ MCRI Evaluator not found in scripts.evaluate_mcri")
    MCRI_EVALUATOR_AVAILABLE = False

def calculate_mcri_score(code_str, eval_id):
    """
    使用 MCRI_Evaluator 計算代碼分數
    """
    if not MCRI_EVALUATOR_AVAILABLE:
        return 0.0

    # 1. Save to temp file
    temp_filename = f"temp_mcri_{eval_id}.py"
    temp_path = os.path.join(PROJECT_ROOT, "skills", temp_filename) # Put in skills folder as MCRI expects
    
    # Ensure skills dir exists
    os.makedirs(os.path.dirname(temp_path), exist_ok=True)
    
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(code_str)
            
        # 2. Initialize Evaluator
        # ablation_id=3 (Ab3 - Healer)
        evaluator = MCRI_Evaluator(temp_path, ablation_id=3) 
        
        if not evaluator.load_skill_module():
            return 0.0
            
        # 3. Calculate Scores (Simplified MCRI Logic)
        # L1: Syntax & Safety
        l1_score, _ = evaluator.evaluate_syntax_safety()
        l1_stab, _, _ = evaluator.evaluate_runtime_stability(repetitions=1)
        l1_total = l1_score + l1_stab # Max 17.5 approx
        
        # Fake result dict for L2/L3 (simplified)
        # We run generate to get a result for checking
        try:
            gen_result = evaluator.generate_func()
        except:
            gen_result = {}

        # L2: Interface
        l2_contract, _ = evaluator.evaluate_interface_contract(gen_result)
        l2_fmt, _ = evaluator.evaluate_format_purity(gen_result)
        l2_total = l2_contract + l2_fmt
        
        # L3: Consistency
        l3_score, _ = evaluator.evaluate_internal_consistency(gen_result)
        
        # L4: Math Quality
        q_text = str(gen_result.get('question_text', ''))
        ans_text = str(gen_result.get('answer', ''))
        math_res = evaluator.score_math_question(q_text, ans_text)
        l4_total = math_res.get('total_math_score', 0)
        
        # Simple Weighted Sum (Normalized to 100 roughly)
        # L1(15) + L2(15) + L3(20) + L4(50) = 100
        # Our partial sums:
        # l1 ~ 17.5 (scaled to 15) -> l1 * 0.85
        # l2 ~ 15 -> l2 * 1.0
        # l3 ~ 15 (scaled to 20 without external check) -> l3 * 1.3
        # l4 ~ 50 -> l4
        
        total_score = (min(l1_total, 15)) + (min(l2_total, 15)) + (min(l3_score, 20)) + (min(l4_total, 50))
        
        return round(total_score, 1)

    except Exception as e:
        print(f"  ⚠️ MCRI Calc Error: {e}")
        return 0.0
    finally:
        # Cleanup
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass


def load_prompt_from_file(prompt_filename):
    """從 experiments/golden_prompts/temp/ 讀取 Prompt 內容 (模擬 SKILL.md)"""
    path = os.path.join(PROJECT_ROOT, "experiments", "golden_prompts", "temp", prompt_filename)
    if not os.path.exists(path):
        # 嘗試在上一層找 (可能是 golden_prompts/)
        path = os.path.join(PROJECT_ROOT, "experiments", "golden_prompts", prompt_filename)
    
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return None

def run_benchmark(evals_file="evals.json"):
    print("🚀 Starting Math Problem Generator Benchmark...")
    print(f"Project Root: {PROJECT_ROOT}")

    # 1. Load Evals
    # evals_path = os.path.join(PROJECT_ROOT, "math-problem-generator", "evals", "evals.json")
    # If evals_file is absolute path, use it; else, look in evals dir or project root
    if os.path.isabs(evals_file):
        evals_path = evals_file
    else:
        # Check in math-problem-generator/evals first
        try_path = os.path.join(PROJECT_ROOT, "math-problem-generator", "evals", evals_file)
        if os.path.exists(try_path):
            evals_path = try_path
        else:
            evals_path = os.path.join(PROJECT_ROOT, evals_file)

    if not os.path.exists(evals_path):
        print(f"❌ Evals file not found: {evals_path}")
        return
        
    try:
        with open(evals_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            evals = data.get("evals", [])
    except Exception as e:
        print(f"❌ Failed to load evals.json: {e}")
        return

    print(f"📋 Loaded {len(evals)} test cases.")
    
    results = []
    
    # 2. Run Each Eval
    client = get_ai_client()
    regex_healer = RegexHealer()
    ast_healer = ASTHealer() # Ensure initialized for AST mode

    for idx, test_case in enumerate(evals):
        eval_id = test_case.get("eval_id", f"case_{idx}")
        prompt_file = test_case.get("prompt_file", "")
        desc = test_case.get("description", "")
        
        print(f"\nExample {idx+1}/{len(evals)}: [{eval_id}] {desc}")
        
        # Load Prompt (Simulate `SKILL.md` usage)
        skill_prompt = load_prompt_from_file(prompt_file)
        if not skill_prompt:
            print(f"  ⚠️ Prompt file not found: {prompt_file}. Skipping.")
            continue
            
        print("  Running AI Generation...")
        start_time = time.time()
        
        # Call AI (Simulate Agent Execution)
        try:
            # 模擬 AI 呼叫
            response = call_ai_with_retry(client, skill_prompt, max_retries=3)
            
            # [Fix] Extract text from response object
            if hasattr(response, 'text'):
                raw_code = response.text
            else:
                raw_code = str(response)
            
            # [Debug Print Removed to reduce noise]
            
            # [Pre-Healer Cleaning]
            cleaned_code = raw_code.strip()
            if cleaned_code.startswith("```python"):
                cleaned_code = cleaned_code[9:]
            elif cleaned_code.startswith("```"):
                cleaned_code = cleaned_code[3:]
            
            if cleaned_code.endswith("```"):
                cleaned_code = cleaned_code[:-3]
            
            raw_code = cleaned_code.strip()
                
            duration = time.time() - start_time
            
            if "def generate" not in raw_code:
                # Try simple wrapping if missing
                # raw_code = "def generate():\n" + raw_code # risky
                pass
            
            # Run Healer based on configuration
            healer_type = test_case.get("healer_type", "Regex") # Default to Regex if not specified
            
            if healer_type == "None":
                healed_code = raw_code
                fixes = {}
            elif healer_type == "Regex":
                healed_code, fixes = regex_healer.heal(raw_code)
            elif healer_type == "AST":
                # Pipeline: Regex -> AST
                temp_code, r_fixes = regex_healer.heal(raw_code)
                healed_code, a_fixes = ast_healer.heal(temp_code)
                fixes = {**r_fixes, **a_fixes}
            else:
                # Default fallback
                healed_code, fixes = regex_healer.heal(raw_code)

            # [Injection] Manual Scaffolding for Benchmark (Only for Ab3/AST or explicit request)
            # We inject for AST mode or if prompt is Ab2/Ab3 to ensure fair comparison of logic if needed
            # But strictly speaking, Ab1 might not have these tools. 
            # Let's inject only if healer is not None, assuming Ab1 (None) implies raw generation testing.
            if healer_type != "None":
                domain_lib_path = os.path.join(PROJECT_ROOT, "core", "prompts", "domain_function_library.py")
                if os.path.exists(domain_lib_path):
                    try:
                        with open(domain_lib_path, "r", encoding="utf-8") as f:
                            domain_lib_code = f.read()
                        healed_code = domain_lib_code + "\n\n" + healed_code
                    except Exception as e:
                        print(f"  ⚠️ Failed to inject domain library: {e}")

            # 3. 驗證代碼 (Validation & Scoring)
            is_valid, error_msg = validate_python_code(healed_code)
            
            mcri_score = 0.0
            if is_valid:
                mcri_score = calculate_mcri_score(healed_code, eval_id)
            
            # Define PASS: Valid execution
            status = "PASS" if is_valid else "FAIL" 
            color = "\033[92m" if status == "PASS" else "\033[91m"
            reset = "\033[0m"
            
            print(f"  Result: {color}{status}{reset} (Time: {duration:.2f}s | Healer: {healer_type} | MCRI: {mcri_score:.1f})")
            if not is_valid:
                print(f"  Error: {error_msg}")
                
            results.append({
                "id": eval_id,
                "ablation": test_case.get("ablation_target", "Unknown"),
                "status": status,
                "time": duration,
                "fixes": fixes,
                "score": mcri_score
            })
            
        except Exception as e:
            print(f"  ❌ Runtime Error: {e}")
            results.append({"id": eval_id, "ablation": test_case.get("ablation_target", "Unknown"), "status": "ERROR", "error": str(e), "score": 0.0})

    # 3. Summary Report
    print("\n" + "="*60)
    print("📊 FULL ABLATION BENCHMARK SUMMARY")
    print("="*60)
    
    # Group by Ablation Target
    ablations = list(set(r.get("ablation", "Unknown") for r in results))
    ablations.sort()
    
    for ab in ablations:
        group_results = [r for r in results if r.get("ablation") == ab]
        total = len(group_results)
        passed = sum(1 for r in group_results if r["status"] == "PASS")
        avg_score = sum(r.get("score", 0) for r in group_results) / total if total > 0 else 0
        rate = (passed / total * 100) if total > 0 else 0
        
        print(f"[{ab}] Pass Rate: {rate:5.1f}% | Avg Score: {avg_score:4.1f} | Samples: {total}")
        
    print("="*60)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--evals", default="evals.json", help="Path to evals json file")
    args = parser.parse_args()
    
    # Update global PROJECT_ROOT if needed or pass path
    run_benchmark(args.evals)
